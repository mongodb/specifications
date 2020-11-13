======================
Server Selection Tests
======================

This directory contains platform-independent tests that drivers can use
to prove their conformance to the Server Selection spec. The tests
are provided in both YAML and JSON formats, and drivers may test against
whichever format is more convenient for them.

Version
-------

Files in the "specifications" repository have no version scheme. They are not
tied to a MongoDB server version.

Test Format and Use
-------------------

There are two types of tests for the server selection spec, tests for
round trip time (RTT) calculation, and tests for server selection logic.

Drivers should be able to test their server selection logic
without any network I/O, by parsing topology descriptions and read preference
documents from the test files and passing them into driver code. Parts of the
server selection code may need to be mocked or subclassed to achieve this.

RTT Calculation Tests
>>>>>>>>>>>>>>>>>>>>>

These YAML files contain the following keys:

- ``avg_rtt_ms``: a server's previous average RTT, in milliseconds
- ``new_rtt_ms``: a new RTT value for this server, in milliseconds
- ``new_avg_rtt``: this server's newly-calculated average RTT, in milliseconds

For each file, create a server description object initialized with ``avg_rtt_ms``.
Parse ``new_rtt_ms``, and ensure that the new RTT value for the mocked server
description is equal to ``new_avg_rtt``.

If driver architecture doesn't easily allow construction of server description
objects in isolation, unit testing the EWMA algorithm using these inputs
and expected outputs is acceptable.

Server Selection Logic Tests
>>>>>>>>>>>>>>>>>>>>>>>>>>>>

These YAML files contain the following setup for each test:

- ``topology_description``: the state of a mocked cluster
- ``operation``: the kind of operation to perform, either read or write
- ``read_preference``: a read preference document

For each file, create a new TopologyDescription object initialized with the values
from ``topology_description``. Create a ReadPreference object initialized with the
values from ``read_preference``.

Together with "operation", pass the newly-created TopologyDescription and ReadPreference
to server selection, and ensure that it selects the correct subset of servers from
the TopologyDescription. Each YAML file contains a key for these stages of server selection:

- ``suitable_servers``: the set of servers in topology_description that are suitable, as
  per the Server Selection spec, given operation and read_preference
- ``in_latency_window``: the set of suitable_servers that fall within the latency window

Drivers implementing server selection MUST test that their implementation
correctly returns the set of servers in ``in_latency_window``. Drivers SHOULD also test
against ``suitable_servers`` if possible.

Selection Within Latency Window Spec Tests
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

These tests verify that servers select servers from within the latency
window correctly. These tests MUST only be implemented by
multi-threaded or async drivers.

Each YAML file for these tests has the following format:

- ``topology_description``: the state of a mocked cluster

- ``in_window``: array of servers in the latency window that the selected server
  is to be chosen from. Each element will have all of the following fields:

  - ``address``: a unique address identifying this server

  - ``operation_count``: the ``operationCount`` for this server

- ``expected_frequencies``: a document whose keys are the server addresses from the
  ``in_window`` array and values are numbers in [0, 1] indicating the frequency
  at which the server should have been selected.

For each file, pass the information from `in_window` to whatever function is
used to select a server from within the latency window 10000 times, counting how
many times each server is selected.  Once 10000 selections have been made, verify
that each server was selected at a frequency within 0.02 of the frequency
contained in ``expected_frequencies`` for that server. If the expected frequency
for a given server is 1 or 0, then the observed frequency MUST be exactly equal
to the expected one.

Mocking may be required to implement these tests. A mocked topology description
is included in each file for drivers that require a full description to
implement these tests. If a ReadPreference needs to be specified as part of
running these tests, specify one with the default ("primary") mode. The provided
topologies will always be sharded so this should not have an effect on the
results of the test.

Selection Within Latency Window Prose Test
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

Multi-threaded and async drivers MUST also implement the following
prose test:

1. Configure a sharded cluster with two mongoses.

2. Enable the following failpoint against exactly one of the mongoses::

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

3. Create a client with both mongoses' adresses in its seed list,
   appName="loadBalancingTest", and command monitoring enabled.

4. Start 10 concurrent threads / tasks that each run 10 `findOne`
   operations using that client.

5. Assert that fewer than 25% of the CommandStartedEvents occurred on
   the mongos that the failpoint was enabled on.

6. Disable the failpoint.

7. Repeat this test without any failpoints and assert that each mongos
   was selected roughly 50% of the time.
