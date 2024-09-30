# Server Selection Test Plan

- Status: Accepted

- Minimum Server Version: 2.4

See also the YAML test files and their accompanying README in the "tests" directory.

______________________________________________________________________

## ReadPreference Document Validation

While there are no YAML tests for this section, clients implementing this spec SHOULD perform validations on
ReadPreference documents provided by the user. Specifically, documents with the following values should raise an error:

- Mode PRIMARY and non-empty tag set

## Calculating Round Trip Time

Drivers implementing server selection MUST test that RTT values are calculated correctly. YAML tests for RTT
calculations can be found in the "tests" directory and they test for correctness in the following scenarios:

- first RTT: new average RTT equals measurement
- subsequent measurements: new average RTT is calculated using the new measurement and the previous average as described
  in the spec.

Additionally, drivers SHOULD ensure that their implementations reject negative RTT values.

Lastly, drivers SHOULD ensure that average RTT for a given ServerDescription is reset to 0 if that server is
disconnected (ie a network error occurs during a `hello` or legacy hello call). Upon reconnect, the first new RTT value
should become the average RTT for this server.

The RTT tests are intentionally simplified to test the implementation of the EWMA algorithm without imposing any
additional conditions on drivers that might affect architecture. For some drivers, RTT tests might require mocks; for
others, it might just require unit tests.

## Server Selection

The following test cases can be found in YAML form in the "tests" directory. Each test lists a TopologyDescription
representing a set of servers, a ReadPreference document, and sets of servers returned at various stages of the server
selection process. These sets are described below. Note that it is not required to test for correctness at every step.

| Test Case           | Description                                                                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `suitable_servers`  | the set of servers matching all server selection logic.                                                                                            |
| `in_latency_window` | the subset of `suitable_servers` that falls within the allowable latency window (required). NOTE: tests use the default localThresholdMS of 15 ms. |

Drivers implementing server selection MUST test that their implementations correctly return **one** of the servers in
`in_latency_window`. Drivers SHOULD test against the full set of servers in `in_latency_window` and against
`suitable_servers` if possible.

### Topology Type Single

- The single server is always selected.

### Topology Type ReplicaSetNoPrimary

**Reads**

- PRIMARY
  - no server selected
- PRIMARY_PREFERRED
  - Matching tags: select any eligible secondary
  - Non-matching tags: no server selected
- SECONDARY
  - Matching tags: select any eligible secondary
  - Non-matching tags: no server selected
- SECONDARY_PREFERRED
  - Matching tags: select any eligible secondary
  - Non-matching tags: no server selected
- NEAREST
  - Matching tags: select any eligible secondary
  - Non-matching tags: no server selected

**Writes**

- Writes must go to a primary, no server can be selected.

### Topology Type ReplicaSetWithPrimary

**Reads**

- PRIMARY
  - primary is selected **NOTE:** it is an error to provide tags with mode PRIMARY. See "ReadPreference Document
    Validation."
- PRIMARY_PREFERRED
  - Matching tags: primary is selected
  - Non-matching tags: primary is selected
- SECONDARY
  - Matching tags: select any eligible secondary
  - Non-matching tags: no server selected
- SECONDARY_PREFERRED
  - Matching tags: select any eligible secondary
  - Non-matching tags: primary is selected
- NEAREST
  - Matching tags: select any eligible server
  - Non-matching tags: no server selected

**Writes**

- Primary is selected.

### Topology Type Sharded

**Reads**

- Select any mongos.

**Writes**

- Select any mongos.

### Topology Type Unknown

**Reads**

- No server is selected.

**Writes**

- No server is selected.

## Passing ReadPreference to Mongos

While there are no YAML tests for this, drivers are strongly encouraged to test in a way specific to their
implementation that ReadPreference is correctly passed to Mongos in the following scenarios:

- PRIMARY
  - the SecondaryOk wire protocol flag is NOT set
  - $readPreference is NOT used
- PRIMARY_PREFERRED
  - the SecondaryOk wire protocol flag is set
  - $readPreference is used
- SECONDARY
  - the SecondaryOk wire protocol flag is set
  - $readPreference is used
- SECONDARY_PREFERRED
  - the SecondaryOk wire protocol flag is set
  - if `tag_sets` or `hedge` are specified $readPreference is used, otherwise $readPreference is NOT used
- NEAREST
  - the SecondaryOk wire protocol flag is set
  - $readPreference is used

## Random Selection Within Latency Window (single-threaded drivers)

The Server Selection spec mandates that single-threaded drivers select a server at random from the set of suitable
servers that are within the latency window. Drivers implementing the spec SHOULD test their implementations in a
language-specific way to confirm randomness.

For example, the following topology description, operation, and read preference will return a set of three suitable
servers within the latency window:

```
    topology_description:
      type: ReplicaSetWithPrimary
      servers:
      - &secondary_1
        address: b:27017
        avg_rtt_ms: 5
        type: RSSecondary
        tags: {}
      - &secondary_2
        address: c:27017
        avg_rtt_ms: 10
        type: RSSecondary
        tags: {}
      - &primary
        address: a:27017
        avg_rtt_ms: 6
        type: RSPrimary
        tags: {}
    operation: read
    read_preference:
      mode: Nearest
      tags: {}
    in_latency_window:
    - *primary
    - *secondary_1
    - *secondary_2
```

Drivers SHOULD check that their implementation selects one of `primary`, `secondary_1`, and `secondary_2` at random.

## operationCount-based Selection Within Latency Window (multi-threaded or async drivers)

The Server Selection spec mandates that multi-threaded or async drivers select a server from within the latency window
according to their operationCounts. There are YAML tests verifying that drivers implement this selection correctly which
can be found in the `tests/in_window` directory. Multi-threaded or async drivers implementing the spec MUST use them to
test their implementations.

The YAML tests each include some information about the servers within the late ncy window. For each case, the driver
passes this information into whatever function it uses to select from within the window. Because the selection algorithm
relies on randomness, this process MUST be repeated 2000 times. Once the 2000 selections are complete, the runner
tallies up the number of times each server was selected and compares those counts to the expected results included in
the test case. Specifics of the test format and how to run the tests are included in the tests README.

### Prose Test

Multi-threaded and async drivers MUST also implement the following prose test:

1. Configure a sharded cluster with two mongoses. Use a 4.2.9 or newer server version.

2. Enable the following failpoint against exactly one of the mongoses:

   ```
   {
      configureFailPoint: "failCommand",
      mode: { times: 10000 },
      data: {
          failCommands: ["find"],
          blockConnection: true,
          blockTimeMS: 500,
          appName: "loadBalancingTest",
      },
   }
   ```

3. Create a client with both mongoses' addresses in its seed list, appName="loadBalancingTest", and
   localThresholdMS=30000.

   - localThresholdMS is set to a high value to help avoid a single mongos being selected too many times due to a random
     spike in latency in the other mongos.

4. Using CMAP events, ensure the client's connection pools for both mongoses have been saturated, either via setting
   minPoolSize=maxPoolSize or executing operations.

   - This helps reduce any noise introduced by connection establishment latency during the actual server selection
     tests.

5. Start 10 concurrent threads / tasks that each run 10 `findOne` operations with empty filters using that client.

6. Using command monitoring events, assert that fewer than 25% of the CommandStartedEvents occurred on the mongos that
   the failpoint was enabled on.

7. Disable the failpoint.

8. Start 10 concurrent threads / tasks that each run 100 `findOne` operations with empty filters using that client.

9. Using command monitoring events, assert that each mongos was selected roughly 50% of the time (within +/- 10%).

## Application-Provided Server Selector

The Server Selection spec allows drivers to configure registration of a server selector function that filters the list
of suitable servers. Drivers implementing this part of the spec MUST test that:

- The application-provided server selector is executed as part of the server selection process when there is a nonzero
  number of candidate or eligible servers. For example, execute a test against a replica set: Register a server selector
  that selects the suitable server with the highest port number. Execute 10 queries with nearest read preference and,
  using command monitoring, assert that all the operations execute on the member with the highest port number.
