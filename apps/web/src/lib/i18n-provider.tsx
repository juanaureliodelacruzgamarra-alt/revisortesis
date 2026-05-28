"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";

type Lang = "es" | "en";

type Translations = Record<string, Record<Lang, string>>;

const DICT: Translations = {
  "sidebar.title": { es: "Revisión académica con IA", en: "AI Academic Review" },
  "sidebar.logout": { es: "Cerrar sesión", en: "Log out" },
  "role.admin": { es: "Administrador", en: "Administrator" },
  "role.coordinator": { es: "Coordinador", en: "Coordinator" },
  "role.advisor": { es: "Asesor", en: "Advisor" },
  "role.student": { es: "Estudiante", en: "Student" },
  "nav.home": { es: "Inicio", en: "Home" },
  "nav.programs": { es: "Programas", en: "Programs" },
  "nav.users": { es: "Usuarios", en: "Users" },
  "nav.templates": { es: "Plantillas", en: "Templates" },
  "nav.submissions": { es: "Mis avances", en: "My submissions" },
  "nav.reviews": { es: "Revisiones", en: "Reviews" },
  "nav.rubrics": { es: "Rúbricas", en: "Rubrics" },
  "nav.plagiarism": { es: "Plagio", en: "Plagiarism" },
  "nav.citations": { es: "Citas", en: "Citations" },
  "nav.settings": { es: "Configuración", en: "Settings" },
  "nav.fine_tuning": { es: "Fine-tuning", en: "Fine-tuning" },
  "nav.orcid": { es: "ORCID", en: "ORCID" },
  "nav.dashboard": { es: "Dashboard", en: "Dashboard" },
  "nav.batch": { es: "Lotes", en: "Batch" },
  "theme.dark": { es: "Oscuro", en: "Dark" },
  "theme.light": { es: "Claro", en: "Light" },
  "lang.label": { es: "ES", en: "EN" },
};

interface I18nCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nCtx>({
  lang: "es",
  setLang: () => {},
  t: (k) => k,
});

export function useI18n() {
  return useContext(I18nContext);
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem("kimy-lang") as Lang) || "es";
    }
    return "es";
  });

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    localStorage.setItem("kimy-lang", l);
    document.documentElement.lang = l;
  }, []);

  const t = useCallback(
    (key: string) => DICT[key]?.[lang] ?? key,
    [lang],
  );

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  );
}
