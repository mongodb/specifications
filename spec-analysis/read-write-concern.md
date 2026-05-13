# Analysis: read-write-concern

## Missing Tests

- [ ] Commands supporting ReadConcern MUST raise an error when `maxWireVersion < 4` and a non-default, non-local read
    concern is specified (§Errors)
- [ ] `readConcern` with `atClusterTime` in snapshot operations (§Snapshot Read Concern) — no test verifies
    `atClusterTime` sent or returned
- [ ] `aggregate` with write stage on 4.2+: linearizable MUST be rejected; other levels MUST work (§Read Concern)
- [ ] `WriteConcern` consistency: `w=0` AND `journal=true` MUST raise an error — only one document test, no connection
    string test
- [ ] `fsync` field SHOULD be treated identically to `journal` for consistency validation (§FSync) — no test for fsync
- [ ] ReadConcern and WriteConcern inheritance: Client → Database → Collection (§Location Specification) — no operation
    test for inheritance chain
- [ ] `RunCommand` MUST NOT automatically apply ReadConcern or WriteConcern (§Generic Command Method)
- [ ] `WriteConcernError` parsing from server replies (§Errors) — no test for writeConcernError extraction from
    `findAndModify` or `aggregate`
- [ ] `findAndModify` with WriteConcern MUST omit `writeConcern` when `maxWireVersion < 4` (§Find And Modify)

## Ambiguities

- **`getLastErrorDefaults` reference (§Server's Default WriteConcern)**: This MongoDB feature was removed (Changelog
    2024-10-30). The section referencing it is now outdated and confusing.
- **`mapReduce` with write stage and ReadConcern**: Spec lists mapReduce as supporting writes, but it's unclear whether
    ReadConcern is disallowed on mapReduce with a write stage (similar to aggregate).
- **"On the Wire" inheritance rule**: "If Client/Database/Collection has non-default RC, MUST include command's RC even
    if command specifies server default." This nuance is not clearly tested across all commands.

## Inconsistencies

- **No ReadConcern operation tests**: All 4 operation test files (`default-write-concern-*.yml`) focus exclusively on
    WriteConcern. No unified tests verify ReadConcern is sent/omitted correctly in read operations.
- **Snapshot level undertested**: Added in 2021 but only basic validity is checked in document tests. No tests verify
    `atClusterTime` behavior or server response handling.
- **`w=-2` rejected but very large `w` not tested**: Tests verify `w=-2` is invalid, but no test covers values that
    could overflow in some languages.

## Notes

- ~75 tests total across connection-string, document, and operation test directories.
- Operation tests are split by server version (2.6, 3.2, 3.4, 4.2) — well-structured but makes it unclear which tests
    apply to modern servers.
