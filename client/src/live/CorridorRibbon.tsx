import type { Frame, Network } from "../api/types";
import { useI18n } from "../i18n/I18n";
import { siteName } from "../i18n/names";
import { siteLoad, stageTone } from "./siteLoad";

interface Props {
  network: Network;
  frame: Frame | null;
  selectedSite: string | null;
  onSelect: (id: string) => void;
}

export function CorridorRibbon({ network, frame, selectedSite, onSelect }: Props) {
  const { t, lang } = useI18n();
  const sites = [...network.sites].sort((a, b) => a.center[0] - b.center[0]);
  const frames = new Map(frame?.sites.map((s) => [s.id, s]));

  return (
    <nav className="ribbon" aria-label={t("westToEast")}>
      <div className="ribbon__axis" aria-hidden="true">
        <span>W</span>
        <span className="ribbon__street">{lang === "mn" ? "Энх тайваны өргөн чөлөө" : "Peace Avenue"}</span>
        <span>E</span>
      </div>
      <ol className="ribbon__sites">
        {sites.map((site) => {
          const state = frames.get(site.id);
          const load = state ? siteLoad(state) : null;
          return (
            <li key={site.id}>
              <button
                type="button"
                className="ribbon__site"
                aria-pressed={selectedSite === site.id}
                onClick={() => onSelect(site.id)}
              >
                <span className="ribbon__node" data-tone={state ? stageTone(state) : undefined} aria-hidden="true" />
                <span className="ribbon__name">{siteName(site, lang)}</span>
                <span className="ribbon__phases" aria-label={state ? t("phaseN", { n: state.phase + 1 }) : undefined}>
                  {site.phases.map((phase) => {
                    const isActive = state?.phase === phase.index;
                    const isTarget = state?.target === phase.index;
                    return (
                      <i
                        key={phase.index}
                        data-active={isActive || undefined}
                        data-target={isTarget || undefined}
                        data-tone={isActive && state ? stageTone(state) : undefined}
                      />
                    );
                  })}
                </span>
                <span className="ribbon__load" data-level={load?.level} title={t("worstWait")}>
                  {load ? (
                    <>
                      <span>
                        {load.queue} {t("vehiclesShort")}
                      </span>
                      <span>{Math.round(Math.max(load.vehicleWait, load.pedWait))} s</span>
                    </>
                  ) : (
                    <span>{t("noValue")}</span>
                  )}
                  {load?.spillback && <span className="ribbon__flag" title={t("spillbackBadge")}>S</span>}
                  {load?.blocked && <span className="ribbon__flag ribbon__flag--blocked" title={t("blockedBadge")}>✕</span>}
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
