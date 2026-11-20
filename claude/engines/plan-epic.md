# Epic mode

Read with `engines/plan.md`: the interview, lookup, five answers, plan note and node table apply here too. The output is diagrams and a table, not a document: an epic design that gets skimmed has failed at its only job.

Done when: every child ticket, link and design page is read; the three questions in "Nothing here is gospel" are answered; the diagrams render; the review converged; the ticket table has acceptance and needs per row; every question the plan could not settle is listed.

## 1. Read what was asked for

The epic, every child ticket and **the comments as a separate fetch**: a thread is where scope changes and the body rarely catches up. `change-reader` returns each description and its comments verbatim; read that text, not the summary, and say where the two disagree. Then every ticket those link or name, in full with comments: the earlier attempt, the security bug and the rollout gate are where the constraints live. Then every design page and frame group, not only the linked frames; the last frame holds the state nobody mentioned. Then the code: worktrees pinned at fresh `origin/<base>`, detached, under `<repo>/.claude/worktrees/<epic-key>` for every repo touched.

Answer product questions from the epic, its stories and the designs before asking anyone. Only a real gap goes to product.

## 2. Attack the premise

Shape each change against `checklists/design.md`, `review-core.md`, `review-domain.md` and `design-review-shared.md`. `premise-attacker` takes the epic and nothing else, plus every `Decided:` item. It looks for the premise the code contradicts, the sibling repo that already does this, the measurement a constant beats, and inputs built for an output nobody validated. **A false premise at epic level is the most expensive thing in this workflow:** every ticket underneath inherits it and no code review reaches it. If the epic rests on something untrue, stop and say so; do not design around it.

## 3. Nothing here is gospel

Not the epic, the tickets, product's framing or the platform as it stands. Answer out loud before any diagram:

- **Is the platform the right shape to receive this?** Where a seam does not exist, either build the seam first as its own work, or hang the feature off something never meant to carry it (how platforms rot). Name the seam, say which option the epic takes, and say it in the summary.
- **Should something else be done first?** A missing abstraction three epics work around, a misplaced boundary, a migration everyone avoids: say *this epic is doable now, and that would make it and the next two smaller.* The owner judges; do not resolve it by proceeding.
- **Does product's reasoning hold?** Which claims about users, frequency and value are measured and which assumed, and the cheapest test of the biggest assumption.

A missing seam does not stop the run: name it, say which option the epic takes, and say it in the summary. Something to do first goes to the owner, never resolved by proceeding.

## 4. Decision records

If the repo keeps decision records, read all of them, not a search: split the directory across several `researcher` agents in one message, each given the design summary and returning one line per record (`NONE`, `AFFECTS` with constraint and quote, or `CONFLICT`). One `researcher` or `code-locator` is enough for a single question. Check every claimed conflict against the record's text yourself. Name any deviation.

**A conflict with a decision record stops the design.** Say which record and which part of the epic, and hand it back. Where the epic needs something no record covers and later work must follow, say so: it is a new architectural decision.

## 5. Draw the flow

A `sequenceDiagram` is almost always the shape. Which type, how to draw it and the render check: `engines/write.md` diagram decision. What makes one carry the design:

- `autonumber`, so a ticket can say "step 6".
- Self-calls for work inside a service; that is where most decisions live.
- Dashed returns (`-->>`) so a reply is visibly a reply.
- `Note over` for the threshold, algorithm or rule, numbers included.
- Participants are services or processes, never a sentence.

A second diagram, what owns what, when the epic moves a boundary: a component `flowchart TB` with one subgraph per service, the additions styled (an `erDiagram` for a pure schema epic). Together with the build-order flowchart from `engines/plan.md` "Diagrams" that is the full set: shape after, build order, main flow. Render all with `mmdc` and look at the images first. A `;` inside a sequence note or message breaks the parse.

## 6. Converge

Rounds, caps and the stop rule: `engines/review.md` plan mode, with the round shapes there. Lanes:

- `approach-reviewer`: authority, spoofing, races, duplicates, partial-failure exposure, plus the gap pass: product coverage, decision records and platform fit. For every "rendered from X", "mounted in Y" or "called via Z", find the code that produces it at that spot with a `file:line`, and look in the frontend and sibling repos for an existing client before choosing a transport.
- Mechanism audit, once the change plan exists: `premise-attacker` checks the mechanism every planned change relies on (a precondition, event, stream, hook point) and returns change / mechanism / exists-false-unverified.
- `clean-code`: cut what is not `Decided:`.

Every prompt carries every `Decided:` item and states that "no code exists yet" is not a finding. Verify every load-bearing claim before folding it in. Triage each round into verified, housekeeping, drop and unverified, and show the owner that split, never the raw list. A real fork (push vs poll, generic vs single-producer) goes to the owner with the long-term trade-off; never pick the cheaper option to save effort. Findings never shrink the ticket's scope: note them and keep the requirement.

## 7. Cut it into tickets

One table; each row is a ticket someone could pick up. If stories exist, map pieces onto them by ticket key; only prerequisites no story covers become new tickets, and stale story text gets a short comment, not a rewrite.

| Column | Holds |
|---|---|
| **title** | imperative, names the work not the file |
| **steps** | which numbered diagram steps it implements |
| **repo** | where it lands |
| **needs** | other rows by title, each as `needs <row>'s <data or file>`; real needs only |
| **acceptance** | one sentence; more than one means two tickets |
| **decision** | a question for a person, with a name against it; blocks its dependents |

A ticket nobody could reject independently of its neighbour is not a ticket. **Validate the output before building its inputs:** if the end deliverable has never been seen to work, the first ticket proves it. Where several tickets feed one deliverable, say which single ticket would be the whole thing at a smaller scale; that is usually first.

## 8. Report back

Chat, short: the verdict; **Platform** (the seam, whether it exists, the option taken); **Do first** (or nothing); the diagrams; the table; **For the owner to check**, one line per question the plan could not settle and who or what would settle it; the one thing that would make the epic unnecessary, if it exists. Never fold a question into an assumption: at epic scale it surfaces as rework three tickets in.

Create no stories yet: the ticket table stays as drafts in the note, and after approval one Out ask: "create N stories, optional wiki page".

## Where the artifact lives

The plan note holds the diagrams as Mermaid blocks and the ticket table. `seq.mmd`, `owners.mmd`, `order.mmd` (build order) and their PNGs sit in `${DRAFTS_DIR:-~/drafts}/projects/<slug>/<epic-key>/`, linked by path. A wiki page only if the team will work from it, and only after the owner says so.

To show the team, publish one private page with the Artifact tool: where things stand today; all three diagrams as native `<pre class="mermaid">` blocks with `<` `>` `&` escaped; the design screens as a click-to-enlarge gallery uploaded through `files`; the build table grouped by tracker story, prerequisites first; the decisions and risks carried forward. Keep the HTML as a template in the same folder with `{{SEQ}}` / `{{OWNERS}}` / `{{ORDER}}` placeholders and republish with `url` to keep the link. Recover a lost copy with `Artifact read`.

Changes built from the epic carry its sequence and owners diagrams unchanged in Screenshots: same source, same colours. Render with `mmdc -c ${DRAFTS_DIR:-~/drafts}/projects/<slug>/<epic-key>/artifact-theme.json -b '#f5f7fa'` and put the change's own slice beside them.
