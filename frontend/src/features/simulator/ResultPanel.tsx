import { AlertTriangle, ArrowDown, ArrowUp, Info } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { SimulateResponse, WarningCode } from "@/api/types.gen";
import { formatNumber, rangeEnds, signed } from "@/lib/format";
import { cn } from "@/lib/utils";

export type ResultError = "no_data" | "invalid" | "other";

interface Props {
  data?: SimulateResponse;
  updating: boolean;
  error: ResultError | null;
  noDataReason?: string | null;
  ready: boolean;
}

const SERIOUS: WarningCode[] = ["low_confidence", "out_of_range", "new_policy", "partial_data"];

export function ResultPanel({ data, updating, error, noDataReason, ready }: Props) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const n = (v: number, d = 1) => formatNumber(v, lang, d);

  let body: React.ReactNode;
  if (error === "no_data") {
    body = (
      <p role="alert">
        {t("result.noData")}{" "}
        {noDataReason ? t(`noDataReason.${noDataReason}`, { defaultValue: "" }) : null}
      </p>
    );
  } else if (!ready) {
    body = <p className="opacity-80">{t("result.empty")}</p>;
  } else if (!data) {
    body = (
      <p role={error ? "alert" : "status"}>
        {error === "invalid"
          ? t("result.invalid")
          : error
            ? t("result.error")
            : t("result.updating")}
      </p>
    );
  } else {
    const r = data.result;
    const [low, high] = rangeEnds(r.low, r.high);
    body = (
      <div className={cn("grid gap-4", updating && "opacity-60")} aria-busy={updating}>
        <div>
          <p className="text-sm font-semibold">{t(`metric.${data.metric_base}`)}</p>
          <p className="font-mono text-3xl" data-testid="range">
            {t("result.range", { low: n(low, 0), high: n(high, 0) })}
          </p>
          <p className="text-sm">
            <span className="tabular-nums">{t("result.middle", { point: n(r.point) })}</span>
            <span className="ml-2 opacity-80">{t("result.rangeNote")}</span>
          </p>
          {updating && (
            <p role="status" className="text-xs opacity-80">
              {t("result.updating")}
            </p>
          )}
        </div>

        <ul className="grid gap-1 text-sm">
          <li className="tabular-nums">{t("result.fromData", { level: n(r.level) })}</li>
          <li className="tabular-nums">
            {t("result.fromModel", {
              central: signed(r.changes.central, lang),
              weak: signed(r.changes.weak, lang),
              strong: signed(r.changes.strong, lang),
            })}
          </li>
        </ul>

        <div>
          <h3 className="font-serif text-base">{t("result.reasonsTitle")}</h3>
          {data.reasons.length === 0 ? (
            <p className="text-sm opacity-80">{t("result.noReasons")}</p>
          ) : (
            <ol className="mt-1 grid gap-1 text-sm">
              {data.reasons.map((x) => (
                <li key={x.term} className="flex items-center gap-2">
                  {x.direction === "up" ? (
                    <ArrowUp className="size-4 text-good" aria-hidden="true" />
                  ) : (
                    <ArrowDown className="size-4 text-alert" aria-hidden="true" />
                  )}
                  <span>
                    <strong>{t(`reason.${x.term}`, { defaultValue: x.term })}</strong>{" "}
                    {t(x.direction === "up" ? "reason.up" : "reason.down", {
                      pp: n(Math.abs(x.effect_pp)),
                    })}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </div>

        {data.warnings.length > 0 && (
          <div>
            <h3 className="font-serif text-base">{t("result.warningsTitle")}</h3>
            <ul className="mt-1 grid gap-2 text-sm">
              {data.warnings.map((w) => {
                const serious = SERIOUS.includes(w);
                const Icon = serious ? AlertTriangle : Info;
                return (
                  <li
                    key={w}
                    className={cn(
                      "flex gap-2 rounded border p-2",
                      serious ? "border-warn" : "border-line",
                    )}
                  >
                    <Icon
                      className={cn(
                        "mt-0.5 size-4 shrink-0",
                        serious ? "text-warn" : "text-accent",
                      )}
                      aria-hidden="true"
                    />
                    <span>{t(`warning.${w}`)}</span>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </div>
    );
  }

  return (
    <section aria-labelledby="result-title" className="rounded border border-line bg-surface p-4">
      <h2 id="result-title" className="mb-2 font-serif text-lg">
        {t("result.title")}
      </h2>
      {body}
    </section>
  );
}
