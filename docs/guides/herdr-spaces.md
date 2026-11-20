# Herdr spaces

A herdr space splits one workspace into two Claude tabs so the expensive model stops re-reading big contexts. That roughly halves the cost.

| Tab | Model | Job |
| --- | --- | --- |
| `◆ lead` | Opus | Plans, answers the work tab's questions, runs the final whole-change check |
| `▸ work` | Sonnet | Owns the plan: builds nodes in parallel, reviews and babysits. You can talk to it directly |

## Install

Install [herdr](https://herdr.dev) yourself. It is Apache-2.0 and is not bundled. Then run `./install.sh install`.

## Set up a space

Once per space, open Claude in the tab you want as lead and run:

```sh
herdr-manager setup
```

It renames the tab `◆ lead` and opens `▸ work` after it with `WORKSTATION_LEAD_PANE` set to the lead's pane. Run it again to repair a missing `▸ work` tab.

## Daily use

1. Plan with the lead.
2. To build, the lead clears the work tab and hands it the plan with a plain `herdr agent prompt` that first tells it to re-read the work brief, so a brief change applies after `/clear`.
3. Work starts a `/loop`, pushes every ready node in parallel and asks the lead only for a decision beyond the plan.
4. When every node is green, work sends the lead `done, check <plan path>` and the lead runs the final `/verify-self`.

## Troubleshooting

- Startup prompts are answered for you: folder trust and external `CLAUDE.md` imports, only under the lead's folder. Anywhere else, run `claude` there once to trust it.
- To stop a stuck shell, run `shell-reap <pid>`, never `kill`.
