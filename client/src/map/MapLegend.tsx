import { useI18n } from "../i18n/I18n";
import { palette } from "../ui/palette";

const Vehicle = ({ color, length }: { color: string; length: number }) => (
  <svg viewBox={`0 0 ${length + 2} 8`} width={length + 2} height={8} aria-hidden="true">
    <rect x="1" y="1" width={length} height="6" rx="2" fill={color} />
  </svg>
);

export function MapLegend() {
  const { t } = useI18n();
  return (
    <details className="map-legend" open>
      <summary>{t("legendCongestion")} · {t("legendSignals")}</summary>
      <div className="map-legend__body">
        <section>
          <h3>{t("legendCongestion")}</h3>
          <ul>
            <li><i className="swatch swatch--road" style={{ background: palette.go, opacity: 0.6 }} />{t("congestion_0")}</li>
            <li><i className="swatch swatch--road" style={{ background: palette.amber }} />{t("congestion_1")}</li>
            <li><i className="swatch swatch--road" style={{ background: palette.stop }} />{t("congestion_2")}</li>
          </ul>
        </section>
        <section>
          <h3>{t("legendSignals")}</h3>
          <ul>
            <li><i className="swatch swatch--zebra" style={{ color: palette.go }} />{t("signalGreen")}</li>
            <li><i className="swatch swatch--zebra" style={{ color: palette.amber }} />{t("signalAmber")}</li>
            <li><i className="swatch swatch--zebra" style={{ color: palette.stop }} />{t("signalRed")}</li>
            <li><i className="swatch swatch--zebra swatch--blink" style={{ color: palette.stop }} />{t("signalFlashing")}</li>
            <li><i className="swatch swatch--zebra" style={{ color: palette.background }} />{t("signalBackground")}</li>
          </ul>
        </section>
        <section>
          <h3>{t("legendRoadUsers")}</h3>
          <ul>
            <li><Vehicle color={palette.car} length={10} />{t("car")}</li>
            <li><Vehicle color={palette.bus} length={18} />{t("bus")}</li>
            <li><Vehicle color={palette.truck} length={14} />{t("truck")}</li>
            <li><i className="swatch swatch--dot" style={{ background: palette.walker }} />{t("pedestrian")}</li>
          </ul>
          <p className="map-legend__note">{t("stoppedDim")}</p>
        </section>
      </div>
    </details>
  );
}
