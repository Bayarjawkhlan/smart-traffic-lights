from __future__ import annotations

import sumolib

PERMISSIVE_TURNS = frozenset("lLrRt")


class PhasePlanner:
    def __init__(self, net: sumolib.net.Net, tls_id: str) -> None:
        tl = net.getTLS(tls_id)
        self.size = 1 + max(index for _, _, index in tl.getConnections())
        self.conn: dict[int, sumolib.net.connection.Connection] = {}
        for from_lane, to_lane, index in tl.getConnections():
            for conn in from_lane.getOutgoing():
                if conn.getToLane() == to_lane and conn.getTLLinkIndex() == index:
                    self.conn[index] = conn
        self.nodes = {lane.getEdge().getToNode().getID() for lane, _, _ in tl.getConnections() if lane.getEdge().getFunction() == ""}
        self._node_index: dict[int, tuple[sumolib.net.node.Node, int]] = {}
        for index, conn in self.conn.items():
            node = conn.getJunction()
            self._node_index[index] = (node, node.getLinkIndex(conn))

    def pedestrian(self, index: int) -> bool:
        return self.conn[index].getToLane().getEdge().getFunction() == "crossing"

    def inner(self, index: int) -> bool:
        edge = self.conn[index].getFrom()
        return edge.getFunction() == "" and edge.getFromNode().getID() in self.nodes

    def foes(self, a: int, b: int) -> bool:
        (node_a, ia), (node_b, ib) = self._node_index[a], self._node_index[b]
        if node_a.getID() != node_b.getID() or ia < 0 or ib < 0:
            return False
        return node_a.areFoes(ia, ib) or node_a.areFoes(ib, ia)

    def strict_conflict(self, a: int, b: int) -> bool:
        if not self.foes(a, b):
            return False
        ped_a, ped_b = self.pedestrian(a), self.pedestrian(b)
        if ped_a and ped_b:
            return False
        dir_a = "" if ped_a else self.conn[a].getDirection()
        dir_b = "" if ped_b else self.conn[b].getDirection()
        if ped_a or ped_b:
            return (dir_a or dir_b) not in PERMISSIVE_TURNS
        return dir_a not in PERMISSIVE_TURNS and dir_b not in PERMISSIVE_TURNS

    def compatible(self, green: set[int], extra: set[int]) -> bool:
        return not any(self.strict_conflict(a, b) for a in green for b in extra)

    def plan(self, approach_links: list[set[int]], crosswalk_links: list[set[int]]) -> list[str]:
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
        for green in groups:
            for links in approach_links:
                if not links <= green and self.compatible(green, links):
                    green |= links
        inner = {i for i in self.conn if self.inner(i) and not self.pedestrian(i)}
        for green in groups:
            for index in sorted(inner):
                if self.compatible(green, {index}):
                    green.add(index)
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
            for index in sorted(set(self.conn) - walk):
                if not self.pedestrian(index) and self.compatible(walk, {index}) and self.compatible({index}, walk):
                    walk.add(index)
            groups.append(walk)
        return [self._state(green) for green in groups]

    def _state(self, green: set[int]) -> str:
        chars = []
        for index in range(self.size):
            if index not in green:
                chars.append("r")
                continue
            node, own = self._node_index[index]
            yields = any(
                other != index and self._node_index[other][0].getID() == node.getID()
                and self.foes(index, other) and node.forbids(self.conn[other], self.conn[index])
                for other in green
            )
            chars.append("g" if yields else "G")
        return "".join(chars)
