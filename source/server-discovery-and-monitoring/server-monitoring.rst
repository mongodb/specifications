=================
Server Monitoring
=================

:Spec: 1580
:Title: Server Monitoring
:Status: Accepted
:Type: Standards
:Version: Same as the `Server Discovery And Monitoring`_ spec
:Last Modified: 2020-02-20

.. contents::

--------

Abstract
--------

This spec defines how a driver monitors a MongoDB server. In summary, the
client monitors each server in the topology. The scope of server monitoring is
to provide the topology with updated ServerDescriptions based on isMaster
command responses.

META
----

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
-------------

Terms
'''''

See the terms in the `main SDAM spec`_.

.. _checking: #check
.. _checks: #check

check
`````

The client checks a server by attempting to call ismaster on it,
and recording the outcome.

.. _scans: #scans

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
Suitability is fully specified in the `Server Selection Spec`_.

Monitoring
''''''''''

The client monitors servers by `checking`_ them periodically,
pausing heartbeatFrequencyMS between checks.
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

When checking a server, clients MUST NOT include SCRAM mechanism
negotiation requests with the ``isMaster`` command, as doing so would
make monitoring checks more expensive for the server.

The following subsections specify how monitoring works,
first in multi-threaded or asynchronous clients,
and second in single-threaded clients.
This spec provides detailed requirements for monitoring
because it intends to make all drivers behave consistently.

Multi-threaded or asynchronous monitoring
`````````````````````````````````````````

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

Drivers MUST NOT authenticate on sockets used for monitoring.

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
roundTripTime: no operation that was blocked will
be able to proceed anyway.

Clients update the topology from each handshake
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a client successfully calls ismaster to handshake a new connection for application
operations, it SHOULD use the ismaster reply to update the ServerDescription
and TopologyDescription, the same as with an ismaster reply on a monitoring
socket. If the ismaster call fails, the client SHOULD mark the server Unknown
and update its TopologyDescription, the same as a failed server check on
monitoring socket.

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

Selection failure triggers an immediate scan.
When a client that uses single-threaded monitoring
fails to select a suitable server for any operation,
it `scans`_ the servers, then attempts selection again,
to see if the scan discovered suitable servers. It repeats, waiting
`minHeartbeatFrequencyMS`_ after each scan, until a timeout.

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
This value MUST be 500 ms, and it MUST NOT be configurable (no knobs).

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

(See `heartbeatFrequencyMS in the main SDAM spec`_.)

Error handling
''''''''''''''

Network error during server check
`````````````````````````````````

When a server `check`_ fails due to a network error (including a network timeout),
the client MUST clear its connection pool for the server:
if the monitor's socket is bad it is likely that all are.
(See `JAVA-1252 <https://jira.mongodb.org/browse/JAVA-1252>`_).

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
                    reconnect and call ismaster
                    return new ServerDescription
                except NetworkError as e1:
                    return new ServerDescription with type=Unknown, error=e1

(See `retry ismaster calls once`_ and
`JAVA-1159 <https://jira.mongodb.org/browse/JAVA-1159>`_.)

Implementation notes
''''''''''''''''''''

This section intends to provide generous guidance to driver authors.
It is complementary to the reference implementations.
Words like "should", "may", and so on are used more casually here.

Monitor thread
``````````````

Most platforms can use an event object to control the monitor thread.
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


Rationale
---------

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

Changelog
---------

- 2020-02-20 Extracted server monitoring from SDAM into this new spec.

.. Section for links.

.. _Server Selection Spec: /source/server-selection/server-selection.rst
.. _main SDAM spec: server-discovery-and-monitoring.rst
.. _Server Discovery And Monitoring: server-discovery-and-monitoring.rst
.. _heartbeatFrequencyMS in the main SDAM spec: server-discovery-and-monitoring.rst#heartbeatFrequencyMS
.. _error handling: server-discovery-and-monitoring.rst#error-handling
.. _initial servers: server-discovery-and-monitoring.rst#initial-servers
.. _updateRSWithoutPrimary: server-discovery-and-monitoring.rst#updateRSWithoutPrimary
.. _updateRSFromPrimary: server-discovery-and-monitoring.rst#updateRSFromPrimary
