# Analysis: open-telemetry

## Missing Tests

- [ ] `db.query.text` truncation at `query_text_max_length` — only absence when disabled is tested; no test for partial
    truncation
- [ ] Environment variable configuration (`OTEL_#{LANG}_INSTRUMENTATION_MONGODB_ENABLED`,
    `OTEL_#{LANG}_INSTRUMENTATION_MONGODB_QUERY_TEXT_MAX_LENGTH`) — prose tests only, no YAML
- [ ] Tracer attributes (`name`, `version`) MUST be set when creating a Tracer — never validated
- [ ] Spans MUST be created within the current span of the host application (parent-child relationship) — not tested
- [ ] Exception attributes at driver operation level (`exception.message`, `exception.type`, `exception.stacktrace`) —
    command-level only, not operation-level
- [ ] Client-level `bulkWrite` operation span — distinct from collection-level; coverage unclear
- [ ] Retry behavior: each retry MUST produce a separate command span nested under the same operation span — tested but
    spec wording is ambiguous on expected structure
- [ ] `db.mongodb.cursor_id`, `db.mongodb.lsid`, `db.mongodb.txn_number` for cursor-returning operations —
    `distinct.yml`, `count.yml` etc. exist but don't assert all three attributes

## Ambiguities

- **`db.namespace` for admin database commands**: Spec repeats guidance for `commitTransaction → admin` in two sections;
    unclear if client-level `bulkWrite` on admin has different requirements.
- **`network.transport` values**: MUST be `'tcp'` or `'unix'` — unclear if `'wss'` (WebSocket) should be supported.
- **`db.query.text` excluded fields in transactions**: Commands in transactions include `txnNumber` and `autocommit` —
    should these also be excluded from `db.query.text`?
- **`db.mongodb.cursor_id` condition**: "SHOULD be added if a cursor is created or used in the operation" — does "used"
    mean any operation that accepts a cursor ID, or only ones that actually return/have a cursor?

## Inconsistencies

- **Query truncation not tested**: `find_without_query_text.yml` disables payload entirely
    (`enableCommandPayload: false`); no test demonstrates partial truncation matching the logging spec behavior.
- **`ignoreExtraSpans: true` in some tests**: May mask missing spans (e.g., `find.yml` line 85); reduces strictness of
    assertions.
- **Test file naming vs. spec operation names**: Spec lists `findOneAndDelete` but test file is `find_and_modify.yml`.

## Notes

- 22 YAML test files with `ignoreExtraSpans: false` for strict assertions. 2 prose tests (environment variables) require
    manual implementation per driver.
- Spec allows implementing tracing without adding the OTel SDK dependency — tests don't validate this requirement.
- No Changelog section.
