# Triage Labels

This table maps the engineering skills' triage roles to the intended GitHub label names. It defines vocabulary, not which labels currently exist.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

Before assigning a role, run `gh label list --limit 100` in the repo. If its mapped label is absent, create it with `gh label create <name> --description "<meaning from the table>"`, then apply it to the issue. Completion requires the mapped label to appear on the issue.

Keep this mapping authoritative when changing the triage vocabulary.
