# Analysis: ocsp-support

## Missing Tests

- [ ] Cache key structure matches RFC 6960 Section 4.1.1 `CertID` — no unit test for cache key construction
- [ ] Cache validity boundary conditions: exactly at `nextUpdate`, before `thisUpdate`
- [ ] `tlsDisableOCSPEndpointCheck` and `tlsDisableCertificateRevocationCheck` conflict — URI options tests exist but no
    exact error messages or exception types specified
- [ ] SNI MUST be used in TLS `ClientHello` — no explicit test that SNI is actually included
- [ ] Driver SHOULD NOT reach OCSP endpoints for intermediate certificates — negative test (verify no intermediate
    network calls are made)
- [ ] Soft-fail behavior: connection proceeds when the OCSP endpoint is unreachable and no stapled response is available

## Ambiguities

- **Soft Fail vs Hard Fail detection**: Default value of `tlsDisableOCSPEndpointCheck` depends on whether the driver
    exhibits soft or hard-fail behavior, but no programmatic detection mechanism is specified.
- **OCSP responder timeout**: "A timeout should be applied per CSOT, with a default of five seconds" — is "should" MUST
    or SHOULD? Is this per-responder or cumulative for parallel requests?
- **"Unknown" OCSP response**: Does "unknown" include network timeouts and transient errors? The boundary between
    "unknown", "revoked", and "good" is not defined.
- **"Application-wide settings"**: "MUST NOT change any OCSP settings" — unclear what constitutes "OCSP settings" and
    how to detect whether the TLS library uses application-wide settings.
- **Parallel responder queries – "first valid response"**: First to arrive or first to be processed? What if multiple
    responders disagree (one says "good", another says "revoked")?

## Inconsistencies

- Cache may be empty or partial (only "conclusive" responses are cached) but spec says "driver SHOULD attempt to
    validate using the cache" — fallback behavior when the cache is empty is not defined.
- Distinction between "server's certificate" OCSP endpoint (reach: YES) and "intermediate certificate" OCSP endpoints
    (reach: NO) is unclear when the certificate chain has multiple intermediate CAs.
- Line 35: "OCSP MUST be enabled by default whenever possible" vs. line 179: "MUST enable OCSP unless driver exhibits
    hard-fail behavior" — precedence is unclear for hard-fail drivers.

## Notes

- All practical tests are integration tests requiring an OCSP responder, specific certificates, and
    `mongo-orchestration`.
- Platform-specific behavior (Windows/macOS/Linux stapling support) is documented but not programmatically enforced in
    the test matrix.
- Requires substantial infrastructure: `drivers-evergreen-tools`, RSA/ECDSA certificates with Must-Staple extension,
    OS-level cache management.
