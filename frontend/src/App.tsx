import { useQuery } from "@tanstack/react-query";
import { Moon, Sun, SunMoon } from "lucide-react";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Route, Routes } from "react-router-dom";
import { getHealthOptions } from "./api/@tanstack/react-query.gen";
import { Simulator } from "./features/simulator/Simulator";
import { WakeUp } from "./features/simulator/WakeUp";
import { applyTheme, type Theme, useUi } from "./store/ui";

const THEMES: Theme[] = ["system", "light", "dark"];
const ICON = { system: SunMoon, light: Sun, dark: Moon } as const;

function Header() {
  const { t, i18n } = useTranslation();
  const { theme, setTheme } = useUi();
  const Icon = ICON[theme];
  const next = THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length] ?? "system";
  return (
    <header className="border-b border-line bg-surface">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 p-4">
        <div>
          <h1 className="font-serif text-2xl">{t("app.title")}</h1>
          <p className="text-sm opacity-80">{t("app.tagline")}</p>
        </div>
        <div className="flex items-center gap-2">
          <fieldset className="flex gap-1">
            <legend className="sr-only">{t("lang.switch")}</legend>
            {(["en", "hi"] as const).map((lng) => (
              <button
                key={lng}
                type="button"
                aria-pressed={i18n.language === lng}
                className="rounded border border-line px-2 py-1 text-sm aria-pressed:bg-accent aria-pressed:text-surface"
                onClick={() => i18n.changeLanguage(lng)}
              >
                {t(`lang.${lng}`)}
              </button>
            ))}
          </fieldset>
          <button
            type="button"
            className="flex items-center gap-1 rounded border border-line px-2 py-1 text-sm"
            aria-label={`${t("theme.label")}: ${t(`theme.${theme}`)}`}
            onClick={() => setTheme(next)}
          >
            <Icon className="size-4" aria-hidden="true" />
            {t(`theme.${theme}`)}
          </button>
        </div>
      </div>
    </header>
  );
}

export default function App() {
  const { i18n } = useTranslation();
  const theme = useUi((s) => s.theme);
  const health = useQuery({
    ...getHealthOptions(),
    refetchInterval: (q) => (q.state.data ? false : 3000),
    retry: false,
  });

  useEffect(() => {
    applyTheme(theme);
    if (theme !== "system") return;
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!mq) return;
    const on = () => applyTheme("system");
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, [theme]);
  useEffect(() => {
    document.documentElement.lang = i18n.language;
  }, [i18n.language]);

  return (
    <>
      <Header />
      {health.data ? (
        <Routes>
          <Route path="/" element={<Simulator />} />
        </Routes>
      ) : (
        <WakeUp />
      )}
    </>
  );
}
