================
Serverless Tests
================

.. contents::

----

Introduction
============

This file describes a subset of existing spec tests as well as some new prose
tests that drivers MUST use to assert compatibility with Serverless.

Test Configuration
==================

These tests MUST be run against a live Serverless instance on Atlas. A new
Serverless instance MUST be created each time the test suite is run, and it MUST
be deleted once the tests have completed, regardless of their outcome. The
`serverless directory in the drivers-evergreen-tools repository`_ contains
scripts for creating and deleting Serverless instances, and the ``config.yml``
contains an example evergreen configuration that uses them to run the tests.

.. _serverless directory in the drivers-evergreen-tools repository: https://github.com/mongodb-labs/drivers-evergreen-tools/tree/master/.evergreen/serverless

All tests MUST be run with wire protocol compression and authentication
enabled. Additionally, Serverless requires the usage of the versioned API, so
the tests MUST be run with a server API version specified.

Required Variables
~~~~~~~~~~~~~~~~~~

Managing the Serverless instances and connecting to them requires a few
variables to be specified. The variables marked "private" are confidential and
MUST be specified as private Evergreen variables or used only in private
Evergreen projects. If using a public Evergreen project, xtrace MUST be disabled
when using these variables to help prevent accidental leaks.

- ``${SERVERLESS_DRIVERS_GROUP}``: Contains the ID of the Atlas group dedicated
  to drivers testing of Serverless.

- ``${SERVERLESS_API_PUBLIC_KEY}``: The public key required to use the Atlas API
  for provisioning of Serverless instances.

- ``${SERVERLESS_API_PRIVATE_KEY}``: (private) The private key required to use
  the Atlas API for provisioning of Serverless instances.

- ``${SERVERLESS_ATLAS_USER}``: (private) The SCRAM username used to
  authenticate to any Serverless instance created in the drivers testing Atlas
  group.

- ``${SERVERLESS_ATLAS_PASSWORD}``: (private) The SCRAM password used to
  authenticate to any Serverless instance created in the drivers testing Atlas
  group.


Existing Spec Tests
===================

Tests defined in the following specifications MUST be included in a driver's
serverless testing suite, including prose tests:

- CRUD, including the v1, v2, and unified tests

In the future, this list will be expanded to include a greater portion of the
tests once the Serverless proxy has more robust failCommand support.

Note that the formats for the JSON/YAML tests of these specifications were
updated to include a new ``runOnRequirement`` specifically for serverless
testing, so make sure to update the affected test runners to support this
requirement and then sync the tests.

The Serverless proxy presents itself as a mongos, so any test meant to run
against sharded clusters will be executed by the runners, with the exception of
the tests affected by the previously mentioned ``runOnRequirement``.

Prose Tests
===========

The following tests MUST be implemented to fully test compatibility with
Serverless.

#. Test that the driver properly constructs and issues a `killCursors
   <https://docs.mongodb.com/manual/reference/command/killCursors/>`_ command to
   the Serverless proxy. For this test, configure an APM listener on a client
   and execute a query on a collection that will leave a cursor open on the
   server (e.g. specify ``batchSize=2`` for a query that would match 3+
   documents). Drivers MAY iterate the cursor if necessary to execute the
   initial ``find`` command but MUST NOT iterate further to avoid executing a
   ``getMore``.

   Observe the CommandSucceededEvent event for the ``find`` command and extract
   the cursor's ID and namespace from the response document's ``cursor.id`` and
   ``cursor.ns`` fields, respectively. Destroy the cursor object and observe
   a CommandStartedEvent and CommandSucceededEvent for the ``killCursors``
   command. Assert that the cursor ID and target namespace in the outgoing
   command match the values from the ``find`` command's CommandSucceededEvent.
   When matching the namespace, note that the ``killCursors`` field will contain
   the collection name and the database may be inferred from either the ``$db``
   field or accessed via the CommandStartedEvent directly. Finally, assert that
   the ``killCursors`` CommandSucceededEvent indicates that the expected cursor
   was killed in the ``cursorsKilled`` field.

#. Repeat test 1 on a cursor that is still left open after both the initial
   ``find`` and a single ``getMore`` (e.g. specify ``batchSize=1`` for a query
   that would match 3+ documents).

Other Tests
===========

Any other existing tests for cursor behavior that a driver may have implemented
independently of any spec requirements SHOULD also be included in the driver's
Serverless testing suite. Note that ChangeStreams are not supported by the
proxy, so tests for them cannot be included.
