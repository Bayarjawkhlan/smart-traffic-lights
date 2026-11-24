import type { LoggedEvent } from "../api/live";
import type { EventKind, Network, SiteInfo } from "../api/types";
import { useI18n, type I18n } from "../i18n/I18n";
import { approachLabel, crosswalkLabel, siteName } from "../i18n/names";
import { clock } from "../lib/format";

const KIND_LABEL: Record<EventKind, { en: string; mn: string }> = {
  override: { en: "Override", mn: "Албадлага" },
  button: { en: "Button", mn: "Товч" },
  incident: { en: "Incident", mn: "Осол" },
  controller: { en: "Controller", mn: "Удирдлага" },
  caps: { en: "Caps", mn: "Хязгаар" },
};

const RULE_MN: Record<string, string> = {
  "pedestrian-hard-cap": "явган хүний хатуу хязгаар",
  "vehicle-hard-cap": "машины хатуу хязгаар",
  "vehicle-soft-cap": "машины зөөлөн хязгаар",
};

function localName(site: SiteInfo | undefined, label: string, i18n: I18n): string {
  const approach = site?.approaches.find((a) => a.label === label);
  if (approach) return approachLabel(approach, i18n);
  const crosswalk = site?.crosswalks.find((c) => c.label === label);
  return crosswalk ? crosswalkLabel(crosswalk, i18n) : label;
}

const SITE_EVENT = /^(?:(\d+) lane\(s\) blocked|Lane reopened|Pedestrian button pressed): (.+)$/;

interface Props {
  events: LoggedEvent[];
  network: Network;
  site?: string;
  emptyText: string;
  limit?: number;
}

export function EventFeed({ events, network, site, emptyText, limit = 120 }: Props) {
  const i18n = useI18n();
  const { lang, t } = i18n;
  const shown = (site ? events.filter((event) => event.site === site) : events).slice(0, limit);
  const sites = new Map(network.sites.map((s) => [s.id, s]));

  if (shown.length === 0) return <p className="feed__empty">{emptyText}</p>;

  const text = (event: LoggedEvent) => {
    if (lang === "en") return event.text;
    if (event.override) {
      const where = sites.get(event.override.site);
      return `Албадсан: ${RULE_MN[event.override.rule] ?? event.override.rule}, ${where ? siteName(where, "mn") : ""} — ${localName(where, event.override.subject, i18n)} ${Math.round(event.override.wait)} с хүлээсэн`;
    }
    const where = event.site ? sites.get(event.site) : undefined;
    const match = SITE_EVENT.exec(event.text);
    const suffix = where ? ` at ${where.nameEn}` : "";
    if (!where || !match?.[2]?.endsWith(suffix)) return event.text;
    const name = localName(where, match[2].slice(0, -suffix.length), i18n);
    if (event.kind === "button") return t("eventButton", { name });
    return match[1] ? t("eventBlocked", { n: match[1], name }) : t("eventReopened", { name });
  };

  return (
    <ol className="feed" aria-live="polite" aria-relevant="additions">
      {shown.map((event) => {
        const where = event.site ? sites.get(event.site) : undefined;
        return (
          <li key={event.seq} className={`feed__item feed__item--${event.kind}`}>
            <span className="feed__time">{clock(event.t)}</span>
            <span className="feed__kind">{KIND_LABEL[event.kind][lang]}</span>
            <span className="feed__text">
              {text(event)}
              {where && !site && lang === "mn" && <span className="feed__site">{siteName(where, lang)}</span>}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
