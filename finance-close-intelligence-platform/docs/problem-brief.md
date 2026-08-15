# Problem Brief — Finance Close Intelligence Platform

> First draft. A starting point to refine, not final copy. Personas, capability map,
> and detailed user stories are their own documents and are intentionally only gestured at here.

## The problem

The **financial close** — the process of finalizing the books at the end of each accounting period — is recurring, deadline-bound, and cross-functional. It depends on hundreds of small tasks completing in order: reconciliations getting done, journal entries getting posted correctly, exceptions getting cleared, and sign-offs happening on time.

In most organizations this process is managed with spreadsheets, checklists, and status emails. The result:

- **No single view of close health.** Whether the close is on track is a matter of asking around, not looking at a number.
- **Reconciliations and tasks lose their owners.** Work slips because nobody notices it's unassigned or overdue until the deadline.
- **Data-quality problems surface late.** Unbalanced or miscoded entries are often found during review or audit rather than as they happen.
- **No trend visibility.** Teams can't see whether the close is getting faster or slower over time, or where the recurring bottlenecks are.

## Who has this problem

At a high level (personas are developed in a separate doc):

- **The Controller / Close Owner** — accountable for the close finishing on time and clean; needs a status-at-a-glance view.
- **Accountants / Preparers** — do the reconciliations and journal entries; need to see what's theirs and what's overdue.
- **Finance leadership (CFO / VP Finance)** — cares about trend, risk, and control, not line-item detail.
- **Internal audit / controllership** — cares about data-quality exceptions and segregation-of-duties signals.

## What "good" looks like

A close where the people running it can answer, at any moment and without asking around:

- *Are we on track to close on time?* (cycle time, task completion, reconciliation status)
- *What's stuck, and whose is it?* (overdue and unassigned work)
- *Is the data clean?* (exceptions — unbalanced, miscoded, out-of-period, duplicate entries)
- *Are we getting better?* (period-over-period trend)

## Scope of this prototype

**In scope:** a realistic model of the close and the analytics/dashboard layer that answers the questions above, on synthetic data.

**Explicitly out of scope** (deliberate simplifications for a portfolio piece): live ERP integration, production deployment and orchestration, authentication, a hosted live dashboard, and advanced accounting complexity (multi-currency consolidation, intercompany eliminations) beyond what's needed to illustrate the concepts.

## Success criteria for the case study

The prototype succeeds if a finance-technology hiring manager reading it comes away believing the author can understand the close domain, frame it as a data product, and drive the build. Concretely: the metrics and exceptions are recognizable to a close practitioner, the seeded data makes every one of them demonstrable, and the docs tell a coherent product story.

---

*Metrics definitions, the data-quality exception catalog, and the analytical-view catalog are grounded in [`research/reference-close-models.md`](research/reference-close-models.md). The specific data model and schema are defined separately as the build progresses.*
