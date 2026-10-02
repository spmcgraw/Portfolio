# Sample close dataset — Finance Close Intelligence Platform

> Resolves map ticket [#7 "Design the sample close dataset"](https://github.com/spmcgraw/Portfolio/issues/7),
> part of the [Finance Close Intelligence spec map (#1)](https://github.com/spmcgraw/Portfolio/issues/1).
> Grounded in the settled [data model (#3)](data-model.md) and the
> [view catalog (#6)](view-catalog.md), whose **(S)** acceptance clauses are the contract
> this dataset must satisfy.
> This is the **spec** — the Python data-generation script is written directly from it in
> the downstream build phase (out of scope here).

## What this spec is

The shape and volume of the **synthetic** close dataset: how many rows of each table, how
they're distributed across entities and periods, and — the point of the whole exercise —
the **deliberate "messiness"** injected so the analytical views have real exceptions to
surface. It is a spec, **not the data**: the data-generation script (a downstream,
graduated ticket) implements it.

The governing idea is **signal vs. noise**. The dataset tells one clear story: a single
**"bad month"** (one entity × one period) where the close went wrong in every way the
platform is built to detect, standing out against otherwise-healthy closes. Good months
carry a *light, realistic* baseline of benign noise — never perfectly clean (that looks
synthetic), never noisy enough to drown the bad month.

## The story the data tells

**Sub B's June 2025 close fell behind.** To force the books closed, the team hand-jammed a
pile of manual journal entries — skipping memos, self-approving their own work, and
fat-fingering a few out of balance. Reconciliations were marked complete that didn't tie, a
duplicate vendor bill slipped through, and tasks went unassigned and overdue. The close
landed a week past target.

Every other entity-period — including the **other two subs closing the same June** — reads
healthy. That cross-entity contrast (an isolated failure, not a systemic data problem) plus
the time-series contrast (a spike-and-recovery against 20 clean months) is what makes the
bad month unmistakable. The **manual-JE spike is the root cause**; most other exceptions
ride on those extra manual entries.

---

## Dimensions (the grid)

### Entities — 4

| # | Role | Closes monthly? | Currency | Purpose |
|---|---|---|---|---|
| 1 | Parent holding co. | No | USD | Non-operating; exists for the `parent_entity_id` consolidation hierarchy |
| 2 | **Sub A** | Yes | USD | Operating subsidiary (clean peer) |
| 3 | **Sub B** | Yes | USD | Operating subsidiary — **carries the bad month** |
| 4 | **Sub C** | Yes | USD | Operating subsidiary (clean peer) |

All USD — multi-currency consolidation is out of scope for the map. Only the 3 operating
subs generate JEs, reconciliations, close tasks, and `period_close` rows; the parent exists
to make the self-referential hierarchy non-trivial.

### Periods — 21

Monthly periods **2025-01 → 2026-09** (full FY2025 + FY2026 to date).

- FY2025 (12 periods) and FY2026 Jan–Aug (8 periods) are **closed** with full history.
- **2026-09 is the open, in-flight close**: `period_close.status = 'Open'`,
  `close_complete_date` NULL for the operating subs. This exercises the view catalog's
  open-close branch (`days_to_close` / `days_vs_target` NULL while open; `days_elapsed`
  populated). No 2026-10 period row — October hasn't ended, so no close has started.
- `period_close`: 3 subs × 21 periods = **63 rows** (60 closed + 3 open for 2026-09).

### Employees — ~10

| Role | Count | Primary slots |
|---|---|---|
| Staff Accountant | 5 | Preparers, task owners, recon preparers |
| Controller | 2 | Approvers, recon reviewers (the SoD "second signature") |
| FP&A | 2 | Task owners, analytical reviewers |
| IT | 1 | Owns a couple of system/automated-close tasks |

1–2 flagged `is_active = false` (a departed accountant) for realism. The **5 staff / 2
controller** split is load-bearing: with two controllers always available, a self-approved
JE reads as a *deliberate* control failure, not "there was no one else to sign."

### Chart of accounts — ~50

| `account_type` | Count |
|---|---|
| Asset | 15 |
| Liability | 10 |
| Equity | 3 |
| Revenue | 7 |
| Expense | 15 |

- **~8 reconciled balance-sheet accounts** — the monthly recons: Cash, AR, AP, Prepaid
  Expenses, Fixed Assets / Accum. Depreciation, Accrued Liabilities, Inventory, and an
  intercompany/suspense account. These drive `reconciliations`, `reconciling_items`, and the
  `gl_balance` vs `source_balance` tie-out.
- **1–2 inactive accounts** (`is_active = false`) — an old "Misc/Suspense" account,
  deactivated — to seed the "miscoded → inactive account" flavor of the uncoded-line rule.

### Source systems — 4 (origin, not storage)

`source_system_id` records where an activity record **originated**, not where it is stored.
All JEs are stored in the NetSuite GL regardless; the dimension preserves the feeder
provenance you can't see inside NetSuite alone.

| System | Category | Origin of… |
|---|---|---|
| NetSuite | ERP | JEs booked natively in the GL (manual/recurring journals); stores *all* JEs |
| Concur | Expense | Expense JEs fed into NetSuite |
| ADP | Payroll | Payroll JEs fed into NetSuite |
| FloQast | Close tool | All reconciliations and close tasks (reads NetSuite's GL for balances) |

---

## Transaction typing

Two separate dimensions on `transaction_header`, populated together for realism:

- **`entry_type`** (manual / automated / recurring) — the *control* characteristic the
  manual-JE ratio measures.
- **`transaction_type`** — *what kind of transaction it is*, NetSuite-flavored.

**`transaction_type` vocabulary:** Journal Entry, Vendor Bill, Bill Payment, Customer
Invoice, Customer Payment, Item Receipt, Item Fulfillment, Inventory Adjustment, Expense
Report, Deposit.

**Correlation (baseline mix):**

| `entry_type` | Baseline % | Typical `transaction_type`s | Origin |
|---|---|---|---|
| **manual** | ~20% | Journal Entry (hand-booked accruals, reclasses, true-ups); occasional manual Inventory Adjustment | NetSuite (native) |
| **recurring** | ~30% | Journal Entry (recurring depreciation / amortization / standard accruals); Payroll Journal | NetSuite recurring, ADP |
| **automated** | ~50% | Vendor Bill, Bill Payment, Customer Invoice, Customer Payment, Item Receipt, Item Fulfillment, Deposit, Expense Report, Inventory Adjustment | NetSuite modules, Concur |

So `manual_je_ratio` effectively measures the hand-booked **Journal Entry** slice — the
control signal a controller cares about — while the automated 50% carries genuine subledger
transaction types rather than fake journals. Baseline `manual_je_ratio ≈ 0.20`.

---

## Baseline volumes (a normal, healthy entity × period)

| Table | Per entity × period | Approx. total (×3 subs ×21 periods) | Notes |
|---|---|---|---|
| `transaction_header` | ~60 | **~3,800** | Believable monthly GL volume for a small sub |
| `transaction_lines` | avg ~3.2 lines/JE (min 2; some 6–10 allocations) | **~12,000** | Line grain makes the balance + manual-ratio checks real |
| `close_tasks` | ~25 | **~1,575** | A realistic close checklist length |
| `reconciliations` | 8 (fixed by the reconciled-account set) | **~500** | One per reconciled account |
| `reconciling_items` | ~30% of recons carry 1–4 open items | **~300** | Most recons tie cleanly; some carry open items |

Totals are deliberately light (~16K rows across headers + lines) — enough to look like a
real close, small enough that a handful of injected exceptions is a believable *small*
fraction and the dataset stays snappy in Postgres and Power BI.

### Natural variance (texture, not exceptions)

So the good months aren't suspiciously flat:

- `manual_je_ratio` wobbles **0.15 – 0.25** month to month (bad month spikes to ~0.45).
- `days_to_close` varies **3 – 6 days** around a target of **5** — most months meet it, one
  or two land +1 over. This naturally satisfies `v_close_health`'s "at least one met and at
  least one missed target" clause before the bad month's big breach is even counted.

---

## The bad month — Sub B, June 2025 (`2025-06`)

A single **closed** period (so it has a complete, comparable `days_to_close`), with 5 clean
months before and ~15 after → a clear spike-and-recovery on the trend line. One
concentrated bad month; no second "warning" blip.

### Close-health deltas (`v_close_health`)

| Metric | Bad month | Baseline |
|---|---|---|
| `manual_je_ratio` | **~0.45** | ~0.20 |
| `days_to_close` | **12** (vs target 5) → `days_vs_target` = **+7** | 3–6 (meets ~5) |
| `task_completion_pct` | **~75%** | ~95%+ |
| `recon_completion_pct` | **~75%** | ~95%+ |
| `overdue_tasks`, `overdue_recons` | elevated | ~0 |

The manual spike means ~27 manual JEs instead of ~12; most exceptions below ride on those
extra manual entries.

### Injected DQ exceptions (`v_dq_exceptions`)

| `exception_type` | Bad-month count | Lands on | Good-month baseline |
|---|---|---|---|
| Unbalanced entry | 3 | manual Journal Entries | 0 |
| Uncoded line | 4 (2 null `account_id` + 2 → inactive account) | manual JE lines | 0 |
| Out-of-period posting | 3 | JEs dated outside June | ~0–1 (sparse) |
| Missing memo | 5 | manual Journal Entries | ~1–2 (routine hygiene noise) |
| Falsely-completed recon | 2 | Complete recon, `gl_balance ≠ source_balance` | 0 |
| Duplicate entry | 1 pair (2 rows) | **Vendor Bills** (duplicate-payment risk) | 0 |

### Injected ownership gaps (`v_ownership_gaps`)

| `gap_type` | Bad-month count | Good-month baseline |
|---|---|---|
| Unassigned task (`owner_id` NULL) | 3 | 0 |
| Unassigned recon (`preparer_id` or `reviewer_id` NULL) | 2 | 0 |
| Self-approved JE (`preparer_id = approver_id`) | 3 | 0 |
| Unapproved JE (`approver_id` NULL) | 2 | 0 |
| Self-reviewed recon (`preparer_id = reviewer_id`) | 1 | 0 |

### Reconciliation specifics (bad month, Sub B June)

- **2 falsely-completed** recons (Complete with non-zero variance — also surface in
  `v_dq_exceptions`).
- **≥1 recon with a 60+ day aged** open item (vs. routine 0–30 / 31–60 aging elsewhere).
- **≥1 overdue** recon.

Net: ~15–18 of Sub B's ~60 June JEs carry at least one flag (~25–30%) — reads convincingly
as "this close was a mess" without being cartoonish.

---

## Signal-vs-noise policy

The distinction that keeps the dataset believable:

- **Benign, routine issues** — a light baseline in good months (missing memos, the odd
  out-of-period posting, normal 0–30 / 31–60 recon aging). Real close data always carries a
  little of this; zero would look synthetic.
- **Serious control failures** — effectively **zero outside the bad month**: unbalanced
  entries, uncoded lines, duplicate entries, all five ownership/SoD gaps, and 60+ aging.
  Keeping these June-only makes `v_ownership_gaps` and the severe `v_dq_exceptions` rows a
  near-empty page that lights up exactly once — a crisp, legible control story.

---

## Coverage check against the view-catalog contract

Every **(S)** clause from the [view catalog](view-catalog.md) is satisfied:

| Hand-off requirement | Satisfied by |
|---|---|
| ≥1 of every `exception_type` (6) in the bad month | Injected DQ exceptions table above |
| ≥1 of every `gap_type` (5) in the bad month | Injected ownership gaps table above |
| `days_vs_target` breach + a met-target period for contrast | +7 breach at Sub B June; other subs/months meet target (also via natural variance) |
| Elevated `manual_je_ratio` vs surrounding months | 0.45 vs 0.15–0.25 baseline |
| ≥1 falsely-completed recon | 2 at Sub B June |
| ≥1 recon with a 60+ aged item | ≥1 at Sub B June |
| Open close exercising NULL `days_to_close` / `days_elapsed` | 2026-09 left open |
| `entry_type` breakdown non-trivial (all three present) | 50/30/20 baseline mix on every entity-period |
| At least one of each aging bucket (0–30 / 31–60 / 60+) | Routine aging baseline + the seeded 60+ item |
| Good months clean enough that the bad month is unmistakable | Signal-vs-noise policy above |

---

## Downstream (out of scope here)

Writing the Python generator that produces rows satisfying this spec, loading them into
PostgreSQL, and the data-validation checks are all **build-phase** work, ticketed from this
spec as a separate downstream effort.
