# Project board: Finance Intelligence

Issues for work under **`finance-close-intelligence-platform/`** are tracked on the
**Finance Intelligence** GitHub Project (a Projects v2 board owned by `spmcgraw`).

GitHub has no notion of "which folder I'm working in," so a **label** is the bridge:
every issue for this folder carries `finance-close`, and the board's automation keys
off that label.

## The rule for agents

When creating an issue while working under `finance-close-intelligence-platform/`:

1. **Label it** `finance-close` on creation:
   `gh issue create --title "..." --body "..." --label finance-close`
2. That label triggers the Project's built-in **Auto-add** workflow, which adds the
   issue to the board and sets its **Status** to **Backlog**.
3. **Set the correct Status** for the issue's real state (see mapping below) —
   auto-add only ever lands it in Backlog.

## Status mapping

| Status        | Meaning                                            |
| ------------- | -------------------------------------------------- |
| `Backlog`     | Blocked, or not yet prioritized (the default)      |
| `Ready`       | Unblocked and ready to start                       |
| `In Progress` | Actively being worked                              |
| `Done`        | Closed / completed                                 |

Set Status when the state changes: move to `Ready` once an issue is unblocked and
scoped, to `In Progress` when work starts (typically alongside `gh issue edit <n>
--add-assignee @me`), and let closing the issue drive `Done`.

## Setting status with `gh`

`gh project` commands require the `project` scope. If you hit
`missing required scopes [read:project]` or `[project]`, run once:

```
gh auth refresh -s project
```

Status is a single-select field on the Project, so setting it needs three IDs:
the Project id, the Status field id, and the target option id. Discover them once:

```bash
# Project number (find "Finance Intelligence" in the list)
gh project list --owner spmcgraw

# Project node id + the Status field id and its option ids
gh project field-list <project-number> --owner spmcgraw --format json \
  | jq '.fields[] | select(.name=="Status") | {fieldId:.id, options:.options}'

gh project view <project-number> --owner spmcgraw --format json | jq '.id'   # PVT_... project id
```

Then, for a given issue already on the board:

```bash
# The item id for this issue on the board
ITEM=$(gh project item-list <project-number> --owner spmcgraw --format json \
  | jq -r '.items[] | select(.content.number==<issue-number>) | .id')

gh project item-edit \
  --project-id <PVT_project_id> \
  --id "$ITEM" \
  --field-id <status_field_id> \
  --single-select-option-id <option_id_for_desired_status>
```

To add an issue to the board manually (if auto-add hasn't fired yet):

```bash
gh project item-add <project-number> --owner spmcgraw \
  --url https://github.com/spmcgraw/Portfolio/issues/<issue-number>
```

## One-time board setup (owner, in the GitHub UI)

These live on the Project itself, not in this repo:

1. **Status field** — ensure the Status single-select has options
   `Backlog`, `Ready`, `In Progress`, `Done` (add `Backlog` / `Ready` if the board
   still has the default `Todo`/`In Progress`/`Done`).
2. **Workflows** (Project → ••• → *Workflows*):
   - *Auto-add to project* → filter `is:issue label:finance-close` → enable.
   - *Item added to project* → set **Status = Backlog**.
   - *Item closed* → set **Status = Done**.
