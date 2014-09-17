==========================================
Server Discovery And Monitoring -- Summary
==========================================

:Spec: 101
:Title: Server Discovery And Monitoring
:Author: A\. Jesse Jiryu Davis
:Advisors: David Golden, Craig Wilson
:Status: Draft
:Type: Standards
:Last Modified: September 8, 2014

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

The server discovery and monitoring method is specified in five sections.
First, a client is constructed.
Second, it begins monitoring the topology by calling ismaster on all servers.
(Multi-threaded and asynchronous monitoring is described first,
then single-threaded monitoring.)
Third, as ismaster calls are received
the client parses them,
and fourth, it updates its view of the topology.
Finally, this spec describes how drivers update their topology view
in response to errors.

This spec does not describe how a client selects a server for an operation;
that is the domain of the specs for Mongos High Availability
and for Read Preferences.
There is no discussion of driver architecture and data structures,
nor is there any specification of a user-facing API.
This spec is only concerned with the algorithm for monitoring the topology.

The Java driver 2.12.1 is the reference implementation
for multi-threaded drivers.
Mongos 2.6's replica set monitor
is the reference implementation for single-threaded drivers,
with a few differences.

General Requirements
--------------------

A client MUST be able to connect to a single server of any type.
This includes querying hidden replica set members,
and connecting to uninitialized members in order to run
"replSetInitiate".

A client MUST be able to discover an entire replica set from
a seed list containing one or more replica set members.
It MUST be able to continue monitoring the replica set
even when some members go down,
or when reconfigs add and remove members.
A client MUST be able to connect to a replica set
while there is no primary, or while the primary is down.

A client MUST be able to connect to a set of mongoses
and monitor their availability and round trip time.
This spec defines how mongoses are discovered and monitored,
but does not define which mongos is selected for a given operation.

A client MUST be able to directly connect to a mongod begun with "--slave".
No additional master-slave features are described in this spec.

Multi-threaded or asynchronous clients
MUST unblock waiting operations
as soon as a suitable server is found,
rather than waiting for all servers to be checked.
For example, if the client is discovering a replica set
and the application attempts a write operation,
the write operation MUST proceed as soon as the primary is found,
rather than blocking until the client has checked all members.

Client Construction
-------------------

This spec does not intend
to require any drivers to make breaking changes regarding
what configuration options are available,
how options are named,
or what combinations of options are allowed.

A multi-threaded or asynchronous client's constructor MUST NOT do any I/O.
The constructor MAY start the monitors as background tasks,
or they MAY be started by some "initialize" method (by any name),
or on the first use of the client for an operation.
This means that the constructor does not throw an exception
if the deployment is unavailable:
Instead, all subsequent operations on the client fail
as long as the error persists.

The justification is that
if clients can be constructed when the deployment is in some states
but not in other states,
it leads to an unfortunate scenario:
When the deployment is passing through a strange state,
long-running applications may keep working,
but any applications restarted during this period fail.

Additionally, since asynchronous clients cannot do I/O in a constructor,
it is consistent to prohibit I/O in other clients' constructors as well.

Single-threaded clients also MUST NOT do I/O in the constructor.
They scan the servers on demand,
when the first operation is attempted.
Thus they behave consistently with multi-threaded and asynchronous clients.

Monitoring
----------

The client monitors servers by checking them periodically,
or after an error indicates that the client's view of the topology is wrong,
or when no suitable server is found for a write or a read.

Drivers differ from Mongos 2.6 in two respects. First,
if a client frequently rechecks a server,
it MUST wait at least 10 ms
since the previous check to avoid excessive effort.

Second, Mongos 2.6 does not monitor arbiters, but drivers MUST do so.
It costs little, and in rare cases an arbiter may be the client's last hope
to find the new replica set configuration.

Multi-threaded or asynchronous monitoring
'''''''''''''''''''''''''''''''''''''''''

All servers' monitors run independently, in parallel:
If some monitors block calling ismaster over slow connections,
other monitors MUST proceed unimpeded.
The natural implementation is a thread per server,
but the decision is left to the implementer.

Multi-threaded and asynchronous drivers
MUST call ismaster on servers every 10 seconds by default.
(10 seconds is Mongos's frequency.)
This frequency MAY be configurable.

Single-threaded monitoring
''''''''''''''''''''''''''

Single-threaded clients MUST scan all servers synchronously,
inline with regular application operations.
For single-threaded drivers the default frequency MUST be 60 seconds
and MUST be configurable.

If the topology is a replica set,
a single-threaded client attempts to contact the primary as soon as possible
to get an authoritative list of members.
Otherwise, the client attempts to check all members it knows of,
in order from the least-recently to the most-recently checked.
The scanning order is described completely in the spec.

Parsing ismaster
----------------

The full algorithm for determining server type from an ismaster response
is specified and test cases are provided.

Drivers MUST record the server's round trip time
after each successful call to ismaster.
How round trip times are averaged is not in this spec's scope.

Updating the Topology View
--------------------------

After each attempt to call ismaster on a server,
the client updates its topology view.
Initial topology discovery and long-running monitoring
are both specified by the same detailed algorithm.

When monitoring a replica set,
the client strives to use only the servers that the primary says are members.
While there is no known primary,
the client MUST add servers from non-primaries' host lists,
but it MUST NOT remove servers.
Eventually, when a primary is discovered, any hosts not in the primary's host
list are removed from the client's view of the topology.

The client MUST NOT use replica set members' "setVersion"
to detect reconfigs, since race conditions with setVersion
make it inferior to simply trusting the primary.

Error handling
--------------

When an application operation fails because of
any network error besides a socket timeout,
the client MUST mark the server "down".
The server will eventually be re-checked by periodic monitoring.
The specific operation that discovered the error
MUST abort and raise an exception if it was a write.
It MAY be retried if it was a read.
(The Read Preferences spec includes retry rules for reads.)

If a monitor's ismaster call fails on a server,
the behavior is different from a failed application operation.
The ismaster call is retried once, immediately,
before the server is marked "down".

In either case the client SHOULD clear its connection pool for the server:
if one socket is bad, it is likely that all are.

An algorithm is specified for parsing
"not master" and "node is recovering" errors.
When the client sees such an error it knows its topology view is out of date.
It MUST mark the server type "unknown."
Multi-threaded and asynchronous clients MUST re-check the server soon,
and single-threaded clients MUST request a scan before the next operation.
The client SHOULD clear its connection pool for the server.
