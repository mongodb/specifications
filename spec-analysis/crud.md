# Analysis: crud

## Missing Tests

- [ ] `countDocuments` with `skip` > collection size — behavior with oversized skip not tested
- [ ] `distinct` on a field that doesn't exist in any document — should return empty array
- [ ] `aggregate` with `$out`/`$merge` + `bypassDocumentValidation` interaction
- [ ] Bulk write splitting at exactly 2 MiB boundary — spec defines size limits but exact boundary behavior is not
    tested
- [ ] CSOT interaction with tailable cursor `await` timeouts
- [ ] `estimatedDocumentCount` with `comment` on servers < 4.4 — behavior when server doesn't support the option
- [ ] `rawData` option for non-time-series collections — error handling when sent to pre-8.2 servers or wrong collection
    type

## Ambiguities

- **`bypassDocumentValidation` without `$out`/`$merge`**: Spec says "only applies when `$out` or `$merge` stage is
    specified" — should an explicit `bypassDocumentValidation=true` on a pipeline without these stages error or be
    silently ignored?
- **`comment` + `hint` interaction**: Spec mentions comment can be any BSON type (4.4+) but doesn't specify if comment
    affects query planning alongside hint.
- **`rawData` documentation scope**: Marked "internal use by MongoDB teams" but criteria for when to include it in
    public vs. internal documentation is vague.

## Inconsistencies

- **`countDocuments` vs. `estimatedDocumentCount` options**: `countDocuments` has `skip`/`limit`/`hint`;
    `estimatedDocumentCount` explicitly does not — rationale not explained in spec.
- **`batchSize` change between operations**: "SHOULD apply to both original aggregate command and subsequent getMore" —
    doesn't clarify if batch size can change between operations mid-cursor.
- **`comment` field server version requirements**: Different operations have different version thresholds for comment
    support; version matrix is scattered across sections rather than centralized.

## Notes

- ~378 test files. Strong happy-path coverage across all CRUD operations. Collation, hint, and comment interactions in
    complex queries lack depth.
- Server version compatibility for newer options (rawData, comment as BSON type) not comprehensively covered.
- Edge cases around cursor timeouts and bulk write splitting are under-tested.
