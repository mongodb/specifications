# Analysis: logging

## Missing Tests

Testing is delegated to the unified test format spec; no local test files are expected. However, the following behaviors
lack explicit test coverage:

- [ ] Per-component env vars (`MONGODB_LOG_COMMAND`, `MONGODB_LOG_TOPOLOGY`, `MONGODB_LOG_SERVER_SELECTION`,
    `MONGODB_LOG_CONNECTION`, `MONGODB_LOG_ALL`) correctly set log levels
- [ ] Invalid env var values are silently ignored (no exception thrown)
- [ ] Log destination configured via `MONGODB_LOG_PATH`: stdout, stderr, or a file path
- [ ] Documents longer than `MONGODB_LOG_MAX_DOCUMENT_LENGTH` are truncated with `"..."` appended
- [ ] BSON documents in log messages use Relaxed Extended JSON format
- [ ] Null values are omitted from structured log messages
- [ ] Expensive operations (e.g., Extended JSON serialization) are only executed when the log level is enabled
- [ ] Field names in structured logs match the exact casing specified in individual driver specs

## Ambiguities

- **"Does not require code changes" vs "minimal changes acceptable"**: Spec says drivers SHOULD support logging without
    requiring any application changes but then says "minimal changes are acceptable." Pick one.
- **Non-file logging frameworks**: "Provide a straightforward, idiomatic way to programmatically consume messages and
    write to a file" — too vague. Does the driver need to ship a built-in file handler, or is documentation sufficient?
- **Truncation logic contradiction**: "MUST ensure graceful handling of mid-code-point truncation" but also "MUST
    implement truncation naively by simply truncating at the required length." These directly contradict each other.
- **"Less severe level if one is available"**: "Available" could mean supported by the logging framework OR present in
    the spec table — ambiguous.
- **"Internal way to intercept structured data"**: What does "internal" mean for drivers that use unstructured logging
    frameworks?

## Inconsistencies

- **Programmatic precedence vs user override**: Spec says "programmatic configuration MUST take precedence over
    environment variables" but Design Rationale says it is straightforward for users to override, and spec then says
    "MUST provide an example of how users can implement custom logic to allow an env var to override a programmatic
    default" — contradicts the precedence rule.
- **Error handling asymmetry**: Invalid env vars → silent (MAY warn, MUST NOT throw). Invalid API options → MUST
    validate, SHOULD throw. Asymmetric error handling with no justification.

## Notes

- This is a meta-spec: it defines logging infrastructure, not message content. Actual message content is defined in
    `command-logging-and-monitoring`, SDAM, etc.
- Security section: individual specs must define redaction rules for sensitive fields.
- Status: Accepted.
- Changelog present (lines 404–421).
