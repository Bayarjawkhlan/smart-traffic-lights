import type { CorridorInfo, Network, SiteInfo } from "../api/types";

export function corridorSites(network: Network, corridor: CorridorInfo | null): SiteInfo[] {
  if (!corridor) return network.sites;
  return corridor.sites.flatMap((id) => network.sites.find((s) => s.id === id) ?? []);
}
