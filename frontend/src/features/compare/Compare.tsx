import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { type SetURLSearchParams, useSearchParams } from "react-router-dom";
import {
  compareOptions,
  getDistrictsOptions,
  getSchemesOptions,
  getStatesOptions,
} from "@/api/@tanstack/react-query.gen";
import type { CompareResponse, SchemeOut } from "@/api/types.gen";
import { Switch } from "@/components/ui/switch";
import { CustomPolicy, type PolicyDraft } from "@/features/custom-policy/CustomPolicy";
import { DownloadBar, PrintSummary, useMeta } from "@/features/downloads/Downloads";
import { compareCsv } from "@/features/downloads/rows";
import { Pickers, SchemePicker } from "@/features/simulator/Pickers";
import { ResultBody } from "@/features/simulator/ResultPanel";
import { Sliders } from "@/features/simulator/Sliders";
import { signed } from "@/lib/format";
import { type Overrides, type Policy, parsePolicy, toSetting, writePolicy } from "@/lib/scenario";

type Side = "a" | "b";

function readParams(p: URLSearchParams) {
  return {
    state: p.get("state") || null,
    district: p.get("district") || null,
    a: parsePolicy(p, "a_"),
    b: parsePolicy(p, "b_"),
  };
}

type CompareScenario = ReturnType<typeof readParams>;

function writeParams(s: CompareScenario): URLSearchParams {
  const p = new URLSearchParams();
  if (s.state) p.set("state", s.state);
  if (s.district) p.set("district", s.district);
  writePolicy(s.a, p, "a_");
  writePolicy(s.b, p, "b_");
  return p;
}

function sidePatcher(setParams: SetURLSearchParams, side: Side) {
  return (patch: Partial<Policy>) =>
    setParams(
      (prev) => {
        const cur = readParams(prev);
        return writeParams({ ...cur, [side]: { ...cur[side], ...patch } });
      },
      { replace: true },
    );
}

function errorText(e: unknown): "no_data" | "invalid" | "other" | null {
  if (!e) return null;
  if (typeof e === "object" && e !== null) {
    if ("code" in e && e.code === "no_data") return "no_data";
    if ("detail" in e) return "invalid";
  }
  return "other";
}

function reasonOf(e: unknown): string | null {
  return typeof e === "object" && e !== null && "reason" in e && typeof e.reason === "string"
    ? e.reason
    : null;
}

interface ColumnProps {
  side: Side;
  policy: Policy;
  schemes: SchemeOut[];
  onPolicy: (patch: Partial<Policy>) => void;
}

function PolicyColumn({ side, policy, schemes, onPolicy }: ColumnProps) {
  const { t } = useTranslation();
  const scheme = schemes.find((s) => s.code === policy.scheme) ?? schemes[0];
  const setOverrides = useCallback((overrides: Overrides) => onPolicy({ overrides }), [onPolicy]);
  const setDraft = useCallback((d: PolicyDraft) => onPolicy(d), [onPolicy]);
  return (
    <section
      aria-labelledby={`${side}-title`}
      className="grid content-start gap-4 rounded border border-line bg-surface p-4"
    >
      <h2 id={`${side}-title`} className="font-serif text-lg">
        {t(`compare.setting_${side}`)}
      </h2>
      <SchemePicker
        schemes={schemes}
        value={policy.scheme}
        custom={policy.custom}
        onChange={(code) => onPolicy({ scheme: code, overrides: {} })}
      />
      <div className="flex items-center justify-between gap-3 text-sm">
        <span id={`${side}-custom-label`} className="font-semibold">
          {t("custom.toggle")}
        </span>
        <Switch
          aria-labelledby={`${side}-custom-label`}
          checked={policy.custom}
          onCheckedChange={(custom) => onPolicy({ custom })}
        />
      </div>
      {policy.custom && (
        <CustomPolicy
          id={`${side}-custom`}
          name={policy.name}
          group={policy.group}
          onChange={setDraft}
        />
      )}
      {scheme && (
        <Sliders
          key={scheme.code}
          idPrefix={`${side}-`}
          scheme={scheme}
          overrides={policy.overrides}
          onChange={setOverrides}
        />
      )}
    </section>
  );
}

export function DifferencePanel({ data }: { data: CompareResponse }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const d = data.difference;
  let body: React.ReactNode;
  if (!d.comparable || d.point === null || d.low === null || d.high === null) {
    const key =
      data.a.scheme !== data.b.scheme ? "compare.diffOtherScheme" : "compare.diffOtherBase";
    body = <p role="status">{t(key)}</p>;
  } else {
    body = (
      <div className="grid gap-1">
        <p className="font-mono text-3xl" data-testid="difference">
          {t("compare.diffRange", {
            low: signed(d.low, lang),
            high: signed(d.high, lang),
          })}
        </p>
        <p className="text-sm tabular-nums">
          {t("compare.diffMiddle", { point: signed(d.point, lang) })}
        </p>
        <p className="text-xs opacity-80">{t("compare.diffNote")}</p>
      </div>
    );
  }
  return (
    <section
      aria-labelledby="diff-title"
      className="rounded border border-line bg-surface-2 p-4 text-sm"
    >
      <h2 id="diff-title" className="mb-2 font-serif text-lg">
        {t("compare.diffTitle")}
      </h2>
      {body}
    </section>
  );
}

export function Compare() {
  const { t, i18n } = useTranslation();
  const meta = useMeta();
  const [params, setParams] = useSearchParams();
  const sc = useMemo(() => readParams(params), [params]);
  const states = useQuery(getStatesOptions());
  const districts = useQuery(getDistrictsOptions());
  const schemes = useQuery(getSchemesOptions());

  const place = districts.data?.find((d) => d.id === sc.district);
  const schemeA = schemes.data?.find((s) => s.code === sc.a.scheme);
  const schemeB = schemes.data?.find((s) => s.code === sc.b.scheme);
  const canRun = Boolean(schemeA && schemeB && sc.district && place?.has_data);

  const cmp = useQuery({
    ...compareOptions({
      body: {
        district_id: sc.district ?? "",
        a: schemeA ? toSetting(sc.a, schemeA.defaults) : { scheme: sc.a.scheme },
        b: schemeB ? toSetting(sc.b, schemeB.defaults) : { scheme: sc.b.scheme },
      },
    }),
    enabled: canRun,
    placeholderData: keepPreviousData,
    retry: false,
  });

  const update = useCallback(
    (patch: Partial<CompareScenario>) =>
      setParams((prev) => writeParams({ ...readParams(prev), ...patch }), { replace: true }),
    [setParams],
  );
  const patchA = useMemo(() => sidePatcher(setParams, "a"), [setParams]);
  const patchB = useMemo(() => sidePatcher(setParams, "b"), [setParams]);

  const err = canRun ? errorText(cmp.error) : null;
  const noData = (!canRun && place && !place.has_data) || err === "no_data";
  const reason = reasonOf(cmp.error) ?? place?.reason;
  const updating = cmp.isFetching && cmp.isPlaceholderData;

  return (
    <div className="mx-auto grid max-w-7xl gap-6 p-4">
      <div>
        <h1 className="font-serif text-2xl">{t("compare.title")}</h1>
        <p className="text-sm opacity-80">{t("compare.intro")}</p>
      </div>

      {states.data && districts.data && schemes.data ? (
        <div className="max-w-xl print:hidden">
          <Pickers
            hideScheme
            states={states.data}
            districts={districts.data}
            schemes={schemes.data}
            state={sc.state}
            district={sc.district}
            scheme={sc.a.scheme}
            onState={(state) => update({ state, district: null })}
            onDistrict={(district) => update({ district })}
            onScheme={() => undefined}
          />
        </div>
      ) : (
        <p role={states.isError || districts.isError || schemes.isError ? "alert" : "status"}>
          {states.isError || districts.isError || schemes.isError
            ? t("picker.loadError")
            : t("picker.loading")}
        </p>
      )}

      {schemes.data && (
        <div className="grid gap-6 lg:grid-cols-2 print:hidden">
          <PolicyColumn side="a" policy={sc.a} schemes={schemes.data} onPolicy={patchA} />
          <PolicyColumn side="b" policy={sc.b} schemes={schemes.data} onPolicy={patchB} />
        </div>
      )}

      {noData ? (
        <p role="alert" className="rounded border border-line bg-surface p-4">
          {t("result.noData")} {reason ? t(`noDataReason.${reason}`, { defaultValue: "" }) : null}
        </p>
      ) : !canRun ? (
        <p className="rounded border border-line bg-surface p-4">{t("compare.empty")}</p>
      ) : err && !cmp.data ? (
        <p role="alert" className="rounded border border-line bg-surface p-4">
          {err === "invalid" ? t("result.invalid") : t("result.error")}
        </p>
      ) : cmp.data ? (
        <div className="grid gap-6">
          <PrintSummary items={[cmp.data.a, cmp.data.b]} meta={meta} />
          <DownloadBar
            fileKey="download.compareFile"
            build={() =>
              cmp.data && !cmp.isPlaceholderData
                ? compareCsv(cmp.data, t, i18n.language, meta)
                : null
            }
          />
          <DifferencePanel data={cmp.data} />
          <div className="grid gap-6 lg:grid-cols-2">
            {(["a", "b"] as const).map((side) => (
              <section
                key={side}
                aria-label={t(`compare.result_${side}`)}
                className="rounded border border-line bg-surface p-4"
              >
                <h2 className="mb-2 font-serif text-lg">{t(`compare.result_${side}`)}</h2>
                <ResultBody data={cmp.data[side]} updating={updating} />
              </section>
            ))}
          </div>
        </div>
      ) : (
        <p role="status">{t("result.updating")}</p>
      )}
    </div>
  );
}
