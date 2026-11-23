// Keep in sync with the custom properties in styles/tokens.css; MapLibre paint needs literal colours.
export const palette = {
  night: "#0b0f14",
  deck: "#10161d",
  ink: "#e9eef4",
  ink3: "#8592a2",
  go: "#3ad07f",
  amber: "#f4b53f",
  stop: "#ff5b55",
  frost: "#8ccfff",
  idle: "#3a4554",
  background: "#556070",
  sidewalk: "#26303c",
  walker: "#f3ecff",
  car: "#d9e1ea",
  bus: "#7fd1ff",
  truck: "#c9a8ff",
  seriesBaseline: "#a7afbb",
  seriesPressure: "#3987e5",
  seriesRl: "#d95926",
} as const;

export const controllerColor = (name: string): string =>
  name === "fixed-time" ? palette.seriesBaseline : name === "max-pressure" ? palette.seriesPressure : name === "rl" ? palette.seriesRl : palette.ink3;
