=====================================
Server Discovery And Monitoring Tests
=====================================

The YAML and JSON files in this directory tree are platform-independent tests
that drivers can use to prove their conformance to the
Server Discovery And Monitoring Spec.

Additional prose tests, that cannot be represented as spec tests, are
described and MUST be implemented.

Version
-------

Files in the "specifications" repository have no version scheme. They are not
tied to a MongoDB server version.

Format
------

Each YAML file has the following keys:

- description: A textual description of the test.
- uri: A connection string.
- phases: An array of "phase" objects.
  A phase of the test optionally sends inputs to the client,
  then tests the client's resulting TopologyDescription.

Each phase object has two keys:

- responses: (optional) An array of "response" objects. If not provided,
  the test runner should construct the client and perform assertions specified
  in the outcome object without processing any responses.
- outcome: An "outcome" object representing the TopologyDescription.

A response is a pair of values:

- The source, for example "a:27017".
  This is the address the client sent the "ismaster" command to.
- An ismaster response, for example `{ok: 1, ismaster: true}`.
  If the response includes an electionId it is shown in extended JSON like
  `{"$oid": "000000000000000000000002"}`.
  The empty response `{}` indicates a network error
  when attempting to call "ismaster".

In non-monitoring tests, an "outcome" represents the correct
TopologyDescription that results from processing the responses in the phases
so far. It has the following keys:

- topologyType: A string like "ReplicaSetNoPrimary".
- setName: A string with the expected replica set name, or null.
- servers: An object whose keys are addresses like "a:27017", and whose values
  are "server" objects.
- logicalSessionTimeoutMinutes: null or an integer.
- maxSetVersion: absent or an integer.
- maxElectionId: absent or a BSON ObjectId.
- compatible: absent or a bool.

A "server" object represents a correct ServerDescription within the client's
current TopologyDescription. It has the following keys:

- type: A ServerType name, like "RSSecondary".
- setName: A string with the expected replica set name, or null.
- setVersion: absent or an integer.
- electionId: absent, null, or an ObjectId.
- logicalSessionTimeoutMinutes: absent, null, or an integer.
- minWireVersion: absent or an integer.
- maxWireVersion: absent or an integer.
- topologyVersion: absent, null, or a topologyVersion document.

In monitoring tests, an "outcome" contains a list of SDAM events that should
have been published by the client as a result of processing ismaster responses
in the current phase. Any SDAM events published by the client during its
construction (that is, prior to processing any of the responses) should be
combined with the events published during processing of ismaster responses
of the first phase of the test. A test MAY explicitly verify events published
during client construction by providing an empty responses array for the
first phase.


Use as unittests
----------------

Mocking
~~~~~~~

Drivers should be able to test their server discovery and monitoring logic
without any network I/O, by parsing ismaster responses from the test file
and passing them into the driver code. Parts of the client and monitoring
code may need to be mocked or subclassed to achieve this. `A reference
implementation for PyMongo 3.x is available here
<https://github.com/mongodb/mongo-python-driver/blob/26d25cd74effc1e7a8d52224eac6c9a95769b371/test/test_discovery_and_monitoring.py>`_.

Initialization
~~~~~~~~~~~~~~

For each file, create a fresh client object initialized with the file's "uri".

All files in the "single" directory include a connection string with one host
and no "replicaSet" option.
Set the client's initial TopologyType to Single, however that is achieved using the client's API.
(The spec says "The user MUST be able to set the initial TopologyType to Single"
without specifying how.)

All files in the "sharded" directory include a connection string with multiple hosts
and no "replicaSet" option.
Set the client's initial TopologyType to Unknown or Sharded, depending on the client's API.

All files in the "rs" directory include a connection string with a "replicaSet" option.
Set the client's initial TopologyType to ReplicaSetNoPrimary.
(For most clients, parsing a connection string with a "replicaSet" option
automatically sets the TopologyType to ReplicaSetNoPrimary.)

Set up a listener to collect SDAM events published by the client, including
events published during client construction.

Test Phases
~~~~~~~~~~~

For each phase in the file, parse the "responses" array.
Pass in the responses in order to the driver code.
If a response is the empty object `{}`, simulate a network error.

For non-monitoring tests,
once all responses are processed, assert that the phase's "outcome" object
is equivalent to the driver's current TopologyDescription.

For monitoring tests, once all responses are processed, assert that the
events collected so far by the SDAM event listener are equivalent to the
events specified in the phase.

Some fields such as "logicalSessionTimeoutMinutes", "compatible", and
"topologyVersion" were added later and haven't been added to all test files.
If these fields are present, test that they are equivalent to the fields of
the driver's current TopologyDescription or ServerDescription.

For monitoring tests, clear the list of events collected so far.

Continue until all phases have been executed.

Prose Tests
-----------

The following prose tests cannot be represented as spec tests and MUST be
implemented.

Streaming protocol Tests
~~~~~~~~~~~~~~~~~~~~~~~~

Drivers that implement the streaming protocol (multi-threaded or
asynchronous drivers) must implement the following tests. Each test should be
run against a standalone, replica set, and sharded cluster unless otherwise
noted.

Some of these cases should already be tested with the old protocol; in
that case just verify the test cases succeed with the new protocol.

1.  Test that the Monitor does not time out sooner than
    connectTimeoutMS+heartbeatFrequencyMS:

    #. Create a MongoClient with ``appName=monitorTimeoutTest``,
       ``connectTimeoutMS=100``, and ``heartbeatFrequencyMS=500``.

    #. Run an insert operation to prove the client has discovered the server.

    #. Sleep for 2 seconds. This must be long enough for multiple heartbeats
       to succeed.

    #. Assert the client never marked the server Unknown and never cleared
       the connection pool. If the Monitor had mistakenly neglected to set
       the connection timeout to connectTimeoutMS+heartbeatFrequencyMS the
       connection would have seen a timeout error after 100ms.

    #. Run an insert operation to prove the server is still selectable.

2.  Test that the Monitor times out after connectTimeoutMS+heartbeatFrequencyMS:

    #. Create a MongoClient with ``appName=monitorTimeoutTest``,
       ``connectTimeoutMS=100``, and ``heartbeatFrequencyMS=500``.

    #. Run an insert operation to prove the client has discovered the server.

    #. Configure the following failpoint to block isMaster replies longer
       than connectTimeoutMS+heartbeatFrequencyMS::

         db.adminCommand({
             configureFailPoint: "failCommand",
             mode: {times: 2},
             data: {
               failCommands: ["isMaster"],
               blockConnection: true,
               blockTimeMS: 700,
             },
         });

    #. Assert the client marks the server as Unknown after
       approximately connectTimeoutMS+maxAwaitTimeMS. For example, wait for
       a ServerDescriptionChangedEvent that marks the server Unknown or wait
       for a PoolClearEvent.

    #. Assert the client rediscovers the server in the next second. For
       example, wait for a ServerDescriptionChangedEvent where the server
       changes from Unknown to Known.

    #. Run an insert operation to prove the client has rediscovered the server.

3.  Same as above, but make mongod send ok: 0 in subsequent isMaster
    replies (with the failCommand fail point). Assert the client
    marks the server Unknown. If possible, assert that the Monitor closes the
    monitoring connection.

4.  Test that the Monitor handles ok: 1 but *without* the moreToCome flag set:

    #. Create a MongoClient with ``connectTimeoutMS=100`` and
       ``heartbeatFrequencyMS=500``.

    #. Run an insert operation to prove the client has discovered the server.

    #. Configure the server to not add the moreToCome flag via the
       ``doNotSetMoreToCome`` failpoint::

         db.adminCommand({
             configureFailPoint: "doNotSetMoreToCome",
             mode: {times: 1000},
         });

    #. Sleep for 2 seconds. This must be long enough for multiple heartbeats
       to succeed.

    #. Assert the client never marked the server Unknown and never cleared
       the connection pool. If the Monitor had mistakenly neglected to handle
       the missing moreToCome flag, then it would have timed out attempting
       to read the the next response after
       connectTimeoutMS+heartbeatFrequencyMS.

    #. Run an insert operation to prove the server is still selectable.

    #. Finally disable the doNotSetMoreToCome failpoint::

         db.adminCommand({
             configureFailPoint: "doNotSetMoreToCome",
             mode: {times: 'off'},
         });


5.  Configure the client with heartbeatFrequencyMS set to 500,
    overriding the default of 10000. Assert the client processes
    isMaster replies more frequently (approximately every 500ms).

6.  With a replica set. Configure the client to set heartbeatFrequencyMS
    to 5 minutes, overriding the default of 10000. Run
    replSetStepDown on the primary and assert the client discovers
    the new primary quickly.

7.  Configure the server to hang up on all "find" commands (using the
    "failCommand" failpoint). Execute a find command and assert the
    client marks the server Unknown. (See "Network error when reading
    or writing" in the main design doc.)

8.  Test that a MongoClient ignores errors from previous generations.

    #. Create a MongoClient with ``retryWrites=false``.

    #. Run an insert operation to prove the client has discovered the server.

    #. Configure the following failpoint to block insert command for 500ms
       and then close the connection. Blocking the insert commands allows
       both commands to be executed on connections from the same pool
       generation::

         db.adminCommand({
             configureFailPoint: "failCommand",
             mode: {times: 2},
             data: {
               failCommands: ["insert"],
               closeConnection: true,
               blockConnection: true,
               blockTimeMS: 500,
             },
         });

    #. Run 2 insertOne operations concurrently and assert that both operations
       fail with network errors.

    #. Assert that the server is reset to Unknown exactly once and the
       application pool is cleared exactly once. For example, assert that
       there was a single single ServerDescriptionChangedEvent that marks the server Unknown and a single PoolClearEvent.

    #. Run an insert operation to prove the server is rediscovered.

9.  Issue a write from 2 threads using two connections at the same time.
    Cause the server to fail both operations with a State Change
    Error (using the failCommand failpoint). Assert that the server
    is only reset to Unknown once and the application pool is not
    cleared.

RTT Tests
~~~~~~~~~

1.  Test that RTT is continuously updated.

    #. Create a client with  ``heartbeatFrequencyMS=500`` and subscribe to
       server events.

    #. Run a find command to wait for the server to be discovered.

    #. Sleep for 2 seconds. This must be long enough for multiple heartbeats
       to succeed.

    #. Assert that each ``ServerDescriptionChangedEvent`` includes a non-zero
       RTT.

    #. Configure the following failpoint to block isMaster commands for 250ms
       which should add extra latency to each RTT check::

         db.adminCommand({
             configureFailPoint: "failCommand",
             mode: {times: 1000},
             data: {
               failCommands: ["isMaster"],
               blockConnection: true,
               blockTimeMS: 250,
             },
         });

    #. Wait for the server's RTT to exceed 250ms.

    #. Disable the failpoint::

         db.adminCommand({
             configureFailPoint: "failCommand",
             mode: "off",
         });
