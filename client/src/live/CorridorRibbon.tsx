import { useEffect, useRef } from "react";
import type { CorridorInfo, Frame, Network } from "../api/types";
import { useI18n } from "../i18n/I18n";
import { siteName } from "../i18n/names";
import { corridorSites } from "./corridorSites";
import { siteLoad, stageTone } from "./siteLoad";
import { ALL_SITES } from "./useCorridor";

// matches the fade width of .ribbon__row
const FADE = 16;

function scrollToShow(row: HTMLElement, item: Element): void {
  const view = row.getBoundingClientRect();
  const box = item.getBoundingClientRect();
  // scrollIntoView would also scroll the page when the map is partly off screen
  if (box.left < view.left + FADE) row.scrollLeft -= view.left + FADE - box.left;
  else if (box.right > view.right - FADE) row.scrollLeft += box.right - view.right + FADE;
}

const AXIS = {
  ew: { order: "orderWestEast", start: "endWest", finish: "endEast" },
  ns: { order: "orderNorthSouth", start: "endNorth", finish: "endSouth" },
} as const;

interface Props {
  network: Network;
  corridor: CorridorInfo | null;
  frame: Frame | null;
  selectedSite: string | null;
  onChoose: (corridor: string) => void;
  onSelect: (id: string) => void;
}

export function CorridorRibbon({ network, corridor, frame, selectedSite, onChoose, onSelect }: Props) {
  const { t, lang } = useI18n();
  const rowRef = useRef<HTMLDivElement>(null);
  const frames = new Map(frame?.sites.map((s) => [s.id, s]));
  const axis = corridor ? AXIS[corridor.axis] : null;

  useEffect(() => {
    const scrollToSelected = () => {
      const row = rowRef.current;
      const button = row?.querySelector('[aria-pressed="true"]');
      if (row && button) scrollToShow(row, button);
    };
    scrollToSelected();
    document.fonts.addEventListener("loadingdone", scrollToSelected);
    return () => document.fonts.removeEventListener("loadingdone", scrollToSelected);
  }, [selectedSite, corridor, lang]);

  useEffect(() => {
    const row = rowRef.current;
    if (!row) return;
    const mark = () => {
      row.toggleAttribute("data-more-before", row.scrollLeft > 1);
      row.toggleAttribute("data-more-after", row.scrollLeft + row.clientWidth < row.scrollWidth - 1);
    };
    const resizes = new ResizeObserver(mark);
    resizes.observe(row);
    if (row.firstElementChild) resizes.observe(row.firstElementChild);
    row.addEventListener("scroll", mark, { passive: true });
    return () => {
      resizes.disconnect();
      row.removeEventListener("scroll", mark);
    };
  }, [corridor]);

  return (
    <nav className="ribbon" aria-label={t("sites")}>
      {network.corridors && network.corridors.length > 0 && (
        <div className="ribbon__head">
          <label className="ribbon__picker">
            <span>{t("corridor")}</span>
            <select className="select" value={corridor?.id ?? ALL_SITES} onChange={(event) => onChoose(event.target.value)}>
              {network.corridors.map((c) => (
                <option key={c.id} value={c.id}>
                  {siteName(c, lang)}
                </option>
              ))}
              <option value={ALL_SITES}>{t("allSites")}</option>
            </select>
          </label>
        </div>
      )}
      <div key={corridor?.id ?? ALL_SITES} ref={rowRef} className="ribbon__row">
        <div className="ribbon__track">
          {axis && (
            <span className="ribbon__end" aria-hidden="true">
              {t(axis.start)}
            </span>
          )}
          <ol
            className="ribbon__sites"
            data-connected={corridor !== null || undefined}
            aria-label={axis ? t(axis.order) : undefined}
          >
            {corridorSites(network, corridor).map((site, index) => {
              const state = frames.get(site.id);
              const load = state ? siteLoad(state) : null;
              return (
                <li key={site.id}>
                  <button
                    type="button"
                    className="ribbon__site"
                    aria-pressed={selectedSite === site.id}
                    onFocus={(event) => rowRef.current && scrollToShow(rowRef.current, event.currentTarget)}
                    onClick={() => onSelect(site.id)}
                  >
                    <span className="ribbon__node" data-tone={state ? stageTone(state) : undefined} aria-hidden="true" />
                    <span className="ribbon__name">
                      {corridor && (
                        <span className="ribbon__number" aria-hidden="true">
                          {index + 1}
                        </span>
                      )}
                      {siteName(site, lang)}
                    </span>
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
          {axis && (
            <span className="ribbon__end" aria-hidden="true">
              {t(axis.finish)}
            </span>
          )}
        </div>
      </div>
    </nav>
  );
}
