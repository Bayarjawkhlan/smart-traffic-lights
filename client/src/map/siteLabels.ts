import type { Map as MapLibreMap } from "maplibre-gl";
import type { LngLat } from "../api/types";

const PIN_RADIUS = 9;
const QUIET_PIN_RADIUS = 5;
const OWN_GAP = 4;
// larger than OWN_GAP, so a name is always nearest to its own pin
const OTHER_GAP = 6;
const NAME_GAP = 4;
const EDGE = 6;

const FORMS = ["line", "wrap", "line-alt", "wrap-alt"] as const;
type Form = (typeof FORMS)[number];

interface Box {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

interface Label {
  center: LngLat;
  element: HTMLElement;
  sizes: Record<Form, { width: number; height: number }>;
}

interface Placement {
  form: Form;
  box: Box;
}

const overlap = (a: Box, b: Box, gap: number) =>
  a.left < b.right + gap && b.left < a.right + gap && a.top < b.bottom + gap && b.top < a.bottom + gap;

const clamp = (value: number, low: number, high: number) => Math.min(Math.max(value, low), high);

function splitName(name: string): [string, string] {
  const slash = name.indexOf(" / ");
  if (slash > 0) return [name.slice(0, slash + 2), name.slice(slash + 3)];
  const middle = name.length / 2;
  let cut = -1;
  for (let i = name.indexOf(" "); i >= 0; i = name.indexOf(" ", i + 1)) {
    if (cut < 0 || Math.abs(i - middle) < Math.abs(cut - middle)) cut = i;
  }
  return cut < 0 ? [name, ""] : [name.slice(0, cut), name.slice(cut + 1)];
}

export class SiteLabels {
  private map: MapLibreMap;
  private layer = document.createElement("div");
  private obstacles: () => Iterable<Element>;
  private obstacleBoxes: Box[] = [];
  private labels = new Map<string, Label>();
  private order: string[] = [];
  private selected: string | null = null;
  private active: string | null = null;

  constructor(map: MapLibreMap, obstacles: () => Iterable<Element>) {
    this.map = map;
    this.obstacles = obstacles;
    this.layer.className = "site-names";
    this.layer.setAttribute("aria-hidden", "true");
    map.getCanvasContainer().append(this.layer);
    map.on("move", this.layout);
    map.on("resize", this.measure);
    document.fonts.addEventListener("loadingdone", this.measure);
  }

  add(id: string, center: LngLat, pin: HTMLElement): void {
    const element = document.createElement("div");
    element.className = "site-name";
    element.dataset.site = id;
    element.innerHTML = `<span class="site-name__main"><span></span> <span></span></span><span class="site-name__alt"></span>`;
    this.layer.append(element);
    const none = { width: 0, height: 0 };
    this.labels.set(id, { center, element, sizes: { line: none, wrap: none, "line-alt": none, "wrap-alt": none } });
    const activate = () => this.activate(id);
    const release = () => this.active === id && this.activate(null);
    pin.addEventListener("pointerenter", activate);
    pin.addEventListener("pointerleave", release);
    pin.addEventListener("focus", () => pin.matches(":focus-visible") && activate());
    pin.addEventListener("blur", release);
  }

  setNames(names: { id: string; name: string; alt: string }[]): void {
    for (const { id, name, alt } of names) {
      const element = this.labels.get(id)?.element;
      if (!element) continue;
      const [first, second] = element.querySelectorAll(".site-name__main > span");
      [first!.textContent, second!.textContent] = splitName(name);
      element.querySelector(".site-name__alt")!.textContent = alt;
    }
    this.measure();
  }

  show(order: string[], selected: string | null): void {
    this.order = order;
    this.selected = selected;
    this.measure();
  }

  destroy(): void {
    this.map.off("move", this.layout);
    this.map.off("resize", this.measure);
    document.fonts.removeEventListener("loadingdone", this.measure);
    this.layer.remove();
  }

  private activate(id: string | null): void {
    this.active = id;
    this.layout();
  }

  private measure = (): void => {
    const origin = this.map.getContainer().getBoundingClientRect();
    this.obstacleBoxes = [...this.obstacles()].map((element) => {
      const box = element.getBoundingClientRect();
      return { left: box.left - origin.left, right: box.right - origin.left, top: box.top - origin.top, bottom: box.bottom - origin.top };
    });
    for (const form of FORMS) {
      for (const { element } of this.labels.values()) element.dataset.form = form;
      for (const label of this.labels.values()) {
        const { width, height } = label.element.getBoundingClientRect();
        label.sizes[form] = { width: Math.ceil(width), height: Math.ceil(height) };
      }
    }
    this.layout();
  };

  private layout = (): void => {
    const pins = new Map([...this.labels].map(([id, label]) => [id, this.map.project(label.center)]));
    const pinBoxes = new Map(
      [...pins].map(([id, { x, y }]) => {
        const quiet = this.order.length > 0 && !this.order.includes(id) && id !== this.selected && id !== this.active;
        const radius = quiet ? QUIET_PIN_RADIUS : PIN_RADIUS;
        return [id, { left: x - radius, right: x + radius, top: y - radius, bottom: y + radius }];
      }),
    );

    const find = (id: string, forms: readonly Form[], taken: Iterable<Placement>): Placement | null => {
      const others = [...taken];
      for (const form of forms) {
        for (const box of this.positions(id, form, pins.get(id)!)) {
          if (!this.inView(box)) continue;
          if (others.some((other) => overlap(box, other.box, NAME_GAP))) continue;
          if ([...pinBoxes].some(([other, pin]) => other !== id && overlap(box, pin, OTHER_GAP))) continue;
          return { form, box };
        }
      }
      return null;
    };

    const arrange = (forms: readonly Form[]) => {
      const placed = new Map<string, Placement>();
      for (const id of new Set(this.selected ? [this.selected, ...this.order] : this.order)) {
        if (!this.labels.has(id)) continue;
        const place = find(id, id === this.selected ? ["line-alt", "wrap-alt", ...forms] : forms, placed.values());
        if (place) placed.set(id, place);
      }
      return placed;
    };

    const single = arrange(["line", "wrap"]);
    const wrapped = single.size < this.order.length ? arrange(["wrap", "line"]) : single;
    const placed = wrapped.size > single.size ? wrapped : single;

    if (this.active && !placed.has(this.active)) {
      const forms: Form[] = ["line", "wrap"];
      const beside = find(this.active, forms, placed.values());
      const over = beside ?? find(this.active, forms, []);
      if (over) {
        // names already shown may give way but must not move, or they would jump as the pointer passes pins
        for (const [id, other] of placed) if (overlap(over.box, other.box, NAME_GAP)) placed.delete(id);
        placed.set(this.active, over);
      }
    }

    for (const [id, { element }] of this.labels) {
      const place = placed.get(id);
      element.classList.toggle("is-shown", place !== undefined);
      if (!place) continue;
      element.dataset.form = place.form;
      element.style.transform = `translate(${place.box.left}px, ${place.box.top}px)`;
    }
  };

  private positions(id: string, form: Form, pin: { x: number; y: number }): Box[] {
    const { width, height } = this.labels.get(id)!.sizes[form];
    const away = PIN_RADIUS + OWN_GAP;
    const reach = Math.max(0, width / 2 - PIN_RADIUS);
    const fit = clamp(0, EDGE + width / 2 - pin.x, this.map.getContainer().clientWidth - EDGE - width / 2 - pin.x);
    const tops = [pin.y - away - height, pin.y + away];
    if (this.order.indexOf(id) % 2 === 1) tops.reverse();
    const shifts = [clamp(fit, -reach, reach), reach / 2, -reach / 2, reach, -reach];
    const at = (left: number, top: number): Box => {
      const x = Math.round(left);
      const y = Math.round(top);
      return { left: x, top: y, right: x + width, bottom: y + height };
    };
    const centred = (shift: number) => tops.map((top) => at(pin.x + shift - width / 2, top));
    return [...shifts.flatMap(centred), at(pin.x + away, pin.y - height / 2), at(pin.x - away - width, pin.y - height / 2)];
  }

  private inView(box: Box): boolean {
    const { clientWidth, clientHeight } = this.map.getContainer();
    if (box.left < 0 || box.right > clientWidth || box.top < 0 || box.bottom > clientHeight) return false;
    return !this.obstacleBoxes.some((other) => overlap(box, other, 0));
  }
}
