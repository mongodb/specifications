====================================
Driver Read Semantics: Specification
====================================

:author: Read Semantics Working Group
:date: Feb 14, 2014
:version: 4
:status: Final

.. contents::

The Objective
-------------

How do drivers and mongos choose which member of a replica set to read from
for queries and read-only commands?

How do application developers control that behavior?

Terms
-----

Connection:
    An instance of a "Connection" or "Mongo" class, or whatever class
    represents a MongoDB server in each driver.

socket:
   An open socket to the MongoDB Server.

RS:
   A replica set.

near:
   responding promptly to the ``ping`` command.

far:
   not responding promptly to the ``ping`` command.

Assumptions
-----------

Unless they explicitly override these priorities, we assume our customers
prefer their applications to be, in order:

* Consistent
* Available
* Low-latency

Drivers and mongos know the state of the replica set (how they do RS monitoring is outside this spec):

* They know which members are up or down, what their tags are, and which is primary
* They know ping times to each available member
* They detect reconfigs and the addition or removal of members

Read Preferences
----------------

A "read preference" determines the candidate replica set members to which a query or command can be sent. It consists of:

* "mode": Whether to read from primary or secondary
* "tag sets": How to choose a member based on its tags in the replica set configuration
* "acceptable latency": How to choose a member based on ping time

The mode and tag sets filter out members of the replica set as candidates for a
read operation. These two options stack, or in other words, the mode defines a
subset of nodes to potentially read from and the tags refine that subset even
further. The driver or mongos chooses a member from among the nearest members
that match the mode and tag sets.

Mode
~~~~

Drivers and mongos will support five modes:

"PRIMARY":
````

Read from primary only. All operations produce an error (throw an exception
where applicable) if primary is unavailable. Cannot be combined with tags.

*This is the default.*

"PRIMARY_PREFERRED":
````

Read from primary if available, otherwise a secondary.


"SECONDARY":
````

Read from secondary if available, otherwise error.


"SECONDARY_PREFERRED":
````

Read from a secondary if available, otherwise read from the primary.

"NEAREST":
````

Read from any member.

*Note on NEAREST*: All modes read from among the nearest candidates, but unlike
other modes, NEAREST will include both the primary and all secondaries in the
random selection. The name NEAREST is chosen to emphasize its use, when
latency is most important. For I/O-bound users who want to distribute reads
across all members evenly regardless of ping time, set
secondaryAcceptableLatencyMS very high. See "Ping Times" below.

*Note on other member states*: Members can be in several states besides PRIMARY
or SECONDARY, e.g. STARTUP2 or RECOVERING. Such a member must not be used for
any read no matter what. See
`DRIVERS-73 <https://jira.mongodb.org/browse/DRIVERS-73>`_.

Tag Sets
~~~~

Drivers will support the use of tag sets in combination with a mode. This can
be utilized for data center awareness. Tags only filter secondary read
operations. Primary will be read independent of any tags.

A member matches a tag set if its tags match all the tags in the set. For
example, a member tagged "\{ dc: 'ny', rack: 2, size: 'large' \}" matches the
tag set "\{ dc: 'ny', rack: 2 \}". A member's extra tags don't affect whether
it's a match.

A read preference optionally includes a list of tag sets. A driver or mongos
searches through the list, from first tag set to last, looking for a tag set
that matches one or more members which also match the mode.

If no tag is provided it will match any member which matches the mode (PRIMARY,
SECONDARY, etc.). For compatibility reasons the final tag set can be empty
document \{ \}, which has the same behavior as not providing this parameter.

How Modes Interact With Tag Sets:
~~~~~~~~

"PRIMARY":
````

It is an error to specify any tag sets with PRIMARY, see "errors" below.

"PRIMARY_PREFERRED":
````

If the primary is up, read from it no matter how it's tagged. If the primary is
down, read from a secondary matching the tags provided. If there is none,
error.

"SECONDARY":
````

The driver or mongos searches through list of tag sets from first to last. When
it finds a tag set matching any available secondaries, it picks a random
secondary among the nearest of them. If no available secondaries match the
tags, raise an error.

"SECONDARY_PREFERRED":
````

The driver or mongos searches through the list of tag sets from first to last.
When it finds a tag set matching any available secondaries, it picks a random
secondary among the nearest of them. If there are no tag sets matching any
secondaries, it reads from primary regardless of any tags provided.

"NEAREST":
````

The driver or mongos searches through the list of tag sets from first to last.
When it finds a tag set matching any available members, it picks a random
member among the nearest of them.

Ping Times
~~~~

Once the driver or mongos has found a list of candidate members based on mode
and tag sets, determine the "nearest" member as the one with the quickest
response to a periodic ping command. (The driver already knows ping times to
all members, see "assumptions" above.) Choose a member randomly from those at
most 15ms "farther" than the nearest member. The 15ms cutoff is overridable
with "secondaryAcceptableLatencyMS".

For mode SECONDARY_PREFERRED, the driver or mongos tries to use a random
secondary member that matches the tag sets and secondaryAcceptableLatencyMS.
Failing that, it uses the primary regardless of its ping time.

*Note*: This is the Java driver's algorithm for choosing a secondary now,
expanded to include read preferences.

*Note*: We recommend periodically pinging all members and tracking a moving
average of recent ping times, but that is not required by this spec.

Requests and Auto-retry
-----------------------

Requests
~~~~

A driver's association of a socket with an application thread is called a
"request". A thread can be "in a request," meaning some association between the
thread and the request is guaranteed, or "not in a request". Drivers differ in
their request semantics, e.g. PyMongo-based programs can opt out of requests,
while Java driver-based programs must opt in.

Client connections to mongos are always "in a request" as long as the client
connection lives.

This section details the relationship of modes, requests, and auto-retry. We
describe how the driver or mongos reacts to a member becoming unavailable,
determined either by a socket error when attempting a read, or by background
monitoring.

*Goals:* Simple implementation, and consistent behavior among the drivers and
mongos. It is *not* a goal to guarantee that a series of reads always moves
forward in time, nor to guarantee read-your-writes consistency, outside of
mode PRIMARY.

For all modes, a mongos or driver picks an appropriate replica-set member, from
among those believed to be up, for a thread's first read. If that first read
throws a socket error, the driver or mongos may try up to 2 other members, if
those members match the tags and mode. After a total of 3 failures, or after
running out of appropriate members to try, it throws an error to the
application. Once a read succeeds with some member (and the thread is in a
request, in the case of the drivers), the thread is *pinned* to that member.

The driver / mongos remembers the read preference (mode, tag sets, and
acceptable latency) that the thread / client used for this first read. As long
as the request lasts and all reads use the same read preference, all reads are
routed to the pinned member. A read that uses a new read preference (different
mode, tags, or acceptable latency) unpins the thread and restarts the
member-selection process from scratch. (See `Note On Pinning`_.) All primary
operations within the request must use the same socket, even if interleaved
with operations on secondaries. (For simplicity, drivers may also use a single
socket on each secondary, but this is not required.)

Not only a change in the read preference can unpin a member: if the client
detects that a member has switched from primary to secondary or vice versa,
such that the member no longer matches a thread's read preference, the member
is unpinned. Changes in tags or ping time do not unpin a member. In short: when
the client refreshes its view of the set, if there's a new primary the client
discards the pinning state for all threads. Otherwise, it does not discard the
pinning state.

Auto-retry
~~~~

After the first successful read in a request, a thread is pinned to a
replica-set member (a secondary or the primary). If that member goes down, the
driver or mongos will try other members according to the original selection
logic (taking mode, tags, and ping times into account). When it finds an up
member, the client is now pinned to the new member. Only if the driver or
mongos runs out of members to try, or has tried *three* members and found them
to be down, does it return an error to the client. The client's next read will
begin the selection logic from scratch with no pinned member.

*Note*: If the member was determined to be down because of a socket error, the
Connection should refresh its view of the replica-set state ASAP.

Commands
--------

Generic Command Helper
~~~~

The driver's generic ``command()`` or ``runCommand()`` API accepts a read
preference, but it only obeys the preference for these commands:

* group
* inline mapreduce
* aggregate without $out specified
* collStats, dbStats
* count, distinct
* geoNear, geoSearch, geoWalk
* text
* parallelCollectionScan

For these exceptional commands, the driver or mongos obeys the read preference
the same as for queries. Otherwise, all commands are run on the primary.

If the driver is directly connected to a member (either the primary or a
secondary) it ignores this list and sends all commands to the member to which
it's connected. (It sets the slaveOkay bit to 1 for any read preference besides
PRIMARY.) Thus we still have a means to run commands like "compact" on
secondaries: via direct connection.

*Note*: In the future we'll need to add a field to commands in ``listCommands``
to distinguish new commands that should obey the read preference. The
``slaveOk`` field alone doesn't cover this: e.g., ``reindex`` has ``slaveOk``
true, but we've decided that ``reindex`` with a read preference of SECONDARY
should *not* reindex a random secondary, it should be run on the primary.

*Note*: mongos doesn't distribute the "text" command to secondaries,
see `SERVER-10947 <https://jira.mongodb.org/browse/SERVER-10947>`_.

Command-Specific Helpers
~~~~

The driver will accept no read preference for any command-specific helper the
driver implements, *unless* the command can run on a secondary (e.g.,
``count``).

If the command can run on a secondary, the helper method can accept and obey a
read preference. If no read preference is specified to the helper, then the
collection's, database's, or connection's read preference is used, same as for
queries.

mongos accepts a read preferences for a command same as for queries, and obeys
or ignores the preference the same as drivers.

Driver API Guidelines
---------------------

These are suggestions. As always, driver authors should balance cross-language
standardization with backwards compatibility and the idioms of their language.

Modes
~~~~

Modes (PRIMARY, SECONDARY, ...) are constants declared in whatever way is
idiomatic for the programming language. The constant values may be ints,
strings, or whatever.

Tags
~~~~

Tags can be configured in the driver in whatever way is natural for the
language. The "Communication with mongos" section below may provide inspiration
for formatting tags.

Read Preference Configuration
~~~~

Applications may set mode and/or tag sets on a per-operation basis similar to
how ``addSpecial``, ``hint``, or ``batchSize`` are set. E.g., in Python::

    db.collection.find({}).read_preference(ReadPreference.SECONDARY)
    db.collection.find({}).read_preference(ReadPreference.NEAREST, [ {'dc': 'ny'} ])

Mode and tag sets can be set on a ``Connection``, ``Database``, or
``Collection`` object with a method named like setReadPreference or
set_read_preference, etc.

``secondaryAcceptableLatencyMS``, on the other hand, can only be set on the
``Connection`` object.

Errors
~~~~

If the driver cannot find an available member that matches the ReadPreference,
the driver should immediately raise an exception without attempting any network
operations or refreshing its view of the replica set. If the driver
distinguishes between configuration and connection errors, this is a connection
error. (Justification: the application may not be misconfigured, the expected
member may just be down.)

Reading from a direct connection to a secondary raises an exception if
preference is ``PRIMARY``. (Same as if slaveOk were false.)

Drivers should return useful error messages, as in the following examples, when
there are no members matching the ReadPreference:

* "PRIMARY cannot be combined with tags"
* "No replica set primary available for query with ReadPreference PRIMARY"
* "No replica set secondary available for query with ReadPreference SECONDARY"
* For NEAREST, PRIMARY_PREFERRED, or SECONDARY_PREFERRED, "No replica set members available for query"
* "No replica set member available for query with ReadPreference " + pref + " and tags " + tags

slaveOk
~~~~

The introduction of ``ReadPreference`` deprecates and totally supersedes
``slaveOk`` as a part of the driver API. ``slaveOk`` is deprecated. Until it's
removed, ``slaveOk=True`` means ``ReadPreference=SECONDARY_PREFERRED``. Passing
a value for both ``slaveOk`` and ``ReadPreference`` is an error: "slaveOk is
deprecated, use ReadPreference."

``slaveOk`` remains as a bit in the wire protocol and drivers will set this bit
to ``1`` for all reads except with ``PRIMARY``.

*Note*: Drivers must set the slaveOk bit to 1 with mode PRIMARY_PREFERRED. This
means that a new driver connected to an old mongos will send it a
$readPreference that the mongos will ignore, and reads will be sent to
secondaries. We should tell customers to upgrade mongos along with their
drivers to use read preferences.

Communication with mongos
-------------------------

mongos must support read preferences for queries and commands the same as
drivers. Drivers connected to a mongos send the read preference to mongos
formatted like::

    {
        ... usual fields ...,
        $readPreference: {
            mode: 'secondary',
            tags: [ { 'dc': 'ny' } ]
        }
    }

"Usual fields" includes $query
for a query, ``count:"collection"`` for a count command, etc.

mongos validates the ``$readPreference`` document:

* mode: the mode field must be present exactly once and have a lowercase string
  value, a valid mode in camel case ("primary", "secondary",
  "primaryPreferred", etc.)
* tags: the tags field must be absent, or be present exactly once and have an
  array value containing at least one subdocument. It must contain only
  documents, no other type. The field must be absent or contain only \{ \} if
  mode is "primary".

A misformatted ``$readPreference`` causes an error.

Interaction of read preferences and the slaveOk wire-protocol bit:

* If slaveOk is set, and no read preference is passed, mongos uses SECONDARY_PREFERRED
* If slaveOk is set, and a read preference is passed, mongos obeys the read preference
* If slaveOk is not set, and a read preference is passed, mongos obeys the read preference
* If slaveOk is not set and no read preference is passed, mongos uses PRIMARY

mongos reports itself using ``"msg": "isdbgrid"`` in its response to
``isMaster``. Drivers should *not* send $readPreference unless connected to
mongos.

Note: Drivers must not send $readPreference to mongos for mode PRIMARY (simply
don't set the slaveOk bit), or for mode SECONDARY_PREFERRED without tags
(simply set the slaveOk bit). That way these two read preferences\-\-PRIMARY,
and SECONDARY_PREFERRED without tags\-\-are backwards compatible with all
versions of mongos.

Reference implementation
----

Based on mongos and the basis of PyMongo's implementation:

https://github.com/10gen/read-prefs-reference

Note On Pinning
----

An earlier version of this spec, which was implemented in the versions of the
drivers and mongos released concomitantly with MongoDB 2.2, stated that a
thread / client should remain pinned to an RS member as long as that member
matched the current mode, tags, and acceptable latency. This minimized
time-travel, but had the following surprising consequence:

1. Thread / client reads with mode SECONDARY or SECONDARY_PREFERRED, gets
   pinned to a secondary
2. Thread / client reads with mode PRIMARY_PREFERRED, driver / mongos sees that
   the pinned member (a secondary) matches the mode (which *allows* for a
   secondary) and reads from secondary, even though the primary is available and
   preferable

The old spec also had the swapped problem, reading from the primary with
SECONDARY_PREFERRED, except for mongos which was changed at the last minute
before release with `SERVER-6565 "Do not use primary if secondaries are
available for slaveOk" <https://jira.mongodb.org/browse/SERVER-6565>`_.

This left application developers with two problems:

1. PRIMARY_PREFERRED and SECONDARY_PREFERRED acted surprisingly and
   unpredictably within requests
2. There was no way to specify a common need: read from a secondary if possible
   with SECONDARY_PREFERRED, then from primary if possible with PRIMARY_PREFERRED,
   all within a request. Instead an application developer would have to do the
   second read with PRIMARY, which would unpin the thread but risk unavailability
   if only secondaries were up.
