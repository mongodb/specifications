# Analysis: client-side-encryption

## Missing Tests

- [ ] `TextOpts` all 4 combinations of `caseSensitive`/`diacriticSensitive` (true/true, true/false, false/true,
    false/false) across substring/prefix/suffix query types
    ([PR #1931](https://github.com/mongodb/specifications/pull/1931) /
    [DRIVERS-3470](https://jira.mongodb.org/browse/DRIVERS-3470) in review: case and diacritic text explicit encryption
    tests)
- [ ] `encryptExpression` with mismatched bound types (e.g., double min/max with int64 value) — error handling
- [ ] `RangeOpts` precision: MUST error when `precision` is omitted for `double`/`decimal128` but min/max are set (or
    vice versa)
- [ ] `rewrapManyDataKey` with keys encrypted by different KMS providers in a single call
- [ ] `deleteKey` behavior when encrypted fields reference the deleted key
- [ ] Internal `MongoClient` creation with `maxPoolSize=0` + `bypassAutoEncryption=false` combination
- [ ] Key vault with malformed key documents (missing required fields like `keyMaterial`) in `getKey`/`getKeys`

## Ambiguities

- **`masterKey` unknown fields**: "MUST have fields corresponding to the given `provider`" — should unknown fields in
    `masterKey` be rejected or silently ignored?
- **"Best-effort secure storage"**: "Drivers SHOULD take a best-effort approach to store sensitive data securely when
    interacting with KMS" — undefined; no test verifies memory handling.
- **`encryptExpression` nesting**: Spec shows only flat structure; unclear if nested `$and`/`$or` inside the outer
    `$and` is supported.
- **`createEncryptedCollection` return value**: "Return the resulting collection and the generated EF'" — unclear if the
    collection reference is immediately usable or requires client auto-encryption configuration first.

## Inconsistencies

- **`schemaMap` and `encryptedFieldsMap` coexistence**: Spec says `schemaMap` "only applies to client-side encryption"
    but no test verifies it is truly ignored when `encryptedFieldsMap` is also present (QE context).
- **Key management function test coverage**: `createDataKey` is extensively tested; `addKeyAltName`, `removeKeyAltName`,
    `deleteKey` have minimal coverage relative to their spec complexity.

## Notes

- ~440 test files. Heavy focus on encryption/decryption correctness and Range/Text query types for Queryable Encryption.
- Legacy test folder indicates FLE1→FLE2 migration was a major focus; cross-version compatibility is not well-tested.
- No `## Changelog` section missing — spec has a changelog but it's not a separate section.
- [PR #1925](https://github.com/mongodb/specifications/pull/1925) /
    [DRIVERS-3321](https://jira.mongodb.org/browse/DRIVERS-3321) (in review): Support Substring/Suffix/Prefix indexes as
    GA.
