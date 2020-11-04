=============================
Server Selection -- Test Plan
=============================

:Spec: 103
:Title: Server Selection
:Author: Samantha Ritter
:Advisors: David Golden
:Status: Draft
:Type: Standards
:Last Modified: March 17, 2020

See also the YAML test files and their accompanying README in the "tests"
directory.

.. contents::

--------

ReadPreference Document Validation
==================================

While there are no YAML tests for this section, clients implementing this spec
SHOULD perform validations on ReadPreference documents provided by the user.
Specifically, documents with the following values should raise an error:

  - Mode PRIMARY and non-empty tag set


Calculating Round Trip Time
===========================

Drivers implementing server selection MUST test that RTT values are calculated correctly.
YAML tests for RTT calculations can be found in the "tests" directory and
they test for correctness in the following scenarios:

- first RTT: new average RTT equals measurement
- subsequent measurements: new average RTT is calculated using the new measurement
  and the previous average as described in the spec.

Additionally, drivers SHOULD ensure that their implementations reject negative RTT values.

Lastly, drivers SHOULD ensure that average RTT for a given ServerDescription is reset to 0 if that
server is disconnected (ie a network error occurs during an ``ismaster`` call). Upon reconnect,
the first new RTT value should become the average RTT for this server.

The RTT tests are intentionally simplified to test the implementation of the
EWMA algorithm without imposing any additional conditions on drivers that might
affect architecture.  For some drivers, RTT tests might require mocks; for others,
it might just require unit tests.

Server Selection
================

The following test cases can be found in YAML form in the "tests"
directory. Each test lists a TopologyDescription representing a set of servers,
a ReadPreference document, and sets of servers returned at various stages of
the server selection process. These sets are described below.  Note that it
is not required to test for correctness at every step.

+------------------------+--------------------------------------------------------+
| ``suitable_servers``   | the set of servers matching all server selection logic.|
+------------------------+--------------------------------------------------------+
| ``in_latency_window``  | the subset of ``suitable_servers`` that falls within   |
|                        | the allowable latency window (required).               |
|                        | NOTE: tests use the default localThresholdMS of 15 ms. |
+------------------------+--------------------------------------------------------+

Drivers implementing server selection MUST test that their implementations
correctly return **one** of the servers in ``in_latency_window``. Drivers SHOULD test
against the full set of servers in ``in_latency_window`` and against
``suitable_servers`` if possible.

Topology Type Single
--------------------

- The single server is always selected.


Topology Type ReplicaSetNoPrimary
---------------------------------

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


Topology Type ReplicaSetWithPrimary
-----------------------------------

**Reads**


- PRIMARY

  - primary is selected

      **NOTE:** it is an error to provide tags with mode PRIMARY.
      See "ReadPreference Document Validation."


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


Topology Type Sharded
---------------------

**Reads**

- Select any mongos.


**Writes**

- Select any mongos.


Topology Type Unknown
---------------------

**Reads**

- No server is selected.


**Writes**

- No server is selected.


Passing ReadPreference to Mongos
================================

While there are no YAML tests for this, drivers are strongly encouraged to test
in a way specific to their implementation that ReadPreference is
correctly passed to Mongos in the following scenarios:

- PRIMARY

  - the slaveOK wire protocol flag is NOT set
  - $readPreference is NOT used

- PRIMARY_PREFERRED

  - the slaveOK wire protocol flag is set
  - $readPreference is used

- SECONDARY

  - the slaveOK wire protocol flag is set
  - $readPreference is used

- SECONDARY_PREFERRED

  - the slaveOK wire protocol flag is set
  - if ``tag_sets`` or ``hedge`` are specified $readPreference is used, otherwise $readPreference is NOT used

- NEAREST

  - the slaveOK wire protocol flag is set
  - $readPreference is used


Selection Within Latency Window
===============================

The Server Selection spec mandates that drivers select a server from within the
latency window according to a certain algorithm. There are YAML tests verifying
that drivers implement this algorithm correctly. Drivers implementing the spec
MUST use them test their implementations.

The tests each include some information about the servers within the latency
window. For each case, the driver passes this information into whatever function
it uses to select from within the window. Because the algorithm relies on
randomness, this process MUST be repeated 1000 times. Once the 1000 selections
are complete, the runner tallies up the number of times each server was selected
and compares those counts to the expected results included in the test
case. Specifics of the test format and how to run the tests are included in the
tests README.


Application-Provided Server Selector
====================================

The Server Selection spec allows drivers to configure registration of a server selector
function that filters the list of suitable servers.  Drivers implementing this part
of the spec MUST test that:

- The application-provided server selector is executed as part of the server selection process when
  there is a nonzero number of candidate or eligible servers. For example, execute a test against a replica
  set: Register a server selector that selects the suitable server with the highest port number. Execute 10
  queries with nearest read preference and, using command monitoring, assert that all the operations execute
  on the member with the highest port number.
