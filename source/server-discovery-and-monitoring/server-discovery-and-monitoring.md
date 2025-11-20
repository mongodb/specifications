# Server Discovery And Monitoring

- Status: Accepted
- Minimum Server Version: 2.4

______________________________________________________________________

## Abstract

This spec defines how a MongoDB client discovers and monitors one or more servers. It covers monitoring a single server,
a set of mongoses, or a replica set. How does the client determine what type of servers they are? How does it keep this
information up to date? How does the client find an entire replica set from a seed list, and how does it respond to a
stepdown, election, reconfiguration, or network error?

All drivers must answer these questions the same. Or, where platforms' limitations require differences among drivers,
there must be as few answers as possible and each must be clearly explained in this spec. Even in cases where several
answers seem equally good, drivers must agree on one way to do it.

MongoDB users and driver authors benefit from having one way to discover and monitor servers. Users can substantially
understand their driver's behavior without inspecting its code or asking its author. Driver authors can avoid subtle
mistakes when they take advantage of a design that has been well-considered, reviewed, and tested.

The server discovery and monitoring method is specified in four sections. First, a client is
[configured](#configuration). Second, it begins [monitoring](#monitoring) by calling
[hello or legacy hello](../mongodb-handshake/handshake.md#terms) on all servers. (Multi-threaded and asynchronous
monitoring is described first, then single-threaded monitoring.) Third, as hello or legacy hello responses are received
the client [parses them](#parsing-a-hello-or-legacy-hello-response), and fourth, it updates its view of the topology.

Finally, this spec describes how drivers update their topology view in response to errors, and includes generous
implementation notes for driver authors.

This spec does not describe how a client chooses a server for an operation; that is the domain of the Server Selection
Spec. But there is a section describing the interaction between monitoring and server selection.

There is no discussion of driver architecture and data structures, nor is there any specification of a user-facing API.
This spec is only concerned with the algorithm for monitoring the server topology.

## Meta

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

### General Requirements

**Direct connections:** A client MUST be able to connect to a single server of any type. This includes querying hidden
replica set members, and connecting to uninitialized members (see [RSGhost](#rsghost-and-rsother)) in order to run
"replSetInitiate". Setting a read preference MUST NOT be necessary to connect to a secondary. Of course, the secondary
will reject all operations done with the PRIMARY read preference because the secondaryOk bit is not set, but the initial
connection itself succeeds. Drivers MAY allow direct connections to arbiters (for example, to run administrative
commands).

**Replica sets:** A client MUST be able to discover an entire replica set from a seed list containing one or more
replica set members. It MUST be able to continue monitoring the replica set even when some members go down, or when
reconfigs add and remove members. A client MUST be able to connect to a replica set while there is no primary, or the
primary is down.

**Mongos:** A client MUST be able to connect to a set of mongoses and monitor their availability and
[round trip time](#round-trip-time). This spec defines how mongoses are discovered and monitored, but does not define
which mongos is selected for a given operation.

### Terms

#### Server

A mongod or mongos process, or a load balancer.

#### Deployment

One or more servers: either a standalone, a replica set, or one or more mongoses.

#### Topology

The state of the deployment: its type (standalone, replica set, or sharded), which servers are up, what type of servers
they are, which is primary, and so on.

#### Client

Driver code responsible for connecting to MongoDB.

#### Seed list

Server addresses provided to the client in its initial configuration, for example from the
[connection string](https://www.mongodb.com/docs/manual/reference/connection-string/).

#### Data-Bearing Server Type

A server type from which a client can receive application data:

- Mongos
- RSPrimary
- RSSecondary
- Standalone
- LoadBalanced

#### Round trip time

Also known as RTT.

The client's measurement of the duration of one hello or legacy hello call. The round trip time is used to support the
"localThresholdMS"[^1] option in the Server Selection Spec.

#### hello or legacy hello outcome

The result of an attempt to call the hello or legacy hello command on a server. It consists of three elements: a boolean
indicating the success or failure of the attempt, a document containing the command response (or null if it failed), and
the round trip time to execute the command (or null if it failed).

#### check

The client checks a server by attempting to call hello or legacy hello on it, and recording the outcome.

#### scan

The process of checking all servers in the deployment.

#### suitable

A server is judged "suitable" for an operation if the client can use it for a particular operation. For example, a write
requires a standalone, primary, or mongos. Suitability is fully specified in the
[Server Selection Spec](../server-selection/server-selection.md).

#### address

The hostname or IP address, and port number, of a MongoDB server.

#### network error

An error that occurs while reading from or writing to a network socket.

#### network timeout

A timeout that occurs while reading from or writing to a network socket.

#### minHeartbeatFrequencyMS

Defined in the [Server Monitoring spec](server-monitoring.md). This value MUST be 500 ms, and it MUST NOT be
configurable.

#### pool generation number

The pool's generation number which starts at 0 and is incremented each time the pool is cleared. Defined in the
[Connection Monitoring and Pooling spec](../connection-monitoring-and-pooling/connection-monitoring-and-pooling.md).

#### connection generation number

The pool's generation number at the time this connection was created. Defined in the
[Connection Monitoring and Pooling spec](../connection-monitoring-and-pooling/connection-monitoring-and-pooling.md).

#### error generation number

The error's generation number is the generation of the connection on which the application error occurred. Note that
when a network error occurs before the handshake completes then the error's generation number is the generation of the
pool at the time the connection attempt was started.

#### State Change Error

A server reply document indicating a "not writable primary" or "node is recovering" error. Starting in MongoDB 4.4 these
errors may also include a [topologyVersion](#topologyversion) field.

### Data structures

This spec uses a few data structures to describe the client's view of the topology. It must be emphasized that a driver
is free to implement the same behavior using different data structures. This spec uses these enums and structs in order
to describe driver **behavior**, not to mandate how a driver represents the topology, nor to mandate an API.

#### Constants

##### clientMinWireVersion and clientMaxWireVersion

Integers. The wire protocol range supported by the client.

#### Enums

##### TopologyType

Single, ReplicaSetNoPrimary, ReplicaSetWithPrimary, Sharded, LoadBalanced, or Unknown.

See [updating the TopologyDescription](#updating-the-topologydescription).

##### ServerType

Standalone, Mongos, PossiblePrimary, RSPrimary, RSSecondary, RSArbiter, RSOther, RSGhost, LoadBalancer or Unknown.

See [parsing a hello or legacy hello response](#parsing-a-hello-or-legacy-hello-response).

> [!NOTE]
> Single-threaded clients use the PossiblePrimary type to maintain proper
> [scanning order](server-monitoring.md#scanning-order). Multi-threaded and asynchronous clients do not need this
> ServerType; it is synonymous with Unknown.

<span id="TopologyDescription"></span>

#### TopologyDescription

The client's representation of everything it knows about the deployment's topology.

Fields:

- `type`: a [TopologyType](#topologytype) enum value. See [initial TopologyType](#initial-topologytype).
- `setName`: the replica set name. Default null.
- `maxElectionId`: an ObjectId or null. The largest electionId ever reported by a primary. Default null. Part of the
    (`electionId`, `setVersion`) tuple.
- `maxSetVersion`: an integer or null. The largest setVersion ever reported by a primary. It may not monotonically
    increase, as electionId takes precedence in ordering Default null. Part of the (`electionId`, `setVersion`) tuple.
- `servers`: a set of ServerDescription instances, one for each of the servers in the topology.
- `stale`: a boolean for single-threaded clients, whether the topology must be re-scanned. (Not related to
    maxStalenessSeconds, nor to stale primaries.)
- `compatible`: a boolean. False if any server's wire protocol version range is incompatible with the client's. Default
    true.
- `compatibilityError`: a string. The error message if "compatible" is false, otherwise null.
- `logicalSessionTimeoutMinutes`: integer or null. Default null. See
    [logical session timeout](#logical-session-timeout).

#### ServerDescription

The client's view of a single server, based on the most recent hello or legacy hello outcome.

Again, drivers may store this information however they choose; this data structure is defined here merely to describe
the monitoring algorithm.

Fields:

- `address`: the hostname or IP, and the port number, that the client connects to. Note that this is **not** the `me`
    field in the server's hello or legacy hello response, in the case that the server reports an address different from
    the address the client uses.

- (=) `error`: information about the last error related to this server. Default null. MUST contain or be able to produce
    a string describing the error.

- `roundTripTime`: the duration of the hello or legacy hello call. Default null.

- `minRoundTripTime`: the minimum RTT for the server. Default null.

- `lastWriteDate`: a 64-bit BSON datetime or null. The `lastWriteDate` from the server's most recent hello or legacy
    hello response.

- `opTime`: an opTime or null. An opaque value representing the position in the oplog of the most recently seen write.
    Default null. (Only mongos and shard servers record this field when monitoring config servers as replica sets, at
    least until
    [drivers allow applications to use readConcern "afterOptime".](../max-staleness/max-staleness.md#future-feature-to-support-readconcern-afteroptime))

- (=) `type`: a [ServerType](#servertype) enum value. Default Unknown.

- (=) `minWireVersion`, `maxWireVersion`: the wire protocol version range supported by the server. Both default to 0.
    [Use min and maxWireVersion only to determine compatibility](#checking-wire-protocol-compatibility).

- (=) `me`: The hostname or IP, and the port number, that this server was configured with in the replica set. Default
    null.

- (=) `hosts`, `passives`, `arbiters`: Sets of addresses. This server's opinion of the replica set's members, if any.
    These [hostnames are normalized to lower-case](#hostnames-are-normalized-to-lower-case). Default empty. The client
    monitors all three types of servers in a replica set.

- (=) `tags`: map from string to string. Default empty.

- (=) `setName`: string or null. Default null.

- (=) `electionId`: an ObjectId, if this is a MongoDB 2.6+ replica set member that believes it is primary. See
    [using electionId and setVersion to detect stale primaries](#using-electionid-and-setversion-to-detect-stale-primaries).
    Default null.

- (=) `setVersion`: integer or null. Default null.

- (=) `primary`: an address. This server's opinion of who the primary is. Default null.

- `lastUpdateTime`: when this server was last checked. Default "infinity ago".

- (=) `logicalSessionTimeoutMinutes`: integer or null. Default null.

- (=) `topologyVersion`: A topologyVersion or null. Default null. The "topologyVersion" from the server's most recent
    hello or legacy hello response or [State Change Error](#state-change-error).

- (=) `iscryptd`: boolean indicating if the server is a
    [mongocryptd](../client-side-encryption/client-side-encryption.md#mongocryptd) server. Default null.

"Passives" are priority-zero replica set members that cannot become primary. The client treats them precisely the same
as other members.

Fields marked (=) are used for [Server Description Equality](#server-description-equality) comparison.

### Configuration

#### No breaking changes

This spec does not intend to require any drivers to make breaking changes regarding what configuration options are
available, how options are named, or what combinations of options are allowed.

#### Initial TopologyDescription

The default values for [TopologyDescription](#topologydescription) fields are described above. Users may override the
defaults as follows:

##### Initial Servers

The user MUST be able to set the initial servers list to a [seed list](#seed-list) of one or more addresses.

The hostname portion of each address MUST be normalized to lower-case.

##### Initial TopologyType

If the `directConnection` URI option is specified when a MongoClient is constructed, the TopologyType must be
initialized based on the value of the `directConnection` option and the presence of the `replicaSet` option according to
the following table:

| directConnection | replicaSet present | Initial TopologyType |
| ---------------- | ------------------ | -------------------- |
| true             | no                 | Single               |
| true             | yes                | Single               |
| false            | no                 | Unknown              |
| false            | yes                | ReplicaSetNoPrimary  |

If the `directConnection` option is not specified, newly developed drivers MUST behave as if it was specified with the
false value.

Since changing the starting topology can reasonably be considered a backwards-breaking change, existing drivers SHOULD
stage implementation according to semantic versioning guidelines. Specifically, support for the `directConnection` URI
option can be added in a minor release. In a subsequent major release, the default starting topology can be changed to
Unknown. Drivers MUST document this in a prior minor release.

Existing drivers MUST deprecate other URI options, if any, for controlling topology discovery or specifying the
deployment topology. If such a legacy option is specified and the `directConnection` option is also specified, and the
values of the two options are semantically different, the driver MUST report an error during URI option parsing.

The API for initializing TopologyType using language-specific native options is not specified here. Drivers might
already have a convention, e.g. a single seed means Single, a setName means ReplicaSetNoPrimary, and a list of seeds
means Unknown. There are variations, however: In the Java driver a single seed means Single, but a **list** containing
one seed means Unknown, so it can transition to replica-set monitoring if the seed is discovered to be a replica set
member. In contrast, PyMongo requires a non-null setName in order to begin replica-set monitoring, regardless of the
number of seeds. This spec does not cover language-specific native options that a driver may provide.

##### Initial setName

It is allowed to use `directConnection=true` in conjunction with the `replicaSet` URI option. The driver must connect in
Single topology and verify that setName matches the specified name, as per
[verifying setName with TopologyType Single](#verifying-setname-with-topologytype-single).

When a MongoClient is initialized using language-specific native options, the user MUST be able to set the client's
initial replica set name. A driver MAY require the set name in order to connect to a replica set, or it MAY be able to
discover the replica set name as it connects.

##### Allowed configuration combinations

Drivers MUST enforce:

- TopologyType Single cannot be used with multiple seeds.
- `directConnection=true` cannot be used with multiple seeds.
- If setName is not null, only TopologyType ReplicaSetNoPrimary, and possibly Single, are allowed. (See
    [verifying setName with TopologyType Single](#verifying-setname-with-topologytype-single).)
- `loadBalanced=true` cannot be used in conjunction with `directConnection=true` or `replicaSet`

##### Handling of SRV URIs resolving to single host

When a driver is given an SRV URI, if the `directConnection` URI option is not specified, and the `replicaSet` URI
option is not specified, the driver MUST start in Unknown topology, and follow the rules in the
[TopologyType table](#topologytype-table) for transitioning to other topologies. In particular, the driver MUST NOT use
the number of hosts from the initial SRV lookup to decide what topology to start in.

<span id="heartbeatFrequencyMS"></span>

#### heartbeatFrequencyMS

The interval between server [checks](#check), counted from the end of the previous check until the beginning of the next
one.

For multi-threaded and asynchronous drivers it MUST default to 10 seconds and MUST be configurable. For single-threaded
drivers it MUST default to 60 seconds and MUST be configurable. It MUST be called heartbeatFrequencyMS unless this
breaks backwards compatibility.

For both multi- and single-threaded drivers, the driver MUST NOT permit users to configure it less than
minHeartbeatFrequencyMS (500ms).

(See
[heartbeatFrequencyMS defaults to 10 seconds or 60 seconds](#heartbeatfrequencyms-defaults-to-10-seconds-or-60-seconds)
and [what's the point of periodic monitoring?](#whats-the-point-of-periodic-monitoring))

### Client construction

Except for [initial DNS seed list discovery](../initial-dns-seedlist-discovery/initial-dns-seedlist-discovery.md) when
given a connection string with `mongodb+srv` scheme, the client's constructor MUST NOT do any I/O. This means that the
constructor does not throw an exception if servers are unavailable: the topology is not yet known when the constructor
returns. Similarly if a server has an incompatible wire protocol version, the constructor does not throw. Instead, all
subsequent operations on the client fail as long as the error persists.

See [clients do no I/O in the constructor](#clients-do-no-io-in-the-constructor) for the justification.

#### Multi-threaded and asynchronous client construction

The constructor MAY start the monitors as background tasks and return immediately. Or the monitors MAY be started by
some method separate from the constructor; for example they MAY be started by some "initialize" method (by any name), or
on the first use of the client for an operation.

#### Single-threaded client construction

Single-threaded clients do no I/O in the constructor. They MUST [scan](#scan) the servers on demand, when the first
operation is attempted.

### Client closing

When a client is closing, before it emits the `TopologyClosedEvent` as per the
[Events API](./server-discovery-and-monitoring-logging-and-monitoring.md#events-api), it SHOULD [remove](#remove) all
servers from its `TopologyDescription` and set its `TopologyType` to `Unknown`, emitting the corresponding
`TopologyDescriptionChangedEvent`.

### Monitoring

See the [Server Monitoring spec](server-monitoring.md) for how a driver monitors each server. In summary, the client
monitors each server in the topology. The scope of server monitoring is to provide the topology with updated
ServerDescriptions based on hello or legacy hello command responses.

### Parsing a hello or legacy hello response

The client represents its view of each server with a [ServerDescription](#serverdescription). Each time the client
[checks](#check) a server, it MUST replace its description of that server with a new one if and only if the new
ServerDescription's [topologyVersion](#topologyversion) is greater than or equal to the current ServerDescription's
[topologyVersion](#topologyversion).

(See [Replacing the TopologyDescription](#replacing-the-topologydescription) for an example implementation.)

This replacement MUST happen even if the new server description compares equal to the previous one, in order to keep
client-tracked attributes like last update time and round trip time up to date.

Drivers MUST be able to handle responses to both `hello` and legacy hello commands. When checking results, drivers MUST
first check for the `isWritablePrimary` field and fall back to checking for an `ismaster` field if `isWritablePrimary`
was not found.

ServerDescriptions are created from hello or legacy hello outcomes as follows:

#### type

The new ServerDescription's type field is set to a [ServerType](#servertype). Note that these states do **not** exactly
correspond to [replica set member states](https://www.mongodb.com/docs/manual/reference/replica-states/). For example,
some replica set member states like STARTUP and RECOVERING are identical from the client's perspective, so they are
merged into "RSOther". Additionally, states like Standalone and Mongos are not replica set member states at all.

| State           | Symptoms                                                                                                 |
| --------------- | -------------------------------------------------------------------------------------------------------- |
| Unknown         | Initial, or after a failed hello or legacy hello call, or "ok: 1" not in hello or legacy hello response. |
| Standalone      | No "msg: isdbgrid", no setName, and no "isreplicaset: true".                                             |
| Mongos          | "msg: isdbgrid".                                                                                         |
| PossiblePrimary | Not yet checked, but another member thinks it is the primary.                                            |
| RSPrimary       | "isWritablePrimary: true" or "ismaster: true", "setName" in response.                                    |
| RSSecondary     | "secondary: true", "setName" in response.                                                                |
| RSArbiter       | "arbiterOnly: true", "setName" in response.                                                              |
| RSOther         | "setName" in response, "hidden: true" or not primary, secondary, nor arbiter.                            |
| RSGhost         | "isreplicaset: true" in response.                                                                        |
| LoadBalanced    | "loadBalanced=true" in URI.                                                                              |

A server can transition from any state to any other. For example, an administrator could shut down a secondary and bring
up a mongos in its place.

##### RSGhost and RSOther

The client MUST monitor replica set members even when they cannot be queried. These members are in state RSGhost or
RSOther.

**RSGhost** members occur in at least three situations:

- briefly during server startup,
- in an uninitialized replica set,
- or when the server is shunned (removed from the replica set config).

An RSGhost server has no hosts list nor setName. Therefore the client MUST NOT attempt to use its hosts list nor check
its setName (see [JAVA-1161](https://jira.mongodb.org/browse/JAVA-1161) or
[CSHARP-671](https://jira.mongodb.org/browse/CSHARP-671).) However, the client MUST keep the RSGhost member in its
TopologyDescription, in case the client's only hope for staying connected to the replica set is that this member will
transition to a more useful state.

For simplicity, this is the rule: any server is an RSGhost that reports "isreplicaset: true".

Non-ghost replica set members have reported their setNames since MongoDB 1.6.2. See
[only support replica set members running MongoDB 1.6.2 or later](#only-support-replica-set-members-running-mongodb-162-or-later).

> [!NOTE]
> The Java driver does not have a separate state for RSGhost; it is an RSOther server with no hosts list.

**RSOther** servers may be hidden, starting up, or recovering. They cannot be queried, but their hosts lists are useful
for discovering the current replica set configuration.

If a [hidden member](https://www.mongodb.com/docs/manual/core/replica-set-hidden-member/) is provided as a seed, the
client can use it to find the primary. Since the hidden member does not appear in the primary's host list, it will be
removed once the primary is checked.

#### error

If the client experiences any error when checking a server, it stores error information in the ServerDescription's error
field. The message contained in this field MUST contain the substrings detailed in the table below when the
ServerDescription is changed to Unknown in the circumstances outlined.

| circumstance                                               | error substring                                                                                                |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| RSPrimary with a stale electionId/setVersion is discovered | `'primary marked stale due to electionId/setVersion mismatch, <stale tuple> is stale compared to <max tuple>'` |
| New primary is elected/discovered                          | `'primary marked stale due to discovery of newer primary'`                                                     |

#### roundTripTime

Drivers MUST record the server's [round trip time](#round-trip-time) (RTT) after each successful call to hello or legacy
hello. The Server Selection Spec describes how RTT is averaged and how it is used in server selection. Drivers MUST also
record the server's minimum RTT per [Server Monitoring (Measuring RTT)](server-monitoring.md#measuring-rtt).

If a hello or legacy hello call fails, the RTT is not updated. Furthermore, while a server's type is Unknown its RTT is
null, and if it changes from a known type to Unknown its RTT is set to null. However, if it changes from one known type
to another (e.g. from RSPrimary to RSSecondary) its RTT is updated normally, not set to null nor restarted from scratch.

#### lastWriteDate and opTime

The hello or legacy hello response of a replica set member running MongoDB 3.4 and later contains a `lastWrite`
subdocument with fields `lastWriteDate` and `opTime` ([SERVER-8858](https://jira.mongodb.org/browse/SERVER-8858)). If
these fields are available, parse them from the hello or legacy hello response, otherwise set them to null.

Clients MUST NOT attempt to compensate for the network latency between when the server generated its hello or legacy
hello response and when the client records `lastUpdateTime`.

#### lastUpdateTime

Clients SHOULD set lastUpdateTime with a monotonic clock.

#### Hostnames are normalized to lower-case

The same as with seeds provided in the initial configuration, all hostnames in the hello or legacy hello response's
"me", "hosts", "passives", and "arbiters" entries MUST be lower-cased.

This prevents unnecessary work rediscovering a server if a seed "A" is provided and the server responds that "a" is in
the replica set.

[RFC 4343](http://tools.ietf.org/html/rfc4343):

> Domain Name System (DNS) names are "case insensitive".

#### logicalSessionTimeoutMinutes

MongoDB 3.6 and later include a `logicalSessionTimeoutMinutes` field if logical sessions are enabled in the deployment.
Clients MUST check for this field and set the ServerDescription's logicalSessionTimeoutMinutes field to this value, or
to null otherwise.

#### topologyVersion

MongoDB 4.4 and later include a `topologyVersion` field in all hello or legacy hello and
[State Change Error](#state-change-error) responses. Clients MUST check for this field and set the ServerDescription's
topologyVersion field to this value, if present. The topologyVersion helps the client and server determine the relative
freshness of topology information in concurrent messages. (See
[What is the purpose of topologyVersion?](#what-is-the-purpose-of-topologyversion))

The topologyVersion is a subdocument with two fields, "processId" and "counter":

```typescript
{
    topologyVersion: {processId: <ObjectId>, counter: <int64>},
    ( ... other fields ...)
}
```

##### topologyVersion Comparison

To compare a topologyVersion from a hello or legacy hello or State Change Error response to the current
ServerDescription's topologyVersion:

1. If the response topologyVersion is unset or the ServerDescription's topologyVersion is null, the client MUST assume
    the response is more recent.
2. If the response's topologyVersion.processId is not equal to the ServerDescription's, the client MUST assume the
    response is more recent.
3. If the response's topologyVersion.processId is equal to the ServerDescription's, the client MUST use the counter
    field to determine which topologyVersion is more recent.

See [Replacing the TopologyDescription](#replacing-the-topologydescription) for an example implementation of
topologyVersion comparison.

#### serviceId

MongoDB 5.0 and later, as well as any mongos-like service, include a `serviceId` field when the service is configured
behind a load balancer.

#### Other ServerDescription fields

Other required fields defined in the [ServerDescription](#serverdescription) data structure are parsed from the hello or
legacy hello response in the obvious way.

#### Server Description Equality

For the purpose of determining whether to publish SDAM events, two server descriptions having the same address MUST be
considered equal if and only if the values of [ServerDescription](#serverdescription) fields marked (=) are respectively
equal.

This specification does not prescribe how to compare server descriptions with different addresses for equality.

### Updating the TopologyDescription

Each time the client checks a server, it processes the outcome (successful or not) to create a
[ServerDescription](#serverdescription), and then it processes the ServerDescription to update its
[TopologyDescription](#topologydescription).

The TopologyDescription's [TopologyType](#topologytype) influences how the ServerDescription is processed. The following
subsection specifies how the client updates its TopologyDescription when the TopologyType is Single. The next subsection
treats the other types.

#### TopologyType Single

The TopologyDescription's type was initialized as Single and remains Single forever. There is always one
ServerDescription in TopologyDescription.servers.

Whenever the client checks a server (successfully or not), and regardless of whether the new server description is equal
to the previous server description as defined in [Server Description Equality](#server-description-equality), the
ServerDescription in TopologyDescription.servers MUST be replaced with the new ServerDescription.

<span id="checking-wire-protocol-compatibility"></span>

##### Checking wire protocol compatibility

A ServerDescription which is not Unknown is incompatible if:

- `minWireVersion` > `clientMaxWireVersion`, or
- `maxWireVersion` < `clientMinWireVersion`

If any ServerDescription is incompatible, the client MUST set the TopologyDescription's "compatible" field to false and
fill out the TopologyDescription's "compatibilityError" field like so:

- if `ServerDescription.minWireVersion` > `clientMaxWireVersion`:

    "Server at `host`:`port` requires wire version `minWireVersion`, but this version of `driverName` only supports up to
    `clientMaxWireVersion`."

- if `ServerDescription.maxWireVersion` < `clientMinWireVersion`:

    "Server at `host`:`port` reports wire version `maxWireVersion`, but this version of `driverName` requires at least
    `clientMinWireVersion` (MongoDB `mongoVersion`)."

Replace `mongoVersion` with the appropriate MongoDB minor version, for example if `clientMinWireVersion` is 2 and it
connects to MongoDB 2.4, format the error like:

> "Server at example.com:27017 reports wire version 0, but this version of My Driver requires at least 2 (MongoDB 2.6)."

In this second case, the exact required MongoDB version is known and can be named in the error message, whereas in the
first case the implementer does not know which MongoDB versions will be compatible or incompatible in the future.

##### Verifying setName with TopologyType Single

A client MAY allow the user to supply a setName with an initial TopologyType of Single. In this case, if the
ServerDescription's setName is null or wrong, the ServerDescription MUST be replaced with a default ServerDescription of
type Unknown.

#### TopologyType LoadBalanced

See the [Load Balancer Specification](../load-balancers/load-balancers.md#server-discovery-logging-and-monitoring) for
details.

#### Other TopologyTypes

If the TopologyType is **not** Single, the topology can contain zero or more servers. The state of topology containing
zero servers is terminal (because servers can only be added if they are reported by a server already in the topology). A
client SHOULD emit a warning if it is constructed with no seeds in the initial seed list. A client SHOULD emit a warning
when, in the process of updating its topology description, it removes the last server from the topology.

Whenever a client completes a hello or legacy hello call, it creates a new ServerDescription with the proper
[ServerType](#servertype). It replaces the server's previous description in TopologyDescription.servers with the new
one.

Apply the logic for [checking wire protocol compatibility](#checking-wire-protocol-compatibility) to each
ServerDescription in the topology. If any server's wire protocol version range does not overlap with the client's, the
client updates the "compatible" and "compatibilityError" fields as described above for TopologyType Single. Otherwise
"compatible" is set to true.

It is possible for a multi-threaded client to receive a hello or legacy hello outcome from a server after the server has
been removed from the TopologyDescription. For example, a monitor begins checking a server "A", then a different monitor
receives a response from the primary claiming that "A" has been removed from the replica set, so the client removes "A"
from the TopologyDescription. Then, the check of server "A" completes.

In all cases, the client MUST ignore hello or legacy hello outcomes from servers that are not in the
TopologyDescription.

The following subsections explain in detail what actions the client takes after replacing the ServerDescription.

##### TopologyType table

The new ServerDescription's type is the vertical axis, and the current TopologyType is the horizontal. Where a
ServerType and a TopologyType intersect, the table shows what action the client takes.

"no-op" means, do nothing **after** replacing the server's old description with the new one.

|                        | TopologyType Unknown                                                                            | TopologyType Sharded | TopologyType ReplicaSetNoPrimary                                                            | TopologyType ReplicaSetWithPrimary                              |
| ---------------------- | ----------------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| ServerType Unknown     | no-op                                                                                           | no-op                | no-op                                                                                       | [checkIfHasPrimary](#checkifhasprimary)                         |
| ServerType Standalone  | [updateUnknownWithStandalone](#updateunknownwithstandalone)                                     | [remove](#remove)    | [remove](#remove)                                                                           | [remove](#remove) and [checkIfHasPrimary](#checkifhasprimary)   |
| ServerType Mongos      | Set topology type to Sharded                                                                    | no-op                | [remove](#remove)                                                                           | [remove](#remove) and [checkIfHasPrimary](#checkifhasprimary)   |
| ServerType RSPrimary   | Set topology type to ReplicaSetWithPrimary then [updateRSFromPrimary](#updatersfromprimary)     | [remove](#remove)    | Set topology type to ReplicaSetWithPrimary then [updateRSFromPrimary](#updatersfromprimary) | [updateRSFromPrimary](#updatersfromprimary)                     |
| ServerType RSSecondary | Set topology type to ReplicaSetNoPrimary then [updateRSWithoutPrimary](#updaterswithoutprimary) | [remove](#remove)    | [updateRSWithoutPrimary](#updaterswithoutprimary)                                           | [updateRSWithPrimaryFromMember](#updaterswithprimaryfrommember) |
| ServerType RSArbiter   | Set topology type to ReplicaSetNoPrimary then [updateRSWithoutPrimary](#updaterswithoutprimary) | [remove](#remove)    | [updateRSWithoutPrimary](#updaterswithoutprimary)                                           | [updateRSWithPrimaryFromMember](#updaterswithprimaryfrommember) |
| ServerType RSOther     | Set topology type to ReplicaSetNoPrimary then [updateRSWithoutPrimary](#updaterswithoutprimary) | [remove](#remove)    | [updateRSWithoutPrimary](#updaterswithoutprimary)                                           | [updateRSWithPrimaryFromMember](#updaterswithprimaryfrommember) |
| ServerType RSGhost     | no-op[^2]                                                                                       | [remove](#remove)    | no-op                                                                                       | [checkIfHasPrimary](#checkifhasprimary)                         |

##### TopologyType explanations

This subsection complements the [TopologyType table](#topologytype-table) with prose explanations of the TopologyTypes
(besides Single and LoadBalanced).

**TopologyType Unknown**

A starting state.

**Actions**:

- If the incoming ServerType is Unknown (that is, the hello or legacy hello call failed), keep the server in
    TopologyDescription.servers. The TopologyType remains Unknown.
- The
    [TopologyType remains Unknown when an RSGhost is discovered](#topologytype-remains-unknown-when-an-rsghost-is-discovered),
    too.
- If the type is Standalone, run [updateUnknownWithStandalone](#updateunknownwithstandalone).
- If the type is Mongos, set the TopologyType to Sharded.
- If the type is RSPrimary, record its setName and call [updateRSFromPrimary](#updatersfromprimary).
- If the type is RSSecondary, RSArbiter or RSOther, record its setName, set the TopologyType to ReplicaSetNoPrimary, and
    call [updateRSWithoutPrimary](#updaterswithoutprimary).

**TopologyType Sharded**

A steady state. Connected to one or more mongoses.

**Actions**:

- If the server is Unknown or Mongos, keep it.
- Remove others.

**TopologyType ReplicaSetNoPrimary**

A starting state. The topology is definitely a replica set, but no primary is known.

**Actions**:

- Keep Unknown servers.
- Keep RSGhost servers: they are members of some replica set, perhaps this one, and may recover. (See
    [RSGhost and RSOther](#rsghost-and-rsother).)
- Remove any Standalones or Mongoses.
- If the type is RSPrimary call [updateRSFromPrimary](#updatersfromprimary).
- If the type is RSSecondary, RSArbiter or RSOther, run [updateRSWithoutPrimary](#updaterswithoutprimary).

**TopologyType ReplicaSetWithPrimary**

A steady state. The primary is known.

**Actions**:

- If the server type is Unknown, keep it, and run [checkIfHasPrimary](#checkifhasprimary).
- Keep RSGhost servers: they are members of some replica set, perhaps this one, and may recover. (See
    [RSGhost and RSOther](#rsghost-and-rsother).) Run [checkIfHasPrimary](#checkifhasprimary).
- Remove any Standalones or Mongoses and run [checkIfHasPrimary](#checkifhasprimary).
- If the type is RSPrimary run [updateRSFromPrimary](#updatersfromprimary).
- If the type is RSSecondary, RSArbiter or RSOther, run [updateRSWithPrimaryFromMember](#updaterswithprimaryfrommember).

#### Actions

##### updateUnknownWithStandalone

This subroutine is executed with the ServerDescription from Standalone when the TopologyType is Unknown:

```python
if description.address not in topologyDescription.servers:
    return

if settings.seeds has one seed:
    topologyDescription.type = Single
else:
    remove this server from topologyDescription and stop monitoring it
```

See
[TopologyType remains Unknown when one of the seeds is a Standalone](#topologytype-remains-unknown-when-one-of-the-seeds-is-a-standalone).

<span id="updateRSWithoutPrimary"></span>

##### updateRSWithoutPrimary

This subroutine is executed with the ServerDescription from an RSSecondary, RSArbiter, or RSOther when the TopologyType
is ReplicaSetNoPrimary:

```python
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
```

Unlike [updateRSFromPrimary](#updatersfromprimary), this subroutine does **not** remove any servers from the
TopologyDescription based on the list of servers in the "hosts" field of the hello or legacy hello response. The only
server that might be removed is the server itself that the hello or legacy hello response is from.

The special handling of description.primary ensures that a single-threaded client [scans](#scan) the possible primary
before other members.

See [replica set monitoring with and without a primary](#replica-set-monitoring-with-and-without-a-primary).

##### updateRSWithPrimaryFromMember

This subroutine is executed with the ServerDescription from an RSSecondary, RSArbiter, or RSOther when the TopologyType
is ReplicaSetWithPrimary:

```python
if description.address not in topologyDescription.servers:
    # While we were checking this server, another thread heard from the
    # primary that this server is not in the replica set.
    return

# SetName is never null here.
if topologyDescription.setName != description.setName:
    remove this server from topologyDescription and stop monitoring it
    checkIfHasPrimary()
    return

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
```

The special handling of description.primary ensures that a single-threaded client [scans](#scan) the possible primary
before other members.

<span id="updateRSFromPrimary"></span>

##### updateRSFromPrimary

This subroutine is executed with a ServerDescription of type RSPrimary:

```python
if serverDescription.address not in topologyDescription.servers:
    return

if topologyDescription.setName is null:
    topologyDescription.setName = serverDescription.setName

else if topologyDescription.setName != serverDescription.setName:
    # We found a primary but it doesn't have the setName
    # provided by the user or previously discovered.
    remove this server from topologyDescription and stop monitoring it
    checkIfHasPrimary()
    return

# Election ids are ObjectIds, see
# see "Using electionId and setVersion to detect stale primaries"
# for comparison rules.

if serverDescription.maxWireVersion >= 17:  # MongoDB 6.0+
    # Null values for both electionId and setVersion are always considered less than
    if serverDescription.electionId > topologyDescription.maxElectionId or (
        serverDescription.electionId == topologyDescription.maxElectionId
        and serverDescription.setVersion >= topologyDescription.maxSetVersion
    ):
        topologyDescription.maxElectionId = serverDescription.electionId
        topologyDescription.maxSetVersion = serverDescription.setVersion
    else:
        # Stale primary.
        # The error field MUST include the substring "primary marked stale due to electionId/setVersion mismatch"
         replace serverDescription with a default ServerDescription of type "Unknown"
        checkIfHasPrimary()
        return
else:
    # Maintain old comparison rules, namely setVersion is checked before electionId
    if serverDescription.setVersion is not null and serverDescription.electionId is not null:
        if (
            topologyDescription.maxSetVersion is not null
            and topologyDescription.maxElectionId is not null
            and (
                topologyDescription.maxSetVersion > serverDescription.setVersion
                or (
                    topologyDescription.maxSetVersion == serverDescription.setVersion
                    and topologyDescription.maxElectionId > serverDescription.electionId
                )
            )
        ):
            # Stale primary.
            # The error field MUST include the substring "primary marked stale due to electionId/setVersion mismatch"
            replace serverDescription with a default ServerDescription of type "Unknown" 
            checkIfHasPrimary()
            return

        topologyDescription.maxElectionId = serverDescription.electionId

    if serverDescription.setVersion is not null and (
        topologyDescription.maxSetVersion is null
        or serverDescription.setVersion > topologyDescription.maxSetVersion
    ):
        topologyDescription.maxSetVersion = serverDescription.setVersion


for each server in topologyDescription.servers:
    if server.address != serverDescription.address:
        if server.type is RSPrimary:
            # See note below about invalidating an old primary.
            # the error field MUST include the substring "primary marked stale due to discovery of newer primary"
            replace the server with a default ServerDescription of type "Unknown"

for each address in serverDescription's "hosts", "passives", and "arbiters":
    if address is not in topologyDescription.servers:
        add new default ServerDescription of type "Unknown"
        begin monitoring the new server

for each server in topologyDescription.servers:
    if server.address not in serverDescription's "hosts", "passives", or "arbiters":
        remove the server and stop monitoring it

checkIfHasPrimary()
```

A note on invalidating the old primary: when a new primary is discovered, the client finds the previous primary (there
should be none or one) and replaces its description with a default ServerDescription of type "Unknown". Additionally,
the `error` field of the new `ServerDescription` object MUST include a descriptive error explaining that it was
invalidated because the primary was determined to be stale. A multi-threaded client MUST
[request an immediate check](server-monitoring.md#requesting-an-immediate-check) for that server as soon as possible.

If the old primary server version is 4.0 or earlier, the client MUST clear its connection pool for the old primary, too:
the connections are all bad because the old primary has closed its sockets. If the old primary server version is 4.2 or
newer, the client MUST NOT clear its connection pool for the old primary.

See [replica set monitoring with and without a primary](#replica-set-monitoring-with-and-without-a-primary).

If the server is primary with an obsolete electionId or setVersion, it is likely a stale primary that is going to step
down. Mark it Unknown and let periodic monitoring detect when it becomes secondary. See
[using electionId and setVersion to detect stale primaries](#using-electionid-and-setversion-to-detect-stale-primaries).
Drivers MAY additionally specify whether this was due to an electionId or setVersion mismatch as described in the
[ServerDescripion.error section](#error).

A note on checking "me": Unlike `updateRSWithPrimaryFromMember`, there is no need to remove the server if the address is
not equal to "me": since the server address will not be a member of either "hosts", "passives", or "arbiters", the
server will already have been removed.

##### checkIfHasPrimary

Set TopologyType to ReplicaSetWithPrimary if there is an RSPrimary in TopologyDescription.servers, otherwise set it to
ReplicaSetNoPrimary.

For example, if the TopologyType is ReplicaSetWithPrimary and the client is processing a new ServerDescription of type
Unknown, that could mean the primary just disconnected, so checkIfHasPrimary must run to check if the TopologyType
should become ReplicaSetNoPrimary.

Another example is if the client first reaches the primary via its external IP, but the response's host list includes
only internal IPs. In that case the client adds the primary's internal IP to the TopologyDescription and begins
monitoring it, and removes the external IP. Right after removing the external IP from the description, the TopologyType
MUST be ReplicaSetNoPrimary, since no primary is available at this moment.

##### remove

Remove the server from TopologyDescription.servers and stop monitoring it.

In multi-threaded clients, a monitor may be currently checking this server and may not immediately abort. Once the check
completes, this server's hello or legacy hello outcome MUST be ignored, and the monitor SHOULD halt.

#### Logical Session Timeout

Whenever a client updates the TopologyDescription from a hello or legacy hello response, it MUST set
TopologyDescription.logicalSessionTimeoutMinutes to the smallest logicalSessionTimeoutMinutes value among
ServerDescriptions of all data-bearing server types. If any have a null logicalSessionTimeoutMinutes, then
TopologyDescription.logicalSessionTimeoutMinutes MUST be set to null.

See the Driver Sessions Spec for the purpose of this value.

### Connection Pool Management

For drivers that support connection pools, after a server check is completed successfully, if the server is determined
to be [data-bearing](server-discovery-and-monitoring.md#data-bearing-server-type) or a
[direct connection](server-discovery-and-monitoring.md#general-requirements) to the server is requested, and does not
already have a connection pool, the driver MUST create the connection pool for the server. Additionally, if a driver
implements a CMAP compliant connection pool, the server's pool (even if it already existed) MUST be marked as "ready".
See the [Server Monitoring spec](server-monitoring.md) for more information.

Clearing the connection pool for a server MUST be synchronized with the update to the corresponding ServerDescription
(e.g. by holding the lock on the TopologyDescription when clearing the pool). This prevents a possible race between the
monitors and application threads. See
[Why synchronize clearing a server's pool with updating the topology?](#why-synchronize-clearing-a-servers-pool-with-updating-the-topology)
for more information.

### Error handling

#### Network error during server check

See error handling in the [Server Monitoring spec](server-monitoring.md).

#### Application errors

When processing a network or command error, clients MUST first check the error's generation number. If the error's
generation number is equal to the pool's generation number then error handling MUST continue according to
[Network error when reading or writing](#network-error-when-reading-or-writing) or
["not writable primary" and "node is recovering"](#not-writable-primary-and-node-is-recovering). Otherwise, the error is
considered stale and the client MUST NOT update any topology state. (See
[Why ignore errors based on CMAP's generation number?](#why-ignore-errors-based-on-cmaps-generation-number))

##### Error handling pseudocode

Application operations can fail in various places, for example:

- A network error, network timeout, or command error may occur while establishing a new connection. Establishing a
    connection includes the MongoDB handshake and completing authentication (if configured).
- A network error or network timeout may occur while reading or writing to an established connection.
- A command error may be returned from the server.
- A "writeConcernError" field may be included in the command response.

Depending on the context, these errors may update SDAM state by marking the server Unknown and may clear the server's
connection pool. Some errors also require other side effects, like cancelling a check or requesting an immediate check.
Drivers may use the following pseudocode to guide their implementation:

```python
def handleError(error):
    address = error.address
    topologyVersion = error.topologyVersion

    with client.lock:
        # Ignore stale errors based on generation and topologyVersion.
        if isStaleError(client.topologyDescription, error)
            return

        if isStateChangeError(error):
            # Don't mark server unknown in load balanced mode.
            if type != LoadBalanced
              # Mark the server Unknown
              unknown = new ServerDescription(type=Unknown, error=error, topologyVersion=topologyVersion)
              onServerDescriptionChanged(unknown, connection pool for server)
            if isShutdown(code) or (error was from <4.2):
              # the pools must only be cleared while the lock is held.
              if type == LoadBalanced:
                clear connection pool for serviceId
              else:
                clear connection pool for server
            if multi-threaded:
                request immediate check
            else:
                # Check right now if this is "not writable primary", since it might be a
                # useful secondary. If it's "node is recovering" leave it for the
                # next full scan.
                if isNotWritablePrimary(error):
                    check failing server
        elif isNetworkError(error) or (not error.completedHandshake):
            # Ignore errors that have a backpressure error label applied.
            if error.hasLabel("SystemOverloadedError"):
                continue
            if type != LoadBalanced
              # Mark the server Unknown
              unknown = new ServerDescription(type=Unknown, error=error)
              onServerDescriptionChanged(unknown, connection pool for server)
              clear connection pool for server
            else
              if serviceId
                clear connection pool for serviceId
            # Cancel inprogress check
            cancel monitor check

def isStaleError(topologyDescription, error):
    currentServer = topologyDescription.servers[server.address]
    currentGeneration = currentServer.pool.generation
    generation = get connection generation from error
    if generation < currentGeneration:
        # Stale generation number.
        return True

    currentTopologyVersion = currentServer.topologyVersion
    # True if the current error's topologyVersion is greater than the server's
    # We use >= instead of > because any state change should result in a new topologyVersion
    return compareTopologyVersion(currentTopologyVersion, error.commandResponse.get("topologyVersion")) >= 0
```

The following pseudocode checks a response for a "not master" or "node is recovering" error:

```python
recoveringCodes = [11600, 11602, 13436, 189, 91]
notWritablePrimaryCodes = [10107, 13435, 10058]
shutdownCodes = [11600, 91]

def isRecovering(message, code):
    if code:
        if code in recoveringCodes:
            return true
    else:
        # if no code, use the error message.
        return ("not master or secondary" in message
            or "node is recovering" in message)

def isNotWritablePrimary(message, code):
    if code:
        if code in notWritablePrimaryCodes:
          return true
    else:
      # if no code, use the error message.
      if isRecovering(message, None):
          return false
      return ("not master" in message)

def isShutdown(code):
    if code and code in shutdownCodes:
        return true
    return false

def isStateChangeError(error):
    message = error.errmsg
    code = error.code
    return isRecovering(message, code) or isNotWritablePrimary(message, code)

def parseGle(response):
    if "err" in response:
        handleError(CommandError(response, response["err"], response["code"]))

# Parse response to any command
def parseCommandResponse(response):
    if not response["ok"]:
        handleError(CommandError(response, response["errmsg"], response["code"]))
    else if response["writeConcernError"]:
        wce = response["writeConcernError"]
        handleError(WriteConcernError(response, wce["errmsg"], wce["code"]))

def parseQueryResponse(response):
    if the "QueryFailure" bit is set in response flags:
        handleError(CommandError(response, response["$err"], response["code"]))
```

The following sections describe the handling of different classes of application errors in detail including network
errors, network timeout errors, state change errors, and authentication errors.

##### Network error when reading or writing

To describe how the client responds to network errors during application operations, we distinguish three phases of
connecting to a server and using it for application operations:

- *Connection establishment and hello*: the client establishes a new connection to the server and completes an initial
    handshake by calling "hello" or legacy hello and reading the response
- *Authentication step*: the client optionally completes an authentication step
- *After the handshake completes*: the client uses the established connection for application operations

If there is a network error or timeout on the connection establishment or the hello, the client MUST NOT change the
server's description.

If there is an network error or timeout during the authentication step, the client MUST replace the server's
description with a default ServerDescription of type Unknown when the TopologyType is not LoadBalanced, and fill the
ServerDescription's error field with useful information.

If there is a network error or timeout on the connection before the handshake completes, and the TopologyType is
LoadBalanced, the client MUST keep the ServerDescription as LoadBalancer.

If there is a network timeout on the connection after the handshake completes, the client MUST NOT mark the server
Unknown. (A timeout may indicate a slow operation on the server, rather than an unavailable server.) If, however, there
is some other network error on the connection after the handshake completes, the client MUST replace the server's
description with a default ServerDescription of type Unknown if the TopologyType is not LoadBalanced, and fill the
ServerDescription's error field with useful information, the same as if an error or timeout occurred before the
handshake completed.

When the client marks a server Unknown due to a network error or timeout, the Unknown ServerDescription MUST be sent
through the same process for [updating the TopologyDescription](#updating-the-topologydescription) as if it had been a
failed hello or legacy hello outcome from a server check: for example, if the TopologyType is ReplicaSetWithPrimary and
a write to the RSPrimary server fails because of a network error (other than timeout), then a new ServerDescription is
created for the primary, with type Unknown, and the client executes the proper subroutine for an Unknown server when the
TopologyType is ReplicaSetWithPrimary: referring to the table above we see the subroutine is
[checkIfHasPrimary](#checkifhasprimary). The result is the TopologyType changes to ReplicaSetNoPrimary. See the test
scenario called "Network error writing to primary".

The client MUST close all idle sockets in its connection pool for the server: if one socket is bad, it is likely that
all are.

Clients MUST NOT request an immediate check of the server; since application sockets are used frequently, a network
error likely means the server has just become unavailable, so an immediate refresh is likely to get a network error,
too.

The server will not remain Unknown forever. It will be refreshed by the next periodic check or, if an application
operation needs the server sooner than that, then a re-check will be triggered by the server selection algorithm.

##### "not writable primary" and "node is recovering"

These errors are detected from a write command response or query response. Clients MUST check if the server error is a
"node is recovering" error or a "not writable primary" error.

If the response includes an error code, it MUST be solely used to determine if error is a "node is recovering" or "not
writable primary" error. Clients MUST match the errors by the numeric error code and not by the code name, as the code
name can change from one server version to the next.

The following error codes indicate a replica set member is temporarily unusable. These are called "node is recovering"
errors:

| Error Name                      | Error Code |
| ------------------------------- | ---------- |
| InterruptedAtShutdown           | 11600      |
| InterruptedDueToReplStateChange | 11602      |
| NotPrimaryOrSecondary           | 13436      |
| PrimarySteppedDown              | 189        |
| ShutdownInProgress              | 91         |

And the following error codes indicate a "not writable primary" error:

| Error Name              | Error Code |
| ----------------------- | ---------- |
| NotWritablePrimary      | 10107      |
| NotPrimaryNoSecondaryOk | 13435      |
| LegacyNotPrimary        | 10058      |

Clients MUST fallback to checking the error message if and only if the response does not include an error code. The
error is considered a "node is recovering" error if the substrings "node is recovering" or "not master or secondary" are
anywhere in the error message. Otherwise, if the substring "not master" is in the error message it is a "not writable
primary" error.

Additionally, if the response includes a write concern error, then the code and message of the write concern error MUST
be checked the same way a response error is checked above.

Errors contained within the writeErrors field MUST NOT be checked.

See the test scenario called "parsing 'not writable primary' and 'node is recovering' errors" for example response
documents.

When the client sees a "not writable primary" or "node is recovering" error and the error's
[topologyVersion](#topologyversion) is strictly greater than the current ServerDescription's topologyVersion it MUST
replace the server's description with a ServerDescription of type Unknown. Clients MUST store useful information in the
new ServerDescription's error field, including the error message from the server. Clients MUST store the error's
[topologyVersion](#topologyversion) field in the new ServerDescription if present. (See
[What is the purpose of topologyVersion?](#what-is-the-purpose-of-topologyversion))

Multi-threaded and asynchronous clients MUST
[request an immediate check](server-monitoring.md#requesting-an-immediate-check) of the server. Unlike in the "network
error" scenario above, a "not writable primary" or "node is recovering" error means the server is available but the
client is wrong about its type, thus an immediate re-check is likely to provide useful information.

For single-threaded clients, in the case of a "not writable primary" or "node is shutting down" error, the client MUST
mark the topology as "stale" so the next server selection scans all servers. For a "node is recovering" error,
single-threaded clients MUST NOT mark the topology as "stale". If a node is recovering for some time, an immediate scan
may not gain useful information.

The following subset of "node is recovering" errors is defined to be "node is shutting down" errors:

| Error Name            | Error Code |
| --------------------- | ---------- |
| InterruptedAtShutdown | 11600      |
| ShutdownInProgress    | 91         |

When handling a "not writable primary" or "node is recovering" error, the client MUST clear the server's connection pool
if and only if the error is "node is shutting down" or the error originated from server version < 4.2.

(See
[when does a client see "not writable primary" or "node is recovering"?](#when-does-a-client-see-not-writable-primary-or-node-is-recovering),
[use error messages to detect "not master" and "node is recovering"](#use-error-messages-to-detect-not-master-and-node-is-recovering),
and [other transient errors](#other-transient-errors) and
[Why close connections when a node is shutting down?](#why-close-connections-when-a-node-is-shutting-down).)

##### MongoDB Handshake errors

If the driver encounters errors that do not have the backpressure error label (`SystemOverloadedError`) applied when
establishing application connections (this includes the initial handshake and authentication), the driver MUST mark the
server Unknown and clear the server's connection pool if the TopologyType is not LoadBalanced. (See
[Why mark a server Unknown after an auth error?](#why-mark-a-server-unknown-after-an-auth-error))

### Monitoring SDAM events

The required driver specification for providing lifecycle hooks into server discovery and monitoring for applications to
consume can be found in the [SDAM Monitoring Specification](server-discovery-and-monitoring-logging-and-monitoring.md).

### Implementation notes

This section intends to provide generous guidance to driver authors. It is complementary to the reference
implementations. Words like "should", "may", and so on are used more casually here.

See also, the implementation notes in the [Server Monitoring spec](server-monitoring.md).

#### Multi-threaded or asynchronous server selection

While no suitable server is available for an operation,
[the client MUST re-check all servers every minHeartbeatFrequencyMS](#the-client-must-re-check-all-servers-every-minheartbeatfrequencyms).
(See [requesting an immediate check](server-monitoring.md#requesting-an-immediate-check).)

#### Single-threaded server selection

When a client that uses [single-threaded monitoring](server-monitoring.md#single-threaded-monitoring) fails to select a
suitable server for any operation, it [scans](#scan) the servers, then attempts selection again, to see if the scan
discovered suitable servers. It repeats, waiting [minHeartbeatFrequencyMS](#minheartbeatfrequencyms) after each scan,
until a timeout.

#### Documentation

##### Giant seed lists

Drivers' manuals should warn against huge seed lists, since it will slow initialization for single-threaded clients and
generate load for multi-threaded and asynchronous drivers.

#### Multi-threaded

#### Warning about the maxWireVersion from a monitor's hello or legacy hello response

Clients consult some fields from a server's hello or legacy hello response to decide how to communicate with it:

- maxWireVersion
- maxBsonObjectSize
- maxMessageSizeBytes
- maxWriteBatchSize

It is tempting to take these values from the last hello or legacy hello response a *monitor* received and store them in
the ServerDescription, but this is an anti-pattern. Multi-threaded and asynchronous clients that do so are prone to
several classes of race, for example:

- Setup: A MongoDB 3.0 Standalone with authentication enabled, the client must log in with SCRAM-SHA-1.
- The monitor thread discovers the server and stores maxWireVersion on the ServerDescription
- An application thread wants a socket, selects the Standalone, and is about to check the maxWireVersion on its
    ServerDescription when...
- The monitor thread gets disconnected from server and marks it Unknown, with default maxWireVersion of 0.
- The application thread resumes, creates a socket, and attempts to log in using MONGODB-CR, since maxWireVersion is
    *now* reported as 0.
- Authentication fails, the server requires SCRAM-SHA-1.

Better to call hello or legacy hello for each new socket, as required by the [Auth Spec](../auth/auth.md), and use the
hello or legacy hello response associated with that socket for maxWireVersion, maxBsonObjectSize, etc.: all the fields
required to correctly communicate with the server.

The hello or legacy hello responses received by monitors determine if the topology as a whole is compatible with the
driver, and which servers are suitable for selection. The monitors' responses should not be used to determine how to
format wire protocol messages to the servers.

##### Immutable data

Multi-threaded drivers should treat ServerDescriptions and TopologyDescriptions as immutable: the client replaces them,
rather than modifying them, in response to new information about the topology. Thus readers of these data structures can
simply acquire a reference to the current one and read it, without holding a lock that would block a monitor from making
further updates.

##### Process one hello or legacy hello outcome at a time

Although servers are checked in parallel, the function that actually creates the new TopologyDescription should be
synchronized so only one thread can run it at a time.

##### Replacing the TopologyDescription

Drivers may use the following pseudocode to guide their implementation. The client object has a lock and a condition
variable. It uses the lock to ensure that only one new ServerDescription is processed at a time, and it must be acquired
before invoking this function. Once the client has taken the lock it must do no I/O:

```python
def onServerDescriptionChanged(server, pool):
    # "server" is the new ServerDescription.
    # "pool" is the pool associated with the server

    if server.address not in client.topologyDescription.servers:
        # The server was once in the topologyDescription, otherwise
        # we wouldn't have been monitoring it, but an intervening
        # state-change removed it. E.g., we got a host list from
        # the primary that didn't include this server.
        return

    newTopologyDescription = client.topologyDescription.copy()

    # Ignore this update if the current topologyVersion is greater than
    # the new ServerDescription's.
    if isStaleServerDescription(td, server):
        return

    # Replace server's previous description.
    address = server.address
    newTopologyDescription.servers[address] = server

    # for drivers that implement CMAP, mark the connection pool as ready after a successful check
    if (server.type in (Mongos, RSPrimary, RSSecondary, Standalone, LoadBalanced))
            or (server.type != Unknown and newTopologyDescription.type == Single):
        pool.ready()

    take any additional actions,
    depending on the TopologyType and server...

    # Replace TopologyDescription and notify waiters.
    client.topologyDescription = newTopologyDescription
    client.condition.notifyAll()

def compareTopologyVersion(tv1, tv2):
    """Return -1 if tv1<tv2, 0 if tv1==tv2, 1 if tv1>tv2"""
    if tv1 is None or tv2 is None:
        # Assume greater.
        return -1
    pid1 = tv1['processId']
    pid2 = tv2['processId']
    if pid1 == pid2:
        counter1 = tv1['counter']
        counter2 = tv2['counter']
        if counter1 == counter2:
            return 0
        elif counter1 < counter2:
            return -1
        else:
            return 1
    else:
        # Assume greater.
        return -1

def isStaleServerDescription(topologyDescription, server):
    # True if the new ServerDescription's topologyVersion is greater than
    # or equal to the current server's.
    currentServer = topologyDescription.servers[server.address]
    currentTopologyVersion = currentServer.topologyVersion
    return compareTopologyVersion(currentTopologyVersion, server.topologyVersion) > 0
```

Notifying the condition unblocks threads waiting in the server-selection loop for a suitable server to be discovered.

> [!NOTE]
> The Java driver uses a CountDownLatch instead of a condition variable, and it atomically swaps the old and new
> CountDownLatches so it does not need "client.lock". It does, however, use a lock to ensure that only one thread runs
> onServerDescriptionChanged at a time.

## Rationale

### Clients do no I/O in the constructor

An alternative proposal was to distinguish between "discovery" and "monitoring". When discovery begins, the client
checks all its seeds, and discovery is complete once all servers have been checked, or after some maximum time.
Application operations cannot proceed until discovery is complete.

If the discovery phase is distinct, then single- and multi-threaded drivers could accomplish discovery in the
constructor, and throw an exception from the constructor if the deployment is unavailable or misconfigured. This is
consistent with prior behavior for many drivers. It will surprise some users that the constructor now succeeds, but all
operations fail.

Similarly for misconfigured seed lists: the client may discover a mix of mongoses and standalones, or find multiple
replica set names. It may surprise some users that the constructor succeeds and the client attempts to proceed with a
compatible subset of the deployment.

Nevertheless, this spec prohibits I/O in the constructor for the following reasons:

#### Common case

In the common case, the deployment is available and usable. This spec favors allowing operations to proceed as soon as
possible in the common case, at the cost of surprising behavior in uncommon cases.

#### Simplicity

It is simpler to omit a special discovery phase and treat all server [checks](#check) the same.

#### Consistency

Asynchronous clients cannot do I/O in a constructor, so it is consistent to prohibit I/O in other clients' constructors
as well.

#### Restarts

If clients can be constructed when the deployment is in some states but not in other states, it leads to an unfortunate
scenario: When the deployment is passing through a strange state, long-running clients may keep working, but any clients
restarted during this period fail.

Say an administrator changes one replica set member's setName. Clients that are already constructed remove the bad
member and stay usable, but if any client is restarted its constructor fails. Web servers that dynamically adjust their
process pools will show particularly undesirable behavior.

### heartbeatFrequencyMS defaults to 10 seconds or 60 seconds

Many drivers have different values. The time has come to standardize. Lacking a rigorous methodology for calculating the
best frequency, this spec chooses 10 seconds for multi-threaded or asynchronous drivers because some already use that
value.

Because scanning has a greater impact on the performance of single-threaded drivers, they MUST default to a longer
frequency (60 seconds).

An alternative is to check servers less and less frequently the longer they remain unchanged. This idea is rejected
because it is a goal of this spec to answer questions about monitoring such as,

- "How rapidly can I rotate a replica set to a new set of hosts?"
- "How soon after I add a secondary will query load be rebalanced?"
- "How soon will a client notice a change in round trip time, or tags?"

Having a constant monitoring frequency allows us to answer these questions simply and definitively. Losing the ability
to answer these questions is not worth any minor gain in efficiency from a more complex scheduling method.

### The client MUST re-check all servers every minHeartbeatFrequencyMS

While an application is waiting to do an operation for which there is no suitable server, a multi-threaded client MUST
re-check all servers very frequently. The slight cost is worthwhile in many scenarios. For example:

1. A client and a MongoDB server are started simultaneously.
2. The client checks the server before it begins listening, so the check fails.
3. The client waits in the server-selection loop for the topology to change.

In this state, the client should check the server very frequently, to give it ample opportunity to connect to the server
before timing out in server selection.

### No knobs

This spec does not intend to introduce any new configuration options unless absolutely necessary.

### The client MUST monitor arbiters

Mongos 2.6 does not monitor arbiters, but it costs little to do so, and in the rare case that all data members are moved
to new hosts in a short time, an arbiter may be the client's last hope to find the new replica set configuration.

### Only support replica set members running MongoDB 1.6.2 or later

Replica set members began reporting their setNames in that version. Supporting earlier versions is impractical.

### TopologyType remains Unknown when an RSGhost is discovered

If the TopologyType is Unknown and the client receives a hello or legacy hello response from
an[RSGhost](#rsghost-and-rsother), the TopologyType could be set to ReplicaSetNoPrimary. However, an RSGhost does not
report its setName, so the setName would still be unknown. This adds an additional state to the existing list:
"TopologyType ReplicaSetNoPrimary **and** no setName." The additional state adds substantial complexity without any
benefit, so this spec says clients MUST NOT change the TopologyType when an RSGhost is discovered.

### TopologyType remains Unknown when one of the seeds is a Standalone

If TopologyType is Unknown and there are multiple seeds, and one of them is discovered to be a standalone, it MUST be
removed. The TopologyType remains Unknown.

This rule supports the following common scenario:

1. Servers A and B are in a replica set.
2. A seed list with A and B is stored in a configuration file.
3. An administrator removes B from the set and brings it up as standalone for maintenance, without changing its port
    number.
4. The client is initialized with seeds A and B, TopologyType Unknown, and no setName.
5. The first hello or legacy hello response is from B, the standalone.

What if the client changed TopologyType to Single at this point? It would be unable to use the replica set; it would
have to remove A from the TopologyDescription once A's hello or legacy hello response comes.

The user's intent in this case is clearly to use the replica set, despite the outdated seed list. So this spec requires
clients to remove B from the TopologyDescription and keep the TopologyType as Unknown. Then when A's response arrives,
the client can set its TopologyType to ReplicaSet (with or without primary).

On the other hand, if there is only one seed and the seed is discovered to be a Standalone, the TopologyType MUST be set
to Single.

See the "member brought up as standalone" test scenario.

### Replica set monitoring with and without a primary

The client strives to fill the "servers" list only with servers that the **primary** said were members of the replica
set, when the client most recently contacted the primary.

The primary's view of the replica set is authoritative for two reasons:

1. The primary is never on the minority side of a network partition. During a partition it is the primary's list of
    servers the client should use.
2. Since reconfigs must be executed on the primary, the primary is the first to know of them. Reconfigs propagate to
    non-primaries eventually, but the client can receive hello or legacy hello responses from non-primaries that
    reflect any past state of the replica set. See the "Replica set discovery" test scenario.

If at any time the client believes there is no primary, the TopologyDescription's type is set to ReplicaSetNoPrimary.
While there is no known primary, the client MUST **add** servers from non-primaries' host lists, but it MUST NOT remove
servers from the TopologyDescription.

Eventually, when a primary is discovered, any hosts not in the primary's host list are removed.

### Using electionId and setVersion to detect stale primaries

Replica set members running MongoDB 2.6.10+ or 3.0+ include an integer called "setVersion" and an ObjectId called
"electionId" in their hello or legacy hello response. Starting with MongoDB 3.2.0, replica sets can use two different
replication protocol versions; electionIds from one protocol version must not be compared to electionIds from a
different protocol.

Because protocol version changes require replica set reconfiguration, clients use the tuple (electionId, setVersion) to
detect stale primaries. The tuple order comparison MUST be checked in the order of electionId followed by setVersion
since that order of comparison is guaranteed monotonicity.

The client remembers the greatest electionId and setVersion reported by a primary, and distrusts primaries from older
electionIds or from the same electionId but with lesser setVersion.

- It compares electionIds as 12-byte sequence i.e. memory comparison.
- It compares setVersions as integer values.

This prevents the client from oscillating between the old and new primary during a split-brain period, and helps provide
read-your-writes consistency with write concern "majority" and read preference "primary".

Prior to MongoDB server version 6.0 drivers had the logic opposite from the server side Replica Set Management logic by
ordering the tuple by `setVersion` before the `electionId`. In order to remain compatibility with backup systems, etc.
drivers continue to maintain the reversed logic when connected to a topology that reports a maxWireVersion less than
`17`. Server versions 6.0 and beyond MUST order the tuple by `electionId` then `setVersion`.

#### Requirements for read-your-writes consistency

Using (electionId, setVersion) only provides read-your-writes consistency if:

- The application uses the same MongoClient instance for write-concern "majority" writes and read-preference "primary"
    reads, and
- All members use MongoDB 2.6.10+, 3.0.0+ or 3.2.0+ with replication protocol 0 and clocks are *less* than 30 seconds
    skewed, or
- All members run MongoDB 3.2.0 and replication protocol 1 and clocks are *less* skewed than the election timeout
    (`electionTimeoutMillis`, which defaults to 10 seconds), or
- All members run MongoDB 3.2.1+ and replication protocol 1 (in which case clocks need not be synchronized).

#### Scenario

Consider the following situation:

1. Server A is primary.
2. A network partition isolates A from the set, but the client still sees it.
3. Server B is elected primary.
4. The client discovers that B is primary, does a write-concern "majority" write operation on B and receives
    acknowledgment.
5. The client receives a hello or legacy hello response from A, claiming A is still primary.
6. If the client trusts that A is primary, the next read-preference "primary" read sees stale data from A that may *not*
    include the write sent to B.

See [SERVER-17975](https://jira.mongodb.org/browse/SERVER-17975), "Stale reads with WriteConcern Majority and
ReadPreference Primary."

#### Detecting a stale primary

To prevent this scenario, the client uses electionId and setVersion to determine which primary was elected last. In this
case, it would not consider "A" a primary, nor read from it because server B will have a greater electionId but the same
setVersion.

#### Monotonicity

The electionId is an ObjectId compared bytewise in order.

(ie. 000000000000000000000001 > 000000000000000000000000, FF0000000000000000000000 > FE0000000000000000000000 etc.)

In some server versions, it is monotonic with respect to a particular servers' system clock, but is not globally
monotonic across a deployment. However, if inter-server clock skews are small, it can be treated as a monotonic value.

In MongoDB 2.6.10+ (which has [SERVER-13542](https://jira.mongodb.org/browse/SERVER-13542) backported), MongoDB 3.0.0+
or MongoDB 3.2+ (under replication protocol version 0), the electionId's leading bytes are a server timestamp. As long
as server clocks are skewed *less* than 30 seconds, electionIds can be reliably compared. (This is precise enough,
because in replication protocol version 0, servers are designed not to complete more than one election every 30 seconds.
Elections do not take 30 seconds--they are typically much faster than that--but there is a 30-second cooldown before the
next election can complete.)

Beginning in MongoDB 3.2.0, under replication protocol version 1, the electionId begins with a timestamp, but the
cooldown is shorter. As long as inter-server clock skew is *less* than the configured election timeout
(`electionTimeoutMillis`, which defaults to 10 seconds), then electionIds can be reliably compared.

Beginning in MongoDB 3.2.1, under replication protocol version 1, the electionId is guaranteed monotonic without relying
on any clock synchronization.

### Using me field to detect seed list members that do not match host names in the replica set configuration

Removal from the topology of seed list members where the "me" property does not match the address used to connect
prevents clients from being able to select a server, only to fail to re-select that server once the primary has
responded.

This scenario illustrates the problems that arise if this is NOT done:

- The client specifies a seed list of A, B, C
- Server A responds as a secondary with hosts D, E, F
- The client executes a query with read preference of secondary, and server A is selected
- Server B responds as a primary with hosts D, E, F. Servers A, B, C are removed, as they don't appear in the primary's
    hosts list
- The client iterates the cursor and attempts to execute a getMore against server A.
- Server selection fails because server A is no longer part of the topology.

With checking for "me" in place, it looks like this instead:

- The client specifies a seed list of A, B, C
- Server A responds as a secondary with hosts D, E, F, where "me" is D, and so the client adds D, E, F as type "Unknown"
    and starts monitoring them, but removes A from the topology.
- The client executes a query with read preference of secondary, and goes into the server selection loop
- Server D responds as a secondary where "me" is D
- Server selection completes by matching D
- The client iterates the cursor and attempts to execute a getMore against server D.
- Server selection completes by matching D.

### Ignore setVersion unless the server is primary

It was thought that if all replica set members report a setVersion, and a secondary's response has a higher setVersion
than any seen, that the secondary's host list could be considered as authoritative as the primary's. (See
[Replica set monitoring with and without a primary](#replica-set-monitoring-with-and-without-a-primary).)

This scenario illustrates the problem with setVersion:

- We have a replica set with servers A, B, and C.
- Server A is the primary, with setVersion 4.
- An administrator runs replSetReconfig on A, which increments its setVersion to 5.
- The client checks Server A and receives the new config.
- Server A crashes before any secondary receives the new config.
- Server B is elected primary. It has the old setVersion 4.
- The client ignores B's version of the config because its setVersion is not greater than 5.

The client may never correct its view of the topology.

Even worse:

- An administrator runs replSetReconfig on Server B, which increments its setVersion to 5.
- Server A restarts. This results in *two* versions of the config, both claiming to be version 5.

If the client trusted the setVersion in this scenario, it would trust whichever config it received first.

mongos 2.6 ignores setVersion and only trusts the primary. This spec requires all clients to ignore setVersion from
non-primaries.

### Use error messages to detect "not master" and "node is recovering"

When error codes are not available, error messages are checked for the substrings "not master" and "node is recovering".
This is because older server versions returned unstable error codes or no error codes in many circumstances.

### Other transient errors

There are other transient errors a server may return, e.g. retryable errors listed in the retryable writes spec. SDAM
does not consider these because they do not imply the connected server should be marked as "Unknown". For example, the
following errors may be returned from a mongos when it cannot route to a shard:

| Error Name      | Error Code |
| --------------- | ---------- |
| HostNotFound    | 7          |
| HostUnreachable | 6          |
| NetworkTimeout  | 89         |
| SocketException | 9001       |

When these are returned, the mongos should *not* be marked as "Unknown", since it is more likely an issue with the
shard.

### Why ignore errors based on CMAP's generation number?

Using CMAP's generation number solves the following race condition among application threads and the monitor during
error handling:

1. Two concurrent writes begin on application threads A and B.
2. The server restarts.
3. Thread A receives the first non-timeout network error, and the client marks the server Unknown, and clears the
    server's pool.
4. The client re-checks the server and marks it Primary.
5. Thread B receives the second non-timeout network error and the client marks the server Unknown again.

The core issue is that the client processes errors in arbitrary order and may overwrite fresh information about the
server's status with stale information. Using CMAP's generation number avoids the race condition because the duplicate
(or stale) network error can be identified (changes in **bold**):

1. Two concurrent writes begin on application threads A and B, **with generation 1**.
2. The server restarts.
3. Thread A receives the first non-timeout network error, and the client marks the server Unknown, and clears the
    server's pool. **The pool's generation is now 2.**
4. The client re-checks the server and marks it Primary.
5. Thread B receives the second non-timeout network error, **and the client ignores the error because the error
    originated from a connection with generation 1.**

### Why synchronize clearing a server's pool with updating the topology?

Doing so solves the following race condition among application threads and the monitor during error handling, similar to
the previous example:

1. A write begins on an application thread.
2. The server restarts.
3. The application thread receives a non-timeout network error.
4. The application thread acquires the lock on the TopologyDescription, marks the Server as Unknown, and releases the
    lock.
5. The monitor re-checks the server and marks it Primary and its pool as "ready".
6. Several other application threads enter the WaitQueue of the server's pool.
7. The application thread clears the server's pool, evicting all those new threads from the WaitQueue, causing them to
    return errors or to retry. Additionally, the pool is now "paused", but the server is considered the Primary,
    meaning future operations will be routed to the server and fail until the next heartbeat marks the pool as "ready"
    again.

If marking the server as Unknown and clearing its pool were synchronized, then the monitor marking the server as Primary
after its check would happen after the pool was cleared and thus avoid putting it an inconsistent state.

### What is the purpose of topologyVersion?

[topologyVersion](#topologyversion) solves the following race condition among application threads and the monitor when
handling State Change Errors:

1. Two concurrent writes begin on application threads A and B.
2. The primary steps down.
3. Thread A receives the first State Change Error, the client marks the server Unknown.
4. The client re-checks the server and marks it Secondary.
5. Thread B receives a delayed State Change Error and the client marks the server Unknown again.

The core issue is that the client processes errors in arbitrary order and may overwrite fresh information about the
server's status with stale information. Using topologyVersion avoids the race condition because the duplicate (or stale)
State Change Errors can be identified (changes in **bold**):

1. Two concurrent writes begin on application threads A and B.
    1. **The primary's ServerDescription.topologyVersion == tv1**
2. The primary steps down **and sets its topologyVersion to tv2**.
3. Thread A receives the first State Change Error **containing tv2**, the client marks the server Unknown (**with
    topologyVersion: tv2**).
4. The client re-checks the server and marks it Secondary (**with topologyVersion: tv2**).
5. Thread B receives a delayed State Change Error (**with topologyVersion: tv2**) **and the client ignores the error
    because the error's topologyVersion (tv2) is not greater than the current ServerDescription (tv2).**

### Why mark a server Unknown after an auth error?

The [Authentication spec](../auth/auth.md) requires that when authentication fails on a server, the driver MUST clear
the server's connection pool. Clearing the pool without marking the server Unknown would leave the pool in the "paused"
state while the server is still selectable. When auth fails due to invalid credentials, marking the server Unknown also
serves to rate limit new connections; future operations will need to wait for the server to be rediscovered.

Note that authentication may fail for a variety of reasons, for example:

- A network error, or network timeout error may occur.
- The server may return a [State Change Error](#state-change-error).
- The server may return a AuthenticationFailed command error (error code 18) indicating that the provided credentials
    are invalid.

Does this mean that authentication failures due to invalid credentials will manifest as server selection timeout errors?
No, authentication errors are still returned to the application immediately. A subsequent operation will block until the
server is rediscovered and immediately attempt authentication on a new connection.

### Clients use the hostnames listed in the replica set config, not the seed list

Very often users have DNS aliases they use in their [seed list](#seed-list) instead of the hostnames in the replica set
config. For example, the name "host_alias" might refer to a server also known as "host1", and the URI is:

```text
mongodb://host_alias/?replicaSet=rs
```

When the client connects to "host_alias", its hello or legacy hello response includes the list of hostnames from the
replica set config, which does not include the seed:

```javascript
{
   hosts: ["host1:27017", "host2:27017"],
   setName: "rs",
   ... other hello or legacy hello response fields ...
}
```

This spec requires clients to connect to the hostnames listed in the hello or legacy hello response. Furthermore, if the
response is from a primary, the client MUST remove all hostnames not listed. In this case, the client disconnects from
"host_alias" and tries "host1" and "host2". (See [updateRSFromPrimary](#updatersfromprimary).)

Thus, replica set members must be reachable from the client by the hostnames listed in the replica set config.

An alternative proposal is for clients to continue using the hostnames in the seed list. It could add new hosts from the
hello or legacy hello response, and where a host is known by two names, the client can deduplicate them using the "me"
field and prefer the name in the seed list.

This proposal was rejected because it does not support key features of replica sets: failover and zero-downtime
reconfiguration.

In our example, if "host1" and "host2" are not reachable from the client, the client continues to use "host_alias" only.
If that server goes down or is removed by a replica set reconfig, the client is suddenly unable to reach the replica set
at all: by allowing the client to use the alias, we have hidden the fact that the replica set's failover feature will
not work in a crisis or during a reconfig.

In conclusion, to support key features of replica sets, we require that the hostnames used in a replica set config are
reachable from the client.

## Backwards Compatibility

The Java driver 2.12.1 has a "heartbeatConnectRetryFrequency". Since this spec recommends the option be named
"minHeartbeatFrequencyMS", the Java driver must deprecate its old option and rename it minHeartbeatFrequency (for
consistency with its other options which also lack the "MS" suffix).

## Reference Implementation

- Java driver 3.x
- PyMongo 3.x
- Perl driver 1.0.0 (in progress)

## Future Work

MongoDB is likely to add some of the following features, which will require updates to this spec:

- Eventually consistent collections (SERVER-2956)
- Mongos discovery (SERVER-1834)
- Put individual databases into maintenance mode, instead of the whole server (SERVER-7826)
- Put setVersion in write-command responses (SERVER-13909)

## Questions and Answers

### When does a client see "not writable primary" or "node is recovering"?

These errors indicate one of these:

- A write was attempted on an unwritable server (arbiter, secondary, ghost, or recovering).
- A read was attempted on an unreadable server (arbiter, ghost, or recovering) or a read was attempted on a read-only
    server without the secondaryOk bit set.
- An operation was attempted on a server that is now shutting down.

In any case the error is a symptom that a ServerDescription's type no longer reflects reality.

On MongoDB 4.0 and earlier, a primary closes its connections when it steps down, so in many cases the next operation
causes a network error rather than "not writable primary". The driver can see a "not writable primary" error in the
following scenario:

1. The client discovers the primary.
2. The primary steps down.
3. Before the client checks the server and discovers the stepdown, the application attempts an operation.
4. The client's connection pool is empty, either because it has never attempted an operation on this server, or because
    all connections are in use by other threads.
5. The client creates a connection to the old primary.
6. The client attempts to write, or to read without the secondaryOk bit, and receives "not writable primary".

See ["not writable primary" and "node is recovering"](#not-writable-primary-and-node-is-recovering), and the test
scenario called "parsing 'not writable primary' and 'node is recovering' errors".

### Why close connections when a node is shutting down?

When a server shuts down, it will return one of the "node is shutting down" errors for each attempted operation and
eventually will close all connections. Keeping a connection to a server which is shutting down open would only produce
errors on this connection - such a connection will never be usable for any operations. In contrast, when a server 4.2 or
later returns "not writable primary" error the connection may be usable for other operations (such as secondary reads).

### What's the point of periodic monitoring?

Why not just wait until a "not writable primary" error or "node is recovering" error informs the client that its
TopologyDescription is wrong? Or wait until server selection fails to find a suitable server, and only scan all servers
then?

Periodic monitoring accomplishes three objectives:

- Update each server's type, tags, and [round trip time](#round-trip-time). Read preferences and the mongos selection
    algorithm require this information remains up to date.
- Discover new secondaries so that secondary reads are evenly spread.
- Detect incremental changes to the replica set configuration, so that the client remains connected to the set even
    while it is migrated to a completely new set of hosts.

If the application uses some servers very infrequently, monitoring can also proactively detect state changes (primary
stepdown, server becoming unavailable) that would otherwise cause future errors.

### Why is auto-discovery the preferred default?

Auto-discovery is most resilient and is therefore preferred.

### Why is it possible for maxSetVersion to go down?

`maxElectionId` and `maxSetVersion` are actually considered a pair of values Drivers MAY consider implementing
comparison in code as a tuple of the two to ensure their always updated together:

```typescript
// New tuple                        old tuple
{ electionId: 2, setVersion: 1 } > { electionId: 1, setVersion: 50 }
```

In this scenario, the maxSetVersion goes from 50 to 1, but the maxElectionId is raised to 2.

## Acknowledgments

Jeff Yemin's code for the Java driver 2.12, and his patient explanation thereof, is the major inspiration for this spec.
Mathias Stearn's beautiful design for replica set monitoring in mongos 2.6 contributed as well. Bernie Hackett gently
oversaw the specification process.

## Changelog

- 2015-12-17: Require clients to compare (setVersion, electionId) tuples.

- 2015-10-09: Specify electionID comparison method.

- 2015-06-16: Added cooldownMS.

- 2016-05-04: Added link to SDAM monitoring.

- 2016-07-18: Replace mentions of the "Read Preferences Spec" with "Server Selection Spec", and
    "secondaryAcceptableLatencyMS" with "localThresholdMS".

- 2016-07-21: Updated for Max Staleness support.

- 2016-08-04: Explain better why clients use the hostnames in RS config, not URI.

- 2016-08-31: Multi-threaded clients SHOULD use hello or legacy hello replies to update the topology when they handshake
    application connections.

- 2016-10-06: In updateRSWithoutPrimary the hello or legacy hello response's "primary" field should be used to update
    the topology description, even if address != me.

- 2016-10-29: Allow for idleWritePeriodMS to change someday.

- 2016-11-01: "Unknown" is no longer the default TopologyType, the default is now explicitly unspecified. Update
    instructions for setting the initial TopologyType when running the spec tests.

- 2016-11-21: Revert changes that would allow idleWritePeriodMS to change in the future.

- 2017-02-28: Update "network error when reading or writing": timeout while connecting does mark a server Unknown,
    unlike a timeout while reading or writing. Justify the different behaviors, and also remove obsolete reference to
    auto-retry.

- 2017-06-13: Move socketCheckIntervalMS to Server Selection Spec.

- 2017-08-01: Parse logicalSessionTimeoutMinutes from hello or legacy hello reply.

- 2017-08-11: Clearer specification of "incompatible" logic.

- 2017-09-01: Improved incompatibility error messages.

- 2018-03-28: Specify that monitoring must not do mechanism negotiation or authentication.

- 2019-05-29: Renamed InterruptedDueToStepDown to InterruptedDueToReplStateChange

- 2020-02-13: Drivers must run SDAM flow even when server description is equal to the last one.

- 2020-03-31: Add topologyVersion to ServerDescription. Add rules for ignoring stale application errors.

- 2020-05-07: Include error field in ServerDescription equality comparison.

- 2020-06-08: Clarify reasoning behind how SDAM determines if a topologyVersion is stale.

- 2020-12-17: Mark the pool for a server as "ready" after performing a successful check. Synchronize pool clearing with
    SDAM updates.

- 2021-01-17: Require clients to compare (electionId, setVersion) tuples.

- 2021-02-11: Errors encountered during auth are handled by SDAM. Auth errors mark the server Unknown and clear the
    pool.

- 2021-04-12: Adding in behaviour for load balancer mode.

- 2021-05-03: Require parsing "isWritablePrimary" field in responses.

- 2021-06-09: Connection pools must be created and eventually marked ready for any server if a direct connection is
    used.

- 2021-06-29: Updated to use modern terminology.

- 2022-01-19: Add iscryptd and 90th percentile RTT fields to ServerDescription.

- 2022-07-11: Convert integration tests to the unified format.

- 2022-09-30: Update `updateRSFromPrimary` to include logic before and after 6.0 servers

- 2022-10-05: Remove spec front matter, move footnote, and reformat changelog.

- 2022-11-17: Add minimum RTT tracking and remove 90th percentile RTT.

- 2024-01-17: Add section on expected client close behaviour

- 2024-05-08: Migrated from reStructuredText to Markdown.

- 2024-08-09: Updated wire versions in tests to 4.0+.

- 2024-08-16: Updated host b wire versions in `too_new` and `too_old` tests

- 2024-11-04: Make the description of `TopologyDescription.servers` consistent with the spec tests.

- 2024-11-11: Removed references to `getLastError`

- 2025-01-22: Add error messages when a new primary is elected or a primary with a stale electionId or setVersion is
    discovered.

- 2025-XX-YY: Add handling of backpressure error labels.

______________________________________________________________________

[^1]: "localThresholdMS" was called "secondaryAcceptableLatencyMS" in the Read Preferences Spec, before it was superseded
    by the Server Selection Spec.

[^2]: [TopologyType remains Unknown when an RSGhost is discovered](#topologytype-remains-unknown-when-an-rsghost-is-discovered).
