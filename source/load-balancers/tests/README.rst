===========================
Load Balancer Support Tests
===========================

.. contents::

----

Introduction
============

This document describes how drivers should create load balanced clusters for
testing and how tests should be executed for such clusters.

Cluster Setup
=============

Drivers MUST execute tests against a load balanced sharded cluster with two
mongos nodes running on localhost ports 27017 and 27018. The shard and config
servers may run on any free ports. In addition to the sharded cluster, there
MUST be two TCP load balancers operating in round-robin mode: one fronting
both mongos nodes and one fronting a single mongos.

When running tests in Evergreen, drivers MUST add a new task to each MongoDB
5.0+ build variant to test against load balanced clusters. For example, if
the latest released server version is 5.2, there should be load balanced
testing tasks for 5.0, 5.2, and ``latest``.

TODO: Once the work for drivers-evergreen-tools is complete, we should add
notes/links about which config files should be used and the names of the
environment variables that will be used to pass in the LB URIs.

Tests
======

The YAML and JSON files in this directory contain platform-independent tests
written in the `Unified Test Format
<../unified-test-format/unified-test-format.rst>`_. Drivers MUST run the
following test suites against a load balanced cluster:

#. All test suites written in the Unified Test Format
#. Retryable Reads
#. Retryable Writes
#. Change Streams
#. Initial DNS Seedlist Discovery
