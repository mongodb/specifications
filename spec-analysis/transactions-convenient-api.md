# Analysis: transactions-convenient-api

## Missing Tests

- [ ] Default 120-second timeout enforcement when `timeoutMS` is unset — no unified test (prose test mentions this with
    mocking caveats)
- [ ] Exponential backoff jitter formula: `jitter * min(BACKOFF_INITIAL * (1.5**retry), BACKOFF_MAX)` — no unified YAML
    test (requires precise timing or mocked RNG)
- [ ] Callback return value MUST be propagated as return value of `withTransaction` (Prose test "Callback Returns a
    Value")
- [ ] Custom (non-labelled) callback errors MUST NOT be retried — prose test only
- [ ] `UnknownTransactionCommitResult` label on callback error: callback manually committed, MUST propagate error
    immediately
- [ ] `commitTransaction` retry: majority write concern MUST be applied — no unified test asserts this in command
    expectations
- [ ] `commitTransaction` with `TransientTransactionError` during retry MUST restart the entire transaction (step back
    to step 2)
- [ ] `commitTransaction` with `UnknownTransactionCommitResult` AND `MaxTimeMSExpired` MUST NOT retry
- [ ] Errors inside callback that silently abort the transaction can cause `NoSuchTransaction`
    (TransientTransactionError) infinite loop — no test

## Ambiguities

- **"Starting transaction" / "transaction in progress" state names**: Spec references
    `../transactions/transactions.md#clientsession-changes` but doesn't quote exact state names used. Unclear if they're
    "STARTING", "IN_PROGRESS", etc.
- **Callback with new transaction**: Spec says "will not detect whether callback has started a new transaction" (line
    324\) but step 7 returns early if session is in "no transaction", "aborted", or "committed" state. What state would a
    new transaction leave the session in?
- **Backoff pseudo-code order**: Pseudo-code calculates backoff before checking elapsed time, but the numbered steps
    describe the check first. Order of operations could differ between implementations.
    ([DRIVERS-3391](https://jira.mongodb.org/browse/DRIVERS-3391) /
    [DRIVERS-3436](https://jira.mongodb.org/browse/DRIVERS-3436) implementing: timeout error wrapping and backoff
    semantics)

## Inconsistencies

- **Majority write concern on retry**: Design Rationale says majority WC is applied on commit retry, but pseudo-code
    just calls `this.commitTransaction()` with a comment trusting the transactions spec. Responsibility boundary is
    unclear.
- **Timeout check in pseudo-code vs. numbered steps**: Pseudo-code uses `Date.now() + backoff - startTime >= timeout`;
    numbered steps say "elapsed time < TIMEOUT_MS." For first check these are equivalent but for subsequent checks the
    implementations may diverge.
- **Transaction state after callback (step 7 vs. step 8)**: Step 7 handles "no transaction/aborted/committed" states;
    step 8 assumes transaction is still in progress. No error handling if state is somehow invalid but doesn't match
    step 7 conditions.

## Notes

- ~41 unified tests + prose tests. Main paths are well-covered (callback succeeds, TransientTransactionError retry,
    commit retry).
- Several critical behaviors are explicitly "not easily expressed in YAML" (Retry Backoff, Retry Timeout, Callback
    Returns Value) — moved to prose and left to driver-specific implementation.
- Server version gating: 4.0 for replica sets, 4.1.8 for sharded/LB. The 4.2-specific test covers a server-side behavior
    change not explained in the spec.
