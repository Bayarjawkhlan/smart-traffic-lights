import { useI18n } from "../i18n/I18n";
import { capLevel } from "./capLevel";

interface Props {
  value: number;
  soft?: number;
  hard: number;
  label?: string;
  compact?: boolean;
}

export function CapRail({ value, soft, hard, label, compact }: Props) {
  const { t } = useI18n();
  const max = hard * 1.08;
  const pct = (v: number) => `${Math.min(100, (v / max) * 100)}%`;
  const level = capLevel(value, hard, soft);
  return (
    <div
      className={`cap-rail cap-rail--${level}${compact ? " cap-rail--compact" : ""}`}
      role="meter"
      aria-valuemin={0}
      aria-valuemax={hard}
      aria-valuenow={Math.round(value)}
      aria-label={label}
    >
      <div className="cap-rail__track">
        <div className="cap-rail__fill" style={{ width: pct(value) }} />
        {soft !== undefined && <span className="cap-rail__notch cap-rail__notch--soft" style={{ left: pct(soft) }} title={`${t("softCap")} ${soft} s`} />}
        <span className="cap-rail__notch cap-rail__notch--hard" style={{ left: pct(hard) }} title={`${t("hardCap")} ${hard} s`} />
      </div>
    </div>
  );
}
