======================
Atlas Serverless Tests
======================

.. contents::

----

Introduction
============

This file describes a subset of existing tests that drivers MUST use to assert
compatibility with Atlas Serverless.

Serverless Configuration
========================

These tests MUST be run against a live Atlas Serverless instance. A new instance
MUST be created each time the test suite is run, and that instance MUST be used
for all of the tests required by this specification. Once the tests are
finished, the instance MUST be deleted regardless of the outcome of the tests.
The `serverless directory in the drivers-evergreen-tools repository`_ contains
scripts for creating and deleting Atlas Serverless instances, and the
``config.yml`` contains an example Evergreen configuration that uses them to run
the tests. It can take up to 15 minutes or so to provision a new Atlas
Serverless instance, so it is recommended to create one manually via the scripts
in drivers-evergreen-tools that can be reused for the initial implementation of
the tests before moving to Evergreen patches.

.. _serverless directory in the drivers-evergreen-tools repository: https://github.com/mongodb-labs/drivers-evergreen-tools/tree/master/.evergreen/serverless

Drivers MUST use the `create-instance.sh`_ script in ``drivers-evergreen-tools``
to create a new Atlas Serverless instance for Evergreen tasks. The script writes
a URI for the newly created instance to a YAML expansions file:

.. _create-instance.sh: https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/serverless/create-instance.sh

- ``SERVERLESS_URI`` An SRV connection string to a load balancer fronting a
  single Atlas Serverless proxy.

The ``expansions.update`` Evergreen command can be used to read this file and
copy the URI into a ``SERVERLESS_URI`` environment variable.

Test Runner Configuration
=========================

All tests MUST be run with wire protocol compression and authentication enabled.

In contrast to the `Load Balancer testing`_, which has separate URIs for load
balancers fronting a single or multiple servers, there is only a single URI for
Atlas Serverless testing (i.e. ``SERVERLESS_URI``).

.. _Load Balancer testing: ../load-balancers/tests/README.rst

The TXT record for ``SERVERLESS_URI`` already specifies ``loadBalanced=true`` so
drivers need not add that.

``SERVERLESS_URI`` does not include authentication credentials. Drivers MUST
specify a username and password (see: `Required Variables`_) when connecting to
``SERVERLESS_URI``.

Drivers MUST use ``SERVERLESS_URI`` to configure both internal clients and
clients under test (as described in the `Unified Test Format spec`_).

.. _Unified Test Format spec: ../unified-test-format/unified-test-format.rst

Required Variables
~~~~~~~~~~~~~~~~~~

Managing the Atlas Serverless instances and connecting to them requires a few
variables to be specified. The variables marked "private" are confidential and
MUST be specified as private Evergreen variables or used only in private
Evergreen projects. If using a public Evergreen project, xtrace MUST be disabled
when using these variables to help prevent accidental leaks.

- ``${SERVERLESS_DRIVERS_GROUP}``: Contains the ID of the Atlas group dedicated
  to drivers testing of Atlas Serverless. The backing multi-tenant MongoDB (MTM)
  MUST have the ``SINGLE_TARGET_SERVERLESS_DEPLOYMENT`` feature flag enabled
  (`CLOUDP-117288`_).

- ``${SERVERLESS_API_PUBLIC_KEY}``: The public key required to use the Atlas API
  for managing Atlas Serverless instances.

- ``${SERVERLESS_API_PRIVATE_KEY}``: (private) The private key required to use
  the Atlas API for managing Atlas Serverless instances.

- ``${SERVERLESS_ATLAS_USER}``: (private) The SCRAM username used to
  authenticate to any Atlas Serverless instance created in the drivers testing
  Atlas group.

- ``${SERVERLESS_ATLAS_PASSWORD}``: (private) The SCRAM password used to
  authenticate to any Atlas Serverless instance created in the drivers testing
  Atlas group.

.. _CLOUDP-117288: https://jira.mongodb.org/browse/CLOUDP-117288

Existing Spec Tests
===================

Unified spec tests from all specifications MUST be run against Atlas Serverless.
Since schema version 1.4, unified tests can specify Atlas Serverless
compatibility in their ``runOnRequirements``.

Any prose and legacy spec tests defined in the following specifications MUST be
included in a driver's Atlas Serverless testing suite:

- CRUD
- Load Balancer
- Retryable Reads
- Retryable Writes
- Sessions
- Transactions (excluding convenient API)

  - Note: the killAllSessions command is not supported on Serverless, so the
    transactions tests may hang if an individual test leaves a transaction open
    when it finishes (`CLOUDP-84298`_).
- Versioned/Stable API
- Client Side Encryption

  - Drivers MUST test with a version of the ``crypt_shared`` shared library that
    matches the MongoDB Server version running in Serverless.
    See `Using crypt_shared <https://github.com/mongodb/specifications/tree/e761591616849d9b507287811e77f7a359fb9587/source/client-side-encryption/tests#using-crypt-shared>`_.

.. _CLOUDP-84298: https://jira.mongodb.org/browse/CLOUDP-84298

Note that the legacy JSON/YAML test formats for these specifications were
updated to include a new ``runOnRequirement`` specifically for Atlas Serverless
testing. To ensure these requirements are enforced properly, the runner MUST be
informed that it is running against an Atlas Serverless instance through some
indicator (e.g. an environment variable).

Note that since Atlas Serverless testing uses a load balancer fronting a single
Atlas Serverless proxy, the connection string cannot be modified for
``useMultipleMongoses``. Drivers SHOULD ignore ``useMultipleMongoses`` for
purposes of Atlas Serverless testing.

Other Tests
===========

Any other existing tests for cursor behavior that a driver may have implemented
independently of any spec requirements SHOULD also be included in the driver's
Atlas Serverless testing suite. Note that change streams are not supported by the
proxy, so their spec and prose tests MUST be skipped.


Changelog
=========

:2022-04-22: Testing uses a load balancer fronting a single proxy.
:2021-08-25: Update tests for load balanced serverless instances.

