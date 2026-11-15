import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { getHealthOptions } from "./api/@tanstack/react-query.gen";

export default function App() {
  const { t, i18n } = useTranslation();
  const health = useQuery({
    ...getHealthOptions(),
    refetchInterval: (q) => (q.state.data ? false : 3000),
  });

  const status = health.data
    ? t("health.ok")
    : health.isError
      ? t("health.waking")
      : t("health.checking");

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="font-serif text-2xl">{t("app.title")}</h1>
      <p>{t("app.tagline")}</p>
      <p role="status" className="font-mono">
        {status}
      </p>
      <div className="mt-4 flex gap-2">
        {(["en", "hi"] as const).map((lng) => (
          <button
            key={lng}
            type="button"
            className="rounded border border-line px-2 py-1"
            onClick={() => i18n.changeLanguage(lng)}
          >
            {t(`lang.${lng}`)}
          </button>
        ))}
      </div>
    </main>
  );
}
