// Keep in sync with the custom properties in styles/tokens.css; MapLibre paint needs literal colours.
export const palette = {
  night: "#15181c",
  deck: "#1b1f24",
  ink: "#d9dde2",
  ink3: "#8b939c",
  go: "#6fb98f",
  amber: "#e0b867",
  stop: "#d9776b",
  frost: "#8aaed6",
  idle: "#3a4149",
  background: "#5d646c",
  sidewalk: "#2b3036",
  walker: "#ece8f4",
  car: "#cfd4da",
  bus: "#8fbbe0",
  truck: "#b9a6d9",
  seriesBaseline: "#6b737c",
  seriesPressure: "#7ea6d8",
  seriesRl: "#cf8f5e",
} as const;

export const controllerColor = (name: string): string =>
  name === "fixed-time" ? palette.seriesBaseline : name === "max-pressure" ? palette.seriesPressure : name === "rl" ? palette.seriesRl : palette.ink3;
