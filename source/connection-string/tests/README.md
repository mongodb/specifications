# Connection String Tests

The YAML and JSON files in this directory tree are platform-independent tests that drivers can use to prove their
conformance to the Connection String Spec.

As the spec is primarily concerned with parsing the parts of a URI, these tests do not focus on host and option
validation. Where necessary, the tests use options known to be (un)supported by drivers to assert behavior such as
issuing a warning on repeated option keys. As such these YAML tests are in no way a replacement for more thorough
testing. However, they can provide an initial verification of your implementation.

## Version

Files in the "specifications" repository have no version scheme. They are not tied to a MongoDB server version.

## Format

Each YAML file contains an object with a single `tests` key. This key is an array of test case objects, each of which
have the following keys:

- `description`: A string describing the test.
- `uri`: A string containing the URI to be parsed.
- `valid:` A boolean indicating if the URI should be considered valid.
- `warning:` A boolean indicating whether URI parsing should emit a warning (independent of whether or not the URI is
    valid).
- `hosts`: An array of host objects, each of which have the following keys:
    - `type`: A string denoting the type of host. Possible values are "ipv4", "ip_literal", "hostname", and "unix".
        Asserting the type is *optional*.
    - `host`: A string containing the parsed host.
    - `port`: An integer containing the parsed port number.
- `auth`: An object containing the following keys:
    - `username`: A string containing the parsed username. For auth mechanisms that do not utilize a password, this may be
        the entire `userinfo` token (as discussed in [RFC 2396](https://www.ietf.org/rfc/rfc2396.txt)).
    - `password`: A string containing the parsed password.
    - `db`: A string containing the parsed authentication database. For legacy implementations that support namespaces
        (databases and collections) this may be the full namespace eg: `<db>.<coll>`
- `options`: An object containing key/value pairs for each parsed query string option.

If a test case includes a null value for one of these keys (e.g. `auth: ~`, `port: ~`), no assertion is necessary. This
both simplifies parsing of the test files (keys should always exist) and allows flexibility for drivers that might
substitute default values *during* parsing (e.g. omitted `port` could be parsed as 27017).

The `valid` and `warning` fields are boolean in order to keep the tests flexible. We are not concerned with asserting
the format of specific error or warnings messages strings.

### Use as unit tests

Testing whether a URI is valid or not should simply be a matter of checking whether URI parsing (or MongoClient
construction) raises an error or exception. Testing for emitted warnings may require more legwork (e.g. configuring a
log handler and watching for output).

Not all drivers may be able to directly assert the hosts, auth credentials, and options. Doing so may require exposing
the driver's URI parsing component.

The file `valid-db-with-dotted-name.yml` is a special case for testing drivers that allow dotted namespaces, instead of
only database names, in the Auth Database portion of the URI.

## Credential disclosure tests

`credential-disclosure.yml` is a separate corpus for the requirements in
[Disclosure of Sensitive Values](../connection-string-spec.md#disclosure-of-sensitive-values). Its cases have only two
keys:

- `description`: A string describing the test.
- `uri`: A string containing the URI to be parsed.

Every URI carries a sentinel credential, in the username or the password component, in one of two forms:

- the literal `SENTINELpassword1234`, or
- that same literal fully percent-encoded, as `%53%45%4E%54%49%4E%45%4C%70%61%73%73%77%6F%72%64%31%32%33%34`.

The sentinel is deliberately alphanumeric so that no percent-encoding of the URI can split it and a driver can detect it
by scanning for it as a fixed string. A driver MUST scan for both forms, case-insensitively: the literal form because
drivers lowercase option keys, and the encoded form because a driver that echoes the URI without decoding it still
discloses a credential that is trivially recoverable. Cases carrying the encoded form exist because several drivers
decode a component before including it in a message. No other normalization is required.

For each case:

- If the driver rejects the URI, neither form of the sentinel may appear in the resulting error message.
- Any warning the driver logs while parsing the URI must contain neither form of the sentinel.
- If the driver accepts the URI, the case asserts nothing.

The last clause is deliberate. These URIs are malformed in ways this specification does not fully pin down, so drivers
legitimately differ on which of them parse. Where a driver accepts one, the sentinel has been relocated into a parsed
component such as the database name or an option value, and that is a separate defect from the message hygiene these
tests cover, and it is tracked separately. Tightening this into an unconditional "the sentinel appears nowhere"
assertion would fail drivers for a defect these tests are not about.

Drivers SHOULD run each case twice: once catching the error and inspecting only its message, and once letting the error
escape to the language runtime's default handler. Drivers have been observed to disclose on one path and not the other.

The corpus is curated rather than exhaustive. When adding cases, include at least one per structural family per
disclosure mechanism, and prefer a URI shape that is known to leak in more than one driver: cross-driver provenance is
what makes a case worth its place, since a corpus assembled from any single driver's own ideas has repeatedly been shown
to miss shapes that leak in most of the others.

## Prose Tests

These tests cover requirements that cannot be expressed as a list of URIs. They use the sentinel credentials
`SENTINELuser5678` and `SENTINELpassword1234`.

1. **Redacted string representation.** Construct a connection string object, and a client if the driver's API requires
    one, from `mongodb://SENTINELuser5678:SENTINELpassword1234@localhost:27017/db`. This URI is valid, so no error is
    raised. Assert that neither sentinel appears in any idiomatic representation of the object: the language's string
    conversion, its debug or inspection representation, and its serialized form if the object is serializable. Assert
    that the driver's redaction marker appears in place of both the username and the password, and that it is the same
    marker in both positions.

2. **Explicitly named unredacted API.** If the driver provides an API that returns the unredacted connection string,
    assert that it returns both sentinels, and confirm by inspection that its name makes the disclosure evident.

3. **Unrecognized option values are not logged.** Parse
    `mongodb://localhost:27017/?notARealOption=SENTINELpassword1234`. Assert that the driver does not log the sentinel
    password string.

4. **Sensitive option values are not logged.** Parse
    `mongodb://localhost:27017/?authMechanismProperties=SENTINELpassword1234`, whose value is malformed because it
    contains no colon. Assert that any message the driver emits does not contain the sentinel.
