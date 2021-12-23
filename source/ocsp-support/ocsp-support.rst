============
OCSP Support
============

:Spec Title: OCSP Support
:Spec Version: 2.1.0
:Author: Vincent Kam
:Lead: Jeremy Mikola
:Advisory Group: Divjot Arora *(POC author)*, Clyde Bazile *(POC author)*, Esha Bhargava *(Program Manager)*, Matt Broadstone, Bernie Hackett *(POC author)*, Shreyas Kaylan *(Server Project Lead)*, Jeremy Mikola *(Spec Lead)*
:Status: Accepted
:Type: Standards
:Minimum Server Version: 4.4
:Last Modified: 2021-12-23

.. contents::

--------

Abstract
========

This specification is about the ability for drivers to to support
`OCSP <https://en.wikipedia.org/wiki/Online_Certificate_Status_Protocol>`__—Online
Certificate Status Protocol (`RFC
6960 <https://tools.ietf.org/html/rfc6960>`__)—and two of its related
extensions: `OCSP
stapling <https://en.wikipedia.org/wiki/OCSP_stapling>`__ (`RFC
6066 <https://tools.ietf.org/html/rfc6066>`__) and
`Must-Staple <https://scotthelme.co.uk/ocsp-must-staple/>`__ (`RFC
7633 <https://tools.ietf.org/html/rfc7633>`__).

META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

Required Server Versions
------------------------

The server supports attaching a stapled OCSP response with versions ≥
4.4. Future backports will bring stapling support to server versions ≥
3.6. Drivers need not worry about the version of the server as a
driver’s TLS library should automatically perform the proper certificate
revocation checking behavior once OCSP is enabled.

Enabling OCSP Support by Default
--------------------------------

Drivers whose TLS libraries utilize application-wide settings for OCSP
MUST respect the application’s settings and MUST NOT change any OCSP
settings. Otherwise:

-  If a driver’s TLS library supports OCSP, OCSP MUST be enabled by
   default whenever possible (even if this also enables Certificate
   Revocation List (CRL) checking).

-  If a driver’s TLS library supports verifying stapled OCSP responses,
   this option MUST be enabled by default whenever possible (even if
   this also enables CRL checking).

.. _Suggested OCSP Behavior:

Suggested OCSP Behavior
-----------------------

Drivers SHOULD implement the OCSP behavior defined below to the extent
that their TLS library allows. At any point in the steps defined below,
if a certificate in or necessary to validate the chain is found to be
invalid, the driver SHOULD end the connection.

1.  If a driver’s TLS library supports Stapled OCSP, the server has a
    Must-Staple certificate and the server does not present a
    stapled OCSP response, a driver SHOULD end the connection.

2.  If a driver’s TLS library supports Stapled OCSP and the server
    staples an OCSP response that does not cover the certificate it presents or
    is invalid per `RFC 6960 Section 3.2 <https://tools.ietf.org/html/rfc6960#section-3.2>`_,
    a driver SHOULD end the connection.

3.  If a driver’s TLS library supports Stapled OCSP and the server
    staples an OCSP response that does cover the certificate it
    presents, a driver SHOULD accept the stapled OCSP response and
    validate all of the certificates that are presented in the
    response.

4.  If any unvalidated certificates in the chain remain and the client
    possesses an OCSP cache, the driver SHOULD attempt to validate
    the status of the unvalidated certificates using the cache.

5.  If any unvalidated certificates in the chain remain and the driver
    has a user specified CRL, the driver SHOULD attempt to validate
    the status of the unvalidated certificates using the
    user-specified CRL.

6.  If any unvalidated certificates in the chain remain and the driver
    has access to cached CRLs (e.g.
    OS-level/application-level/user-level caches), the driver SHOULD
    attempt to validate the status of the unvalidated certificates
    using the cached CRLs.

7.  If the server’s certificate remains unvalidated, that certificate
    has a list of OCSP responder endpoints, and
    ``tlsDisableOCSPEndpointCheck`` or
    ``tlsDisableCertificateRevocationCheck`` is false (`if the driver
    supports these options <MongoClient Configuration>`_), the driver SHOULD
    send HTTP requests to the responders in parallel. The first valid
    response that concretely marks the certificate status as good or revoked
    should be used. A timeout should be applied to requests per the `Client
    Side Operations Timeout
    <../client-side-operations-timeout/client-side-operations-timeout>`__
    specification, with a default timeout of five seconds. The status for a
    response should only be checked if the response is valid per `RFC 6960
    Section 3.2 <https://tools.ietf.org/html/rfc6960#section-3.2>`_

8.  If any unvalidated intermediate certificates remain and those
    certificates have OCSP endpoints, for each certificate, the
    driver SHOULD NOT reach out to the OCSP endpoint specified and
    attempt to validate that certificate.\*

9.  If any unvalidated intermediate certificates remain and those
    certificates have CRL distribution points, the driver SHOULD NOT
    download those CRLs and attempt to validate the status of all
    the other certificates using those CRLs.\*

10. Finally, the driver SHOULD continue the connection, even if the
    status of all the unvalidated certificates has not been
    confirmed yet. This means that the driver SHOULD default to
    "soft fail" behavior, connecting as long as there are no
    explicitly invalid certificates—i.e. the driver will connect
    even if the status of all the unvalidated certificates has not
    been confirmed yet (e.g. because an OCSP responder is down).

\*: See `Design Rationale: Suggested OCSP Behavior <ocsp-support.rst#id7>`__

Suggested OCSP Response Validation Behavior
-------------------------------------------

Drivers SHOULD validate OCSP Responses in the manner specified in `RFC
6960: 3.2 <https://tools.ietf.org/html/rfc6960#section-3.2>`__ to the
extent that their TLS library allows.

Suggested OCSP Caching Behavior
-------------------------------
Drivers with sufficient control over their TLS library's OCSP
behavior SHOULD implement an OCSP cache. The key for this cache
SHOULD be the certificate identifier (CertID) of the OCSP request
as specified in `RFC 6960: 4.1.1
<https://tools.ietf.org/html/rfc6960#section-4.1.1>`__.
For convenience, the relevant section has been duplicated below:

.. code:: ASN.1

   CertID          ::=     SEQUENCE {
       hashAlgorithm       AlgorithmIdentifier,
       issuerNameHash      OCTET STRING, -- Hash of issuer's DN
       issuerKeyHash       OCTET STRING, -- Hash of issuer's public key
       serialNumber        CertificateSerialNumber }

If a driver would accept a conclusive OCSP response (stapled or
non-stapled), the driver SHOULD cache that response. We define a
conclusive OCSP response as an OCSP response that indicates that a
certificate is either valid or revoked. Thus, an unknown certificate
status SHOULD NOT be considered conclusive, and the corresponding OCSP
response SHOULD NOT be cached.

In accordance with `RFC: 6960: 3.2
<https://tools.ietf.org/html/rfc6960#section-3.2>`__,
a cached response SHOULD be considered valid up to and excluding
the time specified in the response's ``nextUpdate`` field.
In other words, if the current time is *t*, then the cache entry
SHOULD be considered valid if *thisUpdate ⩽ t < nextUpdate*.

If a driver would accept a stapled OCSP response and that response
has a later ``nextUpdate`` than the response already in the cache,
drivers SHOULD replace the older entry in the cache with the fresher
response.

MongoClient Configuration
--------------------------

This specification introduces the client-level configuration options
defined below.

tlsDisableOCSPEndpointCheck
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Drivers that can, on a per MongoClient basis, disable non-stapled OCSP
while keeping stapled OCSP enabled MUST implement this option.

This boolean option determines whether a MongoClient should refrain from
reaching out to an OCSP endpoint i.e.  whether non-stapled OCSP should
be disabled.  When set to true, a driver MUST NOT reach out to OCSP
endpoints. When set to false, a driver MUST reach out to OCSP
endpoints if needed (as described in
`Specification: Suggested OCSP Behavior <ocsp-support.rst#id1>`__).

For drivers that pass the `"Soft Fail Test"
<tests/README.rst#integration-tests-permutations-to-be-tested>`__, this
option MUST default to false.

For drivers that fail the "Soft Fail Test" because their TLS library
exhibits hard-fail behavior when a responder is unreachable, this option
MUST default to true, and a driver MUST document this behavior. If this
hard-failure behavior is specific to a particular platform (e.g. the TLS
library hard-fails only on Windows) then this option MUST default to
true only on the platform where the driver exhibits hard-fail behavior,
and a driver MUST document this behavior.

tlsDisableCertificateRevocationCheck
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Drivers whose TLS libraries support an option to toggle general
certificate revocation checking must implement this option if enabling
general certificate revocation checking causes hard-fail behavior when
no revocation mechanisms are available (i.e. no methods are defined
or the CRL distribution points/OCSP endpoints are unreachable).

This boolean option determines whether a MongoClient should refrain
checking certificate revocation status. When set to true, a driver
MUST NOT check certificate revocation status via CRLs or OCSP.  When
set to false, a driver MUST check certificate revocation status, reach
out to OCSP endpoints if needed (as described in
`Specification: Suggested OCSP Behavior <ocsp-support.rst#id1>`__).

For drivers that pass the `"Soft Fail Test"
<tests/README.rst#integration-tests-permutations-to-be-tested>`__ , this
option MUST default to false.

If a driver does not support ``tlsDisableOCSPEndpointCheck`` and
that driver fails the "Soft Fail Test" because their TLS
library exhibits hard-fail behavior when a responder is unreachable,
then that driver must default `tlsDisableCertificateRevocationCheck` to
true. Such a driver also MUST document this behavior. If this
hard-failure behavior is specific to a particular platform (e.g. the
TLS library hard-fails only on Windows) then this option MUST default
to true only on the platform where the driver exhibits hard-fail
behavior, and a driver MUST document this behavior.

Naming Deviations
^^^^^^^^^^^^^^^^^^

Drivers MUST use the defined names of ``tlsDisableOCSPEndpointCheck``
and ``tlsDisableCertificateRevocationCheck`` for the connection string
parameters to ensure portability of connection strings across
applications and drivers. If drivers solicit MongoClient options
through another mechanism (e.g. an options dictionary provided to the
MongoClient constructor), drivers SHOULD use the defined name but MAY
deviate to comply with their existing conventions. For example, a
driver may use ``tls_disable_ocsp_endpoint_check`` instead of
``tlsDisableOCSPEndpointCheck``.

How OCSP interacts with existing configuration options
------------------------------------------------------

The following requirements apply only to drivers that are able to
enable/disable OCSP on a per MongoClient basis.

1. If a connection string specifies ``tlsInsecure=true`` then the
   driver MUST disable OCSP.

2. If a connection string contains both ``tlsInsecure`` and
   ``tlsDisableOCSPEndpointCheck`` then the driver MUST throw an
   error.

3. If a driver supports ``tlsAllowInvalidCertificates``, and a
   connection string specifies ``tlsAllowInvalidCertificates=true``,
   then the driver MUST disable OCSP.

4. If a driver supports ``tlsAllowInvalidCertificates``, and a
   connection string specifies both ``tlsAllowInvalidCertificates``
   and ``tlsDisableOCSPEndpointCheck``, then the driver MUST
   throw an error.

The remaining requirements in this section apply only to drivers that
expose an option to enable/disable certificate revocation checking on a
per MongoClient basis.

1. Driver MUST enable OCSP support (with stapling if possible) when
   certificate revocation checking is enabled **unless** their driver
   exhibits hard-fail behavior (see
   `tlsDisableCertificateRevocationCheck`_). In such a case, a driver
   MUST disable OCSP support on the platforms where its TLS library
   exhibits hard-fail behavior.

2. Drivers SHOULD throw an error if any of ``tlsInsecure=true`` or
   ``tlsAllowInvalidCertificates=true`` or
   ``tlsDisableOCSPEndpointCheck=true`` is specified alongside the
   option to enable certificate revocation checking.

3. If a connection string contains both ``tlsInsecure`` and
   ``tlsDisableCertificateRevocationCheck`` then the driver MUST throw
   an error.

4. If a driver supports ``tlsAllowInvalidCertificates`` and a
   connection string specifies both ``tlsAllowInvalidCertificates``
   and ``tlsDisableCertificateRevocationCheck``, then the driver MUST
   throw an error.

5. If a driver supports ``tlsDisableOCSPEndpointCheck``, and a
   connection string specifies ``tlsDisableCertificateRevocationCheck``,
   then the driver MUST throw an error.


TLS Requirements
----------------
`Server Name Indication
<https://en.wikipedia.org/wiki/Server_Name_Indication>`__ (SNI) MUST BE
used in the TLS connection that obtains the server's certificate,
otherwise the server may present the incorrect certificate. This
requirement is especially relevant to drivers whose TLS libraries allow
for finer-grained control over their TLS behavior (e.g. Python, C).


Documentation Requirements
--------------------------

Drivers that cannot support OCSP MUST document this lack of support.
Additionally, such drivers MUST document the following:

-  They MUST document that they will be unable to support certificate
   revocation checking with Atlas when Atlas moves to OCSP-only
   certificates.

-  They MUST document that users should be aware that if they use a
   Certificate Authority (CA) that issues OCSP-only certificates,
   then the driver cannot perform certificate revocation checking.

Drivers that support OCSP without stapling MUST document this lack of
support for stapling. They also MUST document their behavior when an
OCSP responder is unavailable and a server has a Must-Staple
certificate. If a driver is able to connect in such a scenario due to
the prevalence of
"\ `soft-fail <https://www.imperialviolet.org/2014/04/19/revchecking.html>`__\ "
behavior in TLS libraries (where a certificate is accepted when an
answer from an OCSP responder cannot be obtained), they additionally
MUST document that this ability to connect to a server with a
Must-Staple certificate when an OCSP responder is unavailable differs
from the mongo shell or a driver that does support OCSP-stapling, both
of which will fail to connect (i.e. "hard-fail") in such a scenario.

If a driver (e.g.
`Python <https://api.mongodb.com/python/current/examples/tls.html>`__,
`C <http://mongoc.org/libmongoc/current/mongoc_ssl_opt_t.html>`__)
allows the user to provide their own certificate revocation list (CRL),
then that driver MUST document their TLS library’s preference between
the user-provided CRL and OCSP.

Drivers that cannot enable OCSP by default on a per MongoClient basis
(e.g. Java) MUST document this limitation.

Drivers that fail either of the "Malicious Server Tests" (i.e. the
driver connects to a test server without TLS constraints being relaxed)
as defined in the test plan below MUST document that their chosen TLS
library will connect in the case that a server with a Must-Staple
certificate does not staple a response.

Drivers that fail "Malicious Server Test 2" (i.e. the driver connects to
the test server without TLS constraints being relaxed) as defined in the
test plan below MUST document that their chosen TLS library will connect
in the case that a server with a Must-Staple certificate does not staple
a response and the OCSP responder is down.

Drivers that fail "Soft Fail Test" MUST document that their driver’s
TLS library utilizes "hard fail" behavior in the case of an
unavailable OCSP responder in contrast to the mongo shell and drivers
that utilize "soft fail" behavior. They also MUST document the change
in defaults for the applicable options (see `MongoClient
Configuration`_).

If any changes related to defaults for OCSP behavior are made after a
driver version that supports OCSP has been released, the driver MUST
document potential backwards compatibility issues as noted in the
`Backwards Compatibility`_ section.

Test Plan
==========
See `tests/README <tests/README.rst>`__ for tests.

Motivation for Change
======================

MongoDB Atlas intends to use
`LetsEncrypt <https://letsencrypt.org/>`__, a Certificate Authority
(CA) that does not use CRLs and only uses OCSP. (Atlas currently uses
DigiCert certificates which specify both OCSP endpoints and CRL
distribution points.) Therefore, the MongoDB server is adding support
for OCSP, and drivers need to support OCSP in order for applications to
continue to have the ability to verify the revocation status of an Atlas
server’s certificate. Other CAs have also stopped using CRLs, so
enabling OCSP support will ensure that a customer’s choice in CAs is not
limited by a driver’s lack of OCSP support.

OCSP stapling will also help applications deployed behind a firewall
with an outbound allowList. It’s a very natural mistake to neglect to
allowList the CRL distribution points and the OCSP endpoints, which can
prevent an application from connecting to a MongoDB instance if
certificate revocation checking is enabled but the driver does not
support OCSP stapling.

Finally, drivers whose TLS libraries support `OCSP
stapling <https://en.wikipedia.org/wiki/OCSP_stapling>`__ extension
will be able to minimize the number of network round trips for the
client because the driver’s TLS library will read an OCSP response
stapled to the server’s certificate that the server provides as part of
the TLS handshake. Drivers whose TLS libraries support OCSP but not
stapling will need to make an additional round trip to contact the OCSP
endpoint.

Design Rationale
=================

We have chosen not to force drivers whose TLS libraries do not support
OCSP/stapling "out of the box" to implement OCSP support due to the
extra work and research that this might require. Similarly, this
specification uses "SHOULD" more commonly (when other specs would
prefer "MUST") to account for the fact that some drivers may not be
able to fully customize OCSP behavior in their TLS library.

We are requiring drivers to support both stapled OCSP and non-stapled
OCSP in order to support revocation checking for server versions in
Atlas that do not support stapling, especially after Atlas switches to
Let’s Encrypt certificates (which do not have CRLs). Additionally, even
when servers do support stapling, in the case of a non-"Must Staple"
certificate (which is the type that Atlas is planning to use), if the
server is unable to contact the OCSP responder (e.g. due to a network
error) and staple a certificate, the driver being able to query the
certificate’s OCSP endpoint allows for one final chance to attempt to
verify the certificate’s validity.

Malicious Server Tests
----------------------

"Malicious Server Test 2" is designed to reveal the behavior of TLS
libraries of drivers in one of the worst case scenarios. Since a
majority of the drivers will not have fine-grained control over their
OCSP behavior, this test case provides signal about the soft/hard fail
behavior in a driver’s TLS library so that we can document this.

A driver with control over its OCSP behavior will react the same in
"Malicious Server Test 1" and "Malicious Server Test 2", terminating the
connection as long as TLS constraints have not been relaxed.

Atlas Connectivity Tests
------------------------

No additional Atlas connectivity tests will be added because the
existing tests should provide sufficient coverage (provided that one of
the non-free tier clusters is upgraded ≥ 3.6).

.. _Design Rationale for Suggested OCSP Behavior:

Suggested OCSP Behavior
-----------------------

For drivers with finer-grain control over their OCSP behavior, the
suggested OCSP behavior was chosen as a balance between security and
availability, erring on availability while minimizing network round
trips. Therefore, in the
`Specification: Suggested OCSP Behavior <ocsp-support.rst#id1>`__ section,
in order to minimize network round trips, drivers are advised not to
reach out to OCSP endpoints and CRL distribution points in order to
verify the revocation status of intermediate certificates.

Backwards Compatibility
========================

An application behind a firewall with an outbound allowList that
upgrades to a driver implementing this specification may experience
connectivity issues when OCSP is enabled. This is because the driver may need to contact
OCSP endpoints or CRL distribution points [1]_ specified in the
server’s certificate and if these OCSP endpoints and/or CRL
distribution points are not accessible, then the connection to the
server may fail. (N.B.: TLS libraries `typically implement "soft fail"
<https://blog.hboeck.de/archives/886-The-Problem-with-OCSP-Stapling-and-Must-Staple-and-why-Certificate-Revocation-is-still-broken.html>`__
such that connections can continue even if the OCSP server is
inaccessible, so this issue is much more likely in the case of a
server with a certificate that only contains CRL distribution points.)
In such a scenario, connectivity may be able to be restored by
disabling non-stapled OCSP via ``tlsDisableOCSPEndpointCheck`` or by
disabling certificate revocation checking altogether
via ``tlsDisableCertificateRevocationCheck``.

An application that uses a driver that utilizes hard-fail behavior
when there are no certificate revocation mechanisms available may also
experience connectivity issue. Cases in which no certificate
revocation mechanisms being available include:

1. When a server's certificate defines neither OCSP endpoints nor CRL
   distribution points
2. When a certificate defines CRL distribution points and/or OCSP
   endpoints but these points are unavailable (e.g. the points are
   down or the application is deployed behind a restrictive firewall).

In such a scenario, connectivity may be able to be restored by disabling
non-stapled OCSP via ``tlsDisableOCSPEndpointCheck`` or by disabling
certificate revocation checking via
``tlsDisableCertificateRevocationCheck``.

Reference Implementation
=========================

The .NET/C#, Python, C, and Go drivers will provide the reference
implementations. See
`CSHARP-2817 <https://jira.mongodb.org/browse/CSHARP-2817>`__,
`PYTHON-2093 <https://jira.mongodb.org/browse/PYTHON-2093>`__,
`CDRIVER-3408 <https://jira.mongodb.org/browse/CDRIVER-3408>`__ and
`GODRIVER-1467 <http://jira.mongodb.org/browse/GODRIVER-1467>`__.

Security Implications
=====================

Customers should be aware that if they choose to use CA that only
supports OCSP, they will not be able to check certificate validity in
drivers that cannot support OCSP.

In the case that the server has a Must-Staple certificate and its OCSP
responder is down (for longer than the server is able to cache and
staple a previously acquired response), the mongo shell or a driver that
supports OCSP stapling will not be able to connect while a driver that
supports OCSP but not stapling will be able to connect.

TLS libraries may implement
"\ `soft-fail <https://www.imperialviolet.org/2014/04/19/revchecking.html>`__\ "
in the case of non-stapled OCSP which may be undesirable in highly
secure contexts.

Drivers that fail the "Malicious Server" tests as defined in Test Plan
will connect in the case that server with a Must-Staple certificate does
not staple a response.

Testing Against Valid Certificate Chains
----------------------------------------

Some TLS libraries are stricter about the types of certificate chains
they're willing to accept (and it can be difficult to debug why a
particular certificate chain is considered invalid by a TLS library).
Clients and servers with more control over their OCSP implementation may
run into fewer up front costs, but this may be at the cost of not fully
implementing every single aspect of OCSP.

For example, the server team’s certificate generation tool generated
X509 V1 certificates which were used for testing OCSP without any issues
in the server team’s tests. However, while we were creating a test plan
for drivers, we discovered that Java’s keytool refused to import X509 V1
certificates into its trust store and thus had to modify the server
team’s certificate generation tool to generate V3 certificates.

Another example comes from `.NET on
Linux <https://github.com/dotnet/corefx/issues/41475>`__, which
currently enforces the CA/Browser forum requirement that while a leaf
certificate can be covered solely by OCSP, "public CAs have to have
CRL[s] covering their issuing CAs". This requirement is not enforced
with Java’s default TLS libraries. See also: `Future Work: CA/Browser
Forum Requirements
Complications <#cabrowser-forum-requirements-complications>`__.

Future Work
============

When the server work is backported, drivers will need to update their
prose tests so that tests are run against a wider range of compatible
servers.

Automated Atlas connectivity tests
(`DRIVERS-382 <https://jira.mongodb.org/browse/DRIVERS-382>`__) may be
updated with additional OCSP-related URIs when 4.4 becomes available for
Atlas; alternatively, the clusters behind those URIs may be updated to
4.4 (or an earlier version where OCSP has been backported). Note: While
the free tier cluster used for the Automated Atlas connectivity tests
will automatically get updated to 4.4 when it is available, Atlas
currently does not plan to enable OCSP for free and shared tier
instances (i.e. Atlas Proxy).

Options to configure failure behavior (e.g. to maximize security or
availability) may be added in the future.

CA/Browser Forum Requirements Complications
-------------------------------------------

The test plan may need to be reworked if we discover that a driver’s TLS
library strictly implements CA/Browser forum requirements (e.g. `.NET
on Linux <https://github.com/dotnet/corefx/issues/41475>`__). This is
because our current chain of certificates does not fulfill the following
requirement: while a leaf certificate can be covered solely by OCSP,
"public CAs have to have CRL[s] covering their issuing CAs." This rework
of the test plan may happen during the initial implementation of OCSP
support or happen later if a driver’s TLS library implements the
relevant CA/Browser forum requirement.

Extending the chain to fulfill the CA/Browser requirement should solve
this issue, although drivers that don't support manually supplying a CRL
may need to host a web server that serves the required CRL during
testing.

Q&A
====

Can we use one Evergreen task combined with distinct certificates for each column in the test matrix to prevent OCSP caching from affecting testing?
----------------------------------------------------------------------------------------------------------------------------------------------------

No. This is because Evergreen may reuse a host with an OCSP cache from a
previous execution, so using distinct certificates per column would not
obviate the need to clear all relevant OCSP caches prior to each test
run. Since Evergreen does perform some cleanup between executions,
having separate tasks for each test column offers an additional layer of
safety in protecting against stale data in OCSP caches.

Should drivers use a nonce when creating an OCSP request?
---------------------------------------------------------
A driver MAY use a nonce if desired, but `including a nonce in an OCSP
request <https://tools.ietf.org/html/rfc6960#section-4.4.1>`__
is not required as the server does not explicitly support nonces.

Should drivers utilize a tolerance period when accepting OCSP responses?
------------------------------------------------------------------------
No. Although `RFC 5019, The Lightweight Online Certificate Status Protocol
(OCSP) Profile for High-Volume Environments, <https://tools.ietf.org/html/rfc5019>`__
allows for the configuration of a tolerance period for the acceptance of OCSP
responses after ``nextUpdate``, this spec is not adhering to that RFC.

Why was the decision made to allow OCSP endpoint checking to be enabled/disabled via a URI option?
---------------------------------------------------------------------------------------------------
We initially hoped that we would be able to not expose any options
specifically related to OCSP to the user, in accordance with the
"\`No Knobs" drivers mantra
<https://github.com/mongodb/specifications#no-knobs>`__. However, we
later decided that users may benefit from having the ability to
disable OCSP endpoint checking when applications are deployed behind
restrictive firewall with outbound allowLists, and this benefit is
worth adding another URI option.

Appendix
========

OS-Level OCSP Cache Manipulation
--------------------------------

Windows
^^^^^^^

On Windows, the OCSP cache can be viewed like so:

.. code-block:: console

  certutil -urlcache

To search the cache for "Lets Encrypt" OCSP cache entries, the following
command could be used:

.. code-block:: console

  certutil -urlcache | findstr letsencrypt.org

On Windows, the OCSP cache can be cleared like so:

.. code-block:: console

  certutil -urlcache * delete

To delete only "Let’s Encrypt" related entries, the following command
could be used:

.. code-block:: console

  certutil -urlcache letsencrypt.org delete

macOS
^^^^^

On macOS 10.14, the OCSP cache can be viewed like so:

.. code-block:: console

  find ~/profile/Library/Keychains -name 'ocspcache.sqlite3' \
  -exec sqlite3 "{}" 'SELECT responderURI FROM responses;' \;

To search the cache for "Let’s Encrypt" OCSP cache entries, the
following command could be used:

.. code-block:: console

  find ~/profile/Library/Keychains \
  -name 'ocspcache.sqlite3' \
  -exec sqlite3 "{}" \
  'SELECT responderURI FROM responses WHERE responderURI LIKE "http://%.letsencrypt.org%";' \;

On macOS 10.14, the OCSP cache can be cleared like so:

.. code-block:: console

  find ~/profile/Library/Keychains -name 'ocspcache.sqlite3' \
  -exec sqlite3 "{}" 'DELETE FROM responses ;' \;

To delete only "Let’s Encrypt" related entries, the following command
  could be used:

.. code-block:: console

  find ~/profile/Library/Keychains -name 'ocspcache.sqlite3' \
  -exec sqlite3 "{}" \
  'DELETE FROM responses WHERE responderURI LIKE "http://%.letsencrypt.org%";' \;

Optional Quick Manual Validation Tests of OCSP Support
------------------------------------------------------

These optional validation tests are not a required part of the test
plan. However, these optional tests may be useful for drivers trying to
quickly determine if their TLS library supports OCSP and/or as an
initial manual testing goal when implementing OCSP support.

Optional test to ensure that the driver’s TLS library supports OCSP stapling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a test application with a connection string with TLS enabled that
connects to any server that has OCSP-only certificate and supports OCSP
stapling.

For example, the test application could connect to C\ :sub:`V`, one of
the special testing Atlas clusters with a valid OCSP-only certificate.
see Future Work for additional information).

Alternatively, the test application can attempt to connect to a
**non-mongod server** that supports OCSP-stapling and has a valid an
OCSP-only certificate. The connection will fail of course, but we are
only interested in the TLS handshake and the OCSP requests that may
follow. For example, the following connection string could be used:
``mongodb://valid-isrgrootx1.letsencrypt.org:443/?tls=true``

Run the test application and verify through packet analysis that the
driver’s ClientHello message’s TLS extension section includes the
``status_request`` extension, thus indicating that the driver is advertising
that it supports OCSP stapling.

Note: If using `WireShark <https://www.wireshark.org/>`__ as your
chosen packet analyzer, the ``tls`` (case-sensitive) display filter may be
useful in this endeavor.

OCSP Caching and the optional test to ensure that the driver’s TLS library supports non-stapled OCSP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The "Optional test to ensure that the driver’s TLS library supports
non-stapled OCSP" is complicated by the fact that OCSP allows the client
to `cache the OCSP
responses <https://tools.ietf.org/html/rfc5019#section-6.1>`__, so
clearing an OCSP cache may be needed in order to force the TLS library
to reach out to an OCSP endpoint. This cache may exist at the OS-level,
application-level and/or at the user-level.

Optional test to ensure that the driver’s TLS library supports non-stapled OCSP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a test application with a connection string with TLS enabled that
connects to any server with an OCSP-only certificate.

Alternatively, the test application can attempt to connect to a
**non-mongod server** that does not support OCSP-stapling and has a
valid an OCSP-only certificate. The connection will fail of course, but
we are only interested in the TLS handshake and the OCSP requests that
may follow.

Alternatively, if it’s known that a driver’s TLS library does not
support stapling or if stapling support can be toggled off, then any
**non-mongod server** that has a valid an OCSP-only certificate will
work, including the example shown in the "Optional test to ensure that
the driver’s TLS library supports OCSP stapling."

Clear the OS/user/application OCSP cache, if one exists and the TLS
library makes use of it.

Run the test application and ensure that the TLS handshake succeeds.
connection succeeds. Ensure that the driver’s TLS library has contacted
the OCSP endpoint specified in the server’s certificate. Two simple ways
of checking this are:

-  Use a packet analyzer while the test application is running to ensure
   that the driver’s TLS library contacts the OCSP endpoint. When
   using WireShark, the ``ocsp`` and ``tls`` (case-sensitive) display
   filters may be useful in this endeavor.

-  If the TLS library utilizes an OCSP cache and the cache was cleared
   prior to starting the test application, check the OCSP cache for
   a response from an OCSP endpoint specified in the server's
   certificate.

Changelog
==========

**2021-12-23**: 2.1.0: Require that timeouts be applied per the client-side
operations timeout spec.

**2021-04-07**: 2.0.1: Updated terminology to use allowList.

**2020-07-01**: 2.0.0: Default tlsDisableOCSPEndpointCheck or
tlsDisableCertificateRevocationCheck to true in the case that a driver's
TLS library exhibits hard-fail behavior and add provision for
platform-specific defaults.

**2020-03-20**: 1.3.1: Clarify OCSP documentation requirements for
drivers unable to enable OCSP by default on a per MongoClient basis.

**2020-03-03**: 1.3.0: Add tlsDisableCertificateRevocationCheck URI
option. Add Go as a reference implementation. Add hard-fail backwards
compatibility documentation requirements.

**2020-02-26**: 1.2.0: Add tlsDisableOCSPEndpointCheck URI option.

**2020-02-19**: 1.1.1 Clarify behavior for reaching out to OCSP responders.

**2020-02-10**: 1.1.0: Add cache requirement.

**2020-01-31**: 1.0.2: Add SNI requirement and clarify design rationale
regarding minimizing round trips.

**2020-01-28**: 1.0.1: Clarify behavior regarding nonces and tolerance periods.

**2020-01-16**: 1.0.0: Initial commit.

Endnotes
========
.. [1]
   Since this specification mandates that a driver must enable OCSP when
   possible, this may involve enabling certificate revocation checking
   in general, and thus the accessibility of CRL distribution points can
   become a factor.
