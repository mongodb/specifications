# Analysis: unified-test-format

## Missing Tests

- [ ] Entity map concurrent access under contention — spec requires thread-safe access but only basic thread operations
    are tested; race conditions around creation/retrieval not tested
- [ ] `saveResultAsEntity` error when saving a non-BSON driver-level object (e.g., `Cursor`) to entity map in
    BSON-restricted mode
- [ ] `$$placeholder` substitution failure: missing environment variable or config — behavior not specified
- [ ] `runOnRequirements` with conflicting conditions (e.g., `minServerVersion: 5.0` AND `maxServerVersion: 4.4`) —
    error handling
- [ ] `schemaVersion` with unsupported patch version (e.g., `1.0.1` when runner supports only `1.0.0`) — should error or
    pass?
- [ ] `expectError` with multiple optional fields where some match and some don't (e.g., `errorCode` matches but
    `errorCodeName` doesn't)
- [ ] `cursor.next()` / `cursor.toArray()` called on an already-exhausted cursor
- [ ] `topologyDescription` entity snapshot timing: does it capture state before or after the operation?

## Ambiguities

- **Entity uniqueness enforcement error types**: "Uniqueness enforcement" and "referential integrity" required but
    exception types and messages not specified — inconsistent across drivers.
- **`createChangeStream` vs. `watch()`**: "SHOULD NOT use `watch()`" — what implementation variations exist? Why is
    `watch()` discouraged?
- **`serverParameters` cache scope**: "Result SHOULD be cached" — per test, per test file, or per runner session? TTL
    not specified.
- **`expectError` mutual exclusivity**: Spec lists it as mutually exclusive with `expectResult` and `saveResultAsEntity`
    but doesn't clarify which takes precedence if multiple are specified.

## Inconsistencies

- **`comment` field in event matching**: Optional in command monitoring events but spec doesn't explain
    filtering/matching logic when `comment` is a complex BSON type vs. string.
- **`ignoreExtraEvents: true` semantics**: "Events after all specified have matched MUST NOT cause a test failure" —
    does event ordering still matter for the matched events when extra events are interspersed?
- **Timeout handling delegation**: Timeout semantics for explicit operations vs. cursor iteration differ; spec delegates
    to CSOT spec but unified format doesn't consistently specify which applies in which context.

## Notes

- ~638 test files. Comprehensive coverage of happy-path test execution, entity creation, and event assertion.
- Error cases and edge cases in entity map management (concurrency, invalid types) are minimal.
- `serverParameters` caching scope is under-specified — different drivers may cache at different granularities.
- No `## Changelog` section — spec has a changelog but it's embedded inline.
