export type Light = "green" | "amber" | "red" | "flashing" | "off";

export function linkLight(state: string, link: number, flashing?: readonly number[]): Light {
  if (flashing?.includes(link)) return "flashing";
  const char = state[link];
  if (char === "G" || char === "g") return "green";
  if (char === "y" || char === "Y") return "amber";
  if (char === "r" || char === "R" || char === "u") return "red";
  return "off";
}

const RANK: Record<Light, number> = { green: 4, amber: 3, flashing: 2, red: 1, off: 0 };

export function bestLight(state: string, links: readonly number[], flashing?: readonly number[]): Light {
  let best: Light = "off";
  for (const link of links) {
    const light = linkLight(state, link, flashing);
    if (RANK[light] > RANK[best]) best = light;
  }
  return best;
}

export const LIGHT_CODE: Record<Light, number> = { off: 0, red: 1, amber: 2, green: 3, flashing: 4 };
