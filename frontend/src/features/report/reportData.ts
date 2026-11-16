import { z } from "zod";
import type { ReportResponse } from "@/api/types.gen";

/** The API types these blocks as loose objects. Check their shape before showing numbers. */
const maeRow = z.object({ agent_mae: z.number(), gbm_mae: z.number(), naive_mae: z.number() });
const fold = maeRow.extend({ name: z.string(), n: z.number() });
const folds = z.object({ folds: z.array(fold), weighted_mean: maeRow });

const betaSet = z.record(z.string(), z.number());
const sets = z.record(z.string(), betaSet);
const recoveryTerm = z.object({ true: z.number(), est: z.number(), err: z.number() });

const schemeBand = z.object({
  median_half_width_pp: z.number(),
  max_half_width_pp: z.number(),
  share_over_30pp_wide_at_real_settings: z.number(),
});

const cell = z.union([z.number(), z.string(), z.null()]);

const parsed = z.object({
  losto: folds,
  loso: folds,
  fixed: sets,
  fitted: sets,
  recovery: z.record(z.string(), z.record(z.string(), recoveryTerm)),
  deff: z.object({ value: z.number(), label: z.string() }),
  bands: z.record(z.string(), schemeBand),
  gbmBands: z.record(z.string(), z.object({ p10: z.number(), p90: z.number() })),
  sanity: z.record(z.string(), z.record(z.string(), z.record(z.string(), cell))),
});

export type ParsedReport = z.infer<typeof parsed> & { raw: ReportResponse };

export const SCHEME_ORDER = ["pmjay", "pmuy", "jsy", "sbm"] as const;
export const SETS = ["weak", "central", "strong"] as const;

/** Returns null when the report does not have the expected shape (page shows an error). */
export function parseReport(r: ReportResponse): ParsedReport | null {
  const betas = r.betas as { fixed_sets_assumed_by_team?: unknown; fitted?: unknown };
  const sb = r.sampling_band as { deff?: unknown; by_scheme?: unknown };
  const res = parsed.safeParse({
    losto: r.losto_headline,
    loso: r.loso,
    fixed: betas.fixed_sets_assumed_by_team,
    fitted: betas.fitted,
    recovery: r.recovery,
    deff: sb.deff,
    bands: sb.by_scheme,
    gbmBands: r.gbm_losto_error_band_pp,
    sanity: r.sanity_table_pp,
  });
  return res.success ? { ...res.data, raw: r } : null;
}

/** Folds where the agent model has a lower error than the GBM. */
export function agentWins(f: { folds: { agent_mae: number; gbm_mae: number }[] }): number {
  return f.folds.filter((x) => x.agent_mae < x.gbm_mae).length;
}
