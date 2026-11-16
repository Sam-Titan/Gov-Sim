import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { z } from "zod";
import type { TargetGroup } from "@/api/types.gen";
import { cleanGroup, GROUP_FIELDS, type GroupField } from "@/lib/scenario";

const DEBOUNCE_MS = 250;
export const NAME_MAX = 60;

const tri = z.enum(["any", "yes", "no"]);
const schema = z.object({
  name: z.string().max(NAME_MAX),
  age_60_plus: tri,
  female: tri,
  disabled: tri,
  rural: tri,
  unbanked: tri,
});
type FormValues = z.infer<typeof schema>;

export interface PolicyDraft {
  name: string;
  group: TargetGroup;
}

const toTri = (v: boolean | null | undefined): "any" | "yes" | "no" =>
  v === true ? "yes" : v === false ? "no" : "any";

function fromForm(v: FormValues): PolicyDraft {
  const group: TargetGroup = {};
  for (const f of GROUP_FIELDS) {
    if (v[f] !== "any") group[f] = v[f] === "yes";
  }
  return { name: v.name.trim(), group: cleanGroup(group) };
}

const SELECT =
  "w-full rounded border border-line bg-surface px-2 py-1.5 text-sm focus-visible:outline-2 focus-visible:outline-accent";

interface Props extends PolicyDraft {
  /** Distinguishes the two forms on the Compare page. */
  id?: string;
  onChange: (v: PolicyDraft) => void;
}

/** Name and target group of a custom policy (SPEC 7.2). Sliders are separate. */
export function CustomPolicy({ id = "custom", name, group, onChange }: Props) {
  const { t } = useTranslation();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name,
      age_60_plus: toTri(group.age_60_plus),
      female: toTri(group.female),
      disabled: toTri(group.disabled),
      rural: toTri(group.rural),
      unbanked: toTri(group.unbanked),
    },
  });
  const latest = useRef(onChange);
  latest.current = onChange;

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    const sub = form.watch((values) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        const parsed = schema.safeParse(values);
        if (parsed.success) latest.current(fromForm(parsed.data));
      }, DEBOUNCE_MS);
    });
    return () => {
      clearTimeout(timer);
      sub.unsubscribe();
    };
  }, [form]);

  const { register } = form;
  const traits: [GroupField, string, string][] = [
    ["age_60_plus", "custom.age.yes", "custom.age.no"],
    ["female", "custom.gender.yes", "custom.gender.no"],
    ["disabled", "custom.disabled.yes", "custom.disabled.no"],
    ["rural", "custom.area.yes", "custom.area.no"],
    ["unbanked", "custom.bank.yes", "custom.bank.no"],
  ];

  return (
    <form
      aria-labelledby={`${id}-title`}
      className="grid gap-3 rounded border border-line bg-surface p-3"
      onSubmit={(e) => e.preventDefault()}
    >
      <h2 id={`${id}-title`} className="font-serif text-lg">
        {t("custom.title")}
      </h2>
      <label className="grid gap-1 text-sm">
        <span className="font-semibold">{t("custom.name")}</span>
        <input
          className={SELECT}
          maxLength={NAME_MAX}
          placeholder={t("custom.namePlaceholder")}
          {...register("name")}
        />
      </label>
      <fieldset className="grid gap-2">
        <legend className="mb-1 text-sm font-semibold">{t("custom.groupTitle")}</legend>
        <p className="text-xs opacity-80">{t("custom.groupHelp")}</p>
        {traits.map(([field, yes, no]) => (
          <label key={field} className="grid gap-1 text-sm">
            <span>{t(`custom.trait.${field}`)}</span>
            <select className={SELECT} {...register(field)}>
              <option value="any">{t("custom.any")}</option>
              <option value="yes">{t(yes)}</option>
              <option value="no">{t(no)}</option>
            </select>
          </label>
        ))}
      </fieldset>
      <p className="text-xs opacity-80">{t("custom.unbankedNote")}</p>
    </form>
  );
}
