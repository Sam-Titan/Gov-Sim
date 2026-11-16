import { useTranslation } from "react-i18next";
import type { DistrictOut, SchemeOut, StateOut } from "@/api/types.gen";

const SELECT =
  "w-full rounded border border-line bg-surface px-2 py-1.5 text-sm focus-visible:outline-2 focus-visible:outline-accent";

interface Props {
  states: StateOut[];
  districts: DistrictOut[];
  schemes: SchemeOut[];
  state: string | null;
  district: string | null;
  scheme: string;
  onState: (s: string | null) => void;
  onDistrict: (id: string | null) => void;
  onScheme: (code: string) => void;
}

export function Pickers(p: Props) {
  const { t } = useTranslation();
  const inState = p.state ? p.districts.filter((d) => d.state === p.state) : [];
  return (
    <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
      <label className="grid gap-1 text-sm">
        <span className="font-semibold">{t("picker.state")}</span>
        <select
          className={SELECT}
          value={p.state ?? ""}
          onChange={(e) => p.onState(e.target.value || null)}
        >
          <option value="">{t("picker.chooseState")}</option>
          {p.states.map((s) => (
            <option key={s.name} value={s.name}>
              {s.name}
            </option>
          ))}
        </select>
      </label>
      <label className="grid gap-1 text-sm">
        <span className="font-semibold">{t("picker.district")}</span>
        <select
          className={SELECT}
          value={p.district ?? ""}
          disabled={!p.state}
          onChange={(e) => p.onDistrict(e.target.value || null)}
        >
          <option value="">{t("picker.chooseDistrict")}</option>
          {inState.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
              {d.has_data ? "" : ` (${t("picker.noData")})`}
            </option>
          ))}
        </select>
      </label>
      <label className="grid gap-1 text-sm">
        <span className="font-semibold">{t("picker.scheme")}</span>
        <select className={SELECT} value={p.scheme} onChange={(e) => p.onScheme(e.target.value)}>
          {p.schemes.map((s) => (
            <option key={s.code} value={s.code}>
              {t(`scheme.${s.code}`, { defaultValue: s.name })}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
