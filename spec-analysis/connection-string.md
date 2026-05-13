# Analysis: connection-string

## Missing Tests

- [ ] Userinfo with reserved characters (/, ?, #) — should they cause errors or warnings? (§Userinfo)
- [ ] Malformed percent-encoding in userinfo (e.g., `%ZZ`, `%1`) MUST throw an exception (§Userinfo Q&A)
- [ ] Unencoded UNIX socket paths MUST produce an error about URL encoding (§Host Information)
- [ ] Port 0 and port 65536 MUST be rejected (§Port) — Changelog 2016-07-22 clarified port 0 is invalid but no test
    covers this
- [ ] Auth database containing prohibited characters (/, , space, `"`, $) MUST cause parsing errors (§Auth Database)
- [ ] Auth database present without credentials MUST NOT trigger authentication (§Auth Database)
- [ ] Deprecated key with renamed key both present: deprecated MUST be ignored and warning logged (§Deprecated Key Value
    Pairs)
- [ ] Semi-colon delimiter (;) as alternative to & MUST be supported (§Legacy support)
- [ ] Non-ASCII characters in username, password, or database name (§Q&A)
- [ ] Multiple @ symbols in auth info (e.g., `mongodb://anne:bob:pass@localhost`) MUST error (§Q&A)

## Ambiguities

- **Key normalization for non-ASCII**: Spec says "lower casing uppercase ASCII characters A through Z." What about
    non-ASCII? What about underscore vs. camelCase enforcement?
- **Auth database optional boundary**: If neither auth database nor options are provided, what exactly is parsed? Empty
    string or absent?
- **Repeated keys with undefined precedence**: "If a key is repeated and the data type is not a List, precedence is
    undefined." Drivers may behave inconsistently for repeated non-list keys.

## Inconsistencies

- **Colon in values is allowed, comma is not**: "Drivers MUST handle unencoded colon signs within the value" but "a
    value containing a comma MUST NOT be provided via the connection string." No tests verify this asymmetry.
- **Period in auth database**: Spec says "Drivers MAY allow periods for namespace notation" in auth database, but also
    says "database names cannot contain a dot" (used to distinguish socket paths from databases). Acknowledged in Q&A
    but not tested.

## Notes

- ~94 tests across 8 test files. Well-organized by category (auth, hosts, sockets, options, valid, invalid).
- Unix socket tests are comprehensive (absolute and relative paths).
- Warnings vs. errors distinction is clearly separated (`valid: false` vs. `warning: true`).
