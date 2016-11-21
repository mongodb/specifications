===============================
Server Discovery And Monitoring
===============================

:Spec: 101
:Title: Server Discovery And Monitoring
:Author: A\. Jesse Jiryu Davis
:Advisors: David Golden, Craig Wilson
:Status: Accepted
:Type: Standards
:Version: 2.7
:Last Modified: November 21, 2016

.. contents::

--------

Abstract
--------

This spec defines how a MongoDB client discovers and monitors one or more servers.
It covers monitoring a single server, a set of mongoses, or a replica set.
How does the client determine what type of servers they are?
How does it keep this information up to date?
How does the client find an entire replica set from a seed list,
and how does it respond to a stepdown, election, reconfiguration, or network error?

All drivers must answer these questions the same.
Or, where platforms' limitations require differences among drivers,
there must be as few answers as possible and each must be clearly explained in this spec.
Even in cases where several answers seem equally good, drivers must agree on one way to do it.

MongoDB users and driver authors benefit from having one way to discover and monitor servers.
Users can substantially understand their driver's behavior without inspecting its code or asking its author.
Driver authors can avoid subtle mistakes
when they take advantage of a design that has been well-considered, reviewed, and tested.

The server discovery and monitoring method is specified in four sections.
First, a client is `configured`_.
Second, it begins `monitoring`_ by calling ismaster on all servers.
(Multi-threaded and asynchronous monitoring is described first,
then single-threaded monitoring.)
Third, as ismaster calls are received
the client `parses them`_,
and fourth, it `updates its view of the topology`_.

Finally, this spec describes how `drivers update their topology view
in response to errors`_,
and includes generous implementation notes for driver authors.

This spec does not describe how a client chooses a server for an operation;
that is the domain of the Server Selection Spec.
But there is a section describing
the `interaction between monitoring and server selection`_.

There is no discussion of driver architecture and data structures,
nor is there any specification of a user-facing API.
This spec is only concerned with the algorithm for monitoring the server topology.

Meta
----

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL
NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
`RFC 2119`_.

.. _RFC 2119: https://www.ietf.org/rfc/rfc2119.txt

Specification
-------------

General Requirements
''''''''''''''''''''

**Direct connections:**
A client MUST be able to connect to a single server of any type.
This includes querying hidden replica set members,
and connecting to uninitialized members (see `RSGhost`_) in order to run
"replSetInitiate".
Setting a read preference MUST NOT be necessary to connect to a secondary.
Of course,
the secondary will reject all operations done with the PRIMARY read preference
because the slaveOk bit is not set,
but the initial connection itself succeeds.
Drivers MAY allow direct connections to arbiters
(for example, to run administrative commands).

**Replica sets:**
A client MUST be able to discover an entire replica set from
a seed list containing one or more replica set members.
It MUST be able to continue monitoring the replica set
even when some members go down,
or when reconfigs add and remove members.
A client MUST be able to connect to a replica set
while there is no primary, or the primary is down.

**Mongos:**
A client MUST be able to connect to a set of mongoses
and monitor their availability and `round trip time`_.
This spec defines how mongoses are discovered and monitored,
but does not define which mongos is selected for a given operation.

**Master-slave:**
A client MUST be able to directly connect to a mongod begun with "--slave".
No additional master-slave features are described in this spec.

Terms
'''''

Server
``````

A mongod or mongos process.

Deployment
``````````

One or more servers:
either a standalone, a replica set, or one or more mongoses.

Topology
````````

The state of the deployment:
its type (standalone, replica set, or sharded),
which servers are up, what type of servers they are,
which is primary, and so on.

Client
``````

Driver code responsible for connecting to MongoDB.

Seed list
`````````

Server addresses provided to the client in its initial configuration,
for example from the `connection string`_.

Round trip time
```````````````

Also known as RTT.

The client's measurement of the duration of an ismaster call.
The round trip time is used to support the "localThresholdMS" [1]_
option in the Server Selection Spec.
Even though this measurement is called "ping time" in that spec,
`drivers MUST NOT use the "ping" command`_ to measure this duration.
`This spec does not mandate how round trip time is averaged`_.

ismaster outcome
````````````````

The result of an attempt to call the "ismaster" command on a server.
It consists of three elements:
a boolean indicating the success or failure of the attempt,
a document containing the command response (or null if it failed),
and the round trip time to execute the command (or null if it failed).

.. _checks:
.. _checking:
.. _checked:

check
`````

The client checks a server by attempting to call ismaster on it,
and recording the outcome.

.. _scans:
.. _rescan:

scan
````

The process of checking all servers in the deployment.

suitable
````````

A server is judged "suitable" for an operation if the client can use it
for a particular operation.
For example, a write requires a standalone
(or the master of a master-slave set),
primary, or mongos.
Suitability is fully specified in the `Server Selection Spec
<https://github.com/mongodb/specifications/blob/master/source/server-selection/server-selection.rst>`_.

address
```````

The hostname or IP address, and port number, of a MongoDB server.

Data structures
'''''''''''''''

This spec uses a few data structures
to describe the client's view of the topology.
It must be emphasized that
a driver is free to implement the same behavior
using different data structures.
This spec uses these enums and structs in order to describe driver **behavior**,
not to mandate how a driver represents the topology,
nor to mandate an API.

Enums
`````

TopologyType
~~~~~~~~~~~~

Single, ReplicaSetNoPrimary, ReplicaSetWithPrimary, Sharded, or Unknown.

See `updating the TopologyDescription`_.

ServerType
~~~~~~~~~~

Standalone, Mongos,
PossiblePrimary, RSPrimary, RSSecondary, RSArbiter, RSOther, RSGhost,
or Unknown.

See `parsing an ismaster response`_.

.. note:: Single-threaded clients use the PossiblePrimary type
   to maintain proper `scanning order`_.
   Multi-threaded and asynchronous clients do not need this ServerType;
   it is synonymous with Unknown.

TopologyDescription
```````````````````

The client's representation of everything it knows about the deployment's topology.

Fields:

* type: a `TopologyType`_ enum value. See `initial TopologyType`_.
* setName: the replica set name. Default null.
* maxSetVersion: an integer or null. The largest setVersion ever reported by
  a primary. Default null.
* maxElectionId: an ObjectId or null. The largest electionId ever reported by
  a primary. Default null.
* servers: a set of ServerDescription instances.
  Default contains one server: "localhost:27017", ServerType Unknown.
* stale: a boolean for single-threaded clients, whether the topology must
  be re-scanned.
  (Not related to maxStalenessSeconds, nor to `stale primaries`_.)
* compatible: a boolean.
  False if any server's wire protocol version range
  is incompatible with the client's.
  Default true.
* compatibilityError: a string.
  The error message if "compatible" is false, otherwise null.

ServerDescription
`````````````````

The client's view of a single server,
based on the most recent `ismaster outcome`_.

Again, drivers may store this information however they choose;
this data structure is defined here
merely to describe the monitoring algorithm.

Fields:

* address: the hostname or IP, and the port number,
  that the client connects to.
  Note that this is **not** the server's ismaster.me field,
  in the case that the server reports an address different
  from the address the client uses.
* error: information about the last error related to this server. Default null.
* roundTripTime: the duration of the ismaster call. Default null.
* lastWriteDate: a 64-bit BSON datetime or null.
  The "lastWriteDate" from the server's most recent ismaster response.
* opTime: an ObjectId or null.
  The last opTime reported by the server; an ObjectId or null.
  (Only mongos and shard servers record this field when monitoring
  config servers as replica sets.)
* type: a `ServerType`_ enum value. Default Unknown.
* minWireVersion, maxWireVersion:
  the wire protocol version range supported by the server.
  Both default to 0.
  `Use min and maxWireVersion only to determine compatibility`_.
* me: The hostname or IP, and the port number, that this server was configured with in the replica set. Default null.
* hosts, passives, arbiters: Sets of addresses.
  This server's opinion of the replica set's members, if any.
  These `hostnames are normalized to lower-case`_.
  Default empty.
  The client `monitors all three types of servers`_ in a replica set.
* tags: map from string to string. Default empty.
* setName: string or null. Default null.
* setVersion: integer or null. Default null.
* electionId: an ObjectId, if this is a MongoDB 2.6+ replica set member that
  believes it is primary. See `using setVersion and electionId to detect stale primaries`_.
  Default null.
* primary: an address. This server's opinion of who the primary is.
  Default null.
* lastUpdateTime: when this server was last checked. Default "infinity ago".

"Passives" are priority-zero replica set members that cannot become primary.
The client treats them precisely the same as other members.

.. _configured:

Configuration
'''''''''''''

No breaking changes
```````````````````

This spec does not intend
to require any drivers to make breaking changes regarding
what configuration options are available,
how options are named,
or what combinations of options are allowed.

Initial TopologyDescription
```````````````````````````

The default values for `TopologyDescription`_ fields are described above.
Users may override the defaults as follows:

Initial Servers
~~~~~~~~~~~~~~~

The user MUST be able to set the initial servers list to a `seed list`_
of one or more addresses.

The hostname portion of each address MUST be normalized to lower-case.

Initial TopologyType
~~~~~~~~~~~~~~~~~~~~

The user MUST be able to set the initial TopologyType to Single.

The user MAY be able to initialize it to ReplicaSetNoPrimary.
This provides the user a way to tell the client
it can only connect to replica set members.
Similarly the user MAY be able to initialize it to Sharded,
to connect only to mongoses.

The user MAY be able to initialize it to Unknown, to allow for discovery of any
topology type based only on ismaster responses.

The API for initializing TopologyType is not specified here.
Drivers might already have a convention, e.g. a single seed means Single,
a setName means ReplicaSetNoPrimary,
and a list of seeds means Unknown.
There are variations, however:
In the Java driver a single seed means Single,
but a **list** containing one seed means Unknown,
so it can transition to replica-set monitoring if the seed is discovered
to be a replica set member.
In contrast, PyMongo requires a non-null setName
in order to begin replica-set monitoring,
regardless of the number of seeds.
This spec does not imply existing driver APIs must change
as long as all the required features are somehow supported.

Initial setName
~~~~~~~~~~~~~~~

The user MUST be able to set the client's initial replica set name.
A driver MAY require the set name in order to connect to a replica set,
or it MAY be able to discover the replica set name as it connects.

Allowed configuration combinations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers MUST enforce:

* TopologyType Single cannot be used with multiple seeds.
* If setName is not null, only TopologyType ReplicaSetNoPrimary,
  and possibly Single,
  are allowed.
  (See `verifying setName with TopologyType Single`_.)

heartbeatFrequencyMS
````````````````````

The interval between server `checks`_, counted from the end of the previous
check until the beginning of the next one.

For multi-threaded and asynchronous drivers
it MUST default to 10 seconds and MUST be configurable.
For single-threaded drivers it MUST default to 60 seconds
and MUST be configurable.
It MUST be called heartbeatFrequencyMS
unless this breaks backwards compatibility.

For both multi- and single-threaded drivers,
the driver MUST NOT permit users to configure it less than minHeartbeatFrequencyMS (500ms).

(See `heartbeatFrequencyMS defaults to 10 seconds or 60 seconds`_
and `what's the point of periodic monitoring?`_)

socketCheckIntervalMS
`````````````````````

If a socket has not been used recently,
a single-threaded client MUST check it, by using it for an ismaster call,
before using it for any operation.
The default MUST be 5 seconds, and it MAY be configurable.

Only for single-threaded clients.

(See `what is the purpose of socketCheckIntervalMS?`_).

Client construction
'''''''''''''''''''

The client's constructor MUST NOT do any I/O.
This means that the constructor does not throw an exception
if servers are unavailable:
the topology is not yet known when the constructor returns.
Similarly if a server has an incompatible wire protocol version,
the constructor does not throw.
Instead, all subsequent operations on the client fail
as long as the error persists.

See `clients do no I/O in the constructor`_ for the justification.

Multi-threaded and asynchronous client construction
```````````````````````````````````````````````````

The constructor MAY start the monitors as background tasks
and return immediately.
Or the monitors MAY be started by some method separate from the constructor;
for example they MAY be started by some "initialize" method (by any name),
or on the first use of the client for an operation.

Single-threaded client construction
```````````````````````````````````

Single-threaded clients do no I/O in the constructor.
They MUST `scan`_ the servers on demand,
when the first operation is attempted.

Monitoring
''''''''''

The client monitors servers by `checking`_ them periodically,
pausing `heartbeatFrequencyMS`_ between checks.
Clients check servers sooner in response to certain events.

The socket used to check a server MUST use the same
`connectTimeoutMS <http://docs.mongodb.org/manual/reference/connection-string/>`_
as regular sockets.
Multi-threaded clients SHOULD set monitoring sockets' socketTimeoutMS to the
connectTimeoutMS.
(See `socket timeout for monitoring is connectTimeoutMS`_.
Drivers MAY let users configure the timeouts for monitoring sockets
separately if necessary to preserve backwards compatibility.)

The client begins monitoring a server when:

* ... the client is initialized and begins monitoring each seed.
  See `initial servers`_.
* ... `updateRSWithoutPrimary`_ or `updateRSFromPrimary`_
  discovers new replica set members.

The following subsections specify how monitoring works,
first in multi-threaded or asynchronous clients,
and second in single-threaded clients.
This spec provides detailed requirements for monitoring
because it intends to make all drivers behave consistently.

.. _mt-monitoring:

Multi-threaded or asynchronous monitoring
`````````````````````````````````````````

(See also: `implementation notes for multi-threaded clients`_.)

Servers are monitored in parallel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All servers' monitors run independently, in parallel:
If some monitors block calling ismaster over slow connections,
other monitors MUST proceed unimpeded.

The natural implementation is a thread per server,
but the decision is left to the implementer.
(See `thread per server`_.)

Servers are monitored with dedicated sockets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`A monitor SHOULD NOT use the client's regular connection pool`_
to acquire a socket;
it uses a dedicated socket that does not count toward the pool's
maximum size.

Servers are checked periodically
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each monitor `checks`_ its server and notifies the client of the outcome
so the client can update the TopologyDescription.

After each check, the next check SHOULD be scheduled `heartbeatFrequencyMS`_ later;
a check MUST NOT run while a previous check is still in progress.

.. _request an immediate check:

Requesting an immediate check
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At any time, the client can request that a monitor check its server immediately.
(For example, after a "not master" error. See `error handling`_.)
If the monitor is sleeping when this request arrives,
it MUST wake and check as soon as possible.
If an ismaster call is already in progress,
the request MUST be ignored.
If the previous check ended less than `minHeartbeatFrequencyMS`_ ago,
the monitor MUST sleep until the minimum delay has passed,
then check the server.

Application operations are unblocked when a server is found
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each time a check completes, threads waiting for a `suitable`_ server
are unblocked. Each unblocked thread MUST proceed if the new TopologyDescription
now contains a suitable server.

As an optimization, the client MAY leave threads blocked
if a check completes without detecting any change besides
`round trip time`_: no operation that was blocked will
be able to proceed anyway.

Clients update the topology from each handshake
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a client successfully calls ismaster to handshake a new connection for application
operations, it SHOULD use the ismaster reply to update the ServerDescription
and TopologyDescription, the same as with an ismaster reply on a monitoring
socket. If the ismaster call fails, the client SHOULD mark the server Unknown
and update its TopologyDescription, the same as a failed server check on
monitoring socket.

.. _st-monitoring:

Single-threaded monitoring
``````````````````````````

cooldownMS
~~~~~~~~~~

After a single-threaded client gets a network error trying to `check`_ a
server, the client skips re-checking the server until cooldownMS has passed.

This avoids spending connectTimeoutMS on each unavailable server
during each scan.

This value MUST be 5000 ms, and it MUST NOT be configurable.

Scanning
~~~~~~~~

Single-threaded clients MUST `scan`_ all servers synchronously,
inline with regular application operations.
Before each operation, the client checks if `heartbeatFrequencyMS`_ has
passed since the previous scan ended, or if the topology is marked "stale";
if so it scans all the servers before
selecting a server and performing the operation.

Selection failure triggers an immediate scan, see
`single-threaded server selection`_.

Checking a single server
~~~~~~~~~~~~~~~~~~~~~~~~

Single-threaded clients MUST be able to check an individual server
on demand (for example, after a "not master" error. See `error handling`_).
When checking a single server, its Server Description must be updated
and the topology must be updated based on the new Server Description.

Scanning order
~~~~~~~~~~~~~~

If the topology is a replica set,
the client attempts to contact the primary as soon as possible
to get an authoritative list of members.
Otherwise, the client attempts to check all members it knows of,
in order from the least-recently to the most-recently checked.

When all servers have been checked the scan is complete.
New servers discovered **during** the scan
MUST be checked before the scan is complete.
Sometimes servers are removed during a scan
so they are not checked, depending on the order of events.

The scanning order is expressed in this pseudocode::

    scanStartTime = now()
    # You'll likely need to convert units here.
    beforeCoolDown = scanStartTime - cooldownMS

    while true:
        serversToCheck = all servers with lastUpdateTime before scanStartTime

        remove from serversToCheck any Unknowns with lastUpdateTime > beforeCoolDown

        if no serversToCheck:
            # This scan has completed.
            break

        if a server in serversToCheck is RSPrimary:
            check it
        else if there is a PossiblePrimary:
            check it
        else if any servers are not of type Unknown or RSGhost:
            check the one with the oldest lastUpdateTime
            if several servers have the same lastUpdateTime, choose one at random
        else:
            check the Unknown or RSGhost server with the oldest lastUpdateTime
            if several servers have the same lastUpdateTime, choose one at random

This algorithm might be better understood with an example:

#. The client is configured with one seed and TopologyType Unknown.
   It begins a scan.
#. When it checks the seed, it discovers a secondary.
#. The secondary's ismaster response includes the "primary" field
   with the address of the server that the secondary thinks is primary.
#. The client creates a ServerDescription with that address,
   type PossiblePrimary, and lastUpdateTime "infinity ago".
   (See `updateRSWithoutPrimary`_.)
#. On the next iteration, there is still no RSPrimary,
   so the new PossiblePrimary is the top-priority server to check.
#. The PossiblePrimary is checked and replaced with an RSPrimary.
   The client has now acquired an authoritative host list.
   Any new hosts in the list are added to the TopologyDescription
   with lastUpdateTime "infinity ago".
   (See `updateRSFromPrimary`_.)
#. The client continues scanning until all known hosts have been checked.

Another common case might be scanning a pool of mongoses.
When the client first scans its seed list,
they all have the default lastUpdateTime "infinity ago",
so it scans them in random order.
This randomness provides some load-balancing if many clients start at once.
A client's subsequent scans of the mongoses
are always in the same order,
since their lastUpdateTimes are always in the same order
by the time a scan ends.

minHeartbeatFrequencyMS
```````````````````````

If a client frequently rechecks a server,
it MUST wait at least minHeartbeatFrequencyMS milliseconds
since the previous check ended, to avoid pointless effort.
This value MUST be 500 ms, and it MUST NOT be configurable.
(See `no knobs`_.)

.. _parses them:

Parsing an ismaster response
''''''''''''''''''''''''''''

The client represents its view of each server with a `ServerDescription`_.
Each time the client `checks`_ a server,
it replaces its description of that server with a new one.

ServerDescriptions are created from ismaster outcomes as follows:

type
````

The new ServerDescription's type field is set to a `ServerType`_.
Note that these states do **not** exactly correspond to
`replica set member states
<http://docs.mongodb.org/manual/reference/replica-states/>`_.
For example, some replica set member states like STARTUP and RECOVERING
are identical from the client's perspective, so they are merged into "RSOther".
Additionally, states like Standalone and Mongos
are not replica set member states at all.

+-------------------+---------------------------------------------------------------+
| State             | Symptoms                                                      |
+===================+===============================================================+
| Unknown           | Initial, or after a network error or failed ismaster call,    |
|                   | or "ok: 1" not in ismaster response.                          |
+-------------------+---------------------------------------------------------------+
| Standalone        | No "msg: isdbgrid", no setName, and no "isreplicaset: true".  |
+-------------------+---------------------------------------------------------------+
| Mongos            | "msg: isdbgrid".                                              |
+-------------------+---------------------------------------------------------------+
| PossiblePrimary   | Not yet checked, but another member thinks it is the primary. |
+-------------------+---------------------------------------------------------------+
| RSPrimary         | "ismaster: true", "setName" in response.                      |
+-------------------+---------------------------------------------------------------+
| RSSecondary       | "secondary: true", "setName" in response.                     |
+-------------------+---------------------------------------------------------------+
| RSArbiter         | "arbiterOnly: true", "setName" in response.                   |
+-------------------+---------------------------------------------------------------+
| RSOther           | "setName" in response, "hidden: true" or not primary,         |
|                   | secondary, nor arbiter.                                       |
+-------------------+---------------------------------------------------------------+
| RSGhost           | "isreplicaset: true" in response.                             |
+-------------------+---------------------------------------------------------------+

A server can transition from any state to any other.
For example, an administrator could shut down a secondary
and bring up a mongos in its place.

.. _RSGhost:

RSGhost and RSOther
~~~~~~~~~~~~~~~~~~~

The client MUST monitor replica set members
even when they cannot be queried.
These members are in state RSGhost or RSOther.

**RSGhost** members occur in at least three situations:

* briefly during server startup,
* in an uninitialized replica set,
* or when the server is shunned (removed from the replica set config).

An RSGhost server has no hosts list nor setName.
Therefore the client MUST NOT attempt to use its hosts list
nor check its setName
(see `JAVA-1161 <https://jira.mongodb.org/browse/JAVA-1161>`_
or `CSHARP-671 <https://jira.mongodb.org/browse/CSHARP-671>`_.)
However, the client MUST keep the RSGhost member in its TopologyDescription,
in case the client's only hope for staying connected to the replica set
is that this member will transition to a more useful state.

RSGhosts may report their setNames in the future
(see `SERVER-13458 <https://jira.mongodb.org/browse/SERVER-13458>`_).
For simplicity, this is the rule:
any server is an RSGhost that reports "isreplicaset: true".

Non-ghost replica set members have reported their setNames
since MongoDB 1.6.2.
See `only support replica set members running MongoDB 1.6.2 or later`_.

.. note:: The Java driver does not have a separate state for RSGhost;
   it is an RSOther server with no hosts list.

**RSOther** servers may be hidden, starting up, or recovering.
They cannot be queried, but their hosts lists are useful
for discovering the current replica set configuration.

If a `hidden member <http://docs.mongodb.org/manual/core/replica-set-hidden-member/>`_
is provided as a seed,
the client can use it to find the primary.
Since the hidden member does not appear in the primary's host list,
it will be removed once the primary is checked.

error
`````

If the client experiences any error when checking a server,
it stores error information in the ServerDescription's error field.

roundTripTime
`````````````

Drivers MUST record the server's `round trip time`_ (RTT)
after each successful call to ismaster,
but `this spec does not mandate how round trip time is averaged`_.

If an ismaster call fails, the RTT is not updated.
Furthermore, while a server's type is Unknown its RTT is null,
and if it changes from a known type to Unknown its RTT is set to null.
However, if it changes from one known type to another
(e.g. from RSPrimary to RSSecondary) its RTT is updated normally,
not set to null nor restarted from scratch.

lastWriteDate and opTime
````````````````````````

The isMaster response of a replica set member running MongoDB 3.4 and later
contains a ``lastWrite`` subdocument with fields ``lastWriteDate`` and ``opTime``
(`SERVER-8858`_).
If these fields are available, parse them from the ismaster response,
otherwise set them to null.

Clients MUST NOT attempt to compensate for the network latency between when the server
generated its isMaster response and when the client records ``lastUpdateTime``.

.. _SERVER-8858: https://jira.mongodb.org/browse/SERVER-8858

lastUpdateTime
``````````````

Clients SHOULD set lastUpdateTime with a monotonic clock.

Hostnames are normalized to lower-case
``````````````````````````````````````

The same as with seeds provided in the initial configuration,
all hostnames in the ismaster response's "me", "hosts", "passives", and "arbiters"
entries must be lower-cased.

This prevents unnecessary work rediscovering a server
if a seed "A" is provided and the server
responds that "a" is in the replica set.

`RFC 4343 <http://tools.ietf.org/html/rfc4343>`_:

    Domain Name System (DNS) names are "case insensitive".

Other ServerDescription fields
``````````````````````````````

Other required fields
defined in the `ServerDescription`_ data structure
are parsed from the ismaster response in the obvious way.

Network error when calling ismaster
'''''''''''''''''''''''''''''''''''

When a server `check`_ fails due to a network error,
the client SHOULD clear its connection pool for the server:
if the monitor's socket is bad it is likely that all are.
(See `JAVA-1252 <https://jira.mongodb.org/browse/JAVA-1252>`_.)

Once a server is connected, the client MUST change its type
to Unknown
only after it has retried the server once.
(This rule applies to server checks during monitoring.
It does *not* apply when multi-threaded
`clients update the topology from each handshake`_.)

In this pseudocode, "description" is the prior ServerDescription::

    def checkServer(description):
        try:
            call ismaster
            return new ServerDescription
        except NetworkError as e0:
            clear connection pool for the server

            if description.type is Unknown or PossiblePrimary:
                # Failed on first try to reach this server, give up.
                return new ServerDescription with type=Unknown, error=e0
            else:
                # We've been connected to this server in the past, retry once.
                try:
                    call ismaster
                    return new ServerDescription
                except NetworkError as e1:
                    return new ServerDescription with type=Unknown, error=e1

(See `retry ismaster calls once`_ and
`JAVA-1159 <https://jira.mongodb.org/browse/JAVA-1159>`_.)

.. _updates its view of the topology:

Updating the TopologyDescription
''''''''''''''''''''''''''''''''

Each time the client checks a server,
it processes the outcome (successful or not)
to create a `ServerDescription`_,
and then it processes the ServerDescription to update its `TopologyDescription`_.

The TopologyDescription's `TopologyType`_ influences
how the ServerDescription is processed.
The following subsection
specifies how the client updates its TopologyDescription
when the TopologyType is Single.
The next subsection treats the other types.

TopologyType Single
```````````````````

The TopologyDescription's type was initialized as Single
and remains Single forever.
There is always one ServerDescription in TopologyDescription.servers.

Whenever the client checks a server (successfully or not)
the ServerDescription in TopologyDescription.servers
is replaced with the new ServerDescription.

.. _is compatible:
.. _updates the "compatible" and "compatibilityError" fields:

If the server's wire protocol version range overlaps with the client's,
TopologyDescription.compatible is set to true.
Otherwise it is set to false
and the "compatibilityError" field is filled out like,
"Server at HOST:PORT uses wire protocol versions SERVER_MIN through SERVER_MAX,
but CLIENT only supports CLIENT_MIN through CLIENT_MAX."

Verifying setName with TopologyType Single
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A client MAY allow the user to supply a setName
with an initial TopologyType of Single.
In this case, if the ServerDescription's setName is null or wrong,
the client MUST throw an error on every operation.

Other TopologyTypes
```````````````````

If the TopologyType is **not** Single, there can be one or more seeds.

Whenever a client completes an ismaster call,
it creates a new ServerDescription with the proper `ServerType`_.
It replaces the server's previous description in TopologyDescription.servers
with the new one.

If any server's wire protocol version range does not overlap with the client's,
the client `updates the "compatible" and "compatibilityError" fields`_
as described above for TopologyType Single.
Otherwise "compatible" is set to true.

It is possible for a multi-threaded client to receive an ismaster outcome
from a server after the server has been removed from the TopologyDescription.
For example, a monitor begins checking a server "A",
then a different monitor receives a response from the primary
claiming that "A" has been removed from the replica set,
so the client removes "A" from the TopologyDescription.
Then, the check of server "A" completes.

In all cases, the client MUST ignore ismaster outcomes from servers
that are not in the TopologyDescription.

The following subsections explain in detail what actions the client takes
after replacing the ServerDescription.

TopologyType table
~~~~~~~~~~~~~~~~~~

The new ServerDescription's type is the vertical axis,
and the current TopologyType is the horizontal.
Where a ServerType and a TopologyType intersect,
the table shows what action the client takes.

"no-op" means,
do nothing **after** replacing the server's old description
with the new one.

.. csv-table::
  :header-rows: 1
  :stub-columns: 1

  ,TopologyType Unknown,TopologyType Sharded,TopologyType ReplicaSetNoPrimary,TopologyType ReplicaSetWithPrimary
  ServerType Unknown,no-op,no-op,no-op,`checkIfHasPrimary`_
  ServerType Standalone,`updateUnknownWithStandalone`_,`remove`_,`remove`_,`remove`_ and `checkIfHasPrimary`_
  ServerType Mongos,Set type to TopologyType Sharded,no-op,`remove`_,`remove`_ and `checkIfHasPrimary`_
  ServerType RSPrimary,`updateRSFromPrimary`_,`remove`_, `updateRSFromPrimary`_,`updateRSFromPrimary`_
  ServerType RSSecondary,Set type to ReplicaSetNoPrimary then `updateRSWithoutPrimary`_,`remove`_,`updateRSWithoutPrimary`_,`updateRSWithPrimaryFromMember`_
  ServerType RSArbiter,Set type to ReplicaSetNoPrimary then `updateRSWithoutPrimary`_,`remove`_,`updateRSWithoutPrimary`_,`updateRSWithPrimaryFromMember`_
  ServerType RSOther,Set type to ReplicaSetNoPrimary then `updateRSWithoutPrimary`_,`remove`_,`updateRSWithoutPrimary`_,`updateRSWithPrimaryFromMember`_
  ServerType RSGhost,no-op [#]_,`remove`_,no-op,`checkIfHasPrimary`_

.. [#] `TopologyType remains Unknown when an RSGhost is discovered`_.

TopologyType explanations
~~~~~~~~~~~~~~~~~~~~~~~~~

This subsection complements the `TopologyType table`_
with prose explanations of the TopologyTypes (besides Single).

TopologyType Unknown
  A starting state.

  **Actions**:

  * If the incoming ServerType is Unknown (that is, the ismaster call failed),
    keep the server in TopologyDescription.servers.
    The TopologyType remains Unknown.
  * The `TopologyType remains Unknown when an RSGhost is discovered`_, too.
  * If the type is Standalone, run `updateUnknownWithStandalone`_.
  * If the type is Mongos, set the TopologyType to Sharded.
  * If the type is RSPrimary, record its setName
    and call `updateRSFromPrimary`_.
  * If the type is RSSecondary, RSArbiter or RSOther, record its setName,
    set the TopologyType to ReplicaSetNoPrimary,
    and call `updateRSWithoutPrimary`_.

TopologyType Sharded
  A steady state. Connected to one or more mongoses.

  **Actions**:

  * If the server is Unknown or Mongos, keep it.
  * Remove others.

TopologyType ReplicaSetNoPrimary
  A starting state.
  The topology is definitely a replica set,
  but no primary is known.

  **Actions**:

  * Keep Unknown servers.
  * Keep RSGhost servers: they are members of some replica set,
    perhaps this one, and may recover.
    (See `RSGhost and RSOther`_.)
  * Remove any Standalones or Mongoses.
  * If the type is RSPrimary call `updateRSFromPrimary`_.
  * If the type is RSSecondary, RSArbiter or RSOther,
    run `updateRSWithoutPrimary`_.

TopologyType ReplicaSetWithPrimary
  A steady state. The primary is known.

  **Actions**:

  * If the server type is Unknown, keep it,
    and run `checkIfHasPrimary`_.
  * Keep RSGhost servers: they are members of some replica set,
    perhaps this one, and may recover.
    (See `RSGhost and RSOther`_.)
    Run `checkIfHasPrimary`_.
  * Remove any Standalones or Mongoses
    and run `checkIfHasPrimary`_.
  * If the type is RSPrimary run `updateRSFromPrimary`_.
  * If the type is RSSecondary, RSArbiter or RSOther,
    run `updateRSWithPrimaryFromMember`_.

Actions
~~~~~~~

.. _updateUnknownWithStandalone:

updateUnknownWithStandalone
  This subroutine is executed
  with the ServerDescription from Standalone (including a slave)
  when the TopologyType is Unknown::

    if description.address not in topologyDescription.servers:
        return

    if settings.seeds has one seed:
        topologyDescription.type = Single
    else:
        remove this server from topologyDescription and stop monitoring it

  See `TopologyType remains Unknown when one of the seeds is a Standalone`_.

.. _updateRSWithoutPrimary:

updateRSWithoutPrimary
  This subroutine is executed
  with the ServerDescription from an RSSecondary, RSArbiter, or RSOther
  when the TopologyType is ReplicaSetNoPrimary::

    if description.address not in topologyDescription.servers:
        return

    if topologyDescription.setName is null:
        topologyDescription.setName = description.setName

    else if topologyDescription.setName != description.setName:
        remove this server from topologyDescription and stop monitoring it
        return

    for each address in description's "hosts", "passives", and "arbiters":
        if address is not in topologyDescription.servers:
            add new default ServerDescription of type "Unknown"
            begin monitoring the new server

    if description.primary is not null:
        find the ServerDescription in topologyDescription.servers whose
        address equals description.primary

        if its type is Unknown, change its type to PossiblePrimary

    if description.address != description.me:
        remove this server from topologyDescription and stop monitoring it
        return

  Unlike `updateRSFromPrimary`_,
  this subroutine does **not** remove any servers from the TopologyDescription.

  The special handling of description.primary
  ensures that a single-threaded client
  `scans`_ the possible primary before other members.

  See `replica set monitoring with and without a primary`_.

.. _updateRSWithPrimaryFromMember:

updateRSWithPrimaryFromMember
  This subroutine is executed
  with the ServerDescription from an RSSecondary, RSArbiter, or RSOther
  when the TopologyType is ReplicaSetWithPrimary::

    if description.address not in topologyDescription.servers:
        # While we were checking this server, another thread heard from the
        # primary that this server is not in the replica set.
        return

    # SetName is never null here.
    if topologyDescription.setName != description.setName:
        remove this server from topologyDescription and stop monitoring it

    if description.address != description.me:
        remove this server from topologyDescription and stop monitoring it
        checkIfHasPrimary()
        return

    # Had this member been the primary?
    if there is no primary in topologyDescription.servers:
        topologyDescription.type = ReplicaSetNoPrimary

        if description.primary is not null:
            find the ServerDescription in topologyDescription.servers whose
            address equals description.primary

            if its type is Unknown, change its type to PossiblePrimary

  The special handling of description.primary
  ensures that a single-threaded client
  `scans`_ the possible primary before other members.

.. _updateRSFromPrimary:

updateRSFromPrimary
  This subroutine is executed with a ServerDescription of type RSPrimary::

    if description.address not in topologyDescription.servers:
        return

    if topologyDescription.setName is null:
        topologyDescription.setName = description.setName

    else if topologyDescription.setName != description.setName:
        # We found a primary but it doesn't have the setName
        # provided by the user or previously discovered.
        remove this server from topologyDescription and stop monitoring it
        checkIfHasPrimary()
        return

    if description.setVersion is not null and description.electionId is not null:
        # Election ids are ObjectIds, see
        # "using setVersion and electionId to detect stale primaries"
        # for comparison rules.
        if (topologyDescription.maxSetVersion is not null and
            topologyDescription.maxElectionId is not null and (
                topologyDescription.maxSetVersion > description.setVersion or (
                    topologyDescription.maxSetVersion == description.setVersion and
                    topologyDescription.maxElectionId > description.electionId
                )
            ):

            # Stale primary.
            replace description with a default ServerDescription of type "Unknown"
            checkIfHasPrimary()
            return

        topologyDescription.maxElectionId = description.electionId

    if (description.setVersion is not null and
        (topologyDescription.maxSetVersion is null or
            description.setVersion > topologyDescription.maxSetVersion)):

        topologyDescription.maxSetVersion = description.setVersion

    for each server in topologyDescription.servers:
        if server.address != description.address:
            if server.type is RSPrimary:
                # See note below about invalidating an old primary.
                replace the server with a default ServerDescription of type "Unknown"

    for each address in description's "hosts", "passives", and "arbiters":
        if address is not in topologyDescription.servers:
            add new default ServerDescription of type "Unknown"
            begin monitoring the new server

    for each server in topologyDescription.servers:
        if server.address not in description's "hosts", "passives", or "arbiters":
            remove the server and stop monitoring it

    checkIfHasPrimary()

  A note on invalidating the old primary:
  when a new primary is discovered,
  the client finds the previous primary (there should be none or one)
  and replaces its description
  with a default ServerDescription of type "Unknown."
  A multi-threaded client MUST check that server as soon as possible.
  (The Monitor provides a "request refresh" feature for this purpose,
  see `multi-threaded or asynchronous monitoring`_.)

  The client SHOULD clear its connection pool for the old primary, too:
  the connections are all bad because the old primary has closed its sockets.

  See `replica set monitoring with and without a primary`_.

  If the server is primary with an obsolete setVersion or electionId, it is
  likely a stale primary that is going to step down. Mark it Unknown and let periodic
  monitoring detect when it becomes secondary. See
  `using setVersion and electionId to detect stale primaries`_.

  A note on checking "me": Unlike `updateRSWithPrimaryFromMember`, there is no need to remove the server if the address is not equal to
  "me": since the server address will not be a member of either "hosts", "passives", or "arbiters", the server will already have been
  removed.

.. _checkIfHasPrimary:

checkIfHasPrimary
  Set TopologyType to ReplicaSetWithPrimary if there is an RSPrimary
  in TopologyDescription.servers, otherwise set it to ReplicaSetNoPrimary.

  For example, if the TopologyType is ReplicaSetWithPrimary
  and the client is processing a new ServerDescription of type Unknown,
  that could mean the primary just disconnected,
  so checkIfHasPrimary must run to check if the TopologyType should become
  ReplicaSetNoPrimary.

  Another example is if the client first reaches the primary via its external
  IP, but the response's host list includes only internal IPs.
  In that case the client adds the primary's internal IP to the
  TopologyDescription and begins monitoring it, and removes the external IP.
  Right after removing the external IP from the description,
  the TopologyType MUST be ReplicaSetNoPrimary, since no primary is
  available at this moment.

.. _remove:

remove
  Remove the server from TopologyDescription.servers and stop monitoring it.

  In multi-threaded clients, a monitor may be currently checking this server
  and may not immediately abort.
  Once the check completes, this server's ismaster outcome MUST be ignored,
  and the monitor SHOULD halt.

.. _drivers update their topology view in response to errors:

Error handling
''''''''''''''

This section is about errors when reading or writing to a server.
For errors when checking servers, see `network error when calling ismaster`_.

Network error when reading or writing
`````````````````````````````````````

When an application operation fails because of
any network error besides a socket timeout,
the client MUST replace the server's description
with a default ServerDescription of type Unknown,
and fill the ServerDescription's error field with useful information.

The Unknown ServerDescription is sent through the same process for
`updating the TopologyDescription`_ as if it had been a failed ismaster outcome
from a monitor: for example, if the TopologyType is ReplicaSetWithPrimary
and a write to the RSPrimary server fails because of a network error
(other than timeout), then a new ServerDescription is created for the primary,
with type Unknown, and the client executes the proper subroutine for an
Unknown server when the TopologyType is ReplicaSetWithPrimary:
referring to the table above we see the subroutine is `checkIfHasPrimary`_.
The result is the TopologyType changes to ReplicaSetNoPrimary.
See the test scenario called "Network error writing to primary".

The specific operation that discovered the error
MUST abort and raise an exception if it was a write.
It MAY be retried if it was a read.
(The Server Selection spec describes retry options for reads.)

The client SHOULD clear its connection pool for the server:
if one socket is bad, it is likely that all are.

Clients MUST NOT request an immediate check of the server;
since application sockets are used frequently, a network error likely means
the server has just become unavailable,
so an immediate refresh is likely to get a network error, too.

The server will not remain Unknown forever.
It will be refreshed by the next periodic check or,
if an application operation needs the server sooner than that,
then a re-check will be triggered by the server selection algorithm.

"not master" and "node is recovering"
`````````````````````````````````````

These errors are detected from a getLastError response,
write command response, or query response. Clients MUST consider a server
error to be a "node is recovering" error if the substrings "node is recovering"
or "not master or secondary" are anywhere in the error message.
Otherwise, if the substring "not master" is in the error message it is a
"not master" error::

    def is_recovering(message):
        return ("not master or secondary" in message
            or "node is recovering" in message)

    def is_notmaster(message):
        if is_recovering(message):
            return false
        return ("not master" in message)

    def is_notmaster_or_recovering(message):
        return is_recovering(message) or is_notmaster(message)

    def parse_gle(response):
        if "err" in response:
            if is_notmaster_or_recovering(response["err"]):
                handle_not_master_or_recovering(response["err"])

    # Parse response to any command besides getLastError.
    def parse_command_response(response):
        if not response["ok"]:
            if is_notmaster_or_recovering(response["errmsg"]):
                handle_not_master_or_recovering(response["errmsg"])

    def parse_query_response(response):
        if the "QueryFailure" bit is set in response flags:
            if is_notmaster_or_recovering(response["$err"]):
                handle_not_master_or_recovering(response["$err"])

    def handle_not_master_or_recovering(message):
        replace server's description with
        new ServerDescription(type=Unknown, error=message)

        if multi-threaded:
            request immediate check
        else:
            # Check right now if this is "not master", since it might be a
            # useful secondary. If it's "node is recovering" leave it for the
            # next full scan.
            if is_notmaster(message):
                check failing server

        clear connection pool for server

See the test scenario called
"parsing 'not master' and 'node is recovering' errors"
for example response documents.

When the client sees a "not master" or "node is recovering" error
it MUST replace the server's description
with a default ServerDescription of type Unknown.
It MUST store useful information in the new ServerDescription's error field,
including the error message from the server.

Multi-threaded and asynchronous clients MUST `request an immediate check`_
of the server.
Unlike in the "network error" scenario above,
a "not master" or "node is recovering" error means the server is available
but the client is wrong about its type,
thus an immediate re-check is likely to provide useful information.

For single-threaded clients, in the case of a "not master" error, the client
MUST check the server immediately (see `checking a single server`_).  For a
"node is recovering" error, single-threaded clients MUST NOT check the server,
as an immediate server check is unlikely to find a usable server.

The client SHOULD clear its connection pool for the server.

(See `when does a client see "not master" or "node is recovering"?`_.
and `use error messages to detect "not master" and "node is recovering"`_.)

Monitoring SDAM events
''''''''''''''''''''''

The required driver specification for providing lifecycle hooks into server
discovery and monitoring for applications to consume can be found in the
`SDAM Monitoring Specification <https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/server-discovery-and-monitoring-monitoring.rst>`_.

Implementation notes
''''''''''''''''''''

This section intends to provide generous guidance to driver authors.
It is complementary to the reference implementations.
Words like "should", "may", and so on are used more casually here.

.. _interaction between monitoring and server selection:

Multi-threaded or asynchronous server selection
```````````````````````````````````````````````

While no suitable server is available for an operation,
`the client MUST re-check all servers every minHeartbeatFrequencyMS`_.
(See `requesting an immediate check`_.)

Single-threaded server selection
````````````````````````````````

When a client that uses `single-threaded monitoring`_
fails to select a suitable server for any operation,
it `scans`_ the servers, then attempts selection again,
to see if the scan discovered suitable servers. It repeats, waiting
`minHeartbeatFrequencyMS`_ after each scan, until a timeout.

Documentation
`````````````

Giant seed lists
~~~~~~~~~~~~~~~~

Drivers' manuals should warn against huge seed lists,
since it will slow initialization for single-threaded clients
and generate load for multi-threaded and asynchronous drivers.

.. _implementation notes for multi-threaded clients:

Multi-threaded
``````````````

.. _use min and maxWireVersion only to determine compatibility:

Warning about the maxWireVersion from a monitor's ismaster response
```````````````````````````````````````````````````````````````````

Clients consult some fields from a server's ismaster response
to decide how to communicate with it:

* maxWireVersion
* maxBsonObjectSize
* maxMessageSizeBytes
* maxWriteBatchSize

It is tempting to take these values
from the last ismaster response a *monitor* received
and store them in the ServerDescription, but this is an anti-pattern.
Multi-threaded and asynchronous clients that do so
are prone to several classes of race, for example:

* Setup: A MongoDB 3.0 Standalone with authentication enabled,
  the client must log in with SCRAM-SHA-1.
* The monitor thread discovers the server
  and stores maxWireVersion on the ServerDescription
* An application thread wants a socket, selects the Standalone,
  and is about to check the maxWireVersion on its ServerDescription when...
* The monitor thread gets disconnected from server and marks it Unknown,
  with default maxWireVersion of 0.
* The application thread resumes, creates a socket,
  and attempts to log in using MONGODB-CR,
  since maxWireVersion is *now* reported as 0.
* Authentication fails, the server requires SCRAM-SHA-1.

Better to call ismaster for each new socket, as required by the `Auth Spec
<https://github.com/mongodb/specifications/blob/master/source/auth/auth.rst>`_,
and use the ismaster response associated with that socket
for maxWireVersion, maxBsonObjectSize, etc.:
all the fields required to correctly communicate with the server.

The ismaster responses received by monitors determine if the topology
as a whole `is compatible`_ with the driver,
and which servers are suitable for selection.
The monitors' responses should not be used to determine how to format
wire protocol messages to the servers.

Monitor thread
~~~~~~~~~~~~~~

Most platforms can use an event object
to control the monitor thread.
The event API here is assumed to be like the standard `Python Event
<https://docs.python.org/2/library/threading.html#event-objects>`_.
`heartbeatFrequencyMS`_ is configurable,
`minHeartbeatFrequencyMS`_ is always 500 milliseconds::

    def run():
        while this monitor is not stopped:
            check server and create newServerDescription
            onServerDescriptionChanged(newServerDescription)

            start = gettime()

            # Can be awakened by requestCheck().
            event.wait(heartbeatFrequencyMS)
            event.clear()

            waitTime = gettime() - start
            if waitTime < minHeartbeatFrequencyMS:
                # Cannot be awakened.
                sleep(minHeartbeatFrequencyMS - waitTime)

`Requesting an immediate check`_::

    def requestCheck():
        event.set()

Immutable data
~~~~~~~~~~~~~~

Multi-threaded drivers should treat
ServerDescriptions and
TopologyDescriptions as immutable:
the client replaces them, rather than modifying them,
in response to new information about the topology.
Thus readers of these data structures
can simply acquire a reference to the current one
and read it, without holding a lock that would block a monitor
from making further updates.

Process one ismaster outcome at a time
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Although servers are checked in parallel,
the function that actually creates the new TopologyDescription
should be synchronized so only one thread can run it at a time.

.. _onServerDescriptionChanged:

Replacing the TopologyDescription
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers may use the following pseudocode to guide
their implementation.
The client object has a lock and a condition variable.
It uses the lock to ensure that only one new ServerDescription is processed
at a time.
Once the client has taken the lock it must do no I/O::

    def onServerDescriptionChanged(server):
        # "server" is the new ServerDescription.

        # This thread cannot do any I/O until the lock is released.
        client.lock.acquire()

        if server.address not in client.topologyDescription.servers:
            # The server was once in the topologyDescription, otherwise
            # we wouldn't have been monitoring it, but an intervening
            # state-change removed it. E.g., we got a host list from
            # the primary that didn't include this server.
            client.lock.release()
            return

        newTopologyDescription = client.topologyDescription.copy()

        # Replace server's previous description.
        address = server.address
        newTopologyDescription.servers[address] = server

        take any additional actions,
        depending on the TopologyType and server...

        # Replace TopologyDescription and notify waiters.
        client.topologyDescription = newTopologyDescription
        client.condition.notifyAll()
        client.lock.release()

.. https://github.com/mongodb/mongo-java-driver/blob/5fb47a3bf86c56ed949ce49258a351773f716d07/src/main/com/mongodb/BaseCluster.java#L160

Notifying the condition unblocks threads waiting in the server-selection loop
for a suitable server to be discovered.

.. note::
   The Java driver uses a CountDownLatch instead of a condition variable,
   and it atomically swaps the old and new CountDownLatches
   so it does not need "client.lock".
   It does, however, use a lock to ensure that only one thread runs
   onServerDescriptionChanged at a time.

Rationale
---------

Clients do no I/O in the constructor
''''''''''''''''''''''''''''''''''''

An alternative proposal was to distinguish between "discovery" and "monitoring".
When discovery begins, the client checks all its seeds,
and discovery is complete once all servers have been checked,
or after some maximum time.
Application operations cannot proceed until discovery is complete.

If the discovery phase is distinct,
then single- and multi-threaded drivers
could accomplish discovery in the constructor,
and throw an exception from the constructor
if the deployment is unavailable or misconfigured.
This is consistent with prior behavior for many drivers.
It will surprise some users that the constructor now succeeds,
but all operations fail.

Similarly for misconfigured seed lists:
the client may discover a mix of mongoses and standalones,
or find multiple replica set names.
It may surprise some users that the constructor succeeds
and the client attempts to proceed with a compatible subset of the deployment.

Nevertheless, this spec prohibits I/O in the constructor
for the following reasons:

Common case
```````````

In the common case, the deployment is available and usable.
This spec favors allowing operations to proceed as soon as possible
in the common case,
at the cost of surprising behavior in uncommon cases.

Simplicity
``````````

It is simpler to omit a special discovery phase
and treat all server `checks`_ the same.

Consistency
```````````

Asynchronous clients cannot do I/O in a constructor,
so it is consistent to prohibit I/O in other clients' constructors as well.

Restarts
````````

If clients can be constructed when the deployment is in some states
but not in other states,
it leads to an unfortunate scenario:
When the deployment is passing through a strange state,
long-running clients may keep working,
but any clients restarted during this period fail.

Say an administrator changes one replica set member's setName.
Clients that are already constructed remove the bad member and stay usable,
but if any client is restarted its constructor fails.
Web servers that dynamically adjust their process pools
will show particularly undesirable behavior.

heartbeatFrequencyMS defaults to 10 seconds or 60 seconds
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Many drivers have different values. The time has come to standardize.
Lacking a rigorous methodology for calculating the best frequency,
this spec chooses 10 seconds for multi-threaded or asynchronous drivers
because some already use that value.

Because scanning has a greater impact on
the performance of single-threaded drivers,
they MUST default to a longer frequency (60 seconds).

An alternative is to check servers less and less frequently
the longer they remain unchanged.
This idea is rejected because
it is a goal of this spec to answer questions about monitoring such as,

* "How rapidly can I rotate a replica set to a new set of hosts?"
* "How soon after I add a secondary will query load be rebalanced?"
* "How soon will a client notice a change in round trip time, or tags?"

Having a constant monitoring frequency allows us to answer these questions
simply and definitively.
Losing the ability to answer these questions is not worth
any minor gain in efficiency from a more complex scheduling method.

The client MUST re-check all servers every minHeartbeatFrequencyMS
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

While an application is waiting to do an operation
for which there is no suitable server,
a multi-threaded client MUST re-check all servers very frequently.
The slight cost is worthwhile in many scenarios. For example:

#. A client and a MongoDB server are started simultaneously.
#. The client checks the server before it begins listening,
   so the check fails.
#. The client waits in the server-selection loop for the topology to change.

In this state, the client should check the server very frequently,
to give it ample opportunity to connect to the server before
timing out in server selection.

What is the purpose of socketCheckIntervalMS?
'''''''''''''''''''''''''''''''''''''''''''''

Single-threaded clients need to make a compromise:
if they check servers too frequently it slows down regular operations,
but if they check too rarely they cannot proactively avoid errors.

Errors are more disruptive for single-threaded clients than for multi-threaded.
If one thread in a multi-threaded process encounters an error,
it warns the other threads not to use the disconnected server.
But single-threaded clients are deployed as many independent processes
per application server, and each process must throw an error
until all have discovered that a server is down.

The compromise specified here
balances the cost of frequent checks against the disruption of many errors.
The client preemptively checks individual sockets
that have not been used in the last `socketCheckIntervalMS`_,
which is more frequent by default than `heartbeatFrequencyMS`_.

No knobs
''''''''

This spec does not intend to introduce any new configuration options
unless absolutely necessary.

.. _monitors all three types of servers:

The client MUST monitor arbiters
''''''''''''''''''''''''''''''''

Mongos 2.6 does not monitor arbiters,
but it costs little to do so,
and in the rare case that
all data members are moved to new hosts in a short time,
an arbiter may be the client's last hope
to find the new replica set configuration.

Only support replica set members running MongoDB 1.6.2 or later
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Replica set members began reporting their setNames in that version.
Supporting earlier versions is impractical.

Drivers must not use the "ping" command
'''''''''''''''''''''''''''''''''''''''

Since discovery and monitoring require calling the "ismaster" command anyway,
drivers MUST standardize on the ismaster command instead of the "ping" command
to measure round-trip time to each server.

Additionally, the ismaster command is widely viewed as a special command used
when a client makes its initial connection to the server,
so it is less likely than "ping" to require authentication soon.

This spec does not mandate how round trip time is averaged
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

The Server Selection Spec requires drivers to calculate a round trip time
for each server to support the localThresholdMS option.
That spec calls this measurement the "ping time".
The measurement probably should be a moving average of some sort,
but it is not in the scope of this spec to mandate how drivers
should average the measurements.

TopologyType remains Unknown when an RSGhost is discovered
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

If the TopologyType is Unknown and the client receives an ismaster response
from an`RSGhost`_, the TopologyType could be set to ReplicaSetNoPrimary.
However, an RSGhost does not report its setName,
so the setName would still be unknown.
This adds an additional state to the existing list:
"TopologyType ReplicaSetNoPrimary **and** no setName."
The additional state adds substantial complexity
without any benefit, so this spec says clients MUST NOT change the TopologyType
when an RSGhost is discovered.

TopologyType remains Unknown when one of the seeds is a Standalone
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

If TopologyType is Unknown and there are multiple seeds,
and one of them is discovered to be a standalone,
it MUST be removed.
The TopologyType remains Unknown.

This rule supports the following common scenario:

#. Servers A and B are in a replica set.
#. A seed list with A and B is stored in a configuration file.
#. An administrator removes B from the set and brings it up as standalone
   for maintenance, without changing its port number.
#. The client is initialized with seeds A and B,
   TopologyType Unknown, and no setName.
#. The first ismaster response is from B, the standalone.

What if the client changed TopologyType to Single at this point?
It would be unable to use the replica set; it would have to remove A
from the TopologyDescription once A's ismaster response comes.

The user's intent in this case is clearly to use the replica set,
despite the outdated seed list. So this spec requires clients to remove B
from the TopologyDescription and keep the TopologyType as Unknown.
Then when A's response arrives, the client can set its TopologyType
to ReplicaSet (with or without primary).

On the other hand,
if there is only one seed and the seed is discovered to be a Standalone,
the TopologyType MUST be set to Single.

See the "member brought up as standalone" test scenario.

Thread per server
'''''''''''''''''

Mongos uses a monitor thread per replica set, rather than a thread per server.
A thread per server is impractical if mongos is monitoring a large number of
replica sets.
But a driver only monitors one.

In mongos, threads trying to do reads and writes join the effort to scan
the replica set.
Such threads are more likely to be abundant in mongos than in drivers,
so mongos can rely on them to help with monitoring.

In short: mongos has different scaling concerns than
a multi-threaded or asynchronous driver,
so it allocates threads differently.

Socket timeout for monitoring is connectTimeoutMS
'''''''''''''''''''''''''''''''''''''''''''''''''

When a client waits for a server to respond to a connection,
the client does not know if the server will respond eventually or if it is down.
Users can help the client guess correctly
by supplying a reasonable connectTimeoutMS for their network:
on some networks a server is probably down if it hasn't responded in 10 ms,
on others a server might still be up even if it hasn't responded in 10 seconds.

The socketTimeoutMS, on the other hand, must account for both network latency
and the operation's duration on the server.
Applications should typically set a very long or infinite socketTimeoutMS
so they can wait for long-running MongoDB operations.

Multi-threaded clients use distinct sockets for monitoring and for application
operations.
A socket used for monitoring does two things: it connects and calls ismaster.
Both operations are fast on the server, so only network latency matters.
Thus both operations SHOULD use connectTimeoutMS, since that is the value
users supply to help the client guess if a server is down,
based on users' knowledge of expected latencies on their networks.

A monitor SHOULD NOT use the client's regular connection pool
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

If a multi-threaded driver's connection pool enforces a maximum size
and monitors use sockets from the pool,
there are two bad options:
either monitors compete with the application for sockets,
or monitors have the exceptional ability
to create sockets even when the pool has reached its maximum size.
The former risks starving the monitor.
The latter is more complex than it is worth.
(A lesson learned from PyMongo 2.6's pool, which implemented this option.)

Since this rule is justified for drivers that enforce a maximum pool size,
this spec recommends that all drivers follow the same rule
for the sake of consistency.

Replica set monitoring with and without a primary
'''''''''''''''''''''''''''''''''''''''''''''''''

The client strives to fill the "servers" list
only with servers that the **primary**
said were members of the replica set,
when the client most recently contacted the primary.

The primary's view of the replica set is authoritative for two reasons:

1. The primary is never on the minority side of a network partition.
   During a partition it is the primary's list of
   servers the client should use.
2. Since reconfigs must be executed on the primary,
   the primary is the first to know of them.
   Reconfigs propagate to non-primaries eventually,
   but the client can receive ismaster responses from non-primaries
   that reflect any past state of the replica set.
   See the "Replica set discovery" test scenario.

If at any time the client believes there is no primary,
the TopologyDescription's type is set to ReplicaSetNoPrimary.
While there is no known primary,
the client MUST **add** servers from non-primaries' host lists,
but it MUST NOT remove servers from the TopologyDescription.

Eventually, when a primary is discovered, any hosts not in the primary's host
list are removed.

.. _stale primaries:

Using setVersion and electionId to detect stale primaries
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Replica set members running MongoDB 2.6.10+ or 3.0+ include an integer called
"setVersion" and an ObjectId called
"electionId" in their ismaster response.
Starting with MongoDB 3.2.0, replica sets can use two different replication
protocol versions; electionIds from one protocol version must not be compared
to electionIds from a different protocol.

Because protocol version changes require replica set reconfiguration,
clients use the tuple (setVersion, electionId) to detect stale primaries.

The client remembers the greatest setVersion and electionId reported by a primary,
and distrusts primaries from older setVersions or from the same setVersion
but with lesser electionIds.
It compares setVersions as integer values.
It compares electionIds as 12-byte big-endian integers.
This prevents the client from oscillating
between the old and new primary during a split-brain period,
and helps provide read-your-writes consistency with write concern "majority"
and read preference "primary".

Requirements for read-your-writes consistency
`````````````````````````````````````````````

Using (setVersion, electionId) only provides read-your-writes consistency if:

* The application uses the same MongoClient instance for write-concern
  "majority" writes and read-preference "primary" reads, and
* All members use MongoDB 2.6.10+, 3.0.0+ or 3.2.0+ with replication protocol 0
  and clocks are *less* than 30 seconds skewed, or
* All members run MongoDB 3.2.0 and replication protocol 1
  and clocks are *less* skewed than the election timeout
  (`electionTimeoutMillis`, which defaults to 10 seconds), or
* All members run MongoDB 3.2.1+ and replication protocol 1
  (in which case clocks need not be synchronized).

Scenario
````````

Consider the following situation:

1. Server A is primary.
2. A network partition isolates A from the set, but the client still sees it.
3. Server B is elected primary.
4. The client discovers that B is primary, does a write-concern "majority"
   write operation on B and receives acknowledgment.
5. The client receives an ismaster response from A, claiming A is still primary.
6. If the client trusts that A is primary, the next read-preference "primary"
   read sees stale data from A that may *not* include the write sent to B.

See `SERVER-17975 <https://jira.mongodb.org/browse/SERVER-17975>`_, "Stale
reads with WriteConcern Majority and ReadPreference Primary."

Detecting a stale primary
`````````````````````````

To prevent this scenario, the client uses setVersion and electionId to
determine which primary was elected last. In this case, it would not consider
A primary, nor read from it, after receiving B's ismaster response with the
same setVersion and a greater electionId.

Monotonicity
````````````

The electionId is an ObjectId compared bytewise in big-endian order.
In some server versions, it is monotonic with respect
to a particular servers' system clock, but is not globally monotonic across
a deployment.  However, if inter-server clock skews are small, it can be
treated as a monotonic value.

In MongoDB 2.6.10+ (which has `SERVER-13542 <https://jira.mongodb.org/browse/SERVER-13542>`_ backported),
MongoDB 3.0.0+ or MongoDB 3.2+ (under replication protocol version 0),
the electionId's leading bytes are a server timestamp.
As long as server clocks are skewed *less* than 30 seconds,
electionIds can be reliably compared.
(This is precise enough, because in replication protocol version 0, servers
are designed not to complete more than one election every 30 seconds.
Elections do not take 30 seconds--they are typically much faster than that--but
there is a 30-second cooldown before the next election can complete.)

Beginning in MongoDB 3.2.0, under replication protocol version 1,
the electionId begins with a timestamp, but
the cooldown is shorter.  As long as inter-server clock skew is *less* than
the configured election timeout (`electionTimeoutMillis`, which defaults to
10 seconds), then electionIds can be reliably compared.

Beginning in MongoDB 3.2.1, under replication protocol version 1,
the electionId is guaranteed monotonic
without relying on any clock synchronization.

Using me field to detect seed list members that do not match host names in the replica set configuration
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Removal from the topology of seed list members where the "me" property does not match the address used to connect
prevents clients from being able to select a server, only to fail to re-select that server once the primary has responded.

This scenario illustrates the problems that arise if this is NOT done:

* The client specifies a seed list of A, B, C
* Server A responds as a secondary with hosts D, E, F
* The client executes a query with read preference of secondary, and server A is selected
* Server B responds as a primary with hosts D, E, F.  Servers A, B, C are removed, as they don't appear in the primary's hosts list
* The client iterates the cursor and attempts to execute a get-more against server A.
* Server selection fails because server A is no longer part of the topology.

With checking for "me" in place, it looks like this instead:

* The client specifies a seed list of A, B, C
* Server A responds as a secondary with hosts D, E, F, where "me" is D, and so the client adds D, E, F as type "Unknown" and starts
  monitoring them, but removes A from the topology.
* The client executes a query with read preference of secondary, and goes in to the server selection loop
* Server D responds as a secondary where "me" is D
* Server selection completes by matching D
* The client iterates the cursor and attempts to execute a get-more against server D.
* Server selection completes by matching D.

Ignore setVersion unless the server is primary
''''''''''''''''''''''''''''''''''''''''''''''

It was thought that if all replica set members report a setVersion,
and a secondary's response has a higher setVersion than any seen,
that the secondary's host list could be considered as authoritative
as the primary's. (See `Replica set monitoring with and without a primary`_.)

This scenario illustrates the problem with setVersion:

* We have a replica set with servers A, B, and C.
* Server A is the primary, with setVersion 4.
* An administrator runs replSetReconfig on A,
  which increments its setVersion to 5.
* The client checks Server A and receives the new config.
* Server A crashes before any secondary receives the new config.
* Server B is elected primary. It has the old setVersion 4.
* The client ignores B's version of the config
  because its setVersion is not greater than 5.

The client may never correct its view of the topology.

Even worse:

* An administrator runs replSetReconfig
  on Server B, which increments its setVersion to 5.
* Server A restarts.
  This results in *two* versions of the config,
  both claiming to be version 5.

If the client trusted the setVersion in this scenario,
it would trust whichever config it received first.

mongos 2.6 ignores setVersion and only trusts the primary.
This spec requires all clients to ignore setVersion from non-primaries.

Retry ismaster calls once
'''''''''''''''''''''''''

A monitor's connection to a server is long-lived
and used only for ismaster calls.
So if a server has responded in the past,
a network error on the monitor's connection likely means there was
a network glitch or a server restart since the last check,
rather than that the server is down.
Marking the server Unknown in this case costs unnecessary effort.

However,
if the server still doesn't respond when the monitor attempts to reconnect,
then it is probably down.

Use error messages to detect "not master" and "node is recovering"
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

An alternative idea is to determine all relevant server error codes,
instead of searching for substrings in the error message.
But for "not master" and "node is recovering" errors,
driver authors have found the substrings to be **more** stable
than error codes.

The substring method has worked for drivers for years
so this spec does not propose a new method.

Clients use the hostnames listed in the replica set config, not the seed list
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

Very often users have DNS aliases they use in their `seed list`_ instead of
the hostnames in the replica set config. For example, the name "host_alias"
might refer to a server also known as "host1", and the URI is::

  mongodb://host_alias/?replicaSet=rs

When the client connects to "host_alias", its ismaster response includes the
list of hostnames from the replica set config, which does not include the seed::

   {
      hosts: ["host1:27017", "host2:27017"],
      setName: "rs",
      ... other ismaster response fields ...
   }

This spec requires clients to connect to the hostnames listed in the ismaster
response. Furthermore, if the response is from a primary, the client MUST
remove all hostnames not listed. In this case, the client disconnects from
"host_alias" and tries "host1" and "host2". (See `updateRSFromPrimary`_.)

Thus, replica set members must be reachable from the client by the hostnames
listed in the replica set config.

An alternative proposal is for clients to continue using the hostnames in the
seed list. It could add new hosts from the ismaster response, and where a host
is known by two names, the client can deduplicate them using the "me" field and
prefer the name in the seed list.

This proposal was rejected because it does not support key features of replica
sets: failover and zero-downtime reconfiguration.

In our example, if "host1" and "host2" are not reachable from the client, the
client continues to use "host_alias" only. If that server goes down or is
removed by a replica set reconfig, the client is suddenly unable to reach the
replica set at all: by allowing the client to use the alias, we have hidden the
fact that the replica set's failover feature will not work in a crisis or
during a reconfig.

In conclusion, to support key features of replica sets, we require that the
hostnames used in a replica set config are reachable from the client.

Backwards Compatibility
-----------------------

The Java driver 2.12.1 has a "heartbeatConnectRetryFrequency".
Since this spec recommends the option be named "minHeartbeatFrequencyMS",
the Java driver must deprecate its old option
and rename it minHeartbeatFrequency (for consistency with its other options
which also lack the "MS" suffix).

Reference Implementation
------------------------

* Java driver 3.x
* PyMongo 3.x
* Perl driver 1.0.0 (in progress)

Future Work
-----------

MongoDB is likely to add some of the following features,
which will require updates to this spec:

* Eventually consistent collections (SERVER-2956)
* Mongos discovery (SERVER-1834)
* Require auth for ismaster command (SERVER-12143)
* Put individual databases into maintenance mode,
  instead of the whole server (SERVER-7826)
* Put setVersion in write-command responses (SERVER-13909)

Questions and Answers
---------------------

When does a client see "not master" or "node is recovering"?
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

These errors indicate one of these:

* A write was attempted on an unwritable server
  (arbiter, secondary, slave, ghost, or recovering).
* A read was attempted on an unreadable server
  (arbiter, ghost, or recovering)
  or a read was attempted on a read-only server without the slaveOk bit set.

In any case the error is a symptom that
a ServerDescription's type no longer reflects reality.

A primary closes its connections when it steps down,
so in many cases the next operation causes a network error
rather than "not master".
The driver can see a "not master" error in the following scenario:

#. The client discovers the primary.
#. The primary steps down.
#. Before the client checks the server and discovers the stepdown,
   the application attempts an operation.
#. The client's connection pool is empty,
   either because it has
   never attempted an operation on this server,
   or because all connections are in use by other threads.
#. The client creates a connection to the old primary.
#. The client attempts to write, or to read without the slaveOk bit,
   and receives "not master".

See `"not master" and "node is recovering"`_,
and the test scenario called
"parsing 'not master' and 'node is recovering' errors".

What's the point of periodic monitoring?
''''''''''''''''''''''''''''''''''''''''

Why not just wait until a "not master" error or
"node is recovering" error informs the client that its
TopologyDescription is wrong? Or wait until server selection
fails to find a suitable server, and only scan all servers then?

Periodic monitoring accomplishes three objectives:

* Update each server's type, tags, and `round trip time`_.
  Read preferences and the mongos selection algorithm
  require this information remains up to date.
* Discover new secondaries so that secondary reads are evenly spread.
* Detect incremental changes to the replica set configuration,
  so that the client remains connected to the set
  even while it is migrated to a completely new set of hosts.

If the application uses some servers very infrequently,
monitoring can also proactively detect state changes
(primary stepdown, server becoming unavailable)
that would otherwise cause future errors.

Acknowledgments
---------------

Jeff Yemin's code for the Java driver 2.12,
and his patient explanation thereof,
is the major inspiration for this spec.
Mathias Stearn's beautiful design for replica set monitoring in mongos 2.6
contributed as well.
Bernie Hackett gently oversaw the specification process.

.. _connection string: http://docs.mongodb.org/manual/reference/connection-string/

Changes
-------

2015-12-17: Require clients to compare (setVersion, electionId) tuples.

2015-10-09: Specify electionID comparison method.

2015-06-16: Added cooldownMS.

2016-05-04: Added link to SDAM monitoring.

2016-07-18: Replace mentions of the "Read Preferences Spec" with "Server Selection Spec",
  and "secondaryAcceptableLatencyMS" with "localThresholdMS".

.. [1] "localThresholdMS" was called "secondaryAcceptableLatencyMS" in the Read Preferences Spec,
  before it was superseded by the Server Selection Spec.

2016-07-21: Updated for Max Staleness support.

2016-08-04: Explain better why clients use the hostnames in RS config, not URI.

2016-08-31: Multi-threaded clients SHOULD use ismaster replies to update the topology
  when they handshake application connections.

2016-10-06: in updateRSWithoutPrimary the isMaster response's "primary" field
  should be used to update the topology description, even if address != me.

2016-10-29: Allow for idleWritePeriodMS to change someday.

2016-11-01: "Unknown" is no longer the default TopologyType, the default is now
  explicitly unspecified. Update instructions for setting the initial
  TopologyType when running the spec tests.

2016-11-21: Revert changes that would allow idleWritePeriodMS to change in the
future.
