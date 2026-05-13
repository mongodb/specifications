# Analysis: server-discovery-and-monitoring

## Missing Tests

- [ ] `topologyVersion` comparison when `processId` is explicitly null (vs. absent) — spec: "assume response is more
    recent if either topologyVersion is unset"
- [ ] `ServerDescription.isCryptd` field: `mongocryptd` server detection and exclusion from normal topology
- [ ] `maxElectionId`/`maxSetVersion` comparison for MongoDB < 6.0 (setVersion-first comparison) — version-dependent
    comparison logic not integration-tested ([DRIVERS-2412](https://jira.mongodb.org/browse/DRIVERS-2412) implementing:
    "SDAM should prioritize electionId over setVersion only on >=6.0 servers")
- [ ] RSGhost server incorrectly reporting a non-null `hosts` list — spec: "client MUST NOT attempt to use its hosts
    list"
- [ ] Load-balanced topology error handling: `serviceId`-based pool clearing in all error paths
- [ ] Wire protocol compatibility error message format: driver name and version substitution in error string
- [ ] Hostname with Unicode/IDNA characters — only ASCII hostnames tested; spec requires normalization to lowercase

## Ambiguities

- **`replacement MUST happen even if new ServerDescription compares equal`**: Does this apply to LoadBalanced topology
    where comparison semantics differ?
- **"SHOULD emit a warning if constructed with no seeds"**: Warning format/delivery mechanism not specified.
- **MongoDB 4.0 pool clearing**: Spec says clear pool for stale primary on v4.0 or earlier — 4.0 is EOL; should drivers
    still support this path?
- **`compareTopologyVersion` uses `>=` instead of `>`**: Rationale for `>=` (equal versions considered stale) is
    counterintuitive and not explained.

## Inconsistencies

- **Error handling pseudocode vs. TopologyType table**: "not writable primary" error handling differs between the
    pseudo-code and the table — table shows `checkIfHasPrimary` action, pseudocode has conditional logic.
- **Network error boundary**: Handling differs for errors "before handshake completes" vs. "after handshake completes,"
    but the exact boundary is undefined in practice.
- **v4.0/v4.2 pool clearing boundary**: "Mark old primary Unknown and clear its pool for v4.0 or earlier" but v4.2+
    should NOT clear pool — the 4.0/4.2 boundary behavior described in two contradictory-sounding places.

## Notes

- ~450 test files covering all topologies. Error handling scenarios are moderately covered but edge cases around stale
    topologies and concurrent monitor updates lack depth.
- `topologyVersion` handling is tested but processId equality edge cases need coverage.
- Single-threaded monitoring scanning order is under-tested relative to multi-threaded cases.
- [DRIVERS-3275](https://jira.mongodb.org/browse/DRIVERS-3275) (Backlog): centralize SDAM tests.
- [DRIVERS-1670](https://jira.mongodb.org/browse/DRIVERS-1670) (Implementing): add log messages to SDAM spec.
