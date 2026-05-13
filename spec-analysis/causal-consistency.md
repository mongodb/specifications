# Analysis: causal-consistency

## Missing Tests

- [ ] Initial state: `operationTime` MUST be unset when `ClientSession` is first created
- [ ] First read MUST NOT send `afterClusterTime` to server — verify command structure before any operation
- [ ] First read/write SHOULD update `operationTime` even on error — test both success and error paths
- [ ] `findOne` followed by any read MUST include `operationTime` in `afterClusterTime` — test propagation across
    multiple reads
- [ ] Write followed by `findOne` MUST include `operationTime` in `afterClusterTime`, including error cases — test
    write→read causal chain ([PR #1930](https://github.com/mongodb/specifications/pull/1930),
    [DRIVERS-3274](https://jira.mongodb.org/browse/DRIVERS-3274))
- [ ] Read in a non-causally-consistent session MUST NOT include `afterClusterTime` — test explicit
    `causalConsistency=false`
- [ ] Causally consistent read against a pre-3.6 server MUST NOT send `afterClusterTime` — test backwards compatibility
- [ ] With default server ReadConcern, `readConcern` MUST NOT include a `level` field
- [ ] With custom ReadConcern, `readConcern` MUST merge ReadConcern value and `afterClusterTime`
- [ ] Messages to pre-cluster-time servers MUST NOT include `$clusterTime`
- [ ] `advanceOperationTime` MUST advance only if new value is greater
- [ ] `advanceOperationTime` MUST NOT validate the `operationTime` value

## Ambiguities

- **`causalConsistency` default inheritance**: "Currently inherited from the global default which is defined to be true.
    In the future it *might* be inherited from client settings." — Vague. Should explicitly state what "global default"
    means and freeze the current behavior.
- **Unacknowledged writes + causal consistency**: Spec accepts the limitation but states "Drivers MUST document that
    causally consistent reads are not causally consistent with unacknowledged writes." The trade-off is not well
    justified for users.
- **Reference to ReadConcern spec for supported commands list**: Creates maintenance coupling. Should include an inline
    list or a stable link.

## Inconsistencies

- **Unacknowledged writes and `operationTime`**: Spec says "do not wait for a response" for unacknowledged writes but
    also says drivers "MUST save the `operationTime` in the `ClientSession` whether the operation succeeded or not."
    Saving `operationTime` requires a response, which contradicts the "no response" statement.
- **Default for implicit sessions**: "For implicit sessions, the value of this property MUST be set to false" conflicts
    with "If no value is supplied for `causalConsistency` the value will be inherited."

## Notes

- Tests exist only as prose in the "Test Plan" section — no structured YAML fixtures. Requires manual per-driver
    implementation.
- Spec references Sessions Specification (required reading) and ReadConcern spec for the list of commands that support
    causal consistency.
- [DRIVERS-1083](https://jira.mongodb.org/browse/DRIVERS-1083) /
    [DRIVERS-2097](https://jira.mongodb.org/browse/DRIVERS-2097) (Backlog): prose tests 6 and 7 always succeed as
    written — known issue predating this analysis.
- [DRIVERS-1374](https://jira.mongodb.org/browse/DRIVERS-1374) (Implementing): remove outdated prose test.
