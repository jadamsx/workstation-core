# Checklists and disciplines

Both are short files an engine or a plan node loads when it needs them. Each rule lives in one of them and nowhere else.

## Checklists

A checklist opens with killer items: skipping one causes real damage, and the report quotes the numbers checked. Everything else sits under Reference, read on demand. Files are in `claude/checklists/`.

| Checklist | Used when |
| --- | --- |
| `build.md` | The author checks its own diff before review |
| `design.md` | Before code exists: the five questions and the design rules |
| `design-review-shared.md` | Data, API, security, failure modes, capacity, observability and rollout, asked once at design time and again on the diff |
| `review-core.md` | Every review works from this list |
| `review-domain.md` | The diff touches concurrency or UI |
| `ui-verify.md` | A node changes a route, component or user-visible flow |
| `prose.md` | Anything a colleague reads is written |

## Disciplines

A discipline is a way of working that a plan node names. It has Rules, Proof (the check run before handing back) and Stop (when the node ends, and what to report if it ends early). Files are in `claude/disciplines/`.

| Discipline | Fits |
| --- | --- |
| `tdd` | New behaviour with a clear input and output, where the test comes first |
| `reproduce-first` | A bug or small change where the failure can be shown before the fix. Extends `tdd` |
| `investigate-first` | An unknown cause, intermittent behaviour or a performance regression. The output is a cause, not a fix |
| `refactor` | Extraction, consolidation or an ownership move with no behaviour change |
| `migration` | Schema, data, API, protocol, configuration or dependency transitions that need a rollback and proof that data survives |
| `acceptance-first` | New behaviour, a product slice or an integration, where the risk is building more than was asked |
| `spike` | A time-boxed question about feasibility or approach. The output is a finding and the code is thrown away |

## Adding one

Copy `claude/templates/checklist.md` or `claude/templates/discipline.md`. [Make it yours](../guides/make-it-yours.md#add-a-domain-checklist) has the steps.
