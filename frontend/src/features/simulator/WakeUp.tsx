import { useTranslation } from "react-i18next";

export function WakeUp() {
  const { t } = useTranslation();
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-xl flex-col items-center justify-center gap-3 p-6 text-center">
      <div
        className="size-8 animate-spin rounded-full border-2 border-line border-t-accent"
        aria-hidden="true"
      />
      <h1 role="status" className="font-serif text-xl">
        {t("wake.title")}
      </h1>
      <p className="text-sm opacity-80">{t("wake.body")}</p>
    </main>
  );
}
