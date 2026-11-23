import { Marker, setWorkerUrl } from "maplibre-gl";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";
import { live } from "../api/live";
import type { Network } from "../api/types";
import { useI18n } from "../i18n/I18n";
import { siteName, siteSecondaryName } from "../i18n/names";
import { prefersReducedMotion } from "../lib/useMediaQuery";
import { MapEngine } from "./engine";
import { MapLegend } from "./MapLegend";

setWorkerUrl(workerUrl);

const RULE_SHORT: Record<string, { en: string; mn: string }> = {
  "pedestrian-hard-cap": { en: "Forced · pedestrian cap", mn: "Албадсан · явган хүний хязгаар" },
  "vehicle-hard-cap": { en: "Forced · vehicle hard cap", mn: "Албадсан · машины хатуу хязгаар" },
  "vehicle-soft-cap": { en: "Forced · vehicle soft cap", mn: "Албадсан · машины зөөлөн хязгаар" },
};

interface Props {
  network: Network;
  selectedSite: string | null;
  onSelectSite: (id: string | null) => void;
  focusRequest: { site: string; nonce: number } | null;
}

export function LiveMap({ network, selectedSite, onSelectSite, focusRequest }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const engineRef = useRef<MapEngine | null>(null);
  const markersRef = useRef(new Map<string, { marker: Marker; element: HTMLButtonElement }>());
  const onSelectRef = useRef(onSelectSite);
  const { lang, t } = useI18n();
  const langRef = useRef(lang);

  useEffect(() => {
    langRef.current = lang;
    onSelectRef.current = onSelectSite;
  });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const engine = new MapEngine(container, network, prefersReducedMotion());
    engineRef.current = engine;
    const markers = markersRef.current;
    const badgeTimers = new Map<string, number>();

    const westToEast = [...network.sites].sort((a, b) => a.center[0] - b.center[0]);
    for (const site of network.sites) {
      const below = westToEast.indexOf(site) % 2 === 1;
      const element = document.createElement("button");
      element.type = "button";
      element.className = "site-marker";
      element.dataset.kind = site.kind;
      element.dataset.side = below ? "below" : "above";
      element.innerHTML = `<span class="site-marker__pin" aria-hidden="true"></span><span class="site-marker__text"><span class="site-marker__name"></span><span class="site-marker__alt"></span></span><span class="site-marker__badge" aria-hidden="true"></span>`;
      element.addEventListener("click", (event) => {
        event.stopPropagation();
        onSelectRef.current(site.id);
      });
      const marker = new Marker({ element, anchor: "center" }).setLngLat(site.center).addTo(engine.map);
      markers.set(site.id, { marker, element });
    }

    const offFrame = live.onFrame((frame) => engine.ingest(frame));
    const offEvents = live.onEvents((events) => {
      for (const event of events) {
        if (event.kind !== "override" || !event.site) continue;
        engine.flashOverride(event);
        const entry = markers.get(event.site);
        if (!entry) continue;
        const badge = entry.element.querySelector<HTMLElement>(".site-marker__badge");
        const rule = event.override?.rule;
        if (badge) badge.textContent = (rule && RULE_SHORT[rule]?.[langRef.current]) ?? "Override";
        entry.element.classList.add("is-override");
        window.clearTimeout(badgeTimers.get(event.site));
        badgeTimers.set(
          event.site,
          window.setTimeout(() => entry.element.classList.remove("is-override"), 4000),
        );
      }
    });
    const latest = live.getSnapshot().frame;
    if (latest) engine.ingest(latest);

    return () => {
      offFrame();
      offEvents();
      for (const timer of badgeTimers.values()) window.clearTimeout(timer);
      for (const { marker } of markers.values()) marker.remove();
      markers.clear();
      engine.destroy();
      engineRef.current = null;
    };
  }, [network]);

  useEffect(() => {
    for (const site of network.sites) {
      const entry = markersRef.current.get(site.id);
      if (!entry) continue;
      entry.element.querySelector(".site-marker__name")!.textContent = siteName(site, lang);
      entry.element.querySelector(".site-marker__alt")!.textContent = siteSecondaryName(site, lang);
      entry.element.setAttribute("aria-label", `${siteName(site, lang)} — ${t(site.kind === "midblock" ? "midblock" : "intersection")}`);
    }
  }, [network, lang, t]);

  useEffect(() => {
    for (const [id, { element }] of markersRef.current) {
      element.classList.toggle("is-selected", id === selectedSite);
      element.setAttribute("aria-pressed", String(id === selectedSite));
    }
  }, [selectedSite]);

  useEffect(() => {
    if (!focusRequest) return;
    const site = network.sites.find((s) => s.id === focusRequest.site);
    if (site) engineRef.current?.focusSite(site.center);
  }, [focusRequest, network]);

  return (
    <div className="map-shell">
      <div ref={containerRef} className="map-canvas" role="region" aria-label={t("corridor")} />
      <MapLegend />
      <button type="button" className="map-fit" onClick={() => engineRef.current?.fitCorridor()} title={t("fitCorridor")}>
        <svg viewBox="0 0 16 16" aria-hidden="true">
          <path d="M2 6V2h4M10 2h4v4M14 10v4h-4M6 14H2v-4" fill="none" stroke="currentColor" strokeWidth="1.5" />
        </svg>
        <span className="sr-only">{t("fitCorridor")}</span>
      </button>
    </div>
  );
}
