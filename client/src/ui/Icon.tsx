const PATHS = {
  play: "M5 3.5v9l7.5-4.5z",
  pause: "M4.5 3h2.5v10H4.5zM9 3h2.5v10H9z",
  restart: "M3 8a5 5 0 1 0 1.6-3.7M3 2.5v3h3",
  close: "M4 4l8 8M12 4l-8 8",
  back: "M10 3L5 8l5 5",
  sliders: "M3 4.5h10M3 11.5h10M6 2.5v4M10 9.5v4",
  hand: "M8 2v6M5.5 4v5M10.5 4v5M5.5 9c0 3 1.2 5 3.5 5s3.5-1.5 3.5-4V6",
  block: "M3 8h10M8 3a5 5 0 1 0 0 10A5 5 0 0 0 8 3z",
  spark: "M8 2v3M8 11v3M2 8h3M11 8h3M4 4l2 2M10 10l2 2M12 4l-2 2M6 10l-2 2",
  alert: "M8 2.5l6 11H2zM8 7v3M8 11.8v.2",
  info: "M8 2a6 6 0 1 0 0 12A6 6 0 0 0 8 2zM8 7v4M8 5v.2",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 16 }: { name: IconName; size?: number }) {
  const filled = name === "play" || name === "pause";
  return (
    <svg className="icon" width={size} height={size} viewBox="0 0 16 16" aria-hidden="true">
      <path
        d={PATHS[name]}
        fill={filled ? "currentColor" : "none"}
        stroke={filled ? "none" : "currentColor"}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
