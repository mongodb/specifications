================
Serverless Tests
================

.. contents::

----

Introduction
============

This file describes a subset of existing tests that drivers MUST use to assert
compatibility with serverless MongoDB.

Test Configuration
==================

These tests MUST be run against a live serverless instance on Atlas. A new
serverless instance MUST be created each time the test suite is run, and it MUST
be deleted once the tests have completed, regardless of their outcome. The
`serverless directory in the drivers-evergreen-tools repository`_ contains
scripts for creating and deleting serverless instances, and the ``config.yml``
contains an example evergreen configuration that uses them to run the tests.

.. _serverless directory in the drivers-evergreen-tools repository: https://github.com/mongodb-labs/drivers-evergreen-tools/tree/master/.evergreen/serverless

All tests MUST be run with wire protocol compression and authentication
enabled. Additionally, serverless requires the usage of the versioned API, so
the tests MUST be run with a server API version specified.

Required Variables
~~~~~~~~~~~~~~~~~~

Managing the serverless instances and connecting to them requires a few
variables to be specified. The variables marked "private" are confidential and
MUST be specified as private Evergreen variables or used only in private
Evergreen projects. If using a public Evergreen project, xtrace MUST be disabled
when using these variables to help prevent accidental leaks.

- ``${SERVERLESS_DRIVERS_GROUP}``: Contains the ID of the Atlas group dedicated
  to drivers testing of serverless MongoDB.

- ``${SERVERLESS_API_PUBLIC_KEY}``: The public key required to use the Atlas API
  for provisioning of serverless instances.

- ``${SERVERLESS_API_PRIVATE_KEY}``: (private) The private key required to use
  the Atlas API for provisioning of serverless instances.

- ``${SERVERLESS_ATLAS_USER}``: (private) The SCRAM username used to
  authenticate to any serverless instance created in the drivers testing Atlas
  group.

- ``${SERVERLESS_ATLAS_PASSWORD}``: (private) The SCRAM password used to
  authenticate to any serverless instance created in the drivers testing Atlas
  group.


Existing Spec Tests
===================

Tests defined in the following specifications MUST be included in a driver's
serverless testing suite, including prose tests:

- CRUD, including the v1, v2, and unified tests

In the future, this list will be expanded to include a greater portion of the
tests once the serverless proxy has more robust failCommand support.

Note that the formats for the JSON/YAML tests of these specifications were
updated to include a new ``runOnRequirement`` specifically for serverless
testing, so make sure to update the affected test runners to support this
requirement and then sync the tests.

The serverless proxy presents itself as a mongos, so any test meant to run
against sharded clusters will be executed by the runners, with the exception of
the tests affected by the previously mentioned ``runOnRequirement``.

Other Tests
===========

Any other existing tests for cursor behavior that a driver may have implemented
independently of any spec requirements SHOULD also be included in the driver's
serverless testing suite. Note that ChangeStreams are not supported by the
proxy, so tests for them cannot be included.
