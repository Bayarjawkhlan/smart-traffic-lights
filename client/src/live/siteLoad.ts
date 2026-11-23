import type { SiteFrame } from "../api/types";
import { capLevel } from "../ui/capLevel";

export function stageTone(site: SiteFrame): "green" | "amber" | "red" | "flashing" {
  switch (site.stage) {
    case "green":
      return "green";
    case "yellow":
      return "amber";
    case "clearance":
      return "flashing";
    case "all-red":
      return "red";
  }
}

export function siteLoad(site: SiteFrame) {
  const queue = site.approaches.reduce((sum, a) => sum + a.queue, 0);
  const people = site.crosswalks.reduce((sum, c) => sum + c.waiting, 0);
  const vehicleWait = Math.max(0, ...site.approaches.map((a) => a.wait));
  const pedWait = Math.max(0, ...site.crosswalks.map((c) => c.wait));
  const vehicleLevel = capLevel(vehicleWait, site.caps.vehicleHard, site.caps.vehicleSoft);
  const pedLevel = capLevel(pedWait, site.caps.pedestrianHard);
  const order = { calm: 0, rising: 1, over: 2 } as const;
  const level = order[vehicleLevel] >= order[pedLevel] ? vehicleLevel : pedLevel;
  return {
    queue,
    people,
    vehicleWait,
    pedWait,
    level,
    spillback: site.approaches.some((a) => a.spillback),
    blocked: site.approaches.some((a) => a.blocked),
  };
}
