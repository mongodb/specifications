===================
Unified Test Format
===================

:Spec Title: Unified Test Format
:Spec Version: 1.0.0
:Author: Jeremy Mikola
:Advisors: Prashant Mital, Isabel Atkinson
:Status: Draft
:Type: Standards
:Minimum Server Version: N/A
:Last Modified: 2020-08-21

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

Specification
=============


Terms
-----

Entity
  Any object or value that is indexed by a unique name and stored in the
  `Entity Map`_. This will typically be a driver object (e.g. client, session)
  defined in `createEntities`_ but may also be a
  `saved operation result <operation_saveResultAsEntity_>`_. Entities are
  referenced throughout the test file (e.g. `Entity Test Operations`_).

Internal MongoClient
  A MongoClient created specifically for use with internal test operations, such
  as inserting collection data before a test, configuring fail points during a
  test, or asserting collection data after a test.


Schema Version
--------------

This specification and the `Test Format`_ follow
`semantic versioning <https://semver.org/>`__. Backwards breaking changes (e.g.
removing a field, introducing a required field) will warrant a new major
version. Backwards compatible changes (e.g. introducing an optional field) will
warrant a new minor version. Small bug fixes and internal changes (e.g. grammar)
will warrant a new patch version.

Each test file defines a `schemaVersion`_, which test runners will use to
determine compatibility (i.e. whether and how the test file will be
interpreted). Test runners MAY support multiple versions of the test format.
Test runners MUST NOT process incompatible files but are otherwise free to
determine how to handle such files (e.g. skip and log a notice, fail and raise
an error).

Each major version of this specification will have a corresponding JSON schema
(e.g. `schema-1.json <schema-1.json>`__), which may be used to programmatically
validate YAML and JSON files using a tool such as `Ajv <https://ajv.js.org/>`__.

The latest JSON schema MUST remain consistent with the `Test Format`_ section.
If and when a new major version is introduced, the `Breaking Changes`_ section
must be updated and JSON schema(s) for any previous major version(s) MUST remain
available so that older test files can still be validated. New tests files
SHOULD always be written using the latest version of this specification.


Entity Map
----------

The entity map indexes arbitrary objects and values by unique names, so that
they can be referenced from test constructs (e.g.
`operation.object <operation_object_>`_). To ensure each test is executed in
isolation, test runners MUST NOT share entity maps between tests. Most entities
will be driver objects created by the `createEntities`_ directive during test
setup, but the entity map may also be modified during test execution via the
`operation.saveResultAsEntity <operation_saveResultAsEntity_>`_ directive.

Test runners may choose to implement the entity map in a fashion most suited to
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


Test Format
-----------

Each specification test file can define one or more tests, which inherit some
top-level configuration (e.g. namespace, initial data). YAML and JSON test files
are parsed as a document by the test runner. This section defines the top-level
keys for that document and links to various sub-sections for definitions of
nested structures (e.g. individual `test`_, `operation`_).

Although test runners are free to process YAML or JSON files, YAML is the
canonical format for writing tests. YAML files may be converted to JSON using a
tool such as `js-yaml <https://github.com/nodeca/js-yaml>`__ .


Top-level Fields
~~~~~~~~~~~~~~~~

The top-level fields of a test file are as follows:

.. _schemaVersion:

- ``schemaVersion``: Required string. Version of this specification to which the
  test file complies. Test runners will use this to determine compatibility
  (i.e. whether and how the test file will be interpreted). The format of this
  string is defined in `Version String`_.

.. _runOn:

- ``runOn``: Optional array of documents. List of server version and/or topology
  requirements for which the tests in this file can be run. These requirements
  may be overridden on a per-test basis by `test.runOn <test_runOn_>`_. Test
  runners MUST skip a test if its requirements are not met.

  If set, the array should contain at least one document. The structure of each
  document is defined in `runOnRequirement`_.

.. _allowMultipleMongoses:

- ``allowMultipleMongoses``: Optional boolean. If false, all MongoClients
  created for this test file (internal and any ` entities <entity_client_>`_)
  that could connect to a sharded cluster MUST be initialized with only a single
  mongos host. Defaults to true. If true or the topology is non-sharded, this
  option has no effect. Test files that include tests with a `failPoint`_
  operation that may run on sharded topologies MUST specify false for this
  option.

.. _createEntities:

- ``createEntities``: Optional array of documents. List of entities (e.g.
  client, collection, session objects) that should be created before each test
  case is executed. The structure of each document is defined in `entity`_.

.. _collectionName:

- ``collectionName``: Optional string. Name of collection under test. This is
  primarily useful when the collection name must be referenced in an assertion.
  If unset, test runners may use whatever value they prefer.

.. _databaseName:

- ``databaseName``: Optional string. Name of database under test. This is
  primarily useful when the database name must be referenced in an assertion.
  If unset, test runners may use whatever value they prefer.

.. _initialData:

- ``initialData``: Optional array of documents. Data that should exist in
  collections before each test case is executed.

  If set, the array should contain at least one document. The structure of each
  document is defined in `collectionData`_.

.. _tests:

- ``tests``: Required array of documents. List of test cases to be executed
  independently of each other.

  The array should contain at least one document. The structure of each
  document is defined in `test`_.


runOnRequirement
~~~~~~~~~~~~~~~~

A combination of server version and/or topology requirements for running the
test(s). The structure of this document is as follows:

- ``minServerVersion``: Optional string. The minimum server version (inclusive)
  required to successfully run the tests. If this field is omitted, it should be
  assumed that there is no lower bound on the required server version. The
  format of this string is defined in `Version String`_.

- ``maxServerVersion``: Optional string. The maximum server version (inclusive)
  against which the tests can be run successfully. If this field is omitted, it
  should be assumed that there is no upper bound on the required server version.
  The format of this string is defined in `Version String`_.

- ``topology``: Optional string or array of strings. One or more of server
  topologies against which the tests can be run successfully. Valid topologies
  are "single", "replicaset", "sharded", and "sharded-replicaset" (i.e. sharded
  cluster backed by replica sets). If this field is omitted, it should be
  assumed that there is no topology requirement for the test.


entity
~~~~~~

An entity (e.g. client, collection, session object) that will be created in the
`Entity Map`_ before each test is executed. This document must contain exactly
one top-level key that identifies the entity type and maps to a nested document,
which specifies a unique name for the entity (``id`` key) and any other
parameters necessary for its construction. Tests SHOULD use sequential names
based on the entity type (e.g. "session0", "session1").

When defining an entity document in YAML, a `node anchor`_ SHOULD be created on
the entity's ``id`` key. This anchor will allow the unique name to be referenced
with an `alias node`_ later in the file (e.g. from another entity or
`operation`_ document) and also leverage YAML's parser for reference validation.

.. _node anchor: https://yaml.org/spec/1.2/spec.html#id2785586
.. _alias node: https://yaml.org/spec/1.2/spec.html#id2786196

The structure of this document is as follows:

.. _entity_client:

- ``client``: Optional document. Corresponds with a MongoClient object. The
  structure of this document is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor`_ for this field (e.g. ``id: &client0 client0``).

  - ``uriOptions``: Optional document. Additional URI options to apply to the
    test suite's connection string that is used to create this client. Any keys
    in this document MUST override conflicting keys in the connection string.

    Documentation for supported options may be found in the
    `URI Options <../uri-options/uri-options.rst>`__ spec, with one notable
    exception: if ``readPreferenceTags`` is specified in this document, the key
    will map to an array of strings, each representing a tag set, since it is
    not feasible to define multiple ``readPreferenceTags`` keys in the document.

.. _entity_database:

- ``database``: Optional document. Corresponds with a Database object. The
  structure of this document is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor`_ for this field (e.g. ``id: &database0 database0``).

  - ``client``: Required string. Client entity from which this database will be
    created. The YAML file SHOULD use an `alias node`_ for a client entity's
    ``id`` field (e.g. ``client: *client0``).

  - ``databaseName``: Optional string. Database name. If omitted, this defaults
    to the name of the database under test (see: `databaseName`_).

  - ``databaseOptions``: Optional document. See `collectionOrDatabaseOptions`_.

.. _entity_collection:

- ``collection``: Optional document. Corresponds with a Collection object. The
  structure of this document is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor`_ for this field (e.g.
    ``id: &collection0 collection0``).

  - ``database``: Required string. Database entity from which this collection
    will be created. The YAML file SHOULD use an `alias node`_ for a database
    entity's ``id`` field (e.g. ``database: *database0``).

  - ``collectionName``: Optional string. Collection name. If omitted, this
    defaults to the name of the collection under test (see: `collectionName`_).

  - ``collectionOptions``: Optional document. See `collectionOrDatabaseOptions`_.

.. _entity_session:

- ``session``: Optional document. Corresponds with an explicit ClientSession
  object. The structure of this document is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor`_ for this field (e.g. ``id: &session0 session0``).

  - ``client``: Required string. Client entity from which this session will be
    created. The YAML file SHOULD use an `alias node`_ for a client entity's
    ``id`` field (e.g. ``client: *client0``).

  - ``sessionOptions``: Optional document. Map of parameters to pass to
    `MongoClient.startSession <../source/sessions/driver-sessions.rst#startsession>`__
    when creating the session. Supported options are defined in the following
    specifications:

    - `Causal Consistency <../causal-consistency/causal-consistency.rst#sessionoptions-changes>`__
    - `Transactions <../transactions/transactions.rst#sessionoptions-changes>`__

- ``bucket``: Optional document. Corresponds with a GridFS Bucket object. The
  structure of this document is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor`_ for this field (e.g. ``id: &bucket0 bucket0``).

  - ``database``: Required string. Database entity from which this bucket will
    be created. The YAML file SHOULD use an `alias node`_ for a database
    entity's ``id`` field (e.g. ``database: *database0``).

  - ``bucketOptions``: Optional document. Additional options used to construct
    the bucket object. Supported options are defined in the
    `GridFS <../source/gridfs/gridfs-spec.rst#configurable-gridfsbucket-class>`__
    specification. The ``readConcern``, ``readPreference``, and ``writeConcern``
    options use the same structure as defined in `Common Options`_.


collectionData
~~~~~~~~~~~~~~

List of documents that should correspond to the contents of a collection. This
structure is used by both `initialData`_ and `test.outcome <test_outcome_>`_,
which insert and read documents, respectively. The structure of this document is
as follows:

- ``collectionName``: Optional string. Collection name (not an `entity`_).
  Defaults to the name of the collection under test (see: `collectionName`_).

- ``databaseName``: Optional string. Database name (not an `entity`_). Defaults
  to the name of the database under test (see: `databaseName`_).

- ``documents``: Required array of documents. List of documents corresponding to
  the contents of the collection. This list may be empty.


test
~~~~

Test case consisting of a sequence of operations to be executed. The test may
optionally include configuration directives and event/outcome assertions. The
structure of each document is as follows:

- ``description``: Required string. The name of the test.

.. _test_runOn:

- ``runOn``: Optional array of documents. List of server version and/or topology
  requirements for which the tests in this file can be run. If specified, these
  requirements override any top-level requirements in `runOn`_. Test runners
  MUST skip a test if its requirements are not met.

  If set, the array should contain at least one document. The structure of each
  document is defined in `runOnRequirement`_.

- ``skipReason``: Optional string. If set, the test will be skipped. The string
  should explain the reason for skipping the test (e.g. JIRA ticket).

.. _test_operations:

- ``operations``: Required array of documents. List of operations to be executed
  for the test case.

  The array should contain at least one document. The structure of each
  document is defined in `operation`_.

.. _test_expectedEvents:

- ``expectedEvents``: Optional array of documents. List of events, which are
  expected to be observed in this order by running the operations.

  The array should contain at least one document. The structure of each
  document is defined in `expectedEvent`_.

  **TODO**: Determine if an empty array should test that no events are observed.
  Decide if event types (e.g. APM, SDAM) should be mixed in the same array and
  whether tests should be able to filter out certain types (assuming the test
  runner observes any supported type).

.. _test_outcome:

- ``outcome``: Optional array of documents. Data that should exist in
  collections after all operations have been executed. The list of documents
  should be sorted ascendingly by the ``_id`` field to allow for deterministic
  comparisons.

  If set, the array should contain at least one document. The structure of each
  document is defined in `collectionData`_.


operation
~~~~~~~~~

An operation to be executed as part of the test. The structure of this document
is as follows:

.. _operation_name:

- ``name``: Required string. Name of the operation (e.g. method) to perform on
  the object.

.. _operation_object:

- ``object``: Required string. Name of the object on which to perform the
  operation. This should correspond to either an `entity`_ name (for
  `Entity Test Operations`_) or "testRunner" (for `Special Test Operations`_).
  If the object is an entity, The YAML file SHOULD use an `alias node`_ for its
  ``id`` field (e.g. ``object: *collection0``).

.. _operation_arguments:

- ``arguments``: Optional document. Map of parameter names and values for the
  operation. The structure of this document will vary based on the operation.
  See `Entity Test Operations`_ and `Special Test Operations`_.

.. _operation_expectedError:

- ``expectedError``: Optional document. One or more assertions for an expected
  error raised by the operation. The structure of this document is
  defined in `expectedError`_.

.. _operation_expectedResult:

- ``expectedResult``: Optional mixed type. A value corresponding to the expected
  result of the operation. This field may be a scalar value, a single document,
  or an array of documents in the case of a multi-document read.  Test runners
  MUST follow the rules in `Evaluating Matches`_ when processing this assertion.
  This field is mutually exclusive with
  `expectedError <operation_expectedError_>`_.

.. _operation_saveResultAsEntity:

- ``saveResultAsEntity``: Optional string. If specified, the actual result
  returned by the operation (if any) will be saved with this name in the
  `Entity Map`_. The test runner MUST raise an error if the name is already in
  use.

  This is primarily used for change streams.


expectedError
~~~~~~~~~~~~~

One or more assertions for an error/exception, which is expected to be raised by
an executed operation. At least one key is required in this document. The
structure of this document is as follows:

- ``type``: Optional string or array of strings. One or more classifications of
  errors, at least one of which should apply to the expected error. Valid types
  are as follows:

  - ``client``: client-generated error (e.g. parameter validation error before
    a command is sent to the server).

  - ``server``: server-generated error (e.g. error derived from a server
    response).

- ``errorContains``: Optional string. A substring of the expected error message.
  See `bulkWrite`_ for special considerations for BulkWriteExceptions.

- ``errorCodeName``: Optional string. The expected "codeName" field in the
  server-generated error response. See `bulkWrite`_ for special considerations
  for BulkWriteExceptions.

- ``errorLabelsContain``: Optional array of strings. A list of error label
  strings that the error is expected to have.

- ``errorLabelsOmit``: Optional array of strings. A list of error label strings
  that the error is expected not to have.

.. _expectedError_expectedResult:

- ``expectedResult``: Optional mixed type. This field follows the same rules as
  `operation.expectedResult <operation_expectedResult_>`_ and is only used in
  cases where the error includes a result (e.g. `bulkWrite`_).


expectedEvent
~~~~~~~~~~~~~

An event (e.g. APM, SDAM), which is expected to be observed while executing
operations. This document must contain exactly one top-level key that identifies
the event type and maps to a nested document, which contains one or more
assertions for the event's properties. The structure of this document is as
follows:

.. _expectedEvent_commandStartedEvent:

- ``commandStartedEvent``: Optional document. Assertions for a one or more
  `CommandStartedEvent <../command-monitoring/command-monitoring.rst#api>`__
  fields. The structure of this document is as follows:

  - ``command``: Optional document. Test runners MUST follow the rules in
    `Evaluating Matches`_ when processing this assertion.

  - ``commandName``: Optional string.

  - ``databaseName``: Optional string.


collectionOrDatabaseOptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Map of parameters used to construct a collection or database object. The
structure of this document is as follows:

  - ``readConcern``: Optional document. See `commonOptions_readConcern`_.

  - ``readPreference``: Optional document. See `commonOptions_readPreference`_.

  - ``writeConcern``: Optional document. See `commonOptions_writeConcern`_.


Common Options
~~~~~~~~~~~~~~

This section defines the structure of common options that are referenced from
various contexts in the test format. Comprehensive documentation for some of
these types and their parameters may be found in the following specifications:

- `Read and Write Concern <../read-write-concern/read-write-concern.rst>`__.
- `Server Selection: Read Preference <../server-selection/server-selection.rst#read-preference>`__.

The structure of these common options is as follows:

.. _commonOptions_readConcern:

- ``readConcern``: Optional document. Map of parameters to construct a read
  concern. The structure of this document is as follows:

  - ``level``: Required string.

.. _commonOptions_readPreference:

- ``readPreference``: Optional document. Map of parameters to construct a read
  preference. The structure of this document is as follows:

  - ``mode``: Required string.

  - ``tagSets``: Optional array of documents.

  - ``maxStalenessSeconds``: Optional integer.

  - ``hedge``: Optional document.

.. _commonOptions_session:

- ``session``: Optional string. Session entity which will be resolved to a
  ClientSession object. The YAML file SHOULD use an `alias node`_ for a session
  entity's ``id`` field (e.g. ``session: *session0``).

.. _commonOptions_writeConcern:

- ``writeConcern``: Optional document. Map of parameters to construct a write
  concern. The structure of this document is as follows:

  - ``journal``: Optional boolean.

  - ``w``: Optional integer or string.

  - ``wtimeoutMS``: Optional integer.


Version String
--------------

Version strings, which are used for `schemaVersion`_ and `runOn`_, MUST conform
to one of the following formats, where each component is an integer:

- ``<major>.<minor>.<patch>``
- ``<major>.<minor>`` (``<patch>>`` is assumed to be zero)
- ``<major>`` (``<minor>`` and ``<patch>>`` are assumed to be zero)


Entity Test Operations
----------------------

Most operations correspond to an API method on a driver object. If
`operation.object <operation_object_>`_ refers to an `entity`_ name (e.g.
"collection0") then `operation.name <operation_name_>`_ is expected to reference
an API method on that class. Required and optional parameters for API methods
are both specified directly within `operation.arguments <operation_arguments_>`_
(e.g. ``upsert`` for ``updateOne`` is *not* nested under an ``options`` key).

This spec does not provide exhaustive documentation for all possible API methods
that may appear in a test; however, the following sections discuss all supported
entities and their operations in some level of detail.

**TODO**: While CRUD methods tend to flatten options into ``arguments``, session
methods often leave those options nested within an ``options`` key. We should
pick one of these conventions for consistency.


client
~~~~~~

These operations and their arguments may be documented in the following
specifications:

- `Change Streams <../change-streams/change-streams.rst>`__
- `Enumerating Databases <../enumerate-databases.rst>`__


database
~~~~~~~~

These operations and their arguments may be documented in the following
specifications:

- `Change Streams <../change-streams/change-streams.rst>`__
- `CRUD <../crud/crud.rst>`__
- `Enumerating Collections <../enumerate-collections.rst>`__

Other database operations not documented by an existing specification follow.


runCommand
``````````

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

- ``readConcern``: Optional document. See `commonOptions_readConcern`_.

- ``readPreference``: Optional document. See `commonOptions_readPreference`_.

- ``session``: Optional string.  See `commonOptions_session`_.

- ``writeConcern``: Optional document. See `commonOptions_writeConcern`_.


collection
~~~~~~~~~~

These operations and their arguments may be documented in the following
specifications:

- `Change Streams <../change-streams/change-streams.rst>`__
- `CRUD <../crud/crud.rst>`__
- `Enumerating Indexes <../enumerate-indexes.rst>`__
- `Index Management <../index-management.rst>`__


bulkWrite
`````````

While operations typically raise an error *or* return a result, the
``bulkWrite`` operation is unique in that it may report both via the
``writeResult`` property of a BulkWriteException. In this case, the intermediary
write result may be matched with `expectedError_expectedResult`_. Because
``writeResult`` is optional for drivers to implement, such assertions should
utilize the `$$unsetOrMatches`` operator.

Additionally, BulkWriteException is unique in that it aggregates one or more
server errors in its ``writeConcernError`` and ``writeErrors`` properties.
When test runners evaluate `expectedError`_ assertions for ``errorContains`` and
``errorCodeName``, they MUST examine the aggregated errors and consider any
match therein to satisfy the assertion(s). Drivers that concatenate all write
and write concern error messages into the BulkWriteException message MAY
optimize the check for ``errorContains`` by examining the concatenated message.


session
~~~~~~~

These operations and their arguments may be documented in the following
specifications:

- `Convenient API for Transactions <../transactions-convenient-api/transactions-convenient-api.rst>`__
- `Driver Sessions <../sessions/driver-sessions.rst>`__


withTransaction
```````````````

The ``withTransaction`` operation is unique in that its ``callback`` parameter
is a function and not easily expressed in YAML/JSON. For ease of testing, this
parameter is defined as an array of `operation`_ documents (analogous to
`test.operations <test_operations>`_). Test runners MUST evaluate error and
result assertions when executing these operations.


bucket
~~~~~~

These operations and their arguments may be documented in the following
specifications:

- `GridFS <../gridfs/gridfs-spec.rst>`__


Special Test Operations
-----------------------

Certain operations do not correspond to API methods but instead represent
special test operations (e.g. assertions). These operations are distinguished by
`operation.object <operation_object_>`_ having a value of "testRunner". The
`operation.name <operation_name_>`_ field will correspond to an operation
defined below.


failPoint
~~~~~~~~~

The ``failPoint`` operation instructs the test runner to configure a fail point
using a ``primary`` read preference and the internal MongoClient. The
``failPoint`` argument is the ``configureFailPoint`` command to run.

Test files using this operation MUST also specify false for
`allowMultipleMongoses`_ if they could be executed on sharded topologies
(according to `runOn`_ or `test.runOn <test_runOn_>`_). This is necessary
because server selection rules for mongos could lead to unpredictable behavior
if different servers were selected for configuring the fail point and executing
subsequent operations.

An example of this operation follows::

    # Enable the fail point on the server selected with a primary read preference
    - name: failPoint
      object: testRunner
      arguments:
        failPoint:
          configureFailPoint: failCommand
          mode: { times: 1 }
          data:
            failCommands: ["insert"]
            closeConnection: true

See also:

- `Clearing Fail Points After Tests`_
- `Excluding configureFailPoint from APM`_

**TODO**: Consider supporting a readPreference argument to target nodes other
than the primary.


targetedFailPoint
~~~~~~~~~~~~~~~~~

The ``targetedFailPoint`` operation instructs the test runner to configure a
fail point on a specific mongos. The MongoClient and mongos on which to run the
``configureFailPoint`` command is determined by the ``session`` argument. Test
runners MUST error if the session is not pinned to a mongos server at the time
this operation is executed. The ``failPoint`` argument is the
``configureFailPoint`` command to run.

This operation SHOULD NOT be used in test files that specify false for
`allowMultipleMongoses`_ because session pinning cannot be meaningfully tested
without connecting to multiple mongos servers. In practice, this means that
`failPoint`_ and `targetedFailPoint`_ SHOULD NOT be utilized in the same test
file.

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

See also:

- `Clearing Fail Points After Tests`_
- `Excluding configureFailPoint from APM`_


assertSessionTransactionState
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``assertSessionTransactionState`` operation instructs the test runner to
assert that the transaction state of the given session is equal to the specified
value. The possible values are as follows: ``none``, ``starting``,
``in_progress``, ``committed``, ``aborted``.

An example of this operation follows::

    - name: assertSessionTransactionState
      object: testRunner
      arguments:
        session: *session0
        state: in_progress


assertSessionPinned
~~~~~~~~~~~~~~~~~~~

The ``assertSessionPinned`` operation instructs the test runner to assert that
the given session is pinned to a mongos.

An example of this operation follows::

    - name: assertSessionPinned
      object: testRunner
      arguments:
        session: *session0


assertSessionUnpinned
~~~~~~~~~~~~~~~~~~~~~

The ``assertSessionUnpinned`` operation instructs the test runner to assert that
the given session is not pinned to a mongos.

An example of this operation follows::

    - name: assertSessionPinned
      object: testRunner
      arguments:
        session: *session0


assertCollectionExists
~~~~~~~~~~~~~~~~~~~~~~

The ``assertCollectionExists`` operation instructs the test runner to assert
that the given collection exists in the database.

An example of this operation follows::

    - name: assertCollectionExists
      object: testRunner
      arguments:
        database: db
        collection: test

Use a ``listCollections`` command to check whether the collection exists. Note
that it is currently not possible to run ``listCollections`` from within a
transaction.

**TODO**: If this will refer to a collection entity, database is redundant.
Otherwise, consider renaming the arguments to databaseName and collectionName as
was done in `collectionData`_.


assertCollectionNotExists
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``assertCollectionNotExists`` operation instructs the test runner to assert
that the given collection does not exist in the database.

An example of this operation follows::

    - name: assertCollectionNotExists
      object: testRunner
      arguments:
        database: db
        collection: test

Use a ``listCollections`` command to check whether the collection exists. Note
that it is currently not possible to run ``listCollections`` from within a
transaction.

**TODO**: If this will refer to a collection entity, database is redundant.
Otherwise, consider renaming the arguments to databaseName and collectionName as
was done in `collectionData`_.


assertIndexExists
~~~~~~~~~~~~~~~~~

The ``assertIndexExists`` operation instructs the test runner to assert that the
index with the given name exists on the collection.

An example of this operation follows::

    - name: assertIndexExists
      object: testRunner
      arguments:
        database: db
        collection: test
        index: t_1

Use a ``listIndexes`` command to check whether the index exists. Note that it is
currently not possible to run ``listIndexes`` from within a transaction.

**TODO**: If this will refer to a collection entity, database is redundant.
Otherwise, consider renaming the arguments to databaseName and collectionName as
was done in `collectionData`_.


assertIndexNotExists
~~~~~~~~~~~~~~~~~~~~

The ``assertIndexNotExists`` operation instructs the test runner to assert that
the index with the given name does not exist on the collection.

An example of this operation follows::

    - name: assertIndexNotExists
      object: testRunner
      arguments:
        database: db
        collection: test
        index: t_1

Use a ``listIndexes`` command to check whether the index exists. Note that it is
currently not possible to run ``listIndexes`` from within a transaction.

**TODO**: If this will refer to a collection entity, database is redundant.
Otherwise, consider renaming the arguments to databaseName and collectionName as
was done in `collectionData`_.


Evaluating Matches
------------------

Expected values in tests (e.g.
`operation.expectedResult <operation_expectedResult_>`_) are expressed as either
relaxed or canonical `Extended JSON <../extended-json.rst>`_.

The algorithm for matching expected and actual values is specified with the
following pseudo-code::

    function match (expected, actual):
      if expected is a document:
        if first key of expected starts with "$$":          
          assert that the special operator (identified by key) matches
          return

        assert that actual is a document

        for every key/value in expected:
          assert that actual[key] exists
          assert that actual[key] matches value

        return

      if expected is an array:
        assert that actual is an array
        assert that actual and expected have the same number of elements

        for every index/value in expected:
          assert that actual[index] matches value

        return

      // expected is neither a document nor array
      assert that actual and expected are the same type
      assert that actual and expected are equal

The rules for comparing documents and arrays are discussed in more detail in
subsequent sections. When comparing types *other* than documents and arrays,
test runners MAY adopt any of the following approaches to compare expected and
actual values, as long as they are consistent:

- Convert both values to relaxed or canonical `Extended JSON`_ and compare
  strings
- Convert both values to BSON, and compare bytes
- Convert both values to native representations, and compare accordingly

When comparing types that may contain documents (e.g. CodeWScope), test runners
MUST follow standard document matching rules when comparing those properties.


Extra Fields in Actual Documents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When matching expected and actual *documents*, test runners MUST permit the
actual documents to contain additional fields not present in the expected
document. For example, the following documents match::

    expected: { x: 1 }
    actual: { x: 1, y: 1 }

The inverse is not true. For example, the following documents would not match::

    expected: { x: 1, y: 1 }
    actual: { x: 1 }

It may be helpful to think of expected documents as a form of query criteria.
The intention behind this rule is that it is not always feasible or relevant for
a test to exhaustively specify all fields in an expected document (e.g. cluster
time in a `CommandStartedEvent <expectedEvent_commandStartedEvent_>`_ command).

Note that this rule for allowing extra fields in actual values only applies when
matching *documents* documents. When comparing arrays, expected and actual
values must contain the same number of elements. For example, the following
arrays corresponding to a ``distinct`` operation result would not match::

    expected: [ 1, 2, 3 ]
    actual: [ 1, 2, 3, 4 ]

That said, any individual documents *within* an array or list (e.g. result of a
``find`` operation) may be matched according to the rules in this section. For
example, the following arrays would match::

    expected: [ { x: 1 }, { x: 2 } ]
    actual: [ { x: 1, y: 1 }, { x: 2, y: 2 } ]


Special Operators for Matching Assertions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When matching expected and actual values, an equality comparison is not always
sufficient. For instance, a test file cannot anticipate what a session ID will
be at runtime, but may still want to analyze the contents of an ``lsid`` field
in a command document. To address this need, special operators can be used.

These operators are documents with a single key identifying the operator. Such
keys are prefixed with ``$$`` to ease in detecting an operator (test runners
need only inspect the first key of each document) and differentiate the document
from MongoDB query operators, which use a single `$` prefix. The key will map to
some value that influences the operator's behavior (if applicable).

When examining the structure of an expected value during a comparison, test
runners MUST examine the first key of any document for a ``$$`` prefix and, if
present, defer to the special logic defined in this section.


$$exists
````````

Syntax::

    { field: { $$exists: <boolean> } }

This operator can be used anywhere the value for a key might be specified in an
expected dcoument. If true, the test runner MUST assert that the key exists in
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

Syntax, where ``bsonType`` is a string or integer::

    { $$type: <bsonType> }
    { $$type: [ <bsonType>, <bsonType>, ... ] }

This operator can be used anywhere a matched value is expected (including an
`expectedResult <operation_expectedResult_>`_). The test runner MUST assert that
the actual value exists and matches one of the expected types, which correspond
to the documented types for the
`$type <https://docs.mongodb.com/manual/reference/operator/query/type/>`__
query operator.

An example of this operator follows::

    command:
      getMore: { $$type: [ int, long ] }
      collection: { $$type: 2 } # string

When the actual value is an array, test runners MUST NOT examine types of the
array's elements. Only the type of actual field should be checked. This is
admittedly inconsistent with the behavior of the
`$type <https://docs.mongodb.com/manual/reference/operator/query/type/>`__
query operator, but there is presently no need for this behavior in tests.


$$unsetOrMatches
````````````````

Syntax::

    { $$unsetOrMatches: <anything> }

This operator can be used anywhere a matched value is expected (including an
`expectedResult <operation_expectedResult_>`_). The test runner MUST assert that
actual value either does not exist or and matches the expected value. Matching
the expected value should use the standard rules in `Evaluating Matches`_, which
means that it may contain special operators.

This operator is primarily used to assert driver-optional fields from the CRUD
spec (e.g. ``insertedId`` for InsertOneResult, ``writeResult`` for
BulkWriteException).

An example of this operator used for a result's field follows::

    expectedResult:
      insertedId: { $$unsetOrMatches: 2 }

An example of this operator used for an entire result follows::

    expectedError:
      expectedResult:
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

    { $$sessionLsid: <string> }

This operation is used for matching any value with the logical session ID of a
`session entity <entity_session_>`_. The value will refer to a unique name of a
session entity. The YAML file SHOULD use an `alias node`_ for a session entity's
``id`` field (e.g. ``session: *session0``).

An example of this operator follows::

    command:
      ping: 1
      lsid: { $$sessionLsid: *session0 }


TBD: Command Started Events
---------------------------

The event listener used for these tests MUST ignore the security commands listed
in the `Command Monitoring <../command-monitoring/command-monitoring.rst#security>`__
spec.


Test Runner Implementation
--------------------------


Configuring the Test Runner
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The test runner MUST be provided with a connection string (or equivalent
configuration), which will be used to initialize the internal MongoClient and
any `client entities <entity_client_>`_ (in combination with other options).
This specification is not prescriptive about how this information is provided.
For example, it may be read from an environment variable or configuration file.


Loading a Test File
~~~~~~~~~~~~~~~~~~~

Test files, which may be YAML or JSON files, MUST be interpreted using an
`Extended JSON`_ parser. The parser MUST accept relaxed and canonical Extended
JSON, as test files may use either.

Upon loading a file, the test runner MUST read the `schemaVersion`_ field and
determine if the test file can be processed further. Test runners MAY support
multiple versions and MUST NOT process incompatible files (as discussed in
`Schema Version`_).

If the test file is compatible, the test runner shall proceed with determining
default names for the database and collection under test, which may be used by
`database <entity_database_>`_ and `collection <entity_collection_>`_ entities
and `collectionData`_. The test runner MUST use the values from `databaseName`_
and `collectionName`_ fields if set. If a field is omitted, the test runner MUST
generate a name. This spec is not prescriptive about the logic for doing so.

Create a MongoClient, which will be used for internal operations (e.g.
`failPoint`_, processing `initialData`_ and `test.outcome <test_outcome_>`_).
This is referred to elsewhere in the specification as the internal MongoClient.

For each element in ``tests``:

#. If the ``skipReason`` field is present, the test runner MUST skip this test
   and MAY use the string value to log a message.

#. Create a MongoClient and call
   ``client.admin.runCommand({killAllSessions: []})`` to clean up any open
   transactions from previous test failures. Ignore a command failure with
   error code 11601 ("Interrupted") to work around `SERVER-38335`_.

   - Running ``killAllSessions`` cleans up any open transactions from
     a previously failed test to prevent the current test from blocking.
     It is sufficient to run this command once before starting the test suite
     and once after each failed test.
   - When testing against a sharded cluster run this command on ALL mongoses.

#. Create a collection object from the MongoClient, using the ``database_name``
   and ``collection_name`` fields of the YAML file.
#. Drop the test collection, using writeConcern "majority".
#. Execute the "create" command to recreate the collection, using writeConcern
   "majority". (Creating the collection inside a transaction is prohibited, so
   create it explicitly.)
#. If the YAML file contains a ``data`` array, insert the documents in ``data``
   into the test collection, using writeConcern "majority".
#. When testing against a sharded cluster run a ``distinct`` command on the
   newly created collection on all mongoses. For an explanation see,
   Why do tests that run distinct sometimes fail with StaleDbVersion?
#. If ``failPoint`` is specified, its value is a configureFailPoint command.
   Run the command on the admin database to enable the fail point.
#. Create a **new** MongoClient ``client``, with Command Monitoring listeners
   enabled. (Using a new MongoClient for each test ensures a fresh session pool
   that hasn't executed any transactions previously, so the tests can assert
   actual txnNumbers, starting from 1.) Pass this test's ``clientOptions`` if
   present.

   - When testing against a sharded cluster and ``useMultipleMongoses`` is
     ``true`` the client MUST be created with multiple (valid) mongos seed
     addreses.

#. Call ``client.startSession`` twice to create ClientSession objects
   ``session0`` and ``session1``, using the test's "sessionOptions" if they
   are present. Save their lsids so they are available after calling
   ``endSession``, see `Logical Session Id`.
#. For each element in ``operations``:

   - If the operation ``name`` is a special test operation type, execute it and
     go to the next operation, otherwise proceed to the next step.
   - Enter a "try" block or your programming language's closest equivalent.
   - Create a Database object from the MongoClient, using the ``database_name``
     field at the top level of the test file.
   - Create a Collection object from the Database, using the
     ``collection_name`` field at the top level of the test file.
     If ``collectionOptions`` or ``databaseOptions`` is present, create the
     Collection or Database object with the provided options, respectively.
     Otherwise create the object with the default options.
   - Execute the named method on the provided ``object``, passing the
     arguments listed. Pass ``session0`` or ``session1`` to the method,
     depending on which session's name is in the arguments list.
     If ``arguments`` contains no "session", pass no explicit session to the
     method.
   - If the driver throws an exception / returns an error while executing this
     series of operations, store the error message and server error code.
   - If the operation's ``error`` field is ``true``, verify that the method
     threw an exception or returned an error.
   - If the result document has an "errorContains" field, verify that the
     method threw an exception or returned an error, and that the value of the
     "errorContains" field matches the error string. "errorContains" is a
     substring (case-insensitive) of the actual error message.

     If the result document has an "errorCodeName" field, verify that the
     method threw a command failed exception or returned an error, and that
     the value of the "errorCodeName" field matches the "codeName" in the
     server error response.

     If the result document has an "errorLabelsContain" field, verify that the
     method threw an exception or returned an error. Verify that all of the
     error labels in "errorLabelsContain" are present in the error or exception
     using the ``hasErrorLabel`` method.

     If the result document has an "errorLabelsOmit" field, verify that the
     method threw an exception or returned an error. Verify that none of the
     error labels in "errorLabelsOmit" are present in the error or exception
     using the ``hasErrorLabel`` method.
   - If the operation returns a raw command response, eg from ``runCommand``,
     then compare only the fields present in the expected result document.
     Otherwise, compare the method's return value to ``result`` using the same
     logic as the CRUD Spec Tests runner.

#. Call ``session0.endSession()`` and ``session1.endSession``.
#. If the test includes a list of command-started events in ``expectations``,
   compare them to the actual command-started events using the
   same logic as the Command Monitoring Spec Tests runner, plus the rules in
   the Command-Started Events instructions below.
#. If ``failPoint`` is specified, disable the fail point to avoid spurious
   failures in subsequent tests. The fail point may be disabled like so::

    db.adminCommand({
        configureFailPoint: <fail point name>,
        mode: "off"
    });

#. For each element in ``outcome``:

   - If ``name`` is "collection", verify that the test collection contains
     exactly the documents in the ``data`` array. Ensure this find reads the
     latest data by using **primary read preference** with
     **local read concern** even when the MongoClient is configured with
     another read preference or read concern.
     Note the server does not guarantee that documents returned by a find
     command will be in inserted order. This find MUST sort by ``{_id:1}``.

.. _SERVER-38335: https://jira.mongodb.org/browse/SERVER-38335


Server Fail Points
==================

Many tests utilize the ``configureFailPoint`` command to trigger server-side
errors such as dropped connections or command errors. Tests can configure fail
points using the special `failPoint`_ or `targetedFailPoint`_ opertions.

This internal command is not documented in the MongoDB manual (pending
`DOCS-10784`_); however, there is scattered documentation available on the
server wiki (`The "failCommand" Fail Point <failpoint-wiki_>`_) and employee blogs
(e.g. `Intro to Fail Points <failpoint-blog1_>`_,
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
-----------------------

The ``configureFailPoint`` command should be executed on the ``admin`` database
and has the following structure::

    db.adminCommand({
        configureFailPoint: <string>,
        mode: <string|document>,
        data: <document>
    });

The value of ``configureFailPoint`` is a string denoting the fail point to be
configured (e.g. "failCommand").

The ``mode`` option is a generic fail point option and may be assigned a string
or document value. The string values "alwaysOn" and "off" may be used to
enable or disable the fail point, respectively. A document may be used to
specify either ``times`` or ``skip``, which are mutually exclusive:

- ``{ times: <integer> }`` may be used to limit the number of times the fail
  point may trigger before transitioning to "off".
- ``{ skip: <integer> }`` may be used to defer the first trigger of a fail
  point, after which it will transition to "alwaysOn".

The ``data`` option is a document that may be used to specify any options that
control the particular fail point's behavior.

In order to use ``configureFailPoint``, the undocumented ``enableTestCommands``
`server parameter <https://docs.mongodb.com/manual/reference/parameters/>`_ must
be enabled by either the configuration file or command line option (e.g.
``--setParameter enableTestCommands=1``). It cannot be enabled at runtime via
the `setParameter <https://docs.mongodb.com/manual/reference/command/setParameter/>`_
command). This parameter should already be enabled for most configuration files
in `mongo-orchestration <https://github.com/10gen/mongo-orchestration>`_.

Clearing Fail Points After Tests
--------------------------------

If a test configures one or more fail points, test runners MUST disable those
fail points after running all `test.operations <test_operations>`_ to avoid
spurious failures in subsequent tests. For tests using `targetedFailPoint`_, the
test runner MUST disable the fail point on the same mongos node on which it was
originally configured.

A fail point may be disabled like so::

    db.adminCommand({
        configureFailPoint: <string>,
        mode: "off"
    });

Excluding configureFailPoint from APM
-------------------------------------

Test runners MUST ensure that ``configureFailPoint`` commands executed for
`failPoint`_ and `targetedFailPoint`_ operations do not appear in the list of
logged commands used to assert `test.expectedEvents <test_expectedEvents_>`_.
This may require manually filtering ``configureFailPoint`` from the list of
observed commands (particularly in the case of `targetedFailPoint`_, which uses
a `client entity <entity_client>`_).


Fail Points Commonly Used in Tests
----------------------------------


failCommand
~~~~~~~~~~~

The ``failCommand`` fail point allows the client to force the server to return
an error for commands listed in the ``data.failCommands`` field. Additionally,
this fail point is documented in server wiki:
`The failCommand Fail Point <https://github.com/mongodb/mongo/wiki/The-%22failCommand%22-fail-point>`__.

The ``failCommand`` fail point may be configured like so::

    db.adminCommand({
        configureFailPoint: "failCommand",
        mode: <string|document>,
        data: {
          failCommands: ["commandName", "commandName2"],
          closeConnection: <true|false>,
          errorCode: <Number>,
          writeConcernError: <document>,
          appName: <string>,
          blockConnection: <true|false>,
          blockTimeMS: <Number>,
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
  ``appname``. New in server 4.4.0-rc2 (`SERVER-47195 <https://jira.mongodb.org/browse/SERVER-47195>`_).
* ``blockConnection``: Optional boolean, which defaults to ``false``. If
  ``true``, the server should block the affected commands for ``blockTimeMS``.
  New in server 4.3.4 (`SERVER-41070 <https://jira.mongodb.org/browse/SERVER-41070>`_).
* ``blockTimeMS``: Integer, which is required when ``blockConnection`` is
  ``true``. The number of milliseconds for which the affected commands should be
  blocked. New in server 4.3.4 (`SERVER-41070 <https://jira.mongodb.org/browse/SERVER-41070>`_).


Design Rationale
================

This specification was primarily derived from the test formats used by the
`Transactions <../transactions/transactions.rst>`__ and
`CRUD <../crud/crud.rst>`__ specs, which have served models or other specs.


Breaking Changes
================

This section is reserved for future use. Any breaking changes to the test format
should be described here in detail for historical reference, in addition to any
shorter description that may be added to the `Change Log`_.


Change Log
==========

Note: this will be cleared when publishing version 1.0 of the spec

2020-08-21:

* clarify error assertions for BulkWriteException

* note that YAML is the canonical format and discuss js-yaml

* note that configureFailPoint must be excluded from APM

* reformat external links to YAML spec and fail point docs

* add schemaVersion field and document how the spec will handle versions

* move client.allowMultipleMongoses to top-level option, since it should apply
  to all clients (internal and entities). also note that targetedFailPoint and
  failPoint should not be used in the same test file, since the latter requires
  allowMultipleMongoses:false and would not provide meaningful test coverage of
  mongos pinning for sessions.

* add terms and define Entity and Internal MongoClient

* note that failPoint always uses internal MongoClient and targetedFailPoint
  uses the client of its session argument

* start writing steps for test execution

2020-08-19:

* added test.runOn and clarified that it can override top-level runOn requirements

* runOn.topology can be a single string in addition to array of strings

* added "sharded-replicaset" topology type, which will be relevant for change
  streams, transactions, retryable writes.

* removed top-level collectionName and databaseName fields, since they can be
  specified when creating collection and database entities.

* removed test.clientOptions, since client entities can specify their own options

* moved operation.failPoint to failPoint special operation

* operation.object is now required and takes either an entity name (e.g.
  "collection0") or "testRunner"

* operation.commandName moved to an argument of the runCommand database
  operation. Since that method is documented entirely in this spec, I didn't
  see an issue with consolidating.

* renamed operation.result to expectedResult and noted that it may co-exist with
  error assertions in special cases (e.g. BulkWriteException).

* remove error assertions from operation.result. These are now specified under
  operation.expectedError, which replaces the error boolean and requires at
  least one assertion. Added a type assertion (e.g. client, server), which
  should be useful for discerning client-side and server-side errors (currently
  achieved with APM assertions).

* added operation.saveResultAsEntity to capture a result in the entity map
  (primarily for use with change streams)

* consolidated documentation for ignoring configureFailPoint commands in APM and
  also disabling fail points after a test, which is now referenced from the
  failPoint and targetedFailPoint operations

* removed $$assert nesting in favor of $$<operator>, since test runners can
  easily check the first document key for a ``$$`` prefix.

* completed section on evaluating matches and added pseudo-code
