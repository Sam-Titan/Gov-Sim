import { useTranslation } from "react-i18next";
import { classLabel, type MapColors, SCALE } from "./colors";

export function Legend({ colors }: { colors: MapColors }) {
  const { t } = useTranslation();
  const [r, g, b] = colors.hatch;
  return (
    <div className="grid gap-2 text-xs">
      <p className="font-semibold">{t("map.legendTitle")}</p>
      <ul className="flex flex-wrap gap-x-3 gap-y-1 font-mono">
        {SCALE.map((c, i) => (
          <li key={c} className="flex items-center gap-1">
            <span
              className="inline-block size-3.5 border border-line"
              style={{ background: c }}
              aria-hidden="true"
            />
            {classLabel(i)}
          </li>
        ))}
      </ul>
      <ul className="flex flex-wrap gap-x-4 gap-y-1">
        <li className="flex items-center gap-1">
          <span
            className="inline-block size-3.5 border border-line"
            style={{ background: colors.noData }}
            aria-hidden="true"
          />
          {t("map.legendNoData")}
        </li>
        <li className="flex items-center gap-1">
          <span
            className="inline-block size-3.5 border border-line"
            style={{
              background: `repeating-linear-gradient(45deg, rgb(${r} ${g} ${b} / 0.8) 0 2px, transparent 2px 5px), ${SCALE[3]}`,
            }}
            aria-hidden="true"
          />
          {t("map.legendHatch")}
        </li>
      </ul>
    </div>
  );
}
