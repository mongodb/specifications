# Analysis: faas-automated-testing

## Missing Tests

This is a **procedural CI/CD guide**, not a normative driver-behavior specification. Most "missing tests" are CI/CD
validation, not unit-testable spec compliance. Testable items:

- [ ] Lambda function creates `MongoClient`, attaches the required listeners (ServerHeartbeatStarted,
    ServerHeartbeatFailed, CommandSucceeded, CommandFailed, ConnectionCreated, ConnectionClosed), performs a single
    insert + delete, and records metrics
- [ ] Function response asserts no `ServerHeartbeat` events contain `awaited=True` (streaming protocol disabled)
- [ ] Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, MONGODB_URI) are correctly read by
    the function

## Ambiguities

- **"Single insert then single delete"**: Ambiguous — delete the same document? Verify `deletedCount=1`?
- **JSON response schema**: "Report metrics as JSON" — no schema defined for the response payload.
- **Host IP for M1 Macs**: "127.0.0.1 MUST be replaced with `host.docker.internal`" — no guidance for detecting or
    automating the fallback for other configurations.

## Inconsistencies

- **AWS region**: Line 46 appears to fix `AWS_REGION=us-east-1` but CI task setup shows it as configurable. Fixed or
    configurable?
- **SAM CLI variants**: 13+ supported Evergreen variants listed but spec says "run on a single variant." No guidance on
    which variant to choose.

## Notes

- **`Status` field is empty** (line 3) — should be filled in.
- This is a guide/tutorial, not a normative spec. Automated testing is largely infeasible here; the document describes
    CI/CD infrastructure setup.
- Changelog present (lines 334–341).
