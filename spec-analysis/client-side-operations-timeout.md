# Analysis: client-side-operations-timeout

## Missing Tests

- [ ] Implicit session acquisition timeout — spec says this is blocking only for certain drivers; no unified test for
    this path
- [ ] `maxAwaitTimeMS >= timeoutMS` MUST raise an error for tailable awaitData cursors — test exists but doesn't assert
    the error is raised at the right threshold
- [ ] `maxTimeMS` MUST NOT be appended for tailable non-awaitData cursors — test file exists but doesn't assert absence
    in `getMore` commands
- [ ] `minPoolSize` maintenance connections MUST use `connectTimeoutMS`, NOT `timeoutMS` — prose test 4 covers
    saslContinue but not this specific distinction
- [ ] Default 120-second timeout for `withTransaction` when `timeoutMS` is unset — tests set explicit values; default
    behavior not verified
- [ ] CSOT-enabled retry count: multiple retries MUST be allowed (vs. single retry when CSOT unset) — no tests for
    CSOT-specific retry count change
- [ ] Cursor `close()` MUST succeed with refreshed timeout even if original timeout expired (`CURSOR_LIFETIME` mode)

## Ambiguities

- **`min(0, other)` universality**: "For cases where 0 means 'infinite', `min(0, other)` MUST evaluate to `other`."
    Which other timeout options also treat 0 as infinite?
- **`minRoundTripTime` definition**: Used in command execution section but only explained in design rationale. Should be
    defined inline or linked.
- **`close()` refresh scope**: Does timeout refresh apply to implicit destructors (garbage collection) or only explicit
    `close()` calls?
- **Client Side Encryption**: "Remaining `timeoutMS` MUST be used for `listCollections` and `find` commands" — is this
    per-command or for the entire encryption/decryption sequence?

## Inconsistencies

- **`runCommand` with `maxTimeMS` in command document**: Behavior is "undefined" and drivers MUST document it but MUST
    NOT check for it — but no test validates drivers do NOT throw an error, confirming the "undefined" behavior passes
    through.
- **`waitQueueTimeoutMS` deprecation test language**: Prose test 1 in README says "SHOULD implement" unit tests for
    `waitQueueTimeoutMS` behavior, but spec says `timeoutMS` MUST override it.

## Notes

- 28 YAML test files + extensive prose tests (11 sections). Strong coverage for CRUD, GridFS, background pooling, server
    selection, and transactions.
- Some blocking sections (implicit sessions, OCSP) rely on optional prose/unit tests.
- [PR #1888](https://github.com/mongodb/specifications/pull/1888) /
    [DRIVERS-3006](https://jira.mongodb.org/browse/DRIVERS-3006) (in review): consolidate CSOT change stream timeout
    tests.
- [PR #1887](https://github.com/mongodb/specifications/pull/1887) /
    [DRIVERS-3269](https://jira.mongodb.org/browse/DRIVERS-3269) (open): move aggregation tests out of tailable
    awaitData cursor.
- [PR #1845](https://github.com/mongodb/specifications/pull/1845) /
    [DRIVERS-2884](https://jira.mongodb.org/browse/DRIVERS-2884) (open): CSOT avoid connection churn on timeout.
- [DRIVERS-2965](https://jira.mongodb.org/browse/DRIVERS-2965) (Blocked): fix CSOT tests that contradict spec.
- [DRIVERS-3259](https://jira.mongodb.org/browse/DRIVERS-3259) (Backlog): CSOT GA.
