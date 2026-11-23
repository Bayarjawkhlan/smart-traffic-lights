import { useRef, useState, type FormEvent } from "react";
import type { Caps, Network, SimState } from "../api/types";
import { useI18n } from "../i18n/I18n";
import { controllerHint, controllerName, scenarioName } from "../i18n/names";
import { Icon } from "../ui/Icon";
import { controllerColor } from "../ui/palette";
import { useControl } from "./useControl";

const SPEEDS = [0.5, 1, 2, 5, 10] as const;

export function OperatorBar({ network, state }: { network: Network; state: SimState }) {
  const { t, lang } = useI18n();
  const { run, pending, error } = useControl();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [draft, setDraft] = useState<Caps>(state.caps);
  const [capsError, setCapsError] = useState<string | null>(null);

  const openCaps = () => {
    setDraft(state.caps);
    setCapsError(null);
    dialogRef.current?.showModal();
  };

  const submitCaps = async (event: FormEvent) => {
    event.preventDefault();
    const { pedestrianHard, vehicleSoft, vehicleHard } = draft;
    if (!(pedestrianHard >= 45 && pedestrianHard <= 300 && vehicleSoft >= 60 && vehicleSoft <= vehicleHard && vehicleHard <= 600)) {
      setCapsError(t("capsRange"));
      return;
    }
    if (await run({ action: "caps", caps: draft })) dialogRef.current?.close();
  };

  return (
    <section className="operator" aria-label={t("operatorMode")}>
      <div className="operator__group" role="group" aria-label={t("controller")}>
        <span className="operator__label">{t("controller")}</span>
        <div className="segmented">
          {network.controllers.map((controller) => (
            <button
              key={controller.name}
              type="button"
              aria-pressed={state.controller === controller.name}
              disabled={pending !== null}
              title={`${controllerName(controller.name, lang, controller.label)} — ${controllerHint(controller.name, lang)}`}
              onClick={() => run({ action: "controller", name: controller.name })}
            >
              <i className="dot" style={{ background: controllerColor(controller.name) }} aria-hidden="true" />
              {controllerName(controller.name, lang, controller.label)}
            </button>
          ))}
        </div>
      </div>

      <label className="operator__group">
        <span className="operator__label">{t("scenario")}</span>
        <select
          className="select"
          value={state.scenario}
          disabled={pending !== null}
          onChange={(event) => run({ action: "scenario", name: event.target.value })}
        >
          {Object.entries(network.scenarios).map(([name, info]) => (
            <option key={name} value={name}>
              {scenarioName(name, lang, info.label)}
            </option>
          ))}
        </select>
      </label>

      <div className="operator__group" role="group" aria-label={t("speed")}>
        <button
          type="button"
          className="button button--icon"
          onClick={() => run({ action: state.paused ? "resume" : "pause" })}
          aria-label={state.paused ? t("resume") : t("pause")}
          title={state.paused ? t("resume") : t("pause")}
        >
          <Icon name={state.paused ? "play" : "pause"} />
        </button>
        <div className="segmented segmented--tight">
          {SPEEDS.map((speed) => (
            <button
              key={speed}
              type="button"
              aria-pressed={state.speed === speed}
              onClick={() => run({ action: "speed", value: speed })}
              aria-label={`${t("speed")} ×${speed}`}
            >
              ×{speed}
            </button>
          ))}
        </div>
      </div>

      <div className="operator__group">
        <button type="button" className="button" onClick={openCaps}>
          <Icon name="sliders" />
          {t("caps")}
          <span className="operator__caps">
            {state.caps.pedestrianHard}/{state.caps.vehicleSoft}/{state.caps.vehicleHard} s
          </span>
        </button>
        <button type="button" className="button" disabled={pending !== null} onClick={() => run({ action: "restart" })}>
          <Icon name="restart" />
          {t("restart")}
        </button>
      </div>

      {error && (
        <p className="operator__error" role="alert">
          {t("controlFailed", { msg: error })}
        </p>
      )}

      <dialog ref={dialogRef} className="dialog" aria-labelledby="caps-title">
        <form onSubmit={submitCaps}>
          <h2 id="caps-title">{t("editCaps")}</h2>
          <p className="dialog__hint">{t("capsRange")}</p>
          {(
            [
              ["pedestrianHard", "pedestrianHardCap", 45, 300],
              ["vehicleSoft", "vehicleSoftCap", 60, 600],
              ["vehicleHard", "vehicleHardCap", 60, 600],
            ] as const
          ).map(([key, label, min, max]) => (
            <label key={key} className="field">
              <span>{t(label)}</span>
              <span className="field__input">
                <input
                  type="number"
                  min={min}
                  max={max}
                  step={5}
                  value={draft[key]}
                  onChange={(event) => setDraft({ ...draft, [key]: Number(event.target.value) })}
                />
                <span>s</span>
              </span>
            </label>
          ))}
          {capsError && (
            <p className="dialog__error" role="alert">
              {capsError}
            </p>
          )}
          <div className="dialog__actions">
            <button type="button" className="button" onClick={() => dialogRef.current?.close()}>
              {t("cancel")}
            </button>
            <button type="submit" className="button button--primary" disabled={pending === "caps"}>
              {t("applyCaps")}
            </button>
          </div>
        </form>
      </dialog>
    </section>
  );
}
