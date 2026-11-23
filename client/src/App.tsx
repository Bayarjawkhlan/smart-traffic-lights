import { useEffect, useState } from "react";
import { live, useLive, type Connection } from "./api/live";
import { useI18n } from "./i18n/I18n";
import type { StringKey } from "./i18n/strings";
import { LivePage } from "./live/LivePage";
import { useRoute, type Page } from "./lib/useRoute";
import { AboutPage } from "./pages/AboutPage";
import { ExperimentsPage } from "./pages/ExperimentsPage";
import { VisionPage } from "./pages/VisionPage";

const NAV: { page: Page; key: StringKey }[] = [
  { page: "live", key: "navLive" },
  { page: "experiments", key: "navExperiments" },
  { page: "vision", key: "navVision" },
  { page: "about", key: "navAbout" },
];

const CONNECTION_KEY: Record<Connection, StringKey> = {
  connecting: "connConnecting",
  open: "connOpen",
  stalled: "connStalled",
  reconnecting: "connReconnecting",
};

const OPERATOR_KEY = "corridor.operator";

function readOperator(): boolean {
  try {
    return localStorage.getItem(OPERATOR_KEY) === "1";
  } catch {
    return false;
  }
}

export function App() {
  const { t, lang, setLang } = useI18n();
  const [route, navigate] = useRoute();
  const [operator, setOperator] = useState(readOperator);
  const { connection, state } = useLive();

  useEffect(() => live.start(), []);

  const toggleOperator = () => {
    const next = !operator;
    setOperator(next);
    try {
      localStorage.setItem(OPERATOR_KEY, next ? "1" : "0");
    } catch {
      // storage unavailable
    }
  };

  const status = connection === "open" && state?.paused ? "paused" : connection;

  return (
    <div className={`app${operator ? " app--operator" : ""}`}>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="topbar">
        <a className="brand" href="#/live" aria-label={t("appName")}>
          <svg className="brand__mark" viewBox="0 0 28 28" aria-hidden="true">
            <rect x="1" y="1" width="26" height="26" rx="7" />
            <circle cx="9" cy="14" r="3" className="brand__go" />
            <circle cx="19" cy="14" r="3" className="brand__stop" />
            <path d="M3 21.5h22" />
          </svg>
          <span className="brand__text">
            <span className="brand__name">{t("appName")}</span>
            <span className="brand__tag">{t("appTagline")}</span>
          </span>
        </a>

        <nav className="tabs" aria-label="Primary">
          {NAV.map((item) => (
            <a
              key={item.page}
              href={`#/${item.page}`}
              className="tabs__item"
              aria-current={route.page === item.page ? "page" : undefined}
            >
              {t(item.key)}
            </a>
          ))}
        </nav>

        <div className="topbar__end">
          <span className="conn" data-status={status} role="status">
            <i aria-hidden="true" />
            {status === "paused" ? t("connPaused") : t(CONNECTION_KEY[connection])}
          </span>
          <div className="segmented segmented--tight" role="group" aria-label={t("language")}>
            <button type="button" aria-pressed={lang === "en"} onClick={() => setLang("en")}>
              EN
            </button>
            <button type="button" aria-pressed={lang === "mn"} onClick={() => setLang("mn")} lang="mn">
              МН
            </button>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={operator}
            className="switch"
            onClick={toggleOperator}
            title={operator ? t("operatorOn") : t("operatorOff")}
          >
            <span className="switch__track" aria-hidden="true">
              <span className="switch__thumb" />
            </span>
            {t("operatorMode")}
          </button>
        </div>
      </header>

      <main id="main" className="main">
        {route.page === "live" && (
          <LivePage
            operator={operator}
            selectedSite={route.site}
            onSelectSite={(site) => navigate({ page: "live", site })}
          />
        )}
        {route.page === "experiments" && <ExperimentsPage operator={operator} />}
        {route.page === "vision" && <VisionPage />}
        {route.page === "about" && <AboutPage />}
      </main>
    </div>
  );
}
