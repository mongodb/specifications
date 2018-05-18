.. role:: javascript(code)
  :language: javascript

==================
Change Streams
==================

.. contents::

--------

Introduction
============

The YAML and JSON files in this directory are platform-independent tests that
drivers can use to prove their conformance to the Change Streams Spec.

Several prose tests, which are not easily expressed in YAML, are also presented
in this file. Those tests will need to be manually implemented by each driver.

Test Format
===========

Each YAML files has the following keys:

- ``database_name``: The default database
- ``collection_name``: The default collection
- ``defaults``: Default values for each test
- ``tests``: An array of tests that are to be run independently of each other.
  Each test will have some of the following fields:

  - ``description``: The name of the test.
  - ``skip``: Notes that this test is incomplete and should not be run
  - ``minServerVersion``: The minimum server version to run this test against. If not present, assume there is no minimum server version.
  - ``maxServerVersion``: Reserved for later use
  - ``failPoint``: Reserved for later use
  - ``topology``: The server topology/topologies to run the test against.
    Valid topologies are ``single``, ``replicaset``, and ``sharded``.
    Can be either a single topology, or a list of topologies.
  - ``target``: The entity to run a changeStream on. Valid values are:
  
    - ``collection``: Watch changes on collection ``database_name.collection_name``
    - ``db``: Watch changes on database ``database_name``
    - ``client``: Watch changes on entire clusters

  - ``numChanges``: The number of changes to expect on a changeStream
  - ``operations``: Array of documents, each describing an operation. Each document has the following fields:

    - ``database``: Database to run the operation against
    - ``collection``: Collection to run the operation against
    - ``commandName``: Name of the command to run
    - ``arguments``: Array of arguments for the command.

  - ``expectations``: Optional list of command-started events
  - ``result``: Document with ONE of the following fields:

    - ``error``: Describes an error received during the test
    - ``success``: An array of documents expected to be received from the changeStream

For every test, if a value does not exist, a value from ``defaults`` should be used in its place.

Use as integration tests
========================

The use of the words MATCH and MATCHES, unless otherwise specified, means that every "expected" value is contained in the "actual" value. There may be values present in "actual" that are not present in "expected", but there must not be values in "expected" that are not present in "actual". This is recursive as well: any sub-fields of "expected" must MATCH the corresponding sub-field in "actual"

Before running the tests, create a MongoDB server topology.

For each YAML file, for each element in ``tests``:

- If the test has ``skip: true``, or the ``topology`` does not match the topology of the server instance(s), skip this test.
- Use either a global MongoClient or a temporary MongoClient to:

  - Drop the database ``database_name``
  - Create the database ``database_name`` and the collection ``database_name.collection_name``

- Create a new MongoClient ``client``, with APM enabled
- Create a changeStream ``changeStream`` against the specified ``target``
- Run every operation in ``operations`` in serial against the server
- Wait until either

  - An error occurres
  - All operations have been successful AND the changeStream has received ``numChanges`` changes

- Close ``changeStream``
- If there was an error

  - Assert that an error was expected for the test.
  - Assert that the error MATCHES ``results.error``

- Else

  - Assert that no error was expected for the test
  - Assert that the changes received from ``changeStream`` MATCH the results in ``results.success``

- If there are any ``expectations``

  - assert that they MATCH the actual APM events

- Close the MongoClient ``client``
