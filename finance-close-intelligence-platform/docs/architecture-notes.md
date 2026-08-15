# Architecture Notes — Finance Close Intelligence Platform

> First draft. Describes how the pieces fit together and why, at the level of layers and
> responsibilities. The concrete data model / schema, the exact SQL, and the Python and Power BI
> internals are defined in their own work — this doc gestures at their shape, it does not fix it.

## The stack, top to bottom

The platform is a small, conventional analytics stack chosen for clarity and portfolio credibility rather than scale:

| Layer | Technology | Responsibility |
|---|---|---|
| Synthetic data generation | **Python** | Produce realistic close data (entries, reconciliations, tasks, owners) with intentional messiness. |
| Storage & relational model | **PostgreSQL** | Hold the close data model; enforce keys and types; the single source of truth. |
| Analytics | **SQL views** (in PostgreSQL) | Turn the raw model into close-health, reconciliation, activity, ownership, and data-quality signals. |
| Validation | **Python + SQL checks** | Load-time and standalone data-quality checks over the seeded data. |
| Presentation | **Power BI** | Consume analytical output tables; present the close as dashboards. |

## Why PostgreSQL

PostgreSQL is the engine for the relational model and the analytical views. It's the right fit here: free and ubiquitous (anyone can clone and run this), strong SQL support for the window functions and aggregations the analytical layer needs, and credible as the kind of warehouse-adjacent store a finance analytics team would actually use. All model DDL and analytical views target Postgres.

## How data flows

```
Python generator  ──▶  data/raw  ──▶  load into PostgreSQL  ──▶  analytical SQL views
                                              │                          │
                                              ▼                          ▼
                                        validation checks        Power BI output tables
                                                                         │
                                                                         ▼
                                                                  Power BI dashboards
```

1. Python generates synthetic close data seeded to trigger every metric and exception.
2. The data is loaded into the PostgreSQL model.
3. Validation checks confirm the load and surface data-quality exceptions.
4. Analytical views compute the close signals directly on the model.
5. Power BI reads the output tables and renders the dashboards.

## The data model (shape, not schema)

The relational model is defined in its own work; these notes only sketch its intended *shape*, grounded in the research ([`research/reference-close-models.md`](research/reference-close-models.md)):

- A **journal/GL fact at distribution-line grain** (one row per debit/credit line) sitting under a journal-entry header — mirroring how real ERP GL exports and open-source finance data models are structured.
- **Reconciliations and close tasks as first-class tables** (with owners, due dates, status, and reconciling-item detail) — these drive the close-health KPIs and don't come from the GL.
- A **chart-of-accounts dimension** that the exception rules and statement logic key off, seeded deliberately with a few "bad" codes so exceptions surface.

The exact tables, columns, keys, and DDL are intentionally **not fixed here** — that's the data-model work's to own.

## The analytical layer (catalog, not queries)

The analytics resolve to a small catalog of views, one per question the close asks — close health, reconciliations, journal activity, ownership gaps, and data-quality exceptions. The precise view definitions, columns, and SQL live in [`../sql/`](../sql/) and are grounded in the metric and exception definitions in the research. This doc names the catalog; it doesn't write the queries.

## The presentation layer

Power BI consumes a set of **output tables** produced from the analytical views (not the raw model directly). The output-table spec and dashboard layout are defined separately; deliverables are the spec, layout diagrams, and screenshots — not a hosted live report.

## Deliberate simplifications

This is a portfolio prototype, so several production concerns are consciously out of scope: no live ERP integration (synthetic data only), no deployment/orchestration/auth/CI, no hosted live dashboard, and no advanced accounting complexity beyond what illustrates the concepts. These are choices, not gaps — called out so the boundaries of the prototype are honest.
