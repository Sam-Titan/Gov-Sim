import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { getDistrictsOptions } from "@/api/@tanstack/react-query.gen";
import { formatNumber } from "@/lib/format";

const SOURCES = ["nfhs", "census", "income", "map"] as const;
const MISSING = ["chandigarh", "vidisha", "lakshadweep"] as const;
const LIMITS = ["survey", "range", "proxy", "census", "boundaries", "model"] as const;

export function About() {
  const { t, i18n } = useTranslation();
  const districts = useQuery(getDistrictsOptions());
  const noData = districts.data?.filter((d) => !d.has_data);
  const unmapped = noData?.filter((d) => d.reason === "unmapped").length;
  const n = (v: number) => formatNumber(v, i18n.language, 0);

  return (
    <div className="mx-auto grid max-w-4xl gap-6 p-4">
      <div>
        <h1 className="font-serif text-2xl">{t("about.title")}</h1>
        <p
          role="note"
          className="mt-2 rounded border border-warn p-3 text-sm font-semibold"
          data-testid="disclaimer"
        >
          {t("about.disclaimer")}
        </p>
      </div>

      <section aria-labelledby="ab-what" className="grid gap-2">
        <h2 id="ab-what" className="font-serif text-lg">
          {t("about.whatTitle")}
        </h2>
        <p className="text-sm">{t("about.what")}</p>
      </section>

      <section aria-labelledby="ab-sources" className="grid gap-3">
        <h2 id="ab-sources" className="font-serif text-lg">
          {t("about.sourcesTitle")}
        </h2>
        <ul className="grid gap-3">
          {SOURCES.map((s) => (
            <li key={s} className="rounded border border-line bg-surface p-3 text-sm">
              <p className="font-semibold">{t(`about.source.${s}.name`)}</p>
              <p>{t(`about.source.${s}.credit`)}</p>
              <p className="opacity-80">
                {t("about.licence")}: {t(`about.source.${s}.licence`)}
              </p>
            </li>
          ))}
        </ul>
        <p className="text-sm">{t("about.mapCredit")}</p>
      </section>

      <section aria-labelledby="ab-missing" className="grid gap-2">
        <h2 id="ab-missing" className="font-serif text-lg">
          {t("about.missingTitle")}
        </h2>
        <ul className="list-disc pl-5 text-sm">
          {MISSING.map((m) => (
            <li key={m}>{t(`about.missing.${m}`)}</li>
          ))}
          {noData && unmapped !== undefined && (
            <li>
              {t("about.missing.counts", {
                n: n(noData.length),
                total: n(districts.data?.length ?? 0),
                unmapped: n(unmapped),
              })}
            </li>
          )}
        </ul>
      </section>

      <section aria-labelledby="ab-limits" className="grid gap-2">
        <h2 id="ab-limits" className="font-serif text-lg">
          {t("about.limitsTitle")}
        </h2>
        <ul className="list-disc pl-5 text-sm">
          {LIMITS.map((l) => (
            <li key={l}>{t(`about.limit.${l}`)}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
