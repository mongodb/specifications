.. role:: javascript(code)
  :language: javascript

==============================
Initial DNS Seedlist Discovery
==============================

:Spec-ticket: SPEC-878
:Title: Initial DNS Seedlist Discovery
:Authors: Derick Rethans
:Status: Draft
:Type: Standards
:Last Modified: 2017-08-29
:Version: 1.0
:Spec Lead: Matt Broadstone
:Advisory Group: \A. Jesse Jiryu Davis
:Approver(s): Bernie Hackett, David Golden, Jeff Yemin, Matt Broadstone, A. Jesse Jiryu Davis


.. contents::

--------

Abstract
========

Presently, seeding a driver with an initial list of ReplicaSet or MongoS
addresses is somewhat cumbersome, requiring a comma-delimited list of host
names to attempt connections to.  A standardized answer to this problem exists
in the form of SRV records, which allow administrators to configure a single
domain to return a list of host names. Supporting this feature would assist
our users by decreasing maintenance load, primarily by removing the need to
maintain seed lists at an application level.

META
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

The connection string parser in the driver is extended with a new protocol
``mongodb+srv`` as a logical pre-processing step before it considers the
connection string and SDAM specifications. In this protocol, the comma
separated list of hostnames is replaced with a single (domain name). The
format is::

    mongodb+srv://servername.example.com/{options}

In this preprocessing step, the driver will query the DNS server for the SRV
record ``_mongodb._tcp.servername.example.com``. This DNS query is expected to
respond with one or more SRV records. From the DNS result, the driver now MUST
behave the same as if an ``mongodb://`` URI was provided with all the host names
and port numbers that were returned as part of the DNS SRV query result.

The priority and weight fields in returned SRV records MUST be ignored.

It is an error to specify a port in a connection string with the
``mongodb+srv`` protocol, and the driver MUST raise a parse error and MUST NOT
do DNS resolution or contact hosts.

The driver MUST NOT attempt to connect to any hosts until the DNS query has
returned its results.

If the DNS result returns no SRV records, or no records at all, or a DNS error
happens, an error MUST be raised indicating that the URI could not be used to
find hostnames. The error SHALL include the reason why they could not be
found. This error MUST be raised only when the application attempts any
operation which requires a server, in the same way as other server selection
errors.


Example
=======

If we provide the following URI::

    mongodb+srv://server.mongodb.com/?connectTimeoutMS=300000

The driver needs to request the DNS server for the SRV record
``_mongodb._tcp.server.mongodb.com``. This could return::

    Record                            TTL   Class    Priority Weight Port  Target
    _mongodb._tcp.server.mongodb.com. 86400 IN SRV   0        5      27317 mongodb1.mongodb.com.
    _mongodb._tcp.server.mongodb.com. 86400 IN SRV   0        5      27017 mongodb2.mongodb.com.


From the DNS result, the driver now MUST treat the host information as if the
following URI was used instead::

    mongodb://mongodb1.mongodb.com:27317,mongodb2.mongodb.com:27107/?connectTimeoutMS=300000

Test Plan
=========

See README.rst in the accompanying test directory.

Additionally, see the "mongodb+srv" tests invalid-uris.yml in the Connection
String Spec tests.

Motivation
==========

Several of our users have asked for this through tickets:

* `<https://jira.mongodb.org/browse/DRIVERS-201>`_
* `<https://jira.mongodb.org/browse/NODE-865>`_
* `<https://jira.mongodb.org/browse/CSHARP-536>`_

Design Rationale
================

The design specifically calls for a pre-processing stage of the processing of
connection URLs to minimize the impact on existing functionality.

Reference Implementation
========================

None yet.

Backwards Compatibility
=======================

There are no backwards compatibility concerns.

Future Work
===========

In the future we could consider using the priority and weight fields of the
SRV records, or to use SRV records to do MongoS discovery.

ChangeLog
=========

2017-09-01: Updated test plan with YAML tests, and moved prose tests for
  URI parsing into invalid-uris.yml in the Connection String Spec tests.
