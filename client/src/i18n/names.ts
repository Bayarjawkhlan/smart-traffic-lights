import type { ApproachInfo, CrosswalkInfo, Direction, SiteInfo } from "../api/types";
import type { I18n } from "./I18n";
import type { Language, StringKey } from "./strings";

const CONTROLLER_NAMES: Record<string, Record<Language, string>> = {
  "fixed-time": { en: "Fixed-time", mn: "Тогтмол хугацаат" },
  "max-pressure": { en: "Max-pressure", mn: "Хамгийн их даралт" },
  rl: { en: "RL", mn: "RL" },
};

const CONTROLLER_HINTS: Record<string, Record<Language, string>> = {
  "fixed-time": { en: "today's baseline", mn: "өнөөдрийн суурь" },
  "max-pressure": { en: "queues against exit roads", mn: "дарааллыг гарах замтай харьцуулна" },
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

const DIRECTION_KEYS: Record<Direction, StringKey> = {
  northbound: "dirNorth",
  southbound: "dirSouth",
  eastbound: "dirEast",
  westbound: "dirWest",
};

export function approachLabel(approach: ApproachInfo, { lang, t }: I18n): string {
  const street = (lang === "mn" ? approach.street : approach.streetEn) || t("sideRoad");
  return t("approachHeading", { street, direction: t(DIRECTION_KEYS[approach.direction]) });
}

export function crosswalkLabel(crosswalk: CrosswalkInfo, { lang, t }: I18n): string {
  return t("crosswalkAcross", { street: crosswalk.streets.map((s) => s[lang]).join(" / ") || t("theRoad") });
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
