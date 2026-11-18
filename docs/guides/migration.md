# Migrate a space to the new workflow

This moves a space that already runs a lead, a work tab and kept managers onto the rebuilt rules. Nothing restarts until you say so, and running work is never cut off.

## What changed for a lead

- Review is `light` by default: one finder, and a fix-check only if it found a Blocker. `medium` and `intense` are opt-in.
- A review ends by round 3. An open Blocker at round 3 comes back to you; there is no round 4.
- `manager-send` writes `<worktree>/.owns` for each `/build` job: the node, the files it owns, and the Decided, Standing and Not-building lines. A commit outside those files is refused.
- A done report carries a `Done-check:` line, `pass` or `deviation`, with a quoted line for each deviation.
- A usage gate parks new starts near the 5-hour and 7-day limits. Running work finishes, and parked work resumes after the reset. [Configuration](../reference/configuration.md) has the thresholds and the override.

## Steps

Do these at a stage boundary, when no manager is mid-job.

1. Rebuild and install. If you layer your own config over core, rebuild that stack from its stack file first. Then run `./install.sh install`, and `./install.sh status` to check it.
2. Restart each kept manager. Close it, then start it again; the `keep` flag survives:

   ```sh
   manager-close <name> --force
   herdr-manager start <name> --dir <path>
   ```

   `herdr-manager list` shows each manager and whether its pane is live.
3. Restart the lead. Exit Claude in the `◆ lead` tab, run `claude` there again (`--resume <session-id>` keeps the conversation), then run `herdr-manager setup`. It re-registers the lead and opens any missing `▸ work` or `? ask` tab. To refresh a live work tab too, run `manager-close work --force` before `setup`.
4. Brief the lead with one line:

   ```
   [workstation] The workflow was rebuilt: light review by default, round cap 3, .owns, Done-check:, usage gate. Reread the engines you use.
   ```

## Plans in flight

A plan that was approved before the upgrade keeps its old shape. Add `legacy: true` to its frontmatter, on one line after `format:` (or `status:` when there is no `format:`):

```yaml
status: approved
format: v2
legacy: true
```

The owns hook lets a `legacy` plan through, so its nodes are not blocked for lacking `.owns`. Plans written after the upgrade do not need it.

## A space with named managers and no work tab

A space that runs three named managers and no work tab keeps that shape. Record the choice once, so `setup` never opens `▸ work`:

```sh
herdr-manager setup --no-work
```

Then restart each named manager and the lead as in the steps above. `herdr-manager setup --work` undoes the choice.

## An archived space

A restored space comes back with its old tabs and the old rules. Open Claude in the lead tab, run `herdr-manager setup`, restart any kept manager as above, and send the lead the `[workstation]` line.
