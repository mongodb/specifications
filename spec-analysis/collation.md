# Analysis: collation

## Missing Tests

- [ ] `maxWireVersion < 5`: ALL operations with collation MUST raise an error — verify error is raised before sending
- [ ] Opcode-based unacknowledged writes with collation MUST raise an error
- [ ] `create` command MUST accept collation parameter — test collection creation with collation
- [ ] `BulkWrite` MUST fail the entire batch (not just the offending operation) if any operation has collation and
    `maxWireVersion < 5`
- [ ] Unknown collation options MUST NOT raise an error; server validates — test forward compatibility
- [ ] `RunCommand` MUST NOT validate collation subdocument or check wire version — test passthrough behavior
- [ ] All CRUD ops MUST support collation option: `aggregate`, `count`, `distinct`, `find`, `findAndModify`, `geoNear`,
    `group`, `mapReduce`, `delete`, `update` — one test per operation
- [ ] Index management ops MUST support collation option: `createIndex`, `dropIndex`, `hint`
- [ ] Two indexes with identical keys but different collations can be created when given custom names
- [ ] Correct index is dropped when specifying index name on `deleteOne`

## Ambiguities

- **Error type for unsupported servers**: Spec states "Drivers MUST throw an error" for `maxWireVersion < 5` but does
    not specify the error type, message format, or whether the error is raised pre-flight or at the wire protocol level.
- **`BulkWrite` rejection timing**: "Fail the entire `bulkWrite` if a collation was explicitly specified" — unclear
    whether the entire batch is rejected before any network call or only after the first operation fails.
- **Test plan vagueness**: "Drivers should test each affected CRUD, Index Management API, and collection
    creation/modification component" — no structured test format is provided.

## Inconsistencies

- **Header "Minimum Server Version: 1.8" vs `maxWireVersion` 5 requirement**: Spec states support for "server versions
    \>= 3.4 (`maxWireVersion` 5)" but the header says the minimum is 1.8. These conflict.
- **Strict Collation model vs unknown options**: Spec defines a strict typed `Collation` class but also says "MUST NOT
    raise an error when a user provides unknown options." This creates tension between strict typing and server-side
    validation.

## Notes

- Only prose test cases (lines 185–195); no JSON/YAML fixtures.
- Q&A clarifies inserts do not take a collation option (collation affects matching, not storage).
- Broken Jira links (`[RUBY-1126]`, `[JAVA-2241]`) with no status indicator.
