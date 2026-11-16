import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getDistrictsOptions, getReportOptions } from "@/api/@tanstack/react-query.gen";
import type { DistrictOut } from "@/api/types.gen";
import { formatNumber, signed } from "@/lib/format";
import { agentWins, type ParsedReport, parseReport, SCHEME_ORDER, SETS } from "./reportData";

type Fmt = (v: number, digits?: number) => string;

function Panel({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section aria-labelledby={id} className="grid gap-3 rounded border border-line bg-surface p-4">
      <h2 id={id} className="font-serif text-lg">
        {title}
      </h2>
      {children}
    </section>
  );
}

function Num({ children }: { children: React.ReactNode }) {
  return <td className="px-2 py-1 text-right font-mono tabular-nums">{children}</td>;
}

function Th({ children, right }: { children: React.ReactNode; right?: boolean }) {
  return (
    <th scope="col" className={`px-2 py-1 font-semibold ${right ? "text-right" : "text-left"}`}>
      {children}
    </th>
  );
}

function Table({ caption, children }: { caption: string; children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[34rem] border-collapse text-sm">
        <caption className="sr-only">{caption}</caption>
        {children}
      </table>
    </div>
  );
}

const rowCls = "border-t border-line";

/** The report stores this label in English; show the translated phrase when we know it. */
function deffLabel(label: string, t: (k: string) => string): string {
  return label === "assumed by team" ? t("sliders.assumed") : label;
}

function MaeChart({
  rows,
  label,
}: {
  rows: { name: string; agent: number; gbm: number; naive: number }[];
  label: string;
}) {
  const { t } = useTranslation();
  return (
    <div role="img" aria-label={label} className="h-64 w-full text-xs">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} margin={{ top: 8, right: 8, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="var(--color-line)" vertical={false} />
          <XAxis dataKey="name" stroke="var(--color-ink-muted)" />
          <YAxis
            stroke="var(--color-ink-muted)"
            label={{ value: t("report.maeAxis"), angle: -90, position: "insideLeft" }}
          />
          <Tooltip
            contentStyle={{
              background: "var(--color-surface)",
              border: "1px solid var(--color-line)",
            }}
          />
          <Legend
            formatter={(v: string) => <span style={{ color: "var(--color-ink)" }}>{v}</span>}
          />
          <Bar
            isAnimationActive={false}
            dataKey="agent"
            name={t("report.agent")}
            fill="var(--color-agent)"
          />
          <Bar
            isAnimationActive={false}
            dataKey="gbm"
            name={t("report.gbm")}
            fill="var(--color-gbm)"
          />
          <Bar
            isAnimationActive={false}
            dataKey="naive"
            name={t("report.naive")}
            fill="var(--color-ink-faint)"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function AccuracyTable({ title, data, n }: { title: string; data: ParsedReport["losto"]; n: Fmt }) {
  const { t } = useTranslation();
  return (
    <Table caption={title}>
      <thead>
        <tr>
          <Th>{t("report.test")}</Th>
          <Th right>{t("report.agent")}</Th>
          <Th right>{t("report.gbm")}</Th>
          <Th right>{t("report.naive")}</Th>
        </tr>
      </thead>
      <tbody>
        <tr className={rowCls}>
          <th scope="row" className="px-2 py-1 text-left font-normal">
            {title}
          </th>
          <Num>{n(data.weighted_mean.agent_mae)}</Num>
          <Num>{n(data.weighted_mean.gbm_mae)}</Num>
          <Num>{n(data.weighted_mean.naive_mae)}</Num>
        </tr>
      </tbody>
    </Table>
  );
}

function Weaknesses({
  r,
  districts,
  n,
}: {
  r: ParsedReport;
  districts: DistrictOut[] | undefined;
  n: Fmt;
}) {
  const { t } = useTranslation();
  const jsy = r.bands.jsy;
  const noData = districts?.filter((d) => !d.has_data);
  const unmapped = noData?.filter((d) => d.reason === "unmapped").length;
  const items: string[] = [
    t("report.weak.agentNotBetter", {
      agent: n(r.losto.weighted_mean.agent_mae),
      gbm: n(r.losto.weighted_mean.gbm_mae),
      wins: agentWins(r.losto),
      folds: r.losto.folds.length,
    }),
    t("report.weak.loso", { schemes: r.loso.folds.length }),
    t("report.weak.fixedBetas"),
    t("report.weak.deff", { deff: n(r.deff.value, 1), label: deffLabel(r.deff.label, t) }),
    jsy
      ? t("report.weak.jsyBirths", {
          median: n(jsy.median_half_width_pp, 2),
          max: n(jsy.max_half_width_pp, 2),
        })
      : t("report.weak.jsyBirthsNoNumbers"),
    t("report.weak.partial", { n: n(r.raw.baseline_partial_rows, 0) }),
    noData && unmapped !== undefined
      ? t("report.weak.noData", {
          n: n(noData.length, 0),
          total: n(districts?.length ?? 0, 0),
          unmapped: n(unmapped, 0),
        })
      : t("report.weak.noDataLoading"),
    t("report.weak.survey"),
    t("report.weak.boundaries"),
  ];
  return (
    <ul className="grid list-disc gap-1 pl-5 text-sm">
      {items.map((x) => (
        <li key={x}>{x}</li>
      ))}
    </ul>
  );
}

export function ReportBody({
  r,
  districts,
}: {
  r: ParsedReport;
  districts: DistrictOut[] | undefined;
}) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const n: Fmt = (v, d = 1) => formatNumber(v, lang, d);
  const sch = (code: string) => t(`scheme.${code}`, { defaultValue: code });
  const schemes = SCHEME_ORDER.filter((s) => r.loso.folds.some((f) => f.name === s));
  const losoRows = r.loso.folds.map((f) => ({
    name: t(`scheme.${f.name}`, { defaultValue: f.name }).split(" (")[0] ?? f.name,
    agent: round1(f.agent_mae),
    gbm: round1(f.gbm_mae),
    naive: round1(f.naive_mae),
  }));
  const lostoMean = r.losto.weighted_mean;
  const lostoRows = [
    {
      name: t("report.losto"),
      agent: round1(lostoMean.agent_mae),
      gbm: round1(lostoMean.gbm_mae),
      naive: round1(lostoMean.naive_mae),
    },
  ];
  const beats = r.raw.agent_model_beats_gbm;

  return (
    <div className="grid gap-6">
      <p
        role="status"
        className={`rounded border p-3 text-sm ${beats ? "border-good" : "border-warn"}`}
      >
        <strong>{t(beats ? "report.beats" : "report.notBeats")}</strong> {t("report.role")}
      </p>

      <Panel id="rep-data" title={t("report.dataTitle")}>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm sm:grid-cols-4">
          {[
            ["report.districts", r.raw.n_districts],
            ["report.rows", r.raw.n_rows],
            ["report.agents", r.raw.n_agents],
            ["report.partialRows", r.raw.baseline_partial_rows],
          ].map(([k, v]) => (
            <div key={String(k)}>
              <dt className="opacity-80">{t(String(k))}</dt>
              <dd className="font-mono tabular-nums">{n(Number(v), 0)}</dd>
            </div>
          ))}
          {districts && (
            <div>
              <dt className="opacity-80">{t("report.noDataDistricts")}</dt>
              <dd className="font-mono tabular-nums">
                {n(districts.filter((d) => !d.has_data).length, 0)} / {n(districts.length, 0)}
              </dd>
            </div>
          )}
        </dl>
      </Panel>

      <Panel id="rep-acc" title={t("report.accTitle")}>
        <p className="text-sm opacity-80">{t("report.accIntro")}</p>
        <AccuracyTable title={t("report.losto")} data={r.losto} n={n} />
        <MaeChart rows={lostoRows} label={t("report.losto")} />
        <p className="text-sm">
          {t("report.wins", { wins: agentWins(r.losto), folds: r.losto.folds.length })}
        </p>
        <details className="text-sm">
          <summary className="cursor-pointer">{t("report.perState")}</summary>
          <Table caption={t("report.perState")}>
            <thead>
              <tr>
                <Th>{t("report.state")}</Th>
                <Th right>{t("report.nRows")}</Th>
                <Th right>{t("report.agent")}</Th>
                <Th right>{t("report.gbm")}</Th>
                <Th right>{t("report.naive")}</Th>
              </tr>
            </thead>
            <tbody>
              {r.losto.folds.map((f) => (
                <tr key={f.name} className={rowCls}>
                  <th scope="row" className="px-2 py-1 text-left font-normal">
                    {f.name}
                  </th>
                  <Num>{n(f.n, 0)}</Num>
                  <Num>{n(f.agent_mae)}</Num>
                  <Num>{n(f.gbm_mae)}</Num>
                  <Num>{n(f.naive_mae)}</Num>
                </tr>
              ))}
            </tbody>
          </Table>
        </details>

        <h3 className="mt-2 font-serif text-base">{t("report.losoTitle")}</h3>
        <p className="text-sm opacity-80">{t("report.losoNote", { schemes: schemes.length })}</p>
        <Table caption={t("report.losoTitle")}>
          <thead>
            <tr>
              <Th>{t("picker.scheme")}</Th>
              <Th right>{t("report.agent")}</Th>
              <Th right>{t("report.gbm")}</Th>
              <Th right>{t("report.naive")}</Th>
            </tr>
          </thead>
          <tbody>
            {r.loso.folds.map((f) => (
              <tr key={f.name} className={rowCls}>
                <th scope="row" className="px-2 py-1 text-left font-normal">
                  {sch(f.name)}
                </th>
                <Num>{n(f.agent_mae)}</Num>
                <Num>{n(f.gbm_mae)}</Num>
                <Num>{n(f.naive_mae)}</Num>
              </tr>
            ))}
            <tr className={`${rowCls} font-semibold`}>
              <th scope="row" className="px-2 py-1 text-left">
                {t("report.mean")}
              </th>
              <Num>{n(r.loso.weighted_mean.agent_mae)}</Num>
              <Num>{n(r.loso.weighted_mean.gbm_mae)}</Num>
              <Num>{n(r.loso.weighted_mean.naive_mae)}</Num>
            </tr>
          </tbody>
        </Table>
        <MaeChart rows={losoRows} label={t("report.losoTitle")} />
      </Panel>

      <Panel id="rep-betas" title={t("report.betaTitle")}>
        <p className="text-sm opacity-80">{t("report.betaIntro")}</p>
        <BetaTable r={r} n={n} />
      </Panel>

      <Panel id="rep-rec" title={t("report.recTitle")}>
        <p className="text-sm opacity-80">{t("report.recIntro")}</p>
        <Table caption={t("report.recTitle")}>
          <thead>
            <tr>
              <Th>{t("report.noise")}</Th>
              <Th>{t("report.term")}</Th>
              <Th right>{t("report.true")}</Th>
              <Th right>{t("report.est")}</Th>
              <Th right>{t("report.err")}</Th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(r.recovery).flatMap(([noise, terms]) =>
              Object.entries(terms).map(([term, v]) => (
                <tr key={`${noise}-${term}`} className={rowCls}>
                  <td className="px-2 py-1 font-mono">
                    {noise.replace("noise_", "").replace("pp", " pp")}
                  </td>
                  <td className="px-2 py-1 font-mono">{term}</td>
                  <Num>{n(v.true, 3)}</Num>
                  <Num>{n(v.est, 3)}</Num>
                  <Num>{signed(v.err, lang, 3)}</Num>
                </tr>
              )),
            )}
          </tbody>
        </Table>
      </Panel>

      <Panel id="rep-band" title={t("report.bandTitle")}>
        <p className="text-sm">
          {t("report.deff", { value: n(r.deff.value, 1), label: deffLabel(r.deff.label, t) })}
        </p>
        <Table caption={t("report.bandTitle")}>
          <thead>
            <tr>
              <Th>{t("picker.scheme")}</Th>
              <Th right>{t("report.bandMedian")}</Th>
              <Th right>{t("report.bandMax")}</Th>
              <Th right>{t("report.bandWide")}</Th>
              <Th right>{t("report.gbmBand")}</Th>
            </tr>
          </thead>
          <tbody>
            {SCHEME_ORDER.filter((s) => r.bands[s]).map((s) => {
              const b = r.bands[s];
              const g = r.gbmBands[s];
              return b ? (
                <tr key={s} className={rowCls}>
                  <th scope="row" className="px-2 py-1 text-left font-normal">
                    {sch(s)}
                  </th>
                  <Num>±{n(b.median_half_width_pp, 2)}</Num>
                  <Num>±{n(b.max_half_width_pp, 2)}</Num>
                  <Num>{n(100 * b.share_over_30pp_wide_at_real_settings, 0)}%</Num>
                  <Num>{g ? `${signed(g.p10, lang, 1)} / ${signed(g.p90, lang, 1)}` : "—"}</Num>
                </tr>
              ) : null;
            })}
          </tbody>
        </Table>
        <p className="text-xs opacity-80">{t("report.bandNote")}</p>
      </Panel>

      <Panel id="rep-sanity" title={t("report.sanityTitle")}>
        <p className="text-sm opacity-80">{t("report.sanityIntro")}</p>
        <SanityTable r={r} />
      </Panel>

      <Panel id="rep-weak" title={t("report.weakTitle")}>
        <Weaknesses r={r} districts={districts} n={n} />
      </Panel>
    </div>
  );
}

function round1(v: number): number {
  return Math.round(v * 10) / 10;
}

function BetaTable({ r, n }: { r: ParsedReport; n: Fmt }) {
  const { t } = useTranslation();
  const fixedTerms = Array.from(new Set(Object.values(r.fixed).flatMap((s) => Object.keys(s))));
  const fittedTerms = Array.from(new Set(Object.values(r.fitted).flatMap((s) => Object.keys(s))));
  return (
    <Table caption={t("report.betaTitle")}>
      <thead>
        <tr>
          <Th>{t("report.term")}</Th>
          <Th>{t("report.source")}</Th>
          {SETS.map((s) => (
            <Th key={s} right>
              {t(`report.set.${s}`)}
            </Th>
          ))}
        </tr>
      </thead>
      <tbody>
        {fixedTerms.map((term) => (
          <tr key={`f-${term}`} className={rowCls}>
            <td className="px-2 py-1 font-mono">{term}</td>
            <td className="px-2 py-1">{t("report.fixed")}</td>
            {SETS.map((s) => (
              <Num key={s}>{r.fixed[s]?.[term] === undefined ? "—" : n(r.fixed[s][term], 2)}</Num>
            ))}
          </tr>
        ))}
        {fittedTerms.map((term) => (
          <tr key={`t-${term}`} className={rowCls}>
            <td className="px-2 py-1 font-mono">{term}</td>
            <td className="px-2 py-1">{t("report.fitted")}</td>
            {SETS.map((s) => (
              <Num key={s}>{r.fitted[s]?.[term] === undefined ? "—" : n(r.fitted[s][term], 2)}</Num>
            ))}
          </tr>
        ))}
      </tbody>
    </Table>
  );
}

function SanityTable({ r }: { r: ParsedReport }) {
  const { t, i18n } = useTranslation();
  const schemes = SCHEME_ORDER.filter((s) => r.sanity[s]);
  const first = schemes[0];
  const rows = first ? Object.keys(r.sanity[first] ?? {}) : [];
  return (
    <Table caption={t("report.sanityTitle")}>
      <thead>
        <tr>
          <Th>{t("report.change")}</Th>
          {schemes.map((s) => (
            <Th key={s} right>
              {t(`scheme.${s}`, { defaultValue: s }).split(" (")[0]}
              <span className="block text-xs font-normal opacity-70">
                {SETS.map((x) => t(`report.setShort.${x}`)).join(" / ")}
              </span>
            </Th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row} className={rowCls}>
            <th scope="row" className="px-2 py-1 text-left font-normal">
              {t(`report.sanity.${row}`, { defaultValue: row })}
            </th>
            {schemes.map((s) => {
              const c = r.sanity[s]?.[row];
              const vals = SETS.map((x) => (c ? c[x] : undefined));
              const nums = vals.filter((v): v is number => typeof v === "number");
              const none = nums.length === SETS.length && nums.every((v) => v === 0);
              return (
                <Num key={s}>
                  {none
                    ? t("report.alreadyRequired")
                    : nums.length === SETS.length
                      ? nums.map((v) => signed(v, i18n.language)).join(" / ")
                      : "—"}
                </Num>
              );
            })}
          </tr>
        ))}
      </tbody>
    </Table>
  );
}

export function Report() {
  const { t } = useTranslation();
  const report = useQuery({ ...getReportOptions(), retry: false });
  const districts = useQuery(getDistrictsOptions());
  const parsedReport = report.data ? parseReport(report.data) : null;
  return (
    <div className="mx-auto grid max-w-5xl gap-6 p-4">
      <div>
        <h1 className="font-serif text-2xl">{t("report.title")}</h1>
        <p className="text-sm opacity-80">{t("report.intro")}</p>
      </div>
      {report.isError || (report.data && !parsedReport) ? (
        <p role="alert">{t("report.loadError")}</p>
      ) : parsedReport ? (
        <ReportBody r={parsedReport} districts={districts.data} />
      ) : (
        <p role="status">{t("picker.loading")}</p>
      )}
    </div>
  );
}
