# Analysis: uri-options

## Missing Tests

- [ ] `directConnection=true` with SRV URI MUST error (§directConnection URI option) — only multiple-seed case tested
- [ ] `heartbeatFrequencyMS < 500` MUST be rejected (§heartbeatFrequencyMS)
- [ ] `maxStalenessSeconds` values 0–89 (except -1) MUST be rejected — only valid values and -1 tested
- [ ] `maxConnecting=0` or negative MUST be rejected (positive integer required)
- [ ] `zlibCompressionLevel` outside -1..9 MUST be rejected
- [ ] `authMechanism` unknown value MUST be accepted (forward compatibility) — no test that unknown values are not
    rejected
- [ ] `authMechanismProperties` values containing colons (e.g., `TOKEN_RESOURCE:mongodb://foo`) — no test for colon
    handling
- [ ] `compressors` invalid value MUST warn, not error (references compression spec)
- [ ] `connectTimeoutMS=0` means no timeout (not immediate timeout)
- [ ] `readPreferenceTags` order MUST be preserved across multiple occurrences
- [ ] `socketTimeoutMS` deprecation warning MUST be issued
- [ ] `wTimeoutMS` values > 2^31-1 MUST be accepted (64-bit integer)
- [ ] TLS enabled implicitly when other TLS options are present — which options trigger this?

## Ambiguities

- **Optional options for poolless drivers**: For options "required for drivers with connection pools" (maxIdleTimeMS,
    maxPoolSize, etc.), must drivers without explicit pools ignore or error?
- **`readPreference` case normalization**: Must `primarypreferred` or `PrimaryPreferred` be accepted and normalized, or
    rejected?
- **`serverMonitoringMode` for single-threaded drivers**: Required for multi-threaded/async drivers — must
    single-threaded drivers reject or silently ignore?

## Inconsistencies

- **`maxConnecting` (positive int) vs. `maxPoolSize` (non-negative int)**: `maxConnecting` cannot be 0 but `maxPoolSize`
    can — no justification for the asymmetry.
- **`wTimeoutMS` deprecation**: `read-write-concern.md` marks it deprecated in favor of `timeoutMS`, but the URI options
    table lists it without a deprecation note.
- **`journal` in URI vs. `j` on wire**: URI option is `journal` but write concern wire field is `j`. Mapping is
    documented in `read-write-concern` tests but not in `uri-options` itself.

## Notes

- ~179 tests across 11 files. TLS options have the most comprehensive coverage (~90 tests).
- Test format is consistent: `{uri, valid, warning, options}` schema across all files.
- No tests for type coercion edge cases (e.g., `maxPoolSize=abc` — warn or error?).
- Deprecation warnings are not explicitly tested for deprecated options.
