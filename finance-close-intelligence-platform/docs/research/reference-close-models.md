> Wayfinder research artifact for issue #4 — grounding brief for the Finance Close Intelligence Platform data model and analytical-view catalog. Read before drafting the schema/views. Sources are linked inline and listed at the end. Where a claim is inferred or sources disagree, it is flagged.

# Reference Close Data Models, Metrics & Data-Quality Patterns

## 1. Reference data models / schemas (close, reconciliations, journal activity)

**dbt ERP finance packages (best structural reference).** Fivetran maintains open-source dbt packages that transform raw ERP exports into analytics-ready finance models — NetSuite, QuickBooks, Xero, Sage Intacct. They are the closest thing to a "canonical" published GL data model in the open-source world and are worth reading for grain and naming conventions.
- `fivetran/dbt_netsuite` produces `netsuite2__transaction_details` (the workhorse — transaction lines enriched with accounting period, account, subsidiary, entity, location, item, department), plus `netsuite2__balance_sheet` and `netsuite2__income_statement` (both at transaction-line grain by default, optionally aggregated). Notably it does **not** ship a single table literally named `general_ledger`; the GL is reconstructed from posting transaction lines. ([dbt_netsuite](https://github.com/fivetran/dbt_netsuite))
- `fivetran/dbt_quickbooks` builds `general_ledger`, `balance_sheet`, `profit_and_loss`, plus AR/AP aging models. ([dbt_quickbooks](https://github.com/fivetran/dbt_quickbooks))
- dbt Labs' own guidance is to **recreate the GL in its entirety first**, then derive statements from it — double-entry lines (debit/credit) at transaction-line grain are the foundational fact table. ([dbt financial modeling blog](https://docs.getdbt.com/blog/financial-modeling-accounting-principles))

**Shape of a NetSuite GL / journal-entry export.** A real ERP GL export (via a NetSuite Transaction saved search, the standard extraction path) typically carries: Date, Type, Document/Transaction Number, Account, Account Type, Name/Entity, Memo, Amount (Debit), Amount (Credit), Posting Period, Subsidiary/Department/Class/Location, Source, and System Notes (created-by / date, i.e. audit trail). Extraction convention: set **Posting = True** (only GL-posted lines) and **Main Line = False** (return every distribution line, not just the header) for line-level granularity; export as CSV to avoid the XLS row cap. ([MindBridge NetSuite GL export](https://support.mindbridge.ai/hc/en-us/articles/360058018553), [RSM: full GL detail for auditors](https://technologyblog.rsmus.com/technologies/netsuite/exporting-full-gl-detail-auditor/))

**Takeaway for the model.** A journal/GL fact should be modeled at the **distribution-line grain** (one row per debit or credit line), keyed to a JE header, with the entry balancing across its lines. Reconciliations and close tasks are separate entities (they don't come from the GL export — they live in close-management tools like BlackLine/Trintech), so our schema should treat *reconciliations* and *close tasks* as first-class tables alongside the GL, not derived from it. (Inference — no single open-source package models close tasks/recons; those come from the KPI/close-ops literature in §2.)

## 2. Close-health metrics / KPIs (with computation)

Definitions below are drawn from close-ops vendor references (BlackLine, OneStream, Trintech, Aico). These vendors broadly agree on the metric set; exact denominators vary, so the formulas are stated explicitly.

| Metric | Definition / computation |
|---|---|
| **Days to close (DTC / close cycle time)** | Calendar (or business) days from period-end date to the date financials are finalized/approved. The flagship close metric; lower trend = more discipline/automation. Compute per period as `close_complete_date − period_end_date`. ([OneStream](https://www.onestream.com/blog/financial-close-kpis/), [BlackLine](https://www.blackline.com/blog/22-financial-kpi-metrics-for-future-ready-financial-operations/)) |
| **Reconciliation completion %** | `# reconciliations completed & approved by deadline ÷ # required reconciliations`. Measures adherence to the close schedule. Track "completed on time" vs. "completed late" separately. ([OneStream](https://www.onestream.com/blog/financial-close-kpis/), [Trintech](https://www.trintech.com/blog/16-kpis-to-prioritize/)) |
| **Aged / open reconciling items** | Count and $ value of reconciling items still open, bucketed by age (e.g. 0–30 / 31–60 / 60+ days). Aging signals unresolved risk sitting on the balance sheet. Compute `as_of_date − item_open_date`, bucket, sum amount. ([Trintech](https://www.trintech.com/blog/16-kpis-to-prioritize/)) |
| **Unassigned / overdue close tasks** | Count of close tasks with no owner (`owner IS NULL`) or past their due date and not complete (`due_date < today AND status != 'complete'`). Ownership-gap and bottleneck indicator. ([OneStream](https://www.onestream.com/blog/financial-close-kpis/)) |
| **Journal-entry volume** | Count of JEs (and lines) posted per period, often sliced by entity/account/preparer. Baseline for workload and for the manual ratio below. ([BlackLine](https://www.blackline.com/blog/22-financial-kpi-metrics-for-future-ready-financial-operations/)) |
| **Manual JE ratio** | `# manual journal entries ÷ total journal entries` in a period (exclude standard recurring/system entries). High ratio = control risk and non-scalable process. A related control metric is the **JE reversal/correction rate** (`# JEs reversed or corrected ÷ total JEs`). ([Hyperbots: manual JE](https://www.hyperbots.com/glossary/manual-journal-entry), [BlackLine](https://www.blackline.com/blog/22-financial-kpi-metrics-for-future-ready-financial-operations/)) |
| **Data-quality exception rate** | `# transactions (or entries) failing validation rules ÷ total transactions`, ideally trended across the period rather than checked only at year-end. Rules feeding this are the patterns in §3. ([CORAA data integrity](https://coraa.ai/blog/data-integrity-verification-audit-automation)) |

## 3. Data-quality exception patterns worth modeling

These are the standard GL/JE exception tests (auditor JE-testing and continuous-monitoring literature). Each maps cleanly to a SQL rule over the line-grain fact.

- **Unbalanced entries** — total debits ≠ total credits for a JE. Detect: `GROUP BY journal_id HAVING SUM(debit) <> SUM(credit)` (or `SUM(signed_amount) <> 0`). ([Greenskies JE tests](https://greenskiesanalytics.com/the-complete-list-of-je-tests/), [eOne: unbalanced GL distribution](https://www.eonesolutions.com/blog/finding-and-fixing-the-unbalanced-gl-entry-distribution-econnect-error-number-944/))
- **Missing owners / preparers / approvers** — a JE or reconciliation with a null preparer, or where preparer = approver (segregation-of-duties breach). Detect: `preparer IS NULL` or `preparer = approver`. ([Greenskies JE tests](https://greenskiesanalytics.com/the-complete-list-of-je-tests/))
- **Uncoded / miscoded transactions** — line posts to a null/invalid account, or to an account not in the chart of accounts, or a mismatched account type. Detect: anti-join line.account_id against dim_account; flag nulls and non-matches. Inconsistent chart-of-accounts coding is cited as the #1 data-quality issue to fix first. ([Numeric: GL reconciliation](https://www.numeric.io/blog/general-ledger-reconciliation), [Greenskies JE tests](https://greenskiesanalytics.com/the-complete-list-of-je-tests/))
- **Out-of-period / backdated postings** — entry date falls outside the posting period, or is posted more than X days after period-end (or on weekends/holidays — a classic fraud flag). Detect: compare `transaction_date` to the period window; flag deltas beyond threshold. ([Greenskies JE tests](https://greenskiesanalytics.com/the-complete-list-of-je-tests/), [Arbutus GL tests](https://www.arbutussoftware.com/en/analytics-tests/-general-ledger/for-internal-auditors))
- **Duplicates** — same account, same amount, same/near date under different JE numbers. Detect: window/`GROUP BY account, amount, date HAVING COUNT(*) > 1`, then review for legitimate repeats. Also catch reversal pairs. ([Greenskies JE tests](https://greenskiesanalytics.com/the-complete-list-of-je-tests/), [Numeric](https://www.numeric.io/blog/general-ledger-reconciliation))
- **Missing descriptions / memos** — blank memo on a manual JE (weakens audit trail). Detect: `memo IS NULL OR memo = ''`, scoped to manual source. ([Greenskies JE tests](https://greenskiesanalytics.com/the-complete-list-of-je-tests/))
- *(Optional enrichments)* **Round-dollar amounts** (estimate-precision flag) and **seldom-used accounts** — both cheap to add and demonstrate audit-analytics literacy. ([Greenskies JE tests](https://greenskiesanalytics.com/the-complete-list-of-je-tests/))

## Implications for our model & views

1. **Model the JE fact at distribution-line grain** (one row per debit/credit), with a JE header table above it — mirrors NetSuite exports and dbt packages, and makes the unbalanced-entry and manual-ratio views trivial. Include `source` (manual vs system), `preparer`, `approver`, `transaction_date`, `posting_period`, `account_id`, `debit`, `credit`/signed amount, `memo`.
2. **Treat reconciliations and close tasks as their own tables** (with owner, due_date, status, open/close dates, reconciling-item amount+age) — the close-health KPIs in §2 need these and they do **not** come from the GL export.
3. **A `dim_account` (chart of accounts) with account_type is load-bearing** — three exception rules (uncoded, miscoded, seldom-used) plus the statement views all key off it. Seed it deliberately with a few "bad" codes/nulls so exceptions surface.
4. **Build the analytical views straight off §2/§3**: `v_close_health` (DTC, recon completion %, overdue/unassigned tasks), `v_reconciliations` (aged open items), `v_journal_activity` (volume, manual-JE ratio, reversal rate), `v_ownership_gaps` (null owners, preparer=approver), `v_dq_exceptions` (unbalanced, uncoded, out-of-period, duplicate, missing-memo). This 1:1 mapping keeps the catalog defensible in interviews.
5. **Seed synthetic data to intentionally trigger every exception and KPI** (a few unbalanced JEs, backdated postings, duplicates, null owners, aged reconciling items, a high manual-JE month) so each view returns non-empty, demonstrable results.
6. **Point the README/portfolio narrative at the dbt packages and BlackLine/auditor references** — showing the model derives from recognized ERP/close-ops conventions is the credibility payoff for a Finance Technology PM piece.

## Sources

- Fivetran dbt NetSuite package — https://github.com/fivetran/dbt_netsuite
- Fivetran dbt QuickBooks package — https://github.com/fivetran/dbt_quickbooks
- dbt Labs, financial modeling / accounting principles — https://docs.getdbt.com/blog/financial-modeling-accounting-principles
- MindBridge, Export the NetSuite general ledger — https://support.mindbridge.ai/hc/en-us/articles/360058018553
- RSM, Exporting full GL detail for your auditor (NetSuite) — https://technologyblog.rsmus.com/technologies/netsuite/exporting-full-gl-detail-auditor/
- BlackLine, 22 financial KPI metrics — https://www.blackline.com/blog/22-financial-kpi-metrics-for-future-ready-financial-operations/
- OneStream, 10 financial close KPIs — https://www.onestream.com/blog/financial-close-kpis/
- Trintech, 16 finance & accounting KPIs — https://www.trintech.com/blog/16-kpis-to-prioritize/
- Hyperbots, Manual journal entry (definition & metrics) — https://www.hyperbots.com/glossary/manual-journal-entry
- Greenskies Analytics, The complete list of JE tests — https://greenskiesanalytics.com/the-complete-list-of-je-tests/
- Arbutus, GL analytics tests for internal auditors — https://www.arbutussoftware.com/en/analytics-tests/-general-ledger/for-internal-auditors
- Numeric, General ledger reconciliation guide — https://www.numeric.io/blog/general-ledger-reconciliation
- eOne, Unbalanced GL entry distribution — https://www.eonesolutions.com/blog/finding-and-fixing-the-unbalanced-gl-entry-distribution-econnect-error-number-944/
- CORAA, Data integrity & verification / continuous validation — https://coraa.ai/blog/data-integrity-verification-audit-automation
