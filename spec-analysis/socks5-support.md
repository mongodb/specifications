# Analysis: socks5-support

## Missing Tests

- [ ] Connection string validation errors: `proxyPort` without `proxyHost`; `proxyUsername` without
    `proxyPassword`/`proxyHost`; `proxyPassword` without `proxyHost`/`proxyUsername` — not covered in `test/README.md`
- [ ] SOCKS5 handshake wire format compliance with RFC 1928 — current tests verify connection outcome only, not
    handshake bytes
- [ ] Destination hostname MUST NOT be DNS-resolved locally; passed as-is to the proxy — verify no A/AAAA DNS queries
    are made for the destination
- [ ] KMS server connections MUST use the SOCKS5 proxy — not covered in `test/README.md`
- [ ] `mongocryptd` connections MUST NOT use the SOCKS5 proxy — not covered in `test/README.md`
- [ ] SOCKS5 connection or authentication failure is treated identically to `ECONNREFUSED` — current tests verify
    failure but not error type equivalence
- [ ] Command monitoring events MUST NOT reference the SOCKS5 proxy in any field — `test/README.md` only checks one
    connection string and one event

## Ambiguities

- **Generic parameter names**: Why are parameters generic (no explicit SOCKS5 mention)? Future protocol extensibility is
    noted but no guidance is given for naming future protocols or maintaining backward compatibility.
- **`proxyHost` as domain name vs IP**: RFC 1928 supports different address types. Spec does not clarify what format the
    driver must pass to the SOCKS5 proxy (domain name vs. resolved IP).
- **Authentication method negotiation edge case**: Only one of `proxyUsername`/`proxyPassword` provided — spec says
    error (lines 52–53) but does not clarify whether this is at construction time or at connection time.
- **`proxyHost` DNS resolution**: Spec says "MUST NOT resolve destination hostname" — but should `proxyHost` itself be
    DNS-resolved before the TCP connect?

## Inconsistencies

- **KMS proxied, `mongocryptd` not proxied**: No explanation in the spec or Q&A for this asymmetry.
- **`directConnection=true` with SOCKS5**: `test/README.md` line 33 tests this combination but the main spec does not
    define this interaction. Is proxying disabled when `directConnection=true`?
- Spec does not define behavior if `proxyHost` DNS resolution fails (for drivers that resolve before TCP connect).

## Notes

- Test infrastructure is simpler than OCSP: requires only `socks5srv.py` from `drivers-evergreen-tools` and a replica
    set.
- All tests are integration tests; no unit tests for SOCKS5 handshake parsing are possible without exposing internal
    APIs.
- Command monitoring transparency is harder to verify than the spec implies — all event fields should be checked, not
    just one.
- Client-side encryption coverage gap: KMS proxying and `mongocryptd` non-proxying are not tested in `test/README.md`.
- No `## Changelog` section visible in spec file.
