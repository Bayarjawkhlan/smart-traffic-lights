from __future__ import annotations

import sumolib

MAX_PHASES = 3
PERMISSIVE_TURNS = frozenset("lLrRt")

Connection = sumolib.net.connection.Connection


def _pedestrian(conn: Connection) -> bool:
    return conn.getToLane().getEdge().getFunction() == "crossing"


class PhasePlanner:
    def __init__(self, net: sumolib.net.Net, tls_id: str) -> None:
        tl = net.getTLS(tls_id)
        self.size = 1 + max(index for _, _, index in tl.getConnections())
        self.conns: dict[int, list[Connection]] = {}
        for from_lane, to_lane, index in tl.getConnections():
            for conn in from_lane.getOutgoing():
                if conn.getToLane() == to_lane and conn.getTLLinkIndex() == index:
                    self.conns.setdefault(index, []).append(conn)
        self.nodes = {lane.getEdge().getToNode().getID() for lane, _, _ in tl.getConnections() if lane.getEdge().getFunction() == ""}
        self._node_index: dict[Connection, tuple[sumolib.net.node.Node, int]] = {}
        for conns in self.conns.values():
            for conn in conns:
                node = conn.getJunction()
                self._node_index[conn] = (node, node.getLinkIndex(conn))

    def pedestrian(self, index: int) -> bool:
        return any(_pedestrian(conn) for conn in self.conns[index])

    def inner(self, index: int) -> bool:
        edges = [conn.getFrom() for conn in self.conns[index]]
        return any(edge.getFunction() == "" and edge.getFromNode().getID() in self.nodes for edge in edges)

    def foes(self, a: Connection, b: Connection) -> bool:
        (node_a, ia), (node_b, ib) = self._node_index[a], self._node_index[b]
        if node_a.getID() != node_b.getID() or ia < 0 or ib < 0:
            return False
        return node_a.areFoes(ia, ib) or node_a.areFoes(ib, ia)

    def strict_conflict(self, a: int, b: int) -> bool:
        return any(self._strict_conflict(ca, cb) for ca in self.conns[a] for cb in self.conns[b])

    def _strict_conflict(self, a: Connection, b: Connection) -> bool:
        if not self.foes(a, b):
            return False
        ped_a, ped_b = _pedestrian(a), _pedestrian(b)
        if ped_a and ped_b:
            return False
        dir_a = "" if ped_a else a.getDirection()
        dir_b = "" if ped_b else b.getDirection()
        if ped_a or ped_b:
            return (dir_a or dir_b) not in PERMISSIVE_TURNS
        return dir_a not in PERMISSIVE_TURNS and dir_b not in PERMISSIVE_TURNS

    def compatible(self, green: set[int], extra: set[int]) -> bool:
        return not any(self.strict_conflict(a, b) for a in green for b in extra)

    def plan(self, approach_links: list[set[int]], crosswalk_links: list[set[int]]) -> list[str]:
        groups = self._greedy(approach_links, crosswalk_links)
        if len(groups) > MAX_PHASES:
            groups = self._pack(approach_links, crosswalk_links) or groups
        return [self._state(green) for green in groups]

    def _greedy(self, approach_links: list[set[int]], crosswalk_links: list[set[int]]) -> list[set[int]]:
        pending = sorted(range(len(approach_links)), key=lambda i: -len(approach_links[i]))
        groups: list[set[int]] = []
        while pending:
            seed = pending.pop(0)
            green = set(approach_links[seed])
            for other in list(pending):
                if self.compatible(green, approach_links[other]):
                    green |= approach_links[other]
                    pending.remove(other)
            groups.append(green)
        self._fill(groups, approach_links)
        unserved: list[set[int]] = []
        for links in crosswalk_links:
            placed = False
            for green in groups:
                if self.compatible(green, links):
                    green |= links
                    placed = True
            if not placed:
                unserved.append(links)
        if unserved:
            walk: set[int] = set().union(*unserved)
            for index in sorted(set(self.conns) - walk):
                if not self.pedestrian(index) and self.compatible(walk, {index}) and self.compatible({index}, walk):
                    walk.add(index)
            groups.append(walk)
        return groups

    def _fill(self, groups: list[set[int]], approach_links: list[set[int]]) -> None:
        for green in groups:
            for links in approach_links:
                if not links <= green and self.compatible(green, links):
                    green |= links
        inner = {i for i in self.conns if self.inner(i) and not self.pedestrian(i)}
        for green in groups:
            for index in sorted(inner):
                if self.compatible(green, {index}):
                    green.add(index)

    def _pack(self, approach_links: list[set[int]], crosswalk_links: list[set[int]]) -> list[set[int]] | None:
        items = sorted((links for links in approach_links + crosswalk_links if links), key=len, reverse=True)
        fits = [[self.compatible(a, b) for b in items] for a in items]

        def place(i: int, chosen: list[list[int]]) -> list[list[int]] | None:
            if i == len(items):
                return chosen
            for k, members in enumerate(chosen):
                if all(fits[i][j] for j in members):
                    found = place(i + 1, [*chosen[:k], [*members, i], *chosen[k + 1 :]])
                    if found:
                        return found
            return place(i + 1, [*chosen, [i]]) if len(chosen) < MAX_PHASES else None

        found = place(0, [])
        if not found:
            return None
        groups = [set().union(*(items[i] for i in members)) for members in found]
        self._fill(groups, approach_links)
        for green in groups:
            for links in crosswalk_links:
                if self.compatible(green, links):
                    green |= links
        return groups

    def _state(self, green: set[int]) -> str:
        lit = [conn for index in green for conn in self.conns[index]]
        chars = []
        for index in range(self.size):
            if index not in green:
                chars.append("r")
                continue
            chars.append("g" if any(self._yields(conn, lit) for conn in self.conns[index]) else "G")
        return "".join(chars)

    def _yields(self, conn: Connection, lit: list[Connection]) -> bool:
        node, _ = self._node_index[conn]
        return any(
            other is not conn and self._node_index[other][0].getID() == node.getID()
            and self.foes(conn, other) and node.forbids(other, conn)
            for other in lit
        )
