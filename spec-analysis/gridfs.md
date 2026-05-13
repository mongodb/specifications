# Analysis: gridfs

## Missing Tests

- [ ] Index creation is idempotent: MUST check whether indexes already exist before creating them
- [ ] Numeric index values MUST be compared by value across types (1 vs 1.0) — type normalization not tested
- [ ] Indexes MUST be created in foreground mode — mode not verified
- [ ] Zero-length file upload MUST NOT create any chunks — verify no chunks document inserted
- [ ] Drivers MUST NOT run the `filemd5` command — negative test
- [ ] Orphaned chunks from a failed upload MUST NOT be cleaned up by the driver
- [ ] Each chunk received during download MUST be validated as the next expected chunk (sequence check)
- [ ] Extra chunks behavior: drivers MAY ignore them — not tested (neither error nor silent ignore)

## Ambiguities

- **Bucket name with dots**: If a user specifies bucket name `fs.backup`, are collections `fs.backup.files` or
    `fs.backup.files.files`? Tests only use simple names.
- **`chunkSize` as non-integer type**: A `chunkSize` stored as double with fractional part (e.g., 262144.5) — what
    happens during chunk processing? Spec requires numeric comparison but doesn't address fractional chunk sizes.
- **`uploadDate` boundary**: "MUST be the datetime when the upload completed, not when it was begun." For streaming
    uploads, is "completed" when `close()` is called or when the server acknowledges the files collection insert?
- **Zero-length file download**: Spec says MUST NOT query chunks collection — but what is returned? Empty stream?
    Exception? Spec is silent.
- **`start == end` in partial retrieval**: `start > end` is an error, but `start == end` returns no data. Tests don't
    clarify this boundary.

## Inconsistencies

- **`metadata: null` vs. omit `metadata`**: Spec says "If not provided the driver MUST omit the metadata field."
    `options=null` creates ambiguity: omit the field or set to null document?
- **Index creation ordering assumption**: Spec says check if `files` collection is empty with `findOne` before creating
    indexes. But `findOne` on a non-existent collection implicitly creates it. Was the write "before the first write"?
    The ordering assumption is unclear.

## Notes

- 8 unified test files covering upload, download, delete, rename, and disableMD5 variants.
- MD5 is deprecated; `disableMD5` option tested separately.
- Tests don't distinguish Basic API (MUST support) from Advanced API (MAY support).
- [DRIVERS-2062](https://jira.mongodb.org/browse/DRIVERS-2062) (Backlog): modify GridFS spec to support sessions,
    transactions and causal consistency.
- [DRIVERS-3442](https://jira.mongodb.org/browse/DRIVERS-3442) (Blocked): increase `timeoutMS` values in CSOT GridFS
    tests.
