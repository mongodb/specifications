=====================
Atlas Data Lake Tests
=====================

.. contents::

----

Introduction
============

The YAML and JSON files in this directory tree are platform-independent tests
that drivers can use to assert compatibility with `Atlas Data Lake <https://docs.mongodb.com/datalake>`_.

Running these integration tests will require a running ``mongohoused``
with data available in its ``test.driverdata`` collection. See the
`ADL directory in drivers-evergreen-tools <https://github.com/mongodb-labs/drivers-evergreen-tools/tree/master/.evergreen/atlas_data_lake>`_
and `10gen/mongohouse README <https://github.com/10gen/mongohouse/blob/master/README.md>`_
for more information.

Several prose tests, which are not easily expressed in YAML, are also presented
in this file. Those tests will need to be manually implemented by each driver.

Test Format
===========

The same as the `CRUD Spec Test format <../../crud/tests/README.rst#Test-Format>`_.

Prose Tests
===========

The following tests MUST be implemented to fully test compatibility with
Atlas Data Lake.

#. Test that the ``killCursors`` command works with Atlas Data Lake.
   For this test, start a query but do not fully iterate over the results
   (e.g. specify batchSize=2 for a query that would match 3+ documents).
   Execute a ``killCursors`` command before executing a ``getMore`` command.
   Continue iterating the cursor to trigger a getMore command and assert
   that ADL raises an error.
   
#. Test that the driver can establish a connection with Atlas Data Lake
   without authentication. For these tests, create a MongoClient using a
   valid connection string without auth credentials and execute a ping
   command.

#. Test that the driver can establish a connection with Atlas Data Lake
   with authentication. For these tests, create a MongoClient using a
   valid connection string with SCRAM-SHA-1 and credentials from the
   drivers-evergreen-tools ADL configuration and execute a ping command.
   Repeat this test using SCRAM-SHA-256.
