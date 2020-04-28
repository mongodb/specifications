===================
Max Staleness Tests
===================

These prose tests supplement the machine-readable YAML tests.

.. contents::

Connection string
=================

Tests of drivers' connection string parsing and validation.

Basic
-----

maxStalenessSeconds is set to 120 from this connection string::

  mongodb://host/?readPreference=secondary&maxStalenessSeconds=120

No maxStalenessSeconds with mode "primary"
------------------------------------------

These connection strings are invalid because the mode is "primary", either
by default or explicitly::

  mongodb://host/?maxStalenessSeconds=120
  mongodb://host/?readPreference=primary&maxStalenessSeconds=120

Specifying "no max staleness" with "-1"
---------------------------------------

A MongoClient with this connection string has no max staleness, the same as
if "maxStalenessSeconds" were omitted from the connection string::

  mongodb://host/?readPreference=secondary&maxStalenessSeconds=-1

This connection string is valid and does not raise an error:

  mongodb://host/?readPreference=primary&maxStalenessSeconds=-1

No validation
-------------

A MongoClient can be initialized with this connection string;
the small maxStalenessSeconds value causes no error initially::

  mongodb://host/?readPreference=secondary&maxStalenessSeconds=1

heartbeatFrequencyMS is configurable
====================================

Server Discovery and Monitoring was updated to accommodate the Max Staleness Spec:
heartbeatFrequencyMS MUST now be configurable in all drivers, not just single-threaded drivers.

Test that a user can set heartbeatFrequencyMS in the connection string::

  mongodb://host/?heartbeatFrequencyMS=500

Test that a client initialized with this string
checks a standalone server roughly twice per second.

Driver Tests
============

Parse lastWriteDate
-------------------

Configure a client with heartbeatFrequencyMS of 500 milliseconds.

Connect to a MongoDB replica set member with maxWireVersion at least 5.
(Only replica set members with maxWireVersion 5 have a lastWriteDate in
the ismaster reply.)

Insert a document and wait one second.

Get the client's ServerDescription for the server.
It must have a non-zero lastWriteDate.
Wait another second. [1]

Insert a document and wait one second.

Get the client's ServerDescription for the server.
The ServerDescription's lastWriteDate must be greater than before,
but less than 10 seconds greater.

(This test is as lenient as possible,
while still testing that the driver parses lastWriteDate
and converts it to an appropriate unit.)

.. [1] This ensures the next insert occurs at least one second after server
selection (another write may have occurred from the noop writer just before
server selection if mongod was configured with periodicNoopIntervalSecs=1).

Absent lastWriteDate
--------------------

Connect to a MongoDB server with maxWireVersion less than 5.
Check that the driver's ServerDescription for this server has no lastWriteDate,
represented with null, zero, or however the driver represents a non-value.

Direct connection to mongos
---------------------------

Initialize a MongoClient with this connection string::

  mongodb://mongos/?readPreference=secondary&maxStalenessSeconds=120

Where "mongos" is the hostname and port
of a mongos server running wire protocol version 5+.
Execute a "findOne" operation.
The MongoClient must include following read preference element with its
"find" command::

  $readPreference: {
      mode: "secondary",
      maxStalenessSeconds: 120
  }

The "maxStalenessSeconds" element must be a BSON int32 or int64 type.

Do the same test with this connection string::

  mongodb://mongos/?readPreference=secondary

The read preference element sent to mongos must omit "maxStalenessSeconds".

Mongos
======

These tests MUST be added to the server code repository,
validating mongos's maxStalenessSeconds implementation.

maxStalenessSeconds and mode "primary"
--------------------------------------

mongos MUST reject a read with::

  $readPreference: {mode: "primary", maxStalenessSeconds: 120}

Validation
----------

mongos MUST reject a read with ``maxStalenessSeconds`` that is not an int32 or int64.

maxStalenessSeconds too small
-----------------------------

The minimum value of maxStalenessSeconds is 90. mongos MUST reject a read with::

  $readPreference: {mode: "secondary", maxStalenessSeconds: 89}

The error code MUST be 160.
