# Analysis: run-command

## Missing Tests

- [ ] `timeoutMS` option enforcement and timeout errors — tests verify command construction but not timeout behavior
- [ ] `runCommand` MUST NOT attach `txnNumber` (all runCommand operations are non-retryable) — not explicitly verified
- [ ] User-provided `readConcern`/`writeConcern` fields in command document MUST be left as-is (§ReadConcern and
    WriteConcern)
- [ ] `runCursorCommand` MUST throw if server response lacks `cursor` field — timing of error (before return vs. on
    first iteration) not tested
- [ ] Tailable and `tailableAwait` cursors: empty `nextBatch` behavior, blocking until data (§Tailable and
    TailableAwait)
- [ ] `getMore` field settings (batchSize, maxTimeMS, comment) dynamic changes mid-cursor-iteration (§Executing getMore
    Commands)
- [ ] `killCursors` MUST be sent when closing a non-exhausted cursor with non-zero cursor ID (§Resource Cleanup)

## Ambiguities

- **Clone MUST/SHOULD ambiguity**: "Drivers MUST NOT modify the user's command; a clone SHOULD be created." MUST NOT
    modify and SHOULD clone — does SHOULD allow modifying a clone of the original? Inconsistent normative levels.
- **`timeoutMode` without `timeoutMS`**: Spec defines `ITERATION` and `CURSOR_LIFETIME` but doesn't specify default
    behavior when `timeoutMode` is set but `timeoutMS` is not.
- **`readPreference` on standalone with non-primary mode**: "$readPreference MUST be included if server is NOT
    standalone AND readPreference is NOT primary." Spec inverts the condition; it's ambiguous whether readPreference is
    validated before server selection.

## Inconsistencies

- **`readPreference` vs. `$readPreference` attachment**: The check happens post-server-selection, but if the
    readPreference affects server selection, there may be an implicit feedback loop. Tests confirm standalone behavior
    but don't clarify the order.
- **`retryability` test vs. spec claim**: Test named "does not retry retryable errors" configures a failpoint that
    closes the connection — but doesn't verify a retryable error code is NOT retried; only that one connection error is
    not retried.
- **Transactions with `readPreference` parameter**: Spec says "MUST source readPreference from transaction options," but
    `runCommand` also accepts a `readPreference` parameter. Does the transaction override the parameter or vice versa?

## Notes

- ~710 lines of tests across 2 files (`runCommand.yml` and `runCursorCommand.yml`). More substantial than most Tier 2
    specs.
- Load balancer connection pinning tests present and cover a subtle requirement.
- Tests verify command construction via `commandStartedEvent`; cannot easily test timeout, error timing, or dynamic
    option changes.
