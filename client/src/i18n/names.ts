import type { ApproachInfo, CrosswalkInfo, SiteInfo } from "../api/types";
import type { I18n } from "./I18n";
import type { Language } from "./strings";

const CONTROLLER_NAMES: Record<string, Record<Language, string>> = {
  "fixed-time": { en: "Fixed-time", mn: "Тогтмол хугацаат" },
  "max-pressure": { en: "Max-pressure", mn: "Хамгийн их даралт" },
  rl: { en: "RL", mn: "RL" },
};

const CONTROLLER_HINTS: Record<string, Record<Language, string>> = {
  "fixed-time": { en: "today's baseline", mn: "өнөөдрийн суурь" },
  "max-pressure": { en: "coordinates with neighbours", mn: "хөрш цэгүүдтэй уялдана" },
  rl: { en: "trained in simulation", mn: "симуляцад сурсан" },
};

const SCENARIO_NAMES: Record<string, Record<Language, string>> = {
  "morning-rush": { en: "Morning rush", mn: "Өглөөний оргил" },
  midday: { en: "Midday", mn: "Үд дунд" },
  "evening-rush": { en: "Evening rush", mn: "Оройн оргил" },
  incident: { en: "Incident: lane blocked", mn: "Осол: эгнээ хаагдсан" },
  "pedestrian-surge": { en: "Pedestrian surge (event at the square)", mn: "Явган хүний урсгал (талбай дээрх арга хэмжээ)" },
};

export const controllerName = (name: string, lang: Language, fallback?: string) =>
  CONTROLLER_NAMES[name]?.[lang] ?? fallback ?? name;

export const controllerHint = (name: string, lang: Language) => CONTROLLER_HINTS[name]?.[lang] ?? "";

export const scenarioName = (name: string, lang: Language, fallback?: string) =>
  SCENARIO_NAMES[name]?.[lang] ?? fallback ?? name;

export const siteName = (site: Pick<SiteInfo, "nameEn" | "nameMn">, lang: Language) =>
  lang === "mn" ? site.nameMn : site.nameEn;

export const siteSecondaryName = (site: Pick<SiteInfo, "nameEn" | "nameMn">, lang: Language) =>
  lang === "mn" ? site.nameEn : site.nameMn;

const DIRECTIONS = [
  ["northbound", "dirNorth"],
  ["southbound", "dirSouth"],
  ["eastbound", "dirEast"],
  ["westbound", "dirWest"],
] as const;

const splitLabel = (label: string) => {
  for (const [word, key] of DIRECTIONS) {
    if (label.endsWith(` ${word}`)) return { road: label.slice(0, -word.length - 1), dirKey: key };
  }
  return { road: label, dirKey: null };
};

export function streetNames(site: SiteInfo): Map<string, string> {
  const names = new Map<string, string>();
  for (const approach of site.approaches) {
    const { road } = splitLabel(approach.label);
    if (approach.street) names.set(road, approach.street);
  }
  return names;
}

export function approachLabel(approach: ApproachInfo, i18n: I18n): string {
  if (i18n.lang === "en") return approach.label;
  const { road, dirKey } = splitLabel(approach.label);
  const street = approach.street || (road === "Side road" ? i18n.t("sideRoad") : road);
  return dirKey ? `${street}, ${i18n.t(dirKey)}` : street;
}

export function crosswalkLabel(crosswalk: CrosswalkInfo, streets: Map<string, string>, i18n: I18n): string {
  if (i18n.lang === "en") return crosswalk.label;
  const match = /^Crosswalk across (.+)$/.exec(crosswalk.label);
  if (!match?.[1]) return crosswalk.label;
  const road = match[1];
  const street = road === "the road" ? i18n.t("theRoad") : (streets.get(road) ?? road);
  return i18n.t("crosswalkAcross", { street });
}

export function uniqueLabels<T extends { id: string }>(items: T[], label: (item: T) => string): Map<string, string> {
  const counts = new Map<string, number>();
  const seen = new Map<string, number>();
  for (const item of items) counts.set(label(item), (counts.get(label(item)) ?? 0) + 1);
  const result = new Map<string, string>();
  for (const item of items) {
    const base = label(item);
    if ((counts.get(base) ?? 0) > 1) {
      const n = (seen.get(base) ?? 0) + 1;
      seen.set(base, n);
      result.set(item.id, `${base} · ${n}`);
    } else {
      result.set(item.id, base);
    }
  }
  return result;
}
