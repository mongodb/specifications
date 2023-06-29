======================
Index Management Tests
======================

.. contents::

----

Test Plan
=========

These prose tests are ported from the legacy enumerate-indexes spec.

Configurations
--------------

- standalone node
- replica set primary node
- replica set secondary node
- mongos node

Preparation
-----------

For each of the configurations:

- Create a (new) database
- Create a collection
- Create a single column index, a compound index, and a unique index
- Insert at least one document containing all the fields that the above
  indicated indexes act on

Tests

- Run the driver's method that returns a list of index names, and:

  - verify that *all* index names are represented in the result
  - verify that there are no duplicate index names
  - verify there are no returned indexes that do not exist

- Run the driver's method that returns a list of index information records, and:

  - verify all the indexes are represented in the result
  - verify the "unique" flags show up for the unique index
  - verify there are no duplicates in the returned list
  - if the result consists of statically defined index models that include an ``ns`` field, verify
    that its value is accurate

Search Index Management Helpers
-------------------------------

These tests are intended to smoke test the search management helpers e2e.  The search index management commands
are asynchronous and mongod/mongos returns before the changes to a clusters' search indexes have completed.  When
these prose tests specify "waiting for the changes", drivers should repeatedly poll the cluster with ``listSearchIndexes``
until the changes are visible.  Each test specifies the criteria which counts as complete.

Since these commands can take a while to run, drivers should raise the timeout for each test to avoid timeout errors.  5 minutes
is a sufficiently large timeout that any timeout that occurs indicates a real failure.

There is a server-side limitation that prevents multiple search indexes from being created with the same name, definition and 
collection name.  This limitation does not take into account collection uuid.  Because these commands are asynchronous, any cleanup
code that may run after a test (cleaning a database or dropping search indexes) may not have completed by the next iteration of the 
test (or the next test run, if running locally).  To address this issue, each test uses a randomly generated collection name.  Drivers
may generate this collection name however they like, but a suggested implementation is a hex representation of an
ObjectId (``new ObjectId().toHexString()`` in Node).

Setup
~~~~~

These tests must run against an Atlas cluster with a 7.0+ server.  Tools are available drivers-evergreen-tools which can setup and teardown
Atlas clusters.  To ensure that the Atlas cluster is cleaned up after each CI run, drivers should configure evergreen to run these tests 
as a part of a task group.  If a driver has an existing task group that creates an Atlas cluster (such as for FAAS testing), this 
task group may be reused as long as the Atlas cluster provisioned satisfies the needs for these tests.

Case 1: Driver can successfully create and list search indexes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Create a collection with a randomly generated name (referred to as ``coll0``).
#. Create a new search index on ``coll0`` with the following definition:

  .. code:: typescript

    {
      name: 'test-search-index',
      definition: {
        mappings: { dynamic: false }
      }
    }

#. Assert that the command does not error and the server responds with a success.
#. Run ``coll0.listSearchIndexes()`` repeatedly every 5 seconds until the following condition is satisfied:
   1. An index with the ``name`` of ``test-search-index`` is present.  This index is referred to as ``index``.
   2. The ``latestDefinition`` property of the search index has the field ``queryable`` with a value of ``true``.
#. Assert that ``index`` has a property ``mappings`` whose value is ``{ dynamic: false }``

Case 2: Driver can successfully create multiple indexes in batch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Create a collection with a randomly generated name (referred to as ``coll0``).
#. Create two new search indexes on ``coll0`` with the ``createSearchIndexes`` command.  Use the following
   definitions when creating the indexes.  These definitions are referred to as ``indexDefinitions``.

  .. code:: typescript

    {
      name: 'test-search-index-1',
      definition: {
        mappings: { dynamic: false }
      }
    }
    {
      name: 'test-search-index-2',
      definition: {
        mappings: { dynamic: false }
      }
    }

#. Assert that the command does not error and the server responds with a success.
#. Run ``coll0.listSearchIndexes()`` repeatedly every 5 seconds until the following condition is satisfied.  Store
   the result in ``indexes``.
   1. An index with the ``name`` of ``test-search-index-1`` is present.  The ``latestDefinition`` property 
      of the search index has the field ``queryable`` with a value of ``true``.
   2. An index with the ``name`` of ``test-search-index-2`` is present.  The ``latestDefinition`` property 
      of the search index has the field ``queryable`` with a value of ``true``.
#. For each ``index`` in ``indexDefinitions``
   1. Find the matching index definition in ``indexes`` by matching on ``index.name``.  If no index exists, raise an error.
   2. Assert that the matching index ``mappings``, whose value is ``{ dynamic: false }``

Case 3: Driver can successfully drop search indexes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Create a collection with a randomly generated name (referred to as ``coll0``).
#. Create a new search index on ``coll0`` with the following definition:

  .. code:: typescript

    {
      name: 'test-search-index',
      definition: {
        mappings: { dynamic: false }
      }
    }

#. Assert that the command does not error and the server responds with a success.
#. Run ``coll0.listSearchIndexes()`` repeatedly every 5 seconds until the following condition is satisfied:
   1. An index with the ``name`` of ``test-search-index`` is present.  This index is referred to as ``index``.
   2. The ``latestDefinition`` property of the search index has the field ``queryable`` with a value of ``true``.

#. Run a ``dropSearchIndexes`` on ``coll0``, using ``test-search-index`` for the name.
#. Run ``coll0.listSearchIndexes()`` repeatedly every 5 seconds until ``listSearchIndexes`` returns an empty array.

This test fails if it times out waiting for the deletion to succeed.

Case 4: Driver can update a search index
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Create a collection with a randomly generated name (referred to as ``coll0``).
#. Create a new search index on ``coll0`` with the following definition:

  .. code:: typescript

    {
      name: 'test-search-index',
      definition: {
        mappings: { dynamic: false }
      }
    }

#. Assert that the command does not error and the server responds with a success.
#. Run ``coll0.listSearchIndexes()`` repeatedly every 5 seconds until the following condition is satisfied:
   1. An index with the ``name`` of ``test-search-index`` is present.  This index is referred to as ``index``.
   2. The ``latestDefinition`` property of the search index has the field ``queryable`` with a value of ``true``.

#. Run a ``updateSearchIndex`` on ``coll0``, using the following definition.
  
  .. code:: typescript

    {
      name: 'test-search-index',
      definition: {
        mappings: { dynamic: true }
      }
    }

#. Assert that the command does not error and the server responds with a success.
#. Run ``coll0.listSearchIndexes()`` repeatedly every 5 seconds until the following condition is satisfied:
   1. An index with the ``name`` of ``test-search-index`` is present.  This index is referred to as ``index``.
   2. The ``latestDefinition`` property of the search index has the field ``queryable`` with a value of ``true``.
   3. The ``latestDefinition`` property of the search index has the field ``status`` with the value of ``READY``.
  
#. Assert that an index is present with the name ``test-search-index`` and the definition has a
  property ``mappings``, whose value is ``{ dynamic: true }``

Case 5: ``dropSearchIndex`` suppresses namespace not found errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Create a driver-side collection object for a randomly generated collection name.  Do not create this collection on the server.
#. Run a ``dropSearchIndex`` command and assert that no error is thrown.