===========================
Wire Compression in Drivers
===========================


:Title: Wire Compression In Drivers
:Author: Hannes Magnússon
:Advisory Group: Jonathan Reams, Christian Kvalheim, Ross Lawley
:Approvers: David Golden (2017-04-26),
            Christian Kvalheim (2017-04-27),
            Jeff Yemin (2017-04-27),
            Bernie Hackett (2017-05-09),
            Dana Groff (2017-05-02) 
:Status: Accepted
:Type: Standards
:Last Modified: 2021-04-06
:Minimum Server Version: 3.4
:Version: 1.3


Abstract
========

This specification describes how to implement Wire Protocol Compression between
MongoDB drivers and mongo[d|s].

Compression is achieved through a new bi-directional wire protocol opcode,
referred to as OP_COMPRESSED.

Server side compressor support is checked during the initial MongoDB Handshake,
and is compatible with all historical versions of MongoDB.  If a client detects
a compatible compressor it will use the compressor for all valid requests.


META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.



Terms
=====

*Compressor* - A compression algorithm.  There are currently three supported
algorithms: snappy, zlib, and zstd.

Specification
=============

MongoDB Handshake Amendment
---------------------------

The `MongoDB Handshake Protocol
<https://github.com/mongodb/specifications/blob/master/source/mongodb-handshake/handshake.rst>`_
describes an argument passed to the handshake command, ``client``.  This specification adds
an additional argument, ``compression``, that SHOULD be provided to the handshake command if
a driver supports wire compression.

The value of this argument is an array of supported compressors.

Example::

    {
        hello: 1,
        client: {}, /* See MongoDB Handshake */
        compression: ["snappy", "zlib", "zstd"]
    }

When no compression is enabled on the client, drivers SHOULD send an empty
compression argument.

Example::

    {
        hello: 1,
        client: {}, /* See MongoDB Handshake */
        compression: []
    }



Clients that want to compress their messages need to send a list of the
algorithms - in the order they are specified in the client configuration - that
they are willing to support to the server during the initial handshake call. For
example, a client wishing to compress with the snappy algorithm, should send::

    { hello: 1, ... , compression: [ "snappy" ] }

The server will respond with the intersection of its list of supported
compressors and the client's. For example, if the server had both snappy and
zlib enabled and the client requested snappy, it would respond with::

    { ... , compression: [ "snappy" ], ok: 1 }

If the client included both snappy and zlib, the server would respond with
something like::

    { ... , compression: [ "snappy", "zlib" ], ok: 1 }

If the server has no compression algorithms in common with the client, it sends
back a handshake response without a compression field. Clients MAY issue a log
level event to inform the user, but MUST NOT error.

When MongoDB server receives a compressor it can support it MAY reply to any
and all requests using the selected compressor, including the reply of the
initial MongoDB Handshake.
As each OP_COMPRESSED message contains the compressor ID, clients MUST NOT
assume which compressor each message uses, but MUST decompress the message
using the compressor identified in the OP_COMPRESSED opcode header.

When compressing, clients MUST use the first compressor in the client's
configured compressors list that is also in the servers list.


Connection String Options
-------------------------

Two new connection string options:

compressors
~~~~~~~~~~~
Comma separated list of compressors the client should present to the server.
Unknown compressors MUST yield a warning, as per the Connection String
specification, and MUST NOT be included in the handshake.
By default, no compressor is configured and thus compression will not be used.
When multiple compressors are provided, the list should be treated as a
priority ordered list of compressors to use, with highest priority given to the
first compressor in the list, and lowest priority to the last compressor in the
list.

Example::

    mongodb://localhost/?compressors=zstd,snappy,zlib
    

zlibCompressionLevel
~~~~~~~~~~~~~~~~~~~~
Integer value from ``-1`` - ``9``. This configuration option only applies to
the zlib compressor. When zlib is not one of the compressors enumerated by the
``compressors`` configuration option then providing this option has no meaning,
but clients SHOULD NOT issue a warning.

+-------+---------------------------------+
| -1    | Default Compression (usually 6) |
+-------+---------------------------------+
| 0     | No compression                  |
+-------+---------------------------------+
| 1     | Best Speed                      |
+-------+---------------------------------+
| 9     | Best Compression                |
+-------+---------------------------------+

Note that this value only applies to the client side compression level, not the
response.


OP_COMPRESSED
-------------

The new opcode, called OP_COMPRESSED, has the following structure::

    struct OP_COMPRESSED {
        struct MsgHeader {
            int32  messageLength;
            int32  requestID;
            int32  responseTo;
            int32  opCode = 2012;
        };
        int32_t  originalOpcode;
        int32_t  uncompressedSize;
        uint8_t  compressorId;
        char    *compressedMessage;
    };


+-------------------+--------------------------------------------------------------------------+
| Field             | Description                                                              |
+===================+==========================================================================+
| originalOpcode    | Contains the value of the wrapped opcode.                                |
+-------------------+--------------------------------------------------------------------------+
| uncompressedSize  | The size of the deflated compressedMessage, which excludes the MsgHeader |
+-------------------+--------------------------------------------------------------------------+
| compressorId      | The ID of the compressor that compressed the message                     |
+-------------------+--------------------------------------------------------------------------+
| compressedMessage | The opcode itself, excluding the MsgHeader                               |
+-------------------+--------------------------------------------------------------------------+

Compressor IDs
--------------

Each compressor is assigned a predefined compressor ID.

+-----------------+-----------------+--------------------------------------------------------+
| compressorId    | Handshake Value |  Description                                           |
+=================+=================+========================================================+
| 0               | noop            | The content of the message is uncompressed.            |
|                 |                 | This is realistically only used for testing.           |
+-----------------+-----------------+--------------------------------------------------------+
| 1               | snappy          | The content of the message is compressed using snappy. |
+-----------------+-----------------+--------------------------------------------------------+
| 2               | zlib            | The content of the message is compressed using zlib.   |
+-----------------+-----------------+--------------------------------------------------------+
| 3               | zstd            | The content of the message is compressed using zstd.   |
+-----------------+-----------------+--------------------------------------------------------+
| 4-255           | reserved        | Reserved for future use.                               |
+-----------------+-----------------+--------------------------------------------------------+


Compressible messages
---------------------

Any opcode can be compressed and wrapped in an ``OP_COMPRESSED`` header.
The ``OP_COMPRESSED`` is strictly a wire protocol without regards to what
opcode it wraps, be it ``OP_QUERY``, ``OP_REPLY``, ``OP_MSG`` or any other
future or past opcode.
The ``compressedMessage`` contains the original opcode, excluding the standard
``MsgHeader``. The ``originalOpcode`` value therefore effectively replaces the
standard ``MsgHeader`` of the compressed opcode.

There is no guarantee that a response will be compressed even though
compression was negotiated for in the handshake. Clients MUST be able to parse
both compressed and uncompressed responses to both compressed and uncompressed
requests.

MongoDB 3.4 will always reply with a compressed response when compression has
been negotiated, but future versions may not.

A client MAY choose to implement compression for only ``OP_QUERY``,
``OP_REPLY``, and ``OP_MSG``, and perhaps for future opcodes, but not to
implement it for ``OP_INSERT``, ``OP_UPDATE``, ``OP_DELETE``, ``OP_GETMORE``,
and ``OP_KILLCURSORS``.

Note that certain messages, such as authentication commands, MUST NOT be
compressed. All other messages MUST be compressed, when compression has been
negotiated and the driver has implemented compression for the opcode in use.


Messages not allowed to be compressed
-------------------------------------

In efforts to mitigate against current and previous attacks, certain messages
MUST NOT be compressed, such as authentication requests.

Messages using the following commands MUST NOT be compressed:

* hello
* legacy hello (see `MongoDB Handshake Protocol <https://github.com/mongodb/specifications/blob/master/source/mongodb-handshake/handshake.rst>`_ for details)
* saslStart
* saslContinue
* getnonce
* authenticate
* createUser
* updateUser
* copydbSaslStart
* copydbgetnonce
* copydb


Test Plan
=========

There are no automated tests accompanying this specification, instead the
following is a description of test scenarios clients should implement.

In general, after implementing this functionality and the test cases, running
the traditional client test suite against a server with compression enabled,
and ensuring the test suite is configured to provide a valid compressor as part
of the connection string, is a good idea. MongoDB-supported drivers MUST add
such variant to their CI environment.


The following cases assume a standalone MongoDB 3.4 (or later) node configured
with::

   mongod --networkMessageCompressors "snappy" -vvv

Create an example application which connects to a provided connection string,
runs ``ping: 1``, and then quits the program normally.

Connection strings, and results
-------------------------------

* mongodb://localhost:27017/?compressors=snappy

  mongod should have logged the following (the exact log output may differ depending on server version)::

   {"t":{"$date":"2021-04-08T13:28:38.885-06:00"},"s":"I",  "c":"NETWORK",  "id":22943,   "ctx":"listener","msg":"Connection accepted","attr":{"remote":"127.0.0.1:50635","uuid":"03961627-aec7-4543-8a17-9690f87273a6","connectionId":2,"connectionCount":1}}
   {"t":{"$date":"2021-04-08T13:28:38.886-06:00"},"s":"D3", "c":"EXECUTOR", "id":22983,   "ctx":"listener","msg":"Starting new executor thread in passthrough mode"}
   {"t":{"$date":"2021-04-08T13:28:38.887-06:00"},"s":"D3", "c":"-",        "id":5127801, "ctx":"thread27","msg":"Setting the Client","attr":{"client":"conn2"}}
   {"t":{"$date":"2021-04-08T13:28:38.887-06:00"},"s":"D2", "c":"COMMAND",  "id":21965,   "ctx":"conn2","msg":"About to run the command","attr":{"db":"admin","commandArgs":{"hello":1,"client":{"application":{"name":"MongoDB Shell"},"driver":{"name":"MongoDB Internal Client","version":"4.9.0-alpha7-555-g623aa8f"},"os":{"type":"Darwin","name":"Mac OS X","architecture":"x86_64","version":"19.6.0"}},"compression":["snappy"],"apiVersion":"1","apiStrict":true,"$db":"admin"}}}
   {"t":{"$date":"2021-04-08T13:28:38.888-06:00"},"s":"I",  "c":"NETWORK",  "id":51800,   "ctx":"conn2","msg":"client metadata","attr":{"remote":"127.0.0.1:50635","client":"conn2","doc":{"application":{"name":"MongoDB Shell"},"driver":{"name":"MongoDB Internal Client","version":"4.9.0-alpha7-555-g623aa8f"},"os":{"type":"Darwin","name":"Mac OS X","architecture":"x86_64","version":"19.6.0"}}}}
   {"t":{"$date":"2021-04-08T13:28:38.889-06:00"},"s":"D3", "c":"NETWORK",  "id":22934,   "ctx":"conn2","msg":"Starting server-side compression negotiation"}
   {"t":{"$date":"2021-04-08T13:28:38.889-06:00"},"s":"D3", "c":"NETWORK",  "id":22937,   "ctx":"conn2","msg":"supported compressor","attr":{"compressor":"snappy"}}
   {"t":{"$date":"2021-04-08T13:28:38.889-06:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn2","msg":"Slow query","attr":{"type":"command","ns":"admin.$cmd","appName":"MongoDB Shell","command":{"hello":1,"client":{"application":{"name":"MongoDB Shell"},"driver":{"name":"MongoDB Internal Client","version":"4.9.0-alpha7-555-g623aa8f"},"os":{"type":"Darwin","name":"Mac OS X","architecture":"x86_64","version":"19.6.0"}},"compression":["snappy"],"apiVersion":"1","apiStrict":true,"$db":"admin"},"numYields":0,"reslen":351,"locks":{},"remote":"127.0.0.1:50635","protocol":"op_query","durationMillis":1}}
   {"t":{"$date":"2021-04-08T13:28:38.890-06:00"},"s":"D2", "c":"QUERY",    "id":22783,   "ctx":"conn2","msg":"Received interrupt request for unknown op","attr":{"opId":596,"knownOps":[]}}
   {"t":{"$date":"2021-04-08T13:28:38.890-06:00"},"s":"D3", "c":"-",        "id":5127803, "ctx":"conn2","msg":"Released the Client","attr":{"client":"conn2"}}
   {"t":{"$date":"2021-04-08T13:28:38.890-06:00"},"s":"D3", "c":"-",        "id":5127801, "ctx":"conn2","msg":"Setting the Client","attr":{"client":"conn2"}}
   {"t":{"$date":"2021-04-08T13:28:38.891-06:00"},"s":"D3", "c":"NETWORK",  "id":22927,   "ctx":"conn2","msg":"Decompressing message","attr":{"compressor":"snappy"}}
   {"t":{"$date":"2021-04-08T13:28:38.891-06:00"},"s":"D2", "c":"COMMAND",  "id":21965,   "ctx":"conn2","msg":"About to run the command","attr":{"db":"admin","commandArgs":{"whatsmyuri":1,"apiStrict":false,"$db":"admin","apiVersion":"1"}}}
   {"t":{"$date":"2021-04-08T13:28:38.892-06:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn2","msg":"Slow query","attr":{"type":"command","ns":"admin.$cmd","appName":"MongoDB Shell","command":{"whatsmyuri":1,"apiStrict":false,"$db":"admin","apiVersion":"1"},"numYields":0,"reslen":63,"locks":{},"remote":"127.0.0.1:50635","protocol":"op_msg","durationMillis":0}}
   {"t":{"$date":"2021-04-08T13:28:38.892-06:00"},"s":"D2", "c":"QUERY",    "id":22783,   "ctx":"conn2","msg":"Received interrupt request for unknown op","attr":{"opId":597,"knownOps":[]}}
   {"t":{"$date":"2021-04-08T13:28:38.892-06:00"},"s":"D3", "c":"NETWORK",  "id":22925,   "ctx":"conn2","msg":"Compressing message","attr":{"compressor":"snappy"}}
   {"t":{"$date":"2021-04-08T13:28:38.893-06:00"},"s":"D3", "c":"-",        "id":5127803, "ctx":"conn2","msg":"Released the Client","attr":{"client":"conn2"}}
   {"t":{"$date":"2021-04-08T13:28:38.893-06:00"},"s":"D3", "c":"-",        "id":5127801, "ctx":"conn2","msg":"Setting the Client","attr":{"client":"conn2"}}
   {"t":{"$date":"2021-04-08T13:28:38.895-06:00"},"s":"D3", "c":"NETWORK",  "id":22927,   "ctx":"conn2","msg":"Decompressing message","attr":{"compressor":"snappy"}}
   {"t":{"$date":"2021-04-08T13:28:38.895-06:00"},"s":"D2", "c":"COMMAND",  "id":21965,   "ctx":"conn2","msg":"About to run the command","attr":{"db":"admin","commandArgs":{"buildinfo":1.0,"apiStrict":false,"$db":"admin","apiVersion":"1"}}}
   {"t":{"$date":"2021-04-08T13:28:38.896-06:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn2","msg":"Slow query","attr":{"type":"command","ns":"admin.$cmd","appName":"MongoDB Shell","command":{"buildinfo":1.0,"apiStrict":false,"$db":"admin","apiVersion":"1"},"numYields":0,"reslen":2606,"locks":{},"remote":"127.0.0.1:50635","protocol":"op_msg","durationMillis":0}}
   {"t":{"$date":"2021-04-08T13:28:38.896-06:00"},"s":"D2", "c":"QUERY",    "id":22783,   "ctx":"conn2","msg":"Received interrupt request for unknown op","attr":{"opId":598,"knownOps":[]}}
   {"t":{"$date":"2021-04-08T13:28:38.897-06:00"},"s":"D3", "c":"NETWORK",  "id":22925,   "ctx":"conn2","msg":"Compressing message","attr":{"compressor":"snappy"}}
   {"t":{"$date":"2021-04-08T13:28:38.897-06:00"},"s":"D3", "c":"-",        "id":5127803, "ctx":"conn2","msg":"Released the Client","attr":{"client":"conn2"}}
   {"t":{"$date":"2021-04-08T13:28:38.897-06:00"},"s":"D3", "c":"-",        "id":5127801, "ctx":"conn2","msg":"Setting the Client","attr":{"client":"conn2"}}
   {"t":{"$date":"2021-04-08T13:28:38.898-06:00"},"s":"D3", "c":"NETWORK",  "id":22927,   "ctx":"conn2","msg":"Decompressing message","attr":{"compressor":"snappy"}}
   {"t":{"$date":"2021-04-08T13:28:38.899-06:00"},"s":"D2", "c":"COMMAND",  "id":21965,   "ctx":"conn2","msg":"About to run the command","attr":{"db":"admin","commandArgs":{"endSessions":[{"id":{"$uuid":"c4866af5-ed6b-4f01-808b-51a3f8aaaa08"}}],"$db":"admin","apiVersion":"1","apiStrict":true}}}
   {"t":{"$date":"2021-04-08T13:28:38.899-06:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn2","msg":"Slow query","attr":{"type":"command","ns":"admin.$cmd","appName":"MongoDB Shell","command":{"endSessions":[{"id":{"$uuid":"c4866af5-ed6b-4f01-808b-51a3f8aaaa08"}}],"$db":"admin","apiVersion":"1","apiStrict":true},"numYields":0,"reslen":38,"locks":{},"remote":"127.0.0.1:50635","protocol":"op_msg","durationMillis":0}}
   {"t":{"$date":"2021-04-08T13:28:38.900-06:00"},"s":"D2", "c":"QUERY",    "id":22783,   "ctx":"conn2","msg":"Received interrupt request for unknown op","attr":{"opId":599,"knownOps":[]}}
   {"t":{"$date":"2021-04-08T13:28:38.900-06:00"},"s":"D3", "c":"NETWORK",  "id":22925,   "ctx":"conn2","msg":"Compressing message","attr":{"compressor":"snappy"}}
   {"t":{"$date":"2021-04-08T13:28:38.900-06:00"},"s":"D3", "c":"-",        "id":5127803, "ctx":"conn2","msg":"Released the Client","attr":{"client":"conn2"}}
   {"t":{"$date":"2021-04-08T13:28:38.901-06:00"},"s":"D3", "c":"-",        "id":5127801, "ctx":"conn2","msg":"Setting the Client","attr":{"client":"conn2"}}
   {"t":{"$date":"2021-04-08T13:28:38.901-06:00"},"s":"D2", "c":"NETWORK",  "id":22986,   "ctx":"conn2","msg":"Session from remote encountered a network error during SourceMessage","attr":{"remote":"127.0.0.1:50635","error":{"code":6,"codeName":"HostUnreachable","errmsg":"Connection closed by peer"}}}
   {"t":{"$date":"2021-04-08T13:28:38.902-06:00"},"s":"D1", "c":"-",        "id":23074,   "ctx":"conn2","msg":"User assertion","attr":{"error":"HostUnreachable: Connection closed by peer","file":"src/mongo/transport/service_state_machine.cpp","line":410}}
   {"t":{"$date":"2021-04-08T13:28:38.902-06:00"},"s":"W",  "c":"EXECUTOR", "id":4910400, "ctx":"conn2","msg":"Terminating session due to error","attr":{"error":{"code":6,"codeName":"HostUnreachable","errmsg":"Connection closed by peer"}}}
   {"t":{"$date":"2021-04-08T13:28:38.902-06:00"},"s":"I",  "c":"NETWORK",  "id":5127900, "ctx":"conn2","msg":"Ending session","attr":{"error":{"code":6,"codeName":"HostUnreachable","errmsg":"Connection closed by peer"}}}
   {"t":{"$date":"2021-04-08T13:28:38.903-06:00"},"s":"I",  "c":"NETWORK",  "id":22944,   "ctx":"conn2","msg":"Connection ended","attr":{"remote":"127.0.0.1:50635","uuid":"03961627-aec7-4543-8a17-9690f87273a6","connectionId":2,"connectionCount":0}}
   {"t":{"$date":"2021-04-08T13:28:38.903-06:00"},"s":"D3", "c":"-",        "id":5127803, "ctx":"conn2","msg":"Released the Client","attr":{"client":"conn2"}}

  The result of the program should have been::

   { "ok" : 1 }


* mongodb://localhost:27017/?compressors=snoopy

  mongod should have logged the following::

   {"t":{"$date":"2021-04-20T09:57:26.823-06:00"},"s":"D2", "c":"COMMAND",  "id":21965,   "ctx":"conn5","msg":"About to run the command","attr":{"db":"admin","commandArgs":{"hello":1,"client":{"driver":{"name":"mongo-csharp-driver","version":"2.12.2.0"},"os":{"type":"macOS","name":"Darwin 19.6.0 Darwin Kernel Version 19.6.0: Tue Jan 12 22:13:05 PST 2021; root:xnu-6153.141.16~1/RELEASE_X86_64","architecture":"x86_64","version":"19.6.0"},"platform":".NET 5.0.3"},"compression":[],"$readPreference":{"mode":"secondaryPreferred"},"$db":"admin"}}}
   {"t":{"$date":"2021-04-20T09:57:26.823-06:00"},"s":"I",  "c":"NETWORK",  "id":51800,   "ctx":"conn5","msg":"client metadata","attr":{"remote":"127.0.0.1:54372","client":"conn5","doc":{"driver":{"name":"mongo-csharp-driver","version":"2.12.2.0"},"os":{"type":"macOS","name":"Darwin 19.6.0 Darwin Kernel Version 19.6.0: Tue Jan 12 22:13:05 PST 2021; root:xnu-6153.141.16~1/RELEASE_X86_64","architecture":"x86_64","version":"19.6.0"},"platform":".NET 5.0.3"}}}
   {"t":{"$date":"2021-04-20T09:57:26.824-06:00"},"s":"D3", "c":"NETWORK",  "id":22934,   "ctx":"conn5","msg":"Starting server-side compression negotiation"}
   {"t":{"$date":"2021-04-20T09:57:26.824-06:00"},"s":"D3", "c":"NETWORK",  "id":22936,   "ctx":"conn5","msg":"No compressors provided"}
   {"t":{"$date":"2021-04-20T09:57:26.825-06:00"},"s":"I",  "c":"COMMAND",  "id":51803,   "ctx":"conn5","msg":"Slow query","attr":{"type":"command","ns":"admin.$cmd","command":{"hello":1,"client":{"driver":{"name":"mongo-csharp-driver","version":"2.12.2.0"},"os":{"type":"macOS","name":"Darwin 19.6.0 Darwin Kernel Version 19.6.0: Tue Jan 12 22:13:05 PST 2021; root:xnu-6153.141.16~1/RELEASE_X86_64","architecture":"x86_64","version":"19.6.0"},"platform":".NET 5.0.3"},"compression":[],"$readPreference":{"mode":"secondaryPreferred"},"$db":"admin"},"numYields":0,"reslen":319,"locks":{},"remote":"127.0.0.1:54372","protocol":"op_query","durationMillis":1}}

  e.g., empty compression: [] array. No operations should have been compressed.

  The results of the program should have been::

   WARNING: Unsupported compressor: 'snoopy'
   { "ok" : 1 }


* mongodb://localhost:27017/?compressors=snappy,zlib

  mongod should have logged the following::

   {"t":{"$date":"2021-04-08T13:28:38.898-06:00"},"s":"D3", "c":"NETWORK",  "id":22927,   "ctx":"conn2","msg":"Decompressing message","attr":{"compressor":"snappy"}}

  The results of the program should have been::

   { "ok" : 1 }


* mongodb://localhost:27017/?compressors=zlib,snappy

  mongod should have logged the following::

   {"t":{"$date":"2021-04-08T13:28:38.898-06:00"},"s":"D3", "c":"NETWORK",  "id":22927,   "ctx":"conn2","msg":"Decompressing message","attr":{"compressor":"zlib"}}

  The results of the program should have been::

   { "ok" : 1 }

* Create example program that authenticates to the server using SCRAM-SHA-1,
  then creates another user (MONGODB-CR), then runs hello followed with
  serverStatus.
* Reconnect to the same server using the created MONGODB-CR credentials.
  Observe that the only command that was decompressed on the server was
  ``serverStatus``, while the server replied with OP_COMPRESSED for at least
  the serverStatus command.






Motivation For Change
=====================

Drivers provide the canonical interface to MongoDB. Most tools for MongoDB are
written with the aid of MongoDB drivers. There exist a lot of tools for MongoDB
that import massive datasets which could stand to gain a lot from compression.
Even day-to-day applications stand to gain from reduced bandwidth utilization
at low cpu costs, especially when doing large reads off the network.

Not all use cases fit compression, but we will allow users to decide if wire
compression is right for them.


Design rationale
================

Snappy has minimal cost and provides a reasonable compression ratio, but it is
not expected to be available for all languages MongoDB Drivers support.
Supporting zlib is therefore important to the ecosystem, but for languages that
do support snappy we expected it to be the default choice.  While snappy has no
knobs to tune, zlib does have support for specifying the compression level
(tuned from speed to compression). As we don’t anticipate adding support for
compression libraries with complex knobs to tune this specification has opted
not to define a complex configuration structure and only define the currently
relevant ``zlibCompressionLevel``. When other compression libraries are
supported, adding support for configuring that library (if any is needed)
should be handled on a case by case basis.

More recently, the MongoDB server added Zstandard (zstd) support for another
modern alternative to zlib.


Backwards Compatibility
=======================

The new argument provided to the MongoDB Handshake has no backwards compatible
implications as servers that do not expect it will simply ignore it.  This
means a server will therefore never reply with a list of acceptable compressors
which in turns means a client CANNOT use the OP_COMPRESSED opcode.


Reference Implementation
========================

* `mongoc <https://jira.mongodb.org/browse/CDRIVER-2116>`_


Future Work
===========

Possible future improvements include defining an API to determine compressor
and configuration per operation, rather than needing to create two different
client pools, one for compression and one without, when the user is expecting
only needing to (not) compress very few operations.



Q & A
=====
* Statistics?
   * See `serverStatus
     <https://docs.mongodb.com/manual/reference/command/serverStatus/>`_ in the
     server

* How to try this/enable it?
   * mongod --networkMessageCompressors "snappy"

* The server MAY reply with compressed data even if the request was not compressed?
   * Yes, and this is in fact the behaviour of MongoDB 3.4

* Can drivers compress the initial MongoDB Handshake/hello request?
   * No.

* Can the server reply to the MongoDB Handshake/hello compressed?
   * Yes, yes it can. Be aware it is completely acceptable for the server to
     use compression for any and all replies, using any supported
     compressor, when the client announced support for compression - this
     includes the reply to the actual MongoDB Handshake/hello where the
     support was announced.

* This is billed a MongoDB 3.6 feature -- but I hear it works with MongoDB3.4?
   * Yes, it does. All MongoDB versions support the ``compression`` argument
     to the initial handshake and all MongoDB versions will reply with an intersection
     of compressors it supports. This works even with MongoDB 3.0, as it
     will not reply with any compressors. It also works with MongoDB 3.4
     which will reply with ``snappy`` if it was part of the driver's list.
     MongoDB 3.6 will likely include zlib support.

* Which compressors are currently supported?
   * MongoDB 3.4 supports ``snappy``
   * MongoDB 3.6 supports ``snappy`` and ``zlib``
   * MongoDB 4.2 supports ``snappy``, ``zlib``, and ``zstd``

* My language supports xyz compressor, should I announce them all in the handshake?
   * No. But you are allowed to if you really want to make sure you can use
     that compressor with MongoDB 42 and your current driver versions.

* My language does not support xzy compressor. What do I do?
   * That is OK. You don’t have to support xyz.

* No MongoDB supported compressors are available for my language
   * That is OK. You don’t have to support compressors you can’t support.
     All it means is you can’t compress the request, and since you never
     declared support for any compressor, you won’t be served with
     compressed responses either.

* Why did the server not support zlib in MongoDB 3.4?
   * Snappy was selected for its very low performance hit, while giving
     reasonable compression, resulting in quite significant bandwidth
     reduction.  Zlib characteristics are slightly different out-of-the-box
     and did not make sense for the initial goal of reducing bandwidth
     between replica set nodes.

* If snappy is preferable to zlib, why add support for zlib in MongoDB 3.6?
   * Zlib is available on every platform known to man. Snappy is not. Having
     zlib support makes sense for client traffic, which could originate on
     any type of platform, which may or may not support snappy.



Changelog
=========

+------------+--------------------------------------------------------+
| 2021-04-06 | v1.3 Use 'hello' command                               |
+------------+--------------------------------------------------------+
| 2019-05-13 | v1.2 Add zstd as supported compression algorithm       |
+------------+--------------------------------------------------------+
| 2017-06-13 | v1.1 Don't require clients to implement legacy opcodes |
+------------+--------------------------------------------------------+
| 2017-05-10 | v1.0 Initial commit                                    |
+------------+--------------------------------------------------------+
