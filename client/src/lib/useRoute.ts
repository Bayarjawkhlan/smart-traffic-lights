import { useCallback, useSyncExternalStore } from "react";

export type Page = "live" | "experiments" | "vision" | "about";
export interface Route {
  page: Page;
  site: string | null;
}

const PAGES: readonly Page[] = ["live", "experiments", "vision", "about"];

function parse(hash: string): Route {
  const [first, second] = hash.replace(/^#\/?/, "").split("/");
  const page = PAGES.find((p) => p === first) ?? "live";
  return { page, site: page === "live" && second ? decodeURIComponent(second) : null };
}

const subscribe = (onChange: () => void) => {
  window.addEventListener("hashchange", onChange);
  return () => window.removeEventListener("hashchange", onChange);
};

export function useRoute(): [Route, (route: Route) => void] {
  const hash = useSyncExternalStore(subscribe, () => window.location.hash);
  const navigate = useCallback((route: Route) => {
    window.location.hash = route.site ? `/${route.page}/${encodeURIComponent(route.site)}` : `/${route.page}`;
  }, []);
  return [parse(hash), navigate];
}
