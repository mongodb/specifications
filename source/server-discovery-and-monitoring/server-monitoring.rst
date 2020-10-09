=================
Server Monitoring
=================

:Spec: 1580
:Title: Server Monitoring
:Status: Accepted
:Type: Standards
:Version: Same as the `Server Discovery And Monitoring`_ spec
:Last Modified: 2020-06-11

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

client
``````

A process that initiates a connection to a MongoDB server. This includes
mongod and mongos processes in a replica set or sharded cluster, as well as
drivers, the shell, tools, etc.

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

significant topology change
```````````````````````````

A change in the server's state that is relevant to the client's view of the
server, e.g. a change in the server's replica set member state, or its replica
set tags. In SDAM terms, a significant topology change on the server means the
client's ServerDescription is out of date. Standalones and mongos do not
currently experience significant topology changes but they may in the future.

regular isMaster command
````````````````````````

A default ``{isMaster: 1}`` command where the server responds immediately.


streamable isMaster command
```````````````````````````

The isMaster command feature which allows the server to stream multiple
replies back to the client.

RTT
```

Round trip time. The client's measurement of the duration of one isMaster call.
The RTT is used to support `localThresholdMS`_ from the Server Selection spec.


Monitoring
''''''''''

The client monitors servers using the isMaster command. In MongoDB 4.4+, a
monitor uses the `Streaming Protocol`_ to continuously stream isMaster
responses from the server. In MongoDB <= 4.2, a monitor uses the
`Polling Protocol`_ pausing heartbeatFrequencyMS between `checks`_.
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

Drivers MUST NOT authenticate on sockets used for monitoring nor include
SCRAM mechanism negotiation (i.e. ``saslSupportedMechs``), as doing so would
make monitoring checks more expensive for the server.

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

When a monitor check creates a new connection, the `connection handshake`_
response MUST be used to satisfy the check and update the topology.

When a client successfully calls ismaster to handshake a new connection for application
operations, it SHOULD use the ismaster reply to update the ServerDescription
and TopologyDescription, the same as with an ismaster reply on a monitoring
socket. If the ismaster call fails, the client SHOULD mark the server Unknown
and update its TopologyDescription, the same as a failed server check on
monitoring socket.

Clients use the streaming protocol when supported
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a monitor discovers that the server supports the streamable isMaster
command, it MUST use the `streaming protocol`_.

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

Awaitable isMaster Server Specification
'''''''''''''''''''''''''''''''''''''''

As of MongoDB 4.4 the isMaster command can wait to reply until there is a
topology change or a maximum time has elapsed. Clients opt in to this
"awaitable isMaster" feature by passing new isMaster parameters
"topologyVersion" and "maxAwaitTimeMS". Exhaust support has also been added,
which clients can enable in the usual manner by setting the
`OP_MSG exhaustAllowed flag`_.

Clients use the awaitable isMaster feature as the basis of the streaming
heartbeat protocol to learn much sooner about stepdowns, elections, reconfigs,
and other events.

topologyVersion
```````````````

A server that supports awaitable isMaster includes a "topologyVersion"
field in all isMaster replies and State Change Error replies.
The topologyVersion is a subdocument with two fields, "processId" and
"counter":

.. code:: typescript

    {
        topologyVersion: {processId: <ObjectId>, counter: <int64>},
        ( ... other fields ...)
    }

processId
~~~~~~~~~

An ObjectId maintained in memory by the server. It is reinitialized by the
server using the standard ObjectId logic each time this server process starts.

counter
~~~~~~~

An int64 State change counter, maintained in memory by the server. It begins
at 0 when the server starts, and it is incremented whenever there is a
significant topology change.

maxAwaitTimeMS
``````````````

To enable awaitable isMaster, the client includes a new int64 field
"maxAwaitTimeMS" in the isMaster request. This field determines the maximum
duration in milliseconds a server will wait for a significant topology change
before replying.

Feature Discovery
`````````````````

To discover if the connected server supports awaitable isMaster, a client
checks the most recent isMaster command reply. If the reply includes
"topologyVersion" then the server supports awaitable isMaster.

Awaitable isMaster Protocol
```````````````````````````

To initiate an awaitable isMaster command, the client includes both
maxAwaitTimeMS and topologyVersion in the request, for example:

.. code:: typescript

    {
        isMaster: 1,
        maxAwaitTimeMS: 10000,
        topologyVersion: {processId: <ObjectId>, counter: <int64>},
        ( ... other fields ...)
    }

Clients MAY additionally set the `OP_MSG exhaustAllowed flag`_ to enable
streaming isMaster. With streaming isMaster, the server MAY send multiple
isMaster responds without waiting for further requests.

A server that implements the new protocol follows these rules:

- Always include the server's topologyVersion in isMaster and State Change
  Error replies.
- If the request includes topologyVersion without maxAwaitTimeMS or vice versa,
  return an error.
- If the request omits topologyVersion and maxAwaitTimeMS, reply immediately.
- If the request includes topologyVersion and maxAwaitTimeMS, then reply
  immediately if the server's topologyVersion.processId does not match the
  request's, otherwise reply when the server's topologyVersion.counter is
  greater than the request's, or maxAwaitTimeMS elapses, whichever comes first.
- Following the `OP_MSG spec`_, if the request omits the exhaustAllowed flag,
  the server MUST NOT set the moreToCome flag on the reply. If the request's
  exhaustAllowed flag is set, the server MAY set the moreToCome flag on the
  reply. If the server sets moreToCome, it MUST continue streaming replies
  without awaiting further requests. Between replies it MUST wait until the
  server's topologyVersion.counter is incremented or maxAwaitTimeMS elapses,
  whichever comes first. If the reply includes ``ok: 0`` the server MUST NOT
  set the moreToCome flag.
- On a topology change that changes the horizon parameters, the server will
  close all application connections.


Example awaitable isMaster conversation:

+---------------------------------------+--------------------------------+
| Client                                | Server                         |
+=======================================+================================+
| isMaster handshake ->                 |                                |
+---------------------------------------+--------------------------------+
|                                       | <- reply with topologyVersion  |
+---------------------------------------+--------------------------------+
| isMaster as OP_MSG with               |                                |
| maxAwaitTimeMS and topologyVersion -> |                                |
+---------------------------------------+--------------------------------+
|                                       | wait for change or timeout     |
+---------------------------------------+--------------------------------+
|                                       | <- OP_MSG with topologyVersion |
+---------------------------------------+--------------------------------+
| ...                                   |                                |
+---------------------------------------+--------------------------------+

Example streaming isMaster conversation (awaitable isMaster with exhaust):

+---------------------------------------+--------------------------------+
| Client                                | Server                         |
+=======================================+================================+
| isMaster handshake ->                 |                                |
+---------------------------------------+--------------------------------+
|                                       | <- reply with topologyVersion  |
+---------------------------------------+--------------------------------+
| isMaster as OP_MSG with               |                                |
| exhaustAllowed, maxAwaitTimeMS,       |                                |
| and topologyVersion ->                |                                |
+---------------------------------------+--------------------------------+
|                                       | wait for change or timeout     |
+---------------------------------------+--------------------------------+
|                                       | <- OP_MSG with moreToCome      |
|                                       | and topologyVersion            |
+---------------------------------------+--------------------------------+
|                                       | wait for change or timeout     |
+---------------------------------------+--------------------------------+
|                                       | <- OP_MSG with moreToCome      |
|                                       | and topologyVersion            |
+---------------------------------------+--------------------------------+
|                                       | ...                            |
+---------------------------------------+--------------------------------+
|                                       | <- OP_MSG without moreToCome   |
+---------------------------------------+--------------------------------+
| ...                                   |                                |
+---------------------------------------+--------------------------------+


Streaming Protocol
''''''''''''''''''

The streaming protocol is used to monitor MongoDB 4.4+ servers and optimally
reduces the time it takes for a client to discover server state changes.
Multi-threaded or asynchronous drivers MUST use the streaming protocol when
connected to a server that supports the awaitable isMaster command. This
protocol requires an extra thread and an extra socket for
each monitor to perform RTT calculations.

Streaming isMaster
``````````````````

The streaming isMaster protocol uses awaitable isMaster with the OP_MSG
exhaustAllowed flag to continuously stream isMaster responses from the server.
Drivers MUST set the OP_MSG exhaustAllowed flag with the awaitable isMaster
command and MUST process each isMaster response. (I.e., they MUST process
responses strictly in the order they were received.)

A client follows these rules when processing the isMaster exhaust response:

- If the response indicates a command error, or a network error or timeout
  occurs, the client MUST close the connection and restart the monitoring
  protocol on a new connection. (See
  `Network or command error during server check`_.)
- If the response is successful (includes "ok:1") and includes the OP_MSG
  moreToCome flag, then the client begins reading the next response.
- If the response is successful (includes "ok:1") and does not include the
  OP_MSG moreToCome flag, then the client initiates a new awaitable isMaster
  with the topologyVersion field from the previous response.

Socket timeout
``````````````

Clients MUST use connectTimeoutMS as the timeout for the connection handshake.
When connectTimeoutMS=0, the timeout is unlimited and MUST remain unlimited
for awaitable isMaster replies. Otherwise, connectTimeoutMS is non-zero and
clients MUST use connectTimeoutMS + heartbeatFrequencyMS as the timeout for
awaitable isMaster replies.

Measuring RTT
`````````````

When using the streaming protocol, clients MUST issue an isMaster command to
each server to measure RTT every heartbeatFrequencyMS. The RTT command
MUST be run on a dedicated connection to each server. For consistency,
clients MAY use dedicated connections to measure RTT for all servers, even
those that do not support awaitable isMaster. (See
`Monitors MUST use a dedicated connection for RTT commands`_.)

Clients MUST update the RTT from the isMaster duration of the initial
connection handshake. Clients MUST NOT update RTT based on streaming isMaster
responses.

Clients MUST ignore the response to the isMaster command when measuring RTT.
Errors encountered when running a isMaster command MUST NOT update the topology.
(See `Why don't clients mark a server unknown when an RTT command fails?`_)

When constructing a ServerDescription from a streaming isMaster response,
clients MUST use the current roundTripTime from the RTT task.

See the pseudocode in the `RTT thread`_ section for an example implementation.

SDAM Monitoring
```````````````

Clients MUST publish a ServerHeartbeatStartedEvent before attempting to
read the next isMaster exhaust response. (See
`Why must streaming isMaster clients publish ServerHeartbeatStartedEvents?`_)

Clients MUST NOT publish any events when running an RTT command. (See
`Why don't streaming isMaster clients publish events for RTT commands?`_)

Heartbeat frequency
```````````````````

In the polling protocol, a client sleeps between each isMaster check (for at
least minHeartbeatFrequencyMS and up to heartbeatFrequencyMS). In the
streaming protocol, after processing an "ok:1" isMaster response, the client
MUST NOT sleep and MUST begin the next check immediately.

Clients MUST set `maxAwaitTimeMS`_ to heartbeatFrequencyMS.

isMaster Cancellation
`````````````````````

When a client is closed, clients MUST cancel all isMaster checks; a monitor
blocked waiting for the next streaming isMaster response MUST be interrupted
such that threads may exit promptly without waiting maxAwaitTimeMS.

When a client marks a server Unknown from `Network error when reading or
writing`_, clients MUST cancel the isMaster check on that server and close the
current monitoring connection. (See
`Drivers cancel in-progress monitor checks`_.)

Polling Protocol
''''''''''''''''

The polling protocol is used to monitor MongoDB <= 4.4 servers. The client
`checks`_ a server with an isMaster command and then sleeps for
heartbeatFrequencyMS before running another check.

Error handling
''''''''''''''

Network or command error during server check
````````````````````````````````````````````

When a server `check`_ fails due to a network error (including a network
timeout) or a command error (``ok: 0``), the client MUST follow these steps:

#. Close the current monitoring connection.
#. Mark the server Unknown.
#. Clear the connection pool for the server. (See
   `Clear the connection pool on both network and command errors`_.)
#. If this was a network error and the server was in a known state before the
   error, the client MUST NOT sleep and MUST begin the next check immediately.
   (See `retry ismaster calls once`_ and
   `JAVA-1159 <https://jira.mongodb.org/browse/JAVA-1159>`_.)
#. Otherwise, wait for heartbeatFrequencyMS (or minHeartbeatFrequencyMS if a
   check is requested) before restarting the monitoring protocol on a new
   connection.

   - Note that even in the streaming protocol, a monitor in this state will
     wait for an application operation to `request an immediate check`_ or
     for the heartbeatFrequencyMS timeout to expire before begining the next
     check.

See the pseudocode in the `Monitor thread` section.

Note that this rule applies only to server checks during monitoring.
It does *not* apply when multi-threaded
`clients update the topology from each handshake`_.

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
`minHeartbeatFrequencyMS`_ is always 500 milliseconds:

.. code-block:: python

  class Monitor(Thread):
    def __init__():
        # Monitor options:
        serverAddress = serverAddress
        connectTimeoutMS = connectTimeoutMS
        heartbeatFrequencyMS = heartbeatFrequencyMS
        minHeartbeatFrequencyMS = 500

        # Internal Monitor state:
        connection = Null
        description = default ServerDescription
        lock = Mutex()
        rttMonitor = RttMonitor(serverAddress)

    def run():
        # Start the RttMonitor.
        rttMonitor.run()
        while this monitor is not stopped:
            previousDescription = description
            try:
                description = checkServer(previousDescription)
            except CheckCancelledError:
                if this monitor is stopped:
                    # The client was closed.
                    return
                # The client marked this server Unknown and cancelled this
                # check during "Network error when reading or writing".
                # Wait before running the next check.
                wait()
                continue
            topology.onServerDescriptionChanged(description)
            if description.error != Null:
                # Clear the connection pool only after the server description is set to Unknown.
                clear connection pool for server

            # Immediately proceed to the next check if the previous response
            # was successful and included the topologyVersion field, or the
            # previous response included the moreToCome flag, or the server
            # has just transitioned to Unknown from a network error.
            serverSupportsStreaming = description.type != Unknown and description.topologyVersion != Null
            connectionIsStreaming = connection != Null and connection.moreToCome
            transitionedWithNetworkError = isNetworkError(description.error) and previousDescription.type != Unknown
            if serverSupportsStreaming or connectionIsStreaming or transitionedWithNetworkError:
                continue

            wait()

    def setUpConnection():
        # Take the mutex to avoid a data race becauase this code writes to the connection field and a concurrent
        # cancelCheck call could be reading from it.
        with lock:
            connection = new Connection(serverAddress)
            set connection timeout to connectTimeoutMS

        # Do any potentially blocking operations after releasing the mutex.
        create the socket and perform connection handshake

    def checkServer(previousDescription):
        try:
            # The connection is null if this is the first check. It's closed if there was an error during the previous
            # check or the previous check was cancelled.
            if not connection or connection.isClosed():
                setUpConnection()
                rttMonitor.addSample(connection.handshakeDuration)
                response = connection.handshakeResponse
            elif connection.moreToCome:
                response = read next isMaster exhaust response
            elif previousDescription.topologyVersion:
                # Initiate streaming isMaster
                if connectTimeoutMS != 0:
                    set connection timeout to connectTimeoutMS+heartbeatFrequencyMS
                response = call {isMaster: 1, topologyVersion: previousDescription.topologyVersion, maxAwaitTimeMS: heartbeatFrequencyMS}
            else:
                # The server does not support topologyVersion.
                response = call {isMaster: 1}

            return ServerDescription(response, rtt=rttMonitor.average())
        except Exception as exc:
            close connection
            rttMonitor.reset()
            return ServerDescription(type=Unknown, error=exc)

    def wait():
        start = gettime()

        # Can be awakened by requestCheck().
        event.wait(heartbeatFrequencyMS)
        event.clear()

        waitTime = gettime() - start
        if waitTime < minHeartbeatFrequencyMS:
            # Cannot be awakened.
            sleep(minHeartbeatFrequencyMS - waitTime)


`Requesting an immediate check`_:

.. code-block:: python

    def requestCheck():
        event.set()


`isMaster Cancellation`_:

.. code-block:: python

    def cancelCheck():
        # Take the mutex to avoid reading the connection value while setUpConnection is writing to it.
        # Copy the connection value in the lock but do the actual cancellation outside.
        with lock:
            tempConnection = connection

        if tempConnection:
          interrupt connection read
          close tempConnection

RTT thread
``````````

The requirements in the `Measuring RTT`_ section can be satisfied with an
addtional thread that periodically runs the isMaster command on a dedicated
connection, for example:

.. code-block:: python

  class RttMonitor(Thread):
    def __init__():
        # Options:
        serverAddress = serverAddress
        connectTimeoutMS = connectTimeoutMS
        heartbeatFrequencyMS = heartbeatFrequencyMS
        # Internal state:
        connection = Null
        lock = Mutex()
        movingAverage = MovingAverage()

    def reset():
        with lock:
            movingAverage.reset()

    def addSample(rtt):
        with lock:
            movingAverage.update(rtt)

    def average():
        with lock:
            return movingAverage.get()

    def run():
        while this monitor is not stopped:
            try:
                rtt = pingServer()
                addSample(rtt)
            except Exception as exc:
                # Don't call reset() here. The Monitor thread is responsible
                # for resetting the average RTT.
                close connection
                connection = Null

            # Can be awakened when the client is closed.
            event.wait(heartbeatFrequencyMS)
            event.clear()

    def setUpConnection():
        connection = new Connection(serverAddress)
        set connection timeout to connectTimeoutMS
        perform connection handshake

    def pingServer():
        if not connection:
            setUpConnection()
            return RTT of the connection handshake

        start = time()
        call {isMaster: 1}
        rtt = time() - start
        return rtt


Design Alternatives
-------------------

Alternating isMaster to check servers and RTT without adding an extra connection
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

The streaming isMaster protocol is optimal in terms of latency; clients
are always blocked waiting for the server to stream updated isMaster
information, they learn of server state changes as soon as possible.
However, streaming isMaster has two downsides:

1. Streaming isMaster requires a new connection to each server to
   calculate the RTT.
2. Streaming isMaster requires a new thread (or threads) to calculate
   the RTT of each server.

To address these concerns we designed the alternating isMaster protocol.
This protocol would have alternated between awaitable isMaster and regular
isMaster. The awaitable isMaster replaces the polling protocol's
client side sleep and allows the client to receive updated isMaster
responses sooner. The regular isMaster allows the client to maintain
accurate RTT calculations without requiring any extra threads or
sockets.

We reject this design because streaming isMaster is strictly better at
reducing the client's time-to-recovery. We determined that one extra
connection per server per MongoClient is reasonable for all drivers.
Applications that upgrade may see a modest increase in connections and
memory usage on the server. We don't expect this increase to be
problematic; however, we have several projects planned for future
MongoDB releases to make the streaming isMaster protocol cheaper
server-side which should mitigate the cost of the extra monitoring
connections.

Use TCP smoothed round-trip time instead of measuring RTT explicitly
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

TCP sockets internally maintain a "smoothed round-trip time" or SRTT. Drivers
could use this SRTT instead of measuring RTT explicitly via isMaster commands.
The server could even include this value on all ismaster responses. We reject
this idea for a few reasons:

- Not all programming languages have an API to access the TCP socket's RTT.
- On Windows, RTT access requires Admin privileges.
- TCP's SRTT would likely differ substantially from RTT measurements in
  the current protocol. For example, the SRTT can be reset on
  `retransmission timeouts <https://tools.ietf.org/html/rfc2988#section-5>`_.

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

Monitors MUST use a dedicated connection for RTT commands
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''

When using the streaming protocol, a monitor needs to maintain an extra
dedicated connection to periodically update its average round trip time in
order to support `localThresholdMS`_ from the Server Selection spec.

It could pop a connection from its regular pool, but we rejected this option
for a few reasons:

- Under contention the RTT task may block application operations from
  completing in a timely manner.
- Under contention the application may block the RTT task from completing in
  a timely manner.
- Under contention the RTT task may often result in an extra connection
  anyway because the pool creates new connections under contention up to maxPoolSize.
- This would be inconsistent with the rule that a monitor SHOULD NOT use the
  client's regular connection pool.

The client could open and close a new connection for each RTT check.
We rejected this design, because if we ping every heartbeatFrequencyMS
(default 10 seconds) then the cost to the client and the server of creating
and destroying the connection might exceed the cost of keeping a dedicated
connection open.

Instead, the client must use a dedicated connection reserved for RTT commands.
Despite the cost of the additional connection per server, we chose this option
as the safest and least likely to result in surprising behavior under load.

Monitors MUST use the isMaster command to measure RTT
'''''''''''''''''''''''''''''''''''''''''''''''''''''

In the streaming protocol, clients could use either the "ping" or "isMaster"
command to measure RTT. This spec chooses "isMaster" for consistency with the
polling protocol as well as consistency with the initial RTT provided the
connection handshake which also uses the isMaster command. Additionally,
mongocryptd does not allow the ping command but does allow isMaster.

Why not use `awaitedTimeMS` in the server response to calculate RTT in the streaming protocol?
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

One approach to calculating RTT in the streaming protocol would be to have the server
return an ``awaitedTimeMS`` in its ``isMaster`` response. A driver could then determine the
RTT by calculating the difference between the initial request, or last response, and the
``awaitedTimeMS``.

We rejected this design because of a number of issue with the unreliability of clocks in
distributed sytems. Clocks skew between local and remote system clocks. This approach mixes
two notions of time: the local clock times the whole operation while the remote clock times
the wait. This means that if these clocks tick at different rates, or there are anomalies
like clock changes, you will get bad results. To make matters worse, you will be comparing
times from multiple servers that could each have clocks ticking at different rates. This
approach will bias toward servers with the fastest ticking clock, since it will seem like it
spends the least time on the wire.

Additionally, systems using NTP will experience clock "slew". ntpd "slews" time by up to 500
parts-per-million to have the local time gradually approach the "true" time without big
jumps - over a 10 second window that means a 5ms difference. If both sides are slewing in
opposite directions, that can result in an effective difference of 10ms. Both of these times
are close enough to `localThresholdMS`_ to significantly affect which servers are viable
in NEAREST calculations.

Ensuring that all measurements use the same clock obviates the need for a more complicated
solution, and mitigates the above mentioned concerns.

Why don't clients mark a server unknown when an RTT command fails?
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

In the streaming protocol, clients use the isMaster command on a dedicated
connection to measure a server's RTT. However, errors encountered when running
the RTT command MUST NOT mark a server Unknown. We reached this decision
because the dedicate RTT connection does not come from a connection pool and
thus does not have a generation number associated with it. Without a generation
number we cannot handle errors from the RTT command without introducing race
conditions. Introducing such a generation number would add complexity to this
design without much benefit. It is safe to ignore these errors because the
Monitor will soon discover the server's state regardless (either through an
updated streaming response, an error on the streaming connection, or by
handling an error on an application connection).

Drivers cancel in-progress monitor checks
'''''''''''''''''''''''''''''''''''''''''

When an application operation fails with a non-timeout network error, drivers
cancel that monitor's in-progress check.

We assume that a non-timeout network error on one application connection
implies that all other connections to that server are also bad. This means
that it is redundant to continue reading on the current monitoring connection.
Instead, we cancel the current monitor check, close the monitoring connection,
and start a new check soon. Note that we rely on the connection/pool
generation number checking to avoid races and ensure that the monitoring
connection is only closed once.

This approach also handles the rare case where the client sees a network error
on an application connection but the monitoring connection is still healthy.
If we did not cancel the monitor check in this scenario, then the server would
remain in the Unknown state until the next isMaster response (up to
maxAwaitTimeMS). A potential real world example of this behavior is when
Azure closes an idle connection in the application pool.

Retry ismaster calls once
'''''''''''''''''''''''''

A monitor's connection to a server is long-lived and used only for ismaster
calls. So if a server has responded in the past, a network error on the
monitor's connection means that there was a network glitch, or a server restart
since the last check, or that the server is truly down. To handle the case
that the server is truly down, the monitor makes the server unselectable by
marking it Unknown. To handle the case of a transient network glitch or
restart, the monitor immediately runs the next check without waiting.

Clear the connection pool on both network and command errors
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

A monitor clears the connection pool when a server check fails with a network
or command error (`Network or command error during server check`_).
When the check fails with a network error it is likely that all connections
to that server are also closed.
(See `JAVA-1252 <https://jira.mongodb.org/browse/JAVA-1252>`_).

When the server is shutting down, it may respond to isMaster commands with
ShutdownInProgress errors before closing connections. In this case, the
monitor clears the connection pool because all connections will be closed soon.
Other command errors are unexpected but are handled identically.

Why must streaming isMaster clients publish ServerHeartbeatStartedEvents?
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

The `SDAM Monitoring spec`_ guarantees that every ServerHeartbeatStartedEvent
has either a correlating ServerHeartbeatSucceededEvent or
ServerHeartbeatFailedEvent. This is consistent with Command Monitoring on
exhaust cursors where the driver publishes a fake CommandStartedEvent before
reading the next getMore response.

Why don't streaming isMaster clients publish events for RTT commands?
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

In the streaming protocol, clients MUST NOT publish any events
(server, topology, command, CMAP, etc..) when running an RTT command. We
considered introducing new RTT events (ServerRTTStartedEvent,
ServerRTTSucceededEvent, ServerRTTFailedEvent) but it's not clear that
there is a demand for this. Applications can still monitor changes to a
server's RTT by listening to TopologyDescriptionChangedEvents.

What is the purpose of the "awaited" field on server heartbeat events?
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

ServerHeartbeatSucceededEvents published from awaitable isMaster
responses will regularly have 10 second durations. The spec introduces
the "awaited" field on server heartbeat events so that applications can
differentiate a slow heartbeat in the polling protocol from a normal
awaitable isMaster heartbeat in the new protocol.


Changelog
---------

- 2020-06-11 Support connectTimeoutMS=0 in streaming heartbeat protocol.

- 2020-05-20 Include rationale for why we don't use `awaitedTimeMS`

- 2020-04-20 Add streaming heartbeat protocol.

- 2020-03-09 A monitor check that creates a new connection MUST use the
  connection's handshake to update the topology.

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
.. _Network error when reading or writing: server-discovery-and-monitoring.rst#network-error-when-reading-or-writing
.. _"not master" and "node is recovering": server-discovery-and-monitoring.rst#not-master-and-node-is-recovering
.. _connection handshake: mongodb-handshake/handshake.rst
.. _localThresholdMS: /source/server-selection/server-selection.rst#localThresholdMS
.. _SDAM Monitoring spec: server-discovery-and-monitoring-monitoring.rst#heartbeats
.. _OP_MSG Spec: /source/message/OP_MSG.rst
.. _OP_MSG exhaustAllowed flag: /source/message/OP_MSG.rst#exhaustAllowed
