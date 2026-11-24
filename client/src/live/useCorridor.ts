import { useState } from "react";
import type { CorridorInfo, Network } from "../api/types";

export const ALL_SITES = "all";
const START_CORRIDOR = "peace";

export interface CorridorChoice {
  corridor: CorridorInfo | null;
  choose: (id: string) => void;
  reveal: (site: string) => void;
}

function corridorShowing(corridors: CorridorInfo[], current: string, site: string): string {
  if (current === ALL_SITES || corridors.find((c) => c.id === current)?.sites.includes(site)) return current;
  return corridors.find((c) => c.sites.includes(site))?.id ?? ALL_SITES;
}

export function useCorridor(network: Network | null, selectedSite: string | null): CorridorChoice {
  const [choice, setChoice] = useState(START_CORRIDOR);
  const [revealed, setRevealed] = useState<string | null>(null);
  const corridors = network?.corridors ?? [];
  const current = choice === ALL_SITES ? ALL_SITES : (corridors.find((c) => c.id === choice) ?? corridors[0])?.id ?? ALL_SITES;

  const reveal = (site: string) => {
    if (network?.sites.some((s) => s.id === site)) setChoice(corridorShowing(corridors, current, site));
  };

  if (network && selectedSite !== revealed) {
    setRevealed(selectedSite);
    if (selectedSite) reveal(selectedSite);
  }

  return { corridor: corridors.find((c) => c.id === current) ?? null, choose: setChoice, reveal };
}
