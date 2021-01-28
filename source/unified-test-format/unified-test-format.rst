===================
Unified Test Format
===================

:Spec Title: Unified Test Format
:Spec Version: 1.1.1
:Author: Jeremy Mikola
:Advisors: Prashant Mital, Isabel Atkinson, Thomas Reggi
:Status: Accepted
:Type: Standards
:Minimum Server Version: N/A
:Last Modified: 2020-12-23

.. contents::

--------

Abstract
========

This project defines a unified schema for YAML and JSON specification tests,
which run operations against a MongoDB deployment. By conforming various spec
tests to a single schema, drivers can implement a single test runner to execute
acceptance tests for multiple specifications, thereby reducing maintenance of
existing specs and implementation time for new specifications.


META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`__.

This document tends to use "SHOULD" more frequently than other specifications,
but mainly in the context of providing guidance on writing test files. This is
discussed in more detail in `Design Rationale`_.


Goals
=====

This test format can be used to define tests for the following specifications:

- `Change Streams <../change-streams/change-streams.rst>`__
- `Command Monitoring <../command-monitoring/command-monitoring.rst>`__
- `CRUD <../crud/crud.rst>`__
- `GridFS <../gridfs/gridfs-spec.rst>`__
- `Retryable Reads <../retryable-reads/retryable-reads.rst>`__
- `Retryable Writes <../retryable-writes/retryable-writes.rst>`__
- `Sessions <../sessions/driver-sessions.rst>`__
- `Transactions <../transactions/transactions.rst>`__
- `Convenient API for Transactions <../transactions-convenient-api/transactions-convenient-api.rst>`__

This is not an exhaustive list. Specifications that are known to not be
supported by this format may be discussed under `Future Work`_.


Specification
=============


Terms
-----

Entity
  Any object or value that is indexed by a unique name and stored in the
  `Entity Map`_. This will typically be a driver object (e.g. client, session)
  defined in `createEntities`_ but may also be a
  `saved operation result <operation_saveResultAsEntity_>`_. A exhaustive list
  of supported types is presented in `Supported Entity Types`_. Entities are
  referenced by name throughout the test file (e.g. `Entity Test Operations`_).

Internal MongoClient
  A MongoClient created specifically for use with internal test operations, such
  as inserting collection data before a test, performing special assertions
  during a test, or asserting collection data after a test.

Iterable
  This term is used by various specifications as the return type for operations
  that return a sequence of items, which may be iterated. For example, the CRUD
  spec uses this as the return value for ``find`` and permit API flexibility
  rather than stipulate that a cursor object be returned directly.


Schema Version
--------------

This specification and the `Test Format`_ follow
`semantic versioning <https://semver.org/>`__. The version is primarily used to
validate test files with a `JSON schema <https://json-schema.org/>`__ and also
allow test runners to determine whether a particular test file is supported.

New tests files SHOULD always be written using the latest major version of this
specification; however, test files SHOULD be conservative in the minor version
they specify (as noted in `schemaVersion`_).


JSON Schema Validation
~~~~~~~~~~~~~~~~~~~~~~

Each major version of this specification SHALL have one JSON schema, which will
correspond to its most recent minor version. When a new minor version is
introduced, the previous schema file for that major version SHALL be renamed.
For example: if an additive change is made to version 1.0 of the spec, the
``schema-1.0.json`` file will be renamed to ``schema-1.1.json`` and modified
accordingly.

A particular minor version MUST be capable of validating any and all test files
in that major version series up to and including the minor version. For example,
``schema-2.1.json`` should validate test files with `schemaVersion`_ "2.0" and
"2.1", but would not be expected to validate files specifying "1.0", "2.2", or
"3.0".

The JSON schema MUST remain consistent with the `Test Format`_ section. If and
when a new major version is introduced, the `Breaking Changes`_ section MUST be
updated and any JSON schema(s) for a previous major version(s) MUST remain
available so that older test files can still be validated.

`Ajv <https://ajv.js.org/>`__ MAY be used to programmatically validate both YAML
and JSON files using the JSON schema. The JSON schema MUST NOT use syntax that
is unsupported by this tool, which bears mentioning because there are multiple
versions of the
`JSON schema specification <https://json-schema.org/specification.html>`__.


Test Runner Support
~~~~~~~~~~~~~~~~~~~

Each test file defines a `schemaVersion`_, which test runners will use to
determine compatibility (i.e. whether and how the test file will be
interpreted). Test files are considered compatible with a test runner if their
`schemaVersion`_ is less than or equal to a supported version in the test
runner, given the same major version component. For example:

- A test runner supporting version 1.5.1 could execute test files with versions
  1.0 and 1.5 but *not* 1.6 and 2.0.
- A test runner supporting version 2.1 could execute test files with versions
  2.0 and 2.1 but *not* 1.0 and 1.5.
- A test runner supporting *both* versions 1.5.1 and 2.0 could execute test
  files with versions 1.4, 1.5, and 2.0, but *not* 1.6, 2.1, or 3.0.
- A test runner supporting version 2.0.1 could execute test files with versions
  2.0 and 2.0.1 but *not* 2.0.2 or 2.1. This example is provided for
  completeness, but test files SHOULD NOT need to refer to patch versions (as
  previously mentioned).

Test runners MUST NOT process incompatible files and MUST raise an error if they
encounter an incompatible file (as discussed in `Executing a Test File`_). Test
runners MAY support multiple schema versions (as demonstrated in the example
above).


Impact of Spec Changes on Schema Version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Backwards-breaking changes SHALL warrant a new major version. These changes
include, but are not limited to:

- Subtractive changes, such as removing a field, operation, or type of supported
  entity or event
- Changing an existing field from optional to required
- Introducing a new, required field in the test format
- Significant changes to test file execution (not BC)

Backwards-compatible changes SHALL warrant a new minor version. These changes
include, but are not limited to:

- Additive changes, such as a introducing a new `Special Test Operations`_ or
  type of supported entity or event
- Changing an existing field from required to optional
- Introducing a new, optional field in the test format
- Minor changes to test file execution (BC)

Small fixes and internal spec changes (e.g. grammar, adding clarifying text to
the spec) MAY warrant a new patch version; however, patch versions SHOULD NOT
alter the structure of the test format and thus SHOULD NOT be relevant to test
files (as noted in `schemaVersion`_).


Entity Map
----------

The entity map indexes arbitrary objects and values by unique names, so that
they can be referenced from test constructs (e.g.
`operation.object <operation_object_>`_). To ensure each test is executed in
isolation, test runners MUST NOT share entity maps between tests. Most entities
will be driver objects created by the `createEntities`_ directive during test
setup, but the entity map may also be modified during test execution via the
`operation.saveResultAsEntity <operation_saveResultAsEntity_>`_ directive.

Test runners MAY choose to implement the entity map in a fashion most suited to
their language, but implementations MUST enforce both uniqueness of entity names
and referential integrity when fetching an entity. Test runners MUST raise an
error if an attempt is made to store an entity with a name that already exists
in the map and MUST raise an error if an entity is not found for a name or is
found but has an unexpected type.

Consider the following examples::

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


Supported Entity Types
~~~~~~~~~~~~~~~~~~~~~~

Test runners MUST support the following types of entities:

- MongoClient. See `entity_client`_ and `Client Operations`_.
- Database. See `entity_database`_ and `Database Operations`_.
- Collection. See `entity_collection`_ and `Collection Operations`_
- ClientSession. See `entity_session`_ and `Session Operations`_.
- GridFS Bucket. See `entity_bucket`_ and `Bucket Operations`_.
- ChangeStream. See `ChangeStream Operations`_.
- All known BSON types and/or equivalent language types for the target driver.
  For the present version of the spec, the following BSON types are known:
  0x01-0x13, 0x7F, 0xFF.

  Tests SHOULD NOT utilize deprecated types (e.g. 0x0E: Symbol), since they may
  not be supported by all drivers and could yield runtime errors (e.g. while
  loading a test file with an Extended JSON parser).

This is an exhaustive list of supported types for the entity map. Test runners
MUST raise an error if an attempt is made to store an unsupported type in the
entity map.

Adding new entity types (including known BSON types) to this list will require
a minor version bump to the spec and schema version. Removing entity types will
require a major version bump. See `Impact of Spec Changes on Schema Version`_
for more information.


Test Format
-----------

Each specification test file can define one or more tests, which inherit some
top-level configuration (e.g. namespace, initial data). YAML and JSON test files
are parsed as an object by the test runner. This section defines the top-level
keys for that object and links to various sub-sections for definitions of
nested structures (e.g. individual `test`_, `operation`_).

Although test runners are free to process YAML or JSON files, YAML is the
canonical format for writing tests. YAML files may be converted to JSON using a
tool such as `js-yaml <https://github.com/nodeca/js-yaml>`__ .


Top-level Fields
~~~~~~~~~~~~~~~~

The top-level fields of a test file are as follows:

- ``description``: Required string. The name of the test file.

  This SHOULD describe the common purpose of tests in this file and MAY refer to
  the filename (e.g. "updateOne-hint").

.. _schemaVersion:

- ``schemaVersion``: Required string. Version of this specification with which
  the test file complies.

  Test files SHOULD be conservative when specifying a schema version. For
  example, if the latest schema version is 1.1 but the test file complies with
  schema version 1.0, the test file should specify 1.0.

  Test runners will use this to determine compatibility (i.e. whether and how
  the test file will be interpreted). The format of this string is defined in
  `Version String`_; however, test files SHOULD NOT need to refer to specific
  patch versions since patch-level changes SHOULD NOT alter the structure of the
  test format (as previously noted in `Schema Version`_).

.. _runOnRequirements:

- ``runOnRequirements``: Optional array of one or more `runOnRequirement`_
  objects. List of server version and/or topology requirements for which the
  tests in this file can be run. If no requirements are met, the test runner
  MUST skip this test file.

.. _createEntities:

- ``createEntities``: Optional array of one or more `entity`_ objects. List of
  entities (e.g. client, collection, session objects) that SHALL be created
  before each test case is executed.

  Test files SHOULD define entities in dependency order, such that all
  referenced entities (e.g. client) are defined before any of their dependent
  entities (e.g. database, session).

.. _initialData:

- ``initialData``: Optional array of one or more `collectionData`_ objects. Data
  that will exist in collections before each test case is executed.

  Before each test and for each `collectionData`_, the test runner MUST drop the
  collection and insert the specified documents (if any) using a "majority"
  write concern. If no documents are specified, the test runner MUST create the
  collection with a "majority" write concern.

.. _tests:

- ``tests``: Required array of one or more `test`_ objects. List of test cases
  to be executed independently of each other.

.. _yamlAnchors

- ``_yamlAnchors``: Optional object containing arbitrary data. This is only used
  to define anchors within the YAML files and MUST NOT be used by test runners.


runOnRequirement
~~~~~~~~~~~~~~~~

A combination of server version and/or topology requirements for running the
test(s).

The format of server version strings is defined in `Version String`_. When
comparing server version strings, each component SHALL be compared numerically.
For example, "4.0.10" is greater than "4.0.9" and "3.6" and less than "4.2.0".

The structure of this object is as follows:

- ``minServerVersion``: Optional string. The minimum server version (inclusive)
  required to successfully run the tests. If this field is omitted, there is no
  lower bound on the required server version. The format of this string is
  defined in `Version String`_.

- ``maxServerVersion``: Optional string. The maximum server version (inclusive)
  against which the tests can be run successfully. If this field is omitted,
  there is no upper bound on the required server version. The format of this
  string is defined in `Version String`_.

- ``topologies``: Optional array of one or more strings. Server topologies
  against which the tests can be run successfully. Valid topologies are
  "single", "replicaset", "sharded", and "sharded-replicaset" (i.e. sharded
  cluster backed by replica sets). If this field is omitted, there is no
  topology requirement for the test.

  When matching a "sharded-replicaset" topology, test runners MUST ensure that
  all shards are backed by a replica set. The process for doing so is described
  in `Determining if a Sharded Cluster Uses Replica Sets`_. When matching a
  "sharded" topology, test runners MUST accept any type of sharded cluster (i.e.
  "sharded" implies "sharded-replicaset", but not vice versa).

- ``serverParameters``: Optional object of server parameters to check against.
  To check server parameters, drivers send a
  ``{ getParameter: 1, <parameter>: 1 }`` command to the server using the
  internal MongoClient. Drivers MAY also choose to send a
  ``{ getParameter: '*' }`` command and fetch all parameters at once. The result
  SHOULD be cached to avoid repeated calls to fetch the same parameter. Test
  runners MUST apply the rules specified in `Flexible Numeric Comparisons`_ when
  comparing values. If a server does not support a parameter, test runners MUST
  treat the comparison as not equal and skip the test. This includes errors that
  occur when fetching a single parameter using ``getParameter``.

Test runners MUST evaluate these conditions in the order specified above.

entity
~~~~~~

An entity (e.g. client, collection, session object) that will be created in the
`Entity Map`_ before each test is executed.

This object MUST contain **exactly one** top-level key that identifies the
entity type and maps to a nested object, which specifies a unique name for the
entity (``id`` key) and any other parameters necessary for its construction.
Tests SHOULD use sequential names based on the entity type (e.g. "session0",
"session1").

When defining an entity object in YAML, a `node anchor`_ SHOULD be created on
the entity's ``id`` key. This anchor will allow the unique name to be referenced
with an `alias node`_ later in the file (e.g. from another entity or
`operation`_ document) and also leverage YAML's parser for reference validation.

.. _node anchor: https://yaml.org/spec/1.2/spec.html#id2785586
.. _alias node: https://yaml.org/spec/1.2/spec.html#id2786196

The structure of this object is as follows:

.. _entity_client:

- ``client``: Optional object. Defines a MongoClient object.

  The structure of this object is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor`_ for this field (e.g. ``id: &client0 client0``).

  - ``uriOptions``: Optional object. Additional URI options to apply to the
    test suite's connection string that is used to create this client. Any keys
    in this object MUST override conflicting keys in the connection string.

    Documentation for supported options may be found in the
    `URI Options <../uri-options/uri-options.rst>`__ spec, with one notable
    exception: if ``readPreferenceTags`` is specified in this object, the key
    will map to an array of strings, each representing a tag set, since it is
    not feasible to define multiple ``readPreferenceTags`` keys in the object.

  .. _entity_client_useMultipleMongoses:

  - ``useMultipleMongoses``: Optional boolean. If true and the topology is a
    sharded cluster, the test runner MUST assert that this MongoClient connects
    to multiple mongos hosts (e.g. by inspecting the connection string). If
    false and the topology is a sharded cluster, the test runner MUST ensure
    that this MongoClient connects to only a single mongos host (e.g. by
    modifying the connection string).

    If this option is not specified and the topology is a sharded cluster, the
    test runner MUST NOT enforce any limit on the number of mongos hosts in the
    connection string and any tests using this client SHOULD NOT depend on a
    particular number of mongos hosts.

    This option SHOULD be set to true if the resulting entity is used to
    conduct transactions against a sharded cluster. This is advised because
    connecting to multiple mongos servers is necessary to test session
    pinning.

    This option has no effect for non-sharded topologies.

  .. _entity_client_observeEvents:

  - ``observeEvents``: Optional array of one or more strings. Types of events
    that can be observed for this client. Unspecified event types MUST be
    ignored by this client's event listeners and SHOULD NOT be included in
    `test.expectEvents <test_expectEvents_>`_ for this client.

    Test files SHOULD NOT observe events from multiple specs (e.g. command
    monitoring *and* SDAM events) for a single client. See
    `Mixing event types in observeEvents and expectEvents`_ for more
    information.

    Supported types correspond to the top-level keys (strings) documented in
    `expectedEvent`_ and are as follows:

    - `commandStartedEvent <expectedEvent_commandStartedEvent_>`_

    - `commandSucceededEvent <expectedEvent_commandSucceededEvent_>`_

    - `commandFailedEvent <expectedEvent_commandFailedEvent_>`_

  .. _entity_client_ignoreCommandMonitoringEvents:

  - ``ignoreCommandMonitoringEvents``: Optional array of one or more strings.
    Command names for which the test runner MUST ignore any observed command
    monitoring events. The command(s) will be ignored in addition to
    ``configureFailPoint`` and any commands containing sensitive information
    (per the
    `Command Monitoring <../command-monitoring/command-monitoring.rst#security>`__
    spec).

    Test files SHOULD NOT use this option unless one or more command monitoring
    events are specified in `observeEvents <entity_client_observeEvents_>`_.
    
  - ``storeEventsAsEntities``: Optional map of event names to entity names.
    If provided the test runner MUST:
    
      - For each entity name, create the respective entity with a type of
        "event list". If multiple event names map to the same entity name,
        exactly one entity MUST be created. If the entity already exists
        (such as from a previous ``storeEventsAsEntities`` declaration from
        another client), the test runner MUST raise an error.
      - Set up an event subscriber for each event named. The event subscriber
        MUST serialize the events it receives into a document and append
        the document to the array stored in the specified entity.
        The fields in the document MUST be as follows:
        
        - For ``CommandStartedEvent``:
       
          - ``name``: the name of the event, i.e. ``CommandStartedEvent``.
          - ``commandName``: the name of the command, e.g. ``insert``.
          - ``startTime``: the (floating-point) number of seconds since
            the Unix epoch when the command began executing.
          - ``address``: the address of the server to which the command
             was sent, e.g. ``localhost:27017``.
        
        - For ``CommandSucceededEvent``:
       
          - ``name``: the name of the event, i.e. ``CommandSucceededEvent``.
          - ``commandName``: the name of the command, e.g. ``insert``.
          - ``duration``: the time, in (floating-point) seconds, it took for
            the command to execute.
          - ``startTime``: the (floating-point) number of seconds since
            the Unix epoch when the command began executing.
          - ``address``: the address of the server to which the command
             was sent, e.g. ``localhost:27017``.
        
        - For ``CommandFailedEvent``:
       
          - ``name``: the name of the event, i.e. ``CommandFailedEvent``.
          - ``commandName``: the name of the command, e.g. ``insert``.
          - ``duration``: the time, in (floating-point) seconds, it took for
            the command to execute.
          - ``failure``: this field MUST contain a textual description
             of the error encountered while executing the command.
          - ``startTime``: the (floating-point) number of seconds since
            the Unix epoch when the command began executing.
          - ``address``: the address of the server to which the command
             was sent, e.g. ``localhost:27017``.
             
        - For connection pool events (``PoolCreatedEvent``,
          ``PoolReadyEvent``, ``PoolClearedEvent``, ``PoolClosedEvent``):
               
          - ``name``: the name of the event, e.g. ``PoolCreatedEvent``.
          - ``time``: the (floating-point) number of seconds since the
            Unix epoch when the event was published.
          - ``address``: the address of the server that the command was
            published for, e.g. ``localhost:27017``.
        
        - For connnection events (``ConnectionCreatedEvent``,
          ``ConnectionReadyEvent``, ``ConnectionClosedEvent``,
          ``ConnectionCheckOutStartedEvent``, ``ConnectionCheckOutFailedEvent``,
          ``ConnectionCheckedOutEvent``, ``ConnectionCheckedInEvent``):
               
          - ``name``: the name of the event, e.g. ``ConnectionCreatedEvent``.
          - ``time``: the (floating-point) number of seconds since the
            Unix epoch when the event was published.
          - ``address``: the address of the server that the command was
            published for, e.g. ``localhost:27017``.
          - ``connectionId``: the identifier for the connection for which
            the event was published.
          - ``reason``: a textual reason for why the event was published
            (if defined by the CMAP specification for the respective event;
            ``ConnectionClosedEvent`` and ``ConnectionCheckOutFailedEvent``
            are specified to have the ``reason`` field).

  - ``serverApi``: Optional object to declare an API version on the client
    entity. A ``version`` string is required, and test runners MUST fail if the
    given version string is not supported by the driver. The ``strict`` and
    ``deprecationErrors`` members take an optional boolean that is passed to the
    ``ServerApi`` object. See the
    `Versioned API <../versioned-api/versioned-api.rst>`__ spec for more details
    on these fields.

.. _entity_database:

- ``database``: Optional object. Defines a Database object.

  The structure of this object is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor`_ for this field (e.g. ``id: &database0 database0``).

  - ``client``: Required string. Client entity from which this database will be
    created. The YAML file SHOULD use an `alias node`_ for a client entity's
    ``id`` field (e.g. ``client: *client0``).

  - ``databaseName``: Required string. Database name. The YAML file SHOULD
    define a `node anchor`_ for this field (e.g.
    ``databaseName: &database0Name foo``).

  - ``databaseOptions``: Optional `collectionOrDatabaseOptions`_ object.

.. _entity_collection:

- ``collection``: Optional object. Defines a Collection object.

  The structure of this object is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor`_ for this field (e.g.
    ``id: &collection0 collection0``).

  - ``database``: Required string. Database entity from which this collection
    will be created. The YAML file SHOULD use an `alias node`_ for a database
    entity's ``id`` field (e.g. ``database: *database0``).

  - ``collectionName``: Required string. Collection name. The YAML file SHOULD
    define a `node anchor`_ for this field (e.g.
    ``collectionName: &collection0Name foo``).

  - ``collectionOptions``: Optional `collectionOrDatabaseOptions`_ object.

.. _entity_session:

- ``session``: Optional object. Defines an explicit ClientSession object.

  The structure of this object is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor`_ for this field (e.g. ``id: &session0 session0``).

  - ``client``: Required string. Client entity from which this session will be
    created. The YAML file SHOULD use an `alias node`_ for a client entity's
    ``id`` field (e.g. ``client: *client0``).

  - ``sessionOptions``: Optional object. Map of parameters to pass to
    `MongoClient.startSession <../sessions/driver-sessions.rst#startsession>`__
    when creating the session. Supported options are defined in the following
    specifications:

    - `Causal Consistency <../causal-consistency/causal-consistency.rst#sessionoptions-changes>`__
    - `Transactions <../transactions/transactions.rst#sessionoptions-changes>`__

    When specifying TransactionOptions for ``defaultTransactionOptions``, the
    transaction options MUST remain nested under ``defaultTransactionOptions``
    and MUST NOT be flattened into ``sessionOptions``.

.. _entity_bucket:

- ``bucket``: Optional object. Defines a Bucket object, as defined in the
  `GridFS <../gridfs/gridfs-spec.rst>`__ spec.

  The structure of this object is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor`_ for this field (e.g. ``id: &bucket0 bucket0``).

  - ``database``: Required string. Database entity from which this bucket will
    be created. The YAML file SHOULD use an `alias node`_ for a database
    entity's ``id`` field (e.g. ``database: *database0``).

  - ``bucketOptions``: Optional object. Additional options used to construct
    the bucket object. Supported options are defined in the
    `GridFS <../gridfs/gridfs-spec.rst#configurable-gridfsbucket-class>`__
    specification. The ``readConcern``, ``readPreference``, and ``writeConcern``
    options use the same structure as defined in `Common Options`_.


collectionData
~~~~~~~~~~~~~~

List of documents corresponding to the contents of a collection. This structure
is used by both `initialData`_ and `test.outcome <test_outcome_>`_, which insert
and read documents, respectively.

The structure of this object is as follows:

- ``collectionName``: Required string. See `commonOptions_collectionName`_.

- ``databaseName``: Required string. See `commonOptions_databaseName`_.

- ``documents``: Required array of objects. List of documents corresponding to
  the contents of the collection. This list may be empty.


test
~~~~

Test case consisting of a sequence of operations to be executed.

The structure of this object is as follows:

- ``description``: Required string. The name of the test.

  This SHOULD describe the purpose of this test (e.g. "insertOne is retried").

.. _test_runOnRequirements:

- ``runOnRequirements``: Optional array of one or more `runOnRequirement`_
  objects. List of server version and/or topology requirements for which this
  test can be run. If specified, these requirements are evaluated independently
  and in addition to any top-level `runOnRequirements`_. If no requirements in
  this array are met, the test runner MUST skip this test.

  These requirements SHOULD be more restrictive than those specified in the
  top-level `runOnRequirements`_ (if any) and SHOULD NOT be more permissive.
  This is advised because both sets of requirements MUST be satisified in order
  for a test to be executed and more permissive requirements at the test-level
  could be taken out of context on their own.

.. _test_skipReason:

- ``skipReason``: Optional string. If set, the test will be skipped. The string
  SHOULD explain the reason for skipping the test (e.g. JIRA ticket).

.. _test_operations:

- ``operations``: Required array of one or more `operation`_ objects. List of
  operations to be executed for the test case.

.. _test_expectEvents:

- ``expectEvents``: Optional array of one or more `expectedEventsForClient`_
  objects. For one or more clients, a list of events that are expected to be
  observed in a particular order.

  If a driver only supports configuring event listeners globally (for all
  clients), the test runner SHOULD associate each observed event with a client
  in order to perform these assertions.

  Test files SHOULD NOT expect events from multiple specs (e.g. command
  monitoring *and* SDAM events) for a single client. See
  `Mixing event types in observeEvents and expectEvents`_ for more
  information.

.. _test_outcome:

- ``outcome``: Optional array of one or more `collectionData`_ objects. Data
  that is expected to exist in collections after each test case is executed.

  The list of documents herein SHOULD be sorted ascendingly by the ``_id`` field
  to allow for deterministic comparisons. The procedure for asserting collection
  contents is discussed in `Executing a Test`_.


operation
~~~~~~~~~

An operation to be executed as part of the test.

The structure of this object is as follows:

.. _operation_name:

- ``name``: Required string. Name of the operation (e.g. method) to perform on
  the object.

.. _operation_object:

- ``object``: Required string. Name of the object on which to perform the
  operation. This SHOULD correspond to either an `entity`_ name (for
  `Entity Test Operations`_) or "testRunner" (for `Special Test Operations`_).
  If the object is an entity, The YAML file SHOULD use an `alias node`_ for its
  ``id`` field (e.g. ``object: *collection0``).

.. _operation_arguments:

- ``arguments``: Optional object. Map of parameter names and values for the
  operation. The structure of this object will vary based on the operation.
  See `Entity Test Operations`_ and `Special Test Operations`_.

  The ``session`` parameter is handled specially (see `commonOptions_session`_).

.. _operation_expectError:

- ``expectError``: Optional `expectedError`_ object. One or more assertions for
  an error expected to be raised by the operation.

  This field is mutually exclusive with
  `expectResult <operation_expectResult_>`_ and
  `saveResultAsEntity <operation_saveResultAsEntity_>`_.

  This field SHOULD NOT be used for `Special Test Operations`_ (i.e.
  ``object: testRunner``).

.. _operation_expectResult:

- ``expectResult``: Optional mixed type. A value corresponding to the expected
  result of the operation. This field may be a scalar value, a single document,
  or an array of values. Test runners MUST follow the rules in
  `Evaluating Matches`_ when processing this assertion.

  This field is mutually exclusive with `expectError <operation_expectError_>`_.

  This field SHOULD NOT be used for `Special Test Operations`_ (i.e.
  ``object: testRunner``).

.. _operation_saveResultAsEntity:

- ``saveResultAsEntity``: Optional string. If specified, the actual result
  returned by the operation (if any) will be saved with this name in the
  `Entity Map`_.  The test runner MUST raise an error if the name is already in
  use or if the result does not comply with `Supported Entity Types`_.

  This field is mutually exclusive with `expectError <operation_expectError_>`_.

  This field SHOULD NOT be used for `Special Test Operations`_ (i.e.
  ``object: testRunner``).


expectedError
~~~~~~~~~~~~~

One or more assertions for an error/exception, which is expected to be raised by
an executed operation. At least one key is required in this object.

The structure of this object is as follows:

- ``isError``: Optional boolean. If true, the test runner MUST assert that an
  error was raised. This is primarily used when no other error assertions apply
  but the test still needs to assert an expected error. Test files MUST NOT
  specify false, as `expectedError`_ is only applicable when an operation is
  expected to raise an error.

- ``isClientError``: Optional boolean. If true, the test runner MUST assert that
  the error originates from the client (i.e. it is not derived from a server
  response). If false, the test runner MUST assert that the error does not
  originate from the client.

  Client errors include, but are not limited to: parameter validation errors
  before a command is sent to the server; network errors.

- ``errorContains``: Optional string. A substring of the expected error message
  (e.g. "errmsg" field in a server error document). The test runner MUST assert
  that the error message contains this string using a case-insensitive match.

  See `bulkWrite`_ for special considerations for BulkWriteExceptions.

- ``errorCode``: Optional integer. The expected "code" field in the
  server-generated error response. The test runner MUST assert that the error
  includes a server-generated response whose "code" field equals this value.
  In the interest of readability, YAML files SHOULD use a comment to note the
  corresponding code name (e.g. ``errorCode: 26 # NamespaceNotFound``).

  Server error codes are defined in
  `error_codes.yml <https://github.com/mongodb/mongo/blob/master/src/mongo/base/error_codes.yml>`__.

  Test files SHOULD NOT assert error codes for client errors, as specifications
  do not define standardized codes for client errors.

- ``errorCodeName``: Optional string. The expected "codeName" field in the
  server-generated error response. The test runner MUST assert that the error
  includes a server-generated response whose "codeName" field equals this value
  using a case-insensitive comparison.

  See `bulkWrite`_ for special considerations for BulkWriteExceptions.

  Server error codes are defined in
  `error_codes.yml <https://github.com/mongodb/mongo/blob/master/src/mongo/base/error_codes.yml>`__.

  Test files SHOULD NOT assert error codes for client errors, as specifications
  do not define standardized codes for client errors.

- ``errorLabelsContain``: Optional array of one or more strings. A list of error
  label strings that the error is expected to have. The test runner MUST assert
  that the error contains all of the specified labels (e.g. using the
  ``hasErrorLabel`` method).

- ``errorLabelsOmit``: Optional array of one or more strings. A list of error
  label strings that the error is expected not to have. The test runner MUST
  assert that the error does not contain any of the specified labels (e.g. using
  the ``hasErrorLabel`` method).

.. _expectedError_expectResult:

- ``expectResult``: Optional mixed type. This field follows the same rules as
  `operation.expectResult <operation_expectResult_>`_ and is only used in cases
  where the error includes a result (e.g. `bulkWrite`_). If specified, the test
  runner MUST assert that the error includes a result and that it matches this
  value.


expectedEventsForClient
~~~~~~~~~~~~~~~~~~~~~~~

A list of events that are expected to be observed (in that order) for a client
while executing `operations <test_operations_>`_.

The structure of each object is as follows:

- ``client``: Required string. Client entity on which the events are expected
  to be observed. See `commonOptions_client`_.

- ``events``: Required array of `expectedEvent`_ objects. List of events, which
  are expected to be observed (in this order) on the corresponding client while
  executing `operations`_. If the array is empty, the test runner MUST assert
  that no events were observed on the client (excluding ignored events).


expectedEvent
~~~~~~~~~~~~~

An event (e.g. APM), which is expected to be observed while executing the test's
operations.

This object MUST contain **exactly one** top-level key that identifies the
event type and maps to a nested object, which contains one or more assertions
for the event's properties.

Some event properties are omitted in the following structures because they
cannot be reliably tested. Taking command monitoring events as an example,
``requestId`` and ``operationId`` are nondeterministic and types for
``connectionId`` and ``failure`` can vary by implementation.

The structure of this object is as follows:

.. _expectedEvent_commandStartedEvent:

- ``commandStartedEvent``: Optional object. Assertions for one or more
  `CommandStartedEvent <../command-monitoring/command-monitoring.rst#api>`__
  fields.

  The structure of this object is as follows:

  - ``command``: Optional document. A value corresponding to the expected
    command document. Test runners MUST follow the rules in
    `Evaluating Matches`_ when processing this assertion.

  - ``commandName``: Optional string. Test runners MUST assert that the command
    name matches this value.

  - ``databaseName``: Optional string. Test runners MUST assert that the
    database name matches this value. The YAML file SHOULD use an `alias node`_
    for this value (e.g. ``databaseName: *database0Name``).

.. _expectedEvent_commandSucceededEvent:

- ``commandSucceededEvent``: Optional object. Assertions for one or more
  `CommandSucceededEvent <../command-monitoring/command-monitoring.rst#api>`__
  fields.

  The structure of this object is as follows:

  - ``reply``: Optional document. A value corresponding to the expected
    reply document. Test runners MUST follow the rules in `Evaluating Matches`_
    when processing this assertion.

  - ``commandName``: Optional string. Test runners MUST assert that the command
    name matches this value.

.. _expectedEvent_commandFailedEvent:

- ``commandFailedEvent``: Optional object. Assertions for one or more
  `CommandFailedEvent <../command-monitoring/command-monitoring.rst#api>`__
  fields.

  The structure of this object is as follows:

  - ``commandName``: Optional string. Test runners MUST assert that the command
    name matches this value.


collectionOrDatabaseOptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Map of parameters used to construct a collection or database object.

The structure of this object is as follows:

  - ``readConcern``: Optional object. See `commonOptions_readConcern`_.

  - ``readPreference``: Optional object. See `commonOptions_readPreference`_.

  - ``writeConcern``: Optional object. See `commonOptions_writeConcern`_.


Common Options
--------------

This section defines the structure of common options that are referenced from
various contexts in the test format. Comprehensive documentation for some of
these types and their parameters may be found in the following specifications:

- `Read and Write Concern <../read-write-concern/read-write-concern.rst>`__.
- `Server Selection: Read Preference <../server-selection/server-selection.rst#read-preference>`__.

The structure of these common options is as follows:

.. _commonOptions_collectionName:

- ``collectionName``: String. Collection name. The YAML file SHOULD use an
  `alias node`_ for a collection entity's ``collectionName`` field (e.g.
  ``collectionName: *collection0Name``).

.. _commonOptions_databaseName:

- ``databaseName``: String. Database name. The YAML file SHOULD use an
  `alias node`_ for a database entity's ``databaseName`` field (e.g.
  ``databaseName: *database0Name``).

.. _commonOptions_readConcern:

- ``readConcern``: Object. Map of parameters to construct a read concern.

  The structure of this object is as follows:

  - ``level``: Required string.

.. _commonOptions_readPreference:

- ``readPreference``: Object. Map of parameters to construct a read
  preference.

  The structure of this object is as follows:

  - ``mode``: Required string.

  - ``tagSets``: Optional array of objects.

  - ``maxStalenessSeconds``: Optional integer.

  - ``hedge``: Optional object.

.. _commonOptions_client:

- ``client``: String. Client entity name, which the test runner MUST resolve
  to a MongoClient object. The YAML file SHOULD use an `alias node`_ for a
  client entity's ``id`` field (e.g. ``client: *client0``).

.. _commonOptions_session:

- ``session``: String. Session entity name, which the test runner MUST resolve
  to a ClientSession object. The YAML file SHOULD use an `alias node`_ for a
  session entity's ``id`` field (e.g. ``session: *session0``).

.. _commonOptions_writeConcern:

- ``writeConcern``: Object. Map of parameters to construct a write concern.

  The structure of this object is as follows:

  - ``journal``: Optional boolean.

  - ``w``: Optional integer or string.

  - ``wtimeoutMS``: Optional integer.


Version String
--------------

Version strings, which are used for `schemaVersion`_ and `runOnRequirement`_,
MUST conform to one of the following formats, where each component is a
non-negative integer:

- ``<major>.<minor>.<patch>``
- ``<major>.<minor>`` (``<patch>`` is assumed to be zero)
- ``<major>`` (``<minor>`` and ``<patch>`` are assumed to be zero)


Entity Test Operations
----------------------

Entity operations correspond to an API method on a driver object. If
`operation.object <operation_object_>`_ refers to an `entity`_ name (e.g.
"collection0") then `operation.name <operation_name_>`_ is expected to reference
an API method on that class.

Test files SHALL use camelCase when referring to API methods and parameters,
even if the defining specifications use other forms (e.g. snake_case in GridFS).

This spec does not provide exhaustive documentation for all possible API methods
that may appear in a test; however, the following sections discuss all supported
entities and their operations in some level of detail. Special handling for
certain operations is also discussed as needed.


Expressing Required and Optional Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some specifications group optional parameters for API methods under an
``options`` parameter (e.g. ``options: Optional<UpdateOptions>`` in the CRUD
spec); however, driver APIs vary in how they accept options (e.g. Python's
keyword/named arguments, ``session`` as either an option or required parameter
depending on whether a language supports method overloading). Therefore, test
files SHALL declare all required and optional parameters for an API method
directly within `operation.arguments <operation_arguments_>`_ (e.g. ``upsert``
for ``updateOne`` is *not* nested under an ``options`` key).


Special Handling for Arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If ``session`` is specified in `operation.arguments`_, it is defined according
to `commonOptions_session`_. Test runners MUST resolve the ``session`` argument
to `session <entity_session_>`_ entity *before* passing it as a parameter to any
API method.

If ``readConcern``, ``readPreference``, or ``writeConcern`` are specified in
`operation.arguments`_, test runners MUST interpret them according to the
corresponding definition in `Common Options`_ and MUST convert the value into
the appropriate object *before* passing it as a parameter to any API method.


Converting Returned Model Objects to Documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For operations that return a model object (e.g. ``BulkWriteResult`` for
``bulkWrite``), the test runner MUST convert the model object to a document when
evaluating `expectResult <operation_expectResult_>`_ or
`saveResultAsEntity <operation_saveResultAsEntity_>`_. Similarly, for operations
that may return iterables of model objects (e.g. ``DatabaseInfo`` for
``listDatabases``), the test runner MUST convert the iterable to an array of
documents when evaluating `expectResult`_ or `saveResultAsEntity`_.


Iterating Returned Iterables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unless otherwise stated by an operation below, test runners MUST fully iterate
any iterable returned by an operation as part of that operation's execution.
This is necessary to ensure consistent behavior among drivers, as discussed in
`collection_aggregate`_ and `find`_, and also ensures that error and event
assertions can be evaluated consistently.


Client Operations
-----------------

These operations and their arguments may be documented in the following
specifications:

- `Change Streams <../change-streams/change-streams.rst>`__
- `Enumerating Databases <../enumerate-databases.rst>`__

Client operations that require special handling or are not documented by an
existing specification are described below.


.. _client_createChangeStream:

createChangeStream
~~~~~~~~~~~~~~~~~~

Creates a cluster-level change stream and ensures that the server-side cursor
has been created.

This operation proxies the client's ``watch`` method and supports the same
arguments and options. Test files SHOULD NOT use the client's ``watch``
operation directly for reasons discussed in `ChangeStream Operations`_. Test
runners MUST ensure that the server-side cursor is created (i.e. ``aggregate``
is executed) as part of this operation and before the resulting change stream
might be saved with
`operation.saveResultAsEntity <operation_saveResultAsEntity_>`_.

Test runners MUST NOT iterate the change stream when executing this operation
and test files SHOULD NOT specify
`operation.expectResult <operation_expectResult_>`_ for this operation.


watch
~~~~~

This operation SHOULD NOT be used in test files. See
`client_createChangeStream`_.


Database Operations
-------------------

These operations and their arguments may be documented in the following
specifications:

- `Change Streams <../change-streams/change-streams.rst>`__
- `CRUD <../crud/crud.rst>`__
- `Enumerating Collections <../enumerate-collections.rst>`__

Database operations that require special handling or are not documented by an
existing specification are described below.

.. _database_aggregate:

aggregate
~~~~~~~~~

When executing an ``aggregate`` operation, the test runner MUST fully iterate
the result. This will ensure consistent behavior between drivers that eagerly
create a server-side cursor and those that do so lazily when iteration begins.


.. _database_createChangeStream:

createChangeStream
~~~~~~~~~~~~~~~~~~

Creates a database-level change stream and ensures that the server-side cursor
has been created.

This operation proxies the database's ``watch`` method and supports the same
arguments and options. Test files SHOULD NOT use the database's ``watch``
operation directly for reasons discussed in `ChangeStream Operations`_. Test
runners MUST ensure that the server-side cursor is created (i.e. ``aggregate``
is executed) as part of this operation and before the resulting change stream
might be saved with
`operation.saveResultAsEntity <operation_saveResultAsEntity_>`_.

Test runners MUST NOT iterate the change stream when executing this operation
and test files SHOULD NOT specify
`operation.expectResult <operation_expectResult_>`_ for this operation.


runCommand
~~~~~~~~~~

Generic command runner.

This method does not inherit a read concern or write concern (per the
`Read and Write Concern <../read-write-concern/read-write-concern.rst#generic-command-method>`__
spec), nor does it inherit a read preference (per the
`Server Selection <../server-selection/server-selection.rst#use-of-read-preferences-with-commands>`__
spec); however, they may be specified as arguments.

The following arguments are supported:

- ``command``: Required document. The command to be executed.

- ``commandName``: Required string. The name of the command to run. This is used
  by languages that are unable preserve the order of keys in the ``command``
  argument when parsing YAML/JSON.

- ``readConcern``: Optional object. See `commonOptions_readConcern`_.

- ``readPreference``: Optional object. See `commonOptions_readPreference`_.

- ``session``: Optional string. See `commonOptions_session`_.

- ``writeConcern``: Optional object. See `commonOptions_writeConcern`_.


watch
~~~~~

This operation SHOULD NOT be used in test files. See
`database_createChangeStream`_.


Collection Operations
---------------------

These operations and their arguments may be documented in the following
specifications:

- `Change Streams <../change-streams/change-streams.rst>`__
- `CRUD <../crud/crud.rst>`__
- `Enumerating Indexes <../enumerate-indexes.rst>`__
- `Index Management <../index-management.rst>`__

Collection operations that require special handling or are not documented by an
existing specification are described below.

.. _collection_aggregate:

aggregate
~~~~~~~~~

When executing an ``aggregate`` operation, the test runner MUST fully iterate
the result. This will ensure consistent behavior between drivers that eagerly
create a server-side cursor and those that do so lazily when iteration begins.


bulkWrite
~~~~~~~~~

The ``requests`` parameter for ``bulkWrite`` is documented as a list of
WriteModel interfaces. Each WriteModel implementation (e.g. InsertOneModel)
provides important context to the method, but that type information is not
easily expressed in YAML and JSON. To account for this, test files MUST nest
each WriteModel object in a single-key object, where the key identifies the
request type (e.g. "insertOne") and its value is an object expressing the
parameters, as in the following example::

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

Because the ``insertedIds`` field of BulkWriteResult is optional for drivers to
implement, assertions for that field SHOULD utilize the `$$unsetOrMatches`_
operator.

While operations typically raise an error *or* return a result, the
``bulkWrite`` operation is unique in that it may report both via the
``writeResult`` property of a BulkWriteException. In this case, the intermediary
write result may be matched with `expectedError_expectResult`_. Because
``writeResult`` is optional for drivers to implement, such assertions SHOULD
utilize the `$$unsetOrMatches`_ operator.

Additionally, BulkWriteException is unique in that it aggregates one or more
server errors in its ``writeConcernError`` and ``writeErrors`` properties.
When test runners evaluate `expectedError`_ assertions for ``errorContains`` and
``errorCodeName``, they MUST examine the aggregated errors and consider any
match therein to satisfy the assertion(s). Drivers that concatenate all write
and write concern error messages into the BulkWriteException message MAY
optimize the check for ``errorContains`` by examining the concatenated message.
Drivers that expose ``code`` but not ``codeName`` through BulkWriteException MAY
translate the expected code name to a number (see:
`error_codes.yml <https://github.com/mongodb/mongo/blob/master/src/mongo/base/error_codes.yml>`__)
and compare with ``code`` instead, but MUST raise an error if the comparison
cannot be attempted (e.g. ``code`` is also not available, translation fails).


.. _collection_createChangeStream:

createChangeStream
~~~~~~~~~~~~~~~~~~

Creates a collection-level change stream and ensures that the server-side cursor
has been created.

This operation proxies the collection's ``watch`` method and supports the same
arguments and options. Test files SHOULD NOT use the collection's ``watch``
operation directly for reasons discussed in `ChangeStream Operations`_. Test
runners MUST ensure that the server-side cursor is created (i.e. ``aggregate``
is executed) as part of this operation and before the resulting change stream
might be saved with
`operation.saveResultAsEntity <operation_saveResultAsEntity_>`_.

Test runners MUST NOT iterate the change stream when executing this operation
and test files SHOULD NOT specify
`operation.expectResult <operation_expectResult_>`_ for this operation.


find
~~~~

When executing a ``find`` operation, the test runner MUST fully iterate the
result. This will ensure consistent behavior between drivers that eagerly create
a server-side cursor and those that do so lazily when iteration begins.


findOneAndReplace and findOneAndUpdate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``returnDocument`` option for ``findOneAndReplace`` and ``findOneAndUpdate``
is documented as an enum with possible values "Before" and "After". Test files
SHOULD express ``returnDocument`` as a string and test runners MUST raise an
error if its value does not case-insensitively match either enum value.


insertMany
~~~~~~~~~~

The CRUD spec documents ``insertMany`` as returning a BulkWriteResult. Because
the ``insertedIds`` field of BulkWriteResult is optional for drivers to
implement, assertions for that field SHOULD utilize the `$$unsetOrMatches`_
operator.


insertOne
~~~~~~~~~

The CRUD spec documents ``insertOne`` as returning an InsertOneResult; however,
because all fields InsertOneResult are optional drivers are permitted to forgo
it entirely and have ``insertOne`` return nothing (i.e. void method). Tests
asserting InsertOneResult SHOULD utilize the `$$unsetOrMatches`_ operator for
*both* the result object and any optional fields within, as in the following
examples::

    - name: insertOne
      object: *collection0
      arguments:
        document: { _id: 2 }
      expectResult:
        $$unsetOrMatches:
          insertedId: { $$unsetOrMatches: 2 }


watch
~~~~~

This operation SHOULD NOT be used in test files. See
`collection_createChangeStream`_.


Session Operations
------------------

These operations and their arguments may be documented in the following
specifications:

- `Convenient API for Transactions <../transactions-convenient-api/transactions-convenient-api.rst>`__
- `Driver Sessions <../sessions/driver-sessions.rst>`__

Session operations that require special handling or are not documented by an
existing specification are described below.


withTransaction
~~~~~~~~~~~~~~~

The ``withTransaction`` operation's ``callback`` parameter is a function and not
easily expressed in YAML/JSON. For ease of testing, this parameter is expressed
as an array of `operation`_ objects (analogous to
`test.operations <test_operations>`_). Test runners MUST evaluate error and
result assertions when executing these operations in the callback.


Bucket Operations
-----------------

These operations and their arguments may be documented in the following
specifications:

- `GridFS <../gridfs/gridfs-spec.rst>`__

Bucket operations that require special handling or are not documented by an
existing specification are described below.


.. _download:
.. _downloadByName:

download and downloadByName
~~~~~~~~~~~~~~~~~~~~~~~~~~~

These operations proxy the bucket's ``openDownloadStream`` and
``openDownloadStreamByName`` methods and support the same parameters and
options, but return a string containing the stream's contents instead of the
stream itself. Test runners MUST fully read the stream to yield the returned
string. This is also necessary to ensure that any expected errors are raised
(e.g. missing chunks). Test files SHOULD use `$$matchesHexBytes`_ in
`expectResult <operation_expectResult_>`_ to assert the contents of the returned
string.


downloadToStream and downloadToStreamByName
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These operations SHOULD NOT be used in test files. See
`IO operations for GridFS streams`_ in `Future Work`_.


openDownloadStream and openDownloadStreamByName
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These operations SHOULD NOT be used in test files. See
`download and downloadByName`_.


.. _openUploadStream:
.. _openUploadStreamWithId:

openUploadStream and openUploadStreamWithId
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These operations SHOULD NOT be used in test files. See
`IO operations for GridFS streams`_ in `Future Work`_. 


.. _upload:
.. _uploadWithId:

upload and uploadWithId
~~~~~~~~~~~~~~~~~~~~~~~

These operations proxy the bucket's ``uploadFromStream`` and
``uploadFromStreamWithId`` methods and support the same parameters and options
with one exception: the ``source`` parameter is an object specifying hex bytes
from which test runners MUST construct a readable stream for the underlying
methods. The structure of ``source`` is as follows::

    { $$hexBytes: <string> }

The string MUST contain an even number of hexademical characters
(case-insensitive) and MAY be empty. The test runner MUST raise an error if the
structure of ``source`` or its string is malformed. The test runner MUST convert
the string to a byte sequence denoting the stream's readable data (if any). For
example, "12ab" would denote a stream with two bytes: "0x12" and "0xab".



uploadFromStream and uploadFromStreamWithId
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These operations SHOULD NOT be used in test files. See
`upload and uploadWithId`_.


ChangeStream Operations
-----------------------

Change stream entities are special in that they are not defined in
`createEntities`_ but are instead created by using
`operation.saveResultAsEntity <operation_saveResultAsEntity_>`_ with a
`client_createChangeStream`_, `database_createChangeStream`_, or
`collection_createChangeStream`_ operation.

Test files SHOULD NOT use a ``watch`` operation to create a change stream, as
the implementation of that method may vary among drivers. For example, some
implementations of ``watch`` immediately execute ``aggregate`` and construct the
server-side cursor, while others may defer ``aggregate`` until the change stream
object is iterated.

The `Change Streams <../change-streams/change-streams.rst>`__ spec does not
define a consistent API for the ChangeStream class, since the mechanisms for
iteration and capturing a resume token may differ between synchronous and
asynchronous drivers. To account for this, this section explicitly defines the
supported operations for change stream entities.


iterateUntilDocumentOrError
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Iterates the change stream until either a single document is returned or an
error is raised. This operation takes no arguments. If
`expectResult <operation_expectResult_>`_ is specified, it SHOULD be a single
document.

`Iterating the Change Stream <../change-streams/tests#iterating-the-change-stream>`__
in the change stream spec cautions drivers that implement a blocking mode of
iteration (e.g. asynchronous drivers) not to iterate the change stream
unnecessarily, as doing so could cause the test runner to block indefinitely.
This should not be a concern for ``iterateUntilDocumentOrError`` as iteration
only continues until either a document or error is encountered.

Test runners MUST ensure that this operation will not inadvertently skip the
first document in a change stream. Albeit rare, this could happen if
``iterateUntilDocumentOrError`` were to blindly invoke ``next`` (or equivalent)
on a change stream in a driver where newly created change streams are already
positioned at their first element and the change stream cursor had a non-empty
``firstBatch`` (i.e. ``resumeAfter`` or ``startAfter`` used). Alternatively,
some drivers may use a different iterator method for advancing a change stream
to its first position (e.g. ``rewind`` in PHP).


Special Test Operations
-----------------------

Certain operations do not correspond to API methods but instead represent
special test operations (e.g. assertions). These operations are distinguished by
`operation.object <operation_object_>`_ having a value of "testRunner". The
`operation.name <operation_name_>`_ field will correspond to an operation
defined below.

Special test operations return no result and are always expected to succeed.
These operations SHOULD NOT be combined with
`expectError <operation_expectError_>`_,
`expectResult <operation_expectResult_>`_, or
`saveResultAsEntity <operation_saveResultAsEntity_>`_.


failPoint
~~~~~~~~~

The ``failPoint`` operation instructs the test runner to configure a fail point
using a "primary" read preference using the specified client entity (fail points
are not configured using the internal MongoClient).

The following arguments are supported:

- ``failPoint``: Required document. The ``configureFailPoint`` command to be
  executed.

- ``client``: Required string. See `commonOptions_client`_.

  The client entity SHOULD specify false for
  `useMultipleMongoses <entity_client_useMultipleMongoses_>`_ if this operation
  could be executed on a sharded topology (according to `runOnRequirements`_ or
  `test.runOnRequirements <test_runOnRequirements_>`_). This is advised because
  server selection rules for mongos could lead to unpredictable behavior if
  different servers were selected for configuring the fail point and executing
  subsequent operations.

When executing this operation, the test runner MUST keep a record of the fail
point so that it can be disabled after the test. The test runner MUST also
ensure that the ``configureFailPoint`` command is excluded from the list of
observed command monitoring events for this client (if applicable).

An example of this operation follows::

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


targetedFailPoint
~~~~~~~~~~~~~~~~~

The ``targetedFailPoint`` operation instructs the test runner to configure a
fail point on a specific mongos.

The following arguments are supported:

- ``failPoint``: Required document. The ``configureFailPoint`` command to be
  executed.

- ``session``: Required string. See `commonOptions_session`_.

The mongos on which to set the fail point is determined by the ``session``
argument (after resolution to a session entity). Test runners MUST error if
the session is not pinned to a mongos server at the time this operation is
executed.

If the driver exposes an API to target a specific server for a command, the
test runner SHOULD use the client entity associated with the session
to execute the ``configureFailPoint`` command. In this case, the test runner
MUST also ensure that this command is excluded from the list of observed
command monitoring events for this client (if applicable). If such an API is
not available, test runners MUST create a new MongoClient that is directly
connected to the session's pinned server for this operation. The new
MongoClient instance MUST be closed once the command has finished executing.

When executing this operation, the test runner MUST keep a record of both the
fail point and pinned mongos server so that the fail point can be disabled on
the same mongos server after the test.

An example of this operation follows::

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


assertSessionTransactionState
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``assertSessionTransactionState`` operation instructs the test runner to
assert that the given session has a particular transaction state.

The following arguments are supported:

- ``session``: Required string. See `commonOptions_session`_.

- ``state``: Required string. Expected transaction state for the session.
  Possible values are as follows: ``none``, ``starting``, ``in_progress``,
  ``committed``, and ``aborted``.

An example of this operation follows::

    - name: assertSessionTransactionState
      object: testRunner
      arguments:
        session: *session0
        state: in_progress


assertSessionPinned
~~~~~~~~~~~~~~~~~~~

The ``assertSessionPinned`` operation instructs the test runner to assert that
the given session is pinned to a mongos server.

The following arguments are supported:

- ``session``: Required string. See `commonOptions_session`_.

An example of this operation follows::

    - name: assertSessionPinned
      object: testRunner
      arguments:
        session: *session0


assertSessionUnpinned
~~~~~~~~~~~~~~~~~~~~~

The ``assertSessionUnpinned`` operation instructs the test runner to assert that
the given session is not pinned to a mongos server.

The following arguments are supported:

- ``session``: Required string. See `commonOptions_session`_.

An example of this operation follows::

    - name: assertSessionUnpinned
      object: testRunner
      arguments:
        session: *session0


assertDifferentLsidOnLastTwoCommands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``assertDifferentLsidOnLastTwoCommands`` operation instructs the test runner
to assert that the last two CommandStartedEvents observed on the client have
different ``lsid`` fields. This assertion is primarily used to test that dirty
server sessions are discarded from the pool.

The following arguments are supported:

- ``client``: Required string. See `commonOptions_client`_.

  The client entity SHOULD include "commandStartedEvent" in
  `observeEvents <entity_client_observeEvents_>`_.

The test runner MUST fail this assertion if fewer than two CommandStartedEvents
have been observed on the client or if either command does not include an
``lsid`` field.

An example of this operation follows::

    - name: assertDifferentLsidOnLastTwoCommands
      object: testRunner
      arguments:
        client: *client0


assertSameLsidOnLastTwoCommands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``assertSameLsidOnLastTwoCommands`` operation instructs the test runner to
assert that the last two CommandStartedEvents observed on the client have
identical ``lsid`` fields. This assertion is primarily used to test that
non-dirty server sessions are not discarded from the pool.

The following arguments are supported:

- ``client``: Required string. See `commonOptions_client`_.

  The client entity SHOULD include "commandStartedEvent" in
  `observeEvents <entity_client_observeEvents_>`_.

The test runner MUST fail this assertion if fewer than two CommandStartedEvents
have been observed on the client or if either command does not include an
``lsid`` field.

An example of this operation follows::

    - name: assertSameLsidOnLastTwoCommands
      object: testRunner
      arguments:
        client: *client0


assertSessionDirty
~~~~~~~~~~~~~~~~~~

The ``assertSessionDirty`` operation instructs the test runner to assert that
the given session is marked dirty.

The following arguments are supported:

- ``session``: Required string. See `commonOptions_session`_.

An example of this operation follows::

    - name: assertSessionDirty
      object: testRunner
      arguments:
        session: *session0


assertSessionNotDirty
~~~~~~~~~~~~~~~~~~~~~

The ``assertSessionNotDirty`` operation instructs the test runner to assert that
the given session is not marked dirty.

The following arguments are supported:

- ``session``: Required string. See `commonOptions_session`_.

An example of this operation follows::

    - name: assertSessionNotDirty
      object: testRunner
      arguments:
        session: *session0


assertCollectionExists
~~~~~~~~~~~~~~~~~~~~~~

The ``assertCollectionExists`` operation instructs the test runner to assert
that the given collection exists in the database. The test runner MUST use the
internal MongoClient for this operation.

The following arguments are supported:

- ``collectionName``: Required string. See `commonOptions_collectionName`_.

- ``databaseName``: Required string. See `commonOptions_databaseName`_.

An example of this operation follows::

    - name: assertCollectionExists
      object: testRunner
      arguments:
        collectionName: *collection0Name
        databaseName:  *database0Name

Use a ``listCollections`` command to check whether the collection exists. Note
that it is currently not possible to run ``listCollections`` from within a
transaction.


assertCollectionNotExists
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``assertCollectionNotExists`` operation instructs the test runner to assert
that the given collection does not exist in the database. The test runner MUST
use the internal MongoClient for this operation.

The following arguments are supported:

- ``collectionName``: Required string. See `commonOptions_collectionName`_.

- ``databaseName``: Required string. See `commonOptions_databaseName`_.

An example of this operation follows::

    - name: assertCollectionNotExists
      object: testRunner
      arguments:
        collectionName: *collection0Name
        databaseName:  *database0Name

Use a ``listCollections`` command to check whether the collection exists. Note
that it is currently not possible to run ``listCollections`` from within a
transaction.


assertIndexExists
~~~~~~~~~~~~~~~~~

The ``assertIndexExists`` operation instructs the test runner to assert that an
index with the given name exists on the collection. The test runner MUST use the
internal MongoClient for this operation.

The following arguments are supported:

- ``collectionName``: Required string. See `commonOptions_collectionName`_.

- ``databaseName``: Required string. See `commonOptions_databaseName`_.

- ``indexName``: Required string. Index name.

An example of this operation follows::

    - name: assertIndexExists
      object: testRunner
      arguments:
        collectionName: *collection0Name
        databaseName:  *database0Name
        indexName: t_1

Use a ``listIndexes`` command to check whether the index exists. Note that it is
currently not possible to run ``listIndexes`` from within a transaction.


assertIndexNotExists
~~~~~~~~~~~~~~~~~~~~

The ``assertIndexNotExists`` operation instructs the test runner to assert that
an index with the given name does not exist on the collection. The test runner
MUST use the internal MongoClient for this operation.

- ``collectionName``: Required string. See `commonOptions_collectionName`_.

- ``databaseName``: Required string. See `commonOptions_databaseName`_.

- ``indexName``: Required string. Index name.

An example of this operation follows::

    - name: assertIndexNotExists
      object: testRunner
      arguments:
        collectionName: *collection0Name
        databaseName:  *database0Name
        indexName: t_1

Use a ``listIndexes`` command to check whether the index exists. Note that it is
currently not possible to run ``listIndexes`` from within a transaction.


loop
~~~~

The ``loop`` operation executes sub-operations in a loop until a termination
signal is received by the unified test runner. It supports the following
arguments:

- ``operations``: the sub-operations to run on each loop iteration.
  Each sub-operation must be a valid operation as described in this
  specification.

- ``storeErrorsAsEntity``: if specified, the runner MUST handle errors
  arising during sub-operation execution and append a document with error
  information to the array stored in the specified entity. If
  ``storeFailuresAsEntity`` is specified, the runner MUST NOT include
  failures in the errors. If ``storeFailuresAsEntity`` is not specified,
  the runner MUST include failures in the errors. The error document
  MUST contain the following fields:
  
  - ``error``: the textual description of the error encountered.
  - ``time``: the number of (floating-point) seconds since the Unix epoch
    when the error was encountered.

- ``storeFailuresAsEntity``: if specified, the runner MUST handle failures
  arising during sub-operation execution and append a document with failure
  information to the array stored in the specified entity. If
  not specified, the runner MUST treat failures as errors, and either
  handle them following the logic described in ``storeErrorsAsEntity``
  or cause them to terminate execution, if ``storeErrorsAsEntity`` is not
  specified. The failure document MUST contain the following fields:
  
  - ``error``: the textual description of the failure encountered.
  - ``time``: the number of (floating-point) seconds since the Unix epoch
    when the failure was encountered.

- ``storeIterationsAsEntity``: if specfied, the runner MUST keep track of
  the number of iterations of the loop performed, and store that number
  in the specified entity.

The following termination behavior MUST be implemented by the unified test
runner:

- There MUST be a way to request termination of the loops. This request
  will be made by the Atlas testing workload executor in response to
  receiving the termination signal from Astrolabe.
  
- When the termination request is received, the workload executor MUST
  stop looping. The current loop iteration SHOULD complete to its natural
  conclusion (success or failure).

- After the termination request is received, the runner MUST NOT start
  any further loops.
  
- When the termination request is received, the runner SHOULD skip
  any non-loop operations not yet started and terminate as soon as practical.
  
- Termination request MUST cause a successful termination of the test
  overall, i.e., receiving the termination request MUST NOT by itself be
  considered an error.

The exact mechanism by which the termination signal is delivered to the
unified test runner, including the respective API, is left to the driver.

An example of this operation follows::

    - name: loop
      object: testRunner
      arguments:
        storeErrorsAsEntity: errors
        storeFailuresAsEntity: failures
        storeIterationsAsEntity: iterations
        operations:
          - name: find
            object: *collection0
            arguments:
              filter: { _id: { $gt: 1 }}
              sort: { _id: 1 }
            expectResult:
              -
                _id: 2
                x: 22
              -
                _id: 3
                x: 33


Evaluating Matches
------------------

Expected values in tests (e.g.
`operation.expectResult <operation_expectResult_>`_) are expressed as either
relaxed or canonical `Extended JSON <../extended-json.rst>`_.

The algorithm for matching expected and actual values is specified with the
following pseudo-code::

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

The rules for comparing documents and arrays are discussed in more detail in
subsequent sections. When comparing types *other* than documents and arrays,
test runners MAY adopt any of the following approaches to compare expected and
actual values, as long as they are consistent:

- Convert both values to relaxed or canonical `Extended JSON`_ and compare
  strings
- Convert both values to BSON, and compare bytes
- Convert both values to native representations, and compare accordingly

When comparing types that contain documents as internal properties (e.g.
CodeWScope), the rules in `Evaluating Matches`_ do not apply and the documents
MUST match exactly; however, test runners MUST permit variation in document key
order or otherwise normalize the documents before comparison.


Flexible Numeric Comparisons
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When comparing numeric types (excluding Decimal128), test runners MUST consider
32-bit, 64-bit, and floating point numbers to be equal if their values are
numerically equivalent. For example, an expected value of ``1`` would match an
actual value of ``1.0`` (e.g. ``ok`` field in a server response) but would not
match ``1.5``.


Allowing Extra Fields in Root-level Documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When matching root-level documents, test runners MUST permit the actual document
to contain additional fields not present in the expected document. Examples of
root-level documents include, but are not limited to:

- ``command`` for `CommandStartedEvent <expectedEvent_commandStartedEvent_>`_
- ``reply`` for `CommandSucceededEvent <expectedEvent_commandSucceededEvent_>`_
- `expectResult`_ for ``findOneAndUpdate`` `Collection Operations`_
- `expectResult`_ for `iterateUntilDocumentOrError`_ `ChangeStream Operations`_
- each array element in `expectResult`_ for `find`_ or `collection_aggregate`_
  `Collection Operations`_

For example, the following documents match::

    expected: { x: 1 }
    actual: { x: 1, y: 1 }

The inverse is not true. For example, the following documents do not match::

    expected: { x: 1, y: 1 }
    actual: { x: 1 }

Test runners MUST NOT permit additional fields in nested documents. For example,
the following documents do not match::

    expected: { x: { y: 1 } }
    actual: { x: { y: 1, z: 1 } }

It may be helpful to think of expected documents as a form of query criteria.
The intention behind this rule is that it is not always feasible or relevant for
a test to exhaustively specify all fields in an expected document (e.g. cluster
time in ``command`` for `CommandStartedEvent`_).

When the expected value is an array, test runners MUST differentiate between
an array of values, which may be documents, (e.g. ``distinct``) and an array of
root-level documents (e.g. ``find``, ``aggregate``). For example, the following
array of documents would not match if returned by ``distinct``, but would match
if returned via ``find`` (after iterating the cursor):

    expected: [ { x: 1 }, { x: 2 } ]
    actual: [ { x: 1, y: 1 }, { x: 2, y: 2 } ]


Document Key Order Variation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When matching documents, test runners MUST NOT require keys in the expected and
actual document to appear in the same order. For example, the following
documents would match:

    expected: { x: 1, y: 1 }
    actual: { y: 1, x: 1 }


Arrays Must Contain the Same Number of Elements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When comparing arrays, expected and actual values MUST contain the same number
of elements. For example, the following arrays corresponding to a ``distinct``
operation result would not match::

    expected: [ 1, 2, 3 ]
    actual: [ 1, 2, 3, 4 ]


Special Operators for Matching Assertions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When matching expected and actual values, an equality comparison is not always
sufficient. For instance, a test file cannot anticipate what a session ID will
be at runtime, but may still want to analyze the contents of an ``lsid`` field
in a command document. To address this need, special operators can be used.

These operators are objects with a single key identifying the operator. Such
keys are prefixed with ``$$`` to ease in detecting an operator (test runners
need only inspect the first key of each object) and differentiate the object
from MongoDB query operators, which use a single `$` prefix. The key will map to
some value that influences the operator's behavior (if applicable).

When examining the structure of an expected value during a comparison, test
runners MUST check if the value is an object whose first and only key starts
with ``$$`` and, if so, defer to the special logic defined in this section.


$$exists
````````

Syntax::

    { field: { $$exists: <boolean> } }

This operator can be used anywhere the value for a key might be specified in an
expected document. If true, the test runner MUST assert that the key exists in
the actual document, irrespective of its value (e.g. a key with a ``null`` value
would match). If false, the test runner MUST assert that the key does not exist
in the actual document. This operator is modeled after the
`$exists <https://docs.mongodb.com/manual/reference/operator/query/exists/>`__
query operator.

An example of this operator checking for a field's presence follows::

    command:
      getMore: { $$exists: true }
      collection: *collectionName,
      batchSize: 5

An example of this operator checking for a field's absence follows::

    command:
      update: *collectionName
      updates: [ { q: {}, u: { $set: { x: 1 } } } ]
      ordered: true
      writeConcern: { $$exists: false }


$$type
``````

Syntax::

    { $$type: <string> }
    { $$type: [ <string>, <string>, ... ] }

This operator can be used anywhere a matched value is expected (including
`expectResult <operation_expectResult_>`_). The test runner MUST assert that the
actual value exists and matches one of the expected types, which correspond to
the documented string types for the
`$type <https://docs.mongodb.com/manual/reference/operator/query/type/>`__
query operator.

An example of this operator follows::

    command:
      getMore: { $$type: [ "int", "long" ] }
      collection: { $$type: "string" }

When the actual value is an array, test runners MUST NOT examine types of the
array's elements. Only the type of actual field SHALL be checked. This is
admittedly inconsistent with the behavior of the
`$type <https://docs.mongodb.com/manual/reference/operator/query/type/>`__
query operator, but there is presently no need for this behavior in tests.


$$matchesEntity
```````````````

Syntax, where ``entityName`` is a string::

    { $$matchesEntity: <entityName> }

This operator can be used to reference a BSON entity anywhere a matched value
is expected (including `expectResult <operation_expectResult_>`_). If the
BSON entity is defined in the current test's `Entity Map`_, the test runner
MUST fetch that entity and assert that the actual value matches the entity
using the standard rules in `Evaluating Matches`_; otherwise, the test runner
MUST raise an error for an undefined or mistyped entity. The YAML file SHOULD
use an `alias node`_ for the entity name.

This operator is primarily used to assert identifiers for uploaded GridFS files.

An example of this operator follows::

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


$$matchesHexBytes
`````````````````

Syntax, where ``hexBytes`` is an even number of hexademical characters
(case-insensitive) and MAY be empty::

    { $$matchesHexBytes: <hexBytes> }

This operator can be used anywhere a matched value is expected (including
`expectResult <operation_expectResult_>`_) and the actual value is a string.
The test runner MUST raise an error if the ``hexBytes`` string is malformed.
This operator is primarily used to assert the results of `download`_ and
`downloadByName`_, which return stream contents as a string.


$$unsetOrMatches
````````````````

Syntax::

    { $$unsetOrMatches: <anything> }

This operator can be used anywhere a matched value is expected (including
`expectResult <operation_expectResult_>`_), excluding an array element because
`Arrays Must Contain the Same Number of Elements`_. The test runner MUST assert
that the actual value either does not exist or matches the expected value.
Matching the expected value MUST use the standard rules in
`Evaluating Matches`_, which means that it may contain special operators.

This operator is primarily used to assert driver-optional fields from the CRUD
spec (e.g. ``insertedId`` for InsertOneResult, ``writeResult`` for
BulkWriteException).

An example of this operator used for a result's field follows::

    expectResult:
      insertedId: { $$unsetOrMatches: 2 }

An example of this operator used for an entire result follows::

    expectError:
      expectResult:
        $$unsetOrMatches:
          deletedCount: 0
          insertedCount: 2
          matchedCount: 0
          modifiedCount: 0
          upsertedCount: 0
          upsertedIds: { }


$$sessionLsid
`````````````

Syntax::

    { $$sessionLsid: <sessionEntityName> }

This operator can be used anywhere a matched value is expected (including
`expectResult <operation_expectResult_>`_).  If the
`session entity <entity_session_>`_ is defined in the current test's
`Entity Map`_, the test runner MUST assert that the actual value equals its
logical session ID; otherwise, the test runner MUST raise an error for an
undefined or mistyped entity. The YAML file SHOULD use an `alias node`_ for a
session entity's ``id`` field (e.g. ``session: *session0``).

An example of this operator follows::

    command:
      ping: 1
      lsid: { $$sessionLsid: *session0 }


Test Runner Implementation
--------------------------

The sections below describe instructions for instantiating the test runner,
loading each test file, and executing each test within a test file. Test runners
MUST NOT share state created by processing a test file with the processing of
subsequent test files, and likewise for tests within a test file.


Initializing the Test Runner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The test runner MUST be configurable with a connection string (or equivalent
configuration), which will be used to initialize the internal MongoClient and
any `client entities <entity_client_>`_ (in combination with other URI options).
This specification is not prescriptive about how this information is provided.
For example, it may be read from an environment variable or configuration file.

Create a new MongoClient, which will be used for internal operations (e.g.
processing `initialData`_ and `test.outcome <test_outcome_>`_). This is referred
to elsewhere in the specification as the internal MongoClient.

Determine the server version and topology type using the internal MongoClient.
This information will be used to evaluate any future `runOnRequirement`_ checks.

The test runner SHOULD terminate any open transactions (see:
`Terminating Open Transactions`_) using the internal MongoClient before
executing any tests.


Executing a Test File
~~~~~~~~~~~~~~~~~~~~~

The instructions in this section apply for each test file loaded by the test
runner.

Test files, which may be YAML or JSON files, MUST be interpreted using an
`Extended JSON`_ parser. The parser MUST accept relaxed and canonical Extended
JSON (per `Extended JSON: Parsers <../extended-json.rst#parsers>`__), as test
files may use either.

Upon loading a file, the test runner MUST read the `schemaVersion`_ field and
determine if the test file can be processed further. Test runners MAY support
multiple versions and MUST NOT process incompatible files (as discussed in
`Test Runner Support`_). If a test file is incompatible, test runners MUST raise
an error and MAY do so by reporting a test failure. Test runners MAY make an
effort to infer the number of tests (and their descriptions) from an
incompatible file and report a failure for each test.

If `runOnRequirements`_ is specified, the test runner MUST skip the test file
unless one or more `runOnRequirement`_ objects are satisfied.

For each element in `tests`_, follow the process in `Executing a Test`_.


Executing a Test
~~~~~~~~~~~~~~~~

The instructions in this section apply for each `test`_ occuring in a test file
loaded by the test runner. After processing a test, test runners MUST reset
any internal state that resulted from doing so. For example, the `Entity Map`_
created for one test MUST NOT be shared with another.

If at any point while executing this test an unexpected error is encountered or
an assertion fails, the test runner MUST consider this test to have failed and
SHOULD continue with the instructions in this section to ensure that the test
environment is cleaned up (e.g. disable fail points, kill sessions) while also
forgoing any additional assertions.

If `test.skipReason <test_skipReason_>`_ is specified, the test runner MUST skip
this test and MAY use the string value to log a message.

If `test.runOnRequirements <test_runOnRequirements_>`_ is specified, the test
runner MUST skip the test unless one or more `runOnRequirement`_ objects are
satisfied.

If `initialData`_ is specified, for each `collectionData`_ therein the test
runner MUST drop the collection and insert the specified documents (if any)
using a "majority" write concern. If no documents are specified, the test runner
MUST create the collection with a "majority" write concern. The test runner
MUST use the internal MongoClient for these operations.

Create a new `Entity Map`_ that will be used for this test. If `createEntities`_
is specified, the test runner MUST create each `entity`_ accordingly and add it
to the map. If the topology is a sharded cluster, the test runner MUST handle
`useMultipleMongoses`_ accordingly if it is specified for any client entities.

If the test might execute a ``distinct`` command within a sharded transaction,
for each target collection the test runner SHOULD execute a non-transactional
``distinct`` command on each mongos server using the internal MongoClient. See
`StaleDbVersion Errors on Sharded Clusters`_ for more information.

If the test might execute a ``configureFailPoint`` command, for each target
client the test runner MAY specify a reduced value for ``heartbeatFrequencyMS``
(and ``minHeartbeatFrequencyMS`` if possible) to speed up SDAM recovery time and
server selection after a failure; however, test runners MUST NOT do so for any
client that specifies ``heartbeatFrequencyMS`` in its ``uriOptions``. 

For each client entity where `observeEvents <entity_client_observeEvents_>`_
has been specified, the test runner MUST enable all event listeners necessary to
collect the specified event types. Test runners MAY leave event listeners
disabled for tests that do not assert events (i.e. tests that omit both
`test.expectEvents <test_expectEvents_>`_ and special operations such as
`assertSameLsidOnLastTwoCommands`_).

For each client with command monitoring enabled, the test runner MUST ignore
events for the following:

- Any command(s) specified in
  `ignoreCommandMonitoringEvents <entity_client_ignoreCommandMonitoringEvents_>`_.

- Any ``configureFailPoint`` commands executed for `failPoint`_ and
  `targetedFailPoint`_ operations.

- Any commands containing sensitive information (per the
  `Command Monitoring <../command-monitoring/command-monitoring.rst#security>`__
  spec).

For each element in `test.operations <test_operations_>`_, follow the process
in `Executing an Operation`_. If an unexpected error is encountered or an
assertion fails, the test runner MUST consider this test to have failed.

If any event listeners were enabled on any client entities, the test runner MUST
now disable those event listeners.

If any fail points were configured, the test runner MUST now disable those fail
points (on the same server) to avoid spurious failures in subsequent tests. For
any fail points configured using `targetedFailPoint`_, the test runner MUST
disable the fail point on the same mongos server on which it was originally
configured. See `Disabling Fail Points`_ for more information.

If `test.expectEvents <test_expectEvents_>`_ is specified, for each object
therein the test runner MUST assert that the number and sequence of expected
events match the number and sequence of actual events observed on the specified
client. If the list of expected events is empty, the test runner MUST assert
that no events were observed on the client. The process for matching events is
described in `expectedEvent`_.

If `test.outcome <test_outcome_>`_ is specified, for each `collectionData`_
therein the test runner MUST assert that the collection contains exactly the
expected data. The test runner MUST query each collection using the internal
MongoClient, an ascending sort order on the ``_id`` field (i.e. ``{ _id: 1 }``),
a "primary" read preference, a "local" read concern. When comparing collection
data, the rules in `Evaluating Matches`_ do not apply and the documents MUST
match exactly; however, test runners MUST permit variations in document key
order or otherwise normalize the documents before comparison. If the list of
documents is empty, the test runner MUST assert that the collection is empty.

Clear the entity map for this test. For each ClientSession in the entity map,
the test runner MUST end the session (e.g. call
`endSession <../sessions/driver-sessions.rst#endsession>`_).

If the test started a transaction, the test runner MUST terminate any open
transactions (see: `Terminating Open Transactions`_).

Proceed to the subsequent test.


Executing an Operation
~~~~~~~~~~~~~~~~~~~~~~

The instructions in this section apply for each `operation`_ occuring in a
`test`_ contained within a test file loaded by the test runner.

If at any point while executing an operation an unexpected error is encountered
or an assertion fails, the test runner MUST consider the parent test to have
failed and proceed from `Executing a Test`_ accordingly.

If `operation.object <operation_object_>`_ is "testRunner", this is a special
operation. If `operation.name <operation_name_>`_ is defined in
`Special Test Operations`_, the test runner MUST execute the operation
accordingly and, if successful, proceed to the next operation in the test;
otherwise, the test runner MUST raise an error for an undefined operation. The
test runner MUST keep a record of any fail points configured by special
operations so that they may be disabled after the current test.

If `operation.object`_ is not "testRunner", this is an entity operation. If
`operation.object`_ is defined in the current test's `Entity Map`_, the test
runner MUST fetch that entity and note its type; otherwise, the test runner
MUST raise an error for an undefined entity. If `operation.name`_ does not
correspond to a known operation for the entity type (per
`Entity Test Operations`_), the test runner MUST raise an error for an
unsupported operation. Test runners MAY skip tests that include operations that
are intentionally unimplemented (e.g.
``listCollectionNames``).

Proceed with preparing the operation's arguments. If ``session`` is specified in
`operation.arguments <operation_arguments_>`_, the test runner MUST resolve it
to a session entity and MUST raise an error if the name is undefined or maps to
an unexpected type. If a key in `operation.arguments`_ does not correspond to a
known parameter/option for the operation, the test runner MUST raise an error
for an unsupported argument.

Before executing the operation, the test runner MUST be prepared to catch a
potential error from the operation (e.g. enter a ``try`` block). Proceed with
executing the operation and capture its result or error.

Note that some operations require special handling, as discussed in
`Entity Test Operations`_. For example, model objects may need to be converted
to documents (before matching or saving in the entity map) and returned
iterables may need to be fully iterated.

If `operation.expectError <operation_expectError_>`_ is specified, the test
runner MUST assert that the operation yielded an error; otherwise, the test
runner MUST assert that the operation did not yield an error. If an error was
expected, the test runner MUST evaluate any assertions in `expectedError`_
accordingly.

If `operation.expectResult <operation_expectResult_>`_ is specified, the test
MUST assert that it matches the actual result of the operation according to the
rules outlined in `Evaluating Matches`_.

If `operation.saveResultAsEntity <operation_saveResultAsEntity_>`_ is specified,
the test runner MUST store the result in the current test's entity map using the
specified name. If the operation did not return a result or the result does not
comply with `Supported Entity Types`_ then the test runner MUST raise an error.

After asserting the operation's error and/or result and optionally saving the
result, proceed to the subsequent operation.


Special Procedures
~~~~~~~~~~~~~~~~~~

This section describes some procedures that may be referenced from earlier
sections.


Terminating Open Transactions
`````````````````````````````

Open transactions can cause tests to block indiscriminately. Test runners SHOULD
terminate all open transactions at the start of a test suite and after each
failed test by killing all sessions in the cluster. Using the internal
MongoClient, execute the ``killAllSessions`` command on either the primary or,
if connected to a sharded cluster, all mongos servers.

For example::

    db.adminCommand({
      killAllSessions: []
    });

The test runner MAY ignore any command failure with error Interrupted(11601) to
work around `SERVER-38335`_.

.. _SERVER-38335: https://jira.mongodb.org/browse/SERVER-38335


StaleDbVersion Errors on Sharded Clusters
`````````````````````````````````````````

When a shard receives its first command that contains a ``databaseVersion``, the
shard returns a StaleDbVersion error and mongos retries the operation. In a
sharded transaction, mongos does not retry these operations and instead returns
the error to the client. For example::

    Command distinct failed: Transaction aa09e296-472a-494f-8334-48d57ab530b6:1 was aborted on statement 0 due to: an error from cluster data placement change :: caused by :: got stale databaseVersion response from shard sh01 at host localhost:27217 :: caused by :: don't know dbVersion.

To workaround this limitation, a test runners MUST execute a non-transactional
``distinct`` command on each mongos server before running any test that might
execute ``distinct`` within a transaction. To ease the implementation, test
runners MAY execute ``distinct`` before *every* test.

Test runners can remove this workaround once `SERVER-39704`_ is resolved, after
which point mongos should retry the operation transparently. The ``distinct``
command is the only command allowed in a sharded transaction that uses the
``databaseVersion`` concept so it is the only command affected.

.. _SERVER-39704: https://jira.mongodb.org/browse/SERVER-39704


Server Fail Points
------------------

Many tests utilize the ``configureFailPoint`` command to trigger server-side
errors such as dropped connections or command errors. Tests can configure fail
points using the special `failPoint`_ or `targetedFailPoint`_ opertions.

This internal command is not documented in the MongoDB manual (pending
`DOCS-10784`_); however, there is scattered documentation available on the
server wiki (`The "failCommand" Fail Point <failpoint-wiki_>`_) and employee
blogs (e.g. `Intro to Fail Points <failpoint-blog1_>`_,
`Testing Network Errors with MongoDB <failpoint-blog2_>`_). Documentation can
also be gleaned from JIRA tickets (e.g. `SERVER-35004`_, `SERVER-35083`_). This
specification does not aim to provide comprehensive documentation for all fail
points available for driver testing, but some fail points are documented in
`Fail Points Commonly Used in Tests`_.

.. _failpoint-wiki: https://github.com/mongodb/mongo/wiki/The-%22failCommand%22-fail-point
.. _failpoint-blog1: https://kchodorow.com/2013/01/15/intro-to-fail-points/
.. _failpoint-blog2: https://emptysqua.re/blog/mongodb-testing-network-errors/
.. _DOCS-10784: https://jira.mongodb.org/browse/DOCS-10784
.. _SERVER-35004: https://jira.mongodb.org/browse/SERVER-35004
.. _SERVER-35083: https://jira.mongodb.org/browse/SERVER-35083


Configuring Fail Points
~~~~~~~~~~~~~~~~~~~~~~~

The ``configureFailPoint`` command is executed on the ``admin`` database and has
the following structure::

    db.adminCommand({
        configureFailPoint: <string>,
        mode: <string|object>,
        data: <object>
    });

The value of ``configureFailPoint`` is a string denoting the fail point to be
configured (e.g. "failCommand").

The ``mode`` option is a generic fail point option and may be assigned a string
or object value. The string values "alwaysOn" and "off" may be used to enable or
disable the fail point, respectively. An object may be used to specify either
``times`` or ``skip``, which are mutually exclusive:

- ``{ times: <integer> }`` may be used to limit the number of times the fail
  point may trigger before transitioning to "off".
- ``{ skip: <integer> }`` may be used to defer the first trigger of a fail
  point, after which it will transition to "alwaysOn".

The ``data`` option is an object that may be used to specify any options that
control the particular fail point's behavior.

In order to use ``configureFailPoint``, the undocumented ``enableTestCommands``
`server parameter <https://docs.mongodb.com/manual/reference/parameters/>`_ must
be enabled by either the configuration file or command line option (e.g.
``--setParameter enableTestCommands=1``). It cannot be enabled at runtime via
the `setParameter <https://docs.mongodb.com/manual/reference/command/setParameter/>`_
command). This parameter should already be enabled for most configuration files
in `mongo-orchestration <https://github.com/10gen/mongo-orchestration>`_.


Disabling Fail Points
~~~~~~~~~~~~~~~~~~~~~

A fail point may be disabled like so::

    db.adminCommand({
        configureFailPoint: <string>,
        mode: "off"
    });


Fail Points Commonly Used in Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


failCommand
```````````

The ``failCommand`` fail point allows the client to force the server to return
an error for commands listed in the ``data.failCommands`` field. Additionally,
this fail point is documented in server wiki:
`The failCommand Fail Point <https://github.com/mongodb/mongo/wiki/The-%22failCommand%22-fail-point>`__.

The ``failCommand`` fail point may be configured like so::

    db.adminCommand({
        configureFailPoint: "failCommand",
        mode: <string|object>,
        data: {
          failCommands: [<string>, ...],
          closeConnection: <boolean>,
          errorCode: <integer>,
          writeConcernError: <object>,
          appName: <string>,
          blockConnection: <boolean>,
          blockTimeMS: <integer>,
        }
    });

``failCommand`` supports the following ``data`` options, which may be combined
if desired:

* ``failCommands``: Required array of strings. Lists the command names to fail.
* ``closeConnection``: Optional boolean, which defaults to ``false``. If
  ``true``, the command will not be executed, the connection will be closed, and
  the client will see a network error.
* ``errorCode``: Optional integer, which is unset by default. If set, the
  command will not be executed and the specified command error code will be
  returned as a command error.
* ``appName``: Optional string, which is unset by default. If set, the fail
  point will only apply to connections for MongoClients created with this
  ``appname``. New in server 4.4.0-rc2
  (`SERVER-47195 <https://jira.mongodb.org/browse/SERVER-47195>`_).
* ``blockConnection``: Optional boolean, which defaults to ``false``. If
  ``true``, the server should block the affected commands for ``blockTimeMS``.
  New in server 4.3.4
  (`SERVER-41070 <https://jira.mongodb.org/browse/SERVER-41070>`_).
* ``blockTimeMS``: Optional integer, which is required when ``blockConnection``
  is ``true``. The number of milliseconds for which the affected commands should
  be blocked. New in server 4.3.4
  (`SERVER-41070 <https://jira.mongodb.org/browse/SERVER-41070>`_).


Determining if a Sharded Cluster Uses Replica Sets
--------------------------------------------------

When connected to a mongos server, the test runner can query the
`config.shards <https://docs.mongodb.com/manual/reference/config-database/#config.shards>`__
collection. Each shard in the cluster is represented by a document in this
collection. If the shard is backed by a single server, the ``host`` field will
contain a single host. If the shard is backed by a replica set, the ``host``
field contain the name of the replica followed by a forward slash and a
comma-delimited list of hosts.


Design Rationale
================

This specification was primarily derived from the test formats used by the
`Transactions <../transactions/transactions.rst>`__ and
`CRUD <../crud/crud.rst>`__ specs, which have served models or other specs.

This specification commonly uses "SHOULD" when providing guidance on writing
test files. While this may appear contradictory to the driver mantra preferring
"MUST", it is intentional. Some of this guidance addresses style (e.g. adding
comments, using YAML anchors) and cannot be enforced with a JSON schema. Other
guidance needs to be purposefully ignored in order to test the test runner
implementation (e.g. defining entities out of order to trigger runtime errors).
The specification does prefer "MUST" in other contexts, such as discussing parts
of the test file format that *are* enforceable by the JSON schema or the test
runner implementation.


Breaking Changes
================

This section is reserved for future use. Any breaking changes to the test format
SHOULD be described here in detail for historical reference, in addition to any
shorter description that may be added to the `Change Log`_.


Future Work
===========


Mixing event types in observeEvents and expectEvents
----------------------------------------------------

The test format advises against mixing events from different specs (e.g. command
monitoring *and* SDAM) in `observeEvents`_ and `test.expectEvents`_. While
registering event listeners is trivial, determining how to collate events of
multiple types can be a challenge, particularly when some events may not be
predictable (e.g. ServerHeartbeatStartedEvent, CommandStartedEvent for
``getMore`` issued during change stream iteration). If the need arises to expect
multiple types of events in the same test, a future version of this spec can
define an approach for doing so.


Support events types beyond command monitoring
----------------------------------------------

The spec currently only supports command monitoring events in `observeEvents`_
and `test.expectEvents`_, as those are the only kind of events used in tests for
specifications that will initially adopt the unified test format. New event
types (e.g. SDAM) can be added in future versions of the spec as needed, which
will also require `Mixing event types in observeEvents and expectEvents`_ to be
addressed.


Allow extra observed events to be ignored
-----------------------------------------

While command monitoring events for specific commands can be ignored (e.g.
killCursors for change streams), the sequence of observed events must otherwise
match the sequence of expected events (including length). The present design
would not support expecting an event for a command while also ignoring extra
events for the same command (e.g. change stream iteration on a sharded cluster
where multiple getMore commands may be issued). No spec tests currently require
this functionality, but that may change in the future.


Assert expected log messages
----------------------------

When drivers support standardized logging, the test format may need to support
assertions for messages expected to be logged while executing operations. Since
log messages are strings, this may require an operator to match regex patterns
within strings. Additionally, the test runner may need to support ignoring extra
log output, similar to `Allow extra observed events to be ignored`_.


Target failPoint by read preference
-----------------------------------

The `failPoint`_ operation currently uses a "primary" read preference. To date,
no spec has needed behavior to configure a fail point on a non-primary node. If
the need does arise, `failPoint`_ can be enhanced to support a
``readPreference`` argument.


IO operations for GridFS streams
--------------------------------

Original GridFS spec tests refer to "upload", "download", and "download_by_name"
methods, which allow the tests to abstract stream IO and either upload a byte
sequence or assert a downloaded byte sequence. These operations correspond to
the `download`_, `downloadByName`_, `upload`_, and `uploadWithId`_
`Bucket Operations`_.

In order to support methods such as ``downloadToStream``, ``openUploadStream``,
and ``openUploadStreamWithId``, test runners would need to represent streams as
entities and support IO operations to directly read from and write to a stream
entity. This may not be worth the added complexity if the existing operations
provide adequate test coverage for GridFS implementations.


Support Client-side Encryption integration tests
------------------------------------------------

Supporting client-side encryption spec tests will require the following changes
to the test format:

- ``json_schema`` will need to be specified when creating a collection, via
  either the collection entity definition or `initialData`_.
- ``key_vault_data`` can be expressed via `initialData`_
- ``autoEncryptOpts`` will need to be specified when defining a client entity.
  Preparation of this field may require reading AWS credentials from environment
  variables.

The process for executing tests should not require significant changes, but test
files will need to express a dependency on mongocryptd.


Support SDAM integration tests
------------------------------

SDAM integration tests should not require test format changes, but will
introduce several new special test operations for the "testRunner" object. While
the tests themselves only define expectations for command monitoring events,
some special operations may require observing additional event types. There are
also special operations for defining threads and executing operations within
threads, which may warrant introducing a new "thread" entity type.


Incorporate referenced entity operations into the schema version
----------------------------------------------------------------

The `Schema Version`_ is not impacted by changes to operations defined in other
specs and referenced in `Entity Test Operations` (e.g. ``find`` for CRUD). The
`operation.name <operation_name_>`_ and
`operation.arguments <operation_arguments_>`_ fields are loosely defined in the
JSON schema as string and object types, respectively.

Ideally, all operations (and their arguments) would be enforced by the JSON
schema *and* any changes to operations would affect the schema version
accordingly. For example, a new ``find`` option would warrant a minor version
bump both for the CRUD spec and this spec and its schema.

As discussed in `Executing an Operation`_, test runners MUST raise errors for
unsupported operations and arguments. This is a concession until such time that
better processes can be established for versioning other specs *and* collating
spec changes developed in parallel or during the same release cycle.


Change Log
==========

:2020-12-23: Clarify how JSON schema is renamed for new minor versions.

:2020-11-06: Added ``serverApi`` option for client entities, ``_yamlAnchors``
             property to define values for later use in YAML tests, and
             ``serverParameters`` property for ``runOnRequirements``.
