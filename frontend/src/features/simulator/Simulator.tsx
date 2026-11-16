import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import {
  getDistrictsOptions,
  getSchemesOptions,
  getStatesOptions,
  simulateOptions,
  simulateStateOptions,
} from "@/api/@tanstack/react-query.gen";
import { Switch } from "@/components/ui/switch";
import { CustomPolicy, type PolicyDraft } from "@/features/custom-policy/CustomPolicy";
import { DownloadBar, PrintSummary, useMeta } from "@/features/downloads/Downloads";
import { simulateCsv, stateCsv } from "@/features/downloads/rows";
import { DistrictMap } from "@/features/map/DistrictMap";
import { stateIds } from "@/features/map/geo";
import { useGeo } from "@/features/map/useGeo";
import {
  DEFAULT_SCHEME,
  type Overrides,
  parseScenario,
  type Scenario,
  serializeScenario,
  toSetting,
} from "@/lib/scenario";
import { isDark, useUi } from "@/store/ui";
import { Pickers } from "./Pickers";
import { type ResultError, ResultPanel } from "./ResultPanel";
import { Sliders } from "./Sliders";

/** The API sends a body with `code` for 404s and `detail` for 422s. */
function errorKind(e: unknown): ResultError | null {
  if (!e) return null;
  if (typeof e === "object" && e !== null) {
    if ("code" in e && e.code === "no_data") return "no_data";
    if ("detail" in e) return "invalid";
  }
  return "other";
}

function errorReason(e: unknown): string | null {
  if (typeof e === "object" && e !== null && "reason" in e && typeof e.reason === "string") {
    return e.reason;
  }
  return null;
}

export function Simulator() {
  const { t, i18n } = useTranslation();
  const meta = useMeta();
  const theme = useUi((s) => s.theme);
  const [params, setParams] = useSearchParams();
  const sc = useMemo(() => parseScenario(params), [params]);

  const states = useQuery(getStatesOptions());
  const districts = useQuery(getDistrictsOptions());
  const schemes = useQuery(getSchemesOptions());
  const geo = useGeo();

  const scheme = schemes.data?.find((s) => s.code === sc.scheme) ?? schemes.data?.[0];
  const place = districts.data?.find((d) => d.id === sc.district);
  const setting = scheme ? toSetting(sc, scheme.defaults) : { scheme: sc.scheme };
  const canRun = Boolean(scheme && sc.district && place?.has_data);

  const sim = useQuery({
    ...simulateOptions({
      body: { ...setting, district_id: sc.district ?? "" },
    }),
    enabled: canRun,
    placeholderData: keepPreviousData,
    retry: false,
  });
  const stateSim = useQuery({
    ...simulateStateOptions({ body: { ...setting, state: sc.state ?? "" } }),
    enabled: Boolean(scheme && sc.state),
    placeholderData: keepPreviousData,
    retry: false,
  });

  const update = useCallback(
    (patch: Partial<Scenario>) =>
      setParams((prev) => serializeScenario({ ...parseScenario(prev), ...patch }), {
        replace: true,
      }),
    [setParams],
  );
  const setOverrides = useCallback((overrides: Overrides) => update({ overrides }), [update]);
  const setDraft = useCallback((d: PolicyDraft) => update(d), [update]);

  const pickFromMap = (id: string) => {
    const d = districts.data?.find((x) => x.id === id);
    if (!d) return;
    if (d.state !== sc.state) update({ state: d.state, district: null });
    else if (d.has_data) update({ district: d.id });
  };

  const ids = useMemo(() => stateIds(districts.data ?? [], sc.state), [districts.data, sc.state]);
  const loadError = states.isError || districts.isError || schemes.isError;
  const ready = canRun;
  const showError = !canRun && place && !place.has_data ? "no_data" : errorKind(sim.error);
  const noDataReason = errorReason(sim.error) ?? place?.reason;

  return (
    <div className="mx-auto grid max-w-7xl gap-6 p-4 lg:grid-cols-[22rem_1fr] print:block">
      <div className="grid content-start gap-6 print:hidden">
        {loadError && (
          <p role="alert" className="text-alert">
            {t("picker.loadError")}
          </p>
        )}
        {states.data && districts.data && schemes.data ? (
          <Pickers
            states={states.data}
            districts={districts.data}
            schemes={schemes.data}
            state={sc.state}
            district={sc.district}
            scheme={scheme?.code ?? DEFAULT_SCHEME}
            custom={sc.custom}
            onState={(state) => update({ state, district: null })}
            onDistrict={(district) => update({ district })}
            onScheme={(code) => update({ scheme: code, overrides: {} })}
          />
        ) : (
          !loadError && <p role="status">{t("picker.loading")}</p>
        )}
        <div className="flex items-center justify-between gap-3 text-sm">
          <span id="custom-toggle-label" className="font-semibold">
            {t("custom.toggle")}
          </span>
          <Switch
            aria-labelledby="custom-toggle-label"
            checked={sc.custom}
            onCheckedChange={(custom) => update({ custom })}
          />
        </div>
        {sc.custom && <CustomPolicy name={sc.name} group={sc.group} onChange={setDraft} />}
        {scheme && (
          <Sliders
            key={scheme.code}
            scheme={scheme}
            overrides={sc.overrides}
            onChange={setOverrides}
          />
        )}
      </div>

      <div className="grid content-start gap-6">
        {ready && sim.data && <PrintSummary items={[sim.data]} meta={meta} />}
        <ResultPanel
          ready={ready || showError === "no_data"}
          data={ready ? sim.data : undefined}
          updating={sim.isFetching && sim.isPlaceholderData}
          error={showError}
          noDataReason={noDataReason}
        />
        {ready && sim.data && (
          <DownloadBar
            fileKey="download.simulateFile"
            build={() => (sim.data ? simulateCsv(sim.data, t, i18n.language, meta) : null)}
          />
        )}
        <div className="grid gap-6 print:hidden">
          {stateSim.data && (
            <DownloadBar
              fileKey="download.stateFile"
              label="download.csvState"
              print={false}
              build={() =>
                stateSim.data && scheme
                  ? stateCsv(
                      stateSim.data,
                      toSetting(sc, scheme.defaults),
                      scheme.defaults,
                      t,
                      meta,
                    )
                  : null
              }
            />
          )}
          {geo.data ? (
            <DistrictMap
              geo={geo.data}
              dark={isDark(theme)}
              state={sc.state}
              stateDistrictIds={ids}
              rows={stateSim.data?.districts ?? []}
              selected={sc.district}
              onPick={pickFromMap}
              group={sc.custom}
            />
          ) : (
            <p role={geo.isError ? "alert" : "status"}>
              {geo.isError ? t("map.loadError") : t("map.loading")}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
