import type { Map as MapLibreMap } from "maplibre-gl";
import { palette } from "../ui/palette";

const PIXEL_RATIO = 2;

interface Shape {
  id: string;
  width: number;
  length: number;
  fill: string;
  draw: (ctx: CanvasRenderingContext2D, w: number, h: number) => void;
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
}

const SHAPES: Shape[] = [
  {
    id: "vehicle-car",
    width: 7,
    length: 13,
    fill: palette.car,
    draw: (ctx, w, h) => {
      roundRect(ctx, 1, 1, w - 2, h - 2, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "rgba(8,12,18,0.55)";
      roundRect(ctx, 3, 5, w - 6, 5, 1.5);
      ctx.fill();
    },
  },
  {
    id: "vehicle-bus",
    width: 8,
    length: 26,
    fill: palette.bus,
    draw: (ctx, w, h) => {
      roundRect(ctx, 1, 1, w - 2, h - 2, 3);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "rgba(8,12,18,0.5)";
      for (let y = 8; y < h - 6; y += 8) ctx.fillRect(3, y, w - 6, 4);
    },
  },
  {
    id: "vehicle-truck",
    width: 8,
    length: 20,
    fill: palette.truck,
    draw: (ctx, w, h) => {
      roundRect(ctx, 1, 1, w - 2, 6, 2);
      ctx.fill();
      ctx.stroke();
      roundRect(ctx, 1, 8, w - 2, h - 9, 1);
      ctx.fill();
      ctx.stroke();
    },
  },
];

export function registerVehicleIcons(map: MapLibreMap): void {
  for (const shape of SHAPES) {
    if (map.hasImage(shape.id)) continue;
    const w = shape.width * PIXEL_RATIO;
    const h = shape.length * PIXEL_RATIO;
    const canvas = document.createElement("canvas");
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) continue;
    ctx.fillStyle = shape.fill;
    ctx.strokeStyle = "rgba(5,8,12,0.9)";
    ctx.lineWidth = 2;
    shape.draw(ctx, w, h);
    map.addImage(shape.id, ctx.getImageData(0, 0, w, h), { pixelRatio: PIXEL_RATIO });
  }
}

export const VEHICLE_ICON_BY_KIND = ["vehicle-car", "vehicle-bus", "vehicle-truck"] as const;
