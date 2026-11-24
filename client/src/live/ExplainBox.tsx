import { useState } from "react";
import { HttpError } from "../api/http";
import { requestExplanation } from "../api/sim";
import type { SiteInfo } from "../api/types";
import { useI18n } from "../i18n/I18n";
import type { Language } from "../i18n/strings";
import { clock } from "../lib/format";

type Result =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "done"; text: string; t: number; language: Language }
  | { kind: "error"; message: string; unavailable: boolean };

export function ExplainBox({ site, available }: { site: SiteInfo; available: boolean }) {
  const { t, lang } = useI18n();
  const [chosenLanguage, setLanguage] = useState<Language | null>(null);
  const [result, setResult] = useState<Result>({ kind: "idle" });
  const language = chosenLanguage ?? lang;

  const ask = async () => {
    setResult({ kind: "loading" });
    try {
      const response = await requestExplanation(site.id, language);
      setResult({ kind: "done", text: response.text, t: response.t, language });
    } catch (error) {
      const unavailable = error instanceof HttpError && error.status === 503;
      setResult({ kind: "error", message: error instanceof HttpError ? error.detail : String(error), unavailable });
    }
  };

  return (
    <section className="site-panel__section explain">
      <div className="explain__controls">
        <button type="button" className="button button--primary" disabled={!available || result.kind === "loading"} onClick={ask}>
          {t("explain")}
        </button>
        <div className="segmented segmented--tight" role="group" aria-label={t("explainIn")}>
          {(["en", "mn"] as const).map((code) => (
            <button key={code} type="button" aria-pressed={language === code} onClick={() => setLanguage(code)}>
              {code === "en" ? "EN" : "МН"}
            </button>
          ))}
        </div>
      </div>
      {!available && <p className="hint">{t("explainUnavailable")}</p>}
      {result.kind === "loading" && (
        <p className="explain__loading" role="status">
          {t("explaining")}
        </p>
      )}
      {result.kind === "done" && (
        <blockquote className="explain__text" lang={result.language}>
          <span className="explain__time mono">{clock(result.t)}</span>
          {result.text}
        </blockquote>
      )}
      {result.kind === "error" && (
        <p className="inline-error" role="alert">
          {result.unavailable ? t("explainUnavailable") : t("explainFailed", { msg: result.message })}
        </p>
      )}
      {available && <p className="hint">{t("explainNote")}</p>}
    </section>
  );
}
