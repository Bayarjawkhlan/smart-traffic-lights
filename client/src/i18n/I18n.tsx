import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { dictionaries, type Language, type StringKey } from "./strings";

type Vars = Record<string, string | number>;

export interface I18n {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: StringKey, vars?: Vars) => string;
}

const I18nContext = createContext<I18n | null>(null);
const STORAGE_KEY = "corridor.lang";

function initialLanguage(): Language {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "en" || stored === "mn") return stored;
  } catch {
    // storage unavailable
  }
  return navigator.language.toLowerCase().startsWith("mn") ? "mn" : "en";
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>(initialLanguage);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.title = dictionaries[lang].appName;
  }, [lang]);

  const setLang = useCallback((next: Language) => {
    setLangState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // storage unavailable
    }
  }, []);

  const t = useCallback(
    (key: StringKey, vars?: Vars) => {
      const template = dictionaries[lang][key];
      if (!vars) return template;
      return template.replace(/\{(\w+)\}/g, (match, name: string) => (name in vars ? String(vars[name]) : match));
    },
    [lang],
  );

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18n {
  const context = useContext(I18nContext);
  if (!context) throw new Error("useI18n must be used inside I18nProvider");
  return context;
}
