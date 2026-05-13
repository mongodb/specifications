# Analysis: find_getmore_killcursors_commands

## Missing Tests

- [ ] `find` command is used instead of `OP_QUERY` when `maxWireVersion >= 4`
- [ ] Response includes `cursor.id`, `cursor.ns`, and `cursor.firstBatch`
- [ ] System collection queries use replacement commands (`currentOp`, `fsyncUnlock`, `listIndexes`, `listCollections`)
- [ ] Exhaust cursor: correct behavior for server 4.0 and earlier (OP_QUERY), 4.2–5.0 (OP_MSG preferred), 5.1+ (OP_MSG
    only)
- [ ] `secondaryOk` is set only on `find`, not on `getMore` or `killCursors`
- [ ] Negative `limit`/`batchSize` values are transformed to `singleBatch=true` and their positive equivalents
- [ ] On server 5.0+, cursor is closed when `limit` is reached and cursor ID > 0 is returned, requiring a `killCursors`
    call
- [ ] `batchSize=1` returns a single document per batch without closing the cursor
- [ ] Tailable cursor: `awaitData`, `maxTimeMS`, and `maxAwaitTimeMS` handling
- [ ] `getMore` response: driver updates cursor ID, namespace, and stores `nextBatch`
- [ ] `killCursors` returns `cursorsKilled`, `cursorsNotFound`, `cursorsAlive` arrays
- [ ] Error handling: `ok: 0` with `errmsg` and `code` fields

## Ambiguities

- **`limit < 0` / `batchSize < 0` transformation**: Spec says to transform before adding to the `find` command but does
    not clarify at what point invalid combinations (e.g., `limit=0` and `batchSize=-1`) should be rejected vs.
    transformed.
- **`maxAwaitTimeMS` option requirement**: "Drivers MUST provide a Cursor level option named `maxAwaitTimeMS`" — does
    "MUST provide" mean: accept the option, expose it in the API, or enforce a default value?
- **Last step: `getMore` vs `killCursors` on limit exhaustion**: Spec shows both as possible final steps but provides no
    algorithm for deciding which to issue.
- **`secondaryOk` on `getMore`/`killCursors` (SHOULD NOT)**: If the server remembers the value from `find`, why is
    SHOULD NOT a requirement rather than a performance optimization?

## Inconsistencies

- **Changelog 2015-09-30 vs current spec**: Old entry says "Legacy `secondaryOk` flag MUST be set to true on `getMore`
    and `killCursors`" but current spec says "SHOULD NOT." The contradiction is not resolved in the spec text.
- **Exhaust cursor 3.6 version gap**: Changelog says "Exhaust cursors must use OP_MSG on 3.6+ servers" (2021-08-27) but
    current table says "4.0 and earlier MUST use OP_QUERY." Server 3.6 falls between these two rules — which applies?
- **Duplicate `maxTimeMS` rules**: One rule for non-tailable cursors and one for tailable with `awaitData` use nearly
    identical wording, creating confusion about which applies in which context.

## Notes

- RST redirect at `source/find_getmore_killcursors_commands.rst` — can be cleaned up.
- Status: Accepted, Version 3.2. Stable spec.
- Extensive changelog from 2015–2024.
- FAQ section (lines 430–455) provides useful clarifications.
