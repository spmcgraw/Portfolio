# Analytical view catalog — Finance Close Intelligence Platform

> Resolves map ticket [#6 "Define the close-health & exception view catalog"](https://github.com/spmcgraw/Portfolio/issues/6),
> part of the [Finance Close Intelligence spec map (#1)](https://github.com/spmcgraw/Portfolio/issues/1).
> Grounded in the settled [data model (#3)](data-model.md) and the
> [reference-close-models research (#4)](research/reference-close-models.md).
> This is the **spec** — the SQL views are written directly from it in the downstream build phase.

## What this layer is

The analytical layer sits **on top of the gold-layer tables** from the
[data model](data-model.md). Every view is derived — no view stores state; each is a
`CREATE VIEW` over the base facts and dimensions. Power BI sits directly on these views.

Data-quality exceptions and ownership gaps are **derived here, never stored as flags on
rows** (a decision fixed in the data model): an unbalanced or uncoded or self-approved
entry is a *condition detectable* from base data, not a *fact to store*. Views are never
stale; stored flags rot the moment a line is edited.

## Design decisions and rationale

These shaped the catalog; the "why" is what makes it defensible in an interview.

| Decision | Choice | Why |
|---|---|---|
| **Grain contract** | A deliberate **mix**: *summary* views compute metrics in SQL (window functions, ratios); *atomic* views are one-row-per-record and let Power BI/DAX aggregate | Shows both muscles — window functions in SQL *and* measures in DAX — and puts each computation where it belongs. A scorecard wants pre-computed metrics; an exception register wants the offending row itself. |
| **Time model** | **All periods.** Summary views are one row per **entity × period**; atomic views carry `period_id` for filtering | The synthetic dataset seeds a "bad month" — that story only lands when the bad period stands out against good ones. A days-to-close trend line is the platform's strongest exec visual, and it needs history. |
| **Exception register shape** | Both `v_ownership_gaps` and `v_dq_exceptions` are **unified, discriminated** views (`UNION ALL` of each rule into a common skeleton with a `*_type` column) | One table per page for Power BI, and it demonstrates normalizing heterogeneous exceptions into a common shape — a product-minded move. |
| **Ownership vs integrity boundary** | `v_ownership_gaps` = *accountability* problems (nulls + segregation of duties); `v_dq_exceptions` = *data-integrity* problems (the data itself is wrong) | A clean, defensible line. The falsely-completed reconciliation is an *integrity* problem, so it lives in `v_dq_exceptions`, not ownership gaps. |
| **No reversal rate** | Dropped from `v_journal_activity` | Detecting reversals needs either a model change (a `reversal_of` FK — which NetSuite has no native equivalent of, so it would undercut the realism story) or a fragile mirror-image heuristic. The manual-JE ratio already carries the control-quality signal. |
| **No model changes** | The catalog is fully derivable from the settled data model | Both model-touching ideas (reversal FK, stored DQ flags) were rejected. [#3](data-model.md) stands as-is. |

## Conventions used below

- **"as of" dating** — anything time-relative (overdue, aging) is measured against the
  record's own **`period.end_date`**, never `today`. This keeps metrics period-consistent
  and stops them rotting on a static synthetic dataset.
- **Overdue** — a task/recon is overdue if `completed_date > due_date`, **or** it is still
  open (`completed_date IS NULL`) and `due_date < period.end_date`.
- **Completed** — `completed_date IS NOT NULL` (and, for recons, `status = 'Complete'`).
- **Acceptance clauses** — every view carries three kinds: **(I) invariant** (grain /
  uniqueness), **(T) tie-out** (bounds and reconciliation to base tables), and
  **(S) seed expectation** (what the sample-data design must make appear). The (S) clauses
  are the hand-off contract to the sample-data ticket.

---

## `v_close_health`

**Purpose.** The executive close scorecard — one row that answers "was this close healthy?"
for an entity and period. The landing page of the platform.

**Type / grain.** Summary. **One row per `entity_id` × `period_id`.**

**Reads from.** `period_close` (days-to-close fact), `close_tasks`, `reconciliations`,
`entities`, `periods`.

**Columns / metrics.**

| Column | Source / rule |
|---|---|
| `entity_id`, `entity_name` | `entities` |
| `period_id`, `period_code`, `end_date` | `periods` |
| `target_close_date`, `close_complete_date`, `close_status` | `period_close` |
| `days_to_close` | `close_complete_date − end_date`; **NULL while the close is open** |
| `days_elapsed` | `end_date`-relative elapsed days for an open close (in-flight number; kept separate from `days_to_close`) |
| `target_days_to_close` | `target_close_date − end_date` |
| `days_vs_target` | `days_to_close − target_days_to_close` (RAG-status driver; NULL while open) |
| `total_tasks`, `completed_tasks`, `task_completion_pct` | over `close_tasks` for the entity×period |
| `overdue_tasks` | `close_tasks` meeting the overdue rule |
| `unassigned_tasks` | `close_tasks.owner_id IS NULL` (ties to `v_ownership_gaps`) |
| `total_recons`, `completed_recons`, `recon_completion_pct` | over `reconciliations` |
| `overdue_recons` | `reconciliations` meeting the overdue rule |

**Acceptance.**
- **(I)** Unique on (`entity_id`, `period_id`). One row per `period_close` row.
- **(T)** `completed_tasks ≤ total_tasks`; `task_completion_pct ∈ [0,100]`; same for recons.
  `days_to_close` and `days_vs_target` are NULL **iff** `close_status = 'Open'`.
  `total_tasks` reconciles to `COUNT(*)` on `close_tasks` for the same entity×period.
- **(S)** Across the seeded history, at least one entity×period shows a **positive
  `days_vs_target`** (missed target) and at least one shows a non-positive value (met target),
  so the RAG story has contrast. The bad month shows visibly lower `task_completion_pct`
  and `recon_completion_pct` than the surrounding good months, and `unassigned_tasks > 0`.

---

## `v_reconciliations`

**Purpose.** Reconciliation status and quality per account reconciliation — completion,
overdue, whether it actually ties, and how many open items are aging.

**Type / grain.** Summary. **One row per `reconciliation_id`** (= entity × account × period).

**Reads from.** `reconciliations`, `reconciling_items` (rolled up), `entities`,
`chart_of_accounts`, `periods`.

**Columns / metrics.**

| Column | Source / rule |
|---|---|
| `reconciliation_id` | `reconciliations` (drill key) |
| `entity_id`, `entity_name`, `account_id`, `account_number`, `account_name`, `period_id`, `period_code`, `end_date` | dims |
| `status`, `due_date`, `completed_date` | `reconciliations` |
| `is_overdue` | overdue rule |
| `gl_balance`, `source_balance` | `reconciliations` |
| `reconciliation_variance` | `gl_balance − source_balance` |
| `is_falsely_completed` | `status = 'Complete'` AND `reconciliation_variance <> 0` (also surfaced as an exception in `v_dq_exceptions`) |
| `open_item_count` | count of `reconciling_items` with `status = 'Open'` |
| `open_item_amount` | Σ `amount` of open items |
| `aged_0_30`, `aged_31_60`, `aged_60_plus` | Σ open-item `amount` bucketed by `end_date − open_date` |

**Acceptance.**
- **(I)** Unique on `reconciliation_id`. One row per `reconciliations` row.
- **(T)** `aged_0_30 + aged_31_60 + aged_60_plus = open_item_amount`; `open_item_count ≥ 0`;
  `is_falsely_completed` is true only where `status = 'Complete'`.
- **(S)** At least one recon is **falsely completed** (Complete with non-zero variance).
  At least one recon carries open items in the **60+** bucket. At least one recon is overdue
  in the bad month.

---

## `v_reconciling_items`

**Purpose.** The aged open-items detail — the drill-through behind `v_reconciliations`,
so a reviewer can see *which* items are aging.

**Type / grain.** Atomic. **One row per open `reconciling_item_id`.**

**Reads from.** `reconciling_items`, `reconciliations` (for entity/account/period context),
dims.

**Columns / metrics.**

| Column | Source / rule |
|---|---|
| `reconciling_item_id`, `reconciliation_id` | keys |
| `entity_id/name`, `account_id/number`, `period_id/code`, `end_date` | context via `reconciliations` |
| `description`, `amount`, `open_date` | `reconciling_items` |
| `age_days` | `end_date − open_date` |
| `aging_bucket` | '0–30' / '31–60' / '60+' from `age_days` |

**Acceptance.**
- **(I)** Unique on `reconciling_item_id`. Only `status = 'Open'` items appear.
- **(T)** `age_days ≥ 0`; `aging_bucket` matches `age_days`. Row set and `Σ amount` per
  `reconciliation_id` reconcile to the open-item rollups in `v_reconciliations`.
- **(S)** At least one item in each bucket exists across the seed, including a 60+ item.

---

## `v_journal_activity`

**Purpose.** Journal-entry volume and control-quality per entity and period — how much
posted, and how much of it was manual.

**Type / grain.** Summary. **One row per `entity_id` × `period_id`.**

**Reads from.** `transaction_header`, `transaction_lines`, `entities`, `periods`.

**Columns / metrics.**

| Column | Source / rule |
|---|---|
| `entity_id/name`, `period_id/code`, `end_date` | dims |
| `total_entries` | count of headers |
| `total_lines` | count of lines |
| `total_debit_amount` | Σ `debit` across lines (= Σ credit when balanced) — $ volume |
| `manual_entries` | headers with `entry_type = 'manual'` |
| `automated_entries`, `recurring_entries` | the `entry_type` breakdown |
| `manual_je_ratio` | `manual_entries / total_entries` — **by count** (headline KPI) |
| `manual_dollar_ratio` | Σ debit of manual entries / `total_debit_amount` — materiality |
| `avg_lines_per_entry` | `total_lines / total_entries` — complexity signal |
| `distinct_preparers` | distinct `preparer_id` — workload spread |

**Acceptance.**
- **(I)** Unique on (`entity_id`, `period_id`).
- **(T)** `manual_entries + automated_entries + recurring_entries = total_entries`;
  `manual_je_ratio ∈ [0,1]`; `manual_dollar_ratio ∈ [0,1]`; `total_entries` reconciles to
  `COUNT(*)` on `transaction_header` for the entity×period.
- **(S)** The **bad month** shows a visibly elevated `manual_je_ratio` versus surrounding
  months (the manual-workaround spike). At least one entity×period has all three
  `entry_type` values present so the breakdown is non-trivial.

---

## `v_ownership_gaps`

**Purpose.** The accountability register — every record where ownership or segregation of
duties has failed. One page: "who's on the hook, and where has that broken down?"

**Type / grain.** Atomic, **unified**. **One row per offending record**, discriminated by
`gap_type`. Built as a `UNION ALL` of the rules below into a common skeleton.

**Reads from.** `close_tasks`, `reconciliations`, `transaction_header`, dims.

**Rules (`gap_type`).**

| `gap_type` | Rule | `record_type` |
|---|---|---|
| Unassigned task | `close_tasks.owner_id IS NULL` | close_task |
| Unassigned recon | `reconciliations.preparer_id IS NULL` OR `reviewer_id IS NULL` | reconciliation |
| Self-approved JE | `transaction_header.preparer_id = approver_id` | transaction |
| Unapproved JE | `transaction_header.approver_id IS NULL` | transaction |
| Self-reviewed recon | `reconciliations.preparer_id = reviewer_id` | reconciliation |

**Common skeleton.**

| Column | Notes |
|---|---|
| `gap_type` | discriminator (values above) |
| `entity_id/name`, `period_id/code` | slicers (every source has both) |
| `record_type` | 'close_task' / 'reconciliation' / 'transaction' |
| `record_id` | offending row's PK (drill key) |
| `record_reference` | human handle — `task_name` / `account_number` / `document_number` |
| `responsible_person` | the person who should own it, or the preparer on a self-approved/self-reviewed record; NULL when absence *is* the gap |

**Acceptance.**
- **(I)** One row per offending record; unique on (`record_type`, `record_id`, `gap_type`).
- **(T)** Every row satisfies exactly its `gap_type`'s predicate. `unassigned_tasks` count in
  `v_close_health` equals the count of `Unassigned task` rows here for the same entity×period.
- **(S)** The seed produces **≥ 1 row of every `gap_type`**, concentrated in the bad month.

---

## `v_dq_exceptions`

**Purpose.** The data-quality exception register — every record where the data itself is
wrong. The "what needs fixing before we trust this close?" page.

**Type / grain.** Atomic, **unified**. **One row per offending record**, discriminated by
`exception_type`. `UNION ALL` of the rules below.

**Reads from.** `transaction_header`, `transaction_lines`, `reconciliations`, `periods`, dims.

**Rules (`exception_type`).**

| `exception_type` | Rule | `record_type` |
|---|---|---|
| Unbalanced entry | `SUM(debit) <> SUM(credit)` per `transaction_id` | transaction |
| Uncoded line | `transaction_lines.account_id IS NULL` (or → inactive account) | line |
| Out-of-period posting | `transaction_date NOT BETWEEN period.start_date AND period.end_date` for the entry's `period_id` | transaction |
| Missing memo | `transaction_header.memo IS NULL` | transaction |
| Falsely-completed recon | `reconciliations.status = 'Complete'` AND `gl_balance <> source_balance` | reconciliation |
| Duplicate entry | same `entity_id` + `transaction_date` + total `debit` amount + identical account set, different `transaction_id` (`GROUP BY … HAVING COUNT(*) > 1`) | transaction |

**Common skeleton.**

| Column | Notes |
|---|---|
| `exception_type` | discriminator (values above) |
| `entity_id/name`, `period_id/code` | slicers |
| `record_type` | 'transaction' / 'line' / 'reconciliation' |
| `record_id` | offending row's PK (drill key) |
| `record_reference` | `document_number` / line ref / `account_number` |
| `detail` | the offending value — out-of-balance amount, variance, duplicate group total, etc. (text) |

**Acceptance.**
- **(I)** One row per offending record; unique on (`record_type`, `record_id`, `exception_type`)
  — except **Duplicate entry**, which emits one row per member of a duplicate group.
- **(T)** Every row satisfies exactly its `exception_type`'s predicate. No stored flags are
  read — every exception is computed from base data.
- **(S)** The seed produces **≥ 1 row of every `exception_type`**, concentrated in the bad
  month: at least one unbalanced entry, one uncoded line, one out-of-period posting, one
  missing memo, one falsely-completed recon, and one duplicate pair.

---

## Hand-off: the sample-data contract

The **(S)** clauses above collectively define what the [sample-data design](https://github.com/spmcgraw/Portfolio/issues/1)
must produce. In summary, the seeded dataset must include a **"bad month"** (one
entity × one period) that surfaces:

- **≥ 1 of every `exception_type`** in `v_dq_exceptions` (6 types).
- **≥ 1 of every `gap_type`** in `v_ownership_gaps` (5 types).
- A **`days_vs_target` breach** in `v_close_health`, with a met-target period for contrast.
- An elevated **`manual_je_ratio`** versus surrounding good months.
- At least one **falsely-completed recon** and one **60+ aged** reconciling item.

Good months around it must be clean enough that the bad month is unmistakable.

## Downstream (out of scope here)

Writing the actual `CREATE VIEW` SQL, the seed generator that satisfies the contract above,
and the Power BI pages that sit on these views are all **build-phase** work, ticketed from
this spec as a separate downstream effort.
