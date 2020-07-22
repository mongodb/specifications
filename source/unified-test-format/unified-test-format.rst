===================
Unified Test Format
===================

:Spec Title: Unified Test Format
:Spec Version: 1.0
:Author: Jeremy Mikola
:Advisors: Prashant Mital
:Status: Draft
:Type: Standards
:Minimum Server Version: N/A
:Last Modified: 2020-08-15

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
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============


Test Format
-----------

Each specification test file can define one or more tests, which inherit some
top-level configuration (e.g. namespace, initial data). YAML and JSON test files
are parsed as a document by the test runner. This section defines the top-level
keys for that document and links to various sub-sections for definitions of
nested structures (e.g. individual `test`_, `operation`_).

The test format is also defined in the accompanying `schema.json <schema.json>`_
file, which may be used to programmatically validate YAML and JSON files using
a tool such as `Ajv <https://ajv.js.org/>`_.

The top-level fields of a test file are as follows:

- ``runOn``: Optional array of documents. List of server version and/or topology
  requirements for which the tests can be run. If the test environment satisfies
  one or more of these requirements, the tests may be executed; otherwise, this
  file should be skipped. If this field is omitted, the tests can be assumed to
  have no particular requirements and should be executed.

  If set, the array should contain at least one document. The structure of each
  document is defined in `runOnRequirement`_.

- ``createEntities``: Optional array of documents. List of entities (e.g.
  client, collection, session objects) that should be created before each test
  case is executed. The structure of each document is defined in `entity`_.

- ``collectionName``: Optional string. Name of collection under test. This is
  primarily useful when the collection name must be referenced in an assertion.
  If unset, drivers may use whatever value they prefer.

- ``databaseName``: Optional string. Name of database under test. This is
  primarily useful when the database name must be referenced in an assertion.
  If unset, drivers may use whatever value they prefer.

.. _initialData:

- ``initialData``: Optional array of documents. Data that should exist in
  collections before each test case is executed.

  If set, the array should contain at least one document. The structure of each
  document is defined in `collectionData`_.

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
  assumed that there is no lower bound on the required server version.

- ``maxServerVersion``: Optional string. The maximum server version (inclusive)
  against which the tests can be run successfully. If this field is omitted, it
  should be assumed that there is no upper bound on the required server version. 

- ``topology``: Optional array of strings. List of server topologies against
  which the tests can be run successfully. Valid topologies are "single",
  "replicaset", and "sharded". If this field is omitted, the default is all
  topologies (i.e. ``["single", "replicaset", "sharded"]``).

  **TODO**: Consider a sharded-replicaset topology.


entity
~~~~~~

An entity (e.g. client, collection, session object) that will be created
before each test is executed. This document must contain exactly one top-level
key that identifies the entity type and maps to a nested document, which
specifies a unique name for the entity (``id`` key) and any other parameters
necessary for its construction. Tests SHOULD use sequential names based on the
entity type (e.g. "session0", "session1").

When defining an entity document in YAML, a
`node anchor <https://yaml.org/spec/1.2/spec.html#id2785586>`_ SHOULD be created
on the entity's ``id`` key. This anchor will allow the unique name to be
referenced with an `alias node <https://yaml.org/spec/1.2/spec.html#id2786196>`_
later in the file (e.g. from another entity or `operation`_ document) and also
leverage YAML's parser for reference validation.

The structure of this document is as follows:

- ``client``: Optional document. Corresponds with a MongoClient object. The
  structure of this document is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor <https://yaml.org/spec/1.2/spec.html#id2785586>`_
    for this field (e.g. ``id: &client0 client0``).

  - ``uriOptions``: Optional document. Additional URI options to apply to the
    test suite's connection string that is used to create this client. Any keys
    in this document MUST override conflicting keys in the connection string.

    Documentation for supported options may be found in the
    `URI Options <../uri-options/uri-options.rst>`__ spec, with one notable
    exception: if ``readPreferenceTags`` is specified in this document, the key
    will map to an array of strings, each representing a tag set, since it is
    not feasible to define multiple ``readPreferenceTags`` keys in the document.

    **TODO**: Consider moving the ``useMultipleMongoses`` `test`_ option here.

- ``database``: Optional document. Corresponds with a Database object. The
  structure of this document is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor <https://yaml.org/spec/1.2/spec.html#id2785586>`_
    for this field (e.g. ``id: &database0 database0``).

  - ``client``: Required string. Client entity from which this database will be
    created. The YAML file SHOULD use an
    `alias node <https://yaml.org/spec/1.2/spec.html#id2786196>`_ for a client
    entity's ``id`` field (e.g. ``client: *client0``).

  - ``databaseName``: Optional string. Database name. If omitted, this defaults
    to the name of the database under test.

  - ``databaseOptions``: Optional document. See `collectionOrDatabaseOptions`_.

- ``collection``: Optional document. Corresponds with a Collection object. The
  structure of this document is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor <https://yaml.org/spec/1.2/spec.html#id2785586>`_
    for this field (e.g. ``id: &collection0 collection0``).

  - ``database``: Required string. Database entity from which this collection
    will be created. The YAML file SHOULD use an
    `alias node <https://yaml.org/spec/1.2/spec.html#id2786196>`_ for a database
    entity's ``id`` field (e.g. ``database: *database0``).

  - ``collectionName``: Optional string. Collection name. If omitted, this
    defaults to the name of the collection under test.

  - ``collectionOptions``: Optional document. See `collectionOrDatabaseOptions`_.

- ``session``: Optional document. Corresponds with an explicit ClientSession
  object. The structure of this document is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor <https://yaml.org/spec/1.2/spec.html#id2785586>`_
    for this field (e.g. ``id: &session0 session0``).

  - ``client``: Required string. Client entity from which this session will be
    created. The YAML file SHOULD use an
    `alias node <https://yaml.org/spec/1.2/spec.html#id2786196>`_ for a client
    entity's ``id`` field (e.g. ``client: *client0``).

  - ``sessionOptions``: Optional document. Map of parameters to pass to
    `MongoClient.startSession <../source/sessions/driver-sessions.rst#startsession>`__
    when creating the session. Supported options are defined in the following
    specifications:

    - `Causal Consistency <../causal-consistency/causal-consistency.rst#sessionoptions-changes>`__
    - `Transactions <../transactions/transactions.rst#sessionoptions-changes>`__

- ``bucket``: Optional document. Corresponds with a GridFS Bucket object. The
  structure of this document is as follows:

  - ``id``: Required string. Unique name for this entity. The YAML file SHOULD
    define a `node anchor <https://yaml.org/spec/1.2/spec.html#id2785586>`_
    for this field (e.g. ``id: &bucket0 bucket0``).

  - ``database``: Required string. Database entity from which this bucket will
    be created. The YAML file SHOULD use an
    `alias node <https://yaml.org/spec/1.2/spec.html#id2786196>`_ for a database
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
which insert and read documents, respectively. Both of those directives 
directives may operate on the collection under test, they do not share the
same Collection object(s) as test `operations <operation_>`_. The structure of
this document is as follows:

- ``collectionName``: Optional string. Collection name (not an `entity`_).
  Defaults to the name of the collection under test.

- ``databaseName``: Optional string. Database name (not an `entity`_). Defaults
  to the name of the database under test.

- ``documents``: Required array of documents. List of documents corresponding to
  the contents of the collection. This list may be empty.


test
~~~~

Test case consisting of a sequence of operations to be executed. The test may
optionally include configuration directives and event/outcome assertions. The
structure of each document is as follows:

- ``description``: Required string. The name of the test.

- ``skipReason``: Optional string. If set, the test will be skipped. The string
  should explain the reason for skipping the test (e.g. JIRA ticket).

- ``useMultipleMongoses``. Optional boolean. If true, the MongoClient for this
  test should be initialized with multiple mongos seed addresses. If false or
  omitted, only a single mongos address should be specified. This field has no
  effect for non-sharded topologies.

    Note: ``useMultipleMongoses:true`` is mutually exclusive with ``failPoint``.

- ``clientOptions``: Optional document. Additional connection string options
  to pass to the MongoClient constructor.

    Note: this option does not support expressing multiple read preference tags,
    tags, since keys would repeat.

.. _test_failPoint:

- ``failPoint``: Optional document. A server failpoint to enable expressed as
  a complete ``configureFailPoint`` command to run on the admin database.

    Note: This option is mutually exclusive with ``useMultipleMongoses:true``.

- ``sessionOptions``: Optional document. Map of session names (e.g. "session0")
  to documents, each of which denotes parameters to pass to
  ``MongoClient.startSession()`` when creating that session.

  **TODO**: remove this in favor of the session `entity`_

.. _test_operations:

- ``operations``: Required array of documents. List of operations to be executed
  for the test case.

  The array should contain at least one document. The structure of each
  document is defined in `operation`_.

- ``expectedEvents``: Optional array of documents. List of events, which are
  expected to be observed in this order by running the operations.

  The array should contain at least one document. The structure of each
  document is defined in `expectedEvent`_.

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

- ``object``: Optional string. Name of the object on which to perform the
  operation. Can be "collection", "database", "session0", "session1", or
  "testRunner". Defaults to "collection".

  **TODO**: link to special operations section

  **TODO**: update this to refer to an entity identifier

- ``collectionOptions``: Optional document. See `collectionOrDatabaseOptions`_.

- ``databaseOptions``: Optional document. See `collectionOrDatabaseOptions`_.

.. _operation_commandName:

- ``commandName``: Optional string. Required only when ``name`` is "runCommand".
  The name of the command to run. This may be used by languages that are unable
  preserve the order of keys in the ``command`` argument when parsing YAML/JSON.

.. _operation_arguments:

- ``arguments``: Optional document. Map of parameter names and values for the
  operation. The structure of this document will vary based on the operation.

  **TODO**: link to operation section

- ``error``: Optional boolean. If true, the test should expect the operation to
  raise an error/exception. This could be either a server-generated or a
  driver-generated error. Defaults to false.

- ``result``: Optional mixed type. The return value from the operation, if any.
  This field may be a scalar value, a single document, or an array of documents
  in the case of a multi-document read. If the operation is expected to raise an
  error/exception (i.e. ``error:true``), the structure of this document is
  defined in `expectedError`_.

  **TODO**: link to section on matching logic


expectedError
~~~~~~~~~~~~~

One or more assertions for an error/exception, which is expected to be raised by
an executed operation. At least one key is required in this document. The
structure of this document is as follows:

- ``errorContains``: Optional string. A substring of the expected error message.

- ``errorCodeName``: Optional string. The expected "codeName" field in the
  server-generated error response.

- ``errorLabelsContain``: Optional array of strings. A list of error label
  strings that the error is expected to have.

- ``errorLabelsOmit``: Optional array of strings. A list of error label strings
  that the error is expected not to have.


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

  - ``command``: Optional document.

    **TODO**: link to section on matching logic

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
  ClientSession object. The YAML file SHOULD use an
  `alias node <https://yaml.org/spec/1.2/spec.html#id2786196>`_ for a session
  entity's ``id`` field (e.g. ``session: *session0``).

.. _commonOptions_writeConcern:

- ``writeConcern``: Optional document. Map of parameters to construct a write
  concern. The structure of this document is as follows:

  - ``journal``: Optional boolean.

  - ``w``: Optional integer or string.

  - ``wtimeoutMS``: Optional integer.


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

Generic command runner. This operation requires that
`operation.commandName <operation_commandName_>`_ also be specified.

This method does not inherit a read concern or write concern (per the
`Read and Write Concern <../read-write-concern/read-write-concern.rst#generic-command-method>`__
spec), nor does it inherit a read preference (per the
`Server Selection <../server-selection/server-selection.rst#use-of-read-preferences-with-commands>`__
spec); however, they may be specified as arguments.

The following arguments are supported:

- ``command``: Required document. The command to be executed.

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
`test.operations <test_operations>`_). Drivers MUST evaluate error and result
assertions when executing these operations.


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


targetedFailPoint
~~~~~~~~~~~~~~~~~

The ``targetedFailPoint`` operation instructs the test runner to configure a
fail point on a specific mongos. The mongos on which to run the
``configureFailPoint`` command is determined by the ``session`` argument. The
session must already be pinned to a mongos server. The "failPoint" argument is
the ``configureFailPoint`` command to run.

If a test uses ``targetedFailPoint``, drivers SHOULD disable the fail point
after running all `test.operations <test_operations>`_ to avoid spurious
failures in subsequent tests. The fail point may be disabled like so::

    db.adminCommand({
        configureFailPoint: <fail point name>,
        mode: "off"
    });

An example instructing the test runner to enable the `failCommand`_ fail point
on the mongos server to which "session0" is pinned follows::

    # Enable the fail point only on the mongos to which session0 is pinned
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

Tests that use the ``targetedFailPoint`` operation do not include
``configureFailPoint`` commands in their command expectations. Drivers MUST
ensure that ``configureFailPoint`` commands do not appear in the list of logged
commands, either by manually filtering it from the list of observed commands or
by using a different MongoClient to execute ``configureFailPoint``.


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


TBD: Command Started Events
---------------------------

The event listener used for these tests MUST ignore the security commands listed
in the `Command Monitoring <../command-monitoring/command-monitoring.rst#security>`__
spec.


Logical Session Id
~~~~~~~~~~~~~~~~~~

Each `expectedEvent_commandStartedEvent`_ that includes an ``lsid`` with the
value "session0" or "session1". Tests MUST assert that the command's actual
``lsid`` matches the id of the correct ClientSession named ``session0`` or
``session1``.

**TODO**: Define a custom matcher for comparing with a session entity's LSID
(e.g. ``lsid: { $$sessionLsid: *session0 }``).


Null Values
~~~~~~~~~~~

Some command-started events in ``expectations`` include ``null`` values for
fields such as ``txnNumber``, ``autocommit``, and ``writeConcern``.
Tests MUST assert that the actual command **omits** any field that has a
``null`` value in the expected command.

**TODO**: Define a custom matcher for checking whether a field exists or not
(e.g. ``txnNumber: { $$exists: false }``).


Cursor Id
~~~~~~~~~

A ``getMore`` value of ``"42"`` in a command-started event is a fake cursorId
that MUST be ignored. (In the Command Monitoring Spec tests, fake cursorIds are
correlated with real ones, but that is not necessary for Transactions Spec
tests.)

**TODO**: Define a custom matcher for checking whether a field exists or not
(e.g. ``getMore: { $$exists: true }``) or matches a particular BSON type (e.g.
``getMore: { $$type: "int" }``, ``getMore: { $$type: ["int", "long"] }``).


afterClusterTime
~~~~~~~~~~~~~~~~

A ``readConcern.afterClusterTime`` value of ``42`` in a command-started event
is a fake cluster time. Drivers MUST assert that the actual command includes an
afterClusterTime.

**TODO**: Define a custom matcher for checking whether a field exists or not
(e.g. ``afterClusterTime: { $$exists: true }``).


recoveryToken
~~~~~~~~~~~~~

A ``recoveryToken`` value of ``42`` in a command-started event is a
placeholder for an arbitrary recovery token. Drivers MUST assert that the
actual command includes a "recoveryToken" field and SHOULD assert that field
is a BSON document.

**TODO**: Define a custom matcher for checking whether a field matches a
particular BSON type (e.g. ``recoveryToken: { $$type: "object" }``).


TBD: Use as Integration Tests
-----------------------------

Run a MongoDB replica set with a primary, a secondary, and an arbiter,
**server version 4.0.0 or later**. (Including a secondary ensures that
server selection in a transaction works properly. Including an arbiter helps
ensure that no new bugs have been introduced related to arbiters.)

A driver that implements support for sharded transactions MUST also run these
tests against a MongoDB sharded cluster with multiple mongoses and
**server version 4.2 or later**. Some tests require
initializing the MongoClient with multiple mongos seeds to ensures that mongos
transaction pinning and the recoveryToken works properly.

Load each YAML (or JSON) file using a Canonical Extended JSON parser.

Then for each element in ``tests``:

#. If the ``skipReason`` field is present, skip this test completely.
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
   ``endSession``, see `Logical Session Id`_.
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
errors such as dropped connections or command errors. Tests refer to this by the
`test.failPoint <test_failPoint_>`_  field or the the special ``targetedFailPoint`` operation
type on the ``testRunner`` object (in ``tests[].operations[]``).

This internal command is not documented in the MongoDB manual (pending
`DOCS-10784`_); however, there is scattered documentation available on the
server wiki (`The failCommand Fail Point <https://github.com/mongodb/mongo/wiki/The-%22failCommand%22-fail-point>`__)
and employee blogs (e.g. `Intro to Fail Points <https://kchodorow.com/2013/01/15/intro-to-fail-points/>`__,
`Testing Network Errors with MongoDB <https://emptysqua.re/blog/mongodb-testing-network-errors/>`__).
Documentation can also be gleaned from JIRA tickets (e.g. `SERVER-35004`_,
`SERVER-35083`_). This specification does not aim to provide comprehensive
documentation for all fail points available for driver testing.

.. _DOCS-10784: https://jira.mongodb.org/browse/DOCS-10784
.. _SERVER-35004: https://jira.mongodb.org/browse/SERVER-35004
.. _SERVER-35083: https://jira.mongodb.org/browse/SERVER-35083

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


failCommand
-----------

The ``failCommand`` fail point allows the client to force the server to return
an error for commands listed in the ``data.failCommands`` field. Additionally,
this fail point is documented in server wiki:
`The failCommand Fail Point <https://github.com/mongodb/mongo/wiki/The-%22failCommand%22-fail-point>`_.

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


Change Log
==========
