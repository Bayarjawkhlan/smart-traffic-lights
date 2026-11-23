import type { LiveSnapshot } from "../api/live";
import type { OverrideRule } from "../api/types";
import { useI18n } from "../i18n/I18n";
import { controllerName, scenarioName } from "../i18n/names";
import { clock, num } from "../lib/format";
import { CapRail } from "../ui/CapRail";
import { controllerColor } from "../ui/palette";

const RULE_KEYS: Record<OverrideRule, "pedestrianHardCap" | "vehicleSoftCap" | "vehicleHardCap"> = {
  "pedestrian-hard-cap": "pedestrianHardCap",
  "vehicle-soft-cap": "vehicleSoftCap",
  "vehicle-hard-cap": "vehicleHardCap",
};

export function MetricsStrip({ snapshot }: { snapshot: LiveSnapshot }) {
  const { t, lang } = useI18n();
  const { frame, state, network } = snapshot;
  const metrics = frame?.metrics;
  const scenario = frame?.scenario ?? state?.scenario;
  const controller = frame?.controller ?? state?.controller;
  const duration = scenario ? network?.scenarios[scenario]?.duration : undefined;
  const pedCap = state?.caps.pedestrianHard ?? 90;
  const overrideBreakdown = metrics
    ? (Object.entries(metrics.overrides) as [OverrideRule, number][])
        .map(([rule, n]) => `${t(RULE_KEYS[rule])}: ${n}`)
        .join("\n")
    : "";
  const value = (v: number | undefined, digits = 0) => (v === undefined ? t("noValue") : num(v, digits));

  return (
    <section className="metrics" aria-label={t("scenarioClock")}>
      <div className="metrics__clock">
        <div className="metrics__time">
          <span className="metrics__now">{frame ? clock(frame.t) : "--:--"}</span>
          {duration !== undefined && <span className="metrics__total">/ {clock(duration)}</span>}
          {state?.paused && <span className="tag tag--paused">{t("connPaused")}</span>}
          {state && state.speed !== 1 && <span className="tag">×{state.speed}</span>}
        </div>
        <div className="metrics__context">
          {scenario && <span>{scenarioName(scenario, lang, network?.scenarios[scenario]?.label)}</span>}
          {controller && (
            <span className="metrics__controller">
              <i style={{ background: controllerColor(controller) }} aria-hidden="true" />
              {controllerName(controller, lang)}
            </span>
          )}
        </div>
      </div>

      <dl className="metrics__list">
        <div className="metric">
          <dt>{t("avgVehicleWait")}</dt>
          <dd>
            {value(metrics?.avgVehicleWait, 1)}
            <small>{t("seconds")}</small>
          </dd>
        </div>
        <div className="metric">
          <dt>{t("vehiclesPerHour")}</dt>
          <dd>{value(metrics?.vehiclesPerHour)}</dd>
        </div>
        <div className="metric">
          <dt>{t("avgPedWait")}</dt>
          <dd>
            {value(metrics?.avgPedestrianWait, 1)}
            <small>{t("seconds")}</small>
          </dd>
        </div>
        <div className="metric metric--cap">
          <dt>{t("maxPedWait")}</dt>
          <dd>
            {value(metrics?.maxPedestrianWait)}
            <small>{t("seconds")}</small>
            <span className="metric__cap">{t("pedCap", { n: pedCap })}</span>
          </dd>
          <CapRail value={metrics?.maxPedestrianWait ?? 0} hard={pedCap} compact label={t("maxPedWait")} />
        </div>
        <div className="metric">
          <dt>{t("spillbackMinutes")}</dt>
          <dd>
            {value(metrics?.spillbackMinutes, 1)}
            <small>{t("minutes")}</small>
          </dd>
        </div>
        <div className={`metric${metrics?.overrideCount ? " metric--alert" : ""}`} title={overrideBreakdown}>
          <dt>{t("overrides")}</dt>
          <dd>{value(metrics?.overrideCount)}</dd>
        </div>
      </dl>
    </section>
  );
}
