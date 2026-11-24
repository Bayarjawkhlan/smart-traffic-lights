import { useMemo, useState } from "react";
import type { LiveSnapshot } from "../api/live";
import type { Network, PhaseInfo, SiteFrame, SiteInfo } from "../api/types";
import { useI18n, type I18n } from "../i18n/I18n";
import { approachLabel, crosswalkLabel, siteName, siteSecondaryName, streetNames, uniqueLabels } from "../i18n/names";
import { num } from "../lib/format";
import { CapRail } from "../ui/CapRail";
import { Icon } from "../ui/Icon";
import { EventFeed } from "./EventFeed";
import { ExplainBox } from "./ExplainBox";
import { SiteSchematic } from "./SiteSchematic";
import { stageTone } from "./siteLoad";
import { useControl } from "./useControl";

interface Props {
  network: Network;
  site: SiteInfo;
  snapshot: LiveSnapshot;
  operator: boolean;
  onClose: () => void;
}

function phaseDescription(phase: PhaseInfo, site: SiteInfo, i18n: I18n): string {
  const roads = new Set<string>();
  for (const id of phase.approaches) {
    const approach = site.approaches.find((a) => a.id === id);
    if (approach) roads.add(approachLabel(approach, i18n));
  }
  const parts = [...roads];
  if (phase.crosswalks.length) parts.push(i18n.t("andCrosswalks", { n: phase.crosswalks.length }));
  if (!phase.approaches.length) parts.unshift(i18n.t("pedestriansOnly"));
  return parts.join(" · ");
}

export function SitePanel({ network, site, snapshot, operator, onClose }: Props) {
  const i18n = useI18n();
  const { t, lang } = i18n;
  const { run, pending, error } = useControl();
  const [highlight, setHighlight] = useState<string | null>(null);
  const state: SiteFrame | undefined = snapshot.frame?.sites.find((s) => s.id === site.id);
  const caps = state?.caps ?? snapshot.state?.caps;

  const approachNames = useMemo(() => uniqueLabels(site.approaches, (a) => approachLabel(a, i18n)), [site, i18n]);
  const crosswalkNames = useMemo(() => {
    const streets = streetNames(site);
    return uniqueLabels(site.crosswalks, (c) => crosswalkLabel(c, streets, i18n));
  }, [site, i18n]);

  const scores = state ? Object.entries(state.pressures).map(([k, v]) => [Number(k), v] as const) : [];
  const maxScore = Math.max(1e-6, ...scores.map(([, v]) => Math.abs(v)));
  const tone = state ? stageTone(state) : undefined;

  return (
    <article className="site-panel" aria-labelledby="site-title">
      <header className="site-panel__head">
        <button type="button" className="button button--ghost button--small" onClick={onClose}>
          <Icon name="back" />
          {t("backToCorridor")}
        </button>
        <div className="site-panel__title">
          <span className="label">{t(site.kind === "midblock" ? "midblock" : "intersection")}</span>
          <h2 id="site-title">{siteName(site, lang)}</h2>
          <p lang={lang === "mn" ? "en" : "mn"}>{siteSecondaryName(site, lang)}</p>
        </div>
      </header>

      <SiteSchematic network={network} site={site} state={state} frame={snapshot.frame} highlight={highlight} />

      <section className="site-panel__status" data-tone={tone}>
        <div>
          <span className="label">{t("phase")}</span>
          <strong className="mono">
            {state ? state.phase + 1 : t("noValue")}
            {state?.target != null && <span className="site-panel__next" title={t("nextPhase", { n: state.target + 1 })}> → {state.target + 1}</span>}
          </strong>
        </div>
        <div>
          <span className="label">{t("stage")}</span>
          <strong className="stage-chip" data-tone={tone}>
            {state ? t(`stage_${state.stage}`) : t("noValue")}
          </strong>
        </div>
        <div>
          <span className="label">{t("greenFor")}</span>
          <strong className="mono">{state && state.target == null ? `${num(state.greenFor)} s` : t("noValue")}</strong>
        </div>
      </section>

      <section className="site-panel__section">
        <h3>{t("controllerScores")}</h3>
        {scores.length === 0 ? (
          <p className="muted">{t("scoresNone")}</p>
        ) : (
          <>
            <ol className="scores">
              {site.phases.map((phase) => {
                const score = state?.pressures[String(phase.index)] ?? 0;
                const isActive = state?.phase === phase.index;
                return (
                  <li key={phase.index} className="score" data-active={isActive || undefined} data-target={state?.target === phase.index || undefined}>
                    <div className="score__head">
                      <span className="score__name">
                        {t("phaseN", { n: phase.index + 1 })}
                        {isActive && <span className="score__active">{t("active")}</span>}
                      </span>
                      <span className="score__value mono">{num(score, 1)}</span>
                    </div>
                    <div className="score__bar" aria-hidden="true">
                      <i style={{ width: `${(Math.max(0, score) / maxScore) * 100}%` }} />
                    </div>
                    <p className="score__desc">{phaseDescription(phase, site, i18n)}</p>
                  </li>
                );
              })}
            </ol>
            <p className="hint">{t("scoresHint")}</p>
          </>
        )}
      </section>

      <section className="site-panel__section">
        <h3>{t("approaches")}</h3>
        <ul className="rows">
          {site.approaches.map((approach, index) => {
            const a = state?.approaches.find((x) => x.id === approach.id);
            return (
              <li
                key={approach.id}
                className="row"
                onMouseEnter={() => setHighlight(approach.id)}
                onMouseLeave={() => setHighlight(null)}
              >
                <div className="row__main">
                <div className="row__head">
                  <span className="row__index">{index + 1}</span>
                  <span className="row__name">{approachNames.get(approach.id)}</span>
                  <span className="row__stat mono">
                    {a?.queue ?? 0} <small>{t("vehiclesShort")}</small>
                  </span>
                </div>
                <div className="row__rail">
                  {caps && <CapRail value={a?.wait ?? 0} soft={caps.vehicleSoft} hard={caps.vehicleHard} label={`${t("wait")} ${approachNames.get(approach.id)}`} />}
                  <span className="row__wait mono">{num(a?.wait ?? 0)} s</span>
                </div>
                {(a?.spillback || a?.blocked) && (
                  <div className="row__foot">
                    {a?.spillback && <span className="badge badge--amber">{t("spillbackBadge")}</span>}
                    {a?.blocked && <span className="badge badge--red">{t("blockedBadge")}</span>}
                  </div>
                )}
                </div>
                {operator && (
                  <button
                    type="button"
                    className="button button--small row__action"
                    aria-pressed={a?.blocked ?? false}
                    disabled={pending === `block:${approach.id}`}
                    onClick={() => run({ action: "block", site: site.id, target: approach.id }, `block:${approach.id}`)}
                  >
                    <Icon name="block" size={14} />
                    {a?.blocked ? t("reopenLane") : t("blockLane")}
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      </section>

      <section className="site-panel__section">
        <h3>{t("crosswalks")}</h3>
        <ul className="rows">
          {site.crosswalks.map((crosswalk) => {
            const c = state?.crosswalks.find((x) => x.id === crosswalk.id);
            return (
              <li
                key={crosswalk.id}
                className="row"
                onMouseEnter={() => setHighlight(crosswalk.id)}
                onMouseLeave={() => setHighlight(null)}
              >
                <div className="row__main">
                <div className="row__head">
                  <span className="row__name">{crosswalkNames.get(crosswalk.id)}</span>
                  <span className="row__stat mono">
                    {c?.waiting ? (
                      <>
                        {c.waiting} <small>{t("waitingPeople")}</small>
                      </>
                    ) : (
                      <small>{t("noDemand")}</small>
                    )}
                  </span>
                </div>
                <div className="row__rail">
                  {caps && <CapRail value={c?.wait ?? 0} hard={caps.pedestrianHard} label={`${t("wait")} ${crosswalkNames.get(crosswalk.id)}`} />}
                  <span className="row__wait mono">{num(c?.wait ?? 0)} s</span>
                </div>
                {c?.button && (
                  <div className="row__foot">
                    <span className="badge badge--frost">{t("buttonBadge")}</span>
                  </div>
                )}
                </div>
                {operator && (
                  <button
                    type="button"
                    className="button button--small row__action"
                    disabled={c?.button || pending === `button:${crosswalk.id}`}
                    onClick={() => run({ action: "button", site: site.id, target: crosswalk.id }, `button:${crosswalk.id}`)}
                  >
                    <Icon name="hand" size={14} />
                    {t("pressButton")}
                  </button>
                )}
              </li>
            );
          })}
        </ul>
        {error && (
          <p className="inline-error" role="alert">
            {t("controlFailed", { msg: error })}
          </p>
        )}
      </section>

      <ExplainBox site={site} available={snapshot.state?.explainAvailable ?? false} />

      <section className="site-panel__section">
        <h3>{t("siteEvents")}</h3>
        <EventFeed events={snapshot.events} network={network} site={site.id} emptyText={t("siteEventsEmpty")} limit={30} />
      </section>
    </article>
  );
}
