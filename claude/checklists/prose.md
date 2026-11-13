# Prose checklist

The single home of the prose rules for anything a colleague reads. Process: `engines/write.md`.

Further reading: [Wikipedia, "Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), [Google, "Writing a CL description"](https://google.github.io/eng-practices/review/developer/cl-descriptions.html), [GOV.UK style guide](https://www.gov.uk/guidance/style-guide), [Microsoft Writing Style Guide](https://learn.microsoft.com/style-guide/welcome/).

## Killer items

Quote the numbers you checked. These are the ones that cost credibility when missed.
1. No banned word (delve, foster, leverage, utilize, facilitate, empower, streamline, robust, transformative, and the rest of §1).
2. No binary contrast ("not X, it's Y") and no colon reveal; state the point (§4).
3. No faux-insight setup, throat-clearing opener or fake-profound kicker (§4).
4. No summary-recap ending; stop on the last concrete point (§4).
5. No em dashes (§3).
6. No weasel attribution: a named source or no claim (§4, §5).
7. A verified fact is stated flat; only a judgement is hedged and labelled as one (§5).
8. Under the length cap for the artifact type (§6).
9. Registers followed: change title format, review-comment framing, commit message with no ticket ID (§7).
10. Every line names what was done, not the identifiers touched; no section exists only to be filled (§8).

## 1. Plain words

- No jargon, Latin, or formal abstraction where a plain word says it.
- Second person over impersonal "we" or "one".
- Cut empty intensifiers (just, really, truly, genuinely). Keep one only when it carries real emphasis or the writer's natural voice.
- Cut hedges that dodge commitment (arguably, seemingly, perhaps, essentially).
- Cut filler that delays the point (it's worth noting, at the end of the day, in order to, going forward). Keep a phrase that is part of the writer's recognisable voice and earns its place.
- Banned outright: inflated or stock vocabulary such as delve, leverage, utilize, robust, plus any other word that reads as brochure copy. Several in one paragraph means rewriting the paragraph.
- Business-jargon swaps: navigate → handle/address; unpack → explain; lean into → accept; landscape → situation; deep dive → analysis; take a step back → reconsider; moving forward → next; circle back → return to.

## 2. Sentences

- Active voice, human subject doing something. No inanimate thing performing a human verb ("the config was changed", "the error resolves itself": name who changed it, who fixed it).
- Mix sentence length; break up three consecutive sentences of the same length.
- No sentence starts with a Wh- word (What, When, Why, How); restructure around the subject.
- One idea per sentence. Split when genuinely hard to follow; keep a longer sentence when it's clear and carries the writer's own rhythm.
- Verbs do the work: "made a decision" → "decided"; "has the ability to" → "can".
- Prefer "is" and "has" over a fake-strong verb: "acts as a storage layer for lookups" → "stores lookup results by key".
- Repeat the right word; don't rotate synonyms for style: "The CLI parses the file. The tool validates the input. The utility prints errors" → "The CLI parses the file, validates it, and prints errors."

## 3. Structure and formatting

- No bullet list where two sentences read better; no heading over a two-sentence section.
- No emoji in headings, except a team template that already uses them, copied exactly (tracker tickets are one).
- No bold mid-sentence.
- No title-case headings.
- No heading that repeats the doc's own title, no heading containing only further headings.
- No em dashes. Use a colon, full stop or comma.
- No curly quotes or smart apostrophes in plain text output.
- No inline-header vertical lists, no unusual table for content that's better as prose.

## 4. AI tells

- Binary contrasts: "not X, it's Y" and its variants. State Y directly.
- Negative listing: "Not a X. Not a Y. A Z." State Z.
- Rule of three: lists of exactly three read as templated. Two items, or one, usually lands better.
- Colon reveals: a short label, a colon, then a staged payoff ("The catch: the cache never expires.", "The upside: startup is instant."). Rewrite as a plain sentence ("The cache never expires, which is the catch."). Use colons for lists, labels, and quotes, not staged drama. Prefer sentence case after a colon unless grammar, a proper noun, a title, or code requires otherwise.
- Faux-insight setups and throat-clearing: lines that announce a claim before making it ("here's the thing", "most people miss this", "let me be clear"). Cut the setup, make the claim stand alone.
- Superficial analysis: trailing "-ing" clauses that gesture at meaning without showing it ("highlighting the team's commitment", "reflecting broader trends"). Say the concrete effect or cut the clause.
- Importance puffery: sentences that tell the reader something matters instead of showing it ("a key milestone", "plays a major role"). State the fact, let the reader judge.
- Weasel attribution: a claim credited to nobody in particular ("studies show", "many believe"). Name the source or cut the claim. If there's no source, ask instead of inventing one.
- Summary-recap endings: "in conclusion", "overall", a final paragraph restating the piece. End on the last concrete point instead.
- Fake-profound kickers: a closing line turned into a mic-drop metaphor. Delete it; don't rewrite it into a better metaphor or preserve its rhythm. End on the clearest concrete sentence already there, or if the ending needs more closure, add a plain takeaway or next action.
- Interpretive metadiscourse: lines that step outside the subject to tell the reader what to notice ("note that", "this part is important"). Delete the aside, or replace it with the fact it pointed at.
- Rhetorical setups: a question posed only to answer it, or a teaser before the point ("guess what happened next"). Drop them, make the point.
- Robotic rhythm: repeated sentence shapes, identical paragraph structures, stacked punchy fragments, a paragraph that always ends on a punchy one-liner. Vary the shape.
- Trust readers: state facts directly, skip justification and hand-holding.
- Narrator-from-a-distance: "nobody designed this", "people tend to". Put the reader in the scene, use "you".
- Hedging on things you could check: "it appears", "may suggest", "tends to". If it's a fact, check it and state it; if it's an opinion, say so plainly instead of hedging the wording (§5).
- High density of AI vocabulary words is itself a tell independent of any single word: if several banned words cluster in one paragraph, rewrite the whole paragraph rather than swapping words.

## 5. Honesty

- State a verified fact flat, with no hedge: "Nothing reads `retry_limit`", not "it appears nothing reads it."
- Hedge only a judgement, and say so as a judgement: "probably worth its own ticket."
- Never claim something you didn't check. Run it, or say what you couldn't check and why: "All hooks pass" is a claim, so run them; "12 integration tests deselected without a database" beats silence.
- Say what ran versus what was only read; name the changed files you didn't read. (`engines/review.md` "Reviewer conduct")
- Portability test: if a sentence would read unchanged about another product or company, it's filler. Cut it or make it specific to this.
- Every claim in a change description, the ticket or chat message is one you ran or read; say which. (`checklists/build.md` §3)
- No citation or URL you did not open. (`checklists/build.md` §3)

## 6. Length

Hard caps, not guidance. Over the cap means cut, not reformat. The table below is the source.

| Artifact | Cap |
|---|---|
| Change description | 120 words |
| Ticket description | 150 words |
| Review comment | 3 sentences |
| Plan / design doc | 40 lines |
| Chat reply | answer first, no paragraph over 3 lines |

## 7. Registers

### Change title
Follow the repo's title format (recent merged titles show it). Command-style, present tense: "Remove the cache", not "Removing the cache". Verb, object, stop. No tagline: no comma flourish ("..., with backoff"), no "not X" contrast, no trailing kicker. Say the change, not the area. Needs a comma or an "and": it is two changes or a worse sentence.

### Change description
Open with the problem being solved, then why this approach over the others. A bug number or benchmark figure beats description. Keep what the diff cannot show: the reasoning, what will look like a bug and is not, ordering constraints, anything unsettled, what you ran. Cut: file-by-file walks, counts and methodology, restating the ticket, side fixes, your own process.

### Review comment
3-sentence cap. Blocking findings state the break, the cost, and the fix; non-blocking findings are framed with a non-blocking prefix such as `Should fix:` or `Nit:`, blank line after. Fewer comments beat many. Ask a question when the author may know something you do not. Defer to whoever owns the decision, such as the design lead on a design call. Full framing: `engines/review.md` "Comment style".

### Reply to a review comment
Concede what's right first, then the evidence. No defensiveness, no re-litigating a point already conceded.

### Ticket
Summary: six to eight words, verb and object, no key or prefix decoration, same no-tagline rule as a change title. A summary names the work, not the area. Body: the problem in plain words first, the real cause named, identifiers and numbers in backticks, verified things flat, guesses labelled with what would settle them. A section with five or more bullets holds something that belongs elsewhere. Given/When/Then only for story acceptance criteria.

### Ticket comment
Same register as a review comment: facts flat, the specific file or number, no filler section that exists only to be filled.

### Chat message
Conversational register, same bans as everywhere else: no banned words, no rule-of-three. Short items, not padded sentences.

### Commit message
Follow the repo's commit convention. Command-style summary line. The body gives the problem and the reason for the change, not a line-by-line diff.

### Code comment and docstring
Explain why, never what. Full rule: `~/.claude/CLAUDE.md` "Comments".

### Note
One current statement, not an append log: no dated "update:" tails. Links sit in a sentence that says why the target matters.

## 8. Content

- Write what you did, not what you named: "Added the missing retry settings to the worker", not "`fooCfg` + `barMap`". Identifiers belong where someone can act on them, not in a summary. Read the line aloud; if you would not say it to someone at a desk, rewrite it.
- Depth comes from the number of items, not their length: eight things done is eight short lines of three to eight words plus a reference.
- Fill a section only when you have something for it. A heading followed by "N/A" or a restated summary is worse than none. When a template demands it and there is nothing, one clause saying why: `N/A, docs only.` A template is a menu, not a checklist.
- Concrete over abstract: the file, the function, the number, the date. "cut run time from 10 minutes to 2" beats "improved". Backticks for every identifier, path and command.
- Leave your process out: rounds of review, which agent found what, how many repos you searched, what you tried first, rebases and re-runs. Counts and methodology belong in a commit body. Write from the current state as though producing it today.
- Trim, don't append: anything open for a while accretes a paragraph per round of feedback. Rewrite from what the thing is now.
- The delete test: remove a sentence; if the reader reaches the same conclusions and takes the same actions without it, leave it deleted.
- Write for someone who does not own the domain: the first sentence says what happens, in words with no identifiers in them; evidence underneath. If explaining a piece of writing takes longer than the writing, rewrite it. Plain English is the first draft, not a follow-up.
- Use the team's spelling (British or American) and keep it consistent across a document.
- Editing someone's draft: keep their point and voice, cut only what breaks a rule here, leave sentences that read like a person wrote them. Add no claims, numbers or examples the draft lacks. Keep real hedges and blunt asides.
