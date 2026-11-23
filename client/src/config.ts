const trimSlash = (url: string) => url.replace(/\/+$/, "");

export const SIM_URL = trimSlash(import.meta.env.VITE_SIM_URL ?? "http://localhost:8000");
export const VISION_URL = trimSlash(import.meta.env.VITE_VISION_URL ?? "http://localhost:8001");

export const toWebSocketUrl = (httpUrl: string, path: string) => httpUrl.replace(/^http/, "ws") + path;
