# Power BI experience & output-table spec — Finance Close Intelligence Platform

> Resolves map ticket [#13 "Design the Power BI experience & output-table spec"](https://github.com/spmcgraw/Portfolio/issues/13),
> part of the [Finance Close Intelligence spec map (#1)](https://github.com/spmcgraw/Portfolio/issues/1).
> Grounded in the settled [view catalog (#6)](view-catalog.md), [data model (#3)](data-model.md),
> and [sample-data design (#7)](sample-data-spec.md).
> This is the **design** Sean builds the Power BI report against in the downstream build phase —
> it specifies pages, the views each reads, the visuals, and *where every metric is computed*.
> It deliberately does **not** contain DAX expressions: it names each measure's intent and
> location so the DAX is written by hand during the build.

## What this spec is

The report sits **directly on the analytical views** from the [view catalog](view-catalog.md) —
no Power BI data stays behind a view. This document fixes four things:

1. **Pages** — what exists and the question each answers.
2. **Page → view mapping** — which view(s) each page reads.
3. **Where each metric computes** — the SQL-vs-DAX boundary, per the governing rule below.
4. **The narrative** — how the pages tell the seeded "bad month" story.

## Design decisions and rationale

These shaped the experience; the "why" is what makes it defensible in an interview.

| Decision | Choice | Why |
|---|---|---|
| **Report structure** | **Hybrid**: a composed executive landing page + four detail pages mapping ~1:1 to the views | The exec opens one page — give it a real narrative front door that composes across views. Everyone who drills gets a clean, mechanical "every view earns a page" structure. Doesn't depend on personas (still unspecified). |
| **Exception pages** | Accountability Gaps and DQ Exceptions stay **two separate pages** | Mirrors the catalog's deliberate accountability-vs-integrity boundary, and each register is rich enough to fill a page. The split is a designed decision worth showing. |
| **Recon-items** | A **drill-through** page, not a nav page | It is detail-behind-a-row — the canonical Power BI drill-through pattern. Keeps the top-level nav clean. |
| **Compute boundary (rule A)** | **Additive components live in SQL; ratios and averages are DAX measures over `SUM(...)`.** The catalog's pre-computed `*_pct` columns become reference/debug columns, not what visuals bind to | Averaging pre-computed ratios is wrong (90% of 10 + 50% of 2 ≠ 70%). Carrying additive components and recomputing ratios in DAX keeps every metric correct under *any* slice, and keeps the multi-period days-to-close trend — the strongest exec visual — alive. Shows both muscles: window functions in SQL, measures in DAX. |
| **Non-additive metrics** | `distinct_preparers` is **single-period-only** (reference column); not offered as a cross-period visual | Distinct counts don't sum (3 preparers in June + 3 in July ≠ 6). It is context, not a headline. An atomic journal view is the noted escape hatch if cross-period distinct counts are ever wanted. |
| **Filtering** | **Global synced** entity + period slicers; report opens on **all entities / all periods** | Carrying slicer context into drill-downs keeps the narrative intact. Opening on full history lets the viewer *discover* the bad month as a spike on the trend line rather than being handed the answer — which is the platform's whole thesis. |
| **Measure spec style** | This document names each measure's **intent and location**, never its DAX expression | The build phase is where Sean writes the DAX by hand to build that muscle; handing over formulae would defeat that. |

## The compute rule, concretely (the output-table contract)

Under **rule A**, each summary view must expose the **additive building blocks** that DAX
re-aggregates; the derived ratio/average columns the [view catalog](view-catalog.md) lists are
kept as **reference columns** (useful for tie-out and single-row debugging) but visuals bind to
DAX measures instead. The audit below confirms the settled views already carry what rule A needs.

| View | Additive components (SQL → bound/summed in DAX) | Ratios/averages (DAX measures; catalog column is reference only) | Notes |
|---|---|---|---|
| `v_close_health` | `total_tasks`, `completed_tasks`, `overdue_tasks`, `unassigned_tasks`, `total_recons`, `completed_recons`, `overdue_recons`, `days_to_close`, `target_days_to_close` | `task_completion_pct`, `recon_completion_pct`, `days_vs_target` | All components additive. `days_to_close` averages safely **over rows** (never over ratios). NULL while the close is open — measures must tolerate NULL. |
| `v_journal_activity` | `total_entries`, `total_lines`, `total_debit_amount`, `manual_entries`, `automated_entries`, `recurring_entries` | `manual_je_ratio`, `manual_dollar_ratio`, `avg_lines_per_entry` | **`distinct_preparers` is non-additive** → single-period-only reference column (see wrinkle rule above). |
| `v_reconciliations` | `gl_balance`, `source_balance`, `open_item_count`, `open_item_amount`, `aged_0_30`, `aged_31_60`, `aged_60_plus` | `reconciliation_variance` (additive — difference of sums, safe to re-aggregate) | Per-recon grain rolls up cleanly to entity×period. `is_falsely_completed` / `is_overdue` are row-level booleans used as filters, not aggregated. |
| `v_reconciling_items` | `amount` (Σ per bucket) | — | Atomic; DAX aggregates for the drill-through totals, which tie back to `v_reconciliations` rollups. |
| `v_ownership_gaps` | row counts (`COUNTROWS` by `gap_type`) | — | Atomic register; everything is a DAX count over rows. |
| `v_dq_exceptions` | row counts (`COUNTROWS` by `exception_type`) | — | Atomic register; everything is a DAX count over rows. Duplicate-entry emits one row per group member. |

**Escape hatch (noted, not built):** if a cross-period **distinct preparer** count is later wanted,
it needs preparer identity at row grain — either a new atomic journal view or reading
`preparer_id` from base `transaction_header`. Out of scope for this spec; recorded so the build
doesn't rediscover it.

---

## Page 1 — Close Health Overview (landing)

**Question it answers.** "Was this close healthy?" — at a glance, across the selected entities
and periods. The exec front door and the narrative's opening hook.

**Reads.** `v_close_health` (primary); glances at `v_journal_activity` (Manual JE %) and both
registers (exception counts).

**Story role.** *Hook* — the days-to-close trend and entity bar make the bad month surface as a
visible spike, before any drill-down.

**Visuals.**

| # | Visual | Binds to | Compute |
|---|---|---|---|
| 1 | **KPI card row** — Days to Close vs Target · Task Completion % · Recon Completion % · Manual JE % · Open Exceptions (two cards: gaps + DQ) | DAX measures | All DAX (ratios/counts re-aggregated) |
| 2 | **Days-to-close trend line** (hero) — x = period, y = days to close, with a target reference line, entity on legend | `v_close_health` rows + a target measure | Reads SQL columns across periods; target line is a measure |
| 3 | **Entity comparison bar** — days-vs-target by entity for the selected period (the bad-month reveal) | DAX measure | DAX (`days_to_close − target_days_to_close`, summed) |
| 4 | **Completion visuals** — task & recon completion (stacked bar or gauge) | additive numerator/denominator | DAX ratios |
| 5 | **Exception summary tiles** — open counts, as the drill hooks into pages 4 & 5 | `COUNTROWS` of each register | DAX |

**Measures (intent + location — DAX written during build).**

- **Task Completion %** — completed over total tasks, re-aggregated across the slice. *DAX.*
- **Recon Completion %** — completed over total recons, re-aggregated. *DAX.*
- **Days vs Target** — actual days-to-close less target, aggregated; tolerant of NULL (open close). *DAX.*
- **Manual JE %** — manual over total entries (from `v_journal_activity`). *DAX.*
- **Open Exceptions (Gaps / DQ)** — row counts of each register. *DAX, two measures.*

---

## Page 2 — Reconciliations

**Question it answers.** "Which reconciliations are done, do they actually tie, and what's aging?"

**Reads.** `v_reconciliations`; **drills through** to `v_reconciling_items`.

**Story role.** *Effect (downstream damage)* — a falsely-completed recon and a 60+ aged item the
manual-JE mess obscured.

**Visuals.**

| # | Visual | Binds to | Compute |
|---|---|---|---|
| 1 | **Recon status matrix** — account × status, with completion / overdue flags | `v_reconciliations` | Row-level columns + DAX completion % |
| 2 | **Aging stacked bar** — 0–30 / 31–60 / 60+ by **account**, filtered to the selected entity | `aged_*` components | DAX sums per bucket |
| 3 | **Needs-attention table** — filtered to `is_overdue` OR `is_falsely_completed` | row-level booleans | Filter, no aggregation |
| 4 | **Variance callout** — recons with `reconciliation_variance ≠ 0`, falsely-completed flagged | `reconciliation_variance` | DAX (difference of sums) |

**Drill-through.** Right-click any recon row → `v_reconciling_items` scoped to that
`reconciliation_id`: open items with `age_days`, `aging_bucket`, amount. Totals tie back to the
`open_item_*` rollups in `v_reconciliations`.

**Cross-reference.** The **falsely-completed recon** appears here *and* on DQ Exceptions —
same fact, two audiences (a recon reviewer and a data-integrity reviewer). A deliberate choice,
not duplication to eliminate.

---

## Page 3 — Journal Activity

**Question it answers.** "How much posted, and how much of it was manual?" — the control-quality
signal.

**Reads.** `v_journal_activity`.

**Story role.** *Root cause* — the manual-JE spike in the bad month is where the story starts.

**Visuals.**

| # | Visual | Binds to | Compute |
|---|---|---|---|
| 1 | **Manual JE % trend** — by period; the bad month spikes | DAX measure | DAX ratio across periods |
| 2 | **Entry-type breakdown** — stacked bar, manual / automated / recurring by entity or period | additive counts | DAX sums |
| 3 | **Volume & materiality context** — `total_entries`, `total_debit_amount`, and **Manual $ %** so ratio is read against materiality | components + DAX | Manual $ % is DAX |
| 4 | **Preparer workload** — entries by preparer (**single-period-only**) | `distinct_preparers` reference column | SQL column; valid only at single-period grain — do **not** offer cross-period |

**Measures.** Manual JE % (by count), Manual $ % (materiality), Avg lines per entry — all DAX
over additive components.

---

## Page 4 — Accountability Gaps

**Question it answers.** "Who's on the hook, and where has that broken down?"

**Reads.** `v_ownership_gaps` (unified, discriminated register, one row per offending record).

**Story role.** *Effect (accountability)* — the close rush left unassigned tasks, self-approved
JEs, a self-reviewed recon.

**Visuals (shared workbench pattern).**

| # | Visual | Binds to | Compute |
|---|---|---|---|
| 1 | **Type breakdown bar** — count by `gap_type`; **cross-filters** the table | `COUNTROWS` by type | DAX |
| 2 | **Register table** — the common skeleton (type, entity, period, record reference, responsible person); the actionable list | `v_ownership_gaps` | Row-level |
| 3 | **Concentration matrix/small-multiple** — counts by entity × period, placing the spike in the bad month | DAX counts | DAX |
| 4 | **Drill to source** (optional) — right-click → underlying record where feasible | — | Optional |

---

## Page 5 — Data Quality Exceptions

**Question it answers.** "What needs fixing before we trust this close?"

**Reads.** `v_dq_exceptions` (unified, discriminated register, one row per offending record;
duplicate-entry emits one row per group member).

**Story role.** *Effect (integrity)* — the manual entries caused unbalanced entries, missing
memos, a duplicate, an out-of-period posting, and the falsely-completed recon.

**Visuals (same workbench pattern as page 4, plus one explore visual).**

| # | Visual | Binds to | Compute |
|---|---|---|---|
| 1 | **Type breakdown bar** — count by `exception_type`; **cross-filters** the table | `COUNTROWS` by type | DAX |
| 2 | **Register table** — common skeleton (type, entity, period, record reference, detail) | `v_dq_exceptions` | Row-level |
| 3 | **Decomposition tree** (this page only) — exceptions by type → entity → period | DAX counts | DAX; shows manual-driven types dominating the bad month |
| 4 | **Drill to source** (optional) — a transaction's lines, a recon | — | Optional |

The decomposition tree lives **only** here — reaching for the right advanced visual once, without
over-using it.

---

## Narrative walkthrough — the "bad month" story

The report tells a **cause → effect** story anchored on the **manual-JE spike in Sub B /
June 2025** (the seeded root cause — see [sample-data spec](sample-data-spec.md)). This is the
story only an *integrated* platform can tell: a control-quality breakdown cascading into data
integrity, accountability, and reconciliation damage. The guided path:

1. **Overview, all history** — the days-to-close trend runs healthy until June 2025, where Sub B
   spikes above target; exception tiles are non-zero. *Hook: "something happened in June."*
2. **Slice to June / Sub B** (global synced slicer) — every page scopes to the bad month. Overview
   cards turn red: completion down, Manual JE % up, exceptions present.
3. **Journal Activity — the root cause.** The manual-JE ratio spikes: a wave of manual entries.
   Volume and Manual $ % confirm it's material, not noise.
4. **DQ Exceptions — the integrity effect.** Those manual entries produced unbalanced entries,
   missing memos, a duplicate, and an out-of-period posting, concentrated in June. The
   decomposition tree shows manual-driven types dominating.
5. **Accountability Gaps — the control effect.** The same rush left unassigned tasks, self-approved
   JEs, and a self-reviewed recon.
6. **Reconciliations — the downstream damage.** A falsely-completed recon and a 60+ aged item the
   manual mess obscured.

Each page is tagged above with its **story role** (hook / root cause / effect) so the build keeps
the narrative in view. The good months around June must stay clean enough (per the sample-data
contract) that the spike is unmistakable.

## Downstream (out of scope here)

Building the actual Power BI report — the data model relationships in Power BI, the DAX measures,
the page layouts, theming, and bookmarks — is **build-phase** work, ticketed from this spec as part
of the separate downstream effort. This document is the design that work is built against.
