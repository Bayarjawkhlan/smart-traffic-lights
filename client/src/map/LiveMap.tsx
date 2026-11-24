import { Marker, setWorkerUrl } from "maplibre-gl";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";
import { live } from "../api/live";
import type { CorridorInfo, Network } from "../api/types";
import { useI18n } from "../i18n/I18n";
import { siteName, siteSecondaryName } from "../i18n/names";
import { prefersReducedMotion } from "../lib/useMediaQuery";
import { MapEngine } from "./engine";
import { MapLegend } from "./MapLegend";
import { SiteLabels } from "./siteLabels";

setWorkerUrl(workerUrl);

const RULE_SHORT: Record<string, { en: string; mn: string }> = {
  "pedestrian-hard-cap": { en: "Forced · pedestrian cap", mn: "Албадсан · явган хүний хязгаар" },
  "vehicle-hard-cap": { en: "Forced · vehicle hard cap", mn: "Албадсан · машины хатуу хязгаар" },
  "vehicle-soft-cap": { en: "Forced · vehicle soft cap", mn: "Албадсан · машины зөөлөн хязгаар" },
};

interface Props {
  network: Network;
  corridor: CorridorInfo | null;
  selectedSite: string | null;
  onSelectSite: (id: string) => void;
  focusRequest: { site: string; nonce: number } | null;
}

export function LiveMap({ network, corridor, selectedSite, onSelectSite, focusRequest }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const engineRef = useRef<MapEngine | null>(null);
  const markersRef = useRef(new Map<string, { marker: Marker; element: HTMLButtonElement }>());
  const labelsRef = useRef<SiteLabels | null>(null);
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
    const labels = new SiteLabels(
      engine.map,
      () => container.closest(".live__map")?.querySelectorAll(".map-legend, .maplibregl-ctrl-group, .map-fit, .ribbon") ?? [],
    );
    labelsRef.current = labels;
    const badgeTimers = new Map<string, number>();

    for (const site of network.sites) {
      const element = document.createElement("button");
      element.type = "button";
      element.className = "site-marker";
      element.dataset.kind = site.kind;
      element.innerHTML = `<span class="site-marker__pin" aria-hidden="true"></span><span class="site-marker__badge" aria-hidden="true"></span>`;
      element.addEventListener("click", (event) => {
        event.stopPropagation();
        onSelectRef.current(site.id);
      });
      const marker = new Marker({ element, anchor: "center" }).setLngLat(site.center).addTo(engine.map);
      markers.set(site.id, { marker, element });
      labels.add(site.id, site.center, element);
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
      labels.destroy();
      labelsRef.current = null;
      engine.destroy();
      engineRef.current = null;
    };
  }, [network]);

  useEffect(() => {
    for (const site of network.sites) {
      const entry = markersRef.current.get(site.id);
      if (!entry) continue;
      entry.element.setAttribute("aria-label", `${siteName(site, lang)} — ${t(site.kind === "midblock" ? "midblock" : "intersection")}`);
    }
    labelsRef.current?.setNames(
      network.sites.map((site) => ({ id: site.id, name: siteName(site, lang), alt: siteSecondaryName(site, lang) })),
    );
  }, [network, lang, t]);

  useEffect(() => {
    for (const [id, { element }] of markersRef.current) {
      const position = corridor ? corridor.sites.indexOf(id) + 1 : 0;
      element.classList.toggle("is-selected", id === selectedSite);
      element.classList.toggle("is-quiet", corridor !== null && position === 0);
      element.classList.toggle("is-numbered", position > 0);
      element.querySelector(".site-marker__pin")!.textContent = position ? String(position) : "";
      element.setAttribute("aria-pressed", String(id === selectedSite));
    }
    labelsRef.current?.show(corridor?.sites ?? [], selectedSite);
  }, [network, corridor, selectedSite]);

  useEffect(() => {
    if (!focusRequest) return;
    const site = network.sites.find((s) => s.id === focusRequest.site);
    if (site) engineRef.current?.focusSite(site.center);
  }, [focusRequest, network]);

  return (
    <div className="map-shell">
      <div ref={containerRef} className="map-canvas" role="region" aria-label={t("networkMap")} />
      <MapLegend />
      <button type="button" className="map-fit" onClick={() => engineRef.current?.fitNetwork()} title={t("fitNetwork")}>
        <svg viewBox="0 0 16 16" aria-hidden="true">
          <path d="M2 6V2h4M10 2h4v4M14 10v4h-4M6 14H2v-4" fill="none" stroke="currentColor" strokeWidth="1.5" />
        </svg>
        <span className="sr-only">{t("fitNetwork")}</span>
      </button>
    </div>
  );
}
