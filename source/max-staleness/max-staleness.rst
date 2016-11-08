=============
Max Staleness
=============

:Spec: 142
:Title: Max Staleness
:Author: \A. Jesse Jiryu Davis
:Lead: Bernie Hackett, Andy Schwerin
:Advisors: Christian Kvalheim, Jeff Yemin, Eric Milkie
:Status: Accepted
:Type: Standards
:Last Modified: October 29, 2016
:Version: 1.2

.. contents::

Abstract
========

Read preference gains a new option, "maxStalenessSeconds".

A client (driver or mongos) MUST estimate the staleness of each secondary,
based on lastWriteDate values provided in server isMaster responses, and select only
those secondaries whose staleness is less than or equal to maxStalenessSeconds.

Most of the implementation of the maxStalenessSeconds option is specified in the
Server Discovery And Monitoring Spec and the Server Selection Spec. This
document supplements those specs by collecting information specifically about
maxStalenessSeconds.

Meta
====

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119`_.

.. _RFC 2119: https://www.ietf.org/rfc/rfc2119.txt

Motivation for Change
=====================

Users have often asked for ways to avoid reading from stale secondaries. An
application with a geographically distributed replica set may want to prefer
nearby members to minimize latency, while at the same time avoiding extremely laggy
secondaries to mitigate the risk of very stale reads.

Goals
-----

* Provide an approximate means of limiting the staleness of secondary reads.
* Provide a client-side knob to adjust the tradeoff between network-local reads
  and data recency.
* Be robust in the face of clock skew between the client and servers,
  and skew between the primary and secondaries.
* Avoid "inadvertent primary read preference": prevent a maxStalenessSeconds setting
  so small it forces all reads to the primary regardless of actual replication lag.
* Specify how mongos routers and shards track the opTimes of Config Servers as
  Replica Sets ("CSRS").

Non-Goals
---------

* Provide a global server-side configuration of max acceptable staleness (see
  `rejected ideas`_).
* Support small values for max staleness.
* Make a consistency guarantee resembling readConcern "afterOpTime".
* Specify how maxStalenessSeconds interacts with readConcern "afterOpTime" in drivers
  (distinct from the goal for routers and shards).
* Compensate for the duration of server checks in staleness estimations.

Specification
=============

API
---

"maxStalenessSeconds" is a new read preference option, with a positive numeric value.
It MUST be configurable similar to other read preference options like "readPreference"
and "tag_sets". Clients MUST also recognize it in the connection string::

  mongodb://host/?readPreference=secondary&maxStalenessSeconds=30

Clients MUST consider "maxStalenessSeconds=-1" in the connection string to mean
"no maximum staleness".

A connection string combining a positive maxStalenessSeconds with read preference
mode "primary" MUST be considered invalid; this includes connection strings with
no explicit read preference mode.

By default there is no maximum staleness.

Besides configuring maxStalenessSeconds in the connection string,
the API for configuring it in code is not specified;
drivers are free to use None, null, -1, or other representations of "no value"
to represent "no max staleness".

Replica Sets
------------

Replica set primaries and secondaries implement the following features to
support maxStalenessSeconds.

idleWritePeriodMS
~~~~~~~~~~~~~~~~~

An idle primary writes a no-op to the oplog every 10 seconds to refresh secondaries'
lastWriteDate values (see SERVER-23892 and `primary must write periodic no-ops`_).
If this period changes in the future, replica set members will
publish its value in their isMaster responses as ``idleWritePeriodMillis``.

.. warning:: Increasing the idle write period may break existing applications
  during a rolling upgrade, since acceptable values for maxStalenessSeconds may
  become unacceptable. See `max staleness must be at least heartbeatFrequencyMS
  + idleWritePeriodMS`_.

lastWrite
~~~~~~~~~

A primary's or secondary's isMaster response contains a "lastWrite" subdocument
with these fields (SERVER-8858):

* lastWriteDate: a BSON UTC datetime,
  the wall-clock time of the **primary** when it most recently recorded a write to the oplog.
* opTime: an opaque value representing the most recent replicated write.
  Needed for sharding, not used for the maxStalenessSeconds read preference option.


Wire Version
------------

The maxWireVersion MUST be incremented to 5
to indicate that the server includes maxStalenessSeconds features
(SERVER-23893).

Client
------

A client (driver or mongos) MUST estimate the staleness of each secondary,
based on lastWriteDate values provided in server isMaster responses, and select for
reads only those secondaries whose estimated staleness is less than or equal to
maxStalenessSeconds.

If any server's maxWireVersion is less than 5 and maxStalenessSeconds is a positive number,
every attempt at server selection throws an error.

When there is a known primary,
a secondary S's staleness is estimated with this formula::

  (S.lastUpdateTime - S.lastWriteDate) - (P.lastUpdateTime - P.lastWriteDate) + heartbeatFrequencyMS

Where "P" and "S" are the primary's and secondary's ServerDescriptions.
All datetimes are in milliseconds.
The staleness estimate could be temporarily negative.

When there is no known primary,
a secondary S's staleness is estimated with this formula::

  SMax.lastWriteDate - S.lastWriteDate + heartbeatFrequencyMS

Where "SMax" is the secondary with the greatest lastWriteDate.

Explanation of Staleness Estimate With Primary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. When the client checks the primary, it gets the delta between the primary's
   lastWriteDate and the client clock. Call this "Client_to_Primary".
2. When the client checks a secondary, it gets the delta between the secondary's
   lastWriteDate and the client clock. Call this "Client_to_Secondary".
3. The difference of these two is an estimate of the delta between
   the primary's and secondary's lastWriteDate.

Thus::

  staleness = Client_to_Secondary - Client_to_Primary
  = (S.lastUpdateTime - S.lastWriteDate) - (P.lastUpdateTime - P.lastWriteDate)

Finally, add heartbeatFrequencyMS::

  (S.lastUpdateTime - S.lastWriteDate) - (P.lastUpdateTime - P.lastWriteDate) + heartbeatFrequencyMS

This adjusts for the pessimistic assumption that S stops replicating right after S.lastUpdateTime,
so it will be heartbeatFrequencyMS *more* stale by the time it is checked again.
This means S must be fresh enough at S.lastUpdateTime to be eligible for reads from
now until the next check, even if it stops replicating.

See the Server Discovery and Monitoring Spec and Server Selection Spec for
details of client implementation.

Routers and shards
------------------

Background: Shard servers and mongos servers in a sharded cluster with CSRS
use readConcern "afterOptime" for consistency guarantees when querying the
shard config.

Besides tracking lastWriteDate, routers and shards additionally track the opTime of
CSRS members if they have maxWireVersion 5 or greater. (See Server Discovery and Monitoring Spec
for details.)

When a router or shard selects a CSRS member to read from with readConcern
like::

  readConcern: { afterOpTime: OPTIME }

... then it follows this selection logic:

1. Make a list of known CSRS data members.
2. Filter out those whose last known opTime is older than OPTIME.
3. If no servers remain, select the primary.
4. Otherwise, select randomly one of the CSRS members whose roundTripTime is
   within localThresholdMS of the member with the fastest roundTripTime.

Step 4 is the standard localThresholdMS logic from the Server Selection Spec.

This algorithm helps routers and shards select a secondary that is likely to
satisfy readConcern "afterOpTime" without blocking.

This feature is only for routers and shards, not drivers. See `Future Work`_.

Reference Implementation
========================

The C Driver (CDRIVER-1363) and Perl Driver (PERL-626).

Estimating Staleness: Example With a Primary and Continuous Writes
==================================================================

Consider a primary P and a secondary S,
and a client with heartbeatFrequencyMS set to 10 seconds.
Say that the primary's clock is 50 seconds skewed ahead of the client's.

The client checks P and S at time 60 (meaning 60 seconds past midnight) by the client's clock.
The primary reports its lastWriteDate is 10.

Then, S reports its lastWriteDate is 0. The client estimates S's staleness as::

  (S.lastUpdateTime - S.lastWriteDate) - (P.lastUpdateTime - P.lastWriteDate) + heartbeatFrequencyMS
  = (60 - 0) - (60 - 10) + 10
  = 20 seconds

(Values converted from milliseconds to seconds for the sake of discussion.)

Note that the secondary appears only 10 seconds stale at this moment,
but the client adds heartbeatFrequencyMS, pessimistically assuming that
the secondary will not replicate at all between now and the next check.
If the current staleness plus heartbeatFrequencyMS is still less than maxStalenessSeconds,
then we can safely read from the secondary from now until the next check.

The client re-checks P and S 10 seconds later, at time 70 by the client's clock.
S responds first with a lastWriteDate of 5: it has fallen 5 seconds further behind.
The client updates S's lastWriteDate and lastUpdateTime.
The client now estimates S's staleness as::

  (S.lastUpdateTime - S.lastWriteDate) - (P.lastUpdateTime - P.lastWriteDate) + heartbeatFrequencyMS
  = (70 - 5) - (60 - 10) + 10
  = 25 seconds

Say that P's response arrives 10 seconds later, at client time 80,
and reports its lastWriteDate is 30.
S's staleness is still 25 seconds::

  (S.lastUpdateTime - S.lastWriteDate) - (P.lastUpdateTime - P.lastWriteDate) + heartbeatFrequencyMS
  = (70 - 5) - (80 - 30) + 10
  = 25 seconds

The same story as a table:

+--------------+---------------+-----------------+------------------+-----------------+------------------+-----------------+-------------+
| Client clock | Primary clock | Event           | S.lastUpdateTime | S.lastWriteDate | P.lastUpdateTime | P.lastWriteDate | S staleness |
+==============+===============+=================+==================+=================+==================+=================+=============+
| 60           | 10            | P and S respond | 60               | 0               | 60               | 10              | 20 seconds  |
+--------------+---------------+-----------------+------------------+-----------------+------------------+-----------------+-------------+
| 70           | 20            | S responds      | 70               | 5               | 60               | 10              | 25 seconds  |
+--------------+---------------+-----------------+------------------+-----------------+------------------+-----------------+-------------+
| 80           | 30            | P responds      | 70               | 5               | 80               | 30              | 25 seconds  |
+--------------+---------------+-----------------+------------------+-----------------+------------------+-----------------+-------------+

.. Generated with table.py from https://zeth.net/code/table.txt like:

    from table import Table

    data = [
        ['Client clock', 'Primary clock', 'Event', 'S.lastUpdateTime', 'S.lastWriteDate',
         'P.lastUpdateTime', 'P.lastWriteDate', 'S staleness'],
        ['60', '10', 'P and S respond', '60', '0', '60', '10', '20 seconds'],
        ['70', '20', 'S responds', '70', '5', '60', '10', '25 seconds'],
        ['80', '30', 'P responds', '70', '5', '80', '30', '25 seconds']
    ]

    print Table(data).create_table()

Estimating Staleness: Example With No Primary
=============================================

Consider a replica set with secondaries S1 and S2, and no primary.
S2 lags 15 seconds *farther* behind S1 and has not yet caught up.
The client has heartbeatFrequencyMS set to 10 seconds.

When the client checks the two secondaries,
S1's lastWriteDate is 20 and S2's lastWriteDate is 5.

Because S1 is the secondary with the maximum lastWriteDate, "SMax",
its staleness estimate equals heartbeatFrequencyMS:

  SMax.lastWriteDate - S.lastWriteDate + heartbeatFrequencyMS
  = 20 - 20 + 10
  = 10

(Since max staleness must be at least heartbeatFrequencyMS + idleWritePeriodMS,
S1 is eligible for reads no matter what.)

S2's staleness estimate is::

  SMax.lastWriteDate - S.lastWriteDate + heartbeatFrequencyMS
  = 20 - 5 + 10
  = 25

Estimating Staleness: Example of Worst-Case Accuracy With Idle Replica Set
==========================================================================

Consider a primary P and a secondary S,
and a client with heartbeatFrequencyMS set to 500 ms.
There is no clock skew. (Previous examples show that skew has no effect.)

The primary has been idle for 10 seconds and writes a no-op to the oplog at time 50
(meaning 50 seconds past midnight), and again at time 60.

Before the secondary can replicate the no-op at time 60, the client checks both servers.
The primary reports its lastWriteDate is 60, the secondary reports 50.

The client estimates S's staleness as::

  (S.lastUpdateTime - S.lastWriteDate) - (P.lastUpdateTime - P.lastWriteDate) + heartbeatFrequencyMS
  = (60 - 50) - (60 - 60) + 0.5
  = 10.5

The same story as a table:

+-------+-----------------------+------------------+-----------------+------------------+-----------------+-------------+
| Clock | Event                 | S.lastUpdateTime | S.lastWriteDate | P.lastUpdateTime | P.lastWriteDate | S staleness |
+=======+=======================+==================+=================+==================+=================+=============+
| 50    | Idle write            | 50               |                 | 50               |                 |             |
+-------+-----------------------+------------------+-----------------+------------------+-----------------+-------------+
| 60    | Idle write begins     | 60               |                 | 50               |                 |             |
+-------+-----------------------+------------------+-----------------+------------------+-----------------+-------------+
| 60    | Client checks P and S | 60               | 60              | 50               | 60              | 10.5        |
+-------+-----------------------+------------------+-----------------+------------------+-----------------+-------------+
| 60    | Idle write completes  | 60               |                 | 60               |                 |             |
+-------+-----------------------+------------------+-----------------+------------------+-----------------+-------------+

.. Generated with table.py from https://zeth.net/code/table.txt like:

    from table import Table

    data = [
        ['Clock', 'Event', 'S.lastUpdateTime', 'S.lastWriteDate',
         'P.lastUpdateTime', 'P.lastWriteDate', 'S staleness'],
        ['50', 'Idle write', '50', '', '50', '', ''],
        ['60', 'Idle write begins', '60', '', '50', '', ''],
        ['60', 'Client checks P and S', '60', '60', '50', '60', '10.5'],
        ['60', 'Idle write completes', '60', '', '60', '', ''],
    ]

    print Table(data).create_table()

In this scenario the actual secondary lag is between 0 and 10 seconds.
But the staleness estimate can be as large as::

    staleness = idleWritePeriodMS + heartbeatFrequencyMS

To ensure the secondary is always eligible for reads in an idle replica set,
we require::

    maxStalenessSeconds * 1000 >= heartbeatFrequencyMS + idleWritePeriodMS

Supplemental
============

Python scripts in this document's source directory:

* `test_max_staleness_spo.py`: Uses `scipy.optimize` to determine worst-case
  accuracy of the staleness estimate in an idle replica set.
* `test_staleness_estimate.py`: Tests whether a client would correctly select
  a secondary from an idle replica set, given a random distribution of values
  for maxStalenessSeconds, heartbeatFrequencyMS, lastWriteDate, and
  lastUpdateTime.

Test Plan
=========

See `max-staleness-tests.rst`,
and the YAML and JSON tests in the tests directory.

Design Rationale
================

Specify max staleness in seconds
--------------------------------

Other driver options that are timespans are in milliseconds, for example
serverSelectionTimeoutMS. The max staleness option is specified in seconds,
however, to make it obvious to users that clients can only enforce large,
imprecise max staleness values.

maxStalenessSeconds is part of Read Preferences
-----------------------------------------------

maxStalenessSeconds MAY be configurable at the client, database, and collection
level, and per operation, the same as other read preference fields are,
because users expressed that their tolerance for stale reads varies per
operation.

Primary must write periodic no-ops
----------------------------------

Consider a scenario in which the primary does *not*:

1. There are no writes for an hour.
2. A client performs a heavy read-only workload with read preference mode
   "nearest" and maxStalenessSeconds of 30 seconds.
3. The primary receives a write.
4. In the brief time before any secondary replicates the write, the client
   re-checks all servers.
5. Since the primary's lastWriteDate is an hour ahead of all secondaries', the
   client only queries the primary.
6. After heartbeatFrequencyMS, the client re-checks all servers and finds
   that the secondaries aren't lagging after all, and resumes querying them.

This apparent "replication lag spike" is just a measurement error, but it causes
exactly the behavior the user wanted to avoid: a small replication lag makes the
client route all queries from the secondaries to the primary.

Therefore an idle primary must execute a no-op every 10 seconds to keep secondaries'
lastWriteDate values close to the primary's clock. The no-op also keeps opTimes close to
the primary's, which helps mongos choose an up-to-date secondary to read from
in a CSRS.

Monitoring software like MongoDB Cloud Manager that charts replication lag
will also benefit when spurious lag spikes are solved.

See `Estimating Staleness: Example of Worst-Case Accuracy With Idle Replica Set`_.
and `SERVER-23892 <https://jira.mongodb.org/browse/SERVER-23892>`_.

Max staleness must be at least heartbeatFrequencyMS + idleWritePeriodMS
-----------------------------------------------------------------------

If maxStalenessSeconds is set to exactly heartbeatFrequencyMS (converted to seconds),
then so long as a secondary lags even a millisecond
it is ineligible.
Despite the user's read preference mode, the client will always read from the primary.

This is an example of "inadvertent primary read preference":
a maxStalenessSeconds setting so small
it forces all reads to the primary regardless of actual replication lag.
We want to prohibit this effect (see `goals`_).

We also want to ensure that a secondary in an idle replica set is always considered
eligible for reads with maxStalenessSeconds. See
`Estimating Staleness: Example of Worst-Case Accuracy With Idle Replica Set`_.

All servers must have wire version 5 to support maxStalenessSeconds
-------------------------------------------------------------------

Clients are required to throw an error if maxStalenessSeconds is set,
and any server in the topology has maxWireVersion less than 5.

Servers began reporting lastWriteDate in wire protocol version 5,
and clients require some or all servers' lastWriteDate in order to
estimate any servers' staleness.
The exact requirements of the formula vary according to TopologyType,
so this spec makes a simple ruling: if any server is running an outdated version,
maxStalenessSeconds cannot be supported.

Rejected ideas
--------------

Add all secondaries' opTimes to primary's isMaster response
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not needed; each secondary's self-report of its opTime is just as good as the
primary's.

Use opTimes from command responses besides isMaster
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An idea was to add opTime to command responses that don't already include it
(e.g., "find"), and use these opTimes to update ServerDescriptions more
frequently than the periodic isMaster calls.

But while a server is not being used (e.g., while it is too stale, or while it
does not match some other part of the Read Preference), only its periodic
isMaster responses can update its opTime. Therefore, heartbeatFrequencyMS
sets a lower bound on maxStalenessSeconds, so there is no benefit in recording
each server's opTime more frequently. On the other hand there would be
costs: effort adding opTime to all command responses, lock contention
getting the opTime on the server and recording it on the client, complexity
in the spec and the client code.

Use current time in staleness estimate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A proposed staleness formula estimated the secondary's worst possible staleness::

  P.lastWriteDate + (now - P.lastUpdateTime) - S.lastWriteDate

In this proposed formula, the place occupied by "S.lastUpdateTime" in the actual formula is replaced with "now",
at the moment in the server selection process when staleness is being estimated.

This formula attempted a worst-case estimate right now:
it assumed the primary kept writing after the client checked it,
and that the secondary replicated nothing since the client last checked the secondary.
The formula was rejected because it would slosh load to and from the secondary
during the interval between checks.

For example:
Say heartbeatFrequencyMS is 10 seconds and maxStalenessSeconds is set to 25 seconds,
and immediately after a secondary is checked its staleness is estimated at 20 seconds.
It is eligible for reads until 5 seconds after the check, then it becomes ineligible,
causing all queries to be directed to the primary until the next check, 5 seconds later.

Server-side Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

We considered a deployment-wide "max staleness" setting that servers
communicate to clients in isMaster, e.g., "120 seconds is the max staleness."
The read preference config is simplified: "maxStalenessSeconds" is gone, instead we
have "staleOk: true" (the default?) and "staleOk: false".

Based on Customer Advisory Board feedback, configuring staleness
per-operation on the client side is more useful. We should merely avoid
closing the door on a future server-side configuration feature.

References
==========

Complaints about stale reads, and proposed solutions:

* `SERVER-3346 <https://jira.mongodb.org/browse/SERVER-3346>`_
* `SERVER-4935 <https://jira.mongodb.org/browse/SERVER-4935>`_
* `SERVER-4936 <https://jira.mongodb.org/browse/SERVER-4936>`_
* `SERVER-8476 <https://jira.mongodb.org/browse/SERVER-8476>`_
* `SERVER-12861 <https://jira.mongodb.org/browse/SERVER-12861>`_

Future Work
===========

Future feature to support readConcern "afterOpTime"
---------------------------------------------------

If a future spec allows applications to use readConcern "afterOptime", clients
should prefer secondaries that have already replicated to that opTime, so reads
do not block. This is an extension of the mongos logic for CSRS to applications.

Future feature to support server-side configuration
---------------------------------------------------

For this spec, we chose to control maxStalenessSeconds in client code.
A future spec could allow database administrators to configure from the server
side how much replication lag makes a secondary too stale to read from.
(See `Server-side Configuration`_ above.) This could be implemented atop the
current feature: if a server communicates is staleness configuration in its
ismaster response like::

    { ismaster: true, maxStalenessSeconds: 30 }

... then a future client can use the value from the server as its default
maxStalenessSeconds when there is no client-side setting.

Changes
=======

2016-09-29: Specify "no max staleness" in the URI with "maxStalenessMS=-1"
instead of "maxStalenessMS=0".
2016-10-24: Rename option from "maxStalenessMS" to "maxStalenessSeconds".
2016-10-25: Change minimum maxStalenessSeconds value from 2 * heartbeatFrequencyMS
to heartbeatFrequencyMS + idleWriteFrequencyMS (with proper conversions of course).
2016-10-29: Rename idleWriteFrequencyMS to idleWritePeriodMS, and allow for
the period to change someday.
