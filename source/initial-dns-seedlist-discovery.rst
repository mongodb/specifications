.. role:: javascript(code)
  :language: javascript

==============================
Initial DNS Seedlist discovery
==============================

:Spec-ticket: SPEC-878
:Title: Initial DNS Seedlist discovery
:Authors: Derick Rethans
:Status: Draft
:Type: Standards
:Last Modified: 2017-08-29
:Version: 1.0
:Spec Lead: Matt Broadstone
:Advisory Group: \A. Jesse Jiryu Davis
:Approver(s): Bernie Hackett (2017-08-17), David Golden (2017-08-29), Jeff Yemin (2017-08-22), Matt Broadstone (2017-08-24), A. Jesse Jiryu Davis (2017-08-14)


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

Set up test DNS records to test the expansion. Preferably the following three
sets::

    _mongodb._tcp.test1.test.mongodb.com. 86400 IN SRV 10 1 27017 localhost.
    _mongodb._tcp.test1.test.mongodb.com. 86400 IN SRV 10 1 27018 localhost.

    _mongodb._tcp.test2.test.mongodb.com. 86400 IN SRV 10 1 27018 localhost.
    _mongodb._tcp.test2.test.mongodb.com. 86400 IN SRV 10 1 27019 localhost.

    _mongodb._tcp.test3.test.mongodb.com. 86400 IN SRV 10 1 27017 localhost.


The ``localhost:27017``, ``localhost:27018``, and ``localhost:27019`` nodes
are all part of the same replica set.

This replica set, and these SRV records are to be used with the following test
cases.

For each of the test cases:

1. Verify that the connection string has been parsed correctly
2. Verify that after a ping command, connections to the expanded hosts have
   been made, or that the SDAM mechanism in the driver is aware of these hosts
   existing.
3. RECOMMENDED: Verify that the driver is aware that the seed hosts are
   exactly what the DNS query for the SRV record indicates.

Two results with default port
-----------------------------

``mongodb+srv://test1.test.mongodb.com/``

1. Parsed protocol: ``mongodb+srv``
   
   Parsed hostname: ``test1.test.mongodb.com``

2. The following servers MUST now be known to SDAM:
   
   ``localhost:27017`` ``localhost:27018`` ``localhost:27019``

3. The driver should be aware that the following seed hosts exist:
   
   ``localhost:27017`` ``localhost:27018``

Two results with non-standard port
----------------------------------

``mongodb+srv://test2.test.mongodb.com/``

1. Parsed protocol: ``mongodb+srv``

   Parsed hostname: ``test2.test.mongodb.com``

2. The following server/port combinations must now be known to SDAM:

   ``localhost:27017`` ``localhost:27018`` ``localhost:27019``

3. The driver should be aware that the following seed hosts exist:

   ``localhost:27018`` ``localhost:27019``

One result with default port
----------------------------

``mongodb+srv://test3.test.mongodb.com/``

1. Parsed protocol: ``mongodb+srv``

   Parsed hostname: ``test3.test.mongodb.com``

2. The following server/port combinations must now be known to SDAM:

   ``localhost:27017 localhost:27018 localhost:27019``

3. The driver should be aware the following seed host exist:

   ``localhost:27017``

No results
----------

``mongodb+srv://test4.test.mongodb.com/``


1. Parsed protocol: ``mongodb+srv``

   Parsed hostname: ``test4.test.mongodb.com``

2. An error/exception is raised when doing the ping operation, with the
   message that there were no SRV records found for ``test4.test.mongodb.com``.

Multiple Names in URI
---------------------

``mongodb+srv://test5.test.mongodb.com,test6.test.mongodb.com/``

1. Parser must fail while constructing the MongoClient object, because two
   hostnames are specified with the ``mongodb+srv://`` protocol

2. The driver MUST NOT run the operation and MUST NOT be aware of any hosts

URI has a port
--------------

``mongodb+srv://test7.test.mongodb.com:27018/``

1. Parser must fail while constructing the MongoClient object, because a port
   is specified with the ``mongodb+srv://`` protocol

2. The driver MUST NOT run the operation and MUST NOT be aware of any hosts

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

Nothing yet.
