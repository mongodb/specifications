# Analysis: command-logging-and-monitoring

## Missing Tests

- [ ] All commands in a single bulk write operation MUST share the same `operationId` — tests verify structure but not
    that all commands in a batch share identical `operationId`
- [ ] OP_MSG document sequences MUST be represented as a BSON array in `CommandStartedEvent.command` — tests exercise
    bulk insert but don't explicitly assert the array representation
- [ ] Default write concern MUST be omitted from published command — tests cover unacknowledged writes (`w:0`) but no
    test verifies that a command with default write concern omits it
- [ ] `serviceId` MUST appear in all three event types (Started, Succeeded, Failed) — likely only tested in one
- [ ] Heartbeat command exclusion from logs — `no-handshake-messages.yml` tests handshake but no equivalent test for
    heartbeat commands
- [ ] Server-side `CommandFailedEvent` redaction: `errmsg` and extra fields MUST be removed,
    `code`/`codeName`/`errorLabels` kept — tests focus on auth commands but not general server-error redaction

## Ambiguities

- **`hello` with `speculativeAuthenticate` redaction scope**: Does presence of `speculativeAuthenticate` require
    redacting the entire `hello` command, or only the `speculativeAuthenticate` field?
- **Unacknowledged write reply fields**: Spec requires `{ ok: 1 }` reply for unacknowledged writes but doesn't specify
    whether `n` or other fields may/must be present.
- **`connectionId` structure flexibility**: "For languages without ConnectionId, return driver equivalent which MUST
    include server address and port. The name is flexible." Tests expect specific structure; spec should tighten or
    provide canonical JSON example.
- **`operationId` generation trigger**: Marked OPTIONAL in all event types but spec doesn't define which operations MUST
    include it. Only describes bulk operations; no guidance for single commands.

## Inconsistencies

- **Guarantees section vs. test coverage**: Spec guarantees every `CommandStartedEvent` has a correlating Succeeded or
    Failed, and `requestId` matches — tested for specific operations but not systematically across all CRUD + retry
    scenarios.
- **Logging vs. Monitoring parity**: Spec says drivers MAY implement logging via event subscriber (same mechanism).
    Tests have separate logging and monitoring directories, potentially masking functional divergence between the two.

## Notes

- 10 logging + 15 monitoring test files. Strong coverage for CRUD, error cases, and redaction.
- Prose tests (3 items: truncation limit, explicit truncation, multi-byte codepoints) are well-defined and placed in
    README.
- All tests in unified format; legacy format migration completed in 2022.
