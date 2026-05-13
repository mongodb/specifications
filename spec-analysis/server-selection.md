# Analysis: server-selection

## Missing Tests

- [ ] Hedged reads deprecated in MongoDB 8.0: deprecation warning or behavior — no test for the `hedge` field or its
    deprecation
- [ ] `socketCheckIntervalMS`: idle connection check after interval expiry — pseudocode is defined but not tested
- [ ] `ServerSelectionTryOnce` option: single-threaded drivers MUST support it; multi-threaded MUST NOT — no test for
    the option or its rejection
- [ ] Load-balanced topology server selection — deferred to LB spec but server-selection tests don't include LB topology
    at all
- [ ] Tag set with empty document (`{}`) — "a document of zero or more tags" but empty document edge case not tested

## Ambiguities

- **"Eligible" definition order**: Does `maxStalenessSeconds` filtering happen before or after `tag_sets` filtering?
    Terminology section is ambiguous; algorithm section clarifies but they should align.
- **EWMA statistical claim**: "A weighting factor of 0.2 puts ~85% weight on the 9 most recent observations" — this
    claim is not derivable from the formula alone and is not tested.
- **Latency window selection among equal servers**: Spec says shortest RTT server is "always a possible choice" but
    doesn't specify selection method among servers within the window. Multi-threaded tests use frequency-based
    selection; single-threaded behavior is unspecified.

## Inconsistencies

- **RTT calculation → latency window**: 14 RTT files and 30+ latency window files tested separately, but no end-to-end
    test verifying RTT calculation correctly feeds into latency window filtering.
- **Load-balanced topology**: Mentioned in spec (line 815) but deferred; server-selection tests don't cover it — drivers
    must rely only on load-balancers spec tests.

## Notes

- 147 test files. Extensive RTT and latency window coverage. `in_window` tests include operation count tracking for
    multi-threaded fairness.
- Hedged reads noted as deprecated (8.0+) but no migration/deprecation path is tested.
