export function capLevel(value: number, hard: number, soft?: number): "calm" | "rising" | "over" {
  const limit = soft ?? hard;
  if (value >= limit) return "over";
  if (value >= limit * 0.6) return "rising";
  return "calm";
}
