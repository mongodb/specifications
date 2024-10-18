# Unified Test Format

- Status: Accepted
- Minimum Server Version: N/A
- Current Schema Version: 1.19.0

______________________________________________________________________

## Abstract

This project defines a unified schema for YAML and JSON specification tests, which run operations against a MongoDB
deployment. By conforming various spec tests to a single schema, drivers can implement a single test runner to execute
acceptance tests for multiple specifications, thereby reducing maintenance of existing specs and implementation time for
new specifications.

## META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

This document tends to use "SHOULD" more frequently than other specifications, but mainly in the context of providing
guidance on writing test files. This is discussed in more detail in [Design Rationale](#design-rationale).

## Goals

This test format can be used to define tests for the following specifications:

- [Change Streams](../change-streams/change-streams.md)
- [Command Logging and Monitoring](../command-logging-and-monitoring/command-logging-and-monitoring.md)
- [CRUD](../crud/crud.md)
- [GridFS](../gridfs/gridfs-spec.md)
- [Retryable Reads](../retryable-reads/retryable-reads.md)
- [Retryable Writes](../retryable-writes/retryable-writes.md)
- [Sessions](../sessions/driver-sessions.md)
- [Transactions](../transactions/transactions.md)
- [Convenient API for Transactions](../transactions-convenient-api/transactions-convenient-api.md)
- [Server Discovery and Monitoring](../server-discovery-and-monitoring/server-discovery-and-monitoring.md)

This is not an exhaustive list. Specifications that are known to not be supported by this format may be discussed under
[Future Work](#future-work).

## Specification

### Terms

**Entity** Any object or value that is indexed by a unique name and stored in the [Entity Map](#entity-map). This will
typically be a driver object (e.g. client, session) defined in [createEntities](#createentities) but may also be a
[saved operation result](#operation_saveResultAsEntity). A exhaustive list of supported types is presented in
[Supported Entity Types](#supported-entity-types). Entities are referenced by name throughout the test file (e.g.
[Entity Test Operations](#entity-test-operations)).

**Internal MongoClient** A MongoClient created specifically for use with internal test operations, such as inserting
collection data before a test, performing special assertions during a test, or asserting collection data after a test.

**Iterable** This term is used by various specifications as the return type for operations that return a sequence of
items, which may be iterated. For example, the CRUD spec uses this as the return value for `find` and permit API
flexibility rather than stipulate that a cursor object be returned directly.

### Server Compatibility

The unified test format is intended to only run against enterprise servers. Additionally, many tests make use of
[Server Fail Points](#server-fail-points), so servers MUST be launched with the `enableTestCommands` parameter enabled.

### Schema Version

This specification and the [Test Format](#test-format) follow [semantic versioning](https://semver.org/). The version is
primarily used to validate test files with a [JSON schema](https://json-schema.org/) and also allow test runners to
determine whether a particular test file is supported.

New tests files SHOULD always be written using the latest major version of this specification; however, test files
SHOULD be conservative in the minor version they specify (as noted in [schemaVersion](#schemaVersion)).

#### JSON Schema Validation

Each major or minor version that changes the [Test Format](#test-format) SHALL have a corresponding JSON schema. When a
new schema file is introduced, any existing schema files MUST remain in place since they may be needed for validation.
For example: if an additive change is made to version 1.0 of the spec, the `schema-1.0.json` file will be copied to
`schema-1.1.json` and modified accordingly. A new or existing test file using [schemaVersion](#schemaVersion) "1.0"
would then be expected to validate against both schema files. Schema version bumps MUST be noted in the
[Changelog](#changelog).

A particular minor version MUST be capable of validating any and all test files in that major version series up to and
including the minor version. For example, `schema-2.1.json` should validate test files with
[schemaVersion](#schemaVersion) "2.0" and "2.1", but would not be expected to validate files specifying "1.0", "2.2", or
"3.0".

The JSON schema MUST remain consistent with the [Test Format](#test-format) section. If and when a new major version is
introduced, the [Breaking Changes](#breaking-changes) section MUST be updated.

[Ajv](https://ajv.js.org/) MAY be used to programmatically validate both YAML and JSON files using the JSON schema. The
JSON schema MUST NOT use syntax that is unsupported by this tool, which bears mentioning because there are multiple
versions of the [JSON schema specification](https://json-schema.org/specification.html).

#### Test Runner Support

Each test file defines a [schemaVersion](#schemaVersion), which test runners will use to determine compatibility (i.e.
whether and how the test file will be interpreted). Test files are considered compatible with a test runner if their
[schemaVersion](#schemaVersion) is less than or equal to a supported version in the test runner, given the same major
version component. For example:

- A test runner supporting version 1.5.1 could execute test files with versions 1.0 and 1.5 but *not* 1.6 and 2.0.
- A test runner supporting version 2.1 could execute test files with versions 2.0 and 2.1 but *not* 1.0 and 1.5.
- A test runner supporting *both* versions 1.5.1 and 2.0 could execute test files with versions 1.4, 1.5, and 2.0, but
    *not* 1.6, 2.1, or 3.0.
- A test runner supporting version 2.0.1 could execute test files with versions 2.0 and 2.0.1 but *not* 2.0.2 or 2.1.
    This example is provided for completeness, but test files SHOULD NOT need to refer to patch versions (as previously
    mentioned).

Test runners MUST NOT process incompatible files and MUST raise an error if they encounter an incompatible file (as
discussed in [Executing a Test File](#executing-a-test-file)). Test runners MAY support multiple schema versions (as
demonstrated in the example above).

#### Impact of Spec Changes on Schema Version

Backwards-breaking changes SHALL warrant a new major version. These changes include, but are not limited to:

- Subtractive changes, such as removing a field, operation, or type of supported entity or event
- Changing an existing field from optional to required
- Introducing a new, required field in the test format
- Significant changes to test file execution (not BC)

Backwards-compatible changes SHALL warrant a new minor version. These changes include, but are not limited to:

- Additive changes, such as a introducing a new [Special Test Operations](#special-test-operations) or type of supported
    entity or event
- Changing an existing field from required to optional
- Introducing a new, optional field in the test format
- Minor changes to test file execution (BC)

Small fixes and internal spec changes (e.g. grammar, adding clarifying text to the spec) MAY warrant a new patch
version; however, patch versions SHOULD NOT alter the structure of the test format and thus SHOULD NOT be relevant to
test files (as noted in [schemaVersion](#schemaVersion)).

### Entity Map

The entity map indexes arbitrary objects and values by unique names, so that they can be referenced from test constructs
(e.g. [operation.object](#operation_object)). To ensure each test is executed in isolation, test runners MUST NOT share
entity maps between tests. Most entities will be driver objects created by the [createEntities](#createentities)
directive during test setup, but the entity map may also be modified during test execution via the
[operation.saveResultAsEntity](#operation_saveResultAsEntity) directive.

Test runners MAY choose to implement the entity map in a fashion most suited to their language, but implementations MUST
enforce both uniqueness of entity names and referential integrity when fetching an entity. Test runners MUST raise an
error if an attempt is made to store an entity with a name that already exists in the map and MUST raise an error if an
entity is not found for a name or is found but has an unexpected type.

Test runners MUST provide a mechanism to retrieve entities from the entity map prior to the clearing of the entity map,
as discussed in [Executing a Test](#executing-a-test). There MUST be a way to retrieve an entity by its name (for
example, to support retrieving the iteration count stored by the `storeIterationsAsEntity` option).

Test runners MAY restrict access to driver objects (e.g. MongoClient, ChangeStream) and only allow access to BSON types
(see: [Supported Entity Types](#supported-entity-types)). This restriction may be necessary if the test runner needs to
ensure driver objects in its entity map are properly freed/destroyed between tests.

The entity map MUST be implemented in a way that allows for safe concurrent access, since a test may include multiple
thread entities that all need to access the map concurrently. See [entity_thread](#entity_thread) for more information
on test runner threads.

Consider the following examples:

```
# Error due to a duplicate name (client0 was already defined)
createEntities:
  - client: { id: client0 }
  - client: { id: client0 }

# Error due to a missing entity (client1 is undefined)
createEntities:
  - client: { id: client0 }
  - session: { id: session0, client: client1 }

# Error due to an unexpected entity type (session instead of client)
createEntities:
  - client: { id: client0 }
  - session: { id: session0, client: client0 }
  - session: { id: session1, client: session0 }
```

#### Supported Entity Types

Test runners MUST support the following types of entities:

- MongoClient. See [entity_client](#entity_client) and [Client Operations](#client-operations).
- ClientEncryption. See [entity_clientEncryption](#entity_clientEncryption) and
    [ClientEncryption Operations](#clientencryption-operations).
- Database. See [entity_database](#entity_database) and [Database Operations](#database-operations).
- Collection. See [entity_collection](#entity_collection) and [Collection Operations](#collection-operations)
- ClientSession. See [entity_session](#entity_session) and [Session Operations](#session-operations).
- GridFS Bucket. See [entity_bucket](#entity_bucket) and [Bucket Operations](#bucket-operations).

<span id="entity_changestream"></span>

- ChangeStream. Change stream entities are special in that they are not defined in [createEntities](#createentities) but
    are instead created by using [operation.saveResultAsEntity](#operation_saveResultAsEntity) with a
    [client_createChangeStream](#client_createChangeStream),
    [database_createChangeStream](#database_createChangeStream), or
    [collection_createChangeStream](#collection_createChangeStream) operation.

    Test files SHOULD NOT use a `watch` operation to create a change stream, as the implementation of that method may vary
    among drivers. For example, some implementations of `watch` immediately execute `aggregate` and construct the
    server-side cursor, while others may defer `aggregate` until the change stream object is iterated.

    See [Cursor Operations](#cursor-operations) for a list of operations.

- FindCursor. These entities are not defined in [createEntities](#createentities) but are instead created by using
    [operation.saveResultAsEntity](#operation_saveResultAsEntity) with a
    [collection_createFindCursor](#collection_createFindCursor) operation.

    See [Cursor Operations](#cursor-operations) for a list of operations.

- CommandCursor. These entities are not defined in [createEntities](#createentities) but are instead created by using
    [operation.saveResultAsEntity](#operation_saveResultAsEntity) with a [createCommandCursor](#createcommandcursor)
    operation.

    See [Cursor Operations](#cursor-operations) for a list of operations.

- Event list. See [storeEventsAsEntities](#entity_client_storeEventsAsEntities). The event list MUST store BSON
    documents. The type of the list itself is not prescribed by this specification. Test runner MAY use a BSON array or
    a thread-safe list data structure to implement the event list.

- All known BSON types and/or equivalent language types for the target driver. For the present version of the spec, the
    following BSON types are known: 0x01-0x13, 0x7F, 0xFF.

    Tests SHOULD NOT utilize deprecated types (e.g. 0x0E: Symbol), since they may not be supported by all drivers and
    could yield runtime errors (e.g. while loading a test file with an Extended JSON parser).

<span id="entity_thread"></span>

- Test runner thread. An entity representing a "thread" that can be used to concurrently execute operations. Thread
    entities MUST be able to run concurrently with the main test runner thread and other thread entities, but they do
    not have to be implemented as actual OS threads (e.g. they can be goroutines or async tasks). See
    [entity_thread_object](#entity_thread_object) for more information on how they are created.

<span id="entity_topologydescription"></span>

- TopologyDescription. An entity representing a client's
    [TopologyDescription](../server-discovery-and-monitoring/server-discovery-and-monitoring.md#topologydescription) at
    a certain point in time. These entities are not defined in [createEntities](#createentities) but are instead created
    via [recordTopologyDescription](#recordtopologydescription) test runner operations.

This is an exhaustive list of supported types for the entity map. Test runners MUST raise an error if an attempt is made
to store an unsupported type in the entity map.

Adding new entity types (including known BSON types) to this list will require a minor version bump to the spec and
schema version. Removing entity types will require a major version bump. See
[Impact of Spec Changes on Schema Version](#impact-of-spec-changes-on-schema-version) for more information.

### Test Format

Each specification test file can define one or more tests, which inherit some top-level configuration (e.g. namespace,
initial data). YAML and JSON test files are parsed as an object by the test runner. This section defines the top-level
keys for that object and links to various sub-sections for definitions of nested structures (e.g. individual
[test](#test), [operation](#operation)).

Although test runners are free to process YAML or JSON files, YAML is the canonical format for writing tests. YAML files
may be converted to JSON using a tool such as [js-yaml](https://github.com/nodeca/js-yaml) .

#### Top-level Fields

The top-level fields of a test file are as follows:

- `description`: Required string. The name of the test file.

    This SHOULD describe the common purpose of tests in this file and MAY refer to the filename (e.g. "updateOne-hint").

<span id="schemaVersion"></span>

- `schemaVersion`: Required string. Version of this specification with which the test file complies.

    Test files SHOULD be conservative when specifying a schema version. For example, if the latest schema version is 1.1
    but the test file complies with schema version 1.0, the test file should specify 1.0.

    Test runners will use this to determine compatibility (i.e. whether and how the test file will be interpreted). The
    format of this string is defined in [Version String](#version-string); however, test files SHOULD NOT need to refer
    to specific patch versions since patch-level changes SHOULD NOT alter the structure of the test format (as
    previously noted in [Schema Version](#schema-version)).

<span id="runOnRequirements"></span>

- `runOnRequirements`: Optional array of one or more [runOnRequirement](#runonrequirement) objects. List of server
    version and/or topology requirements for which the tests in this file can be run. If no requirements are met, the
    test runner MUST skip this test file.

<span id="createEntities"></span>

- `createEntities`: Optional array of one or more [entity](#entity) objects. List of entities (e.g. client, collection,
    session objects) that SHALL be created before each test case is executed.

    Test files SHOULD define entities in dependency order, such that all referenced entities (e.g. client) are defined
    before any of their dependent entities (e.g. database, session).

<span id="initialData"></span>

- `initialData`: Optional array of one or more [collectionData](#collectiondata) objects. Data that will exist in
    collections before each test case is executed.

<span id="tests"></span>

- `tests`: Required array of one or more [test](#test) objects. List of test cases to be executed independently of each
    other.
- `_yamlAnchors`: Optional object containing arbitrary data. This is only used to define anchors within the YAML files
    and MUST NOT be used by test runners.

#### runOnRequirement

A combination of server version and/or topology requirements for running the test(s).

The format of server version strings is defined in [Version String](#version-string). When comparing server version
strings, each component SHALL be compared numerically. For example, "4.0.10" is greater than "4.0.9" and "3.6" and less
than "4.2.0".

The structure of this object is as follows:

- `minServerVersion`: Optional string. The minimum server version (inclusive) required to successfully run the tests. If
    this field is omitted, there is no lower bound on the required server version. The format of this string is defined
    in [Version String](#version-string).

- `maxServerVersion`: Optional string. The maximum server version (inclusive) against which the tests can be run
    successfully. If this field is omitted, there is no upper bound on the required server version. The format of this
    string is defined in [Version String](#version-string).

- `topologies`: Optional array of one or more strings. Server topologies against which the tests can be run
    successfully. Valid topologies are "single", "replicaset", "sharded", "load-balanced", and "sharded-replicaset"
    (i.e. sharded cluster backed by replica sets). If this field is omitted, there is no topology requirement for the
    test.

    When matching a "sharded-replicaset" topology, test runners MUST ensure that all shards are backed by a replica set.
    The process for doing so is described in
    [Determining if a Sharded Cluster Uses Replica Sets](#determining-if-a-sharded-cluster-uses-replica-sets). When
    matching a "sharded" topology, test runners MUST accept any type of sharded cluster (i.e. "sharded" implies
    "sharded-replicaset", but not vice versa).

    The "sharded-replicaset" topology type is deprecated. MongoDB 3.6+ requires that all shard servers be replica sets.
    Therefore, tests SHOULD use "sharded" instead of "sharded-replicaset" when targeting 3.6+ server versions in order
    to avoid unnecessary overhead.

    Note: load balancers were introduced in MongoDB 5.0. Therefore, any sharded cluster behind a load balancer implicitly
    uses replica sets for its shards.

- `serverless`: Optional string. Whether or not the test should be run on Atlas Serverless instances. Valid values are
    "require", "forbid", and "allow". If "require", the test MUST only be run on Atlas Serverless instances. If
    "forbid", the test MUST NOT be run on Atlas Serverless instances. If omitted or "allow", this option has no effect.

    The test runner MUST be informed whether or not Atlas Serverless is being used in order to determine if this
    requirement is met (e.g. through an environment variable or configuration option).

    Note: the Atlas Serverless proxy imitates mongos, so the test runner is not capable of determining if Atlas Serverless
    is in use by issuing commands such as `buildInfo` or `hello`. Furthermore, connections to Atlas Serverless use a
    load balancer, so the topology will appear as "load-balanced".

- `serverParameters`: Optional object of server parameters to check against. To check server parameters, drivers send a
    `{ getParameter: 1, <parameter>: 1 }` command to the server using an internal MongoClient. Drivers MAY also choose
    to send a `{ getParameter: '*' }` command and fetch all parameters at once. The result SHOULD be cached to avoid
    repeated calls to fetch the same parameter. Test runners MUST apply the rules specified in
    [Flexible Numeric Comparisons](#flexible-numeric-comparisons) when comparing values. If a server does not support a
    parameter, test runners MUST treat the comparison as not equal and skip the test. This includes errors that occur
    when fetching a single parameter using `getParameter`.

<span id="runOnRequirement_auth"></span>

- `auth`: Optional boolean. If true, the tests MUST only run if authentication is enabled. If false, tests MUST NOT run
    if authentication is enabled. If this field is omitted, there is no authentication requirement.

- `authMechanism`: Optional string. Specifies an authentication mechanism that the server needs to support for the test.
    If set, tests MUST only run if the given string matches (case-insensitive) one of the strings in the
    [authenticationMechanisms](https://www.mongodb.com/docs/manual/reference/parameters/#mongodb-parameter-param.authenticationMechanisms)
    server parameter. If this field is omitted, there is no authentication mechanism requirement.

- `csfle`: Optional boolean. If true, the tests MUST only run if the driver and server support Client-Side Field Level
    Encryption. CSFLE is supported when all of the following are true:

    - Server version is 4.2.0 or higher
    - Driver has libmongocrypt enabled
    - At least one of [crypt_shared](../client-side-encryption/client-side-encryption.md#crypt_shared) and/or
        [mongocryptd](../client-side-encryption/client-side-encryption.md#mongocryptd) is available

    If false, tests MUST NOT run if CSFLE is supported. If this field is omitted, there is no CSFLE requirement.

Test runners MAY evaluate these conditions in any order. For example, it may be more efficient to evaluate `serverless`
or `auth` before communicating with a server to check its version.

#### entity

An entity (e.g. client, collection, session object) that will be created in the [Entity Map](#entity-map) before each
test is executed.

This object MUST contain **exactly one** top-level key that identifies the entity type and maps to a nested object,
which specifies a unique name for the entity (`id` key) and any other parameters necessary for its construction. Tests
SHOULD use sequential names based on the entity type (e.g. "session0", "session1").

When defining an entity object in YAML, a [node anchor](https://yaml.org/spec/1.2/spec.html#id2785586) SHOULD be created
on the entity's `id` key. This anchor will allow the unique name to be referenced with an
[alias node](https://yaml.org/spec/1.2/spec.html#id2786196) later in the file (e.g. from another entity or
[operation](#operation) object) and also leverage YAML's parser for reference validation.

The structure of this object is as follows:

<span id="entity_client"></span>

- `client`: Optional object. Defines a MongoClient object. In addition to the configuration defined below, test runners
    for drivers that implement connection pooling MUST track the number of connections checked out at any given time for
    the constructed MongoClient. This can be done using a single counter and
    [CMAP events](../connection-monitoring-and-pooling/connection-monitoring-and-pooling.md#events). Each
    `ConnectionCheckedOutEvent` should increment the counter and each `ConnectionCheckedInEvent` should decrement it.

    The structure of this object is as follows:

    - `id`: Required string. Unique name for this entity. The YAML file SHOULD define a
        [node anchor](https://yaml.org/spec/1.2/spec.html#id2785586) for this field (e.g. `id: &client0 client0`).

    - `uriOptions`: Optional object. Additional URI options to apply to the test suite's connection string that is used to
        create this client. Any keys in this object MUST override conflicting keys in the connection string.

        Documentation for supported options may be found in the [URI Options](../uri-options/uri-options.md) spec, with one
        notable exception: if `readPreferenceTags` is specified in this object, the key will map to an array of strings,
        each representing a tag set, since it is not feasible to define multiple `readPreferenceTags` keys in the object.

        Note also that when specifying `directConnection` as true, the connection string used to instantiate a client MUST
        only have a single seed and MUST NOT specify the `replicaSet` option. See the
        [URI Options spec](../uri-options/uri-options.md#directconnection-uri-option-with-multiple-seeds-or-srv-uri) for
        more information.

        Any field in `uriOptions` may be a [$$placeholder](#placeholder) document and the test runner MUST support replacing
        the placeholder document with values loaded from the test environment. For example:

        ```
        uriOptions:
          authMechanism: "MONGODB-OIDC"
          authMechanismProperties:
            ENVIRONMENT: { $$placeholder: 1 }
        ```

    <span id="entity_client_useMultipleMongoses"></span>

    - `useMultipleMongoses`: Optional boolean. If true and the topology is a sharded cluster, the test runner MUST assert
        that this MongoClient connects to multiple mongos hosts (e.g. by inspecting the connection string). If false and
        the topology is a sharded cluster, the test runner MUST ensure that this MongoClient connects to only a single
        mongos host (e.g. by modifying the connection string).

        If this option is not specified and the topology is a sharded cluster, the test runner MUST NOT enforce any limit on
        the number of mongos hosts in the connection string and any tests using this client SHOULD NOT depend on a
        particular number of mongos hosts.

        This option SHOULD be set to true in test files if the resulting entity is used to conduct transactions against a
        sharded cluster. This is advised because connecting to multiple mongos servers is necessary to test session
        pinning.

        If the topology type is `LoadBalanced` and Atlas Serverless is not being used, the test runner MUST use one of the
        two load balancer URIs described in [Initializing the Test Runner](#initializing-the-test-runner) to configure the
        MongoClient. If `useMultipleMongoses` is true or unset, the test runner MUST use the URI of the load balancer
        fronting multiple servers. Otherwise, the test runner MUST use the URI of the load balancer fronting a single
        server.

        If the topology type is `LoadBalanced` and Atlas Serverless is being used, this option has no effect. This is
        because provisioning an Atlas Serverless instance yields a single URI (i.e. a load balancer fronting a single
        Atlas Serverless proxy).

        This option has no effect for topologies that are not sharded or load balanced.

    <span id="entity_client_observeEvents"></span>

    - `observeEvents`: Optional array of one or more strings. Types of events that can be observed for this client.
        Unspecified event types MUST be ignored by this client's event listeners and SHOULD NOT be included in
        [test.expectEvents](#test_expectEvents) for this client.

        Supported types correspond to the top-level keys (strings) documented in [expectedEvent](#expectedevent) and are as
        follows:

        - [commandStartedEvent](#expectedEvent_commandStartedEvent)
        - [commandSucceededEvent](#expectedEvent_commandSucceededEvent)
        - [commandFailedEvent](#expectedEvent_commandFailedEvent)
        - [poolCreatedEvent](#expectedEvent_poolCreatedEvent)
        - [poolReadyEvent](#expectedEvent_poolReadyEvent)
        - [poolClearedEvent](#expectedEvent_poolClearedEvent)
        - [poolClosedEvent](#expectedEvent_poolClosedEvent)
        - [connectionCreatedEvent](#expectedEvent_connectionCreatedEvent)
        - [connectionReadyEvent](#expectedEvent_connectionReadyEvent)
        - [connectionClosedEvent](#expectedEvent_connectionClosedEvent)
        - [connectionCheckOutStartedEvent](#expectedEvent_connectionCheckOutStartedEvent)
        - [connectionCheckOutFailedEvent](#expectedEvent_connectionCheckOutFailedEvent)
        - [connectionCheckedOutEvent](#expectedEvent_connectionCheckedOutEvent)
        - [connectionCheckedInEvent](#expectedEvent_connectionCheckedInEvent)
        - [serverDescriptionChangedEvent](#expectedEvent_serverDescriptionChangedEvent)
        - [serverHeartbeatStartedEvent](#expectedEvent_serverHeartbeatStartedEvent)
        - [serverHeartbeatSucceededEvent](#expectedEvent_serverHeartbeatSucceededEvent)
        - [serverHeartbeatFailedEvent](#expectedEvent_serverHeartbeatFailedEvent)
        - [topologyDescriptionChangedEvent](#expectedEvent_topologyDescriptionChangedEvent)

    <span id="entity_client_ignoreCommandMonitoringEvents"></span>

    - `ignoreCommandMonitoringEvents`: Optional array of one or more strings. Command names for which the test runner MUST
        ignore any observed command monitoring events. The command(s) will be ignored in addition to `configureFailPoint`
        and any commands containing sensitive information (per the
        [Command Logging and Monitoring](../command-logging-and-monitoring/command-logging-and-monitoring.md#security)
        spec) unless `observeSensitiveCommands` is true.

        Test files SHOULD NOT use this option unless one or more command monitoring events are specified in
        [observeEvents](#entity_client_observeEvents).

    <span id="entity_client_observeSensitiveCommands"></span>

    - `observeSensitiveCommands`: Optional boolean. If true, events associated with sensitive commands (per the
        [Command Logging and Monitoring](../command-logging-and-monitoring/command-logging-and-monitoring.md#security)
        spec) will be observed for this client. Note that the command and replies for such events will already have been
        redacted by the driver. If false or not specified, events for commands containing sensitive information MUST be
        ignored. Authentication SHOULD be disabled when this property is true, i.e. [auth](#runOnRequirement_auth) should
        be false for each `runOnRequirement`. See
        [rationale_observeSensitiveCommands](#rationale_observeSensitiveCommands).

    <span id="entity_client_storeEventsAsEntities"></span>

    - `storeEventsAsEntities`: Optional array of one or more [storeEventsAsEntity](#storeeventsasentity) objects. Each
        object denotes an entity name and one or more events to be collected and stored in that entity. See
        [storeEventsAsEntity](#storeeventsasentity) for implementation details.

        Note: the implementation of `storeEventsAsEntities` is wholly independent from `observeEvents` and
        `ignoreCommandMonitoringEvents`.

        Example option value:

        ```
        storeEventsAsEntities:
          - id: client0_events
            events: [PoolCreatedEvent, ConnectionCreatedEvent, CommandStartedEvent]
        ```

    <span id="entity_client_observeLogMessages"></span>

    - `observeLogMessages`: Optional object where the key names are log [components](../logging/logging.md#components) and
        the values are minimum [log severity levels](../logging/logging.md#log-severity-levels) indicating which
        components to collect log messages for and what the minimum severity level of collected messages should be.
        Messages for unspecified components and/or with lower severity levels than those specified MUST be ignored by this
        client's log collector(s) and SHOULD NOT be included in [test.expectLogMessages](#test_expectLogMessages) for this
        client.
    - `serverApi`: Optional [serverApi](#serverapi) object.

<span id="entity_clientEncryption"></span>

- `clientEncryption`: Optional object. Defines a ClientEncryption object.

    The structure of this object is as follows:

    - `id`: Required string. Unique name for this entity. The YAML file SHOULD define a
        [node anchor](https://yaml.org/spec/1.2/spec.html#id2785586) for this field (e.g.
        `id: &clientEncryption0 clientEncryption0`).

    - `clientEncryptionOpts`: Required document. A value corresponding to a
        [ClientEncryptionOpts](../client-side-encryption/client-side-encryption.md#clientencryption).

        Note: the `tlsOptions` document is intentionally omitted from the test format. However, drivers MAY internally
        configure TLS options as needed to satisfy the requirements of configured KMS providers.

        The structure of this document is as follows:

        - `keyVaultClient`: Required string. Client entity from which this ClientEncryption will be created. The YAML file
            SHOULD use an [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for a client entity's `id` field (e.g.
            `client: *client0`).

        - `keyVaultNamespace`: Required string. The database and collection to use as the key vault collection for this
            clientEncryption. The namespace takes the form `database.collection` (e.g.
            `keyVaultNamespace: keyvault.datakeys`).

        - `kmsProviders`: Required document. Drivers MUST NOT configure a KMS provider if it is not given. This is to permit
            testing conditions where a required KMS provider is not configured. If a KMS provider is given as an empty
            document (e.g. `kmsProviders: { aws: {} }`), drivers MUST configure the KMS provider without credentials to
            permit testing conditions where KMS credentials are needed. If a KMS credentials field has a placeholder value
            (e.g. `kmsProviders: { aws: { accessKeyId: { $$placeholder: 1 }, secretAccessKey: { $$placeholder: 1 } } }`),
            drivers MUST replace the field with credentials that satisfy the operations required by the unified test files.
            Drivers MAY load the credentials from the environment or a configuration file as needed to satisfy the
            requirements of the given KMS provider and tests. If a KMS credentials field is not given (e.g. the required
            field `secretAccessKey` is omitted in: `kmsProviders: { aws: { accessKeyId: { $$placeholder: 1 } }`), drivers
            MUST NOT include the field during KMS configuration. This is to permit testing conditions where required KMS
            credentials fields are not provided. Otherwise, drivers MUST configure the KMS provider with the explicit value
            of KMS credentials field given in the test file (e.g.
            `kmsProviders: { aws: { accessKeyId: abc, secretAccessKey: def } }`). This is to permit testing conditions where
            invalid KMS credentials are provided.

            Tests may also reference named KMS providers. KMS providers with the name `name1` are expected to be configured
            exactly as the unnamed KMS providers. The `aws:name2` KMS provider and `aws:name1` KMS providers deliberately
            use separate AWS accounts that do not have permission to the other's keys.

            See the [Client-Side Encryption test README](../client-side-encryption/tests/README.md#credentials) for
            instructions to obtain test credentials.

<span id="entity_database"></span>

- `database`: Optional object. Defines a Database object.

    The structure of this object is as follows:

    - `id`: Required string. Unique name for this entity. The YAML file SHOULD define a
        [node anchor](https://yaml.org/spec/1.2/spec.html#id2785586) for this field (e.g. `id: &database0 database0`).
    - `client`: Required string. Client entity from which this database will be created. The YAML file SHOULD use an
        [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for a client entity's `id` field (e.g.
        `client: *client0`).
    - `databaseName`: Required string. Database name. The YAML file SHOULD define a
        [node anchor](https://yaml.org/spec/1.2/spec.html#id2785586) for this field (e.g.
        `databaseName: &database0Name foo`).
    - `databaseOptions`: Optional [collectionOrDatabaseOptions](#collectionordatabaseoptions) object.

<span id="entity_collection"></span>

- `collection`: Optional object. Defines a Collection object.

    The structure of this object is as follows:

    - `id`: Required string. Unique name for this entity. The YAML file SHOULD define a
        [node anchor](https://yaml.org/spec/1.2/spec.html#id2785586) for this field (e.g. `id: &collection0 collection0`).
    - `database`: Required string. Database entity from which this collection will be created. The YAML file SHOULD use an
        [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for a database entity's `id` field (e.g.
        `database: *database0`).
    - `collectionName`: Required string. Collection name. The YAML file SHOULD define a
        [node anchor](https://yaml.org/spec/1.2/spec.html#id2785586) for this field (e.g.
        `collectionName: &collection0Name foo`).
    - `collectionOptions`: Optional [collectionOrDatabaseOptions](#collectionordatabaseoptions) object.

<span id="entity_session"></span>

- `session`: Optional object. Defines an explicit ClientSession object.

    The structure of this object is as follows:

    - `id`: Required string. Unique name for this entity. The YAML file SHOULD define a
        [node anchor](https://yaml.org/spec/1.2/spec.html#id2785586) for this field (e.g. `id: &session0 session0`).

    - `client`: Required string. Client entity from which this session will be created. The YAML file SHOULD use an
        [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for a client entity's `id` field (e.g.
        `client: *client0`).

    - `sessionOptions`: Optional object. Map of parameters to pass to
        [MongoClient.startSession](../sessions/driver-sessions.md#startsession) when creating the session. Supported
        options are defined in the following specifications:

        - [Causal Consistency](../causal-consistency/causal-consistency.md#sessionoptions-changes)
        - [Snapshot Reads](../sessions/snapshot-sessions.md#sessionoptions-changes)
        - [Transactions](../transactions/transactions.md#sessionoptions-changes)
        - [Client Side Operations Timeout](../client-side-operations-timeout/client-side-operations-timeout.md#sessions)

        When specifying TransactionOptions for `defaultTransactionOptions`, the transaction options MUST remain nested under
        `defaultTransactionOptions` and MUST NOT be flattened into `sessionOptions`.

<span id="entity_bucket"></span>

- `bucket`: Optional object. Defines a Bucket object, as defined in the [GridFS](../gridfs/gridfs-spec.md) spec.

    The structure of this object is as follows:

    - `id`: Required string. Unique name for this entity. The YAML file SHOULD define a
        [node anchor](https://yaml.org/spec/1.2/spec.html#id2785586) for this field (e.g. `id: &bucket0 bucket0`).
    - `database`: Required string. Database entity from which this bucket will be created. The YAML file SHOULD use an
        [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for a database entity's `id` field (e.g.
        `database: *database0`).
    - `bucketOptions`: Optional object. Additional options used to construct the bucket object. Supported options are
        defined in the [GridFS](../gridfs/gridfs-spec.md#configurable-gridfsbucket-class) specification. The
        `readConcern`, `readPreference`, and `writeConcern` options use the same structure as defined in
        [Common Options](#common-options).

<span id="entity_thread_object"></span>

- `thread`: Optional object. Defines a test runner "thread". Once the "thread" has been created, it should be idle and
    waiting for operations to be dispatched to it later on by [runOnThread](#runonthread) operations.

    The structure of this object is as follows:

    - `id`: Required string. Unique name for this entity. The YAML file SHOULD define a
        [node anchor](https://yaml.org/spec/1.2/spec.html#id2785586) for this field (e.g. `id: &thread0 thread0`).

#### storeEventsAsEntity

A list of one or more events that will be observed on a client and collectively stored within an entity. This object is
used within [storeEventsAsEntities](#entity_client_storeEventsAsEntities).

The structure of this object is as follows:

- `id`: Required string. Unique name for this entity.
- `events`: Required array of one or more strings, which denote the events to be collected. Currently, only the
    following [CMAP](../connection-monitoring-and-pooling/connection-monitoring-and-pooling.md) and
    [command monitoring](../command-logging-and-monitoring/command-logging-and-monitoring.md) events MUST be supported:
    - PoolCreatedEvent
    - PoolReadyEvent
    - PoolClearedEvent
    - PoolClosedEvent
    - ConnectionCreatedEvent
    - ConnectionReadyEvent
    - ConnectionClosedEvent
    - ConnectionCheckOutStartedEvent
    - ConnectionCheckOutFailedEvent
    - ConnectionCheckedOutEvent
    - ConnectionCheckedInEvent
    - CommandStartedEvent
    - CommandSucceededEvent
    - CommandFailedEvent

For the specified entity name, the test runner MUST create the respective entity with a type of "event list", as
described in [Supported Entity Types](#supported-entity-types). If the entity already exists (such as from a previous
[storeEventsAsEntity](#storeeventsasentity) object) the test runner MUST raise an error.

The test runner MUST set up an event subscriber for each event named. The event subscriber MUST serialize the events it
receives into a document, using the documented properties of the event as field names, and append the document to the
list stored in the specified entity. Additionally, the following fields MUST be stored with each event document:

- `name`: The name of the event (e.g. `PoolCreatedEvent`). The name of the event MUST be the name used in the respective
    specification that defines the event in question.
- `observedAt`: The time, as the floating-point number of seconds since the Unix epoch, when the event was observed by
    the test runner.

The test runner MAY omit the `command` field for CommandStartedEvent and `reply` field for CommandSucceededEvent.

If an event field in the driver is of a type that does not directly map to a BSON type (e.g. `Exception` for the
`failure` field of CommandFailedEvent) the test runner MUST convert values of that field to one of the BSON types. For
example, a test runner MAY store the exception's error message string as the `failure` field of CommandFailedEvent.

If the specification defining an event permits deviation in field names, such as `connectionId` field for
CommandStartedEvent, the test runner SHOULD use the field names used in the specification when serializing events to
documents even if the respective field name is different in the driver's event object.

#### serverApi

Declares an API version for a [client entity](#entity_client).

The structure of this object is as follows:

- `version`: Required string. Test runners MUST fail if the given version string is not supported by the driver.

    Note: the format of this string is unrelated to [Version String](#version-string).

- `strict`: Optional boolean.

- `deprecationErrors`: Optional boolean.

See the [Stable API](../versioned-api/versioned-api.md) spec for more details on these fields.

#### collectionData

List of documents corresponding to the contents of a collection. This structure is used by both
[initialData](#initialData) and [test.outcome](#test_outcome), which insert and read documents, respectively.

The structure of this object is as follows:

- `collectionName`: Required string. See [commonOptions_collectionName](#commonOptions_collectionName).
- `databaseName`: Required string. See [commonOptions_databaseName](#commonOptions_databaseName).
- `createOptions`: Optional object. When used in [initialData](#initialData), these options MUST be passed to the
    [create](https://docs.mongodb.com/manual/reference/command/create/) command when creating the collection. Test files
    MUST NOT specify `writeConcern` in this options document as that could conflict with the use of the `majority` write
    concern when the collection is created during test execution.
- `documents`: Required array of objects. List of documents corresponding to the contents of the collection. This list
    may be empty.

#### test

Test case consisting of a sequence of operations to be executed.

The structure of this object is as follows:

- `description`: Required string. The name of the test.

    This SHOULD describe the purpose of this test (e.g. "insertOne is retried").

<span id="test_runOnRequirements"></span>

- `runOnRequirements`: Optional array of one or more [runOnRequirement](#runonrequirement) objects. List of server
    version and/or topology requirements for which this test can be run. If specified, these requirements are evaluated
    independently and in addition to any top-level [runOnRequirements](#runOnRequirements). If no requirements in this
    array are met, the test runner MUST skip this test.

    These requirements SHOULD be more restrictive than those specified in the top-level
    [runOnRequirements](#runOnRequirements) (if any) and SHOULD NOT be more permissive. This is advised because both
    sets of requirements MUST be satisfied in order for a test to be executed and more permissive requirements at the
    test-level could be taken out of context on their own.

<span id="test_skipReason"></span>

- `skipReason`: Optional string. If set, the test will be skipped. The string SHOULD explain the reason for skipping the
    test (e.g. JIRA ticket).

<span id="test_operations"></span>

- `operations`: Required array of one or more [operation](#operation) objects. List of operations to be executed for the
    test case.

<span id="test_expectEvents"></span>

- `expectEvents`: Optional array of one or more [expectedEventsForClient](#expectedeventsforclient) objects. For one or
    more clients, a list of events that are expected to be observed in a particular order.

    If a driver only supports configuring event listeners globally (for all clients), the test runner SHOULD associate
    each observed event with a client in order to perform these assertions.

    Tests SHOULD NOT specify multiple [expectedEventsForClient](#expectedeventsforclient) objects for a single client
    entity with the same `eventType` field. For example, a test containing two
    [expectedEventsForClient](#expectedeventsforclient) objects with the `eventType` set to `cmap` for both would either
    be redundant (if the `events` arrays were identical) or likely to fail (if the `events` arrays differed).

<span id="test_expectLogMessages"></span>

- `expectLogMessages`: Optional array of one or more [expectedLogMessagesForClient](#expectedlogmessagesforclient)
    objects. For one or more clients, a list of log messages that are expected to be observed in a particular order.

    If a driver only supports configuring log collectors globally (for all clients), the test runner SHOULD associate each
    observed message with a client in order to perform these assertions. One possible implementation is to add a
    test-only option to MongoClient which enables the client to store its entity name and add the entity name to each
    log message to enable filtering messages by client.

    Tests SHOULD NOT specify multiple [expectedLogMessagesForClient](#expectedlogmessagesforclient) objects for a single
    client entity.

<span id="test_outcome"></span>

- `outcome`: Optional array of one or more [collectionData](#collectiondata) objects. Data that is expected to exist in
    collections after each test case is executed.

    The list of documents herein SHOULD be sorted ascendingly by the `_id` field to allow for deterministic comparisons.
    The procedure for asserting collection contents is discussed in [Executing a Test](#executing-a-test).

#### operation

An operation to be executed as part of the test.

The structure of this object is as follows:

<span id="operation_name"></span>

- `name`: Required string. Name of the operation (e.g. method) to perform on the object.

<span id="operation_object"></span>

- `object`: Required string. Name of the object on which to perform the operation. This SHOULD correspond to either an
    [entity](#entity) name (for [Entity Test Operations](#entity-test-operations)) or "testRunner" (for
    [Special Test Operations](#special-test-operations)). If the object is an entity, The YAML file SHOULD use an
    [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for its `id` field (e.g. `object: *collection0`).

<span id="operation_arguments"></span>

- `arguments`: Optional object. Map of parameter names and values for the operation. The structure of this object will
    vary based on the operation. See [Entity Test Operations](#entity-test-operations) and
    [Special Test Operations](#special-test-operations).

    The `session` parameter is handled specially (see [commonOptions_session](#commonOptions_session)).

<span id="operation_ignoreResultAndError"></span>

- `ignoreResultAndError`: Optional boolean. If true, both the error and result for the operation MUST be ignored.

    This field is mutually exclusive with [expectResult](#operation_expectResult), [expectError](#operation_expectError),
    and [saveResultAsEntity](#operation_saveResultAsEntity).

    This field SHOULD NOT be used for [Special Test Operations](#special-test-operations) (i.e. `object: testRunner`).

<span id="operation_expectError"></span>

- `expectError`: Optional [expectedError](#expectederror) object. One or more assertions for an error expected to be
    raised by the operation.

    This field is mutually exclusive with [expectResult](#operation_expectResult) and
    [saveResultAsEntity](#operation_saveResultAsEntity).

    This field SHOULD NOT be used for [Special Test Operations](#special-test-operations) (i.e. `object: testRunner`).

<span id="operation_expectResult"></span>

- `expectResult`: Optional mixed type. A value corresponding to the expected result of the operation. This field may be
    a scalar value, a single document, or an array of values. Test runners MUST follow the rules in
    [Evaluating Matches](#evaluating-matches) when processing this assertion.

    This field is mutually exclusive with [expectError](#operation_expectError).

    This field SHOULD NOT be used for [Special Test Operations](#special-test-operations) (i.e. `object: testRunner`).

<span id="operation_saveResultAsEntity"></span>

- `saveResultAsEntity`: Optional string. If specified, the actual result returned by the operation (if any) will be
    saved with this name in the [Entity Map](#entity-map). The test runner MUST raise an error if the name is already in
    use or if the result does not comply with [Supported Entity Types](#supported-entity-types).

    This field is mutually exclusive with [expectError](#operation_expectError).

    This field SHOULD NOT be used for [Special Test Operations](#special-test-operations) (i.e. `object: testRunner`).

#### expectedError

One or more assertions for an error/exception, which is expected to be raised by an executed operation. At least one key
is required in this object.

The structure of this object is as follows:

- `isError`: Optional boolean. If true, the test runner MUST assert that an error was raised. This is primarily used
    when no other error assertions apply but the test still needs to assert an expected error. Test files MUST NOT
    specify false, as [expectedError](#expectederror) is only applicable when an operation is expected to raise an
    error.

- `isClientError`: Optional boolean. If true, the test runner MUST assert that the error originates from the client
    (i.e. it is not derived from a server response). If false, the test runner MUST assert that the error does not
    originate from the client.

    Client errors include, but are not limited to: parameter validation errors before a command is sent to the server;
    network errors.

- `isTimeoutError`: Optional boolean. If true, the test runner MUST assert that the error represents a timeout due to
    use of the `timeoutMS` option. If false, the test runner MUST assert that the error does not represent a timeout.

- `errorContains`: Optional string. A substring of the expected error message (e.g. "errmsg" field in a server error
    document). The test runner MUST assert that the error message contains this string using a case-insensitive match.

    See [bulkWrite](#bulkwrite) for special considerations for BulkWriteExceptions.

- `errorCode`: Optional integer. The expected "code" field in the server-generated error response. The test runner MUST
    assert that the error includes a server-generated response whose "code" field equals this value. In the interest of
    readability, YAML files SHOULD use a comment to note the corresponding code name (e.g.
    `errorCode: 26 # NamespaceNotFound`).

    Server error codes are defined in
    [error_codes.yml](https://github.com/mongodb/mongo/blob/master/src/mongo/base/error_codes.yml).

    Test files SHOULD NOT assert error codes for client errors, as specifications do not define standardized codes for
    client errors.

- `errorCodeName`: Optional string. The expected "codeName" field in the server-generated error response. The test
    runner MUST assert that the error includes a server-generated response whose "codeName" field equals this value
    using a case-insensitive comparison.

    See [bulkWrite](#bulkwrite) for special considerations for BulkWriteExceptions.

    Server error codes are defined in
    [error_codes.yml](https://github.com/mongodb/mongo/blob/master/src/mongo/base/error_codes.yml).

    Test files SHOULD NOT assert error codes for client errors, as specifications do not define standardized codes for
    client errors.

- `errorLabelsContain`: Optional array of one or more strings. A list of error label strings that the error is expected
    to have. The test runner MUST assert that the error contains all of the specified labels (e.g. using the
    `hasErrorLabel` method).

- `errorLabelsOmit`: Optional array of one or more strings. A list of error label strings that the error is expected not
    to have. The test runner MUST assert that the error does not contain any of the specified labels (e.g. using the
    `hasErrorLabel` method).

- `writeErrors`: Optional document. The write errors expected to be present in the error. The `writeErrors` document
    contains numeric keys representing the index of the write that failed and `writeError` object values. The test
    runner MUST assert that the error contains a `writeError` for each index present in `writeErrors` and MUST assert
    that the `writeError`s match as root-level documents according to the rules in
    [Evaluating Matches](#evaluating-matches). The test runner MUST assert that the error does not contain any
    additional `writeError`s. This field is only intended for use with the [clientBulkWrite](#clientbulkwrite)
    operation.

- `writeConcernErrors`: Optional array of one or more objects. An ordered list of write concern errors expected to be
    present in the error. The test runner MUST assert that each `writeConcernError` in this list matches the
    `writeConcernError` present at the same index in the error's list of `writeConcernError`s as a root-level document
    according to the rules in [Evaluating Matches](#evaluating-matches). The test runner MUST assert that the error does
    not contain any additional `writeConcernErrors`s. This field is only intended for use with the
    [clientBulkWrite](#clientbulkwrite) operation.

<span id="expectedError_errorResponse"></span>

- `errorResponse`: Optional document. A value corresponding to the expected server response. The test runner MUST assert
    that the error includes a server response that matches this value as a root-level document according to the rules in
    [Evaluating Matches](#evaluating-matches).

    Note that some drivers may not be able to evaluate `errorResponse` for write commands (i.e. insert, update, delete)
    and bulk write operations. For example, a BulkWriteException is derived from potentially multiple server responses
    and may not provide direct access to a single response. Tests SHOULD avoid using `errorResponse` for such operations
    if possible; otherwise, affected drivers SHOULD skip such tests if necessary.

<span id="expectedError_expectResult"></span>

- `expectResult`: Optional mixed type. This field follows the same rules as
    [operation.expectResult](#operation_expectResult) and is only used in cases where the error includes a result (e.g.
    [bulkWrite](#bulkwrite)). If specified, the test runner MUST assert that the error includes a result and that it
    matches this value. If the result is optional (e.g. BulkWriteResult reported through the `writeResult` property of a
    BulkWriteException), this assertion SHOULD utilize the [$$unsetOrMatches](#unsetormatches) operator.

#### expectedEventsForClient

A list of events that are expected to be observed (in that order) for a client while executing
[operations](#test_operations).

The structure of each object is as follows:

- `client`: Required string. Client entity on which the events are expected to be observed. See
    [commonOptions_client](#commonOptions_client).
- `eventType`: Optional string. Specifies the type of the monitor which captured the events. Valid values are `command`
    for [Command Monitoring](../command-logging-and-monitoring/command-logging-and-monitoring.md#events-api) events,
    `cmap` for [CMAP](../connection-monitoring-and-pooling/connection-monitoring-and-pooling.md#events) events, and
    `sdam` for
    [SDAM](../server-discovery-and-monitoring/server-discovery-and-monitoring-logging-and-monitoring.md#events-api)
    events. Defaults to `command` if omitted.
- `events`: Required array of [expectedEvent](#expectedevent) objects. List of events, which are expected to be observed
    (in this order) on the corresponding client while executing [operations](#test_operations). If the array is empty,
    the test runner MUST assert that no events were observed on the client (excluding ignored events).
- `ignoreExtraEvents`: Optional boolean. Specifies how the `events` array is matched against the observed events. If
    `false`, observed events after all specified events have matched MUST cause a test failure; if `true`, observed
    events after all specified events have been matched MUST NOT cause a test failure. Defaults to `false`.

#### expectedEvent

An event (e.g. APM), which is expected to be observed while executing the test's operations.

This object MUST contain **exactly one** top-level key that identifies the event type and maps to a nested object, which
contains one or more assertions for the event's properties.

Some event properties are omitted in the following structures because they cannot be reliably tested. Taking command
monitoring events as an example, `requestId` and `operationId` are nondeterministic and types for `connectionId` and
`failure` can vary by implementation.

The events allowed in an `expectedEvent` object depend on the value of `eventType` in the corresponding
[expectedEventsForClient](#expectedeventsforclient) object, which can have one of the following values:

- `command` or omitted: only the event types defined in [expectedCommandEvent](#expectedcommandevent) are allowed.
- `cmap`: only the event types defined in [expectedCmapEvent](#expectedcmapevent) are allowed.
- `sdam`: only the event types defined in [expectedSdamEvent](#expectedsdamevent) are allowed.

##### expectedCommandEvent

The structure of this object is as follows:

<span id="expectedEvent_commandStartedEvent"></span>

- `commandStartedEvent`: Optional object. Assertions for one or more
    [CommandStartedEvent](../command-logging-and-monitoring/command-logging-and-monitoring.md#events-api) fields.

    The structure of this object is as follows:

    - `command`: Optional document. A value corresponding to the expected command document. Test runners MUST follow the
        rules in [Evaluating Matches](#evaluating-matches) when processing this assertion.
    - `commandName`: Optional string. Test runners MUST assert that the command name matches this value.
    - `databaseName`: Optional string. Test runners MUST assert that the database name matches this value. The YAML file
        SHOULD use an [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for this value (e.g.
        `databaseName: *database0Name`).
    - `hasServiceId`: Defined in [hasServiceId](#hasserviceid).
    - `hasServerConnectionId`: Defined in [hasServerConnectionId](#hasserverconnectionid).

<span id="expectedEvent_commandSucceededEvent"></span>

- `commandSucceededEvent`: Optional object. Assertions for one or more
    [CommandSucceededEvent](../command-logging-and-monitoring/command-logging-and-monitoring.md#events-api) fields.

    The structure of this object is as follows:

    - `reply`: Optional document. A value corresponding to the expected reply document. Test runners MUST follow the rules
        in [Evaluating Matches](#evaluating-matches) when processing this assertion.
    - `commandName`: Optional string. Test runners MUST assert that the command name matches this value.
    - `databaseName`: Optional string. Test runners MUST assert that the database name matches this value. The YAML file
        SHOULD use an [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for this value (e.g.
        `databaseName: *database0Name`).
    - `hasServiceId`: Defined in [hasServiceId](#hasserviceid).
    - `hasServerConnectionId`: Defined in [hasServerConnectionId](#hasserverconnectionid).

<span id="expectedEvent_commandFailedEvent"></span>

- `commandFailedEvent`: Optional object. Assertions for one or more
    [CommandFailedEvent](../command-logging-and-monitoring/command-logging-and-monitoring.md#events-api) fields.

    The structure of this object is as follows:

    - `commandName`: Optional string. Test runners MUST assert that the command name matches this value.
    - `databaseName`: Optional string. Test runners MUST assert that the database name matches this value. The YAML file
        SHOULD use an [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for this value (e.g.
        `databaseName: *database0Name`).
    - `hasServiceId`: Defined in [hasServiceId](#hasserviceid).
    - `hasServerConnectionId`: Defined in [hasServerConnectionId](#hasserverconnectionid).

##### expectedCmapEvent

<span id="expectedEvent_poolCreatedEvent"></span>

- `poolCreatedEvent`: Optional object. If present, this object MUST be an empty document as all fields in this event are
    non-deterministic.

<span id="expectedEvent_poolReadyEvent"></span>

- `poolReadyEvent`: Optional object. If present, this object MUST be an empty document as all fields in this event are
    non-deterministic.

<span id="expectedEvent_poolClearedEvent"></span>

- `poolClearedEvent`: Optional object. Assertions for one or more
    [PoolClearedEvent](../connection-monitoring-and-pooling/connection-monitoring-and-pooling.md#events) fields.

    The structure of this object is as follows:

    - `hasServiceId`: Defined in [hasServiceId](#hasserviceid).
    - `interruptInUseConnections`: Optional boolean. If specified, test runners MUST assert that the field is set and
        matches this value.

<span id="expectedEvent_poolClosedEvent"></span>

- `poolClosedEvent`: Optional object. If present, this object MUST be an empty document as all fields in this event are
    non-deterministic.

<span id="expectedEvent_connectionCreatedEvent"></span>

- `connectionCreatedEvent`: Optional object. If present, this object MUST be an empty document as all fields in this
    event are non-deterministic.

<span id="expectedEvent_connectionReadyEvent"></span>

- `connectionReadyEvent`: Optional object. If present, this object MUST be an empty document as all fields in this event
    are non-deterministic.

<span id="expectedEvent_connectionClosedEvent"></span>

- `connectionClosedEvent`: Optional object. Assertions for one or more
    [ConnectionClosedEvent](../connection-monitoring-and-pooling/connection-monitoring-and-pooling.md#events) fields.

    The structure of this object is as follows:

    - `reason`: Optional string. Test runners MUST assert that the reason in the published event matches this value. Valid
        values for this field are defined in the CMAP spec.

<span id="expectedEvent_connectionCheckOutStartedEvent"></span>

- `connectionCheckOutStartedEvent`: Optional object. If present, this object MUST be an empty document as all fields in
    this event are non-deterministic.

<span id="expectedEvent_connectionCheckOutFailedEvent"></span>

- `connectionCheckOutFailedEvent`: Optional object. Assertions for one or more
    [ConnectionCheckOutFailedEvent](../connection-monitoring-and-pooling/connection-monitoring-and-pooling.md#events)
    fields.

    The structure of this object is as follows:

    - `reason`: Optional string. Test runners MUST assert that the reason in the published event matches this value. Valid
        values for this field are defined in the CMAP spec.

<span id="expectedEvent_connectionCheckedOutEvent"></span>

- `connectionCheckedOutEvent`: Optional object. If present, this object MUST be an empty document as all fields in this
    event are non-deterministic.

<span id="expectedEvent_connectionCheckedInEvent"></span>

- `connectionCheckedInEvent`: Optional object. If present, this object MUST be an empty document as all fields in this
    event are non-deterministic.

##### expectedSdamEvent

The structure of this object is as follows:

<span id="expectedEvent_serverDescriptionChangedEvent"></span>

- `serverDescriptionChangedEvent`: Optional object. Assertions for one or more
    [ServerDescriptionChangedEvent](../server-discovery-and-monitoring/server-discovery-and-monitoring-logging-and-monitoring.md#events-api)
    fields.

    The structure of this object is as follows:

    - `previousDescription`: Optional object. A value corresponding to the server description as it was before the change
        that triggered this event.
    - `newDescription`: Optional object. A value corresponding to the server description as it was after the change that
        triggered this event.

    The structure of a server description object (which the `previousDescription` and `newDescription` fields contain) is
    as follows:

    - `type`: Optional string. The type of the server in the description. Test runners MUST assert that the type in the
        published event matches this value. See
        [SDAM: ServerType](../server-discovery-and-monitoring/server-discovery-and-monitoring.md#servertype) for a list of
        valid values.

<span id="expectedEvent_serverHeartbeatStartedEvent"></span>

- `serverHeartbeatStartedEvent`: Optional object. Assertions for one or more
    [ServerHeartbeatStartedEvent](../server-discovery-and-monitoring/server-discovery-and-monitoring-logging-and-monitoring.md#events-api)
    fields.

    The structure of this object is as follows:

    - `awaited`: Optional boolean. If specified, test runners MUST assert that the field is set and matches this value.

<span id="expectedEvent_serverHeartbeatSucceededEvent"></span>

- `serverHeartbeatSucceededEvent`: Optional object. Assertions for one or more
    [ServerHeartbeatSucceededEvent](../server-discovery-and-monitoring/server-discovery-and-monitoring-logging-and-monitoring.md#events-api)
    fields.

    The structure of this object is as follows:

    - `awaited`: Optional boolean. If specified, test runners MUST assert that the field is set and matches this value.

<span id="expectedEvent_serverHeartbeatFailedEvent"></span>

- `serverHeartbeatFailedEvent`: Optional object. Assertions for one or more
    [ServerHeartbeatFailedEvent](../server-discovery-and-monitoring/server-discovery-and-monitoring-logging-and-monitoring.md#events-api)
    fields.

    The structure of this object is as follows:

    - `awaited`: Optional boolean. If specified, test runners MUST assert that the field is set and matches this value.

<span id="expectedEvent_topologyDescriptionChangedEvent"></span>

- `topologyDescriptionChangedEvent`: Optional object. Assertions for one
    [TopologyDescriptionChangedEvent](../server-discovery-and-monitoring/server-discovery-and-monitoring-logging-and-monitoring.md#events-api)
    object.

    The structure of this object is as follows:

    - `previousDescription`: Optional Object. A value corresponding to the topology description as it was before the
        change that triggered the event.

    - `newDescription` : Optional Object. A value corresponding to the topology description as it is after the change that
        triggered the event.

        Test runners SHOULD ignore any other fields than the `previousDescription` and `newDescription` fields.

        The structure of a topology description object (which the `previousDescription` and `newDescription` fields contain
        is as follows:

        - `type`: Optional string. The type of the topology in the description. Test runners MUST assert that the type in
            the published event matches this value. See
            [SDAM: TopologyType](../server-discovery-and-monitoring/server-discovery-and-monitoring.md#topologytype) for a
            list of valid values.

        Test runners SHOULD ignore any other fields present on the `previousDescription` and `newDescription` fields of the
        captured `topologyDescriptionChangedEvent`.

##### hasServiceId

This field is an optional boolean that specifies whether or not the `serviceId` field of an event is set. If true, test
runners MUST assert that the field is set and is a non-empty BSON ObjectId (i.e. all bytes of the ObjectId are not 0).
If false, test runners MUST assert that the field is not set or is an empty BSON ObjectId.

##### hasServerConnectionId

This field is an optional boolean that specifies whether or not the `serverConnectionId` field of an event is set. If
true, test runners MUST assert that the field is set and is a positive Int32. If false, test runners MUST assert that
the field is not set, or, if the driver uses a nonpositive Int32 value to indicate the field being unset, MUST assert
that `serverConnectionId` is a nonpositive Int32.

#### expectedLogMessagesForClient

A list of log messages that are expected to be observed (in that order) for a client while executing
[operations](#test_operations).

The structure of each object is as follows:

- `client`: Required string. Client entity for which the messages are expected to be observed. See
    [commonOptions_client](#commonOptions_client).
- `messages`: Required array of [expectedLogMessage](#expectedlogmessage) objects. List of messages, which are expected
    to be observed (in this order) on the corresponding client while executing [operations](#test_operations). If the
    array is empty, the test runner MUST assert that no messages were observed on the client. The driver MUST assert
    that the messages produced are an exact match, i.e. that the expected and actual message counts are the same and
    that there are no extra messages emitted by the client during the test run. Note: `ignoreMessages` and
    `ignoreExtraMessages` may exclude log messages from this evaluation.
- `ignoreMessages`: Optional array of [expectedLogMessage](#expectedlogmessage) objects. Unordered set of messages,
    which MUST be ignored on the corresponding client while executing [operations](#test_operations). The test runner
    MUST exclude all log messages from observed messages that match any of the messages in `ignoreMessages` array before
    `messages` evaluation. Matching rules used to match messages in `ignoreMessages` are identical to match rules used
    for `messages` matching.
- `ignoreExtraMessages`: Optional boolean. Specifies how the `messages` array is matched against the observed logs. If
    `false`, observed logs after all specified logs have matched MUST cause a test failure; if `true`, observed logs
    after all specified logs have been matched MUST NOT cause a test failure. Defaults to `false`.

<span id="expectedLogMessage"></span>

#### expectedLogMessage

A log message which is expected to be observed while executing the test's operations.

The structure of each object is as follows:

- `level`: Required string. This MUST be one of the level names listed in
    [log severity levels](../logging/logging.md#log-severity-levels). This specifies the expected level for the log
    message and corresponds to the level used for the message in the specification that defines it. Note that since not
    all drivers will necessarily support all log levels, some driver may need to map the specified level to the
    corresponding driver-supported level. Test runners MUST assert that the actual level matches this value.

- `component`: Required string. This MUST be one of the component names listed in
    [components](../logging/logging.md#components). This specifies the expected component for the log message. Note that
    since naming variations are permitted for components, some drivers may need to map this to a corresponding
    language-specific component name. Test runners MUST assert that the actual component matches this value.

- `failureIsRedacted`: Optional boolean. This field SHOULD only be specified when the log message data is expected to
    contain a `failure` value.

    When `failureIsRedacted` is present and its value is `true`, the test runner MUST assert that a failure is present and
    that the failure has been redacted according to the rules defined for error redaction in the
    [command logging and monitoring specification](../command-logging-and-monitoring/command-logging-and-monitoring.md#security).
    

    When `false`, the test runner MUST assert that a failure is present and that the failure has NOT been redacted.

    The exact form of these assertions and how thorough they are will vary based on the driver's chosen error
    representation in logs; e.g. drivers that use strings may only be able to assert on the presence/absence of
    substrings.

- `data`: Required object. Contains key-value pairs that are expected to be attached to the log message. Test runners
    MUST assert that the actual data contained in the log message matches the expected data, and MUST treat the log
    message data as a root-level document.

    A suggested implementation approach is to decode `data` as a BSON document and serialize the data attached to each log
    message to a BSON document, and match those documents.

    Note that for drivers that do not implement structured logging, this requires designing logging internals such that
    data is first gathered in a structured form (e.g. a document or hashmap) which can be intercepted for testing
    purposes.

#### collectionOrDatabaseOptions

Map of parameters used to construct a collection or database object.

The structure of this object is as follows:

- `readConcern`: Optional object. See [commonOptions_readConcern](#commonOptions_readConcern).
- `readPreference`: Optional object. See [commonOptions_readPreference](#commonOptions_readPreference).
- `writeConcern`: Optional object. See [commonOptions_writeConcern](#commonOptions_writeConcern).

### Common Options

This section defines the structure of common options that are referenced from various contexts in the test format.
Comprehensive documentation for some of these types and their parameters may be found in the following specifications:

- [Read and Write Concern](../read-write-concern/read-write-concern.md).
- [Server Selection: Read Preference](../server-selection/server-selection.md#read-preference).
- [Server Discovery and Monitoring: TopologyDescription](../server-discovery-and-monitoring/server-discovery-and-monitoring.md#topologydescription).

The structure of these common options is as follows:

<span id="commonOptions_collectionName"></span>

- `collectionName`: String. Collection name. The YAML file SHOULD use an
    [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for a collection entity's `collectionName` field (e.g.
    `collectionName: *collection0Name`).

<span id="commonOptions_databaseName"></span>

- `databaseName`: String. Database name. The YAML file SHOULD use an
    [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for a database entity's `databaseName` field (e.g.
    `databaseName: *database0Name`).

<span id="commonOptions_readConcern"></span>

- `readConcern`: Object. Map of parameters to construct a read concern.

    The structure of this object is as follows:

    - `level`: Required string.

<span id="commonOptions_readPreference"></span>

- `readPreference`: Object. Map of parameters to construct a read preference.

    The structure of this object is as follows:

    - `mode`: Required string.
    - `tagSets`: Optional array of objects.
    - `maxStalenessSeconds`: Optional integer.
    - `hedge`: Optional object.

<span id="commonOptions_client"></span>

- `client`: String. Client entity name, which the test runner MUST resolve to a MongoClient object. The YAML file SHOULD
    use an [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for a client entity's `id` field (e.g.
    `client: *client0`).

<span id="commonOptions_session"></span>

- `session`: String. Session entity name, which the test runner MUST resolve to a ClientSession object. The YAML file
    SHOULD use an [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for a session entity's `id` field (e.g.
    `session: *session0`).

<span id="commonOptions_writeConcern"></span>

- `writeConcern`: Object. Map of parameters to construct a write concern.

    The structure of this object is as follows:

    - `journal`: Optional boolean.
    - `w`: Optional integer or string.
    - `wtimeoutMS`: Optional integer.

### Version String

Version strings, which are used for [schemaVersion](#schemaVersion) and [runOnRequirement](#runonrequirement), MUST
conform to one of the following formats, where each component is a non-negative integer:

- `<major>.<minor>.<patch>`
- `<major>.<minor>` (`<patch>` is assumed to be zero)
- `<major>` (`<minor>` and `<patch>` are assumed to be zero)

Any component other than `major`, `minor`, and `patch` MUST be discarded prior to comparing versions. This is necessary
to ensure that spec tests run on pre-release versions of the MongoDB server. As an example, when checking if a server
with the version `4.9.0-alpha4-271-g7d5cf02` passes the requirement for a test, only `4.9.0` is relevant for the
comparison. When reading the server version from the `buildInfo` command reply, the three elements of the `versionArray`
field MUST be used, and all other fields MUST be discarded for this comparison.

### Entity Test Operations

Entity operations correspond to an API method on a driver object. If [operation.object](#operation_object) refers to an
[entity](#entity) name (e.g. "collection0") then [operation.name](#operation_name) is expected to reference an API
method on that class.

Test files SHALL use camelCase when referring to API methods and parameters, even if the defining specifications use
other forms (e.g. snake_case in GridFS). Test files SHOULD use the exact API method names defined in specifications for
entity test operations. Test files MAY use a different descriptive name if a naming conflict occurs. For example, the
name "clientBulkWrite" is used for the client-level bulk write operation to differentiate it from the collection-level
bulk write operation.

This spec does not provide exhaustive documentation for all possible API methods that may appear in a test; however, the
following sections discuss all supported entities and their operations in some level of detail. Special handling for
certain operations is also discussed as needed.

#### Expressing Required and Optional Parameters

Some specifications group optional parameters for API methods under an `options` parameter (e.g.
`options: Optional<UpdateOptions>` in the CRUD spec); however, driver APIs vary in how they accept options (e.g.
Python's keyword/named arguments, `session` as either an option or required parameter depending on whether a language
supports method overloading). Therefore, test files SHALL declare all required and optional parameters for an API method
directly within [operation.arguments](#operation_arguments) (e.g. `upsert` for `updateOne` is *not* nested under an
`options` key).

#### Special Handling for Arguments

If `session` is specified in [operation.arguments](#operation_arguments), it is defined according to
[commonOptions_session](#commonOptions_session). Test runners MUST resolve the `session` argument to
[session](#entity_session) entity *before* passing it as a parameter to any API method.

If `readConcern`, `readPreference`, or `writeConcern` are specified in [operation.arguments](#operation_arguments), test
runners MUST interpret them according to the corresponding definition in [Common Options](#common-options) and MUST
convert the value into the appropriate object *before* passing it as a parameter to any API method.

#### Converting Returned Model Objects to Documents

For operations that return a model object (e.g. `BulkWriteResult` for `bulkWrite`), the test runner MUST convert the
model object to a document when evaluating [expectResult](#operation_expectResult) or
[saveResultAsEntity](#operation_saveResultAsEntity). Similarly, for operations that may return iterables of model
objects (e.g. `DatabaseInfo` for `listDatabases`), the test runner MUST convert the iterable to an array of documents
when evaluating [expectResult](#operation_expectResult) or [saveResultAsEntity](#operation_saveResultAsEntity).

#### Iterating Returned Iterables

Unless otherwise stated by an operation below, test runners MUST fully iterate any iterable returned by an operation as
part of that operation's execution. This is necessary to ensure consistent behavior among drivers, as discussed in
[collection_aggregate](#collection_aggregate) and [find](#find), and also ensures that error and event assertions can be
evaluated consistently.

### Client Operations

These operations and their arguments may be documented in the following specifications:

- [Change Streams](../change-streams/change-streams.md)
- [Enumerating Databases](../enumerate-databases/enumerate-databases.md)

Client operations that require special handling or are not documented by an existing specification are described below.

#### close

Closes the client, i.e. close underlying connection pool(s) and cease monitoring the topology. For languages that rely
on built-in language mechanisms such as reference counting to automatically close/deinitialize clients once they go out
of scope, this may require implementing an abstraction to allow a client entity's underlying client to be set to null.
Because drivers do not consistently propagate errors encountered while closing a client, test files SHOULD NOT specify
[expectResult](#operation_expectResult) or [expectError](#operation_expectError) for this operation. Test files SHOULD
NOT specify any operations for a client entity or any entity descended from it following a `close` operation on it, as
driver behavior when an operation is attempted on a closed client or one of its descendant objects is not consistent.

<span id="client_createChangeStream"></span>

#### createChangeStream

Creates a cluster-level change stream and ensures that the server-side cursor has been created.

This operation proxies the client's `watch` method and supports the same arguments and options. Test files SHOULD NOT
use the client's `watch` operation directly for reasons discussed in [ChangeStream](#entity_changestream). Test runners
MUST ensure that the server-side cursor is created (i.e. `aggregate` is executed) as part of this operation and before
the resulting change stream might be saved with [operation.saveResultAsEntity](#operation_saveResultAsEntity).

Test runners MUST NOT iterate the change stream when executing this operation and test files SHOULD NOT specify
[operation.expectResult](#operation_expectResult) for this operation.

#### clientBulkWrite

These considerations only apply to the `MongoClient.bulkWrite` method. See [bulkWrite](#bulkwrite) for special
considerations for `MongoCollection.bulkWrite`.

The `models` parameter for `clientBulkWrite` is documented as a list of WriteModel interfaces. Each WriteModel
implementation (e.g. InsertOneModel) provides important context to the method, but that type information is not easily
expressed in YAML and JSON. To account for this, test files MUST nest each WriteModel object in a single-key object,
where the key identifies the request type (e.g. "insertOne") and its value is an object expressing the parameters, as in
the following example:

```
arguments:
  models:
    - insertOne:
        document: { _id: 1, x: 1 }
    - replaceOne:
        filter: { _id: 2 }
        replacement: { x: 2 }
        upsert: true
    - updateOne:
        filter: { _id: 3 }
        update: { $set: { x: 3 } }
        upsert: true
    - updateMany:
        filter: { }
        update: { $inc: { x: 1 } }
    - deleteOne:
        filter: { x: 2 }
    - deleteMany:
        filter: { x: { $gt: 2 } }
  ordered: true
```

Because the `insertResults`, `updateResults`, and `deleteResults` may be absent or empty in the `BulkWriteResult`
returned from a summary-only bulk write, the `clientBulkWrite` operation SHOULD use the
[$$unsetOrMatches](#unsetormatches) operator for assertions on these fields when `verboseResults` is not set to true.
This also applies to result objects defined in the `expectedResult` field of [expectedError](#expectederror).

The `BulkWriteException` thrown by `MongoClient.bulkWrite` contains an optional `error` field that stores a top-level
error that occurred during the bulk write. Test runners MUST inspect the contents of this field when making assertions
based on the contents of the `errorCode` and `errorContains` fields in [expectedError](#expectederror).

`BulkWriteException` also contains `writeErrors` and `writeConcernErrors` fields that define the individual write errors
and write concern errors that occurred during the bulk write. Unified tests SHOULD use `writeErrors` and
`writeConcernErrors` in `expectedError` to assert on the contents of these fields. Test runners MUST NOT inspect the
contents of these fields when making assertions based on any other fields defined in `expectedError`.

While operations typically raise an error *or* return a result, the `MongoClient.bulkWrite` operation may report both
via the `partialResult` property of a `BulkWriteException`. In this case, the intermediary write result may be matched
with [expectedError_expectResult](#expectedError_expectResult)

#### watch

This operation SHOULD NOT be used in test files. See [client_createChangeStream](#client_createChangeStream).

### ClientEncryption Operations

These operations and their arguments may be documented in the following specifications:

- [Client Side Encryption](../client-side-encryption/client-side-encryption.md)

Operations that require sending and receiving KMS requests to encrypt or decrypt data keys may require appropriate KMS
credentials to be loaded by the driver. Drivers MUST load appropriate KMS credentials (i.e. from the environment or a
configuration file) when prompted by a test providing a placeholder value in a corresponding `kmsProviders` field as
described under [entity.clientEncryption](#entity_clientEncryption).

See the [Client-Side Encryption test README](../client-side-encryption/tests/README.md#credentials) for instructions to
obtain test credentials.

Drivers MUST be running the mock
[KMS KMIP server](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/csfle/kms_kmip_server.py)
when evaluating tests that require KMS requests to a KMIP KMS provider.

Drivers MAY enforce a unique index on `keyAltNames` as described in the
[Client Side Field Level Encryption spec](../client-side-encryption/client-side-encryption.md#why-arent-we-creating-a-unique-index-in-the-key-vault-collection)
when running key management operations on the key vault collection. Although unified tests are written assuming the
existence of the unique index, no unified test currently requires its implementation for correctness (e.g. no unified
test currently attempts to create a data key with an existing keyAltName or add an existing keyAltName to a data key).

### Database Operations

These operations and their arguments may be documented in the following specifications:

- [Change Streams](../change-streams/change-streams.md)
- [CRUD](../crud/crud.md)
- [Enumerating Collections](../enumerate-collections/enumerate-collections.md)

Database operations that require special handling or are not documented by an existing specification are described
below.

#### aggregate

When executing an `aggregate` operation, the test runner MUST fully iterate the result. This will ensure consistent
behavior between drivers that eagerly create a server-side cursor and those that do so lazily when iteration begins.

<span id="database_createChangeStream"></span>

#### createChangeStream

Creates a database-level change stream and ensures that the server-side cursor has been created.

This operation proxies the database's `watch` method and supports the same arguments and options. Test files SHOULD NOT
use the database's `watch` operation directly for reasons discussed in [ChangeStream](#entity_changestream). Test
runners MUST ensure that the server-side cursor is created (i.e. `aggregate` is executed) as part of this operation and
before the resulting change stream might be saved with [operation.saveResultAsEntity](#operation_saveResultAsEntity).

Test runners MUST NOT iterate the change stream when executing this operation and test files SHOULD NOT specify
[operation.expectResult](#operation_expectResult) for this operation.

#### listCollections

When executing a `listCollections` operation, the test runner MUST fully iterate the resulting cursor.

#### runCommand

Generic command runner.

This method does not inherit a read preference (per the
[Server Selection](../server-selection/server-selection.md#use-of-read-preferences-with-commands) spec); however,
`readPreference` may be specified as an argument.

The following arguments are supported:

- `command`: Required document. The command to be executed.
- `commandName`: Required string. The name of the command to run. This is used by languages that are unable preserve the
    order of keys in the `command` argument when parsing YAML/JSON.
- `readPreference`: Optional object. See [commonOptions_readPreference](#commonOptions_readPreference).
- `session`: Optional string. See [commonOptions_session](#commonOptions_session).

#### runCursorCommand

[Generic cursor returning command runner](../run-command/run-command.md).

This method does not inherit a read preference (per the
[Server Selection](../server-selection/server-selection.md#use-of-read-preferences-with-commands) spec); however,
`readPreference` may be specified as an argument.

This operation proxies the database's `runCursorCommand` method and supports the same arguments and options (note:
handling for `getMore` options may vary by driver implementation).

When executing the provided command, the test runner MUST fully iterate the cursor. This will ensure consistent behavior
between drivers that eagerly create a server-side cursor and those that do so lazily when iteration begins.

The following arguments are supported:

- `command`: Required document. The command to be executed.
- `commandName`: Required string. The name of the command to run. This is used by languages that are unable preserve the
    order of keys in the `command` argument when parsing YAML/JSON.
- `readPreference`: Optional object. See [commonOptions_readPreference](#commonOptions_readPreference).
- `session`: Optional string. See [commonOptions_session](#commonOptions_session).
- `batchSize`: Optional positive integer value. Use this value to configure the `batchSize` option sent on subsequent
    `getMore` commands.
- `maxTimeMS`: Optional non-negative integer value. Use this value to configure the `maxTimeMS` option sent on
    subsequent `getMore` commands.
- `comment`: Optional BSON value. Use this value to configure the `comment` option sent on subsequent `getMore`
    commands.
- `cursorType`: Optional string enum value, one of `'tailable' | 'tailableAwait' | 'nonTailable'`. Use this value to
    configure the enum passed to the `cursorType` option.
- `timeoutMode`: Optional string enum value, one of `'iteration' | 'cursorLifetime'`. Use this value to configure the
    enum passed to the `timeoutMode` option.

#### createCommandCursor

This operation proxies the database's `runCursorCommand` method and supports the same arguments and options (note:
handling for `getMore` options may vary by driver implementation). Test runners MUST ensure that the server-side cursor
is created (i.e. the command document has executed) as part of this operation and before the resulting cursor might be
saved with [operation.saveResultAsEntity](#operation_saveResultAsEntity). Test runners for drivers that lazily execute
the command on the first iteration of the cursor MUST iterate the resulting cursor once. The result from this iteration
MUST be used as the result for the first iteration operation on the cursor.

Test runners MUST NOT iterate the resulting cursor when executing this operation and test files SHOULD NOT specify
[operation.expectResult](#operation_expectResult) for this operation.

#### watch

This operation SHOULD NOT be used in test files. See [database_createChangeStream](#database_createChangeStream).

### Collection Operations

These operations and their arguments may be documented in the following specifications:

- [Change Streams](../change-streams/change-streams.md)
- [CRUD](../crud/crud.md)
- [Index Management](../index-management/index-management.md)

Collection operations that require special handling or are not documented by an existing specification are described
below.

<span id="collection_aggregate"></span>

#### aggregate

When executing an `aggregate` operation, the test runner MUST fully iterate the result. This will ensure consistent
behavior between drivers that eagerly create a server-side cursor and those that do so lazily when iteration begins.

#### bulkWrite

These considerations only apply to the `MongoCollection.bulkWrite` method. See [clientBulkWrite](#clientbulkwrite) for
special considerations for `MongoClient.bulkWrite`.

The `requests` parameter for `bulkWrite` is documented as a list of WriteModel interfaces. Each WriteModel
implementation (e.g. InsertOneModel) provides important context to the method, but that type information is not easily
expressed in YAML and JSON. To account for this, test files MUST nest each WriteModel object in a single-key object,
where the key identifies the request type (e.g. "insertOne") and its value is an object expressing the parameters, as in
the following example:

```
arguments:
  requests:
    - insertOne:
        document: { _id: 1, x: 1 }
    - replaceOne:
        filter: { _id: 2 }
        replacement: { x: 2 }
        upsert: true
    - updateOne:
        filter: { _id: 3 }
        update: { $set: { x: 3 } }
        upsert: true
    - updateMany:
        filter: { }
        update: { $inc: { x: 1 } }
    - deleteOne:
        filter: { x: 2 }
    - deleteMany:
        filter: { x: { $gt: 2 } }
  ordered: true
```

Because the `insertedIds` field of BulkWriteResult is optional for drivers to implement, assertions for that field
SHOULD utilize the [$$unsetOrMatches](#unsetormatches) operator.

While operations typically raise an error *or* return a result, the `bulkWrite` operation is unique in that it may
report both via the `writeResult` property of a BulkWriteException. In this case, the intermediary write result may be
matched with [expectedError_expectResult](#expectedError_expectResult). Because `writeResult` is optional for drivers to
implement, such assertions SHOULD utilize the [$$unsetOrMatches](#unsetormatches) operator.

Additionally, BulkWriteException is unique in that it aggregates one or more server errors in its `writeConcernError`
and `writeErrors` properties. When test runners evaluate [expectedError](#expectederror) assertions for `errorContains`
and `errorCodeName`, they MUST examine the aggregated errors and consider any match therein to satisfy the assertion(s).
Drivers that concatenate all write and write concern error messages into the BulkWriteException message MAY optimize the
check for `errorContains` by examining the concatenated message. Drivers that expose `code` but not `codeName` through
BulkWriteException MAY translate the expected code name to a number (see:
[error_codes.yml](https://github.com/mongodb/mongo/blob/master/src/mongo/base/error_codes.yml)) and compare with `code`
instead, but MUST raise an error if the comparison cannot be attempted (e.g. `code` is also not available, translation
fails).

<span id="collection_createChangeStream"></span>

#### createChangeStream

Creates a collection-level change stream and ensures that the server-side cursor has been created.

This operation proxies the collection's `watch` method and supports the same arguments and options. Test files SHOULD
NOT use the collection's `watch` operation directly for reasons discussed in [ChangeStream](#entity_changestream). Test
runners MUST ensure that the server-side cursor is created (i.e. `aggregate` is executed) as part of this operation and
before the resulting change stream might be saved with [operation.saveResultAsEntity](#operation_saveResultAsEntity).

Test runners MUST NOT iterate the change stream when executing this operation and test files SHOULD NOT specify
[operation.expectResult](#operation_expectResult) for this operation.

<span id="collection_createFindCursor"></span>

#### createFindCursor

This operation proxies the collection's `find` method and supports the same arguments and options. Test runners MUST
ensure that the server-side cursor is created (i.e. a `find` command is executed) as part of this operation and before
the resulting cursor might be saved with [operation.saveResultAsEntity](#operation_saveResultAsEntity). Test runners for
drivers that lazily execute the `find` command on the first iteration of the cursor MUST iterate the resulting cursor
once. The result from this iteration MUST be used as the result for the first iteration operation on the cursor.

Test runners MUST NOT iterate the resulting cursor when executing this operation and test files SHOULD NOT specify
[operation.expectResult](#operation_expectResult) for this operation.

#### createSearchIndex

This operations proxies the collection's `createSearchIndex` helper with the same arguments.

Each `createSearchIndex` operation receives a
[SearchIndexModel](../index-management/index-management.md#common-interfaces). If a driver has chosen to implement the
`createSearchIndex(name: String, definition: Document)` overload of `createSearchIndex`, then the `SearchIndexModel`
should be parsed by `createSearchIndex` unified test runner helper and the correct arguments should be passed into the
driver's helper.

#### createSearchIndexes

This operations proxies the collection's `createSearchIndexes` helper with the same arguments.

#### dropSearchIndex

This operation proxies the collection's `dropSearchIndex` helper with the same arguments.

#### find

When executing a `find` operation, the test runner MUST fully iterate the result. This will ensure consistent behavior
between drivers that eagerly create a server-side cursor and those that do so lazily when iteration begins.

#### findOneAndReplace and findOneAndUpdate

The `returnDocument` option for `findOneAndReplace` and `findOneAndUpdate` is documented as an enum with possible values
"Before" and "After". Test files SHOULD express `returnDocument` as a string and test runners MUST raise an error if its
value does not case-insensitively match either enum value.

#### insertMany

The CRUD spec documents `insertMany` as returning a BulkWriteResult. Because the `insertedIds` field of BulkWriteResult
is optional for drivers to implement, assertions for that field SHOULD utilize the [$$unsetOrMatches](#unsetormatches)
operator.

#### insertOne

The CRUD spec documents `insertOne` as returning an InsertOneResult; however, because all fields InsertOneResult are
optional drivers are permitted to forgo it entirely and have `insertOne` return nothing (i.e. void method). Tests
asserting InsertOneResult SHOULD utilize the [$$unsetOrMatches](#unsetormatches) operator for *both* the result object
and any optional fields within, as in the following examples:

```
- name: insertOne
  object: *collection0
  arguments:
    document: { _id: 2 }
  expectResult:
    $$unsetOrMatches:
      insertedId: { $$unsetOrMatches: 2 }
```

#### listSearchIndexes

This operation proxies the collection's `listSearchIndexes` helper and returns the result of the cursor as a list.

#### updateSearchIndex

This operation proxies the collection's `updateSearchIndex` helper with the same arguments.

#### watch

This operation SHOULD NOT be used in test files. See [collection_createChangeStream](#collection_createChangeStream).

### Session Operations

These operations and their arguments may be documented in the following specifications:

- [Convenient API for Transactions](../transactions-convenient-api/transactions-convenient-api.md)
- [Driver Sessions](../sessions/driver-sessions.md)

Session operations that require special handling or are not documented by an existing specification are described below.

#### withTransaction

The `withTransaction` operation's `callback` parameter is a function and not easily expressed in YAML/JSON. For ease of
testing, this parameter is expressed as an array of [operation](#operation) objects (analogous to
[test.operations](#test_operations)). Test runners MUST evaluate error and result assertions when executing these
operations in the callback.

Test runners MUST allow any errors from the callback operation(s) to propagate to `withTransaction`, irrespective of
[ignoreResultAndError](#operation_ignoreResultAndError) or [expectError](#operation_expectError). For example, if a
callback operation raises an error, it should be possible to assert that error at both the callback operation and
`withTransaction` level.

### Bucket Operations

These operations and their arguments may be documented in the following specifications:

- [GridFS](../gridfs/gridfs-spec.md)

Bucket operations that require special handling or are not documented by an existing specification are described below.

<span id="download"></span> <span id="downloadByName"></span>

#### download and downloadByName

These operations proxy the bucket's `openDownloadStream` and `openDownloadStreamByName` methods and support the same
parameters and options, but return a string containing the stream's contents instead of the stream itself. Test runners
MUST fully read the stream to yield the returned string. This is also necessary to ensure that any expected errors are
raised (e.g. missing chunks). Test files SHOULD use [$$matchesHexBytes](#matcheshexbytes) in
[expectResult](#operation_expectResult) to assert the contents of the returned string.

#### downloadToStream and downloadToStreamByName

These operations SHOULD NOT be used in test files. See
[IO operations for GridFS streams](#io-operations-for-gridfs-streams) in [Future Work](#future-work).

#### openDownloadStream and openDownloadStreamByName

These operations SHOULD NOT be used in test files. See [download and downloadByName](#download-and-downloadbyname).

<span id="openUploadStream"></span>

#### openUploadStream and openUploadStreamWithId

These operations SHOULD NOT be used in test files. See
[IO operations for GridFS streams](#io-operations-for-gridfs-streams) in [Future Work](#future-work).

<span id="upload-and-uploadWithId"></span>

#### upload and uploadWithId

These operations proxy the bucket's `uploadFromStream` and `uploadFromStreamWithId` methods and support the same
parameters and options with one exception: the `source` parameter is an object specifying hex bytes from which test
runners MUST construct a readable stream for the underlying methods. The structure of `source` is as follows:

```
{ $$hexBytes: <string> }
```

The string MUST contain an even number of hexadecimal characters (case-insensitive) and MAY be empty. The test runner
MUST raise an error if the structure of `source` or its string is malformed. The test runner MUST convert the string to
a byte sequence denoting the stream's readable data (if any). For example, "12ab" would denote a stream with two bytes:
"0x12" and "0xab".

#### uploadFromStream and uploadFromStreamWithId

These operations SHOULD NOT be used in test files. See [upload and uploadWithId](#upload-and-uploadwithid).

### Cursor Operations

There are no defined APIs for change streams and cursors since the mechanisms for iteration may differ between
synchronous and asynchronous drivers. To account for this, this section explicitly defines the supported operations for
the `ChangeStream`, `FindCursor`, and `CommandCursor` entity types.

Test runners MUST ensure that the iteration operations defined in this section will not inadvertently skip the first
document for a cursor. Albeit rare, this could happen if an operation were to blindly invoke `next` (or equivalent) on a
cursor in a driver where newly created cursors are already positioned at their first element and the cursor had a
non-empty `firstBatch`. Alternatively, some drivers may use a different iterator method for advancing a cursor to its
first position (e.g. `rewind` in PHP).

#### iterateUntilDocumentOrError

Iterates the cursor until either a single document is returned or an error is raised. This operation takes no arguments.
If [expectResult](#operation_expectResult) is specified, it SHOULD be a single document.

Some specification sections (e.g.
[Iterating the Change Stream](../change-streams/tests/README.md#iterating-the-change-stream)) caution drivers that
implement a blocking mode of iteration (e.g. asynchronous drivers) not to iterate the cursor unnecessarily, as doing so
could cause the test runner to block indefinitely. This should not be a concern for `iterateUntilDocumentOrError` as
iteration only continues until either a document or error is encountered.

#### iterateOnce

Performs a single iteration of the cursor. If the cursor's current batch is empty, one `getMore` MUST be attempted to
get more results. This operation takes no arguments. If [expectResult](#operation_expectResult) is specified, it SHOULD
be a single document.

Due to the non-deterministic nature of some cursor types (e.g. change streams on sharded clusters), test files SHOULD
only use this operation to perform command monitoring assertions on the `getMore` command. Tests that perform assertions
about the result of iteration should use [iterateUntilDocumentOrError](#iterateuntildocumentorerror) instead.

#### close

Closes the cursor. Because drivers do not consistently propagate errors from the `killCursors` command, test runners
MUST suppress all errors when closing the cursor. Test files SHOULD NOT specify [expectResult](#operation_expectResult)
or [expectError](#operation_expectError) for this operation. To assert whether the `killCursors` command succeeded or
failed, test files SHOULD use command monitoring assertions with
[commandSucceededEvent](#expectedEvent_commandSucceededEvent) and
[commandFailedEvent](#expectedEvent_commandFailedEvent) events.

### Special Test Operations

Certain operations do not correspond to API methods but instead represent special test operations (e.g. assertions).
These operations are distinguished by [operation.object](#operation_object) having a value of "testRunner". The
[operation.name](#operation_name) field will correspond to an operation defined below.

Special test operations return no result and are always expected to succeed. These operations SHOULD NOT be combined
with [expectError](#operation_expectError), [expectResult](#operation_expectResult), or
[saveResultAsEntity](#operation_saveResultAsEntity).

#### failPoint

The `failPoint` operation instructs the test runner to configure a fail point using a "primary" read preference using
the specified client entity (fail points are not configured using an internal MongoClient).

The following arguments are supported:

- `failPoint`: Required document. The `configureFailPoint` command to be executed.

- `client`: Required string. See [commonOptions_client](#commonOptions_client).

    The client entity SHOULD specify false for [useMultipleMongoses](#entity_client_useMultipleMongoses) if this operation
    could be executed on a sharded topology (according to [runOnRequirements](#runOnRequirements) or
    [test.runOnRequirements](#test_runOnRequirements)). This is advised because server selection rules for mongos could
    lead to unpredictable behavior if different servers were selected for configuring the fail point and executing
    subsequent operations.

When executing this operation, the test runner MUST keep a record of the fail point so that it can be disabled after the
test. The test runner MUST also ensure that the `configureFailPoint` command is excluded from the list of observed
command monitoring events for this client (if applicable).

An example of this operation follows:

```
# Enable the fail point on the server selected with a primary read preference
- name: failPoint
  object: testRunner
  arguments:
    client: *client0
    failPoint:
      configureFailPoint: failCommand
      mode: { times: 1 }
      data:
        failCommands: ["insert"]
        closeConnection: true
```

#### targetedFailPoint

The `targetedFailPoint` operation instructs the test runner to configure a fail point on a specific mongos.

The following arguments are supported:

- `failPoint`: Required document. The `configureFailPoint` command to be executed.

- `session`: Required string. See [commonOptions_session](#commonOptions_session).

    The client entity associated with this session SHOULD specify true for
    [useMultipleMongoses](#entity_client_useMultipleMongoses). This is advised because targeted fail points are intended
    to test mongos pinning, which warrants multiple mongoses.

The mongos on which to set the fail point is determined by the `session` argument (after resolution to a session
entity). Test runners MUST error if the session is not pinned to a mongos server at the time this operation is executed.

If the driver exposes an API to target a specific server for a command, the test runner SHOULD use the client entity
associated with the session to execute the `configureFailPoint` command. In this case, the test runner MUST also ensure
that this command is excluded from the list of observed command monitoring events for this client (if applicable). If
such an API is not available, but the test runner creates an internal MongoClient for each mongos, the test runner
SHOULD use the internal MongoClient corresponding to the session's pinned server for this operation. Otherwise, test
runners MUST create a new MongoClient that is directly connected to the session's pinned server for this operation. The
new MongoClient instance MUST be closed once the command has finished executing.

A test utilizing `targetedFailPoint` SHOULD NOT be permitted execute on a load balancer (according to
[runOnRequirements](#runOnRequirements) or [test.runOnRequirements](#test_runOnRequirements)). This is advised because
the `configureFailPoint` command does not use the session directly, which means there is no guarantee that the load
balancer will direct the command to the intended mongos.

When executing this operation, the test runner MUST keep a record of both the fail point and pinned mongos server so
that the fail point can be disabled on the same mongos server after the test.

An example of this operation follows:

```
# Enable the fail point on the mongos to which session0 is pinned
- name: targetedFailPoint
  object: testRunner
  arguments:
    session: *session0
    failPoint:
      configureFailPoint: failCommand
      mode: { times: 1 }
      data:
        failCommands: ["commitTransaction"]
        closeConnection: true
```

Since mongos pinning only applies when multiple mongoses are used, tests SHOULD NOT use `targetedFailPoint` unless the
session's MongoClient is configured with `useMultipleMongoses: true`.

#### assertSessionTransactionState

The `assertSessionTransactionState` operation instructs the test runner to assert that the given session has a
particular transaction state.

The following arguments are supported:

- `session`: Required string. See [commonOptions_session](#commonOptions_session).
- `state`: Required string. Expected transaction state for the session. Possible values are as follows: `none`,
    `starting`, `in_progress`, `committed`, and `aborted`.

An example of this operation follows:

```
- name: assertSessionTransactionState
  object: testRunner
  arguments:
    session: *session0
    state: in_progress
```

#### assertSessionPinned

The `assertSessionPinned` operation instructs the test runner to assert that the given session is pinned to a mongos
server.

The following arguments are supported:

- `session`: Required string. See [commonOptions_session](#commonOptions_session).

An example of this operation follows:

```
- name: assertSessionPinned
  object: testRunner
  arguments:
    session: *session0
```

#### assertSessionUnpinned

The `assertSessionUnpinned` operation instructs the test runner to assert that the given session is not pinned to a
mongos server.

The following arguments are supported:

- `session`: Required string. See [commonOptions_session](#commonOptions_session).

An example of this operation follows:

```
- name: assertSessionUnpinned
  object: testRunner
  arguments:
    session: *session0
```

#### assertDifferentLsidOnLastTwoCommands

The `assertDifferentLsidOnLastTwoCommands` operation instructs the test runner to assert that the last two
CommandStartedEvents observed on the client have different `lsid` fields. This assertion is primarily used to test that
dirty server sessions are discarded from the pool.

The following arguments are supported:

- `client`: Required string. See [commonOptions_client](#commonOptions_client).

    The client entity SHOULD include "commandStartedEvent" in [observeEvents](#entity_client_observeEvents).

The test runner MUST fail this assertion if fewer than two CommandStartedEvents have been observed on the client or if
either command does not include an `lsid` field.

An example of this operation follows:

```
- name: assertDifferentLsidOnLastTwoCommands
  object: testRunner
  arguments:
    client: *client0
```

#### assertSameLsidOnLastTwoCommands

The `assertSameLsidOnLastTwoCommands` operation instructs the test runner to assert that the last two
CommandStartedEvents observed on the client have identical `lsid` fields. This assertion is primarily used to test that
non-dirty server sessions are not discarded from the pool.

The following arguments are supported:

- `client`: Required string. See [commonOptions_client](#commonOptions_client).

    The client entity SHOULD include "commandStartedEvent" in [observeEvents](#entity_client_observeEvents).

The test runner MUST fail this assertion if fewer than two CommandStartedEvents have been observed on the client or if
either command does not include an `lsid` field.

An example of this operation follows:

```
- name: assertSameLsidOnLastTwoCommands
  object: testRunner
  arguments:
    client: *client0
```

#### assertSessionDirty

The `assertSessionDirty` operation instructs the test runner to assert that the given session is marked dirty.

The following arguments are supported:

- `session`: Required string. See [commonOptions_session](#commonOptions_session).

An example of this operation follows:

```
- name: assertSessionDirty
  object: testRunner
  arguments:
    session: *session0
```

#### assertSessionNotDirty

The `assertSessionNotDirty` operation instructs the test runner to assert that the given session is not marked dirty.

The following arguments are supported:

- `session`: Required string. See [commonOptions_session](#commonOptions_session).

An example of this operation follows:

```
- name: assertSessionNotDirty
  object: testRunner
  arguments:
    session: *session0
```

#### assertCollectionExists

The `assertCollectionExists` operation instructs the test runner to assert that the given collection exists in the
database. The test runner MUST use an internal MongoClient for this operation.

The following arguments are supported:

- `collectionName`: Required string. See [commonOptions_collectionName](#commonOptions_collectionName).
- `databaseName`: Required string. See [commonOptions_databaseName](#commonOptions_databaseName).

An example of this operation follows:

```
- name: assertCollectionExists
  object: testRunner
  arguments:
    collectionName: *collection0Name
    databaseName:  *database0Name
```

Use a `listCollections` command to check whether the collection exists. Note that it is currently not possible to run
`listCollections` from within a transaction.

#### assertCollectionNotExists

The `assertCollectionNotExists` operation instructs the test runner to assert that the given collection does not exist
in the database. The test runner MUST use an internal MongoClient for this operation.

The following arguments are supported:

- `collectionName`: Required string. See [commonOptions_collectionName](#commonOptions_collectionName).
- `databaseName`: Required string. See [commonOptions_databaseName](#commonOptions_databaseName).

An example of this operation follows:

```
- name: assertCollectionNotExists
  object: testRunner
  arguments:
    collectionName: *collection0Name
    databaseName:  *database0Name
```

Use a `listCollections` command to check whether the collection exists. Note that it is currently not possible to run
`listCollections` from within a transaction.

#### assertIndexExists

The `assertIndexExists` operation instructs the test runner to assert that an index with the given name exists on the
collection. The test runner MUST use an internal MongoClient for this operation.

The following arguments are supported:

- `collectionName`: Required string. See [commonOptions_collectionName](#commonOptions_collectionName).
- `databaseName`: Required string. See [commonOptions_databaseName](#commonOptions_databaseName).
- `indexName`: Required string. Index name.

An example of this operation follows:

```
- name: assertIndexExists
  object: testRunner
  arguments:
    collectionName: *collection0Name
    databaseName:  *database0Name
    indexName: t_1
```

Use a `listIndexes` command to check whether the index exists. Note that it is currently not possible to run
`listIndexes` from within a transaction.

#### assertIndexNotExists

The `assertIndexNotExists` operation instructs the test runner to assert that an index with the given name does not
exist on the collection. The test runner MUST use an internal MongoClient for this operation.

The following arguments are supported:

- `collectionName`: Required string. See [commonOptions_collectionName](#commonOptions_collectionName).
- `databaseName`: Required string. See [commonOptions_databaseName](#commonOptions_databaseName).
- `indexName`: Required string. Index name.

An example of this operation follows:

```
- name: assertIndexNotExists
  object: testRunner
  arguments:
    collectionName: *collection0Name
    databaseName:  *database0Name
    indexName: t_1
```

Use a `listIndexes` command to check whether the index exists. Note that it is currently not possible to run
`listIndexes` from within a transaction.

<span id="operation_createEntities"></span>

#### createEntities

The `createEntities` operation instructs the test runner to create the provided entities and store them in the current
test's [Entity Map](#entity-map).

- `entities`: Required array of one or more [entity](#entity) objects. As with the file-level
    [createEntities](#createentities) directive, test files SHOULD declare entities in dependency order, such that all
    referenced entities are defined before any of their dependent entities.

An example of this operation follows:

```
- name: createEntities
  object: testRunner
  arguments:
    entities:
      - client:
          id: &client0 client0
      - database:
          id: &database0 database0
          client: *client0
          databaseName: &database0Name test
```

#### loop

The `loop` operation executes sub-operations in a loop.

The following arguments are supported:

- `operations`: Required array of [operation](#operation) objects. List of operations (henceforth referred to as
    sub-operations) to run on each loop iteration. Each sub-operation must be a valid operation as described in
    [Entity Test Operations](#entity-test-operations).

    Sub-operations SHOULD NOT include the `loop` operation.

    If, in the course of executing sub-operations, a sub-operation yields an error or failure, the test runner MUST NOT
    execute subsequent sub-operations in the same loop iteration. If `storeErrorsAsEntity` and/or
    `storeFailuresAsEntity` options are specified, the loop MUST store the error/failure accordingly and continue to the
    next iteration (i.e. the error/failure will not interrupt the test). If neither `storeErrorsAsEntity` nor
    `storeFailuresAsEntity` are specified, the loop MUST terminate and raise the error/failure (i.e. the error/failure
    will interrupt the test).

- `storeErrorsAsEntity`: Optional string. If specified, the runner MUST capture errors arising during sub-operation
    execution and append a document with error information to the array stored in the specified entity.

    If this option is specified, the test runner MUST check the existence and the type of the entity with the specified
    name before executing the loop. If the entity does not exist, the test runner MUST create it with the type of BSON
    array. If the entity exists and is of type BSON array, the test runner MUST do nothing. If the entity exists and is
    of a different type, the test runner MUST raise an error.

    If this option is specified and `storeFailuresAsEntity` is not, failures MUST also be captured and appended to the
    array.

    Documents appended to the array MUST contain the following fields:

    - `error`: the textual description of the error encountered.
    - `time`: the number of (floating-point) seconds since the Unix epoch when the error was encountered.

- `storeFailuresAsEntity`: Optional string. If specified, the runner MUST capture failures arising during sub-operation
    execution and append a document with failure information to the array stored in the specified entity.

    If this option is specified, the test runner MUST check the existence and the type of the entity with the specified
    name before executing the loop. If the entity does not exist, the test runner MUST create it with the type of BSON
    array. If the entity exists and is of type BSON array, the test runner MUST do nothing. If the entity exists and is
    of a different type, the test runner MUST raise an error.

    If this option is specified and `storeErrorsAsEntity` is not, errors MUST also be captured and appended to the array.

    Documents appended to the array MUST contain the following fields:

    - `error`: the textual description of the failure encountered.
    - `time`: the number of (floating-point) seconds since the Unix epoch when the failure was encountered.

- `storeSuccessesAsEntity`: Optional string. If specified, the runner MUST keep track of the number of sub-operations
    that completed successfully, and store that number in the specified entity. For example, if the loop contains two
    sub-operations, and they complete successfully, each loop execution would increment the number of successes by two.

    If the entity of the specified name already exists, the test runner MUST raise an error.

- `storeIterationsAsEntity`: Optional string. If specified, the runner MUST keep track of the number of iterations of
    the loop performed, and store that number in the specified entity. The number of loop iterations is counted
    irrespective of whether sub-operations within the iteration succeed or fail.

    If the entity of the specified name already exists, the test runner MUST raise an error.

A *failure* is when the result or outcome of an operation executed by the test runner differs from its expected outcome.
For example, an `expectResult` assertion failing to match a BSON document or an `expectError` assertion failing to match
an error message would be considered a failure. An *error* is any other type of error raised by the test runner. For
example, an unsupported operation or inability to resolve an entity name would be considered an error.

This specification permits the test runner to report some failures as errors and some errors as failures. When the test
runner stores errors and failures as entities it MAY classify conditions as errors and failures in the same way as it
would when used in the driver's test suite. This includes reporting all errors as failures or all failures as errors.

If the test runner does not distinguish errors and failures in its reporting, it MAY report both conditions under either
category, but it MUST report any given condition in at most one category.

The following termination behavior MUST be implemented by the test runner:

- The test runner MUST provide a way to request termination of loops. This request will be made by the
    [Atlas testing workload executor](https://mongodb-labs.github.io/drivers-atlas-testing/spec-workload-executor.html)
    in response to receiving the termination signal from Astrolabe.
- When the termination request is received, the test runner MUST stop looping. If the test runner is looping when the
    termination request is received, the current loop iteration MUST complete to its natural conclusion (success or
    failure). If the test runner is not looping when the termination request is received, it MUST NOT start any new loop
    iterations in either the current test or subsequent tests for the lifetime of the test runner.
- The termination request MUST NOT affect non-loop operations, including any operations after the loop. The tests SHOULD
    NOT be written in such a way that the success or failure of operations that follow loops depends on how many loop
    iterations were performed.
- Receiving the termination request MUST NOT by itself be considered an error or a failure by the test runner.

The exact mechanism by which the workload executor requests termination of the loop in the test runner, including the
respective API, is left to the driver.

Tests SHOULD NOT include multiple loop operations (nested or sequential).

An example of this operation follows:

```
- name: loop
  object: testRunner
  arguments:
    storeErrorsAsEntity: errors
    storeFailuresAsEntity: failures
    storeSuccessesAsEntity: successes
    storeIterationsAsEntity: iterations
    operations:
      - name: find
        object: *collection0
        arguments:
          filter: { _id: { $gt: 1 }}
          sort: { _id: 1 }
        expectResult:
          - _id: 2, x: 22
          - _id: 3, x: 33
```

#### assertNumberConnectionsCheckedOut

The `assertNumberConnectionsCheckedOut` operation instructs the test runner to assert that the given number of
connections are currently checked out for the specified client entity. This operation only applies to drivers that
implement connection pooling and should be skipped for drivers that do not.

The following arguments are supported:

- `client`: Required string. See [commonOptions_client](#commonOptions_client).
- `connections`: Required integer. The number of connections expected to be checked out.

An example of this operation follows:

```
- name: assertNumberConnectionsCheckedOut
  object: testRunner
  arguments:
    client: *client0
    connections: 1
```

#### runOnThread

The `runOnThread` operation instructs the test runner to schedule an operation to be run on a given thread. The given
thread MUST begin executing the operation immediately. `runOnThread` MUST NOT wait for the operation to complete. If any
of the operation's test assertions fail, the entire test case MUST fail as well.

When writing test cases that use `runOnThread`, it's important to note that certain entities are not concurrency-safe
(e.g. sessions, cursors) and therefore SHOULD NOT be used in operations on multiple different threads entities.

The following arguments are supported:

- `thread`: Required string. Thread entity on which this operation should be scheduled.
- `operation`: Required [operation](#operation) object. The operation to schedule on the thread. This object must be a
    valid operation as described in [Entity Test Operations](#entity-test-operations).

An example of this operation follows:

```
- name: runOnThread
  object: testRunner
  arguments:
    thread: *thread0
    operation:
      name: insertOne
      object: *collection0
      arguments:
        document: { _id: 2 }
      expectResult:
        $$unsetOrMatches:
          insertedId: { $$unsetOrMatches: 2 }
```

#### waitForThread

The `waitForThread` operation instructs the test runner to notify the given thread that no more operations are
forthcoming, wait for it to complete its last operation, and assert that it exited without any errors.

If the `waitForThread` operation is not satisfied after 10 seconds, this operation MUST cause a test failure.

The `test.operations` list SHOULD contain a `waitForThread` operation for each thread entity that the test creates.

The following arguments are supported:

- `thread`: Required string. Thread entity that should be stopped and awaited for completion.

An example of this operation follows:

```
- name: waitForThread
  object: testRunner
  arguments:
    thread: *thread0
```

#### waitForEvent

The `waitForEvent` operation instructs the test runner to wait until the specified MongoClient has published a specific,
matching event a given number of times. Note that this includes any events published before the `waitForEvent` operation
started.

If the `waitForEvent` operation is not satisfied after 10 seconds, this operation MUST cause a test failure.

The following arguments are supported:

- `client`: Required string. Client entity whose events the runner will be waiting for.
- `event`: Required [expectedEvent](#expectedevent) object. The event which the test runner is waiting to be observed on
    the provided client. The assertions laid out in [expectedEvent](#expectedevent) MUST be used to determine if an
    observed event matches `event`. `event` SHOULD have an event type that was included in the `client`'s
    `observeEvents` field.
- `count`: Required integer. The number of matching events to wait for before resuming execution of subsequent
    operations.

For example, the following instructs the test runner to wait for at least one poolClearedEvent to be published:

```
- name: waitForEvent
  object: testRunner
  arguments:
    client: *client0
    event:
      poolClearedEvent: {}
    count: 1
```

#### assertEventCount

The `assertEventCount` operation instructs the test runner to assert the specified MongoClient has published a specific,
matching event a given number of times so far in the test.

The following arguments are supported:

- `client`: Required string. Client entity whose events the runner will be counting.
- `event`: Required [expectedEvent](#expectedevent) object. The event which the test runner will be counting on the
    provided client. The assertions laid out in [expectedEvent](#expectedevent) MUST be used to determine if an observed
    event matches `event`. `event` SHOULD have an event type that was included in the `client`'s `observeEvents` field.
- `count`: Required integer. The exact number of matching events that `client` should have seen so far.

For example, the following instructs the test runner to assert that a single PoolClearedEvent was published:

```
- name: assertEventCount
  object: testRunner
  arguments:
    client: *client0
    event:
      poolClearedEvent: {}
    count: 1
```

#### recordTopologyDescription

The `recordTopologyDescription` operation instructs the test runner to retrieve the specified MongoClient's current
[TopologyDescription](#entity_topologydescription) and store it in the [Entity Map](#entity-map).

The following arguments are supported:

- `client`: Required string. Client entity whose TopologyDescription will be recorded.
- `id`: Required string. The name with which the TopologyDescription will be stored in the [Entity Map](#entity-map).

For example:

```
- name: recordTopologyDescription
  object: testRunner
  arguments:
    client: *client0
    id: &postInsertTopology postInsertTopology
```

#### assertTopologyType

The `assertTopologyType` operation instructs the test runner to assert that the given
[TopologyDescription](#entity_topologydescription) has a particular TopologyType.

The following arguments are supported:

- `topologyDescription`: Required string. TopologyDescription entity whose TopologyType will be inspected.
- `topologyType`: Required string. Expected TopologyType for the TopologyDescription. See
    [SDAM: TopologyType](../server-discovery-and-monitoring/server-discovery-and-monitoring.md#topologytype) for a list
    of possible values.

For example:

```
- name: assertTopologyType
  object: testRunner
  arguments:
    topologyDescription: *postInsertTopology
    topologyType: ReplicaSetWithPrimary
```

#### waitForPrimaryChange

The `waitForPrimaryChange` operation instructs the test runner to wait until the provided MongoClient discovers a
different primary from the one in the provided [TopologyDescription](#entity_topologydescription). If the provided
TopologyDescription does not include a primary, then this operation will wait until the client discovers any primary.

The following arguments are supported:

- `client`: Required string. See [commonOptions_client](#commonOptions_client).

    The client entity MUST be the same one from which `topologyDescription` was derived. Test runners do not need to
    verify this.

- `priorTopologyDescription`: Required string. The name of a [TopologyDescription](#entity_topologydescription) entity
    which will be used to determine if the primary has changed or not.

- `timeoutMS`: Optional integer. The number of milliseconds to wait for the primary change before timing out and failing
    the test. If unspecified, a default timeout of 10 seconds MUST be used.

For example:

```
- name: waitForPrimaryChange
  object: testRunner
  arguments:
    client: *client0
    priorTopologyDescription: *postInsertTopology
    timeoutMS: 1000
```

#### wait

The `wait` operation instructs the test runner to sleep for a provided number of milliseconds.

The following arguments are supported:

- `ms`: Required integer. The number of milliseconds for which the current test runner thread should sleep.

For example:

```
- name: wait
  object: testRunner
  arguments:
    ms: 1000
```

### Special Placeholder Value

#### $$placeholder

Syntax:

```
{ field: { $$placeholder: 1 } }
```

This special key-value pair can be used anywhere the value for a key might be specified in an test file. It is intended
to act as a placeholder value in contexts where the test runner cannot provide a definite value or may be expected to
replace the placeholder with a value that cannot be specified by the test file (e.g. KMS provider credentials). The test
runner MUST raise an error if a placeholder value is used in an unexpected context or a replacement cannot be made.

An example of using this placeholder value follows:

```
kmsProviders:
  aws:
    accessKeyId: { $$placeholder: 1 }
    privateAccessKey: { $$placeholder: 1 }
```

Note: the test runner is not required to validate the type or value of a `$$placeholder` field.

### Evaluating Matches

Expected values in tests (e.g. [operation.expectResult](#operation_expectResult)) are expressed as either relaxed or
canonical [Extended JSON](../extended-json/extended-json.md).

The algorithm for matching expected and actual values is specified with the following pseudo-code:

```
function match (expected, actual):
  if expected is a document:
    // handle special operators (e.g. $$type)
    if first and only key of expected starts with "$$":
      execute any assertion(s) for the special operator
      return

    assert that actual is a document

    for every key/value in expected:
      // handle key-based operators (e.g. $$exists, $$unsetOrMatches)
      if value is a document and its first and only key starts with "$$":
        execute any assertion(s) for the special operator
        continue to the next iteration unless actual value must be matched

      assert that actual[key] exists
      assert that actual[key] matches value

    if expected is not the root document:
      assert that actual does not contain additional keys

    return

  if expected is an array:
    assert that actual is an array
    assert that actual and expected have the same number of elements

    for every index/value in expected:
      assert that actual[index] matches value

    return

  // expected is neither a document nor array
  assert that actual and expected are the same type, noting flexible numerics
  assert that actual and expected are equal
```

The rules for comparing documents and arrays are discussed in more detail in subsequent sections. When comparing types
*other* than documents and arrays, test runners MAY adopt any of the following approaches to compare expected and actual
values, as long as they are consistent:

- Convert both values to relaxed or canonical [Extended JSON](../extended-json/extended-json.md) and compare strings
- Convert both values to BSON, and compare bytes
- Convert both values to native representations, and compare accordingly

When comparing types that contain documents as internal properties (e.g. CodeWScope), the rules in
[Evaluating Matches](#evaluating-matches) do not apply and the documents MUST match exactly; however, test runners MUST
permit variation in document key order or otherwise normalize the documents before comparison.

#### Flexible Numeric Comparisons

When comparing numeric types (excluding Decimal128), test runners MUST consider 32-bit, 64-bit, and floating point
numbers to be equal if their values are numerically equivalent. For example, an expected value of `1` would match an
actual value of `1.0` (e.g. `ok` field in a server response) but would not match `1.5`.

#### Allowing Extra Fields in Root-level Documents

When matching root-level documents, test runners MUST permit the actual document to contain additional fields not
present in the expected document. Examples of root-level documents include, but are not limited to:

- `command` for [CommandStartedEvent](#expectedEvent_commandStartedEvent)
- `reply` for [CommandSucceededEvent](#expectedEvent_commandSucceededEvent)
- [expectResult](#operation_expectResult) for `findOneAndUpdate` [Collection Operations](#collection-operations)
- [expectResult](#operation_expectResult) for [iterateUntilDocumentOrError](#iterateuntildocumentorerror)
- [expectedError_errorResponse](#expectedError_errorResponse)
- each array element in [expectResult](#operation_expectResult) for [find](#find) or
    [collection_aggregate](#collection_aggregate) [Collection Operations](#collection-operations)

For example, the following documents match:

```
expected: { x: 1 }
actual: { x: 1, y: 1 }
```

The inverse is not true. For example, the following documents do not match:

```
expected: { x: 1, y: 1 }
actual: { x: 1 }
```

Test runners MUST NOT permit additional fields in nested documents. For example, the following documents do not match:

```
expected: { x: { y: 1 } }
actual: { x: { y: 1, z: 1 } }
```

It may be helpful to think of expected documents as a form of query criteria. The intention behind this rule is that it
is not always feasible or relevant for a test to exhaustively specify all fields in an expected document (e.g. cluster
time in `command` for [CommandStartedEvent](#expectedEvent_commandStartedEvent)).

When the expected value is an array, test runners MUST differentiate between an array of values, which may be documents,
(e.g. `distinct`) and an array of root-level documents (e.g. `find`, `aggregate`). For example, the following array of
documents would not match if returned by `distinct`, but would match if returned via `find` (after iterating the
cursor):

```
expected: [ { x: 1 }, { x: 2 } ]
actual: [ { x: 1, y: 1 }, { x: 2, y: 2 } ]
```

#### Document Key Order Variation

When matching documents, test runners MUST NOT require keys in the expected and actual document to appear in the same
order. For example, the following documents would match:

```
expected: { x: 1, y: 1 }
actual: { y: 1, x: 1 }
```

#### Arrays Must Contain the Same Number of Elements

When comparing arrays, expected and actual values MUST contain the same number of elements. For example, the following
arrays corresponding to a `distinct` operation result would not match:

```
expected: [ 1, 2, 3 ]
actual: [ 1, 2, 3, 4 ]
```

#### Special Operators for Matching Assertions

When matching expected and actual values, an equality comparison is not always sufficient. For instance, a test file
cannot anticipate what a session ID will be at runtime, but may still want to analyze the contents of an `lsid` field in
a command document. To address this need, special operators can be used.

These operators are objects with a single key identifying the operator. Such keys are prefixed with `$$` to ease in
detecting an operator (test runners need only inspect the first key of each object) and differentiate the object from
MongoDB query operators, which use a single `$` prefix. The key will map to some value that influences the operator's
behavior (if applicable).

When examining the structure of an expected value during a comparison, test runners MUST check if the value is an object
whose first and only key starts with `$$` and, if so, defer to the special logic defined in this section.

##### $$exists

Syntax:

```
{ field: { $$exists: <boolean> } }
```

This operator can be used anywhere the value for a key might be specified in an expected document. If true, the test
runner MUST assert that the key exists in the actual document, irrespective of its value (e.g. a key with a `null` value
would match). If false, the test runner MUST assert that the key does not exist in the actual document. This operator is
modeled after the [$exists](https://www.mongodb.com/docs/manual/reference/operator/query/exists/) query operator.

An example of this operator checking for a field's presence follows:

```
command:
  getMore: { $$exists: true }
  collection: *collectionName,
  batchSize: 5
```

An example of this operator checking for a field's absence follows:

```
command:
  update: *collectionName
  updates: [ { q: {}, u: { $set: { x: 1 } } } ]
  ordered: true
  writeConcern: { $$exists: false }
```

##### $$type

Syntax:

```
{ $$type: <string> }
{ $$type: [ <string>, <string>, ... ] }
```

This operator can be used anywhere a matched value is expected (including [expectResult](#operation_expectResult)). The
test runner MUST assert that the actual value exists and matches one of the expected types, which correspond to the
documented string types for the [$type](https://www.mongodb.com/docs/manual/reference/operator/query/type/) query
operator.

An example of this operator follows:

```
command:
  getMore: { $$type: [ "int", "long" ] }
  collection: { $$type: "string" }
```

When the actual value is an array, test runners MUST NOT examine types of the array's elements. Only the type of actual
field SHALL be checked. This is admittedly inconsistent with the behavior of the
[$type](https://www.mongodb.com/docs/manual/reference/operator/query/type/) query operator, but there is presently no
need for this behavior in tests.

##### $$matchesEntity

Syntax, where `entityName` is a string:

```
{ $$matchesEntity: <entityName> }
```

This operator can be used to reference a BSON entity anywhere a matched value is expected (including
[expectResult](#operation_expectResult)). If the BSON entity is defined in the current test's [Entity Map](#entity-map),
the test runner MUST fetch that entity and assert that the actual value matches the entity using the standard rules in
[Evaluating Matches](#evaluating-matches); otherwise, the test runner MUST raise an error for an undefined or mistyped
entity. The YAML file SHOULD use an [alias node](https://yaml.org/spec/1.2/spec.html#id2786196) for the entity name.

This operator is primarily used to assert identifiers for uploaded GridFS files.

An example of this operator follows:

```
operations:
  -
    object: *bucket0
    name: upload
    arguments:
      filename: "filename"
      source: { $$hexBytes: "12AB" }
    expectResult: { $$type: "objectId" }
    saveResultAsEntity: &objectid0 "objectid0"
  - object: *filesCollection
    name: find
    arguments:
      sort: { uploadDate: -1 }
      limit: 1
    expectResult:
      - _id: { $$matchesEntity: *objectid0 }
```

##### $$matchesHexBytes

Syntax, where `hexBytes` is an even number of hexadecimal characters (case-insensitive) and MAY be empty:

```
{ $$matchesHexBytes: <hexBytes> }
```

This operator can be used anywhere a matched value is expected (including [expectResult](#operation_expectResult)) and
the actual value is a string. The test runner MUST raise an error if the `hexBytes` string is malformed. This operator
is primarily used to assert the results of [download](#download) and [downloadByName](#downloadByName), which return
stream contents as a string.

##### $$unsetOrMatches

Syntax:

```
{ $$unsetOrMatches: <anything> }
```

This operator can be used anywhere a matched value is expected (including [expectResult](#operation_expectResult)),
excluding an array element because
[Arrays Must Contain the Same Number of Elements](#arrays-must-contain-the-same-number-of-elements). The test runner
MUST assert that the actual value either does not exist or matches the expected value. Matching the expected value MUST
use the standard rules in [Evaluating Matches](#evaluating-matches), which means that it may contain special operators.

This operator is primarily used to assert driver-optional fields from the CRUD spec (e.g. `insertedId` for
InsertOneResult, `writeResult` for BulkWriteException).

An example of this operator used for a result's field follows:

```
expectResult:
  insertedId: { $$unsetOrMatches: 2 }
```

An example of this operator used for an entire result follows:

```
expectError:
  expectResult:
    $$unsetOrMatches:
      deletedCount: 0
      insertedCount: 2
      matchedCount: 0
      modifiedCount: 0
      upsertedCount: 0
      upsertedIds: { }
```

##### $$sessionLsid

Syntax:

```
{ $$sessionLsid: <sessionEntityName> }
```

This operator can be used anywhere a matched value is expected (including [expectResult](#operation_expectResult)). If
the [session entity](#entity_session) is defined in the current test's [Entity Map](#entity-map), the test runner MUST
assert that the actual value equals its logical session ID; otherwise, the test runner MUST raise an error for an
undefined or mistyped entity. The YAML file SHOULD use an [alias node](https://yaml.org/spec/1.2/spec.html#id2786196)
for a session entity's `id` field (e.g. `session: *session0`).

An example of this operator follows:

```
command:
  ping: 1
  lsid: { $$sessionLsid: *session0 }
```

##### $$lte

Syntax:

```
{ $$lte: 5 }
```

This operator can be used anywhere a matched value is expected (including [expectResult](#operation_expectResult)). The
test runner MUST assert that the actual value is less than or equal to the specified value. Test runners MUST also apply
the rules specified in [Flexible Numeric Comparisons](#flexible-numeric-comparisons) for this operator. For example, an
expected value of `1` would match an actual value of `1.0` and `0.0` but would not match `1.1`.

##### $$matchAsDocument

Syntax:

```
{ $$matchAsDocument: <anything> }
```

This operator may be used anywhere a matched value is expected (including [expectResult](#operation_expectResult)) and
the actual value is an extended JSON string. The test runner MUST parse the actual value into a BSON document and match
it against the expected value. Matching the expected value MUST use the standard rules in
[Evaluating Matches](#evaluating-matches), which means that it may contain special operators. This operator is primarily
used to assert on extended JSON commands and command replies included in log messages.

##### $$matchAsRoot

This operator may be used anywhere a matched value is expected (including [expectResult](#operation_expectResult)) and
the expected and actual values are documents. The test runner MUST treat the actual value as a root-level document as
described in [Evaluating Matches](#evaluating-matches) and match it against the expected value.

### Test Runner Implementation

The sections below describe instructions for instantiating the test runner, loading each test file, and executing each
test within a test file. Test runners MUST NOT share state created by processing a test file with the processing of
subsequent test files, and likewise for tests within a test file.

#### Initializing the Test Runner

The test runner MUST be configurable with a connection string (or equivalent configuration), which will be used to
initialize any internal MongoClient(s) and any [client entities](#entity_client) (in combination with other URI
options). This specification is not prescriptive about how this information is provided. For example, it may be read
from an environment variable or configuration file.

Create a new MongoClient, which will be used for internal operations (e.g. processing [initialData](#initialData) and
[test.outcome](#test_outcome)). This is referred to elsewhere in the specification as the internal MongoClient. If this
MongoClient would connect multiple mongos nodes and the driver does not provide a way to target operations to specific
servers, the test runner MAY construct internal MongoClients for each mongos.

Determine the server version and topology type using an internal MongoClient. This information will be used to evaluate
any future [runOnRequirement](#runonrequirement) checks. Test environments SHOULD NOT use mixed version clusters, so it
is not necessary to check multiple servers.

In addition to the aforementioned connection string, the test runner MUST also be configurable with two other connection
strings (or equivalent configuration) that point to TCP load balancers: one fronting multiple servers and one fronting a
single server. These will be used to initialize client entities when executing tests against a load balanced sharded
cluster. If the topology type is `LoadBalanced` and Atlas Serverless is not being used, the test runner MUST error if
either of these URIs is not provided. When testing against other topology types or Atlas Serverless, these URIs SHOULD
NOT be provided and MUST be ignored if provided.

The test runner SHOULD terminate any open transactions (see:
[Terminating Open Transactions](#terminating-open-transactions)) using the internal MongoClient(s) before executing any
tests.

#### Executing a Test File

The instructions in this section apply for each test file loaded by the test runner.

Test files, which may be YAML or JSON files, MUST be interpreted using an
[Extended JSON](../extended-json/extended-json.md) parser. The parser MUST accept relaxed and canonical Extended JSON
(per [Extended JSON: Parsers](../extended-json/extended-json.md#parsers)), as test files may use either.

Upon loading a file, the test runner MUST read the [schemaVersion](#schemaVersion) field and determine if the test file
can be processed further. Test runners MAY support multiple versions and MUST NOT process incompatible files (as
discussed in [Test Runner Support](#test-runner-support)). If a test file is incompatible, test runners MUST raise an
error and MAY do so by reporting a test failure. Test runners MAY make an effort to infer the number of tests (and their
descriptions) from an incompatible file and report a failure for each test.

If [runOnRequirements](#runOnRequirements) is specified, the test runner MUST skip the test file unless one or more
[runOnRequirement](#runonrequirement) objects are satisfied.

For each element in [tests](#tests), follow the process in [Executing a Test](#executing-a-test).

#### Executing a Test

The instructions in this section apply for each [test](#test) occurring in a test file loaded by the test runner. After
processing a test, test runners MUST reset any internal state that resulted from doing so. For example, the
[Entity Map](#entity-map) created for one test MUST NOT be shared with another.

If at any point while executing this test an unexpected error is encountered or an assertion fails, the test runner MUST
consider this test to have failed and SHOULD continue with the instructions in this section to ensure that the test
environment is cleaned up (e.g. disable fail points, kill sessions) while also forgoing any additional assertions.

If [test.skipReason](#test_skipReason) is specified, the test runner MUST skip this test and MAY use the string value to
log a message.

If [test.runOnRequirements](#test_runOnRequirements) is specified, the test runner MUST skip the test unless one or more
[runOnRequirement](#runonrequirement) objects are satisfied.

If [initialData](#initialData) is specified, for each [collectionData](#collectiondata) therein the test runner MUST set
up the collection. All setup operations MUST use the internal MongoClient and a "majority" write concern. The test
runner MUST first drop the collection. If a `createOptions` document is present, the test runner MUST execute a `create`
command to create the collection with the specified options. The test runner MUST then insert the specified documents
(if any). If no documents are present and `createOptions` is not set, the test runner MUST create the collection. If the
topology is sharded, the test runner SHOULD use a single mongos for handling [initialData](#initialData) to avoid
possible runtime errors.

If the test might execute a transaction against a sharded deployment, the test runner MUST collect the latest cluster
time from processing [initialData](#initialData). See
[MigrationConflict Errors on Sharded Clusters](#migrationconflict-errors-on-sharded-clusters) for more information.

Create a new [Entity Map](#entity-map) that will be used for this test. If [createEntities](#createentities) is
specified, the test runner MUST create each [entity](#entity) accordingly and add it to the map. If the topology is a
sharded cluster, the test runner MUST handle [useMultipleMongoses](#entity_client_useMultipleMongoses) accordingly if it
is specified for any client entities. If the topology type is `LoadBalanced`, client entities MUST be initialized with
the appropriate load balancer connection string as discussed in
[useMultipleMongoses](#entity_client_useMultipleMongoses).

If the test might execute a transaction against a sharded deployment, the test runner MUST advance the cluster time of
any session entities created during the test using the cluster time collected from processing
[initialData](#initialData). See
[MigrationConflict Errors on Sharded Clusters](#migrationconflict-errors-on-sharded-clusters) for more information.

If the test might execute a `distinct` command within a sharded transaction, for each target collection the test runner
SHOULD execute a non-transactional `distinct` command on each mongos server using an internal MongoClient. See
[StaleDbVersion Errors on Sharded Clusters](#staledbversion-errors-on-sharded-clusters) for more information.

If the test might execute a `configureFailPoint` command, for each target client the test runner MAY specify a reduced
value for `heartbeatFrequencyMS` (and `minHeartbeatFrequencyMS` if possible) to speed up SDAM recovery time and server
selection after a failure; however, test runners MUST NOT do so for any client that specifies `heartbeatFrequencyMS` in
its `uriOptions`.

For each client entity where [observeEvents](#entity_client_observeEvents) has been specified, the test runner MUST
enable all event listeners necessary to collect the specified event types. Test runners MAY leave event listeners
disabled for tests that do not assert events (i.e. tests that omit both [test.expectEvents](#test_expectEvents) and
special operations such as [assertSameLsidOnLastTwoCommands](#assertsamelsidonlasttwocommands)).

For each client with command monitoring enabled, the test runner MUST ignore events for the following:

- Any command(s) specified in [ignoreCommandMonitoringEvents](#entity_client_ignoreCommandMonitoringEvents).
- Any `configureFailPoint` commands executed for [failPoint](#failpoint) and [targetedFailPoint](#targetedfailpoint)
    operations.
- Any commands containing sensitive information (per the
    [Command Logging and Monitoring](../command-logging-and-monitoring/command-logging-and-monitoring.md#security) spec)
    unless [observeSensitiveCommands](#entity_client_observeSensitiveCommands) is true. Note that drivers will redact
    commands and replies for sensitive commands. For `hello` and legacy hello, which are conditionally sensitive based
    on the presence of a `speculativeAuthenticate` field, the test runner may need to infer that the events are
    sensitive based on whether or not the command and reply documents are redacted (i.e. empty documents).

For each element in [test.operations](#test_operations), follow the process in
[Executing an Operation](#executing-an-operation). If an unexpected error is encountered or an assertion fails, the test
runner MUST consider this test to have failed.

If any event listeners were enabled on any client entities, the test runner MUST now disable those event listeners.

If any fail points were configured, the test runner MUST now disable those fail points (on the same server) to avoid
spurious failures in subsequent tests. For any fail points configured using [targetedFailPoint](#targetedfailpoint), the
test runner MUST disable the fail point on the same mongos server on which it was originally configured. See
[Disabling Fail Points](#disabling-fail-points) for more information.

If [test.expectEvents](#test_expectEvents) is specified, for each object therein the test runner MUST assert that the
number and sequence of expected events match the number and sequence of actual events observed on the specified client.
If the list of expected events is empty, the test runner MUST assert that no events were observed on the client. The
process for matching events is described in [expectedEvent](#expectedevent).

If [test.outcome](#test_outcome) is specified, for each [collectionData](#collectiondata) therein the test runner MUST
assert that the collection contains exactly the expected data. The test runner MUST query each collection using the
internal MongoClient, an ascending sort order on the `_id` field (i.e. `{ _id: 1 }`), a "primary" read preference, and a
"local" read concern. When comparing collection data, the rules in [Evaluating Matches](#evaluating-matches) do not
apply and the documents MUST match exactly; however, test runners MUST permit variations in document key order or
otherwise normalize the documents before comparison. If the list of documents is empty, the test runner MUST assert that
the collection is empty.

Before clearing the entity map at the end of each test, the test runner MUST allow its entities to be accessed
externally. The exact mechanism for facilitating this access is not prescribed by this specification, but drivers should
be mindful of concurrency if applicable. As an example, the test runner MAY be configured with a callback method, which
will be invoked at the end of each test and provided with the entity map (or an equivalent data structure). As
previously discussed in [Entity Map](#entity-map), test runners MAY restrict access to driver objects if necessary.

Clear the entity map for this test. For each ClientSession in the entity map, the test runner MUST end the session (e.g.
call [endSession](../sessions/driver-sessions.md#endsession)). For each ChangeStream and FindCursor in the entity map,
the test runner MUST close the cursor.

If the test started a transaction (i.e. executed a `startTransaction` or `withTransaction` operation), the test runner
MUST terminate any open transactions (see: [Terminating Open Transactions](#terminating-open-transactions)).

Proceed to the subsequent test.

#### Executing an Operation

The instructions in this section apply for each [operation](#operation) occurring in a [test](#test) contained within a
test file loaded by the test runner.

If at any point while executing an operation an unexpected error is encountered or an assertion fails, the test runner
MUST consider the parent test to have failed and proceed from [Executing a Test](#executing-a-test) accordingly.

If [operation.object](#operation_object) is "testRunner", this is a special operation. If
[operation.name](#operation_name) is defined in [Special Test Operations](#special-test-operations), the test runner
MUST execute the operation accordingly and, if successful, proceed to the next operation in the test; otherwise, the
test runner MUST raise an error for an undefined operation. The test runner MUST keep a record of any fail points
configured by special operations so that they may be disabled after the current test.

If [operation.object](#operation_object) is not "testRunner", this is an entity operation. If
[operation.object](#operation_object) is defined in the current test's [Entity Map](#entity-map), the test runner MUST
fetch that entity and note its type; otherwise, the test runner MUST raise an error for an undefined entity. If
[operation.name](#operation_name) does not correspond to a known operation for the entity type (per
[Entity Test Operations](#entity-test-operations)), the test runner MUST raise an error for an unsupported operation.
Test runners MAY skip tests that include operations that are intentionally unimplemented (e.g. `listCollectionNames`).

Proceed with preparing the operation's arguments. If `session` is specified in
[operation.arguments](#operation_arguments), the test runner MUST resolve it to a session entity and MUST raise an error
if the name is undefined or maps to an unexpected type. If a key in [operation.arguments](#operation_arguments) does not
correspond to a known parameter/option for the operation, the test runner MUST raise an error for an unsupported
argument.

Before executing the operation, the test runner MUST be prepared to catch a potential error from the operation (e.g.
enter a `try` block). Proceed with executing the operation and capture its result or error.

Note that some operations require special handling, as discussed in [Entity Test Operations](#entity-test-operations).
For example, model objects may need to be converted to documents (before matching or saving in the entity map) and
returned iterables may need to be fully iterated.

If [operation.ignoreResultAndError](#operation_ignoreResultAndError) is true, the test runner MUST NOT make any
assertions regarding the result or error of the operation and MUST proceed to the subsequent operation.

If [operation.expectError](#operation_expectError) is specified, the test runner MUST assert that the operation yielded
an error; otherwise, the test runner MUST assert that the operation did not yield an error. If an error was expected,
the test runner MUST evaluate any assertions in [expectedError](#expectederror) accordingly.

If [operation.expectResult](#operation_expectResult) is specified, the test MUST assert that it matches the actual
result of the operation according to the rules outlined in [Evaluating Matches](#evaluating-matches).

If [operation.saveResultAsEntity](#operation_saveResultAsEntity) is specified, the test runner MUST store the result in
the current test's entity map using the specified name. If the operation did not return a result or the result does not
comply with [Supported Entity Types](#supported-entity-types) then the test runner MUST raise an error.

After asserting the operation's error and/or result and optionally saving the result, proceed to the subsequent
operation.

#### Special Procedures

This section describes some procedures that may be referenced from earlier sections.

##### Terminating Open Transactions

Open transactions can cause tests to block indiscriminately. When connected to MongoDB 3.6 or later, test runners SHOULD
terminate all open transactions at the start of a test suite and after each failed test by killing all sessions in the
cluster. Using the internal MongoClient(s), execute the `killAllSessions` command on either the primary or, if connected
to a sharded cluster, each mongos server.

For example:

```
db.adminCommand({
  killAllSessions: []
});
```

The test runner MAY ignore the following command failures:

- Interrupted(11601) to work around [SERVER-38335](https://jira.mongodb.org/browse/SERVER-38335).
- Unauthorized(13) to work around [SERVER-54216](https://jira.mongodb.org/browse/SERVER-54216).
- CommandNotFound(59) if the command is executed on a pre-3.6 server

Note that Atlas, by design, does not allow database users to kill sessions belonging to other users. This makes it
impossible to guarantee that an existing transaction will not block test execution. To work around this, test runners
SHOULD either ignore Unauthorized(13) command failures or avoid calling `killAllSessions` altogether when connected to
Atlas (e.g. by detecting `mongodb.net` in the hostname or allowing the test runner to be configured externally).

Test runners MUST NOT execute `killAllSessions` when connected to Atlas Data Lake.

##### MigrationConflict Errors on Sharded Clusters

Following [SERVER-82353](https://jira.mongodb.org/browse/SERVER-82353), drivers may encounter MigrationConflict errors
when executing transactions on sharded clusters due to an outdated cluster time. For example:

```
Transaction fe0b9a7d-4b64-4e38-aad2-4c7dd5ab0c2b - 47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU= -  - :1 was aborted on statement 0 due to: a non-retryable snapshot error :: caused by :: Encountered error from localhost:27217 during a transaction :: caused by :: Database transaction-tests has undergone a catalog change operation at time Timestamp(1708062645, 94) and no longer satisfies the requirements for the current transaction which requires Timestamp(1708062645, 93). Transaction will be aborted.
```

To work around this issue, a test runner MUST collect the latest cluster time from processing
[initialData](#initialData), which is executed using the internal MongoClient, and use it to advance the cluster time of
every session entity created during the test, by either [createEntities](#createentities) or the
[special test operation](#operation_createEntities)). This will ensure that the cluster time is gossipped to any other
mongo hosts that may be used to execute a transaction during the test.

Depending on the test runner implementation, the cluster time may be collected in various ways. For example:

- Execute a `ping` command against the same mongos host used for [initialData](#initialData) and read the `$clusterTime`
    response field
- Execute all operations for [initialData](#initialData) using an explicit session and read its cluster time after the
    last operation.

This logic is only necessary for tests that might execute a transaction against a sharded deployment transaction (i.e.
[test.operations](#test_operations) includes `startTransaction` or `withTransaction` and the topology is sharded or
load-balanced). To ease the implementation, test runners MAY apply this logic to *every* test.

##### StaleDbVersion Errors on Sharded Clusters

When a shard receives its first command that contains a `databaseVersion`, the shard returns a StaleDbVersion error and
mongos retries the operation. In a sharded transaction, mongos does not retry these operations and instead returns the
error to the client. For example:

```
Command distinct failed: Transaction aa09e296-472a-494f-8334-48d57ab530b6:1 was aborted on statement 0 due to: an error from cluster data placement change :: caused by :: got stale databaseVersion response from shard sh01 at host localhost:27217 :: caused by :: don't know dbVersion.
```

To work around this limitation, a test runners MUST execute a non-transactional `distinct` command on each mongos server
before running any test that might execute `distinct` within a transaction. To ease the implementation, test runners MAY
execute `distinct` before *every* test.

Test runners can remove this workaround once [SERVER-39704](https://jira.mongodb.org/browse/SERVER-39704) is resolved,
after which point mongos should retry the operation transparently. The `distinct` command is the only command allowed in
a sharded transaction that uses the `databaseVersion` concept so it is the only command affected.

### Server Fail Points

Many tests utilize the `configureFailPoint` command to trigger server-side errors such as dropped connections or command
errors. Tests can configure fail points using the special [failPoint](#failpoint) or
[targetedFailPoint](#targetedfailpoint) operations.

This internal command is not documented in the MongoDB manual (pending
[DOCS-10784](https://jira.mongodb.org/browse/DOCS-10784)); however, there is scattered documentation available on the
server wiki ([The "failCommand" Fail Point](https://github.com/mongodb/mongo/wiki/The-%22failCommand%22-fail-point)) and
employee blogs (e.g. [Intro to Fail Points](https://kchodorow.com/2013/01/15/intro-to-fail-points/),
[Testing Network Errors With MongoDB](https://emptysqua.re/blog/mongodb-testing-network-errors/)). Documentation can
also be gleaned from JIRA tickets (e.g. [SERVER-35004](https://jira.mongodb.org/browse/SERVER-35004),
[SERVER-35083](https://jira.mongodb.org/browse/SERVER-35083)). This specification does not aim to provide comprehensive
documentation for all fail points available for driver testing, but some fail points are documented in
[Fail Points Commonly Used in Tests](#fail-points-commonly-used-in-tests).

#### Configuring Fail Points

The `configureFailPoint` command is executed on the `admin` database and has the following structure:

```
db.adminCommand({
    configureFailPoint: <string>,
    mode: <string|object>,
    data: <object>
});
```

The value of `configureFailPoint` is a string denoting the fail point to be configured (e.g. "failCommand").

The `mode` option is a generic fail point option and may be assigned a string or object value. The string values
"alwaysOn" and "off" may be used to enable or disable the fail point, respectively. An object may be used to specify
either `times` or `skip`, which are mutually exclusive:

- `{ times: <integer> }` may be used to limit the number of times the fail point may trigger before transitioning to
    "off".
- `{ skip: <integer> }` may be used to defer the first trigger of a fail point, after which it will transition to
    "alwaysOn".

The `data` option is an object that may be used to specify any options that control the particular fail point's
behavior.

In order to use `configureFailPoint`, the undocumented `enableTestCommands`
[server parameter](https://www.mongodb.com/docs/manual/reference/parameters/) must be enabled by either the
configuration file or command line option (e.g. `--setParameter enableTestCommands=1`). It cannot be enabled at runtime
via the [setParameter](https://www.mongodb.com/docs/manual/reference/command/setParameter/) command). This parameter
should already be enabled for most configuration files in
[mongo-orchestration](https://github.com/10gen/mongo-orchestration).

#### Disabling Fail Points

A fail point may be disabled like so:

```
db.adminCommand({
    configureFailPoint: <string>,
    mode: "off"
});
```

#### Fail Points Commonly Used in Tests

##### failCommand

The `failCommand` fail point allows the client to force the server to return an error for commands listed in the
`data.failCommands` field. Additionally, this fail point is documented in server wiki:
[The failCommand Fail Point](https://github.com/mongodb/mongo/wiki/The-%22failCommand%22-fail-point).

The `failCommand` fail point was introduced in mongod 4.0.0
([SERVER-34551](https://jira.mongodb.org/browse/SERVER-34551)) and mongos 4.1.5
([SERVER-35518](https://jira.mongodb.org/browse/SERVER-35518)); however, the fail point was not usable for testing on
mongos until version 4.1.7 ([SERVER-34943](https://jira.mongodb.org/browse/SERVER-34943)).

The `failCommand` fail point may be configured like so:

```
db.adminCommand({
    configureFailPoint: "failCommand",
    mode: <string|object>,
    data: {
      failCommands: [<string>, ...],
      closeConnection: <boolean>,
      errorCode: <integer>,
      errorLabels: [<string>, ...],
      writeConcernError: <object>,
      appName: <string>,
      blockConnection: <boolean>,
      blockTimeMS: <integer>,
    }
});
```

`failCommand` supports the following `data` options, which may be combined if desired:

- `failCommands`: Required array of strings. Lists the command names to fail.
- `closeConnection`: Optional boolean, which defaults to `false`. If `true`, the command will not be executed, the
    connection will be closed, and the client will see a network error.
- `errorCode`: Optional integer, which is unset by default. If set, the command will not be executed and the specified
    command error code will be returned as a command error.
- `errorLabels`: Optional array of strings. If set, this list overrides the server's normal behavior for adding error
    labels. An empty array may be used to suppress the server from adding error labels to the response. New in server
    4.3.1 ([SERVER-43941](https://jira.mongodb.org/browse/SERVER-43941)).
- `appName`: Optional string, which is unset by default. If set, the fail point will only apply to connections for
    MongoClients created with this `appname`. New in server 4.4.0-rc2 and backported to 4.2.9
    ([SERVER-47195](https://jira.mongodb.org/browse/SERVER-47195)).
- `blockConnection`: Optional boolean, which defaults to `false`. If `true`, the server should block the affected
    commands for `blockTimeMS`. New in server 4.3.4 and backported to 4.2.9
    ([SERVER-41070](https://jira.mongodb.org/browse/SERVER-41070)).
- `blockTimeMS`: Optional integer, which is required when `blockConnection` is `true`. The number of milliseconds for
    which the affected commands should be blocked. New in server 4.3.4 and backported to 4.2.9
    ([SERVER-41070](https://jira.mongodb.org/browse/SERVER-41070)).

##### onPrimaryTransactionalWrite

The `onPrimaryTransactionalWrite` fail point allows the client to force a network error before the server would return a
write result to the client. The fail point also allows control whether the server will successfully commit the write via
its `failBeforeCommitExceptionCode` option. Keep in mind that the fail point only triggers for transaction writes (i.e.
write commands including `txnNumber` and `lsid` fields).

The `onPrimaryTransactionalWrite` fail point was introduced in mongod 3.6.0
([SERVER-29606](https://jira.mongodb.org/browse/SERVER-29606)) to facilitate testing of retryable writes. It is only
supported on mongod and cannot be used with sharded clusters.

`onPrimaryTransactionalWrite` supports the following `data` options:

- `closeConnection`: Optional boolean, which defaults to `true`. If `true`, the connection on which the write is
    executed will be closed before a result can be returned.
- `failBeforeCommitExceptionCode`: Optional integer, which is unset by default. If set, the specified exception code
    will be thrown and the write will not be committed. If unset, the write will be allowed to commit.

### Determining if a Sharded Cluster Uses Replica Sets

When connected to a mongos server, the test runner can query the
[config.shards](https://www.mongodb.com/docs/manual/reference/config-database/#mongodb-data-config.shards) collection.
Each shard in the cluster is represented by a document in this collection. If the shard is backed by a single server,
the `host` field will contain a single host. If the shard is backed by a replica set, the `host` field contain the name
of the replica followed by a forward slash and a comma-delimited list of hosts.

Note: MongoDB 3.6+ requires that all shard servers be replica sets.

## Design Rationale

This specification was primarily derived from the test formats used by the
[Transactions](../transactions/transactions.md) and [CRUD](../crud/crud.md) specs, which have served models or other
specs.

This specification commonly uses "SHOULD" when providing guidance on writing test files. While this may appear
contradictory to the driver mantra preferring "MUST", it is intentional. Some of this guidance addresses style (e.g.
adding comments, using YAML anchors) and cannot be enforced with a JSON schema. Other guidance needs to be purposefully
ignored in order to test the test runner implementation (e.g. defining entities out of order to trigger runtime errors).
The specification does prefer "MUST" in other contexts, such as discussing parts of the test file format that *are*
enforceable by the JSON schema or the test runner implementation.

<span id="rationale_observeSensitiveCommands"></span>

### Why can't `observeSensitiveCommands` be true when authentication is enabled?

When running against authentication-enabled clusters, the events observed by a client will always begin with
auth-related commands (e.g. `authenticate`, `saslStart`, `saslContinue`) because the MongoClient will need to
authenticate a connection before issuing the first command in the test specification. Since the exact form of the
authentication command event will depend on whether authentication is enabled, as well as, the auth mechanism in use, it
is not possible to anticipate the command monitoring output and perform the appropriate assertions. Consequently, we
have restricted use of this property to situations where authentication is disabled on the server. This allows tests to
explicitly test sensitive commands via the `runCommand` helper.

## Breaking Changes

This section is reserved for future use. Any breaking changes to the test format SHOULD be described here in detail for
historical reference, in addition to any shorter description that may be added to the [Changelog](#changelog).

## Future Work

### Assert expected log messages

When drivers support standardized logging, the test format may need to support assertions for messages expected to be
logged while executing operations. Since log messages are strings, this may require an operator to match regex patterns
within strings. Additionally, the test runner may need to support ignoring extra log output, similar to
`ignoreExtraEvents`.

### Target failPoint by read preference

The [failPoint](#failpoint) operation currently uses a "primary" read preference. To date, no spec has needed behavior
to configure a fail point on a non-primary node. If the need does arise, [failPoint](#failpoint) can be enhanced to
support a `readPreference` argument.

### IO operations for GridFS streams

Original GridFS spec tests refer to "upload", "download", and "download_by_name" methods, which allow the tests to
abstract stream IO and either upload a byte sequence or assert a downloaded byte sequence. These operations correspond
to the [download](#download), [downloadByName](#downloadByName), [upload](#upload-and-uploadWithId), and
[uploadWithId](#upload-and-uploadWithId) [Bucket Operations](#bucket-operations).

In order to support methods such as `downloadToStream`, `openUploadStream`, and `openUploadStreamWithId`, test runners
would need to represent streams as entities and support IO operations to directly read from and write to a stream
entity. This may not be worth the added complexity if the existing operations provide adequate test coverage for GridFS
implementations.

### Support Client-side Encryption integration tests

Supporting client-side encryption spec tests will require the following changes to the test format:

- `json_schema` will need to be specified when creating a collection, via either the collection entity definition or
    [initialData](#initialData).
- `key_vault_data` can be expressed via [initialData](#initialData)
- `autoEncryptOpts` will need to be specified when defining a client entity. Preparation of this field may require
    reading AWS credentials from environment variables.

The process for executing tests should not require significant changes, but test files will need to express a dependency
on mongocryptd.

### Incorporate referenced entity operations into the schema version

The [Schema Version](#schema-version) is not impacted by changes to operations defined in other specs and referenced in
`Entity Test Operations` (e.g. `find` for CRUD). The [operation.name](#operation_name) and
[operation.arguments](#operation_arguments) fields are loosely defined in the JSON schema as string and object types,
respectively.

Ideally, all operations (and their arguments) would be enforced by the JSON schema *and* any changes to operations would
affect the schema version accordingly. For example, a new `find` option would warrant a minor version bump both for the
CRUD spec and this spec and its schema.

As discussed in [Executing an Operation](#executing-an-operation), test runners MUST raise errors for unsupported
operations and arguments. This is a concession until such time that better processes can be established for versioning
other specs *and* collating spec changes developed in parallel or during the same release cycle.

## Changelog

- 2024-09-18: Note that `failCommand` `appName` option was backported

- 2024-05-08: **Schema version 1.21.**

    Add `writeErrors` and `writeConcernErrors` field to `expectedError` for the client-level bulk write API.

- 2024-04-15: Note that when `directConnection` is set to true test runners should only provide a single seed.

- 2024-03-25: **Schema version 1.20.**

    Add `previousDescription` and `newDescription` assertions to `topologyDescriptionChangedEvent` when checking events
    with `expectEvents`

- 2024-03-11: Note that `killAllSessions` should not be executed on Atlas Data Lake

- 2024-02-27: Document `onPrimaryTransactionalWrite` fail point, which is used in retryable writes tests.

- 2024-02-23: Require test runners to gossip cluster time from internal MongoClient to each session entity.

- 2024-02-14: Clarify that errors raised from callback operations should always propagate to `withTransaction`.

- 2024-02-12: Clarify that `targetedFailPoint` should only be used when `useMultipleMongoses` is true and not on
    load-balanced topologies.

- 2024-02-06: Migrated from reStructuredText to Markdown.

- 2024-01-17: **Schema version 1.19.**

    Add `authMechanism` to `runOnRequirement` and require that `uriOptions` supports placeholder documents.

- 2024-01-11: **Schema version 1.18.**

    Allow named KMS providers in `kmsProviders`. Note location of Client-Side Encryption test credentials.

- 2024-01-03: Document server version requirements for `errorLabels` and `blockConnection` options for `failCommand`
    fail point.

- 2023-10-04: **Schema version 1.17.**

    Add `serverHeartbeatStartedEvent`, `serverHeartbeatSucceededEvent`, and `serverHeartbeatFailedEvent` for asserting on
    SDAM server heartbeat events.

- 2023-09-25: Clarify that the UTR is intended to be run against enterprise servers.

- 2022-07-18: **Schema version 1.16.**

    Add `ignoreMessages` and `ignoreExtraMessages` fields to `expectedLogMessagesForClient` section.

- 2023-06-26: `runOnRequirement.csfle` should check for crypt_shared and/or mongocryptd.

- 2023-06-13: **Schema version 1.15.**

    Add `databaseName` field to `CommandFailedEvent` and `CommandSucceededEvent`.

- 2023-05-26: **Schema version 1.14.**

    Add `topologyDescriptionChangedEvent`.

- 2023-05-17: Add `runCursorCommand` and `createCommandCursor` operations. Added `commandCursor` entity type which can
    be used with existing cursor operations.

- 2023-05-12: Deprecate "sharded-replicaset" topology type. Note that server 3.6+ requires replica sets for shards,
    which is also relevant to load balanced topologies.

- 2023-04-13: Remove `readConcern` and `writeConcern` options from `runCommand` operation.

- 2023-02-24: Fix typo in the description of the `$$matchAsRoot` matching operator.

- 2022-10-17: Add description of a `close` operation for client entities.

- 2022-10-14: **Schema version 1.13.**

    Add support for logging assertions via the `observeLogMessages` field for client entities, along with a new top-level
    field `expectLogMessages` containing `expectedLogMessagesForClient` objects. Add new special matching operators to
    enable command logging assertions, `$$matchAsDocument` and `$$matchAsRoot`.

- 2022-10-14: **Schema version 1.12.**

    Add `errorResponse` to `expectedError`.

- 2022-10-05: Remove spec front matter, add "Current Schema Version" field, and reformat changelog. Add comment to
    remind editors to note schema version bumps in changelog updates (where applicable).

- 2022-09-02: **Schema version 1.11.**

    Add `interruptInUseConnections` field to `poolClearedEvent`

- 2022-07-28: **Schema version 1.10.**

    Add support for `thread` entities (`runOnThread`, `waitForThread`), TopologyDescription entities
    (`recordTopologyDescription`, `waitForPrimaryChange`, `assertTopologyType`), testRunner event assertion operations
    (`waitForEvent`, `assertEventCount`), expected SDAM events, and the `wait` operation.

- 2022-07-27: Retroactively note schema version bumps in the changelog and require doing so for future changes.

- 2022-07-11: Update [Future Work](#future-work) to reflect that support for ignoring extra observed events was added in
    schema version 1.7.

- 2022-06-16: Require server 4.2+ for `csfle: true`.

- 2022-05-10: Add reference to Client Side Encryption spec under
    [ClientEncryption Operations](#clientencryption-operations).

- 2022-04-27: **Schema version 1.9.**

    Added `createOptions` field to `initialData`, introduced a new `timeoutMS` field in `collectionOrDatabaseOptions`, and
    added an `isTimeoutError` field to `expectedError`. Also introduced the `createEntities` operation.

- 2022-04-27: **Schema version 1.8.**

    Add `runOnRequirement.csfle`.

- 2022-04-26: Add `clientEncryption` entity and `$$placeholder` syntax.

- 2022-04-22: Revise `useMultipleMongoses` and "Initializing the Test Runner" for Atlas Serverless URIs using a load
    balancer fronting a single proxy.

- 2022-03-01: **Schema version 1.7.**

    Add `ignoreExtraEvents` field to `expectedEventsForClient`.

- 2022-02-24: Rename Versioned API to Stable API

- 2021-08-30: **Schema version 1.6.**

    Add `hasServerConnectionId` field to `commandStartedEvent`, `commandSuccededEvent` and `commandFailedEvent`.

- 2021-08-30: Test runners may create an internal MongoClient for each mongos. Better clarify how internal MongoClients
    may be used. Clarify that drivers creating an internal MongoClient for each mongos should use those clients for
    `targetedFailPoint` operations.

- 2021-08-23: Allow `runOnRequirement` conditions to be evaluated in any order.

- 2021-08-09: Updated all existing schema files to require at least one element in `test.expectEvents` if specified.

- 2021-07-29: Note that events for sensitive commands will have redacted commands and replies when using
    `observeSensitiveCommands`, and how that affects conditionally sensitive commands such as `hello` and legacy hello.

- 2021-07-01: Note that `expectError.expectResult` should use `$$unsetOrMatches` when the result is optional.

- 2021-06-09: **Schema version 1.5.**

    Added an `observeSensitiveCommands` property to the `client` entity type.

- 2021-05-17: Ensure old JSON schema files remain in place

- 2021-04-19: **Schema version 1.4.**

    Introduce `serverless` [runOnRequirement](#runonrequirement).

- 2021-04-12: **Schema version 1.3.**

    Added a `FindCursor` entity type. Defined a set of cursor operations. Added an `auth` property to `runOnRequirements`
    and modified the `topologies` property to accept `load-balanced`. Added CMAP events to the possible event types for
    `expectedEvent`. Add `assertNumberConnectionsCheckedOut` operation. Add `ignoreResultAndError` operation option.

- 2021-04-08: List additional error codes that may be ignored when calling `killAllSessions` and note that the command
    should not be called when connected to Atlas.

- 2021-03-22: Split `serverApi` into its own section. Note types for `loop` operation arguments. Clarify how `loop`
    iterations are counted for `storeIterationsAsEntity`.

- 2021-03-10: Clarify that `observedAt` field measures time in seconds for `storeEventsAsEntities`.

- 2021-03-09: Clarify which components of a version string are relevant for comparisons.

- 2021-03-04: Change `storeEventsAsEntities` from a map to an array of `storeEventsAsEntity` objects.

- 2021-03-01: **Schema version 1.2.**

    Added `storeEventsAsEntities` option for client entities and `loop` operation, which is needed for Atlas Driver
    Testing.

- 2020-12-23: Clarify how JSON schema is renamed for new minor versions.

- 2020-11-06: **Schema version 1.1.**

    Added `serverApi` option for client entities, `_yamlAnchors` property to define values for later use in YAML tests,
    and `serverParameters` property for `runOnRequirements`.
