# OCSP Support Test Plan

## Introduction

The prose tests defined in this file are platform-independent tests that drivers can use to prove their conformance to
the OCSP Support specification. These tests MUST BE implemented by all drivers.

Additional YAML and JSON tests have also been added to the [URI Options Tests](../../uri-options/tests/README.md).
Specifically, the [TLS Options Test](../../uri-options/tests/tls-options.yml) has been updated with additional tests for
the new URI options `tlsDisableOCSPEndpointCheck` and `tlsDisableCertificateRevocationCheck`.

Tests involving the new URI options MUST BE implemented by drivers that are able to support those new URI options (see
[MongoClient Configuration](../ocsp-support.md#mongoclient-configuration)).

## Testing Invalid Configurations

The following tests only apply to drivers that expose an option to enable/disable certificate revocation checking on a
per MongoClient basis.

1. Create a MongoClient with `tlsInsecure=true`.
2. Enable certificate revocation checking on the MongoClient.
3. Ensure that an error is thrown noting that revocation checking cannot be used in combination with `tlsInsecure=true`.

The following test only applies to drivers that expose an option to enable/disable certificate revocation checking on a
per MongoClient basis and implement support for `tlsAllowInvalidCertificates`.

1. Create a MongoClient with `tlsAllowInvalidCertificates=true`.
2. Enable certificate revocation checking on the MongoClient
3. Ensure that an error is thrown noting that revocation checking cannot be used in combination with
    `tlsAllowInvalidCertificates=true`.

## Integration Tests: Permutations to Be Tested

For integration tests, we will test all combinations of URI options that influence a driver's OCSP behavior with both
validity states of the server's certificate (configured with the mock OCSP responder). We will also test the case where
an OCSP responder is unavailable and two malicious server cases.

Drivers that do not default to enabling OCSP MUST enable OCSP for these tests.

| **URI options**                                    | **Test 1:** **Valid cert + server that staples** | **Test 2:** **Revoked cert + server that staples** | **Test 3:** **Valid cert + server that does not staple** | **Test 4:** **Revoked cert + server that does not staple** | **Soft Fail Test:** **No OCSP Responder + server that does not staple** | **Malicious Server Test 1:** **Revoked cert + server w/ Must- Staple cert that does not staple** | **Malicious Server Test 2: No OCSP Responder + server w/ Must-** **Staple cert that does not staple** |
| -------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| `tls=true`                                         | OK                                               | FAIL                                               | OK                                                       | FAIL                                                       | OK\*                                                                    | FAIL\*                                                                                           | FAIL\*                                                                                                |
| `tls=true` <br>`&tlsInsecure=true`                 | OK                                               | OK                                                 | OK                                                       | OK                                                         | OK                                                                      | OK                                                                                               | OK                                                                                                    |
| `tls=true` <br>`&tlsAllowInvalidCertificates=true` | OK                                               | OK                                                 | OK                                                       | OK                                                         | OK                                                                      | OK                                                                                               | OK                                                                                                    |

See [Required Server Versions](../ocsp-support.md#required-server-versions) to determine which versions of the server
can be used for each column.

Note: From the perspective of a driver that does not support OCSP stapling, the following sets of tests should be
identical: {Test 1, Test 3}, {Test 2, Test 4, Malicious Server Test 1}, and {Soft Fail Test, Malicious Server Test 2}.
For drivers with full control over their OCSP behavior, both malicious server tests are identical as well. However, it
does no harm to test these extra cases and may help reveal unexpected behavior.

\*: Drivers that cannot pass these tests due to limitations in their TLS library's implementation of OCSP will need to
document these failures as described under [Documentation Requirements](../ocsp-support.md#documentation-requirements).
Additionally, drivers that fail the "Soft Fail Test" will need to change any applicable defaults as described under
[MongoClient Configuration](../ocsp-support.md#mongoclient-configuration)

## Mock OCSP Responder Testing Suite

The certificates and scripts needed for testing OCSP are part of
[driver-evergreen-tools](https://github.com/mongodb-labs/drivers-evergreen-tools) in `.evergreen/ocsp`. The `rsa` and
`ecdsa` directories contain the certificates and scripts needed to test with RSA and ECDSA certificates, respectively.

Both of the above directories contain four scripts: `mock-valid.sh`, `mock-revoked.sh`, `mock-delegate-valid.sh`, and
`mock-delegate-revoked.sh`.

`mock-valid.sh` starts up a mock OCSP responder that uses the issuing CA's certificate. This responder will report that
every certificate is valid.

`mock-revoked.sh` starts up a mock OCSP responder that uses the issuing CA's certificate. This responder will report
that every certificate is revoked.

`mock-delegate-valid-valid.sh` starts up a mock OCSP responder that uses a delegate certificate. This responder will
report that every certificate is valid.

`mock-delegate-revoked.sh` starts up a mock OCSP that uses a delegate certificate. This responder will report that every
certificate is revoked.

### mongo-orchestration configurations

The mongo-orchestration configurations needed for testing can be found at `.evergreen/orchestration/configs/servers/`.

#### RSA Tests

Tests that specify that a server should staple MUST use `rsa-basic-tls-ocsp-mustStaple.json`. Tests that specify that a
server should not staple MUST use `rsa-basic-tls-ocsp-disableStapling.json`. The malicious server tests MUST use
`rsa-basic-tls-ocsp-mustStaple-disableStapling.json`.

#### ECDSA Tests

Tests that specify that a server should staple MUST use `ecdsa-basic-tls-ocsp-mustStaple.json`. Tests that specify that
a server should not staple MUST use `ecdsa-basic-tls-ocsp-disableStapling.json`. The malicious server tests MUST use
`ecdsa-basic-tls-ocsp-mustStaple-disableStapling.json`.

## Test Procedure

Each column that utilizes an OCSP responder represents four tests:

1. A test with RSA certificates and an OCSP responder that uses the issuing CA's certificate
2. A test with RSA certificates and an OCSP responder that uses a delegate certificate
3. A test with ECDSA certificates and an OCSP responder that uses the issuing CA's certificate
4. A test with ECDSA certificates and an OCSP responder that uses a delegate certificate

Each column that does not utilize an OCSP responder (i.e. "Soft Fail Test" and "Malicious Server Test 2") represent two
tests:

1. A test with RSA certificates
2. A test with ECDSA certificates

Each test MUST BE its own Evergreen task in order to minimize the impact of OCSP caching. OCSP caching can exist at the
OS-level, user-level and/or application-level; having separate Evergreen tasks should help minimize the impact of
user-level and application-level caching since Evergreen performs some cleanup between test runs.

Since each test column represents four tests, and each test is run as a separate Evergreen task, each Evergreen task
SHOULD set a `batchtime` of 14 days to reduce how often these tests run (this will not affect patch builds).

Any OCSP caches that persist between test runs (e.g. the OS-level OCSP cache) MUST be cleared before configuring a
certificate chain. This is important because the Evergreen instance that is running a driver's test may have a cached
response from a previous test run (Evergreen instances are generally reused between test runs), and this cached result
could lead the driver or server to read stale data. See the
[Appendix](../ocsp-support.md#os-level-ocsp-cache-manipulation) for instructions on how to clear OS-level OCSP caches.

For each test, ensure that the mock OCSP responder is configured to use the correct certificate and to report the
expected revocation status for that certificate (see
[Mock OCSP Responder Testing Suite](#mock-ocsp-responder-testing-suite) for configuration details) and that a `mongod`
is running with the correct certificate chain. The mock OCSP responder MUST BE started before the `mongod` as the
`mongod` expects that a responder will be available upon startup. Again, each test MUST BE its own Evergreen task in
order to minimize the impact of user-level and application-level OCSP caching

To assert whether a test passes or fails, drivers SHOULD create a MongoClient with the options specified under "URI
options", connect to a server and attempt to issue a ping command. The success or failure (due to a TLS error) of the
ping command should correlate with the expected test result.

Drivers may wish to use a smaller value for `serverSelectionTimeoutMS` to speed up tests (otherwise server selection
will spin for the entire duration even after a driver encounters a TLS error early).

### Testing on Linux

Drivers MUST test on Linux platforms that have server support for OCSP stapling.

- [SERVER-51364](https://jira.mongodb.org/browse/SERVER-51364) disables OCSP stapling on the server for Ubuntu 18.04.
- [SERVER-56848](https://jira.mongodb.org/browse/SERVER-56848) is a known bug with Go clients and versions of RHEL 8
    before 8.3.

Consider using RHEL 7.0 or Ubuntu 20.04 as alternative platforms.

### Testing on Windows and macOS

Until [SPEC-1589](http://jira.mongodb.org/browse/SPEC-1589) and [SPEC-1645](https://jira.mongodb.org/browse/SPEC-1645)
are resolved, drivers can only test with ECDSA certificates on Linux and thus, on Windows and macOS, drivers can only
test with RSA certificates. Therefore, when testing on Windows and macOS, each column in the test matrix that utilizes
an OCSP responder represents only two tests:

1. A test with RSA certificates and an OCSP responder that uses the issuing CA's certificate
2. A test with RSA certificates and an OCSP responder that uses a delegate certificate

Additionally, because the Windows and macOS `mongod` do not support stapling when a client connects, the following sets
of tests will be identical even if a driver supports stapled OCSP: {Test 1, Test 3} and {Test 2, Test 4}. Therefore,
when testing on Windows and macOS, a driver MAY skip Test 1 and Test 2 if desired. A driver MAY also simply choose to
run all the tests in the table, irrespective of OS, in order to simplify the testing procedure.

## Changelog

**2024-08-20**: Migrated from reStructuredText to Markdown.

**2021-11-08**: Clarify that not all Linux platforms support server stapling.

**2020-07-01**: Clarify that drivers that do not enable OCSP by default MUST enable OCSP for the tests.

**2020-03-20**: Clarify that the mock OCSP responder must be started before the mongod.

**2020-03-11**: Reduce and clarify Windows testing requirements.

**2020-03-05**: Add tests for tlsDisableCertificateRevocationCheck to URI Options tests. Move/add OCSP URI options
default tests to separate file.

**2021-02-27**: Add delegate responders and ECDSA certificate testing.

**2020-02-26**: Add additional URI Options Tests.

**2020-01-16**: Initial commit.
