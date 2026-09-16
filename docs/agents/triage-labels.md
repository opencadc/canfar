# Triage Labels

Engineering skills use five canonical triage roles. Apply each role as a Jira
status or a GitHub issue label, according to the work item's tracker.

| Skill role | Jira status | GitHub label | Meaning |
| --- | --- | --- | --- |
| `needs-triage` | `To Do` | `needs-triage` | A maintainer needs to evaluate the issue |
| `needs-info` | `On Hold` | `needs-info` | Waiting for more information |
| `ready-for-agent` | `In Progress` | `ready-for-agent` | Fully specified and ready for an agent to implement |
| `ready-for-human` | `Review` | `ready-for-human` | Requires human implementation or review |
| `wontfix` | `On Hold` | `wontfix` | Will not be actioned |

## Jira

When a skill says to apply a canonical triage label, use the mapped Jira status
through an available workflow transition. Keep the `CANFAR` label on work in
the `CADC` project and preserve other existing labels. Do not create Jira labels
named after the roles merely because a generic skill assumes a label-based tracker.

`needs-info` and `wontfix` intentionally share `On Hold`. Consult the issue's
triage explanation to distinguish them; the status alone is insufficient.
When triaging, record the reason and any information needed to resume work.
These roles describe the triage workflow, not every status in the Jira project.

## GitHub Issues

Use the existing labels in `opencadc/canfar`. When changing the triage role,
replace the previous canonical triage label and preserve unrelated labels,
including `PRD`. These labels describe the role; issue closure is a separate
action governed by the requested workflow.
