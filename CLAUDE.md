# Portfolio

A portfolio repository holding folders of individual projects.

## Working conventions

- **Branch from `main` before starting any work.** Never commit directly to `main`.
  Start each piece of work with `git switch main && git pull && git switch -c <branch>`.
- **Work in the main checkout, not a git worktree.** This is a solo repo, so make
  changes on a branch in the normal folder structure — new files should appear in the
  directory they belong to. Do not use the worktree tooling for interactive sessions.
  (Exception: background / cloud agent jobs may isolate in `.claude/worktrees/` because
  that harness enforces it; those branches still merge back into the normal layout.)

## Agent skills

### Issue tracker

Issues are tracked as GitHub issues in `spmcgraw/Portfolio` via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default canonical triage labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

### Project board (Finance Intelligence)

Issues for work under `finance-close-intelligence-platform/` are labelled `finance-close` and tracked on the **Finance Intelligence** GitHub Project, with Status set per its state (Backlog/Ready/In Progress/Done). See `docs/agents/project-board.md`.
