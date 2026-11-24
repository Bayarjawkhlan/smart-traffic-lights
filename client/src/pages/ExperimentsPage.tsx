import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { HttpError } from "../api/http";
import { useLive } from "../api/live";
import { fetchExperiments, startExperiments } from "../api/sim";
import type { ExperimentMetrics, ExperimentResult, ExperimentsResponse } from "../api/types";
import { useI18n } from "../i18n/I18n";
import type { StringKey } from "../i18n/strings";
import { controllerHint, controllerName, scenarioName } from "../i18n/names";
import { num, percent } from "../lib/format";
import { Icon } from "../ui/Icon";
import { controllerColor } from "../ui/palette";
import { renderCode } from "../ui/renderCode";

type MetricKey = "avgVehicleWait" | "maxVehicleWait" | "avgPedestrianWait" | "maxPedestrianWait" | "vehiclesPerHour" | "spillbackMinutes" | "overrideCount";

const METRICS: { key: MetricKey; label: StringKey; lowerBetter: boolean; digits: number }[] = [
  { key: "avgVehicleWait", label: "metric_avgVehicleWait", lowerBetter: true, digits: 1 },
  { key: "avgPedestrianWait", label: "metric_avgPedestrianWait", lowerBetter: true, digits: 1 },
  { key: "vehiclesPerHour", label: "metric_vehiclesPerHour", lowerBetter: false, digits: 0 },
  { key: "maxVehicleWait", label: "metric_maxVehicleWait", lowerBetter: true, digits: 0 },
  { key: "maxPedestrianWait", label: "metric_maxPedestrianWait", lowerBetter: true, digits: 0 },
  { key: "spillbackMinutes", label: "metric_spillbackMinutes", lowerBetter: true, digits: 1 },
  { key: "overrideCount", label: "metric_overrideCount", lowerBetter: true, digits: 0 },
];

const BASELINE = "fixed-time";
const CONTROLLER_ORDER = ["fixed-time", "max-pressure", "rl"];
const EXPERIMENT_SECONDS = 3600;

const delta = (value: number, base: number) => (base === 0 ? null : ((value - base) / Math.abs(base)) * 100);

function latestPerScenario(results: ExperimentResult[], order: string[]): ExperimentResult[] {
  const latest = new Map<string, ExperimentResult>();
  for (const result of results) {
    const current = latest.get(result.scenario);
    if (!current || result.finishedAt > current.finishedAt) latest.set(result.scenario, result);
  }
  return [...latest.values()].sort((a, b) => order.indexOf(a.scenario) - order.indexOf(b.scenario));
}

function useExperiments() {
  const [data, setData] = useState<ExperimentsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setData(await fetchExperiments());
      setError(null);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : String(failure));
    }
  }, []);

  useEffect(() => {
    void refresh();
    const id = window.setInterval(refresh, data?.running ? 3000 : 15000);
    return () => window.clearInterval(id);
  }, [refresh, data?.running]);

  return { data, error, refresh };
}

export function ExperimentsPage({ operator }: { operator: boolean }) {
  const { t, lang } = useI18n();
  const { network } = useLive();
  const { data, error, refresh } = useExperiments();
  const [view, setView] = useState<"charts" | "table">("charts");
  const scenarioOrder = useMemo(() => Object.keys(network?.scenarios ?? {}), [network]);
  const results = useMemo(() => latestPerScenario(data?.results ?? [], scenarioOrder), [data, scenarioOrder]);
  const controllers = useMemo(() => {
    const names = new Set(results.flatMap((r) => Object.keys(r.results)));
    const rank = (name: string) => (CONTROLLER_ORDER.includes(name) ? CONTROLLER_ORDER.indexOf(name) : CONTROLLER_ORDER.length);
    return [...names].sort((a, b) => rank(a) - rank(b));
  }, [results]);

  return (
    <div className="page page--experiments">
      <header className="page__head">
        <div>
          <h1>{t("experimentsTitle")}</h1>
          <p className="page__lead">{t("experimentsLead")}</p>
        </div>
        {results.length > 0 && (
          <div className="segmented" role="group" aria-label={`${t("showCharts")} / ${t("showTable")}`}>
            <button type="button" aria-pressed={view === "charts"} onClick={() => setView("charts")}>
              {t("showCharts")}
            </button>
            <button type="button" aria-pressed={view === "table"} onClick={() => setView("table")}>
              {t("showTable")}
            </button>
          </div>
        )}
      </header>

      {error && !data && (
        <div className="empty-state empty-state--inline">
          <h2>{t("simOfflineTitle")}</h2>
          <p>{renderCode(t("simOfflineBody"))}</p>
        </div>
      )}

      {data && (operator || data.running) && (
        <RunPanel data={data} operator={operator} scenarios={scenarioOrder} onStarted={refresh} />
      )}

      {data && results.length === 0 && (
        <div className="empty-state empty-state--inline">
          <h2>{t("experimentsEmptyTitle")}</h2>
          <p>{renderCode(t("experimentsEmptyBody"))}</p>
        </div>
      )}

      {results.length > 0 && (
        <>
          <Verdict results={results} controllers={controllers} />
          <div className="legend-row" aria-label="Legend">
            {controllers.map((name) => (
              <span key={name} className="legend-row__item">
                <i className={`legend-swatch`} style={{ color: controllerColor(name) }} />
                {controllerName(name, lang)}
                <small>{name === BASELINE ? t("baseline") : controllerHint(name, lang)}</small>
              </span>
            ))}
            <span className="legend-row__meta">
              {t("experimentSubtitle", { n: results.length })}
            </span>
          </div>
          <div className="chart-grid">
            {METRICS.map((metric) => (
              <MetricCard key={metric.key} metric={metric} results={results} controllers={controllers} view={view} />
            ))}
          </div>
          <ul className="runs">
            {results.map((result) => (
              <li key={result.scenario}>
                <strong>{scenarioName(result.scenario, lang, result.label)}</strong>
                <span>{t("simulated", { min: Math.round(result.duration / 60), seed: result.seed })}</span>
                <span>{t("finishedAt", { when: new Date(result.finishedAt).toLocaleString(lang === "mn" ? "mn-MN" : "en-GB") })}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function Verdict({ results, controllers }: { results: ExperimentResult[]; controllers: string[] }) {
  const { t, lang } = useI18n();
  const contenders = controllers.filter((c) => c !== BASELINE);
  if (!controllers.includes(BASELINE) || contenders.length === 0) return null;
  const mean = (controller: string, key: MetricKey) => {
    const values = results
      .map((r) => {
        const value = r.results[controller]?.[key];
        const base = r.results[BASELINE]?.[key];
        return value === undefined || base === undefined ? null : delta(value, base);
      })
      .filter((v): v is number => v !== null);
    return values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
  };
  const shown: { key: MetricKey; lowerBetter: boolean; label: StringKey }[] = [
    { key: "avgVehicleWait", lowerBetter: true, label: "avgVehicleWait" },
    { key: "maxVehicleWait", lowerBetter: true, label: "maxVehicleWait" },
    { key: "avgPedestrianWait", lowerBetter: true, label: "avgPedWait" },
    { key: "vehiclesPerHour", lowerBetter: false, label: "vehiclesPerHour" },
  ];
  return (
    <section className="verdict" aria-label={t("vsBaseline")}>
      {contenders.map((controller) => (
        <article key={controller} className="verdict__card" style={{ ["--series" as string]: controllerColor(controller) }}>
          <h2>
            {controllerName(controller, lang)} <small>{t("vsBaseline")}</small>
          </h2>
          <dl>
            {shown.map((metric) => {
              const value = mean(controller, metric.key);
              const good = value !== null && (metric.lowerBetter ? value < -0.5 : value > 0.5);
              const bad = value !== null && (metric.lowerBetter ? value > 0.5 : value < -0.5);
              return (
                <div key={metric.key}>
                  <dt>{t(metric.label)}</dt>
                  <dd data-verdict={good ? "better" : bad ? "worse" : "same"}>
                    {value === null ? t("noValue") : percent(value)}
                    <small>{good ? t("better") : bad ? t("worse") : ""}</small>
                  </dd>
                </div>
              );
            })}
          </dl>
        </article>
      ))}
    </section>
  );
}

interface CardProps {
  metric: (typeof METRICS)[number];
  results: ExperimentResult[];
  controllers: string[];
  view: "charts" | "table";
}

function MetricCard({ metric, results, controllers, view }: CardProps) {
  const { t, lang } = useI18n();
  const read = (r: ExperimentResult, c: string): number | undefined => (r.results[c] as ExperimentMetrics | undefined)?.[metric.key];
  const max = Math.max(1e-9, ...results.flatMap((r) => controllers.map((c) => read(r, c) ?? 0)));
  const deltaText = (r: ExperimentResult, c: string) => {
    const value = read(r, c);
    const base = read(r, BASELINE);
    if (c === BASELINE || value === undefined || base === undefined) return null;
    const d = delta(value, base);
    if (d === null) return null;
    const good = metric.lowerBetter ? d < -0.5 : d > 0.5;
    const bad = metric.lowerBetter ? d > 0.5 : d < -0.5;
    return { text: percent(d), tone: good ? "better" : bad ? "worse" : "same" };
  };

  return (
    <article className="chart-card">
      <header>
        <h2>{t(metric.label)}</h2>
        <span>{metric.lowerBetter ? t("lowerBetter") : t("higherBetter")}</span>
      </header>
      {view === "charts" ? (
        <div className="bars">
          {results.map((result) => (
            <div key={result.scenario} className="bars__group">
              <span className="bars__scenario">{scenarioName(result.scenario, lang, result.label)}</span>
              <div className="bars__rows">
                {controllers.map((controller) => {
                  const value = read(result, controller);
                  const d = deltaText(result, controller);
                  const name = controllerName(controller, lang);
                  return (
                    <div
                      key={controller}
                      className="bars__row"
                      tabIndex={0}
                      aria-label={`${name}: ${value === undefined ? t("noValue") : num(value, metric.digits)}${d ? `, ${d.text} ${t("vsBaseline")}` : ""}`}
                    >
                      <span
                        className={`bars__bar`}
                        style={{ width: `${((value ?? 0) / max) * 100}%`, color: controllerColor(controller) }}
                      />
                      <span className="bars__value mono">{value === undefined ? t("noValue") : num(value, metric.digits)}</span>
                      {d && (
                        <span className="bars__delta mono" data-verdict={d.tone}>
                          {d.text}
                        </span>
                      )}
                      <span className="bars__tip" role="tooltip">
                        <strong>{name}</strong> {value === undefined ? t("noValue") : num(value, metric.digits)}
                        {d && ` · ${d.text} ${t("vsBaseline")}`}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">{t("scenario")}</th>
              {controllers.map((c) => (
                <th key={c} scope="col">
                  {controllerName(c, lang)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.map((result) => (
              <tr key={result.scenario}>
                <th scope="row">{scenarioName(result.scenario, lang, result.label)}</th>
                {controllers.map((c) => {
                  const value = read(result, c);
                  const d = deltaText(result, c);
                  return (
                    <td key={c} className="mono">
                      {value === undefined ? t("noValue") : num(value, metric.digits)}
                      {d && <small data-verdict={d.tone}> {d.text}</small>}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </article>
  );
}

interface RunProps {
  data: ExperimentsResponse;
  operator: boolean;
  scenarios: string[];
  onStarted: () => Promise<void>;
}

function RunPanel({ data, operator, scenarios, onStarted }: RunProps) {
  const { t, lang } = useI18n();
  const [chosen, setSelected] = useState<string[] | null>(null);
  const selected = chosen ?? scenarios.slice(0, 1);
  const duration = EXPERIMENT_SECONDS;
  const [message, setMessage] = useState<{ tone: "ok" | "error"; text: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (!data.running) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [data.running]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await startExperiments(selected, duration);
      setMessage({ tone: "ok", text: t("experimentStarted") });
      await onStarted();
    } catch (failure) {
      const text =
        failure instanceof HttpError && failure.status === 409
          ? t("experimentAlreadyRunning")
          : t("experimentFailed", { msg: failure instanceof HttpError ? failure.detail : String(failure) });
      setMessage({ tone: "error", text });
    } finally {
      setSubmitting(false);
    }
  };

  const elapsed = data.startedAt ? Math.max(0, Math.round(now / 1000 - data.startedAt)) : 0;
  const ago = elapsed < 60 ? t("secondsAgo", { n: elapsed }) : t("minutesAgo", { n: Math.floor(elapsed / 60) });

  return (
    <section className="run-panel" aria-live="polite">
      {data.running ? (
        <div className="run-panel__running" role="status">
          <span className="spinner" aria-hidden="true" />
          <div>
            <strong>{t("experimentRunning", { ago })}</strong>
            {data.args && (
              <p>
                {data.args.scenarios.map((s) => scenarioName(s, lang)).join(", ")} · {Math.round(data.args.duration / 60)} {t("minutes")}
              </p>
            )}
          </div>
        </div>
      ) : (
        operator && (
          <form className="run-panel__form" onSubmit={submit}>
            <fieldset>
              <legend>{t("experimentScenarios")}</legend>
              <div className="chips">
                {scenarios.map((name) => (
                  <label key={name} className="chip">
                    <input
                      type="checkbox"
                      checked={selected.includes(name)}
                      onChange={(event) =>
                        setSelected(event.target.checked ? [...selected, name] : selected.filter((s) => s !== name))
                      }
                    />
                    <span>{scenarioName(name, lang)}</span>
                  </label>
                ))}
              </div>
            </fieldset>
            <button type="submit" className="button button--primary" disabled={submitting || selected.length === 0}>
              <Icon name="play" />
              {t("runExperiments")}
            </button>
          </form>
        )
      )}
      {message && (
        <p className={message.tone === "error" ? "inline-error" : "hint"} role={message.tone === "error" ? "alert" : undefined}>
          {message.text}
        </p>
      )}
    </section>
  );
}
