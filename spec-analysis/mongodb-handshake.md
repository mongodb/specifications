# Analysis: mongodb-handshake

## Missing Tests

- [ ] FaaS environment variable detection for all 5 providers — prose tests exist (README Test 1 cases 1–9) but no
    unified YAML
- [ ] Container detection via `.dockerenv` and `KUBERNETES_SERVICE_HOST` — prose only
- [ ] `client.os.type` defaults to `"unknown"` when undeterminable — no test for the unknown fallback
- [ ] Metadata size limits: 512 bytes for client document, 128 bytes for `application.name` — truncation order not
    tested in unified format
- [ ] `application.name` MUST cause a failure if set after the first connection (§client.application.name)
- [ ] Duplicate `DriverInfoOptions` MUST NOT result in additional metadata (§Supporting Wrapping Libraries) — prose only
- [ ] Pipe character `|` in metadata strings MUST cause an error (§Supporting Wrapping Libraries)
- [ ] `saslSupportedMechs` with unknown mechanism MUST NOT raise an error (§Speculative Authentication) — prose only
- [ ] Speculative authentication command structure for SCRAM-SHA-1, SCRAM-SHA-256, MONGODB-OIDC (§Speculative
    Authentication)

## Ambiguities

- **FaaS precedence rule**: "vercel takes precedence over aws.lambda; any other combination MUST cause the other FaaS
    values to be entirely omitted." Does GCP + AWS silently omit both or raise an error?
- **Container + FaaS coexistence**: If only FaaS is present (no container), should `client.env.container` be omitted
    entirely or not attempted?
- **Truncation algorithm ("SHOULD" or "MUST")**: "Omit fields from env except env.name → omit fields from os except
    os.type → omit env document → truncate platform" — is this algorithm mandatory or a recommendation?
- **`appendMetadata` timing**: "MUST NOT apply updated metadata to already established connections." But if a connection
    closes for other reasons and reconnects, does it receive new metadata?

## Inconsistencies

- **`application.name` MUST NOT default vs. importance**: Spec says "MUST NOT provide a default value" for
    `application.name`, yet Q&A discusses SDAM implications of it not being in the URI — suggesting it's expected but
    cannot be defaulted.
- **`client.env` omission condition**: "If no fields of client.env would be populated, client.env MUST be entirely
    omitted." But FaaS field population uses "SHOULD." If some SHOULD fields are omitted, when exactly does "no fields"
    trigger?
- **Unified test vs. prose test mismatch**: README Test 1 defines parameterized test cases for metadata appending. The
    unified file `metadata-not-propagated.yml` only verifies that appending doesn't create/close connections — it does
    NOT verify metadata is actually appended to new connections' hello commands.

## Notes

- **Only 1 unified test file** (59 lines). Extensive prose tests in README (8 test suites) but none automated.
- FaaS/container detection is implementation-specific; spec says exact OS detection method is "undefined by this
    specification."
