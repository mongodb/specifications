=====================
Load Balancer Support
=====================

:Status: Accepted
:Minimum Server Version: 5.0

.. contents::

--------

Abstract
========

This specification defines driver behaviour when connected to MongoDB services
through a load balancer.

META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`__.

Specification
=============


Terms
-----

SDAM
^^^^

An abbreviated form of "Server Discovery and Monitoring", specification defined
in `Server Discovery and Monitoring Specification <../server-discovery-and-monitoring/server-discovery-and-monitoring.rst>`__.

Service
^^^^^^^

Any MongoDB service that can run behind a load balancer.


MongoClient Configuration
-------------------------

loadBalanced
^^^^^^^^^^^^

To specify to the driver to operate in load balancing mode, a connection string
option of :code:`loadBalanced=true` MUST be added to the connection string.
This boolean option specifies whether or not the driver is connecting to a
MongoDB cluster through a load balancer. The default value MUST be false.
This option MUST only be configurable at the level of a :code:`MongoClient`.

URI Validation
^^^^^^^^^^^^^^

When :code:`loadBalanced=true` is provided in the connection string, the driver
MUST throw an exception in the following cases:

- The connection string contains more than one host/port.
- The connection string contains a ``replicaSet`` option.
- The connection string contains a ``directConnection`` option with a value of
  ``true``.
- The connection string contains an ``srvMaxHosts`` option with a positive
  integer value.

If a URI is provided with the ``mongodb+srv`` scheme, the driver MUST first do
the SRV and TXT lookup and then perform the validation. For drivers that do SRV
lookup asynchrounously this may result in a ``MongoClient`` being instantiated
but erroring later during operation execution.


DNS Seedlist Discovery
^^^^^^^^^^^^^^^^^^^^^^

The connection string option for :code:`loadBalanced=true` MUST be valid in a
TXT record and when present MUST be validated as defined in the URI Validation section.

When a MongoClient is configured with an SRV URI and :code:`loadBalanced=true`, the
driver MUST NOT poll for changes in the SRV record as is done for non-load balanced
sharded clusters.

Server Discovery Logging and Monitoring
---------------------------------------

Monitoring
^^^^^^^^^^

When :code:`loadBalanced=true` is specified in the URI the topology MUST start
in type :code:`LoadBalanced` and MUST remain as :code:`LoadBalanced` indefinitely.
The topology MUST contain 1 :code:`ServerDescription` with a :code:`ServerType` of
:code:`LoadBalancer`. The "address" field of the :code:`ServerDescription` MUST be
set to the address field of the load balancer. All other fields in the
:code:`ServerDescription` MUST remain unset. In this mode the driver MUST NOT
start a monitoring connection. The :code:`TopologyDescription`'s :code:`compatible`
field MUST always be :code:`true`.

Although there is no monitoring connection in load balanced mode, drivers MUST emit
the following series of SDAM events:

- :code:`TopologyOpeningEvent` when the topology is created.
- :code:`TopologyDescriptionChangedEvent`. The :code:`previousDescription` field MUST
  have :code:`TopologyType` :code:`Unknown` and no servers. The :code:`newDescription`
  MUST have :code:`TopologyType` :code:`LoadBalanced` and one server with
  :code:`ServerType` :code:`Unknown`.
- :code:`ServerOpeningEvent` when the server representing the load balancer is created.
- :code:`ServerDescriptionChangedEvent`. The :code:`previousDescription` MUST have
  :code:`ServerType` :code:`Unknown`. The :code:`newDescription` MUST have
  :code:`ServerType` :code:`LoadBalancer`.
- :code:`TopologyDescriptionChangedEvent`. The :code:`newDescription` MUST have
  :code:`TopologyType` :code:`LoadBalanced` and one server with :code:`ServerType`
  :code:`LoadBalancer`.

Drivers MUST also emit a :code:`ServerClosedEvent` and :code:`TopologyClosedEvent` when
the topology is closed and MUST NOT emit any other events when operating in this mode.

Log Messages
^^^^^^^^^^^^

SDAM events details described in `Monitoring <#monitoring>_` apply to corresponding log messages.
Please refer to the `SDAM logging specification <../server-discovery-and-monitoring/server-discovery-and-monitoring-logging-and-monitoring#log-messages>`_ 
for details on SDAM logging. Drivers MUST emit the relevant SDAM log messages, such as:

- `Starting Topology Monitoring <../server-discovery-and-monitoring/server-discovery-and-monitoring-logging-and-monitoring.rst#starting-topology-monitoring-log-message>`_ 
- `Stopped Topology Mmonitoring <../server-discovery-and-monitoring/server-discovery-and-monitoring-logging-and-monitoring.rst#stopped-topology-monitoring-log-message>`_ 
- `Starting Server Monitoring <../server-discovery-and-monitoring/server-discovery-and-monitoring-logging-and-monitoring.rst#starting-server-monitoring-log-message>`_ 
- `Stopped Server Monitoring <../server-discovery-and-monitoring/server-discovery-and-monitoring-logging-and-monitoring.rst#stopped-server-monitoring-log-message>`_ 
- `Topology Description Changed <../server-discovery-and-monitoring/server-discovery-and-monitoring-logging-and-monitoring.rst#topology-description-changed-log-message>`_ 

Driver Sessions
---------------

Session Support
^^^^^^^^^^^^^^^

When the :code:`TopologyType` is :code:`LoadBalanced`, sessions are always supported.

Session Expiration
^^^^^^^^^^^^^^^^^^

When in load balancer mode, drivers MUST ignore :code:`logicalSessionTimeoutMinutes`
and MUST NOT prune client sessions from the session pool when implemented by the driver.

Data-Bearing Server Type
^^^^^^^^^^^^^^^^^^^^^^^^

A :code:`ServerType` of :code:`LoadBalancer` MUST be considered a data-bearing server.


Server Selection
----------------

A deployment of topology type Load Balanced contains one server of type :code:`LoadBalancer`.

For read and write operations, the single server in the topology MUST always be selected.

During command construction, the LoadBalancer server MUST be treated like a mongos and
drivers MUST add a $readPreference field to the command when required by
`Passing read preference to mongos and load balancers <../server-selection/server-selection.rst#passing-read-preference-to-mongos-and-load-balancers>`_.


Connection Pooling
------------------

Connection Establishment
^^^^^^^^^^^^^^^^^^^^^^^^

In the case of the driver having the :code:`loadBalanced=true` connection string option
specified, every pooled connection MUST add a :code:`loadBalanced` field to the
:code:`hello` command in its `handshake <../mongodb-handshake/handshake.rst#connection-handshake>`__.
The value of the field MUST be :code:`true`. If :code:`loadBalanced=true` is
specified then the ``OP_MSG`` protocol MUST be used for all steps of the
connection handshake.

Example:

Driver connection string contains :code:`loadBalanced=true`:

.. code:: typescript

    { hello: 1, loadBalanced: true }

Driver connection string contains :code:`loadBalanced=false` or no
:code:`loadBalanced` option:

.. code:: typescript

    { hello: 1 }

When the server's hello response does not contain a :code:`serviceId` field,
the driver MUST throw an exception with the message "Driver attempted to initialize
in load balancing mode, but the server does not support this mode."

For single threaded drivers that do not use a connection pool, the driver MUST have only 1
socket connection to the load balancer in load balancing mode.

Connection Pinning
^^^^^^^^^^^^^^^^^^

Some features in MongoDB such as cursors and transactions require sending multiple
commands to the same mongos in a sharded cluster. In load balanced mode, it is not
possible to target the same mongos behind a load balancer when pooling connections.
To account for this, drivers MUST pin to a single connection for these features.
When using a pinned connection, the driver MUST emit only 1
:code:`ConnectionCheckOutStartedEvent`, and only 1 :code:`ConnectionCheckedOutEvent`
or :code:`ConnectionCheckOutFailedEvent`. Similarly, the driver MUST only publish 1
:code:`ConnectionCheckedInEvent`.

Behaviour With Cursors
^^^^^^^^^^^^^^^^^^^^^^

When the driver is in load balancing mode and executing any cursor-initiating command, the driver
MUST NOT check the connection back into the pool unless the command fails or the server
returns a cursor ID of :code:`0` (i.e. all documents are returned in a single batch).
Otherwise, the driver MUST continue to use the same connection for all subsequent
:code:`getMore` commands for the cursor. The driver MUST check the connection back
into the pool if the server returns a cursor ID of :code:`0` in a :code:`getMore`
response (i.e. the cursor is drained). When the cursor's :code:`close` method is
invoked, either explicitly or via an implicit resource cleanup mechanism, the driver
MUST use the same connection to execute a :code:`killCursors` command if necessary
and then check the connection back into the pool regardless of the result.

For multi-threaded drivers, cursors with pinned connections MUST either document to the user
that calling :code:`next()` and :code:`close()` operations on the cursor concurrently
is not permitted, or explicitly prevent cursors from executing those operations
simultaneously.

If a :code:`getMore` fails with a network error, drivers MUST leave the connection pinned
to the cursor. When the cursor's :code:`close` method is invoked, drivers MUST NOT execute
a :code:`killCursors` command because the pinned connection is no longer valid and MUST
return the connection back to the pool.

Behaviour With Transactions
^^^^^^^^^^^^^^^^^^^^^^^^^^^

When executing a transaction in load balancing mode, drivers MUST follow the rules outlined
in `Sharded Transactions <../transactions/transactions.rst#sharded-transactions>`__ with one
exception: drivers MUST use the same connection for all commands in the transaction
(excluding retries of commitTranscation and abortTransaction in some cases). Pinning
to a single connection ensures that all commands in the transaction target the same
service behind the load balancer. The rules for pinning to a connection and releasing
a pinned connection are the same as those for server pinning in non-load balanced sharded
transactions as described in `When to unpin <../transactions/transactions.rst#when-to-unpin>`__.
Drivers MUST NOT use the same connection for two concurrent transactions run under different
sessions from the same client.

Connection Tracking
^^^^^^^^^^^^^^^^^^^

The driver connection pool MUST track the purpose for which connections are checked out
in the following 3 categories:

- Connections checked out for cursors
- Connections checked out for transactions
- Connections checked out for operations not falling under the previous 2 categories

When the connection pool's :code:`maxPoolSize` is reached and the pool times out waiting
for a new connection the :code:`WaitQueueTimeoutError` MUST include a new detailed message,
"Timeout waiting for connection from the connection pool. maxPoolSize: n, connections
in use by cursors: n, connections in use by transactions: n, connections in use by other
operations: n".


Error Handling
--------------

Initial Handshake Errors
^^^^^^^^^^^^^^^^^^^^^^^^

When establishing a new connection in load balanced mode, drivers MUST NOT perform SDAM
error handling for any errors that occur before the MongoDB Handshake
(i.e. :code:`hello` command) is complete. Errors during the MongoDB
Handshake MUST also be ignored for SDAM error handling purposes. Once the initial
handshake is complete, the connection MUST determine its generation number based
on the :code:`serviceId` field in the handshake response. Any errors that occur
during the rest of connection establishment (e.g. errors during authentication commands)
MUST go through the SDAM error handling flow but MUST NOT mark the server as
:code:`Unknown` and when requiring the connection pool to be cleared, MUST only
clear connections for the :code:`serviceId`.

Post-Handshake Errors
^^^^^^^^^^^^^^^^^^^^^^

When the driver is operating in load balanced mode and an application operation receives a
state change error, the driver MUST NOT make any changes to the :code:`TopologyDescription`
or the :code:`ServerDescription` of the load balancer (i.e. it MUST NOT mark the load
balancer as :code:`Unknown`). If the error requires the connection pool to be cleared,
the driver MUST only clear connections with the same :code:`serviceId` as the connection
which errored.


Events
------

When in load balancer mode the driver MUST now include the :code:`serviceId` in the
:code:`CommandStartedEvent`, :code:`CommandSucceededEvent`, and
:code:`CommandFailedEvent`. The driver MAY decide how to expose this information.
Drivers that have a :code:`ConnectionId` object for example, MAY choose to provide a
:code:`serviceId` in that object. The :code:`serviceId` field is only present when
in load balancer mode and connected to a service that is behind a load balancer.

Additionally the :code:`PoolClearedEvent` MUST also contain a :code:`serviceId`
field.


Downstream Visible Behavioral Changes
-------------------------------------

Services MAY add a command line option or other configuration parameter, that tells the service
it is running behind a load balancer. Services MAY also dynamically determine whether they are
behind a load balancer.

All services which terminate TLS MUST be configured to return a TLS certificate for a hostname
which matches the hostname the client is connecting to.

All services behind a load balancer that have been started with the aforementioned option MUST
add a top level :code:`serviceId` field to their response to the :code:`hello`
command. This field MUST be a BSON :code:`ObjectId` and SHOULD NOT change while the service is running.
When a driver is configured to not be in load balanced mode and the service is configured behind
a load balancer, the service MAY return an error from the driver's :code:`hello` command that
the driver is not configured to use it properly.

All services that have the behaviour of reaping idle cursors after a specified period of time MAY
also close the connection associated with the cursor when the cursor is reaped. Conversely, those
services MAY reap a cursor when the connection associated with the cursor is closed.

All services that have the behaviour of reaping idle transactions after a specified period of time
MAY also close the connection associated with the transaction when the transaction is reaped.
Conversely, those services must abort a transaction when the connection associated with the
transaction is closed.

Any applications that connect directly to services and not through the load balancer MUST connect
via the regular service port as they normally would and not the port specified by the
`loadBalancerPort` option. The `loadBalanced=true` URI option MUST be omitted in this case.


Q&A
---

Why use a connection string option instead of a new URI scheme?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use of a connection string option would allow the driver to continue to use SRV records that
pointed at a load balancer instead of a replica set without needing to change the URI provided
to the :code:`MongoClient`. The SRV records could also provide the default :code:`loadBalanced=true`
in the TXT records.

Why explicitly opt-in to this behaviour instead of letting mongos inform the driver of the load balancer?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Other versions of this design proposed a scheme in which the application does not have to opt-in to
load balanced mode. Instead, the server would send a special field in :code:`hello`
command responses to indicate that it was running behind a load balancer and the driver would change
its behavior accordingly. We opted to take an approach that required code changes instead because
load balancing changes driver behavior in ways that could cause unexpected application errors, so
it made sense to have applications consciously opt-in to this mode. For example, connection pinning
creates new stresses on connection pools because we go from a total of :code:`numMongosServers * maxPoolSize`
connections to simply maxPoolSize. Furthermore, connections get pinned to open cursors and transactions,
further straining resource availability. Due to this change, applications may also need to increase
the configured :code:`maxPoolSize` when opting into this mode.

Why does this specification instruct drivers to not check connections back into the connection pool in some circumstances?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the case of a load balancer fronting multiple services, it is possible that a connection to the
load balancer could result in a connection behind the load balancer to a different service. In
order to guarantee these operations execute on the same service they need to be executed on the
same socket - not checking a connection back into the pool for the entire operation guarantees this.

What reason has a client side connection reaper for idle cursors not been put into this specification?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It was discussed as a potential solution for maxed out connection pools that the drivers could
potentially behave similar to the server and close long running cursors after a specified time
period and return their connections to the pool. Due to the high complexity of that solution
it was determined that better error messaging when the connection pool was maxed out would
suffice in order for users to easily debug when the pool ran out of connections and fix their
applications or adjust their pool options accordingly.

Why are we requiring mongos servers to add a new serviceId field in hello responses rather than reusing the existing topologyVersion.processId?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This option was previously discussed, but we opted to add a new :code:`hello` response field in
order to not mix intentions.

Why does this specification not address load balancer restarts or maintenance?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Layer 4 load balancers that would be in use for this feature lack the
ability that a layer 7 load balancer could potentially have to be able to
understand the MongoDB wire protocol and respond to monitoring requests.


Design Rationales
-----------------

Services cannot dynamically switch from running behind a load balancer and not running behind
a load balancer. Based on that, this design forces the application to opt-in to this behaviour
and make potential changes that require restarts to their applications. If this were to change,
see alternative designs below.


Alternative Designs
-------------------

Service PROXY Detection
^^^^^^^^^^^^^^^^^^^^^^^

An alternative to the driver using a connection string option to put it into load balancing
mode would be for the service the driver is connected to to inform the driver it is behind
a load balancer. A possible solution for this would be for all services to understand the
PROXY protocol such as Data Lake does, and to alter their hello responses to inform the
driver they are behind a load balancer, potentially with the IP address of the load balancer itself.

The benefit of this solution would be that no changes would be required from the application
side, and could also not require a restart of any application. A single request to the service
through the load balancer could automatically trigger the change in the hello response and
cause the driver to switch into load balancing mode pointing at the load balancer's IP address.
Also with this solution it would provide services the ability to record the original IP addresses
of the application that was connecting to it as they are provided the PROXY protocol's header bytes.

The additional complexity of this alternative on the driver side is that instead of starting
in a single mode and remaining there for the life of the application, the driver would need
to deal with additional state changes based on the results of the server monitors. From a
service perspective, every service would need to be updated to understand the PROXY protocol
header bytes prepended to the initial connection and modify their states and hello responses
accordingly. Additionally load balancers would need to have additional configuration as noted
in the reference section below, and only load balancers that support the PROXY protocol would
be supported.


Changelog
=========

:2022-10-05: Remove spec front matter and reformat changelog.
:2022-01-18: Clarify that ``OP_MSG`` must be used in load balanced mode.
:2021-12-22: Clarify that pinned connections in transactions are exclusive.
:2021-10-14: Note that ``loadBalanced=true`` conflicts with ``srvMaxHosts``.
