# Design and review: shared concerns

Seven concerns come up twice, once as a question before the code exists (design) and once as a check on the diff (review). One file holds both halves so a rule changes in one place.

## Killer items

1. Identity comes from the verified context only; privileged fields (actor, owner, audience, role, actions) are never caller-supplied.
2. Input at a trust boundary is validated; no interpolation into queries, shells, paths or templates.
3. No failure reads as empty: a read that errors raises, a write helper's count is checked.
4. Every external call has a timeout and a stated outcome on 5xx and network error.
5. Migrations: `up` runs twice, `down` removes only what `up` created, existing data is backfilled or tolerated.
6. Every consumer of a changed shape or contract was found on `origin/<base>`, not assumed.
7. Deploy order of config, migrations and flags is safe either way or stated; each step has a rollback.
8. Pagination and result sets are bounded; new background work is visible when it dies.

## Reference

## Security and privacy

### Review
- **Authentication:** identity comes from the verified context only, never a parameter, and privileged fields (actor, owner, audience, role, actions) are never caller-supplied.
- **Session:** tokens expire, are revoked on logout or privilege change, and aren't fixed or reused across users.
- **Access control:** checked at the right layer; no IDOR; the tool re-checks authority itself; every claimed gate followed to the code that runs it, with bypass paths named.
- **Validation and encoding:** bind variables, never interpolation, and shell, path, template and HTML output escaped.
- **Cryptography:** no home-grown crypto; secrets from config or secret storage, never hard-coded or logged.
- **Errors and logging:** no stack traces or driver text returned to callers; security events logged.
- **Data protection:** PII and secrets aren't stored, returned or logged beyond need. An ungated read is acceptable only when its rows never reach a caller or it's pinned to the server-resolved identity.
- **Communications:** TLS enforced, and no secrets in URLs.
- **Business logic:** a workflow can't be skipped, reordered or replayed by a malicious caller (approval, payment, state machines).
- **Files and APIs:** uploads validated by content; size and rate limits on anything a caller can make large.

### Design
- Threat model: who reaches this, and what do they control? Reach it the way a real caller does.
- Is identity taken from verified context only, never a caller-supplied parameter?
- Are privileged fields (owner, role, action, audience) never caller-supplied?
- Is PII or secret data stored, logged or returned only when required, with expiry enforced?

## Failure modes and error handling

### Review
- Fail fast, with domain-specific exceptions and no bare `except`. (CLAUDE.md)
- **Failure reported as success:** follow every read to the function that runs it. A helper that swallows an error into `[]`, `None` or `{}` makes a failure look empty.
- Write helpers returning counts have them checked. A silent no-op isn't success.
- Retries are bounded, with backoff, and logged on the final attempt. Loops that retry or page end even when nothing changes. (CLAUDE.md)
- In a multi-step operation, the state left when a middle step fails is recoverable, retried or reported.

### Design
- For each external call, what happens on timeout, 5xx, or a network error?
- Is state recoverable, retried, or reported when a middle step of a multi-step operation fails?
- When this is wrong, what's the most likely direction it's wrong in, and what does that cost the reader of the output? A confidently, stably wrong result is worse than a noisy one; noise eventually looks like noise. Caveats in a docstring rarely survive into a summary.

## Performance and capacity

### Review
- No N+1 queries. Pagination and result sets bounded, with caps that fetch limit + 1 and refuse past the cap rather than truncate.
- Connections, files and tasks closed. Timeouts set on every outbound call.
- No unbounded memory, and no work in a hot path that could be cached or done once.
- Indexes exist for the new query shapes.

### Design
- Is there a rough estimate of QPS, concurrency, storage or memory footprint for anything new?
- Are there N+1 shapes or unbounded loops designed in from the start, and are indexes planned for new query shapes?

## Observability

### Review
- Failures are logged at the right level with enough context to act on (ids, not payloads). (CLAUDE.md Errors)
- No secrets or PII in logs. (OWASP)
- New background work (consumers, jobs, retries) is visible: logged, metered or alertable when it dies.

### Design
- Will failures be logged with enough context to act on (ids, not payloads)?
- Is new background work (consumers, jobs, retries) visible: logged, metered, or alertable when it dies?

## Data and migrations

### Review
- Ids are normalised wherever a key, filter or lookup is built.
- Status sets are complete and shared across producer, consumer and schema, and unknown values are refused.
- Producer and schema agree on field placement, nullability, required fields and enums.
- Migrations: `up` can run twice; `down` removes only what `up` created; existing data is backfilled or tolerated.

### Design
- If this touches schema, does the migration run up and down cleanly, twice (`up` can run twice; `down` removes only what `up` created)?
- Is existing data backfilled or explicitly tolerated?
- Are ids normalised and status sets complete and shared across producer, consumer and schema?

## API and contracts

### Review
- Return shapes, error strings and status codes callers read are unchanged, or every caller is updated, found through references.
- The public surface is the minimum, because an interface is the hardest thing to walk back.
- Versioning or feature-flagging for anything external consumers depend on.

### Design
- Do return shapes, error strings or status codes change for existing callers?
- Has every caller of the changed surface been found, not assumed?
- Is versioning or feature-flagging in place for anything external consumers depend on?

## Config, rollout and deploy order

### Review
- Config, migrations and flags are safe to deploy in either order, or the order is stated in the change.
- Generated files are not hand-edited.
- A new dependency is needed, maintained, licence-compatible and pinned in the manifest and lockfile. Reuse beats adding.
- Secrets and environment-specific values come from config, not code. (OWASP)

### Design
- Can config, migrations and flags deploy in either order, or is the order stated explicitly?
- Is there a rollback plan for each deployment step?
- Are feature flags in place for anything risky, with both states testable?

## Ops readiness (plan fields `signals`, `flags`, `migrations`, `deps_added`)
- The new path emits a metric or log a person could page on, and an alert exists for it in the repo's alert files.
- Each flag is tested on and off, and its default is the safe one.
- Revert is safe: no one-way migration or data change hides in the change; the migration ran up, down and up on a copy with realistic rows.
- A runbook line says how to tell it is broken and how to undo it.
- New dependencies have an audit result and a licence that is not copyleft or unknown. (SDL)
- Logs, traces and events carry no personal data or secrets; a named telemetry event fires with the planned fields. (SDL privacy)
- A path that calls a model has a token or cost bound. (AWS cost lens)
