======================
Atlas Serverless Tests
======================

.. contents::

----

Introduction
============

This file describes a subset of existing tests that drivers MUST use to assert
compatibility with Atlas Serverless.

Test Configuration
==================

These tests MUST be run against a live Atlas Serverless instance. A new instance
MUST be created each time the test suite is run, and that instance MUST be used
for all of the tests required by this specification. Once the tests are
finished, the instance MUST be deleted regardless of the outcome of the tests.
The `serverless directory in the drivers-evergreen-tools repository`_ contains
scripts for creating and deleting Atlas Serverless instances, and the
``config.yml`` contains an example evergreen configuration that uses them to run
the tests. It can take up to 15 minutes or so to provision a new Atlas
Serverless instance, so it is recommended to create one manually via the scripts
in drivers-evergreen-tools that can be reused for the initial implementation of
the tests before moving to evergreen patches.

.. _serverless directory in the drivers-evergreen-tools repository: https://github.com/mongodb-labs/drivers-evergreen-tools/tree/master/.evergreen/serverless

All tests MUST be run with wire protocol compression and authentication
enabled.

Required Variables
~~~~~~~~~~~~~~~~~~

Managing the Atlas Serverless instances and connecting to them requires a few
variables to be specified. The variables marked "private" are confidential and
MUST be specified as private Evergreen variables or used only in private
Evergreen projects. If using a public Evergreen project, xtrace MUST be disabled
when using these variables to help prevent accidental leaks.

- ``${SERVERLESS_DRIVERS_GROUP}``: Contains the ID of the Atlas group dedicated
  to drivers testing of Atlas Serverless.

- ``${SERVERLESS_API_PUBLIC_KEY}``: The public key required to use the Atlas API
  for provisioning of Atlas Serverless instances.

- ``${SERVERLESS_API_PRIVATE_KEY}``: (private) The private key required to use
  the Atlas API for provisioning of Atlas Serverless instances.

- ``${SERVERLESS_ATLAS_USER}``: (private) The SCRAM username used to
  authenticate to any Atlas Serverless instance created in the drivers testing
  Atlas group.

- ``${SERVERLESS_ATLAS_PASSWORD}``: (private) The SCRAM password used to
  authenticate to any Atlas Serverless instance created in the drivers testing
  Atlas group.

Existing Spec Tests
===================

Tests defined in the following specifications MUST be included in a driver's
Atlas Serverless testing suite, including prose tests:

- CRUD, including the v1 and unified tests
- Versioned API
- Driver Sessions
- Transactions (excluding convenient API)
    - Note: the killAllSessions command is not supported on Serverless, so the
    transactions tests may hang if an individual test leaves a transaction open
    when it finishes (CLOUDP-84298)
- Load Balancer unified tests

Serverless instances run behind a load balancer. The test topology MUST be
"load-balanced" when comparing a test's ``runOnRequirement`` topology. The
``SINGLE_MONGOS_LB_URI`` and ``MULTI_MONGOS_LB_URI`` must both be set to the
same URI for the serverless instance.

Note that the formats for the JSON/YAML tests of these specifications were
updated to include a new ``runOnRequirement`` specifically for Atlas Serverless
testing, so make sure to update the affected test runners to support this
requirement and then sync the tests. To ensure these requirements are enforced
properly, the runner MUST be informed that it is running against an Atlas
Serverless instance through some indicator (e.g. an environment variable).

Other Tests
===========

Any other existing tests for cursor behavior that a driver may have implemented
independently of any spec requirements SHOULD also be included in the driver's
Atlas Serverless testing suite. Note that ChangeStreams are not supported by the
proxy, so tests for them cannot be included.


Changelog
========
8/23 Note that serverless instances now run behind a load balancer.

