# Analysis: transactions

## Missing Tests

- [ ] On `TransientTransactionError` during non-commit/abort operation: session MUST be unpinned before SDAM retry — no
    test for this unpinning sequence
- [ ] `commitTransaction` retry receives new `recoveryToken`: MUST track and use updated token in subsequent retries
- [ ] `startTransaction` with `readPreference='secondary'` MUST NOT be rejected — only read operations should be
    validated (spec: "MUST NOT validate during startTransaction")
- [ ] Unacknowledged write concern inherited from client/database defaults MUST be rejected in transactions
- [ ] Client error (invalid document structure) during "starting transaction" state MUST NOT change transaction state
- [ ] `commitTransaction` retry with existing `wtimeout`: `w:majority` MUST be applied but existing `wtimeout` MUST be
    preserved
- [ ] Transaction pinning/unpinning in Load Balancer mode (deferred to LB spec but no tests against LB topology)

## Ambiguities

- **NULL cascading for `readConcern`**: "If NULL, inherit from defaultTransactionOptions. If also NULL, inherit from
    MongoClient." — unclear if "NULL" means "not set" or "explicitly set to null." Different interpretations lead to
    different behavior.
- **`startTransaction` deployment detection (SHOULD)**: "SHOULD report an error if driver can detect transactions are
    not supported." SHOULD leaves inconsistent behavior across drivers.
- **Error label for driver-generated timeouts**: Spec adds `TransientTransactionError` to network errors during
    operations, but is a driver-generated timeout (not a server response) also labeled? Tests only verify
    server-generated labels.

## Inconsistencies

- **`recoveryToken` in sharded vs. replica set**: Test files don't clearly separate RS-only vs. mongos-only recovery
    token scenarios. `mongos-recovery-token.yml` is mongos-specific but this isn't enforced by test runners.
- **Automatic vs. explicit `commitTransaction` retry**: Spec says behavior is identical for both, but they are not
    tested separately to confirm.

## Notes

- 80 test files. Comprehensive coverage of state machines, error conditions, write concern, read preference, mongos
    pinning.
- `do-not-retry-read-in-transaction` test correctly prevents double-retry via retryable reads mechanism.
