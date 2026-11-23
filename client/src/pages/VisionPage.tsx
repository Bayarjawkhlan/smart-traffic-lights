import { useCallback, useEffect, useRef, useState } from "react";
import { requestJson } from "../api/http";
import type { VisionCounts, VisionVideo } from "../api/types";
import { toWebSocketUrl, VISION_URL } from "../config";
import { useI18n } from "../i18n/I18n";
import { renderCode } from "../ui/renderCode";

interface Credit {
  shows: { en: string; mn: string };
  source: string;
  author: string;
  authorUrl: string;
  licence: string;
  licenceUrl: string;
  shareAlike: boolean;
}

// Mirrors vision/videos/SOURCES.md; CC BY-SA clips must stay credited wherever the stream is shown.
const CREDITS: Record<string, Credit> = {
  "tyumen-respubliki-ordzhonikidze": {
    shows: {
      en: "Respubliki and Ordzhonikidze streets, Tyumen, Russia · winter 2021 · fixed kerbside camera",
      mn: "Тюмень хот, ОХУ, Республики ба Орджоникидзе гудамжны уулзвар · 2021 оны өвөл · тогтмол камер",
    },
    source: "https://commons.wikimedia.org/wiki/File:Kruci%C4%9Do_de_stratoj_Respubliko_kaj_Or%C4%9Donikidze_(Tjumeno).webm",
    author: "RG72",
    authorUrl: "https://commons.wikimedia.org/wiki/User:RG72",
    licence: "CC BY-SA 4.0",
    licenceUrl: "https://creativecommons.org/licenses/by-sa/4.0/",
    shareAlike: true,
  },
  "toronto-yonge-dundas": {
    shows: {
      en: "Diagonal crosswalk at Yonge and Dundas, Toronto, Canada · 2011 · handheld",
      mn: "Торонто хот, Канад, Yonge ба Dundas уулзварын диагональ гарц · 2011 · гар камер",
    },
    source: "https://commons.wikimedia.org/wiki/File:DiagonalCrosswalkYongeDundas.webm",
    author: "Raysonho @ Open Grid Scheduler / Grid Engine",
    authorUrl: "https://commons.wikimedia.org/wiki/User:Raysonho",
    licence: "CC0 1.0",
    licenceUrl: "https://creativecommons.org/publicdomain/zero/1.0/",
    shareAlike: false,
  },
};

const PREFERRED_VIDEO = "tyumen-respubliki-ordzhonikidze";

type Load = { kind: "loading" } | { kind: "offline"; message: string } | { kind: "ready"; videos: VisionVideo[] };

export function VisionPage() {
  const { t, lang } = useI18n();
  const [load, setLoad] = useState<Load>({ kind: "loading" });
  const [video, setVideo] = useState<string | null>(null);

  const fetchVideos = useCallback(async () => {
    try {
      const videos = await requestJson<VisionVideo[]>(`${VISION_URL}/api/videos`);
      setLoad({ kind: "ready", videos });
      setVideo((current) => current ?? (videos.find((v) => v.name === PREFERRED_VIDEO) ?? videos[0])?.name ?? null);
    } catch (error) {
      setLoad({ kind: "offline", message: error instanceof Error ? error.message : String(error) });
    }
  }, []);

  useEffect(() => {
    void fetchVideos();
  }, [fetchVideos]);

  const credit = video ? CREDITS[video] : undefined;

  return (
    <div className="page page--vision">
      <header className="page__head">
        <div>
          <span className="eyebrow">{t("navVision")}</span>
          <h1>{t("visionTitle")}</h1>
          <p className="page__lead">{t("visionLead")}</p>
        </div>
      </header>

      {load.kind === "loading" && <p className="muted">…</p>}

      {load.kind === "offline" && (
        <div className="empty-state empty-state--inline">
          <h2>{t("visionOfflineTitle")}</h2>
          <p>{renderCode(t("visionOfflineBody"))}</p>
          <p className="mono muted small">{load.message}</p>
          <button
            type="button"
            className="button"
            onClick={() => {
              setLoad({ kind: "loading" });
              void fetchVideos();
            }}
          >
            {t("visionRetry")}
          </button>
        </div>
      )}

      {load.kind === "ready" && load.videos.length === 0 && (
        <div className="empty-state empty-state--inline">
          <p>{renderCode(t("visionNoVideos"))}</p>
        </div>
      )}

      {load.kind === "ready" && video && (
        <div className="vision">
          <div className="vision__stage">
            <div className="segmented" role="group" aria-label={t("visionVideo")}>
              {load.videos.map((v) => (
                <button key={v.name} type="button" aria-pressed={v.name === video} onClick={() => setVideo(v.name)}>
                  {v.name}
                </button>
              ))}
            </div>
            <Stream key={video} video={video} />
            <p className="hint">{t("visionLegend")}</p>
            <footer className="credit">
              <span className="label">{t("visionCredit")}</span>
              {credit ? (
                <p>
                  {credit.shows[lang]} · <a href={credit.authorUrl} target="_blank" rel="noreferrer">{credit.author}</a>,{" "}
                  <a href={credit.source} target="_blank" rel="noreferrer">Wikimedia Commons</a>,{" "}
                  <a href={credit.licenceUrl} target="_blank" rel="noreferrer">{credit.licence}</a>
                  {credit.shareAlike &&
                    (lang === "mn"
                      ? ". Тайлбарласан урсгал нь эх бичлэгийн өөрчилсөн хувилбар тул мөн CC BY-SA 4.0 лицензтэй."
                      : ". The annotated stream is an adaptation and is shared under CC BY-SA 4.0 as well.")}
                </p>
              ) : (
                <p>{lang === "mn" ? "Таны өөрийн бичлэг; лицензийн мэдээлэл бүртгэгдээгүй." : "Your own footage; no licence recorded."}</p>
              )}
            </footer>
          </div>
          <Counts key={video} video={video} />
        </div>
      )}
    </div>
  );
}

function Stream({ video }: { video: string }) {
  const ref = useRef<HTMLImageElement>(null);
  const [broken, setBroken] = useState(false);
  const { t } = useI18n();
  const url = `${VISION_URL}/api/stream.mjpg?video=${encodeURIComponent(video)}`;

  useEffect(() => {
    const img = ref.current;
    if (!img) return;
    let active = true;
    img.onerror = () => {
      if (active) setBroken(true);
    };
    img.src = url;
    return () => {
      active = false;
      // Browsers keep an MJPEG response open until the image source is cleared.
      img.src = "";
    };
  }, [url]);

  return (
    <div className="stream">
      {broken && <div className="stream__offline">{t("visionOfflineTitle")}</div>}
      <img ref={ref} alt={video} hidden={broken} />
    </div>
  );
}

function Counts({ video }: { video: string }) {
  const { t } = useI18n();
  const [counts, setCounts] = useState<VisionCounts | null>(null);

  useEffect(() => {
    let socket: WebSocket | null = null;
    let timer: number | undefined;
    let closed = false;
    const connect = () => {
      socket = new WebSocket(toWebSocketUrl(VISION_URL, `/ws/counts?video=${encodeURIComponent(video)}`));
      socket.onmessage = (message) => {
        if (typeof message.data !== "string") return;
        try {
          setCounts(JSON.parse(message.data) as VisionCounts);
        } catch {
          // ignore malformed message
        }
      };
      socket.onclose = () => {
        if (!closed) timer = window.setTimeout(connect, 2000);
      };
    };
    connect();
    return () => {
      closed = true;
      window.clearTimeout(timer);
      socket?.close();
    };
  }, [video]);

  return (
    <aside className="zones" aria-live="off">
      <header>
        <h2>{t("visionZones")}</h2>
        {counts && <span className="mono muted small">{t("visionFps", { fps: counts.fps.toFixed(1) })} · t {counts.t.toFixed(1)} s</span>}
      </header>
      {!counts && <p className="muted">{t("visionWaitingForCounts")}</p>}
      <ul>
        {counts?.zones.map((zone) => {
          const load = zone.kind === "approach" ? zone.queued : zone.waiting;
          const level = load >= 4 ? "high" : load >= 1 ? "mid" : "low";
          return (
            <li key={zone.id} className="zone" data-level={level}>
              <div className="zone__head">
                <span className="zone__kind">{zone.kind === "approach" ? t("approachKind") : t("crosswalkKind")}</span>
                <strong>{zone.label}</strong>
              </div>
              <dl>
                {zone.kind === "approach" ? (
                  <>
                    <div className="zone__primary">
                      <dt>{t("visionQueued")}</dt>
                      <dd>{zone.queued}</dd>
                    </div>
                    <div>
                      <dt>{t("visionVehicles")}</dt>
                      <dd>{zone.vehicles}</dd>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="zone__primary">
                      <dt>{t("visionWaiting")}</dt>
                      <dd>{zone.waiting}</dd>
                    </div>
                    <div>
                      <dt>{t("visionPersons")}</dt>
                      <dd>{zone.persons}</dd>
                    </div>
                  </>
                )}
              </dl>
              {zone.kind === "crosswalk" && zone.waiting > 0 && <span className="badge badge--frost">{t("visionDemand")}</span>}
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
