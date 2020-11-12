===================
Versioned API Tests
===================

.. contents::

----

Notes
=====

This directory contains tests for the Versioned API specification. They are
implemented in the `Unified Test Format <../../unified-test-format/unified-test-format.rst>`__,
and require schema version 1.1. Note that to run these tests, the server must be
started with both ``enableTestCommands`` and ``acceptAPIVersion2`` parameters
set to true.

Testing with required API version
=================================

Drivers MUST test against a server with the ``requireApiVersion`` parameter
enabled that also requires authentication. Since API versioning options can't be
specified using the connection string, drivers MUST rely on environment
variables to receive the API version to use in tests. The ``apiStrict`` and
``apiDeprecationErrors`` options are not required for this test.
