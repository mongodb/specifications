=================
SRV Polling Tests
=================

.. contents::

Introduction
============

This directory contains prose test descriptions that drivers can use
to prove their conformance to the SRV polling specification.

Without (automated) access to a DNS server configuration, it is nearly
impossible to implement functional tests for a correct implementation of this
specification. However, it might be possible to mock changes to DNS SRV
records such that automated testing is doable. In any case, the following
tests should be executed, either manually, or programmatically.

Configuring the Test Environment
================================

To test, start a sharded cluster with mongos servers on ports 27017, 27018,
27019, and 27020.

For each test, take as starting point the test1 and test3 SRV records from
the `test set-up`_ from the `Initial DNS Seedlist Discovery`_ specification::

    Record                                    TTL    Class   Address
    localhost.test.test.build.10gen.cc.        86400  IN A    127.0.0.1

    Record                                    TTL    Class   Port   Target
    _mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27017  localhost.test.build.10gen.cc.
    _mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27018  localhost.test.build.10gen.cc.
    _mongodb._tcp.test3.test.build.10gen.cc.  86400  IN SRV  27017  localhost.test.build.10gen.cc.

.. _`test set-up`: https://github.com/mongodb/specifications/blob/master/source/initial-dns-seedlist-discovery/tests/README.rst
.. _`Initial DNS Seedlist Discovery`: ../../initial-dns-seedlist-discovery/initial-dns-seedlist-discovery.rst

Prose Tests
===========

Changing DNS records with test1.test.build.10gen.cc
```````````````````````````````````````````````````

The following tests MUST setup a MongoClient using the
``test1.test.build.10gen.cc`` SRV record. Each test MUST mock the described
DNS changes and then verify that the new list of hosts is present.

1. Addition of a new DNS record
-------------------------------

Add the following record::

    _mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27019  localhost.test.build.10gen.cc.

2. Removal of an existing DNS record
------------------------------------

Remove the following record::

    _mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27018  localhost.test.build.10gen.cc.

3. Replacement of a DNS record
------------------------------

Replace the following record::

    _mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27018  localhost.test.build.10gen.cc.

with::

    _mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27019  localhost.test.build.10gen.cc.

4. Replacement of both existing DNS records with *one* new record
-----------------------------------------------------------------

Replace both records with::

    _mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27019  localhost.test.build.10gen.cc.

5. Replacement of both existing DNS records with *two* new records
------------------------------------------------------------------

Replace both records with::

    _mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27019  localhost.test.build.10gen.cc.
    _mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27020  localhost.test.build.10gen.cc.

Error scenarios with test1.test.build.10gen.cc
``````````````````````````````````````````````

The following tests MUST setup a MongoClient using the
``test1.test.build.10gen.cc`` SRV record. Each test MUST mock the described
error situation and assert that the internal list of discovered mongos servers
has not changed.

6. DNS record lookup timeout
----------------------------

Mock a DNS record lookup timeout error.

7. DNS record lookup failure
----------------------------

Mock a DNS record lookup failure (i.e. domain no longer exists because it's no longer registered).

8. Removal of all DNS SRV records
---------------------------------

Mock a DNS record lookup that returns zero SRV records.

Changing DNS records with test3.test.build.10gen.cc
```````````````````````````````````````````````````

The following tests MUST setup a MongoClient using the
``test3.test.build.10gen.cc`` SRV record. Each test MUST mock the described
situation and make the specified assertions.

9. Test that SRV polling is not done for load balalanced clusters
-----------------------------------------------------------------

Connect to ``mongodb+srv://test3.test.build.10gen.cc/?loadBalanced=true``,
mock the addition of the following DNS record::

    _mongodb._tcp.test3.test.build.10gen.cc.  86400  IN SRV  27018  localhost.test.build.10gen.cc.

Wait until ``2*rescanSRVIntervalMS`` and assert that the final topology description
only contains one server: ``localhost.test.build.10gen.cc.`` at port ``27017``.
