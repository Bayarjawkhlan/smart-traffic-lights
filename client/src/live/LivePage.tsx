import { useState } from "react";
import { useLive } from "../api/live";
import { useI18n } from "../i18n/I18n";
import { LiveMap } from "../map/LiveMap";
import { CorridorRibbon } from "./CorridorRibbon";
import { EventFeed } from "./EventFeed";
import { MetricsStrip } from "./MetricsStrip";
import { OperatorBar } from "./OperatorBar";
import { SitePanel } from "./SitePanel";
import { renderCode } from "../ui/renderCode";

interface Props {
  operator: boolean;
  selectedSite: string | null;
  onSelectSite: (id: string | null) => void;
}

export function LivePage({ operator, selectedSite, onSelectSite }: Props) {
  const snapshot = useLive();
  const { t } = useI18n();
  const { network, state, frame } = snapshot;
  const [focusRequest, setFocusRequest] = useState<{ site: string; nonce: number } | null>(() =>
    selectedSite ? { site: selectedSite, nonce: 0 } : null,
  );
  const site = network?.sites.find((s) => s.id === selectedSite) ?? null;

  const selectAndFocus = (id: string) => {
    onSelectSite(id);
    setFocusRequest({ site: id, nonce: Date.now() });
  };

  if (!network) {
    return (
      <div className="live live--loading">
        <div className="empty-state">
          <span className="empty-state__pulse" aria-hidden="true" />
          <h2>{t("simOfflineTitle")}</h2>
          <p>{renderCode(t("simOfflineBody"))}</p>
          {snapshot.networkError && <p className="mono muted small">{snapshot.networkError}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className={`live${operator ? " live--operator" : ""}`}>
      <MetricsStrip snapshot={snapshot} />
      {operator && state && <OperatorBar network={network} state={state} />}
      <div className="live__body">
        <div className="live__map">
          <LiveMap network={network} selectedSite={selectedSite} onSelectSite={(id) => id && onSelectSite(id)} focusRequest={focusRequest} />
          <CorridorRibbon network={network} frame={frame} selectedSite={selectedSite} onSelect={selectAndFocus} />
        </div>
        <aside className="live__rail" aria-label={site ? undefined : t("corridor")}>
          {site ? (
            <SitePanel key={site.id} network={network} site={site} snapshot={snapshot} operator={operator} onClose={() => onSelectSite(null)} />
          ) : (
            <div className="rail-overview">
              <header className="rail-overview__head">
                <h2>{t("eventFeed")}</h2>
                <p className="hint">{t("corridorHint")}</p>
              </header>
              <EventFeed events={snapshot.events} network={network} emptyText={t("eventsEmpty")} />
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}

