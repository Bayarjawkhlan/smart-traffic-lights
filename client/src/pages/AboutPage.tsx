import { useLive } from "../api/live";
import { useI18n } from "../i18n/I18n";

const SOURCE_URL = "https://github.com/Bayarjawkhlan/smart-traffic-lights";

export function AboutPage() {
  const { t, lang } = useI18n();
  const { state } = useLive();
  const caps = state?.caps ?? { pedestrianHard: 90, vehicleSoft: 120, vehicleHard: 180 };
  const flow =
    lang === "mn"
      ? ["Дараалал, хүлээж буй хүн, гарах зам", "Удирдлага: санал", "Аюулгүй байдлын хамгаалалт: шийдвэр", "Гэрлэн дохио"]
      : ["Queues, waiting people, exit roads", "Controller proposes", "Safety Guard decides", "Signals change"];

  return (
    <div className="page page--about">
      <header className="page__head">
        <div>
          <span className="eyebrow">{t("navAbout")}</span>
          <h1>{t("aboutTitle")}</h1>
          <p className="page__lead">{t("aboutLead")}</p>
        </div>
      </header>

      <ol className="flow" aria-label={`${t("aboutProposeTitle")} → ${t("aboutGuardTitle")}`}>
        {flow.map((step, i) => (
          <li key={step} className={i === 2 ? "flow__step flow__step--guard" : "flow__step"}>
            {step}
          </li>
        ))}
      </ol>

      <div className="about-grid">
        <section>
          <h2>{t("aboutProposeTitle")}</h2>
          <p>{t("aboutProposeBody")}</p>
        </section>
        <section>
          <h2>{t("aboutGuardTitle")}</h2>
          <p>{t("aboutGuardBody")}</p>
        </section>
        <section>
          <h2>{t("aboutCapsTitle")}</h2>
          <ul className="caps-list">
            <li>
              <strong className="mono">{caps.pedestrianHard} s</strong>
              {t("aboutCapsPed", { n: caps.pedestrianHard })}
            </li>
            <li>
              <strong className="mono">{caps.vehicleSoft} s</strong>
              {t("aboutCapsSoft", { n: caps.vehicleSoft })}
            </li>
            <li>
              <strong className="mono">{caps.vehicleHard} s</strong>
              {t("aboutCapsHard", { n: caps.vehicleHard })}
            </li>
          </ul>
        </section>
        <section>
          <h2>{t("aboutHonestTitle")}</h2>
          <p>{t("aboutHonestBody")}</p>
        </section>
        <section className="about-grid__wide">
          <h2>{t("aboutDataTitle")}</h2>
          <p>
            {t("aboutData")}{" "}
            <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
              openstreetmap.org/copyright
            </a>
          </p>
          <p>
            {t("aboutSource")}{" "}
            <a href={SOURCE_URL} target="_blank" rel="noreferrer">
              {SOURCE_URL.replace("https://", "")}
            </a>
          </p>
          <p>{t("aboutLlm")}</p>
        </section>
      </div>
    </div>
  );
}
