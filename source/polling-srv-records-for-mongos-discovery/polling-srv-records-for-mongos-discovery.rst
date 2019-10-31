.. role:: javascript(code)
  :language: javascript

========================================
Polling SRV Records for mongos Discovery
========================================

:Title: Polling SRV Records for mongos Discovery
:Author: Derick Rethans
:Status: Accepted
:Type: Standards
:Last Modified: 2018-11-29
:Version: 1.0
:Spec Lead: David Golden

.. contents::

--------

Abstract
========

Currently the `Initial DNS Seedlist Discovery`_ functionality provides a static
seedlist when a MongoClient is constructed. Periodically polling the DNS SRV
records would allow for the mongos proxy list to be updated without having to
change client configuration.

This specification builds on top of the original Initial DNS Seedlist
Discovery specification, and modifies the `Server Discovery and Monitoring`_
specification's definition of monitoring a set of mongos servers in a Sharded
TopologyType.

.. _`Initial DNS Seedlist Discovery`: ../initial-dns-seedlist-discovery/initial-dns-seedlist-discovery.rst
.. _`Server Discovery and Monitoring`: ../server-discovery-and-monitoring/server-discovery-and-monitoring.rst

META
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

Terms
-----

rescan, rescanning
~~~~~~~~~~~~~~~~~~

A rescan is the periodic scan of all DNS SRV records to discover a new set of
mongos hosts.

rescanSRVIntervalMS
~~~~~~~~~~~~~~~~~~~

An internal value representing how often the DNS SRV records should be queried
for.

Implementation
--------------

If the initial topology was created through a ``mongodb+srv://`` URI, then
drivers MUST implement this specification by periodically rescanning the SRV
DNS records. There MUST NOT be an option to turn this behaviour off.

Drivers MUST NOT implement this specification if they do not adhere fully to
the `Initial DNS Seedlist Discovery`_ specification.

This feature is only available when the Server Discovery has determined that
the TopologyType is Sharded, or Unknown. Drivers MUST NOT rescan SRV DNS
records when the Topology is not Sharded (i.e. Single, ReplicaSetNoPrimary, or
ReplicaSetWithPrimary).

The discovery of a set of mongos servers is explained in the seedlist_
discovery section of the original specification. The behaviour of the periodic
rescan is similar, but not identical to the behaviour of initial seedlist
discovery.  Periodic scan MUST follow these rules:

- The driver will query the DNS server for SRV records on
  ``{hostname}.{domainname}``, prefixed with ``_mongodb._tcp.``:
  ``_mongodb._tcp.{hostname}.{domainname}``.

- A driver MUST verify that the host names returned through SRV records have
  the same parent ``{domainname}``. When this verification fails, a driver:

  - MUST NOT add such a non-compliant host name to the topology
  - MUST NOT raise an error
  - SHOULD log the non-compliance, including the host name
  - MUST NOT initiate a connection to any such host

- If the DNS request returns no verified hosts in SRV records, no SRV records
  at all, or a DNS error happens, the driver:

  - MUST NOT change the topology
  - MUST NOT raise an error
  - SHOULD log this situation, including the reason why the DNS records
    could not be found, if possible
  - MUST temporarily set *rescanSRVIntervalMS* to *heartbeatFrequencyMS* until
    at least one verified SRV record is obtained.

- For all verified host names, as returned through the DNS SRV query, the
  driver:

  - MUST add each valid new host to the topology as Unknown
  - MUST remove all hosts that are part of the topology, but are no longer
    in the returned set of valid hosts
  - MUST NOT remove all hosts, and then re-add the ones that were returned.
    Hosts that have not changed, MUST be left alone and unchanged.

- Priorities and weights in SRV records MUST continue to be ignored, and MUST
  NOT dictate which mongos server is used for new connections.

The rescan needs to happen periodically. As SRV records contain a TTL value,
this value can be used to indicate when a rescan needs to happen. Different
SRV records can have different TTL values. The *rescanSRVIntervalMS* value MUST
be set to the lowest of the individual TTL values associated with the
different SRV records in the most recent rescan, but MUST NOT be lower
than *60 seconds*. If a driver is unable to access the TTL values of SRV
records, it MUST rescan every 60 seconds.

Drivers SHOULD endeavour to rescan and obtain a new list of mongos servers
every *rescanSRVIntervalMS* value. The *rescanSRVIntervalMS* period SHOULD be
calculated from the **end** of the previous rescan (or the **end** of the
initial DNS seedlist discovery scan).

.. _seedlist: https://github.com/mongodb/specifications/blob/master/source/initial-dns-seedlist-discovery/initial-dns-seedlist-discovery.rst#seedlist-discovery

Multi-Threaded Drivers
----------------------

A threaded driver MUST use a separate monitoring thread for scanning the DNS
records so that DNS lookups don't block other operations.

Single-Threaded Drivers
-----------------------

The rescan MUST happen **before** scanning all servers as part of the normal
scanning_ functionality, but only if *rescanSRVIntervalMS* has passed.

.. _scanning: https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#scanning

Motivation for Change
=====================

The original `Initial DNS Seedlist Discovery`_ specification only regulates
the initial list of mongos hosts to be used instead of a single hostname from
a connection URI. Although this makes the initial configuration of a set of
mongos servers a lot easier, it does not provide a method for updating the
list of mongos servers in the topology.

Since the introduction of the ``mongo+srv://`` schema to provide an initial
seedlist, some users have requested additional functionality to be able to
update the configured list of mongos hosts that make up the initially seeded
topology:

- https://jira.mongodb.org/browse/JAVA-2927

Design Rationale
================

From the scope document
-----------------------

Should DNS polling use heartbeatFrequencyMS or DNS cache TTLs?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We have selected to use lowest TTLs among all DNS SRV records, with a caveat
that the rescan frequency is not lower than 60 seconds.

Should DNS polling also have a "fast polling" mode when no servers are available?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We have not opted to have a "fast polling" mode, but we did include a
provision that a rescan needs to happen when DNS records are not available. In
that case, a rescan would happen every *heartbeatFrequencyMS*. The rationale
being that polling DNS really often really fast does not make a lot of sense
due to DNS caching, which often uses the TTL already anyway, but when we have
no TTL records to reference we still need a fallback frequency.

For the design
--------------

No option to turn off periodic rescanning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The design does not allow for an option to turn off the periodic rescanning of
SRV records on the basis that we try to have as few options as possible: the
"no knobs" philosophy.

Backwards Compatibility
=======================

This specification changes the behaviour of server monitoring by introducing a
repeating DNS lookup of the SRV records. Although this is an improvement in
the ``mongodb+srv://`` scheme it can nonetheless break expectations with users
that were familiar with the old behaviour. We do not expect this to negatively
impact users.

Reference Implementation
========================

Reference implementations are made for the following drivers:

- Perl
- C#

Security Implication
====================

This specification has no security implications beyond the ones associated
with the original `Initial DNS Seedlist Discovery`_ specification.

Future work
===========

No future work is expected.

Changelog
=========

No changes yet.
