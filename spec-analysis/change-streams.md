# Analysis: change-streams

## Missing Tests

- [ ] Drivers MUST apply timeouts to change stream establishment, iteration, and resume attempts (§Timeouts) — no
    unified test for timeout enforcement
- [ ] Drivers MUST NOT err when they encounter a new `operationType` (§Response Format) — no forward-compatibility test
    for unknown operation types
- [ ] Drivers MUST NOT err when extra fields are encountered in the `ns` document (§Response Format)
- [ ] A driver MUST only attempt to resume once from a resumable error (§Resume Process) — prose test 3 exists but
    limited automated coverage
- [ ] Drivers SHOULD attempt to kill the cursor on the server during the resume process (§Resume Process)
- [ ] `getResumeToken` MUST return `postBatchResumeToken` when batch is empty or exhausted (Prose test 11) — not
    automated
- [ ] `ChangeStream` MUST throw an exception if the server response is missing the resume token (Prose test 2) — prose
    only

## Ambiguities

- **Resumable error codes list for wire version < 9**: It's unclear whether all listed codes (including 63
    StaleShardVersion, 13388 StaleConfig) are truly resumable or contextual. "An error on an aggregate command is not a
    resumable error" is ambiguous for sharded clusters.
- **`startAfter` condition "yet to return a result document"**: "yet to return" is temporally vague — does it mean
    "never returned" or "in the process of returning"?
- **Last document in batch with `postBatchResumeToken`**: If a batch has only one document and `postBatchResumeToken` is
    present, is that document "the last document"? The spec's wording could be interpreted either way.
- **`showExpandedEvents` server version**: ">6.0.0" lacks precision; field visibility changes between 6.0 and 8.2 create
    multiple API surfaces ([DRIVERS-3278](https://jira.mongodb.org/browse/DRIVERS-3278) implementing this adjustment).

## Inconsistencies

- **§Timeouts vs. §Resumable Error**: If a timeout fires during a change stream operation, is it an error on aggregate
    or getMore? The spec says "An error on an aggregate command is not a resumable error" but doesn't clarify timeout
    interaction.
- **§Resume Process vs. Prose test 3**: Prose test 3 says "resume one time" but §Resume Process specifies conditional
    logic (startAfter with no results vs. after results). The unified tests have limited coverage of this branching.
- **change-streams-errors.yml vs. spec error code list**: Tests only cover a subset of the 17+ error codes listed in the
    spec.

## Notes

- 9 unified test files (~18 test cases). Prose tests (19 items) cover advanced resume scenarios but require manual
    implementation.
- Recent changes (2025-03-31) for server 8.2+ field visibility (`operationDescription`, `nsType`, `collectionUUID`) may
    not be fully covered by existing tests ([DRIVERS-3278](https://jira.mongodb.org/browse/DRIVERS-3278),
    [DRIVERS-3458](https://jira.mongodb.org/browse/DRIVERS-3458) implementing).
