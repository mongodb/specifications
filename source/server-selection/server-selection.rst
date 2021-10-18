================
Server Selection
================

:Spec: 103
:Title: Server Selection
:Author: David Golden
:Lead: Bernie Hackett
:Advisors: \A. Jesse Jiryu Davis, Samantha Ritter, Robert Stam, Jeff Yemin
:Status: Accepted
:Type: Standards
:Last Modified: 2021-09-28
:Version: 1.13.4

.. contents::

Abstract
========

MongoDB deployments may offer more than one server that can service an
operation.  This specification describes how MongoDB drivers and mongos shall
select a server for either read or write operations.  It includes the definition
of a "read preference" document, configuration options, and algorithms for
selecting a server for different deployment topologies.

Meta
====

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119`_.

.. _RFC 2119: https://www.ietf.org/rfc/rfc2119.txt

Motivation for Change
=====================

This specification builds upon the prior "Driver Read Preference"
specification, which had a number of omissions, flaws
or other deficiencies:

#.  Mandating features that implied monotonicity for situations where
    monotonicity is not guaranteed

#.  Mandating features that are not supported by mongos

#.  Neglecting to specify a single, standard way to calculate average latency
    times

#.  Specifying complex command-helper rules

#.  Omitting rules for applying read preferences to a single server or to
    select among multiple mongos servers

#.  Omitting test cases for verification of spec compliance

This revision addresses these problems as well as improving structure and
specificity.

Additionally, it adds specifications for server selection more broadly:

*   Selection of a server for write operations

*   Server selection retry and timeout

Specification
=============

Scope and general requirements
------------------------------

This specification describes how MongoDB drivers and mongos select a server
for read and write operations, including commands, OP_QUERY, OP_INSERT, OP_UPDATE,
and OP_DELETE.  For read operations, it describes how drivers and mongos
shall interpret a read preference document.

This specification does not apply to OP_GET_MORE or OP_KILL_CURSORS
operations on cursors, which need to go to the same server that received an
OP_QUERY and returned a cursor ID.

For operations that are part of a sharded transaction this specification only
applies to the initial operation which starts the transaction on a mongos. This
specification does not apply to subsequent operations that are part of the
sharded transaction because all operations in a sharded transaction need to go
to the same mongos server.

Drivers and mongos MUST conform to the semantics of this document, but SHOULD
use language-appropriate data models or variable names.

This specification does not apply to commands issued for server monitoring or
authentication.

Terms
-----

**Available**
    Describes a server that is believed to be reachable over the network and
    able to respond to requests.  A server of type Unknown or PossiblePrimary
    is not available; other types are available.

**Client**
    Software that communicates with a MongoDB deployment.  This includes both
    drivers and mongos.

**Candidate**
   Describes servers in a deployment that enter the selection process,
   determined by the read preference ``mode`` parameter and the servers' type.
   Depending on the ``mode``, candidate servers might only include secondaries
   or might apply to all servers in the deployment.

**Deployment**
    One or more servers that collectively provide access to a single logical
    set of MongoDB databases.

**Command**
    An OP_QUERY operation targeting the '$cmd' collection namespace.

**Direct connection**
    A driver connection mode that sends all database operations to a single
    server without regard for type.

.. _eligible:

**Eligible**
    Describes candidate servers that also meet the criteria specified by the
    ``tag_sets`` and ``maxStalenessSeconds`` read preference parameters.

**Hedged Read**
    A server mode in which the same query is dispatched in parallel to multiple
    replica set members.

**Immediate topology check**
    For a multi-threaded or asynchronous client, this means waking all
    server monitors for an immediate check.  For a single-threaded client,
    this means a (blocking) scan of all servers.

**Latency window**
    When choosing between several suitable servers, the latency window is the
    range of acceptable RTTs from the shortest RTT to the shortest RTT plus the
    local threshold.  E.g. if the shortest RTT is 15ms and the local threshold
    is 200ms, then the latency window ranges from 15ms - 215ms.

**Local threshold**
    The maximum acceptable difference in milliseconds between the shortest RTT
    and the longest RTT of servers suitable to be selected.

**Mode**
    One of several enumerated values used as part of a read preference, defining
    which server types are candidates for reads and the semantics for choosing a
    specific one.

**Primary**
    Describes a server of type RSPrimary.

**Query**
    An OP_QUERY operation targeting a regular (non '$cmd') collection namespace.

**Read preference**
    The parameters describing which servers in a deployment can receive
    read operations, including ``mode``, ``tag_sets``, ``maxStalenessSeconds``,
    and ``hedge``.

**RS**
    Abbreviation for "replica set".

**RTT**
    Abbreviation for "round trip time".

**Round trip time**
    The time in milliseconds to execute a ``hello`` or legacy hello command and
    receive a response for a given server.  This spec differentiates between
    the RTT of a single ``hello`` or legacy hello command and a server's *average*
    RTT over several such commands.

**Secondary**
    A server of type RSSecondary.

**Staleness**
    A worst-case estimate of how far a secondary's replication lags behind the primary's last write.

**Server**
    A mongod or mongos process.

**Server selection**
    The process by which a server is chosen for a database operation out of all
    potential servers in a deployment.

**Server type**
    An enumerated type indicating whether a server is up or down, whether it is
    a mongod or mongos, whether it belongs to a replica set and, if so, what
    role it serves in the replica set.  See the `Server Discovery and Monitoring`_
    spec for more details.

**Suitable**
    Describes a server that meets all specified criteria for a read or write
    operation.

**Tag**
    A single key/value pair describing either (1) a user-specified
    characteristic of a replica set member or (2) a desired characteristic for
    the target of a read operation.  The key and value have no semantic meaning
    to the driver; they are arbitrary user choices.

**Tag set**
    A document of zero or more tags.  Each member of a replica set can be
    configured with zero or one tag set.

**Tag set list**
    A list of zero or more tag sets.  A read preference might have a tag set list
    used for selecting servers.

**Topology**
    The state of a deployment, including its type, which servers are
    members, and the server types of members.

**Topology type**
    An enumerated type indicating the semantics for monitoring servers and
    selecting servers for database operations.  See the `Server Discovery and
    Monitoring`_ spec for more details.

Assumptions
-----------

1.  Unless they explicitly override these priorities, we assume our users
    prefer their applications to be, in order:

    - Predictable: the behavior of the application should not change based on
      the deployment type, whether single mongod, replica set or sharded cluster.

    - Resilient: applications will adapt to topology changes, if possible,
      without raising errors or requiring manual reconfiguration.

    - Low-latency: all else being equal, faster responses to queries and writes
      are preferable.

2.  Clients know the state of a deployment based on some form of ongoing
    monitoring, following the rules defined in the `Server Discovery and
    Monitoring`_ spec.

    - They know which members are up or down, what their tag sets are, and
      their types.

    - They know average round trip times to each available member.

    - They detect reconfiguration and the addition or removal of members.

3.  The state of a deployment could change at any time, in between any network
    interaction.

    - Servers might or might not be reachable; they can change type at any
      time, whether due to partitions, elections, or misconfiguration.

    - Data rollbacks could occur at any time.

MongoClient Configuration
-------------------------

Selecting a server requires the following client-level configuration
options:

localThresholdMS
~~~~~~~~~~~~~~~~~~

This defines the size of the latency window for selecting among multiple
suitable servers. The default is 15 (milliseconds).  It MUST be configurable at
the client level.  It MUST NOT be configurable at the level of a database
object, collection object, or at the level of an individual query.

In the prior read preference specification, ``localThresholdMS`` was called
``secondaryAcceptableLatencyMS`` by drivers.  Drivers MUST support the new
name for consistency, but MAY continue to support the legacy name to avoid
a backward-breaking change.

mongos currently uses ``localThreshold`` and MAY continue to do so.

serverSelectionTimeoutMS
~~~~~~~~~~~~~~~~~~~~~~~~

This defines how long to block for server selection before throwing an
exception.  The default is 30,000 (milliseconds).  It MUST be configurable at
the client level.  It MUST NOT be configurable at the level of a database
object, collection object, or at the level of an individual query.

This default value was chosen to be sufficient for a typical server primary
election to complete.  As the server improves the speed of elections, this
number may be revised downward.

Users that can tolerate long delays for server selection when the topology
is in flux can set this higher.  Users that want to "fail fast" when the
topology is in flux can set this to a small number.

A serverSelectionTimeoutMS of zero MAY have special meaning in some drivers;
zero's meaning is not defined in this spec, but all drivers SHOULD document
the meaning of zero.

serverSelectionTryOnce
~~~~~~~~~~~~~~~~~~~~~~

Single-threaded drivers MUST provide a "serverSelectionTryOnce" mode,
in which the driver scans the topology exactly once after server selection fails,
then either selects a server or raises an error.

The serverSelectionTryOnce option MUST be true by default.
If it is set false, then the driver repeatedly searches for an appropriate server
for up to serverSelectionTimeoutMS milliseconds
(pausing `minHeartbeatFrequencyMS
<https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#minheartbeatfrequencyms>`_
between attempts, as required by the `Server Discovery and Monitoring`_
spec).

Users of single-threaded drivers MUST be able to control this mode in one or
both of these ways:

* In code, pass true or false for an option called serverSelectionTryOnce,
  spelled idiomatically for the language, to the MongoClient constructor.
* Include "serverSelectionTryOnce=true" or "serverSelectionTryOnce=false"
  in the URI. The URI option is spelled the same for all drivers.

Conflicting usages of the URI option and the symbol is an error.

Multi-threaded drivers MUST NOT provide this mode.
(See `single-threaded server selection implementation`_
and the rationale for a `"try once" mode`_.)

heartbeatFrequencyMS
~~~~~~~~~~~~~~~~~~~~

This controls when topology updates are scheduled.
See `heartbeatFrequencyMS`_ in the `Server Discovery and Monitoring`_ spec for details.

socketCheckIntervalMS
~~~~~~~~~~~~~~~~~~~~~

Only for single-threaded drivers.

The default socketCheckIntervalMS MUST be 5000 (5 seconds), and it MAY be
configurable. If socket has been idle for at least this long, it must be
checked before being used again.

See `checking an idle socket after socketCheckIntervalMS`_ and `what is the
purpose of socketCheckIntervalMS?`_.

idleWritePeriodMS
~~~~~~~~~~~~~~~~~

A constant, how often an idle primary writes a no-op to the oplog.
See `idleWritePeriodMS`_ in the `Max Staleness`_ spec for details.

smallestMaxStalenessSeconds
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A constant, 90 seconds. See "Smallest allowed value for maxStalenessSeconds"
in the Max Staleness Spec.

serverSelector
~~~~~~~~~~~~~~

Implementations MAY allow configuration of an optional, application-provided function
that augments the server selection rules.  The function takes as a parameter a list
of server descriptions representing the suitable servers for the read or write operation,
and returns a list of server descriptions that should still be considered suitable.

Read Preference
---------------

A read preference determines which servers are considered suitable for read
operations.  Read preferences are interpreted differently based on topology
type.  See topology-type-specific server selection rules for details.

When no servers are suitable, the selection might be retried or will eventually
fail following the rules described in the `Rules for server selection`_
section.

Components of a read preference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A read preference consists of a ``mode`` and optional
``tag_sets``, ``maxStalenessSeconds``, and ``hedge``.  The ``mode`` prioritizes
between primaries and secondaries to produce either a single suitable server or
a list of candidate servers.  If ``tag_sets`` and ``maxStalenessSeconds`` are
set, they determine which candidate servers are eligible for selection. If
``hedge`` is set, it configures how server hedged reads are used.

The default ``mode`` is 'primary'.  The default ``tag_sets``
is a list with an empty tag set: ``[{}]``. The default ``maxStalenessSeconds``
is -1 or null, depending on the language. The default ``hedge`` is unset.

Each is explained in greater detail below.

mode
````

For a deployment with topology type ReplicaSetWithPrimary or
ReplicaSetNoPrimary, the ``mode`` parameter controls whether primaries or
secondaries are deemed suitable.  Topology types Single and Sharded have
different selection criteria and are described elsewhere.

Clients MUST support these modes:

**primary**
    Only an available primary is suitable.

**secondary**
    All secondaries (and *only* secondaries) are candidates, but only
    `eligible`_ candidates (i.e. after applying ``tag_sets`` and ``maxStalenessSeconds``) are suitable.

**primaryPreferred**
    If a primary is available, only the primary is suitable.  Otherwise,
    all secondaries are candidates, but only eligible secondaries are suitable.

**secondaryPreferred**
    All secondaries are candidates. If there is at least one eligible
    secondary, only eligible secondaries are suitable.  Otherwise, when there
    are no eligible secondaries, the primary is suitable.

**nearest**
    The primary and all secondaries are candidates, but only eligible
    candidates are suitable.

*Note on other server types*: The `Server Discovery and Monitoring`_ spec defines
several other server types that could appear in a replica set.  Such types are never
candidates, eligible or suitable.

.. _algorithm for filtering by staleness:

maxStalenessSeconds
```````````````````

The maximum replication lag, in wall clock time, that a secondary can suffer
and still be eligible.

The default is no maximum staleness.

A ``maxStalenessSeconds`` of -1 MUST mean "no maximum". Drivers are also free to use
None, null, or other representations of "no value" to represent "no max staleness".

Drivers MUST raise an error if ``maxStalenessSeconds`` is a positive number
and the ``mode`` field is 'primary'.

A driver MUST raise an error
if the TopologyType is ReplicaSetWithPrimary or ReplicaSetNoPrimary
and either of these conditions is false::

  maxStalenessSeconds * 1000 >= heartbeatFrequencyMS + idleWritePeriodMS
  maxStalenessSeconds >= smallestMaxStalenessSeconds

``heartbeatFrequencyMS`` is defined in the `Server Discovery and Monitoring`_ spec,
and ``idleWritePeriodMS`` is defined to be 10 seconds in the `Max Staleness`_ spec.

See "Smallest allowed value for maxStalenessSeconds" in the Max Staleness Spec.

mongos MUST reject a read with ``maxStalenessSeconds`` provided and a ``mode`` of 'primary'.

mongos MUST reject a read with ``maxStalenessSeconds`` that is not a positive integer.

mongos MUST reject a read if ``maxStalenessSeconds`` is less than smallestMaxStalenessSeconds,
with error code 160 (SERVER-24421).

During server selection, drivers (but not mongos) with ``minWireVersion`` < 5
MUST raise an error if ``maxStalenessSeconds`` is a positive number, and any
available server's ``maxWireVersion`` is less than 5. [#]_

After filtering servers according to ``mode``, and before filtering with ``tag_sets``,
eligibility MUST be determined from ``maxStalenessSeconds`` as follows:

- If ``maxStalenessSeconds`` is not a positive number, then all servers are eligible.

- Otherwise, calculate staleness. Non-secondary servers (including Mongos
  servers) have zero staleness.
  If TopologyType is ReplicaSetWithPrimary,
  a secondary's staleness is calculated using its ServerDescription "S"
  and the primary's ServerDescription "P"::

    (S.lastUpdateTime - S.lastWriteDate) - (P.lastUpdateTime - P.lastWriteDate) + heartbeatFrequencyMS

  (All datetime units are in milliseconds.)

  If TopologyType is ReplicaSetNoPrimary,
  a secondary's staleness is calculated using its ServerDescription "S"
  and the ServerDescription of the secondary with the greatest lastWriteDate,
  "SMax"::

    SMax.lastWriteDate - S.lastWriteDate + heartbeatFrequencyMS

  Servers with staleness less than or equal to ``maxStalenessSeconds`` are eligible.

See the Max Staleness Spec for overall description and justification of this
feature.

.. _algorithm for filtering by tag_sets:

tag_sets
````````

The read preference ``tag_sets`` parameter is an ordered list of tag sets used
to restrict the eligibility of servers, such as for data center awareness.

Clients MUST raise an error if a non-empty tag set is given in ``tag_sets``
and the ``mode`` field is 'primary'.

A read preference tag set (``T``) matches a server tag set (``S``) –
or equivalently a server tag set (``S``) matches a read preference
tag set (``T``) — if ``T`` is a subset of ``S`` (i.e. ``T ⊆ S``).

For example, the read preference tag set "\{ dc: 'ny', rack: '2' \}" matches a
secondary server with tag set "\{ dc: 'ny', rack: '2', size: 'large' \}".

A tag set that is an empty document matches any server, because the empty
tag set is a subset of any tag set.  This means the default ``tag_sets``
parameter (``[{}]``) matches all servers.

Tag sets are applied after filtering servers by ``mode`` and ``maxStalenessSeconds``,
and before selecting one server within the latency window.

Eligibility MUST be determined from ``tag_sets`` as follows:

- If the ``tag_sets`` list is empty then all candidate servers are eligible
  servers.  (Note, the default of ``[{}]`` means an empty list probably won't
  often be seen, but if the client does not forbid an empty list, this rule
  MUST be implemented to handle that case.)

- If the ``tag_sets`` list is not empty, then tag sets are tried in order until
  a tag set matches at least one candidate server. All candidate servers
  matching that tag set are eligible servers.  Subsequent tag sets in the list
  are ignored.

- If the ``tag_sets`` list is not empty and no tag set in the list matches any
  candidate server, no servers are eligible servers.

hedge
`````

The read preference ``hedge`` parameter is a document that configures how the
server will perform hedged reads. It consists of the following keys:

- ``enabled``: Enables or disables hedging

Hedged reads are automatically enabled in MongoDB 4.4+ when using a ``nearest``
read preference. To explicitly enable hedging, the ``hedge`` document must be
passed. An empty document uses server defaults to control hedging, but the
``enabled`` key may be set to ``true`` or ``false`` to explicitly enable or
disable hedged reads.

Drivers MAY allow users to specify an empty hedge document if they accept
documents for read preference options. Any driver that exposes a builder API for
read preference objects MUST NOT allow an empty ``hedge`` document to be
constructed. In this case, the user MUST specify a value for ``enabled``, which
MUST default to ``true``. If the user does not call a ``hedge`` API method,
drivers MUST NOT send a ``hedge`` option to the server.


Read preference configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers MUST allow users to configure a default read preference on a
``MongoClient`` object.  Drivers MAY allow users to configure a default read
preference on a ``Database`` or ``Collection`` object.

A read preference MAY be specified as an object, document or individual
``mode``, ``tag_sets``, and ``maxStalenessSeconds`` parameters,
depending on what is most idiomatic for the language.

If more than one object has a default read preference, the default of the most
specific object takes precedence.  I.e. ``Collection`` is preferred over
``Database``, which is preferred over ``MongoClient``.

Drivers MAY allow users to set a read preference on queries on a per-operation
basis similar to how ``hint`` or ``batchSize`` are set. E.g., in Python::

    db.collection.find({}, read_preference=ReadPreference.SECONDARY)
    db.collection.find(
        {},
        read_preference=ReadPreference.NEAREST,
        tag_sets=[{'dc': 'ny'}],
        maxStalenessSeconds=120,
        hedge={'enabled': true})

Passing read preference to mongos and load balancers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a server of type Mongos or LoadBalancer is selected for a read operation, the read
preference is passed to the selected mongos through the use of ``$readPreference``
(as a `Global Command Argument`_ for OP_MSG or a query modifier for OP_QUERY) and, for
OP_QUERY only, the ``SecondaryOk`` wire protocol flag, according to the following rules.

For OP_MSG:
```````````

- For mode 'primary', drivers MUST NOT set ``$readPreference``

- For modes 'secondary', 'primaryPreferred', 'secondaryPreferred', and 'nearest', drivers
  MUST set ``$readPreference``

For OP_QUERY:
`````````````

If the read preference contains **only** a ``mode`` parameter and the mode is
'primary' or 'secondaryPreferred', for maximum backwards compatibility with
older versions of mongos, drivers MUST only use the value of the ``SecondaryOk``
wire protocol flag (i.e. set or unset) to indicate the desired read preference
and MUST NOT use a ``$readPreference`` query modifier.

Therefore, when sending queries to a mongos or load balancer, the following rules apply:

- For mode 'primary', drivers MUST NOT set the ``SecondaryOk`` wire protocol flag
  and MUST NOT use ``$readPreference``

- For mode 'secondary', drivers MUST set the ``SecondaryOk`` wire protocol flag
  and MUST also use ``$readPreference``

- For mode 'primaryPreferred', drivers MUST set the ``SecondaryOk`` wire protocol flag
  and MUST also use ``$readPreference``

- For mode 'secondaryPreferred', drivers MUST set the ``SecondaryOk`` wire protocol flag.
  If the read preference contains a non-empty ``tag_sets`` parameter,
  ``maxStalenessSeconds`` is a positive integer, or the ``hedge`` parameter is
  non-empty, drivers MUST use ``$readPreference``; otherwise, drivers MUST NOT
  use ``$readPreference``

- For mode 'nearest', drivers MUST set the ``SecondaryOk`` wire protocol flag
  and MUST also use ``$readPreference``

The ``$readPreference`` query modifier sends the read preference as part of the
query.  The read preference fields ``tag_sets`` is represented in a ``$readPreference``
document using the field name ``tags``.

When sending a read operation via OP_QUERY and any ``$`` modifier is used, including the ``$readPreference`` modifier,
the query MUST be provided using the ``$query`` modifier like so::

    {
        $query: {
            field1: 'query_value',
            field2: 'another_query_value'
        },
        $readPreference: {
            mode: 'secondary',
            tags: [ { 'dc': 'ny' } ],
            maxStalenessSeconds: 120,
            hedge: { enabled: true }
        }
    }

Document structure
``````````````````

A valid ``$readPreference`` document for mongos or load balancer has the following requirements:

1.  The ``mode`` field MUST be present exactly once with the mode represented
    in camel case:

    - 'primary'
    - 'secondary'
    - 'primaryPreferred'
    - 'secondaryPreferred'
    - 'nearest'

2.  If the ``mode`` field is "primary", the ``tags``, ``maxStalenessSeconds``,
    and ``hedge`` fields MUST be absent.

    Otherwise, for other ``mode`` values, the ``tags`` field MUST either be
    absent or be present exactly once and have an array value containing at
    least one document. It MUST contain only documents, no other type.

    The ``maxStalenessSeconds`` field MUST be either be absent or be present
    exactly once with an integer value.

    The ``hedge`` field MUST be either absent or be a document.

Mongos or service receiving a query with ``$readPreference`` SHOULD validate the
``mode``, ``tags``, ``maxStalenessSeconds``, and ``hedge`` fields according to
rules 1 and 2 above, but SHOULD ignore unrecognized fields for
forward-compatibility rather than throwing an error.

Use of read preferences with commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because some commands are used for writes, deployment-changes or other
state-changing side-effects, the use of read preference by a driver depends on
the command and how it is invoked:

1.  Write commands: ``insert``, ``update``, ``delete``, ``findAndModify``

    Write commands are considered write operations and MUST follow the
    corresponding `Rules for server selection`_ for each topology type.

2.  Generic command method: typically ``command`` or ``runCommand``

    The generic command method MUST act as a read operation for the purposes of
    server selection.

    The generic command method has a default read preference of ``mode``
    'primary'.  The generic command method MUST ignore any default read
    preference from client, database or collection configuration.  The generic
    command method SHOULD allow an optional read preference argument.

    If an explicit read preference argument is provided as part of the generic
    command method call, it MUST be used for server selection, regardless of
    the name of the command. It is up to the user to use an appropriate read
    preference, e.g.  not calling ``renameCollection`` with a ``mode`` of
    'secondary'.

    N.B.: "used for server selection" does not supercede rules for server
    selection on "Standalone" topologies, which ignore any requested read
    preference.

3.  Command-specific helper: methods that wrap database commands, like
    ``count``, ``distinct``, ``listCollections`` or ``renameCollection``.

    Command-specific helpers MUST act as read operations for the purposes of
    server selection, with read preference rules defined by the following three
    categories of commands:

    - "must-use-primary":  these commands have state-modifying effects and will
      only succeed on a primary.  An example is ``renameCollection``.

      These command-specific helpers MUST use a read preference ``mode`` of
      'primary', MUST NOT take a read preference argument and MUST ignore any
      default read preference from client, database or collection
      configuration.  Languages with dynamic argument lists MUST throw an error
      if a read preference is provided as an argument.

      Clients SHOULD rely on the server to return a "not writable primary" or
      other error if the command is "must-use-primary".  Clients MAY raise an
      exception before sending the command if the topology type is Single and
      the server type is not "Standalone", "RSPrimary" or "Mongos", but the
      identification of the set of 'must-use-primary' commands is out of scope
      for this specification.

    - "should-use-primary": these commands are intended to be run on a primary,
      but would succeed -- albeit with possibly stale data -- when run against
      a secondary.  An example is ``listCollections``.

      These command-specific helpers MUST use a read preference ``mode`` of
      'primary', MUST NOT take a read preference argument and MUST ignore any
      default read preference from client, database or collection
      configuration.  Languages with dynamic argument lists MUST throw an error
      if a read preference is provided as an argument.

      Clients MUST NOT raise an exception if the topology type is Single.

    - "may-use-secondary": these commands run against primaries or secondaries,
      according to users' read preferences.  They are sometimes called
      "query-like" commands.

      The current list of "may-use-secondary" commands includes:

      - aggregate without a write stage (e.g. ``$out``, ``$merge``)
      - collStats
      - count
      - dbStats
      - distinct
      - find
      - geoNear
      - geoSearch
      - group
      - mapReduce where the ``out`` option is ``{ inline: 1 }``
      - parallelCollectionScan

      Associated command-specific helpers SHOULD take a read preference
      argument and otherwise MUST use the default read preference from client,
      database, or collection configuration.

      For pre-5.0 servers, an aggregate command is "must-use-primary" if its
      pipeline contains a write stage (e.g. ``$out``, ``$merge``); otherwise, it
      is "may-use-secondary". For 5.0+ servers, secondaries can execute an
      aggregate command with a write stage and all aggregate commands are
      "may-use-secondary". This is discussed in more detail in
      `Read preferences and server selection <../crud/crud.rst#read-preferences-and-server-selection>`_
      in the CRUD spec.

      If a client provides a specific helper for inline mapReduce, then it is
      "may-use-secondary" and the *regular* mapReduce helper is
      "must-use-primary". Otherwise, the mapReduce helper is "may-use-secondary"
      and it is the user's responsibility to specify ``{inline: 1}`` when
      running mapReduce on a secondary.

    New command-specific helpers implemented in the future will be considered
    "must-use-primary", "should-use-primary" or "may-use-secondary" according
    to the specifications for those future commands.  Command helper
    specifications SHOULD use those terms for clarity.

Rules for server selection
--------------------------

Server selection is a process which takes an operation type (read or write), a
ClusterDescription, and optionally a read preference and, on success, returns a
ServerDescription for an operation of the given type.

Server selection varies depending on whether a client is
multi-threaded/asynchronous or single-threaded because a single-threaded
client cannot rely on the topology state being updated in the background.

Multi-threaded or asynchronous server selection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A driver that uses multi-threaded or asynchronous monitoring MUST unblock
waiting operations as soon as server selection completes, even if not all
servers have been checked by a monitor.  Put differently, the client MUST NOT
block server selection while waiting for server discovery to finish.

For example, if the client is discovering a replica set and the application
attempts a read operation with mode 'primaryPreferred', the operation MUST
proceed immediately if a suitable secondary is found, rather than blocking
until the client has checked all members and possibly discovered a primary.

The number of threads allowed to wait for server selection SHOULD be either
(a) the same as the number of threads allowed to wait for a connection from
a pool; or (b) governed by a global or client-wide limit on number of
waiting threads, depending on how resource limits are implemented by a
driver.

operationCount
``````````````

Multi-threaded or async drivers MUST keep track of the number of operations that
a given server is currently executing (the server's ``operationCount``). This
value MUST be incremented once a server is selected for an operation and MUST be
decremented once that operation has completed, regardless of its outcome. Where
this value is stored is left as a implementation detail of the driver; some
example locations include the ``Server`` type that also owns the connection pool
for the server (if there exists such a type in the driver's implementation) or
on the pool itself. Incrementing or decrementing a server's ``operationCount``
MUST NOT wake up any threads that are waiting for a topology update as part of
server selection. See `operationCount-based selection within the latency window
(multi-threaded or async)`_ for the rationale behind the way this value is used.

Server Selection Algorithm
``````````````````````````

For multi-threaded clients, the server selection algorithm is as follows:

1. Record the server selection start time

2. If the topology wire version is invalid, raise an error

3. Find suitable servers by topology type and operation type

4. Filter the suitable servers by calling the optional, application-provided server
   selector.

5. If there are any suitable servers, filter them according to `Filtering
   suitable servers based on the latency window`_ and continue to the next step;
   otherwise, goto Step #9.

6. Choose two servers at random from the set of suitable servers in the latency
   window. If there is only 1 server in the latency window, just select that
   server and goto Step #8.

7. Of the two randomly chosen servers, select the one with the lower
   ``operationCount``. If both servers have the same ``operationCount``, select
   arbitrarily between the two of them.

8. Increment the ``operationCount`` of the selected server and return it. Do not
   go onto later steps.

9. Request an immediate topology check, then block the server selection thread
   until the topology changes or until the server selection timeout has elapsed

10. If more than ``serverSelectionTimeoutMS`` milliseconds have elapsed since
    the selection start time, raise a `server selection error`_

11. Goto Step #2


Single-threaded server selection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Single-threaded drivers do not monitor the topology in the background.
Instead, they MUST periodically update the topology during server selection
as described below.

When ``serverSelectionTryOnce`` is true, ``serverSelectionTimeoutMS`` has
no effect; a single immediate topology check will be done if the topology
starts stale or if the first selection attempt fails.

When ``serverSelectionTryOnce`` is false, then the server selection loops
until a server is successfully selected or until
``serverSelectionTimeoutMS`` is exceeded.

Therefore, for single-threaded clients, the server selection algorithm is
as follows:

1. Record the server selection start time

2. Record the maximum time as start time plus ``serverSelectionTimeoutMS``

3. If the topology has not been scanned in ``heartbeatFrequencyMS``
   milliseconds, mark the topology stale

4. If the topology is stale, proceed as follows:

   - record the target scan time as last scan time plus ``minHeartBeatFrequencyMS``

   - if `serverSelectionTryOnce`_ is false and the target scan time would
     exceed the maximum time, raise a `server selection error`_

   - if the current time is less than the target scan time, sleep until
     the target scan time

   - do a blocking immediate topology check (which must also update the
     last scan time and mark the topology as no longer stale)

5. If the topology wire version is invalid, raise an error

6. Find suitable servers by topology type and operation type

7. Filter the suitable servers by calling the optional, application-provided
   server selector.

8. If there are any suitable servers, filter them according to `Filtering
   suitable servers based on the latency window`_ and return one at random from
   the filtered servers; otherwise, mark the topology stale and continue to step
   #9.

9. If `serverSelectionTryOnce`_ is true and the last scan time is newer than
   the selection start time, raise a `server selection error`_; otherwise,
   goto Step #4

10. If the current time exceeds the maximum time, raise a
    `server selection error`_

11. Goto Step #4

Before using a socket to the selected server, drivers MUST check whether
the socket has been used in `socketCheckIntervalMS`_ milliseconds.  If the
socket has been idle for longer, the driver MUST update the
ServerDescription for the selected server.  After updating, if the server
is no longer suitable, the driver MUST repeat the server selection
algorithm and select a new server.

Because single-threaded selection can do a blocking immediate check,
``serverSelectionTimeoutMS`` is not a hard deadline.  The actual
maximum server selection time for any given request can vary from
``serverSelectionTimeoutMS`` minus ``minHeartbeatFrequencyMS`` to
``serverSelectionTimeoutMS`` plus the time required for a blocking scan.

Single-threaded drivers MUST document that when ``serverSelectionTryOne``
is true, selection may take up to the time required for a blocking scan,
and when ``serverSelectionTryOne`` is false, selection may take up to
``serverSelectionTimeoutMS`` plus the time required for a blocking scan.

Topology type: Unknown
~~~~~~~~~~~~~~~~~~~~~~

When a deployment has topology type "Unknown", no servers are suitable for read or write
operations.

Topology type: Single
~~~~~~~~~~~~~~~~~~~~~

A deployment of topology type Single contains only a single server of any type.
Topology type Single signifies a direct connection intended to receive all read
and write operations.

Therefore, read preference is ignored during server selection with topology
type Single.  The single server is always suitable for reads if it is
available.  Depending on server type, the read preference is communicated
to the server differently:

- Type Mongos: the read preference is sent to the server using the rules
  for `Passing read preference to mongos and load balancers`_.

- Type Standalone: clients MUST NOT send the read preference to the server

- For all other types, using OP_QUERY: clients MUST always set the ``SecondaryOk`` wire
  protocol flag on reads to ensure that any server type can handle the
  request.

- For all other types, using OP_MSG: If no read preference is configured by the
  application, or if the application read preference is Primary, then
  $readPreference MUST be set to ``{ "mode": "primaryPreferred" }`` to ensure
  that any server type can handle the request.  If the application read
  preference is set otherwise, $readPreference MUST be set following
  `Document structure`_.

The single server is always suitable for write operations if it is available.

Topology type: LoadBalanced
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

During command construction, drivers MUST add a $readPreference field to the
command when required by `Passing read preference to mongos and load balancers`_;
see the `Load Balancer Specification <../load-balancers/load-balancers.rst#server-selection>`__
for details.


Topology types: ReplicaSetWithPrimary or ReplicaSetNoPrimary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A deployment with topology type ReplicaSetWithPrimary or ReplicaSetNoPrimary
can have a mix of server types: RSPrimary (only in ReplicaSetWithPrimary),
RSSecondary, RSArbiter, RSOther, RSGhost, Unknown or PossiblePrimary.

Read operations
```````````````

For the purpose of selecting a server for read operations, the same rules apply
to both ReplicaSetWithPrimary and ReplicaSetNoPrimary.

To select from the topology a server that matches the user's Read Preference:

If ``mode`` is 'primary', select the primary server.

If ``mode`` is 'secondary' or 'nearest':

  #. Select all secondaries if ``mode`` is 'secondary', or all secondaries and
     the primary if ``mode`` is 'nearest'.
  #. From these, filter out servers staler than ``maxStalenessSeconds`` if it is a positive number.
  #. From the remaining servers, select servers matching the ``tag_sets``.
  #. From these, select one server within the latency window.

(See `algorithm for filtering by staleness`_, `algorithm for filtering by
tag_sets`_, and `filtering suitable servers based on the latency window`_ for
details on each step, and `why is maxStalenessSeconds applied before
tag_sets?`_.)

If ``mode`` is 'secondaryPreferred', attempt the selection algorithm with
``mode`` 'secondary' and the user's ``maxStalenessSeconds`` and ``tag_sets``. If
no server matches, select the primary.

If ``mode`` is 'primaryPreferred', select the primary if it is known, otherwise
attempt the selection algorithm with ``mode`` 'secondary' and the user's
``maxStalenessSeconds`` and ``tag_sets``.

For all read preferences modes except 'primary', clients MUST set the
``SecondaryOk`` wire protocol flag (OP_QUERY) or ``$readPreference`` global
command argument (OP_MSG) to ensure that any suitable server can handle the
request. If the read preference mode is 'primary', clients MUST NOT set the
``SecondaryOk`` wire protocol flag (OP_QUERY) or ``$readPreference`` global
command argument (OP_MSG).

Write operations
````````````````

If the topology type is ReplicaSetWithPrimary, only an available primary is
suitable for write operations.

If the topology type is ReplicaSetNoPrimary, no servers are suitable for write
operations.

Topology type: Sharded
~~~~~~~~~~~~~~~~~~~~~~

A deployment of topology type Sharded contains one or more servers of type
Mongos or Unknown.

For read operations, all servers of type Mongos are suitable; the ``mode``,
``tag_sets``, and ``maxStalenessSeconds`` read preference parameters are ignored for selecting a
server, but are passed through to mongos. See `Passing read preference to mongos and load balancers`_.

For write operations, all servers of type Mongos are suitable.

If more than one mongos is suitable, drivers MUST select a suitable server
within the latency window (see `Filtering suitable servers based on the latency
window`_).

Round Trip Times and the Latency Window
---------------------------------------

Calculation of Average Round Trip Times
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For every available server, clients MUST track the average RTT of server
monitoring ``hello`` or legacy hello commands.

An Unknown server has no average RTT.  When a server becomes unavailable, its
average RTT MUST be cleared.  Clients MAY implement this idiomatically (e.g
nil, -1, etc.).

When there is no average RTT for a server, the average RTT MUST be set equal to
the first RTT measurement (i.e. the first ``hello`` or legacy hello command after
the server becomes available).

After the first measurement, average RTT MUST be computed using an
exponentially-weighted moving average formula, with a weighting factor
(``alpha``) of 0.2.  If the prior average is denoted ``old_rtt``, then the new
average (``new_rtt``) is computed from a new RTT measurement (``x``) using the
following formula::

    alpha = 0.2
    new_rtt = alpha * x + (1 - alpha) * old_rtt

A weighting factor of 0.2 was chosen to put about 85% of the weight of the
average RTT on the 9 most recent observations.

Filtering suitable servers based on the latency window
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Server selection results in a set of zero or more suitable servers.  If more
than one server is suitable, a server MUST be selected from among those within
the latency window.

The ``localThresholdMS`` configuration parameter controls the size of the
latency window used to select a suitable server.

The shortest average round trip time (RTT) from among suitable servers anchors
one end of the latency window (``A``).  The other end is determined by adding
``localThresholdMS`` (``B = A + localThresholdMS``).

A server MUST be selected from among suitable servers that have an average RTT
(``RTT``) within the latency window (i.e. ``A ≤ RTT ≤ B``). In other words, the
suitable server with the shortest average RTT is **always** a possible choice.
Other servers could be chosen if their average RTTs are no more than
``localThresholdMS`` more than the shortest average RTT.

See either `Single-threaded server selection`_ or `Multi-threaded or
asynchronous server selection`_ for information on how to select a server from
among those within the latency window.


Checking an Idle Socket After socketCheckIntervalMS
---------------------------------------------------

Only for single-threaded drivers.

If a server is selected that has an existing connection that has been idle for
socketCheckIntervalMS, the driver MUST check the connection with the "ping"
command. If the ping succeeds, use the selected connection. If not, set the
server's type to Unknown and update the Topology Description according to the
Server Discovery and Monitoring Spec, and attempt **once** more to select a
server.

The logic is expressed in this pseudocode. The algorithm for the "getServer"
function is suggested below, in `Single-threaded server selection
implementation`_::

    def getConnection(criteria):
        # Get a server for writes, or a server matching read prefs, by
        # running the server selection algorithm.
        server = getServer(criteria)
        if not server:
            throw server selection error

        connection = server.connection
        if connection is NULL:
            connect to server and return connection
        else if connection has been idle < socketCheckIntervalMS:
            return connection
        else:
            try:
                use connection for "ping" command
                return connection
            except network error:
                close connection
                mark server Unknown and update Topology Description

                # Attempt *once* more to select.
                server = getServer(criteria)
                if not server:
                    throw server selection error

                connect to server and return connection


See `What is the purpose of socketCheckIntervalMS?`_.

Requests and Pinning Deprecated
-------------------------------

The prior read preference specification included the concept of a "request",
which pinned a server to a thread for subsequent, related reads.  Requests
and pinning are now **deprecated**.  See `What happened to pinning?`_ for
the rationale for this change.

Drivers with an existing request API MAY continue to provide it for backwards
compatibility, but MUST document that pinning for the request does not
guarantee monotonic reads.

Drivers MUST NOT automatically pin the client or a thread to a particular
server without an explicit ``start_request`` (or comparable) method call.

Outside a legacy "request" API, drivers MUST use server selection for each
individual read operation.

Reference Implementation
========================

The single-threaded reference implementation is the Perl master branch (work
towards v1.0.0).  The multi-threaded reference implementation is TBD.

Implementation Notes
====================

These are suggestions. As always, driver authors should balance cross-language
standardization with backwards compatibility and the idioms of their language.

Modes
-----

Modes ('primary', 'secondary', ...) are constants declared in whatever way is
idiomatic for the programming language. The constant values may be ints,
strings, or whatever.  However, when attaching modes to ``$readPreference``
camel case must be used as described above in `Passing read preference to
mongos and load balancers`_.

primaryPreferred and secondaryPreferred
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

'primaryPreferred' is equivalent to selecting a server with read preference mode
'primary' (without ``tag_sets`` or ``maxStalenessSeconds``), or, if that fails, falling back to selecting
with read preference mode 'secondary' (with ``tag_sets`` and ``maxStalenessSeconds``, if provided).

'secondaryPreferred' is the inverse: selecting with mode 'secondary' (with
``tag_sets`` and ``maxStalenessSeconds``) and falling back to selecting with mode 'primary' (without
``tag_sets`` or ``maxStalenessSeconds``).

Depending on the implementation, this may result in cleaner code.

nearest
~~~~~~~

The term 'nearest' is unfortunate, as it implies a choice based on geographic
locality or absolute lowest latency, neither of which are true.

Instead, and unlike the other read preference modes, 'nearest' does not favor
either primaries or secondaries; instead all servers are candidates and are
filtered by ``tag_sets`` and ``maxStalenessSeconds``.

To always select the server with the lowest RTT, users should use mode 'nearest'
without ``tag_sets`` or ``maxStalenessSeconds`` and set ``localThresholdMS`` to zero.

To distribute reads across all members evenly regardless of RTT, users should
use mode 'nearest' without ``tag_sets`` or ``maxStalenessSeconds`` and set ``localThresholdMS`` very high so
that all servers fall within the latency window.

In both cases, ``tag_sets`` and ``maxStalenessSeconds`` could be used to further restrict the set of eligible
servers, if desired.

Tag set lists
-------------

Tag set lists can be configured in the driver in whatever way is natural for
the language.

Multi-threaded server selection implementation
----------------------------------------------

The following example uses a single lock for clarity.  Drivers are free to
implement whatever concurrency model best suits their design.

The following is pseudocode for `multi-threaded or asynchronous server
selection`_::

    def getServer(criteria):
        client.lock.acquire()

        now = gettime()
        endTime = now + serverSelectionTimeoutMS

        while true:
            # The topologyDescription keeps track of whether any server has an
            # an invalid wire version range
            if not topologyDescription.compatible:
                client.lock.release()
                throw invalid wire protocol range error with details

            if maxStalenessSeconds is set:
                if client minWireVersion < 5 and any available server's maxWireVersion < 5:
                    client.lock.release()
                    throw error

                if topologyDescription.type in (ReplicaSetWithPrimary, ReplicaSetNoPrimary):
                    if (maxStalenessSeconds * 1000 < heartbeatFrequencyMS + idleWritePeriodMS or
                        maxStalenessSeconds < smallestMaxStalenessSeconds):
                    client.lock.release()
                    throw error

            servers = all servers in topologyDescription matching criteria

            if serverSelector is not null:
                servers = serverSelector(servers)

            if servers is not empty:
                in_window = servers within the latency window
                if len(in_window) == 1:
                    selected = in_window[0]
                else:
                    server1, server2 = random two entries from in_window
                    if server1.operation_count <= server2.operation_count:
                        selected = server1
                    else:
                        selected = server2
                selected.operation_count += 1
                client.lock.release()
                return selected

            request that all monitors check immediately

            # Wait for a new TopologyDescription. condition.wait() releases
            # client.lock while waiting and reacquires it before returning.
            # While a thread is waiting on client.condition, it is awakened
            # early whenever a server check completes.
            timeout_left = endTime - gettime()
            client.condition.wait(timeout_left)

            if now after endTime:
                client.lock.release()
                throw server selection error


Single-threaded server selection implementation
-----------------------------------------------

The following is pseudocode for `single-threaded server selection`_::

    def getServer(criteria):
        startTime = gettime()
        loopEndTime = startTime
        maxTime = startTime + serverSelectionTimeoutMS/1000
        nextUpdateTime = topologyDescription.lastUpdateTime
                       + heartbeatFrequencyMS/1000:

        if nextUpdateTime < startTime:
            topologyDescription.stale = true

        while true:

            if topologyDescription.stale:
                scanReadyTime = topologyDescription.lastUpdateTime
                              + minHeartbeatFrequencyMS/1000

                if ((not serverSelectionTryOnce) && (scanReadyTime > maxTime)):
                    throw server selection error with details

                # using loopEndTime below is a proxy for "now" but avoids
                # the overhead of another gettime() call
                sleepTime = scanReadyTime - loopEndTime

                if sleepTime > 0:
                    sleep sleepTime

                rescan all servers
                topologyDescription.lastupdateTime = gettime()
                topologyDescription.stale = false

            # topologyDescription keeps a record of whether any
            # server has an incompatible wire version range
            if not topologyDescription.compatible:
                topologyDescription.stale = true
                throw invalid wire version range error with details

            if maxStalenessSeconds is set:
                if client minWireVersion < 5 and any available server's maxWireVersion < 5:
                    throw error

                if topologyDescription.type in (ReplicaSetWithPrimary, ReplicaSetNoPrimary):
                    if (maxStalenessSeconds * 1000 < heartbeatFrequencyMS + idleWritePeriodMS or
                        maxStalenessSeconds < smallestMaxStalenessSeconds):
                    throw error

            servers = all servers in topologyDescription matching criteria

            if serverSelector is not null:
                servers = serverSelector(servers)

            if servers is not empty:
                in_window = servers within the latency window
                return random entry from in_window
            else:
                topologyDescription.stale = true

            loopEndTime = gettime()

            if serverSelectionTryOnce:
                if topologyDescription.lastUpdateTime > startTime:
                    throw server selection error with details
            else if loopEndTime > maxTime:
                throw server selection error with details

.. _server selection error:

Server Selection Errors
-----------------------

Drivers should use server descriptions and their error attributes (if set) to
return useful error messages.

For example, when there are no members matching the ReadPreference:

- "No server available for query with ReadPreference primary"
- "No server available for query with ReadPreference secondary"
- "No server available for query with ReadPreference " + mode + ", tag set list " + tag_sets + ", and ``maxStalenessSeconds`` " + maxStalenessSeconds

Or, if authentication failed:

- "Authentication failed: [specific error message]"

Here is a sketch of some pseudocode for handling error reporting when errors
could be different across servers::

    if there are any available servers:
        error_message = "No servers are suitable for " + criteria
    else if all ServerDescriptions' errors are the same:
        error_message = a ServerDescription.error value
    else:
        error_message = ', '.join(all ServerDescriptions' errors)

Cursors
-------

Cursor operations OP_GET_MORE and OP_KILL_CURSOR do not go through the server
selection process.  Cursor operations must be sent to the original server that
received the query and sent the OP_REPLY.  For exhaust cursors, the same socket
must be used for OP_GET_MORE until the cursor is exhausted.

Sharded Transactions
--------------------

Operations that are part of a sharded transaction (after the initial command)
do not go through the server selection process. Sharded transaction operations
MUST be sent to the original mongos server on which the transaction was
started.

The 'text' command and mongos
-----------------------------

*Note*: As of MongoDB 2.6, mongos doesn't distribute the "text" command to
secondaries, see SERVER-10947_.

However, the "text" command is deprecated in 2.6, so this command-specific
helper may become deprecated before this is fixed.

.. _SERVER-10947: https://jira.mongodb.org/browse/SERVER-10947

Test Plan
=========

The server selection test plan is given in a separate document that
describes the tests and supporting data files: `Server Selection Tests`_

.. _Server Selection Tests: https://github.com/mongodb/specifications/blob/master/source/server-selection/server-selection-tests.rst

Design Rationale
================

Use of topology types
---------------------

The prior version of the read preference spec had only a loose definition of
server or topology types.  The `Server Discovery and Monitoring`_ spec defines these terms
explicitly and they are used here for consistency and clarity.

Consistency with mongos
-----------------------

In order to ensure that behavior is consistent regardless of topology type,
read preference behaviors are limited to those that mongos can proxy.

For example, mongos ignores read preference 'secondary' when a shard consists of
a single server.  Therefore, this spec calls for topology type Single to ignore
read preferences for consistency.

The spec has been written with the intention that it can apply to both drivers
and mongos and the term "client" has been used when behaviors should apply to
both.  Behaviors that are specific to drivers are largely limited to those
for communicating with a mongos.

New localThresholdMS configuration option name
------------------------------------------------

Because this does not apply **only** to secondaries and does not limit absolute
latency, the name ``secondaryAcceptableLatencyMS`` is misleading.

The mongos name ``localThreshold`` misleads because it has nothing to do with
locality.  It also doesn't include the ``MS`` units suffix for consistency with
other time-related configuration options.

However, given a choice between the two, ``localThreshold`` is a more general
term.  For drivers, we add the ``MS`` suffix for clarity about units and
consistency with other configuration options.

Random selection within the latency window (single-threaded)
------------------------------------------------------------

When more than one server is judged to be suitable, the spec calls for random
selection to ensure a fair distribution of work among servers within the
latency window.

It would be hard to ensure a fair round-robin approach given the potential for
servers to come and go.  Making newly available servers either first or last
could lead to unbalanced work.  Random selection has a better fairness
guarantee and keeps the design simpler.

operationCount-based selection within the latency window (multi-threaded or async)
----------------------------------------------------------------------------------

As operation execution slows down on a node (e.g. due to degraded server-side
performance or increased network latency), checked-out pooled connections to
that node will begin to remain checked out for longer periods of time. Assuming
at least constant incoming operation load, more connections will then need to be
opened against the node to service new operations that it gets selected for,
further straining it and slowing it down. This can lead to runaway connection
creation scenarios that can cripple a deployment ("connection storms"). As part
of DRIVERS-781, the random choice portion of multi-threaded server selection was
changed to more evenly spread out the workload among suitable servers in order
to prevent any single node from being overloaded. The new steps achieve this by
approximating an individual server's load via the number of concurrent
operations that node is processing (operationCount) and then routing operations
to servers with less load. This should reduce the number of new operations
routed towards nodes that are busier and thus increase the number routed towards
nodes that are servicing operations faster or are simply less busy. The previous
random selection mechanism did not take load into account and could assign work
to nodes that were under too much stress already.

As an added benefit, the new approach gives preference to nodes that have
recently been discovered and are thus are more likely to be alive (e.g. during a
rolling restart). The narrowing to two random choices first ensures new servers
aren't overly preferred however, preventing a "thundering herd"
situation. Additionally, the `maxConnecting`_ provisions included in the CMAP
specification prevent drivers from crippling new nodes with connection storms.

This approach is based on the `"Power of Two Random Choices with Least Connections" <https://web.archive.org/web/20191212194243/https://www.nginx.com/blog/nginx-power-of-two-choices-load-balancing-algorithm/>`_
load balancing algorithm.

An alternative approach to this would be to prefer selecting servers that
already have available connections. While that approach could help reduce
latency, it does not achieve the benefits of routing operations away from slow
servers or of preferring newly introduced servers. Additionally, that approach
could lead to the same node being selected repeatedly rather than spreading the
load out among all suitable servers.

The SecondaryOk wire protocol flag
----------------------------------

In server selection, there is a race condition that could exist between what
a selected server type is believed to be and what it actually is.

The ``SecondaryOk`` wire protocol flag solves the race problem by communicating
to the server whether a secondary is acceptable.  The server knows its type
and can return a "not writable primary" error if ``SecondaryOk`` is false and
the server is a secondary.

However, because topology type Single is used for direct connections, we want
read operations to succeed even against a secondary, so the ``SecondaryOk`` wire
protocol flag must be sent to mongods with topology type Single.

(If the server type is Mongos, follow the rules for
`Passing read preference to mongos and load balancers`_, even for topology type Single.)

General command method going to primary
---------------------------------------

The list of commands that can go to secondaries changes over time and depends
not just on the command but on parameters.  For example, the ``mapReduce``
command may or may not be able to be run on secondaries depending on the value
of the ``out`` parameter.

It significantly simplifies implementation for the general command method
always to go to the primary unless a explicit read preference is set and rely
on users of the general command method to provide a read preference appropriate
to the command.

The command-specific helpers will need to implement a check of read preferences
against the semantics of the command and its parameters, but keeping this logic
close to the command rather than in a generic method is a better design than
either delegating this check to the generic method, duplicating the logic in
the generic method, or coupling both to another validation method.

Average round trip time calculation
-----------------------------------

Using an exponentially-weighted moving average avoids having to store and
rotate an arbitrary number of RTT observations.  All observations count towards
the average.  The weighting makes recent observations count more heavily while
smoothing volatility.

Verbose errors
--------------

Error messages should be sufficiently verbose to allow users and/or support
engineers to determine the reasons for server selection failures from log
or other error messages.

"Try once" mode
---------------

Single-threaded drivers in languages like PHP and Perl are typically deployed
as many processes per application server. Each process must independently
discover and monitor the MongoDB deployment.

When no suitable server is available (due to a partition or misconfiguration),
it is better for each request to fail as soon as its process detects a
problem, instead of waiting and retrying to see if the deployment recovers.

Minimizing response latency is important for maximizing request-handling
capacity and for user experience (e.g. a quick fail message instead of a slow
web page).

However, when a request arrives and the topology information is already stale,
or no suitable server is known,
making a single attempt to update the topology to service the request is
acceptable.

A user of a single-threaded driver who prefers resilience in the face of topology problems,
rather than short response times,
can turn the "try once" mode off.
Then driver rescans the topology every minHeartbeatFrequencyMS
until a suitable server is found or the serverSelectionTimeoutMS expires.

What is the purpose of socketCheckIntervalMS?
---------------------------------------------

Single-threaded clients need to make a compromise: if they check servers too
frequently it slows down regular operations, but if they check too rarely they
cannot proactively avoid errors.

Errors are more disruptive for single-threaded clients than for multi-threaded.
If one thread in a multi-threaded process encounters an error, it warns the
other threads not to use the disconnected server. But single-threaded clients
are deployed as many independent processes per application server, and each
process must throw an error until all have discovered that a server is down.

The compromise specified here balances the cost of frequent checks against the
disruption of many errors. The client preemptively checks individual sockets
that have not been used in the last `socketCheckIntervalMS`_, which is more
frequent by default than `heartbeatFrequencyMS` defined in the Server Discovery
and Monitoring Spec.

The client checks the socket with a "ping" command, rather than "hello" or legacy
hello, because it is not checking the server's full state as in the Server Discovery
and Monitoring Spec, it is only verifying that the connection is still open. We
might also consider a `select` or `poll` call to check if the socket layer
considers the socket closed, without requiring a round-trip to the server.
However, this technique usually will not detect an uncleanly shutdown server or
a network outage.


Backwards Compatibility
=======================

In general, backwards breaking changes have been made in the name of
consistency with mongos and avoiding misleading users about monotonicity.

* Features removed:

    - Automatic pinning (see `What happened to pinning?`_)

    - Auto retry (replaced by the general server selection algorithm)

    - mongos "high availability" mode (effectively, mongos pinning)

* Other features and behaviors have changed explicitly

    - Ignoring read preferences for topology type Single

    - Default read preference for the generic command method

* Changes with grandfather clauses

    - Alternate names for ``localThresholdMS``

    - Pinning for legacy request APIs

* Internal changes with little user-visibility

    - Clarifying calculation of average RTT

Questions and Answers
=====================

What happened to pinning?
-------------------------

The prior read preference spec, which was implemented in the versions of the
drivers and mongos released concomitantly with MongoDB 2.2, stated that a
thread / client should remain pinned to an RS member as long as that member
matched the current mode, tags, and acceptable latency. This increased the
odds that reads would be monotonic (assuming no rollback),
but had the following surprising consequence:

1. Thread / client reads with mode 'secondary' or 'secondaryPreferred', gets
   pinned to a secondary
2. Thread / client reads with mode 'primaryPreferred', driver / mongos sees that
   the pinned member (a secondary) matches the mode (which *allows* for a
   secondary) and reads from secondary, even though the primary is available and
   preferable

The old spec also had the swapped problem, reading from the primary with
'secondaryPreferred', except for mongos which was changed at the last minute
before release with SERVER-6565_.

This left application developers with two problems:

1. 'primaryPreferred' and 'secondaryPreferred' acted surprisingly and
   unpredictably within requests
2. There was no way to specify a common need: read from a secondary if possible
   with 'secondaryPreferred', then from primary if possible with 'primaryPreferred',
   all within a request. Instead an application developer would have to do the
   second read with 'primary', which would unpin the thread but risk unavailability
   if only secondaries were up.

Additionally, mongos 2.4 introduced the releaseConnectionsAfterResponse option
(RCAR), mongos 2.6 made it the default and mongos 2.8 will remove the ability
to turn it off.  This means that pinning to a mongos offers no guarantee that
connections to shards are pinned.  Since we can't provide the same guarantees
for replica sets and sharded clusters, we removed automatic pinning entirely
and deprecated "requests". See SERVER-11956_ and SERVER-12273_.

Regardless, even for replica sets, pinning offers no monotonicity because of
the ever-present possibility of rollbacks.  Through MongoDB 2.6, secondaries
did not close sockets on rollback, so a rollback could happen between any two
queries without any indication to the driver.

Therefore, an inconsistent feature that doesn't actually do what people think
it does has no place in the spec and has been removed.  Should the server
eventually implement some form of "sessions", this spec will need to be revised
accordingly.

.. _SERVER-6565: https://jira.mongodb.org/browse/SERVER-6565
.. _SERVER-11956: https://jira.mongodb.org/browse/SERVER-11956
.. _SERVER-12273: https://jira.mongodb.org/browse/SERVER-12273

Why change from mongos High Availablity (HA) to random selection?
---------------------------------------------------------------------

Mongos HA has similar problems with pinning, in that one can wind up pinned
to a high-latency mongos even if a lower-latency mongos later becomes
available.

Selection within the latency window avoids this problem and makes server
selection exactly analogous to having multiple suitable servers from a replica
set.  This is easier to explain and implement.

What happened to auto-retry?
----------------------------

The old auto-retry mechanism was closely connected to server pinning, which has
been removed.  It also mandated exactly three attempts to carry out a query on
different servers, with no way to disable or adjust that value, and only for
the first query within a request.

To the extent that auto-retry was trying to compensate for unavailable servers,
the Server Discovery and Monitoring spec and new server selection algorithm
provide a more robust and configurable way to direct *all* queries to available
servers.

After a server is selected, several error conditions could still occur that
make the selected server unsuitable for sending the operation, such as:

    - the server could have shutdown the socket (e.g. a primary stepping down),

    - a connection pool could be empty, requiring new connections; those
      connections could fail to connect or could fail the server handshake

Once an operation is sent over the wire, several additional error conditions
could occur, such as:

    - a socket timeout could occur before the server responds

    - the server might send an RST packet, indicating the socket was already closed

    - for write operations, the server might return a "not writable primary" error

This specification does not require nor prohibit drivers from attempting
automatic recovery for various cases where it might be considered reasonable to
do so, such as:

    - repeating server selection if, after selection, a socket is determined to
      be unsuitable before a message is sent on it

    - for a read operation, after a socket error, selecting a new server
      meeting the read preference and resending the query

    - for a write operation, after a "not writable primary" error, selecting a new
      server (to locate the primary) and resending the write operation

Driver-common rules for retrying operations (and configuring such retries)
could be the topic of a different, future specification.

Why is maxStalenessSeconds applied before tag_sets?
---------------------------------------------------

The intention of read preference's list of tag sets is to allow a user to prefer
the first tag set but fall back to members matching later tag sets. In order to
know whether to fall back or not, we must first filter by all other criteria.

Say you have two secondaries:

  - Node 1, tagged `{'tag': 'value1'}`, estimated staleness 5 minutes
  - Node 2, tagged `{'tag': 'value2'}`, estimated staleness 1 minute

And a read preference:

  - mode: "secondary"
  - maxStalenessSeconds: 120 (2 minutes)
  - tag_sets: `[{'tag': 'value1'}, {'tag': 'value2'}]`

If tag sets were applied before maxStalenessSeconds, we would select Node 1 since it
matches the first tag set, then filter it out because it is too stale, and be
left with no eligible servers.

The user's intent in specifying two tag sets was to fall back to the second set
if needed, so we filter by maxStalenessSeconds first, then tag_sets, and select
Node 2.


References
==========

- `Server Discovery and Monitoring`_ specification
- `Driver Authentication`_ specification
- `Connection Monitoring and Pooling`_ specification

.. _Server Discovery and Monitoring: https://github.com/mongodb/specifications/tree/master/source/server-discovery-and-monitoring
.. _heartbeatFrequencyMS: https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#heartbeatfrequencyms
.. _Max Staleness: https://github.com/mongodb/specifications/tree/master/source/max-staleness
.. _idleWritePeriodMS: https://github.com/mongodb/specifications/blob/master/source/max-staleness/max-staleness.rst#idlewriteperiodms
.. _Driver Authentication: https://github.com/mongodb/specifications/blob/master/source/auth
.. _maxConnecting: /source/connection-monitoring-and-pooling/connection-monitoring-and-pooling.rst#connection-pool
.. _Connection Monitoring and Pooling: /source/connection-monitoring-and-pooling/connection-monitoring-and-pooling.rst
.. _Global Command Argument: /source/message/OP_MSG.rst#global-command-arguments

Changes
=======

2021-08-05: Updated $readPreference logic to describe OP_MSG behavior.

2015-06-26: Updated single-threaded selection logic with "stale" and serverSelectionTryOnce.

2015-08-10: Updated single-threaded selection logic to ensure a scan always
happens at least once under serverSelectionTryOnce if selection fails.
Removed the general selection algorithm and put full algorithms for each of
the single- and multi-threaded sections. Added a requirement that
single-threaded drivers document selection time expectations.

2016-07-21: Updated for Max Staleness support.

2016-08-03: Clarify selection algorithm, in particular that maxStalenessMS
comes before tag_sets.

2016-10-24: Rename option from "maxStalenessMS" to "maxStalenessSeconds".

2016-10-25: Change minimum maxStalenessSeconds value from 2 * heartbeatFrequencyMS
to heartbeatFrequencyMS + idleWritePeriodMS (with proper conversions of course).

2016-11-01: Update formula for secondary staleness estimate with the
equivalent, and clearer, expression of this formula from the Max Staleness Spec

2016-11-21: Revert changes that would allow idleWritePeriodMS to change in the
future, require maxStalenessSeconds to be at least 90.

2017-06-07: Clarify socketCheckIntervalMS behavior, single-threaded drivers
must retry selection after checking an idle socket and discovering it is broken.

2017-11-10: Added application-configurated server selector.

2017-11-12: Specify read preferences for OP_MSG with direct connection, and
delete obsolete comment direct connections to secondaries getting "not writable
primary" errors by design.

2018-01-22: Clarify that $query wrapping is only for OP_QUERY

2018-01-22: Clarify that $out on aggregate follows the "$out Aggregation
Pipeline Operator" spec and warns if read preference is not primary.

2018-01-29: Remove reference to '$out Aggregation spec'. Clarify runCommand
selection rules.

2018-12-13: Update tag_set example to use only String values

2019-05-20: Added rule to not send read preferene to standalone servers

2019-06-07: Clarify language for aggregate and mapReduce commands that write

2020-03-17: Specify read preferences with support for server hedged reads

2020-10-10: Consider server load when selecting servers within the latency
window.

.. [#] mongos 3.4 refuses to connect to mongods with maxWireVersion < 5,
   so it does no additional wire version checks related to maxStalenessSeconds.

2021-4-7: Adding in behaviour for load balancer mode.

2021-05-12: Removed deprecated URI option in favour of readPreference=secondaryPreferred.

2021-05-13: Updated to use modern terminology.

2021-09-03: Clarify that wire version check only applies to available servers.

2021-09-28: Note that 5.0+ secondaries support aggregate with write stages (e.g.
``$out`` and ``$merge``). Clarify setting ``SecondaryOk` wire protocol flag or
``$readPreference`` global command argument for replica set topology.
