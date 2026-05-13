# Analysis: auth

## Missing Tests

- [ ] Drivers MUST raise an error if any required information for a mechanism is missing (§Errors) — no unified test for
    missing username in SCRAM-SHA-256
- [ ] A single invalid credential MUST be treated the same as all credentials being invalid (§Authentication Handshake)
- [ ] If authentication handshake fails, drivers MUST mark the server Unknown and clear its connection pool
    (§Authentication Handshake)
- [ ] Drivers MUST NOT raise an error if `saslSupportedMechs` includes an unknown mechanism (§Mechanism Negotiation) —
    no forward-compatibility test
- [ ] MONGODB-X509 certificate extraction for pre-3.4 servers (§MONGODB-X509) — no test for extracting username from
    cert
- [ ] GSSAPI hostname canonicalization with all three modes: "none", "forward", "forwardAndReverse" (§Hostname
    Canonicalization)
- [ ] Reauthentication on error 391 `ReauthenticationRequired` (§Reauthentication) — not in main auth unified tests
- [ ] All blocking auth operations MUST apply timeouts (§Authentication Handshake)

## Ambiguities

- **`saslSupportedMechs` fallback**: "If SCRAM-SHA-256 is present, use it; otherwise SCRAM-SHA-1 regardless of whether
    SCRAM-SHA-1 is in the list." Ambiguous wording — does "regardless" mean use SHA-1 even if the server only advertises
    SHA-256? Likely a drafting error.
- **Empty string credentials**: `mongodb://user:@host/` (with @ but empty password) — should empty strings be treated as
    "provided" or "missing"?
- **GSSAPI SERVICE_NAME**: No error handling defined when the server uses a different service name than the driver's
    default.

## Inconsistencies

- **Main spec vs. test file split**: `auth.md` covers all mechanisms but unified tests only exist for basic cases.
    `mongodb-aws.md` and `mongodb-oidc.md` contain extensive prose tests with no corresponding unified YAML files.
- **Reauthentication coverage**: Auth spec requires reauthentication support for error 391, but this is only in the
    OIDC-specific test file, not in the main auth unified tests.

## Notes

- Only 2 unified test YAML files. Most automated coverage is in legacy format or separate mechanism-specific prose
    files.
- Multi-user authentication: "Drivers MUST NOT start an implicit session when multiple users are authenticated" — no
    test validates this interaction with the sessions spec.
