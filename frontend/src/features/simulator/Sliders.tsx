import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Inputs, SchemeOut } from "@/api/types.gen";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { formatNumber } from "@/lib/format";
import {
  cashFromPosition,
  cleanOverrides,
  type Field,
  type Overrides,
  positionFromCash,
} from "@/lib/scenario";

const DEBOUNCE_MS = 150;

interface Props {
  scheme: SchemeOut;
  overrides: Overrides;
  onChange: (overrides: Overrides) => void;
}

export function Sliders({ scheme, overrides, onChange }: Props) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const [draft, setDraft] = useState<Overrides>(overrides);
  const current = useRef(overrides);
  current.current = overrides;

  useEffect(() => {
    const id = setTimeout(() => {
      const next = cleanOverrides(draft, scheme.defaults);
      if (JSON.stringify(next) !== JSON.stringify(current.current)) onChange(next);
    }, DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [draft, scheme.defaults, onChange]);

  const value: Inputs = { ...scheme.defaults, ...draft };
  const set = (field: Field, v: number | boolean) => setDraft((d) => ({ ...d, [field]: v }));
  const outside = (field: string) => {
    const env = scheme.real_envelope[field];
    const v = value[field as Field];
    return env !== undefined && typeof v === "number" && (v < env.min || v > env.max);
  };
  const real = (field: string, fmt: (n: number) => string) => {
    const env = scheme.real_envelope[field];
    return env ? t("sliders.real", { min: fmt(env.min), max: fmt(env.max) }) : null;
  };
  const rupees = (n: number) => `₹${formatNumber(n, lang)}`;
  const plain = (n: number) => formatNumber(n, lang);
  const cashRange = scheme.ranges.cash_benefit_inr;
  const moved = Object.keys(cleanOverrides(draft, scheme.defaults)).length > 0;

  return (
    <section aria-labelledby="sliders-title" className="grid gap-4">
      <div className="flex items-baseline justify-between">
        <h2 id="sliders-title" className="font-serif text-lg">
          {t("sliders.title")}
        </h2>
        <button
          type="button"
          className="text-sm text-accent underline disabled:opacity-40"
          disabled={!moved}
          onClick={() => {
            setDraft({});
            onChange({});
          }}
        >
          {t("sliders.reset")}
        </button>
      </div>

      {cashRange && (
        <Row
          id="cash"
          label={t(
            scheme.non_cash ? "sliders.cash_benefit_inr_noncash" : "sliders.cash_benefit_inr",
          )}
          shown={rupees(value.cash_benefit_inr)}
          note={real("cash_benefit_inr", rupees)}
          warn={outside("cash_benefit_inr")}
          realValue={rupees(scheme.defaults.cash_benefit_inr)}
        >
          <Slider
            aria-labelledby="cash-label"
            min={0}
            max={1000}
            step={1}
            value={[
              Math.round(
                positionFromCash(value.cash_benefit_inr, cashRange.min, cashRange.max) * 1000,
              ),
            ]}
            onValueChange={([p]) =>
              set(
                "cash_benefit_inr",
                cashFromPosition((p ?? 0) / 1000, cashRange.min, cashRange.max),
              )
            }
          />
        </Row>
      )}

      {(
        [
          ["document_count", "document_count"],
          ["application_burden", "application_burden"],
          ["benefit_immediacy", "benefit_immediacy"],
        ] as const
      ).map(([field, key]) => {
        const range = scheme.ranges[field];
        if (!range) return null;
        return (
          <Row
            key={field}
            id={field}
            label={t(`sliders.${key}`)}
            shown={plain(value[field])}
            note={real(field, plain)}
            warn={outside(field)}
            assumed={scheme.assumed.includes(field)}
            realValue={plain(scheme.defaults[field])}
          >
            <Slider
              aria-labelledby={`${field}-label`}
              min={range.min}
              max={range.max}
              step={1}
              value={[value[field]]}
              onValueChange={([v]) => set(field, v ?? range.min)}
            />
          </Row>
        );
      })}

      <div className="flex items-center justify-between gap-3 text-sm">
        <div>
          <span id="bank-label" className="font-semibold">
            {t("sliders.requires_bank_account")}
          </span>
          {scheme.assumed.includes("requires_bank_account") && (
            <span className="ml-2 text-xs opacity-70">({t("sliders.assumed")})</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono">
            {value.requires_bank_account ? t("sliders.yes") : t("sliders.no")}
          </span>
          <Switch
            aria-labelledby="bank-label"
            checked={value.requires_bank_account}
            onCheckedChange={(c) => set("requires_bank_account", c)}
          />
        </div>
      </div>
    </section>
  );
}

interface RowProps {
  id: string;
  label: string;
  shown: string;
  note: string | null;
  warn: boolean;
  realValue: string;
  assumed?: boolean;
  children: React.ReactNode;
}

function Row({ id, label, shown, note, warn, realValue, assumed, children }: RowProps) {
  const { t } = useTranslation();
  return (
    <div className="grid gap-1.5 text-sm">
      <div className="flex items-baseline justify-between gap-2">
        <span id={`${id}-label`} className="font-semibold">
          {label}
          {assumed && (
            <span className="ml-2 text-xs font-normal opacity-70">({t("sliders.assumed")})</span>
          )}
        </span>
        <span className="font-mono">{shown}</span>
      </div>
      {children}
      <div className="flex justify-between gap-2 text-xs opacity-80">
        <span>{t("sliders.realValue", { value: realValue })}</span>
        {note && <span>{note}</span>}
      </div>
      {warn && (
        <p className="text-xs font-semibold text-warn" role="note">
          {t("sliders.outside")}
        </p>
      )}
    </div>
  );
}
