======================
OCSP Support Test Plan
======================

.. contents::

----------

Introduction
=============

The prose tests defined in this file are platform-independent tests that
drivers can use to prove their conformance to the OCSP Support
specification. These tests MUST BE implemented by all drivers.

Testing Invalid Configurations
==============================

The following tests only apply to drivers that expose an option to
enable/disable certificate revocation checking on a per MongoClient
basis.

1. Create a MongoClient with ``tlsInsecure=true``.

2. Enable certificate revocation checking on the MongoClient

3. Ensure that an error is thrown noting that revocation checking cannot
   be used in combination with ``tlsInsecure=true``.

The following test only applies to drivers that expose an option to
enable/disable certificate revocation checking on a per MongoClient
basis and implement support for ``tlsAllowInvalidCertificates``.

1. Create a MongoClient with ``tlsAllowInvalidCertificates=true``.

2. Enable certificate revocation checking on the MongoClient

3. Ensure that an error is thrown noting that revocation checking cannot
   be used in combination with ``tlsAllowInvalidCertificates=true``.

Integration Tests: Permutations to Be Tested
============================================

For integration tests, we will test all permutations of URI options that
influence a driver’s OCSP behavior with both validity states of the
server’s certificate (configured with the mock OCSP responder). We will
also test the case where an OCSP responder is unavailable and two
malicious server cases.

+----------------------------------------+-----------------------------------------+-------------------------------------------+-------------------------------------------------+---------------------------------------------------+-----------------------------------------------------+-----------------------------------------------------------------------+--------------------------------------------------------------------+
| **URI options**                        | **Test 1\:**                            | **Test 2\:**                              | **Test 3\:**                                    | **Test 4\:**                                      | **Soft Fail Test\:**                                | **Malicious Server Test 1\:**                                         | **Malicious Server Test 2\: No OCSP Responder + server w/ Must-**  |
|                                        | **Valid cert + server that staples**    | **Invalid cert + server that staples**    | **Valid cert + server that does not staple**    | **Invalid cert + server that does not staple**    | **No OCSP Responder + server that does not staple** | **Invalid cert + server w/ Must- Staple cert that does not staple**   | **Staple cert that does not staple**                               |
+========================================+=========================================+===========================================+=================================================+===================================================+=====================================================+=======================================================================+====================================================================+
| ``tls=true``                           | OK                                      | FAIL                                      | OK                                              | FAIL                                              | OK\*                                                | FAIL\*                                                                | FAIL\*                                                             |
+----------------------------------------+-----------------------------------------+-------------------------------------------+-------------------------------------------------+---------------------------------------------------+-----------------------------------------------------+-----------------------------------------------------------------------+--------------------------------------------------------------------+
| | ``tls=true``                         | OK                                      | OK                                        | OK                                              | OK                                                | OK                                                  | OK                                                                    | OK                                                                 |
| | ``&tlsInsecure=true``                |                                         |                                           |                                                 |                                                   |                                                     |                                                                       |                                                                    |
+----------------------------------------+-----------------------------------------+-------------------------------------------+-------------------------------------------------+---------------------------------------------------+-----------------------------------------------------+-----------------------------------------------------------------------+--------------------------------------------------------------------+
| | ``tls=true``                         | OK                                      | OK                                        | OK                                              | OK                                                | OK                                                  | OK                                                                    | OK                                                                 |
| | ``&tlsAllowInvalidCertificates=true``|                                         |                                           |                                                 |                                                   |                                                     |                                                                       |                                                                    |
+----------------------------------------+-----------------------------------------+-------------------------------------------+-------------------------------------------------+---------------------------------------------------+-----------------------------------------------------+-----------------------------------------------------------------------+--------------------------------------------------------------------+

See
`Required Server Versions <../ocsp-support.rst#required-server-versions>`__
to determine which versions of the server can be used for each column.

Note: From the perspective of a driver that does not support OCSP
stapling, the following sets of tests should be identical: {Test 1, Test
3}, {Test 2, Test 4, Malicious Server Test 1}, and {Soft Fail Test,
Malicious Server Test 2}. For drivers with full control over their OCSP behavior, both malicious
server tests are identical as well. However, it does no harm to test these
extra cases and may help reveal unexpected behavior.

\*: Drivers that cannot pass these tests due to limitations in their TLS
library’s implementation of OCSP will need to document these failures as
described under `Documentation
Requirements <../ocsp-support.rst#documentation-requirements>`__

Mock OCSP Responder Testing Suite
==================================

The certificates and scripts needed for testing OCSP are part of
`driver-evergreen-tools <https://github.com/mongodb-labs/drivers-evergreen-tools>`__
in ``.evergreen/ocsp``. Specifically
`mock\_ocsp\_valid.sh <https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/ocsp/mock_ocsp_valid.sh>`__
will start up a mock OCSP responder that will report that every
certificate is valid, and
`mock\_ocsp\_revoked.sh <hhttps://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/ocsp/mock_ocsp_revoked.sh>`__
will start up a mock OCSP responder that will report that every
certificate is invalid.

The mongo-orchestration configurations needed for testing can be found
at ``.evergreen/orchestration/configs/servers/``. Tests that specify that a
server should staple MUST use ``basic-tls-ocsp-mustStaple.json``. Tests that
specify that a server should not staple MUST use
``basic-tls-ocsp-disableStapling.json``. The malicious server tests MUST use
``basic-tls-ocsp-mustStaple-disableStapling.json``.

Test Procedure
==============

Each test column MUST BE its own Evergreen task in order to minimize the
impact of OCSP caching. OCSP caching can exist at the OS-level,
user-level and/or application-level; having separate Evergreen tasks
should help minimize the impact of user-level and application-level
caching since Evergreen performs some cleanup between test runs.

Any OCSP caches that persist between test runs (e.g. the OS-level OCSP
cache) MUST be cleared before configuring a certificate chain. This is
important because the Evergreen instance that is running a driver’s test
may have a cached response from a previous test run (Evergreen instances
are generally reused between test runs), and this cached result could
lead the driver or server to read stale data. See the
`Appendix <../ocsp-support.rst#os-level-ocsp-cache-manipulation>`__
for instructions on how to clear OS-level OCSP caches.

Ensure that a mongod is running with the correct certificate chain (see
`Mock OCSP Responder Testing
Suite `<#mock-ocsp-responder-testing-suite>`__
for configuration details) and that the mock OCSP responder is configured
to report the expected revocation status for that certificate. Again, each
test column MUST BE its own Evergreen task in order to minimize the impact
of user-level and application-level OCSP caching

Extra configuration is required for the malicious server case when
testing on server versions with stapling support: the following
failpoint MUST be set (see `Required Server
Versions <../ocsp-support.rst#required-server-versions>`__) to force
the server to not staple an OCSP response despite having a Must-Staple
certificate.

.. code:: typescript

  db.adminCommand({
    configureFailPoint: “disableStapling”,
    mode: "alwaysOn"
  });

To assert whether a test passes or fails, drivers should create a
MongoClient with the options specified under “URI options”, connect to a
server and attempt to issue a ping command. The success or failure (due
to a TLS error) of the ping command should correlate with the expected
test result.

Drivers may wish to use a smaller value for ``serverSelectionTimeoutMS`` to
speed up tests (otherwise server selection will spin for the entire
duration even after a driver encounters a TLS error early).

Changelog
==========
**2020-1-16**: Initial commit.
