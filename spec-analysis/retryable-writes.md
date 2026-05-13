# Analysis: retryable-writes

## Missing Tests

- [ ] Error code 20 with errmsg starting with "Transaction numbers" MUST produce an actionable error message — prose
    test only, no YAML
- [ ] `PoolClearedError` during connection checkout MUST get `RetryableWriteError` label — prose test 2 only, no unified
    test
- [ ] `WriteConcernError` with `RetryableWriteError` label + `NoWritesPerformed` on retry: MUST return original error —
    prose test 3 only
- [ ] Sharded cluster: retry MUST target a different mongos (deprioritization) — prose tests 4 & 5 only; not expressible
    in YAML
- [ ] Write commands inside transactions MUST NOT be retried and MUST NOT get `RetryableWriteError` labels
- [ ] Network error during initial connection handshake MUST get `RetryableWriteError` label — `handshakeError.yml`
    exists but completeness unclear
- [ ] CSOT-enabled retries: multiple attempts MUST be allowed (vs. single attempt without CSOT) — no CSOT-specific retry
    count tests

## Ambiguities

- **Server selection deprioritization**: "Failed server MUST be passed as deprioritized" — does this exclude it, rank it
    lower, or merely mark it? Prose test 4 acknowledges this cannot be reliably tested without external tools.
- **`bulkWrite` eligibility granularity**: Eligibility evaluated "after order and batch splitting individually" — if
    `UpdateMany` and `InsertOne` are in different batches, is each batch evaluated independently?
- **mongod vs. mongos error detection**: `writeConcernError` codes are only valid on mongod responses — how do drivers
    distinguish in a sharded cluster where mongos forwards shard errors?

## Inconsistencies

- **`updateMany.yml` and `deleteMany.yml`**: Both say "ignores retryWrites" and verify no `txnNumber`. The spec language
    ("MUST NOT add a transaction ID") is a firm enforcement requirement, not a behavioral choice — naming is misleading.
- **`PoolClearedError` label requirement vs. test coverage**: Spec says MUST add `RetryableWriteError` to pool errors,
    but this is driver-level (from CMAP), not server-level — the distinction in when to apply the label is not
    consistently tested.
- **`operationId` guidance**: Commands in a retry SHOULD share `operationId` but drivers SHOULD NOT use `operationId` to
    relay transaction ID info — somewhat contradictory for multi-command bulk writes.

## Notes

- 35 unified test files with good coverage of single/multi-statement operations, error labels, and server errors.
- 5 prose tests (PoolClearedError, WriteConcernError, sharded cluster deprioritization) — ~12% of critical coverage is
    manual.
- CSOT behavioral change (2022-10-18: "multiple retries allowed when CSOT enabled") has no corresponding test coverage.
