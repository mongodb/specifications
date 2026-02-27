# Atlas Secure Frontend Processor (SFP) Testing

- Status: Accepted
- Minimum Server Version: 7.0

______________________________________________________________________

## Abstract

This specification defines the tests that drivers MUST run to verify connectivity and authentication through an Atlas
Secure Frontend Processor (SFP). The SFP is a proxy that sits in front of Atlas clusters to provide additional security
capabilities.

## META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

### Terms

#### SFP

Secure Frontend Processor - a proxy service that sits in front of Atlas clusters, providing TLS termination,
authentication forwarding, and additional security features.

### Test Environment

SFP clusters are **preconfigured** and do not require provisioning or teardown as part of the test run. Drivers will be
provided with connection URIs and credentials via environment variables.

The SFP proxy is fully transparent to drivers - all standard MongoDB operations should work exactly as they would
against a normal Atlas cluster.

### Required Environment Variables

The following environment variables will be available to run the tests:

| Variable | Description |
|----------|-------------|
| `SFP_ATLAS_URI` | MongoDB connection URI for the SFP-proxied cluster |
| `SFP_ATLAS_USER` | Username for SCRAM authentication |
| `SFP_ATLAS_PASSWORD` | Password for SCRAM authentication |

For X.509 authentication tests, the following additional variables are required:

| Variable | Description |
|----------|-------------|
| `SFP_ATLAS_X509_URI` | MongoDB connection URI for X.509 authentication |
| `SFP_ATLAS_X509_CERT` | Path to client certificate (PEM format) |

### Test Isolation and Cleanup

To prevent conflicts between concurrent test runs and avoid unbounded collection growth:

1. Drivers MUST use a unique collection name for each test run, e.g., `sfp_test_<random>` where `<random>` is a UUID
   or timestamp
2. Drivers MUST drop the test collection after all tests complete, regardless of test success or failure

## Required Tests

Drivers MUST implement and run the following tests against SFP-proxied clusters.

### Common Assertions

The following assertions are used across multiple tests:

#### Assertion: Ping

1. Execute a `ping` command against the `admin` database
2. Assert that the command succeeds with `ok: 1`

#### Assertion: Connection Status

1. Execute a `connectionStatus` command against the `admin` database
2. Assert that the command succeeds with `ok: 1`
3. If authenticated, assert that `authInfo.authenticatedUsers` contains at least one user

#### Assertion: CRUD Operations

1. Insert a document into a test collection and assert the insert succeeds
2. Query the collection using `find` and assert the inserted document is returned

### Unauthenticated Tests

Create a `MongoClient` configured with `SFP_ATLAS_URI` but without credentials. Run the following assertions:

- Ping
- Connection Status (assert `authenticatedUsers` is empty)

### Authenticated Tests

#### SCRAM-SHA-256

Create a `MongoClient` with the connection string and SCRAM-SHA-256 credentials from environment variables. Run the
following assertions:

- Ping
- Connection Status
- CRUD Operations

#### X.509

Create a `MongoClient` with the connection string and X.509 authentication using the client certificate. Run the
following assertions:

- Ping
- Connection Status
- CRUD Operations

## Changelog

- 2025-02-27: Initial version

