# Finance Close Intelligence Platform

> A portfolio case study by a Finance Technology PM / Finance Data Product Owner.
> Built to show product thinking applied to the financial close — not a production system.

## The one-line pitch

A prototype analytics platform that turns the messy, deadline-driven **financial close** into a set of measurable, monitorable signals — close health, reconciliation status, journal activity, ownership gaps, and data-quality exceptions — on top of a realistic (synthetic) close dataset.

## Why this exists

The month-end close is where finance operations live or die: reconciliations pile up, journal entries get posted late or unbalanced, tasks lose their owners, and nobody has a single view of whether the close is on track until it's already late. Most teams manage this in spreadsheets and status emails.

This project asks a product question: **if you treated the close as a data product, what would you measure, and what would the dashboard look like?** It answers that end to end — data model, analytics, and a dashboard spec — so the thinking is concrete rather than hand-wavy.

The audience is a hiring manager evaluating whether the author can (a) understand a finance domain deeply, (b) shape it into a data product, and (c) coordinate the technical build. Credibility over complexity.

## What's in the box

- A **PostgreSQL** relational model of the close, seeded with synthetic close data designed to exercise every metric and exception.
- **Analytical SQL views** for close health, reconciliations, journal activity, ownership gaps, and data-quality exceptions.
- **Python** scripts to generate, load, and validate the data.
- A **Power BI-ready** output layer plus a documented dashboard spec and screenshots.
- A **product-doc set**: problem brief, personas, capability map, roadmap, user stories with acceptance criteria, and a governance model.

> **Status:** early scaffold. The folder tree, this README, and the first-draft docs are in place; the data model, SQL, Python, and Power BI layers are being built out. See [`docs/`](docs/) for the current thinking and each folder's README for the repo tour.

## Repo tour

| Path | What lives here |
|---|---|
| [`docs/`](docs/) | Product & technical docs — problem brief, architecture notes, and the growing doc set. |
| [`docs/research/`](docs/research/) | Grounding research the model and metrics are built on. |
| [`data/`](data/) | Synthetic close data at each pipeline stage (`raw`, `processed`, `sample`). No real data, ever. |
| [`sql/`](sql/) | PostgreSQL model plus the analytical layer — `views/` and `quality_checks/`. |
| [`python/`](python/) | Data generation, load, and validation tooling, with `tests/`. |
| [`powerbi/`](powerbi/) | Dashboard spec, layout `diagrams/`, and `screenshots/`. |

## Design principles

- **Grounded in real close-ops conventions.** The model and metrics derive from recognized ERP data models and close-management practice, not invented from scratch (see [`docs/research/`](docs/research/)).
- **Synthetic, but realistic.** The seeded data deliberately contains the messiness a real close has — so every metric and exception has something real to show.
- **Portfolio-honest.** Where something is a deliberate simplification, the docs say so.

## Where to start reading

1. [`docs/problem-brief.md`](docs/problem-brief.md) — the problem, the users, and what "good" looks like.
2. [`docs/architecture-notes.md`](docs/architecture-notes.md) — how the pieces fit together technically.
