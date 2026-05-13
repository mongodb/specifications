# Analysis: retryable-reads

## Missing Tests

- [ ] CSOT enabled: read MUST be retried multiple times within timeout window (not just once) — spec section "Executing
    Retryable Read Commands" 3c, no unified test ([DRIVERS-3247](https://jira.mongodb.org/browse/DRIVERS-3247) ready for
    work)
- [ ] Wire version dip between initial attempt and retry: driver chooses to recreate command or not retry — no test for
    this transient topology change
- [ ] Sharded cluster: retry MUST target a different mongos (deprioritization) — prose tests 2.1/2.2 acknowledge this
    cannot be reliably tested in YAML
- [ ] Generic read command runner: retryability SHOULD be supported — only MapReduce as unsupported is tested
- [ ] Error server information MUST reflect the originating server, not a previous server from a retry chain (added
    2023-12-05)

## Ambiguities

- **"Equivalent command" definition**: "MAY send a valid command equivalent to the initial command" — "equivalent" is
    footnoted but not clearly defined for complex operations (aggregate with $facet, find with collation).
- **Prose test 1 event count**: "Exactly three `find` CommandStartedEvents were observed" — drivers emitting additional
    ping/isMaster commands would fail this assertion without violating the spec.
- **Server deprioritization**: Tests "cannot reliably distinguish retry on a different mongos from normal SDAM
    behavior." No deterministic test.

## Inconsistencies

- **`mapReduce.yml` test naming**: Test is named "MapReduce succeeds with retry on" — the failure is from the failpoint,
    not from MapReduce being non-retryable. The test doesn't actually verify the non-retry rule is enforced.
- **Wire version dip handling**: Spec prescribes two alternative paths but no test enforces either. A driver could
    choose either approach and pass all tests.

## Notes

- 45 tests. Strong coverage for happy path (find, aggregate, distinct, count). Handshake error tests are auto-generated
    from templates.
- Prose tests correctly identify gaps (deprioritization, PoolCleared under concurrent load).
- No tests for retryable reads combined with causal consistency (`afterClusterTime` in read concern).
