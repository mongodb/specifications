# Analysis: versioned-api

## Missing Tests

- [ ] Declaring an unknown API version (e.g., `"99"`) MUST trigger a client-side error (§ServerApi class)
- [ ] Changes to `ServerApi` after creation MUST be prohibited (immutability) (§ServerApi class)
- [ ] Overriding API version at Database or Collection level MUST be prevented or ignored (§Declared Version
    Inheritance)
- [ ] API version MUST be sent even to servers with old `maxWireVersion` (MUST NOT use maxWireVersion to gate API
    version)
- [ ] `commitTransaction` and `abortTransaction` MUST include API version parameters (§Transactions)
- [ ] `runCommand` with API version on client + API fields in command document — behavior is "undefined" but should be
    documented/tested
- [ ] `getMore` API parameters MUST match the cursor-initiating command's parameters — mismatch should produce server
    error

## Ambiguities

- **"SHOULD" for implementation guidance vs. driver requirements**: Spec notes it uses SHOULD more than other specs "in
    the context of providing guidance on writing test files." Unclear whether SHOULD in implementation sections (e.g.,
    "SHOULD define an enumeration") is truly optional.
- **`readConcern` "default" in transactions**: "readConcern MUST be set if it is NOT the default." What is "the
    default"? Null, server default, or client/database readConcern?
- **API version via connection string**: "MUST NOT allow specification of any stable API options via the connection
    string." If a legacy connection string somehow includes API version fields, should the client error or ignore?
- **`strict=false` and `deprecationErrors=false` on wire**: `$$unsetOrMatches: false` in tests suggests these may
    sometimes be omitted when false. Is false omitted or explicitly sent?

## Inconsistencies

- **API parameters scope for getMore vs. transactions**: Both require API parameters to "match" but spec doesn't define
    what "match" means — identical fields, or just same version?
- **OP_MSG scope**: Spec requires OP_MSG for all messages when API version is declared, but the handshake spec already
    requires this for stable API clients. Creates circular dependency.
- **`runCommand` inheritance vs. readConcern/writeConcern non-inheritance**: API version IS inherited by `runCommand`,
    but ReadConcern/WriteConcern are NOT. No explanation for this asymmetry.

## Notes

- 6 test files (~370 lines total). Heavily focused on CRUD operations; validation, error handling, and edge cases
    undertested.
- No test covers the "undefined behavior" case: API fields in command document + API version on client.
- `transaction-handling.yml` covers `startTransaction` and `insertOne` with API parameters, but doesn't assert API
    params on `commitTransaction`/`abortTransaction`.
