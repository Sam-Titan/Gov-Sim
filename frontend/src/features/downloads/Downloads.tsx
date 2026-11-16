import { useQuery } from "@tanstack/react-query";
import { Download, Printer } from "lucide-react";
import { useTranslation } from "react-i18next";
import { getReportOptions } from "@/api/@tanstack/react-query.gen";
import type { Inputs, SimulateResponse } from "@/api/types.gen";
import { type Cell, downloadCsv, toCsv, today } from "./csv";
import type { Meta } from "./rows";

const SIDE_KEYS = ["a", "b"];

const INPUTS: (keyof Inputs)[] = [
  "cash_benefit_inr",
  "document_count",
  "requires_bank_account",
  "application_burden",
  "benefit_immediacy",
];

/** Link (current URL, carries the scenario), today's date and the report's generated date. */
export function useMeta(): Meta {
  const report = useQuery({ ...getReportOptions(), staleTime: Infinity, retry: false });
  return {
    link: typeof window === "undefined" ? "" : window.location.href,
    date: today(),
    version: report.data?.generated ?? "",
  };
}

interface BarProps {
  /** Called on click; returns the CSV pieces, or null when there is nothing to save. */
  build: () => { header: string[]; rows: Cell[][] } | null;
  fileKey: "download.simulateFile" | "download.stateFile" | "download.compareFile";
  label?: "download.csv" | "download.csvState";
  print?: boolean;
}

export function DownloadBar({ build, fileKey, label = "download.csv", print = true }: BarProps) {
  const { t } = useTranslation();
  const data = build();
  return (
    <div className="flex flex-wrap gap-2 print:hidden">
      <button
        type="button"
        disabled={!data}
        className="flex items-center gap-1 rounded border border-line px-2 py-1 text-sm disabled:opacity-50"
        onClick={() => {
          const d = build();
          if (d) downloadCsv(`${t(fileKey)}-${today()}.csv`, toCsv(d.header, d.rows));
        }}
      >
        <Download className="size-4" aria-hidden="true" />
        {t(label)}
      </button>
      {print && (
        <button
          type="button"
          className="flex items-center gap-1 rounded border border-line px-2 py-1 text-sm"
          onClick={() => window.print()}
        >
          <Printer className="size-4" aria-hidden="true" />
          {t("download.print")}
        </button>
      )}
    </div>
  );
}

function SettingsList({ d }: { d: SimulateResponse }) {
  const { t, i18n } = useTranslation();
  const show = (v: number | boolean) =>
    typeof v === "boolean" ? t(v ? "sliders.yes" : "sliders.no") : v.toLocaleString(i18n.language);
  return (
    <ul className="text-sm">
      {INPUTS.map((k) => (
        <li key={k}>
          {t(`sliders.${k}`)}: {show(d.used_inputs[k])} ({show(d.real_inputs[k])})
        </li>
      ))}
    </ul>
  );
}

/** Only seen on paper: what was chosen, the scenario link, date, version and sources. */
export function PrintSummary({ items, meta }: { items: SimulateResponse[]; meta: Meta }) {
  const { t } = useTranslation();
  return (
    <section data-testid="print-summary" className="hidden print:block">
      <h2 className="font-serif text-xl">{t("print.title")}</h2>
      {items.map((d, i) => (
        <div key={SIDE_KEYS[i]} className="mt-2">
          <p className="font-semibold">
            {items.length > 1 ? `${t(i === 0 ? "print.sideA" : "print.sideB")}: ` : ""}
            {d.district}, {d.state}: {t(`scheme.${d.scheme}`)}
            {d.custom && d.policy_name ? ` (${d.policy_name})` : ""}
          </p>
          <p className="text-sm">{t("print.settings")}</p>
          <SettingsList d={d} />
        </div>
      ))}
      <p className="mt-2 break-all text-sm">
        {t("download.scenarioLink")}: {meta.link}
      </p>
      <p className="text-sm">
        {t("download.date")}: {meta.date}
      </p>
      {meta.version && (
        <p className="text-sm">
          {t("download.modelVersion")}: {meta.version}
        </p>
      )}
      <p className="mt-2 text-xs">{t("print.sources")}</p>
      <p className="text-xs">{t("about.disclaimer")}</p>
    </section>
  );
}
