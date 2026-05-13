# Analysis: initial-dns-seedlist-discovery

## Missing Tests

- [ ] Custom `srvServiceName`: TXT records queried and parsed correctly with custom prefix — test22 checks a custom name
    but not TXT record interaction
- [ ] `srvMaxHosts` randomization: Fisher-Yates shuffle is actually random — tests verify count only, not distribution
    or method
- [ ] TXT record multi-string concatenation order: reversed order produces wrong result — test11 uses this but doesn't
    verify order-dependent parsing
- [ ] `tls=false` in connection string OVERRIDES implicit TLS from `mongodb+srv` — test7 only verifies TXT `ssl=false`
    is rejected, not that URI `tls=false` succeeds
- [ ] All valid/invalid subdomain combinations for SRVs with fewer than 3 dot-separated parts (clarified 2024-09-24) —
    prose tests only, no unified YAML ([PR #1787](https://github.com/mongodb/specifications/pull/1787) /
    [DRIVERS-3162](https://jira.mongodb.org/browse/DRIVERS-3162) open)

## Ambiguities

- **Domain matching for short hostnames**: "SRV records with fewer than three `.` separated parts, the returned hostname
    MUST have at least one more domain level" — does "one more domain level" mean one additional subdomain component or
    one additional dot-separated part? ([DRIVERS-2922](https://jira.mongodb.org/browse/DRIVERS-2922) implementing:
    "Allow valid SRV hostnames with less than 3 parts"; [PR #1854](https://github.com/mongodb/specifications/pull/1854)
    clarifying driver verification requirements)
- **Multiple TXT records**: "MUST NOT allow multiple TXT records and MUST raise an error" — does "multiple" mean
    multiple DNS records in one response, or multiple separate queries?
- **Fisher-Yates for `srvMaxHosts`**: Uses SHOULD, not MUST — drivers can use other randomization methods. Tests only
    verify count, so inconsistency is possible.

## Inconsistencies

- **test12 domain mismatch**: Tests validation failure but the exact rule violated is not clearly documented in the test
    file.
- **TXT record error handling**: test8 (`authSource` without value) and test10 (`socketTimeoutMS=500`, not an allowed
    TXT option) test different error conditions inconsistently.
- **`srvMaxHosts` + `replicaSet` conflict**: Test for `srvMaxHosts` + `loadBalanced=true` conflict exists but no
    parallel test for `srvMaxHosts` + `replicaSet` conflict (both are in the spec).

## Notes

- 107 test files. Strong coverage for replica set, sharded, and load-balanced topologies, plus error cases (invalid
    URIs, DNS failures, wrong domains).
- Recent changelog (2024-09-24) clarified domain matching rules; some tests may predate this clarification.
