# Server Discovery And Monitoring -- Test Plan

- Status: Accepted

- Minimum Server Version: 2.4 See also the YAML test files and their accompanying README in the "tests" directory.

______________________________________________________________________

## All servers unavailable

A MongoClient can be constructed without an exception, even with all seeds unavailable.

## Network error writing to primary

Scenario: With TopologyType ReplicaSetWithPrimary, a write to the primary fails with a network error other than timeout.

Outcome: The former primary's ServerType MUST become Unknown. The TopologyType MUST change to ReplicaSetNoPrimary. The
client MUST NOT immediately re-check the former primary.

## "Not writable primary" error when reading without SecondaryOk bit

Scenario: With TopologyType ReplicaSetWithPrimary, we read from a server we thought was RSPrimary. Thus the SecondaryOk
bit is not set.

The server response should indicate an error due to the server not being a primary.

Outcome: The former primary's ServerType MUST become Unknown. The TopologyType MUST change to ReplicaSetNoPrimary. The
client MUST NOT immediately re-check the former primary.

## "Node is recovering" error reading with SecondaryOk bit

Scenario: With TopologyType ReplicaSetWithPrimary, we read from a server we thought was RSSecondary. Thus the
SecondaryOk bit *is* set.

The server response should indicate an error due to the server being in recovering state.

Outcome: The former secondary's ServerType MUST become Unknown. The TopologyType MUST remain ReplicaSetWithPrimary. A
multi-threaded client MUST immediately re-check the former secondary, a single-threaded client MUST NOT.

## "Node is recovering" error from a write concern error

Scenario: With TopologyType ReplicaSetWithPrimary, a write to the primary responds with the following document:

> { ok: 1, writeConcernError: {code: 91, errmsg: "Replication is being shut down"} }

Outcome: The former primary's ServerType MUST become Unknown. The TopologyType MUST change to ReplicaSetNoPrimary. A
multi-threaded client MUST immediately re-check the former secondary, a single-threaded client MUST NOT.

## Parsing "not writable primary" and "node is recovering" errors

For all these example responses, the client MUST mark the server "Unknown" and store the error message in the
ServerDescription's error field.

Clients MUST NOT depend on any particular field order in these responses.

### Write command

Response to an "insert" command on an arbiter, secondary, recovering member, or ghost:

> {ok: 0, errmsg: "not writable primary"}

### Query with SecondaryOk bit

Response from an arbiter, recovering member, or ghost when SecondaryOk is true:

> {$err: "not primary or secondary; cannot currently read from this replSet member"}

The QueryFailure bit is set in responseFlags.

### Query without SecondaryOk bit

Response from an arbiter, recovering member, ghost, or secondary when SecondaryOk is false:

> {$err: "not writable primary and SecondaryOk=false"}

The QueryFailure bit is set in responseFlags.

### Count with SecondaryOk bit

Command response on an arbiter, recovering member, or ghost when SecondaryOk is true:

> {ok: 0, errmsg: "node is recovering"}

### Count without SecondaryOk bit

Command response on an arbiter, recovering member, ghost, or secondary when SecondaryOk is false:

> {ok: 0, errmsg: "not writable primary"}

## Topology discovery and direct connection

### Topology discovery

Scenario: given a replica set deployment with a secondary, where HOST is the address of the secondary, create a
MongoClient using `mongodb://HOST/?directConnection=false` as the URI. Attempt a write to a collection.

Outcome: Verify that the write succeeded.

### Direct connection

Scenario: given a replica set deployment with a secondary, where HOST is the address of the secondary, create a
MongoClient using `mongodb://HOST/?directConnection=true` as the URI. Attempt a write to a collection.

Outcome: Verify that the write failed with a NotWritablePrimary error.

### Existing behavior

Scenario: given a replica set deployment with a secondary, where HOST is the address of the secondary, create a
MongoClient using `mongodb://HOST/` as the URI. Attempt a write to a collection.

Outcome: Verify that the write succeeded or failed depending on existing driver behavior with respect to the starting
topology.

## Monitors sleep at least minHeartbeatFrequencyMS between checks

This test will be used to ensure monitors sleep for an appropriate amount of time between failed server checks so as to
not flood the server with new connection creations.

This test requires MongoDB 4.9.0+.

1. Enable the following failpoint:

    ```javascript
    {
        configureFailPoint: "failCommand",
        mode: { times: 5 },
        data: {
            failCommands: ["hello"], // or legacy hello command
            errorCode: 1234,
            appName: "SDAMMinHeartbeatFrequencyTest"
        }
    }
    ```

2. Create a client with directConnection=true, appName="SDAMMinHeartbeatFrequencyTest", and
    serverSelectionTimeoutMS=5000.

3. Start a timer.

4. Execute a `ping` command.

5. Stop the timer. Assert that the `ping` took between 2 seconds and 3.5 seconds to complete.

## Connection Pool Management

This test will be used to ensure monitors properly create and unpause connection pools when they discover servers.

This test requires failCommand appName support which is only available in MongoDB 4.2.9+.

1. Create a client with directConnection=true, appName="SDAMPoolManagementTest", and heartbeatFrequencyMS=500 (or lower
    if possible).

2. Verify via SDAM and CMAP event monitoring that a ConnectionPoolReadyEvent occurs after the first
    ServerHeartbeatSucceededEvent event does.

3. Enable the following failpoint:

    ```javascript
    {
        configureFailPoint: "failCommand",
        mode: { times: 2 },
        data: {
            failCommands: ["hello"], // or legacy hello command
            errorCode: 1234,
            appName: "SDAMPoolManagementTest"
        }
    }
    ```

4. Verify that a ServerHeartbeatFailedEvent and a ConnectionPoolClearedEvent (CMAP) are emitted.

5. Then verify that a ServerHeartbeatSucceededEvent and a ConnectionPoolReadyEvent (CMAP) are emitted.

6. Disable the failpoint.

## Connection Pool Backpressure

This test will be used to ensure that connection establishment failures during the TLS handshake do not result in a pool
clear event. We create a setup client to enable the ingress connection establishment rate limiter, and then induce a
connection storm. After the storm, we verify that some of the connections failed to checkout, but that the pool was not
cleared.

This test requires MongoDB 7.0+. See the
[MongoDB Server Parameters](https://www.mongodb.com/docs/manual/reference/parameters/#mongodb-parameter-param.ingressConnectionEstablishmentRateLimiterEnabled)
for more details.

This test MUST be run both with and without TLS enabled. Without TLS enabled, the connection establishment will fail
during the `hello` message, and with TLS enabled it will fail during the TLS handshake.

If running against a sharded cluster, this test MUST be run against only a single host, similar to how
`useMultipleMongoses:false` would be handled in a unified test.

1. Create a test client that listens to CMAP events, with maxConnecting=100. The higher maxConnecting will help ensure
    contention for creating connections.

2. Run the following commands to set up the rate limiter.

    ```python
    client.admin.command("setParameter", 1, ingressConnectionEstablishmentRateLimiterEnabled=True)
    client.admin.command("setParameter", 1, ingressConnectionEstablishmentRatePerSec=20)
    client.admin.command("setParameter", 1, ingressConnectionEstablishmentBurstCapacitySecs=1)
    client.admin.command("setParameter", 1, ingressConnectionEstablishmentMaxQueueDepth=1)
    ```

3. Add a document to the test collection so that the sleep operations will actually block:
    `client.test.test.insert_one({})`.

4. Run the following find command on the collection in 100 parallel threads/coroutines. Run these commands concurrently
    but block on their completion, and ignore errors raised by the command.
    `client.test.test.find_one({"$where": "function() { sleep(2000); return true; }})`

5. Assert that at least 10 `ConnectionCheckOutFailedEvent` occurred.

6. Assert that 0 `PoolClearedEvent` occurred.

7. Ensure that the following steps run at test teardown even if the test fails:

    7.1. Sleep for 1 second to clear the rate limiter.

    7.2. Execute the following command:
    `client.admin("setParameter", 1, ingressConnectionEstablishmentRateLimiterEnabled=False)`.
