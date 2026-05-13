# Analysis: compression

## Missing Tests

- [ ] Unknown compressor in connection string MUST yield a warning — no test verifies the warning mechanism itself (only
    that the compressor is excluded from the handshake)
- [ ] Compressor priority ordering: client uses the first compressor in its configured list that is also in the server's
    list — no test for priority when multiple compressors match (e.g., client `[zstd, snappy, zlib]`, server supports
    `[snappy, zlib]`)
- [ ] OP_COMPRESSED structure validation: `originalOpcode`, `uncompressedSize`, `compressorId`, `compressedMessage`
    fields — no test for byte layout; tests only verify the round-trip outcome
- [ ] Compressor ID mapping: IDs 0 (`noop`), 1 (`snappy`), 2 (`zlib`), 3 (`zstd`) — no test verifying the correct ID
    appears in the OP_COMPRESSED header
- [ ] `zlibCompressionLevel` option: test all valid levels (-1 through 9)
- [ ] Mixed compression: server sends an uncompressed response after compression has been negotiated
- [ ] Authentication messages MUST NOT be compressed: `hello`, `saslStart`, `saslContinue`, `getnonce`, `authenticate`,
    `createUser`, `updateUser`, `copydbSaslStart`, `copydbgetnonce`, `copydb`
- [ ] Version compatibility: MongoDB 3.4 (snappy), 3.6 (+ zlib), 4.2 (+ zstd)

## Ambiguities

- **Warning for unknown compressor**: What log level? What message format? Spec shows example output but does not make
    it normative.
- **`compression: []` vs omitting the `compression` field**: Are these semantically equivalent? Spec says "SHOULD send
    empty compression argument `[]`" when compression is disabled but also "SHOULD be provided if driver supports
    compression."
- **Handshake reply compression**: Q&A says server "will use compression for any and all replies including the handshake
    reply" but main spec says "if no matching compressor, send response without compression field." These contradict for
    the handshake-response case.
- **`noop` compressor use case**: "Realistically only used for testing" — what is the test scenario? Why would a driver
    send OP_COMPRESSED with `noop` instead of just not compressing?

## Inconsistencies

- `compression: []` (SHOULD when disabled) vs omitting `compression` entirely (SHOULD when not supported) — the protocol
    may treat these differently but the spec treats them as equivalent.
- OP_COMPRESSED `originalOpcode` field duplicates information already present in the decompressed message — spec does
    not justify its presence.
- "No guarantee response will be compressed even if negotiated" (line 168) but "A client MAY implement compression for
    only OP_QUERY, OP_REPLY, OP_MSG" (line 172) — if a client skips OP_INSERT, the server might compress it and the
    client cannot decompress it. Spec does not address this scenario.

## Notes

- Test plan is prose-based (not executable YAML), relying on MongoDB server debug log IDs to verify compression. This
    makes automated verification difficult.
- Limited test coverage: only basic snappy usage and unsupported-compressor fallback.
- No test data files provided.
- Last Changelog entry: 2024-02-16.
