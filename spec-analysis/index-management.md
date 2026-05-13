# Analysis: index-management

## Missing Tests

- [ ] `dropIndex("*")` MUST raise an error — no unified test (prose only)
- [ ] `createIndex` with `commitQuorum` on pre-4.4 server MUST raise an error — no unified test (only rawData tested for
    version-gating)
- [ ] Index name generation (`key_direction_pairs` format, `_id_` special case) — no test verifying generated names
    match spec
- [ ] `ns` field population for index models when server doesn't provide it (MongoDB 4.4+) — not tested
- [ ] `comment` option MUST be passed to subsequent `getMore` calls in `listIndexes` — propagation not tested
- [ ] `rawData` option MUST NOT be sent to pre-8.2 servers — tested as omitted, but not that an explicit user request
    errors
- [ ] Timeout enforcement for `createIndex`, `dropIndex`, `listIndexes` per CSOT spec — no tests

## Ambiguities

- **`rawData` option discouragement**: Spec says drivers "SHOULD NOT implement this option unless asked" and "SHOULD
    implement in a way that discourages customer use." Unclear whether this means deprecation warnings,
    documentation-only, or hiding from public API.
- **Search index polling responsibility**: Spec says commands are "asynchronous and return before the index is updated."
    Should drivers automatically poll or document that polling is user responsibility? Not specified.
- **`NamespaceNotFound` suppression scope**: "Drivers MAY suppress NamespaceNotFound from search index helpers" but
    "MUST suppress for `dropSearchIndex`." Which other helpers does MAY apply to?

## Inconsistencies

- **`commitQuorum` validation gap**: Q&A says drivers "manually verify it is only sent to 4.4+ servers" and spec says
    "MUST manually raise an error," but no unified test covers this. The `index-rawdata.yml` tests only cover rawData
    version-gating, not commitQuorum.
- **Search index read/write concern stripping**: Tests assert `readConcern`/`writeConcern` do not exist
    (`$$exists: false`), but spec says "MUST NOT apply" (not "MUST strip"). Ambiguous whether user-supplied fields in
    the command are also stripped.
- **Index View API not tested**: Spec defines both Standard API (createIndex, dropIndex) and Index View API (createOne,
    createMany, dropOne, dropAll), but all unified tests only cover Standard API.

## Notes

- Search index tests are Atlas-only (require server 7.0+ and real Atlas cluster) — cannot run in standard driver CI.
- `rawData` option added in Sept 2025; minimal test coverage (2 tests, command construction only).
- Prose tests and unified tests form a two-tier strategy; search index prose tests (Cases 1–8 with polling) are not
    automated.
