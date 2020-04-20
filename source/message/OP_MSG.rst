======
OP_MSG
======


:Title: One opcode to rule them all
:Author: Hannes Magnússon
:Advisory Group: \A. Jesse Jiryu Davis, Jeremy Mikola, Mathias Stearn, Robert Stam
:Approvers: Bernie Hackett, David Golden, Jeff Yemin, Matt broadstone
:Informed: Bryan Reinero, Chris Hendel, drivers@
:Status: Approved
:Type: Standards
:Last Modified: 2017-11-12
:Minimum Server Version: 3.6
:Version: 1.1



.. contents::


.. This RST artwork improves the readability of the rendered document

|
|
|

Abstract
========

``OP_MSG`` is a bi-directional wire protocol opcode introduced in MongoDB 3.6
with the goal of replacing most existing opcodes, merging their use into one
extendable opcode.

META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.





Specification
=============


Usage
-----

``OP_MSG`` is only available in MongoDB 3.6 (``maxWireVersion >= 6``) and later.
MongoDB drivers MUST continue to perform the MongoDB Handshake using ``OP_QUERY``
to determine if the node supports ``OP_MSG``.

If the node supports ``OP_MSG``, any and all messages MUST use ``OP_MSG``,
optionally compressed with ``OP_COMPRESSED``.



.. This RST artwork improves the readability of the rendered document

|
|
|

OP_MSG
------

Types used in this document

============= =============================================================
Type          Meaning
============= =============================================================
document      A BSON document
------------- -------------------------------------------------------------
cstring       NULL terminated string
------------- -------------------------------------------------------------
int32         4 bytes (32-bit signed integer, two's complement)
------------- -------------------------------------------------------------
uint8         1 byte  (8-bit unsigned integer)
------------- -------------------------------------------------------------
uint32        4 bytes (32-bit unsigned integer)
------------- -------------------------------------------------------------
union         One of the listed members
============= =============================================================

Elements inside brackets (``[`` ``]``) are optional parts of the message.

* Zero or more instances: ``*``
* One or more instances: ``+``

The new opcode, called ``OP_MSG``, has the following structure:

.. code:: c

    struct Section {
        uint8 payloadType;
        union payload {
            document  document; // payloadType == 0
            struct sequence { // payloadType == 1
                int32      size;
                cstring    identifier;
                document*  documents;
            };
        };
    };

    struct OP_MSG {
        struct MsgHeader {
            int32  messageLength;
            int32  requestID;
            int32  responseTo;
            int32  opCode = 2013;
        };
        uint32      flagBits;
        Section+    sections;
        [uint32     checksum;]
    };


Each ``OP_MSG`` MUST NOT exceed the ``maxMessageSizeBytes`` as configured by
the MongoDB Handshake.

Each ``OP_MSG`` MUST have one section with ``Payload Type 0``, and zero or more
``Payload Type 1``. Bulk writes SHOULD use ``Payload Type 1``, and MUST do so
when the batch contains more than one entry.

Sections may exist in any order. Each ``OP_MSG`` MAY contain a checksum, and
MUST set the relevant `flagBits` when that field is included.


==================== ========================================================
Field                Description
==================== ========================================================
flagBits             Network level flags, such as signaling recipient that
                     another message is incoming without any other actions
                     in the meantime, and availability of message checksums
-------------------- --------------------------------------------------------
sections             An array of one or more sections
-------------------- --------------------------------------------------------
checksum             crc32c message checksum. When present, the appropriate
                     flag MUST be set in the flagBits.
==================== ========================================================






.. This RST artwork improves the readability of the rendered document

|
|
|

flagBits
~~~~~~~~

flagBits contains a bit vector of specialized network flags.  The low 16 bits
declare what the current message contains, and what the expectations of the
recipient are.  The high 16 bits are designed to declare optional attributes of
the current message and expectations of the recipient.

All unused bits MUST be set to 0.

Clients MUST error if any unsupported or undefined required bits are set to 1
and MUST ignore all undefined optional bits.

The currently defined flags are:

===== ==================== ========= ========== =========================== 
Bit   Name                 Request   Response   Description
----- -------------------- --------- ---------- --------------------------- 
0     checksumPresent         x         x       Checksum present
----- -------------------- --------- ---------- --------------------------- 
1     moreToCome              x         x       Sender will send another
                                                message and is not prepared
                                                for overlapping messages
----- -------------------- --------- ---------- --------------------------- 
16    exhaustAllowed          x                 Client is prepared for
                                                multiple replies (using the
                                                moreToCome bit) to this
                                                request
===== ==================== ========= ========== =========================== 


checksumPresent
~~~~~~~~~~~~~~~

This is a reserved field for future support of crc32c checksums.


moreToCome
~~~~~~~~~~

The ``OP_MSG`` message is essentially a request-response protocol, one message
per turn. However, setting the ``moreToCome`` flag indicates to the recipient that
the sender is not ready to give up its turn and will send another message.


moreToCome On Requests
~~~~~~~~~~~~~~~~~~~~~~

When the ``moreToCome`` flag is set on a request it signals to the recipient that
the sender does not want to know the outcome of the message. There is no
response to a request where ``moreToCome`` has been set. Clients doing
unacknowledged writes MUST set the ``moreToCome`` flag, and MUST set the
writeConcern to ``w=0``.

If, during the processing of a ``moreToCome`` flagged write request, a server
discovers that it is no longer primary, then the server will close the
connection. All other errors during processing will be silently dropped, and
will not result in the connection being closed.


moreToCome On Responses
~~~~~~~~~~~~~~~~~~~~~~~

When the ``moreToCome`` flag is set on a response it signals to the recipient
that the sender will send additional responses on the connection. The recipient
MUST continue to read responses until it reads a response with the ``moreToCome``
flag not set, and MUST NOT send any more requests on this connection until
it reads a response with the ``moreToCome`` flag not set. The client MUST
either consume all messages with the ``moreToCome`` flag set or close the connection.

When the server sends responses with the ``moreToCome`` flag set,
each of these responses will have a unique ``messageId``, and the
``responseTo`` field of every follow-up response will be the ``messageId`` of
the previous response.

The client MUST be prepared to receive a response without ``moreToCome`` set
prior to completing iteration of a cursor, even if an earlier response for
the same cursor had the ``moreToCome`` flag set. To continue iterating such a cursor,
the client MUST issue an explicit ``getMore`` request.


exhaustAllowed
~~~~~~~~~~~~~~

Setting this flag on a request indicates to the recipient that the sender
is prepared to handle multiple replies (using the ``moreToCome`` bit) to this
request. The server will never produce replies with the ``moreToCome`` bit set
unless the request has the ``exhaustAllowed`` bit set.

Setting the ``exhaustAllowed`` bit on a request does not guarantee that the
responses will have the ``moreToCome`` bit set.

MongoDB server only handles the ``exhaustAllowed`` bit on the following
operations. A driver MUST NOT set the ``exhaustAllowed`` bit on other operations.

============== ============================================================
Operation      Minimum MongoDB Version
============== ============================================================
getMore        4.2
-------------- ------------------------------------------------------------
isMaster       4.4 (discoverable via topologyVersion)
============== ============================================================


.. This RST artwork improves the readability of the rendered document

|
|
|

sections
~~~~~~~~

Each message contains one or more sections. A section is composed of an
uint8 which determines the payload's type, and a separate payload field. The
payload size for payload type 0 and 1 is determined by the first 4 bytes of
the payload field (includes the 4 bytes holding the size but not the payload type).


========= ================================================================= 
Field     Description
--------- ----------------------------------------------------------------- 
type      A byte indicating the layout and semantics of payload
--------- ----------------------------------------------------------------- 
payload   The payload of a section can either be a single document, or a 
          document sequence.
========= ================================================================= 

.. This RST artwork improves the readability of the rendered document

|
|
|

============ ============================================================== 
Field        Description
============ ============================================================== 
When the Payload Type is 0, the content of the payload is
--------------------------------------------------------------------------- 
document     The BSON document. The payload size is inferred from the
             document's leading int32.
------------ -------------------------------------------------------------- 
When the Payload Type is 1, the content of the payload is
--------------------------------------------------------------------------- 
size         Payload size (includes this 4-byte field)
------------ -------------------------------------------------------------- 
identifier   A unique identifier (for this message). Generally the name of
             the "command argument" it contains the value for
------------ -------------------------------------------------------------- 
documents    0 or more BSON documents. Each BSON document cannot be larger
             than ``maxBSONObjectSize``.
============ ============================================================== 


Any unknown Payload Types MUST result in an error and the socket MUST be
closed. There is no ordering implied by payload types. A section with payload
type 1 can be serialized before payload type 0.

A fully constructed ``OP_MSG`` MUST contain exactly one ``Payload Type 0``, and
optionally any number of ``Payload Type 1`` where each identifier MUST be
unique per message.


.. This RST artwork improves the readability of the rendered document

|
|
|

Command Arguments As Payload
----------------------------

Certain commands support "pulling out" certain arguments to the command, and
providing them as ``Payload Type 1``, where the `identifier` is the command
argument’s name.
Specifying a command argument as a separate payload removes the need to use a
BSON Array. For example, ``Payload Type 1`` allows an array of documents to be
specified as a sequence of BSON documents on the wire without the overhead of
array keys.

MongoDB 3.6 only allows certain command arguments to be provided this way.
These are:

============== ============================================================ 
Command Name   Command Argument
============== ============================================================ 
insert         documents
-------------- ------------------------------------------------------------ 
update         updates
-------------- ------------------------------------------------------------ 
delete         deletes
============== ============================================================ 




.. This RST artwork improves the readability of the rendered document

|
|
|

Global Command Arguments
------------------------

The new opcode contains no field for providing the database name. Instead, the
protocol now has the concept of global command arguments.
These global command arguments can be passed to all MongoDB commands alongside
the rest of the command arguments.

Currently defined global arguments:

=============== ========================= =================================
Argument Name   Default Value             Description
=============== ========================= =================================
$db                                       The database name to execute the
                                          command on. MUST be provided and
                                          be a valid database name.
--------------- ------------------------- ---------------------------------
$readPreference ``{ "mode": "primary" }`` Determines server selection, and
                                          also whether a secondary server
                                          permits reads or responds "not
                                          master". See Server Selection Spec
                                          for rules about when read preference
                                          must or must not be included, and for
                                          rules about when read preference
                                          "primaryPreferred" must be added
                                          automatically.
=============== ========================= =================================

Additional global arguments are likely to be introduced in the future and
defined in their own specs.



.. This RST artwork improves the readability of the rendered document

|
|
|

User originating commands
=========================

Drivers MUST NOT mutate user provided command documents in any way, whether it
is adding required arguments, pulling out arguments, compressing it, adding
supplemental APM data or any other modification. 

.. This RST artwork improves the readability of the rendered document

|
|
|

Examples
========

Command Arguments As Payload Examples
-------------------------------------

For example, an insert can be represented like::

   {
      "insert": "collectionName",
      "documents": [
         {"_id": "Document#1", "example": 1},
         {"_id": "Document#2", "example": 2},
         {"_id": "Document#3", "example": 3}
      ],
      "writeConcern": { w: "majority" }
   }


Or, pulling out the ``"documents"`` argument out of the command document and
Into ``Payload Type 1``.
The ``Payload Type 0`` would then be::

   {
      "insert": "collectionName",
      "$db": "databaseName",
      "writeConcern": { w: "majority" }
   }


And ``Payload Type 1``::

   identifier: "documents"
   documents: {"_id": "Document#1", "example": 1}{"_id": "Document#2", "example": 2}{"_id": "Document#3", "example": 3}


Note that the BSON documents are placed immediately after each other, not with
any separator. The writeConcern is also left intact as a command argument in
the ``Payload Type 0`` section.
The command name MUST continue to be the first key of the command arguments in
the ``Payload Type 0`` section.

----

An update can for example be represented like::

   {
      "update": "collectionName",
      "updates": [
         {
            "q": {"example": 1},
            "u": { "$set": { "example": 4} }
         },
         {
            "q": {"example": 2},
            "u": { "$set": { "example": 5} }
         }
      ]
   }



Or, pulling out the ``"update"`` argument out of the command document and
Into ``Payload Type 1``.
The ``Payload Type 0`` would then be::


   {
      "update": "collectionName",
      "$db": "databaseName"
   }

And ``Payload Type 1``::

   identifier: updates
   documents: {"q": {"example": 1}, "u": { "$set": { "example": 4}}}{"q": {"example": 2}, "u": { "$set": { "example": 5}}}


Note that the BSON documents are placed immediately after each other, not
with any separator.

----

A delete can for example be represented like::

   {
      "delete": "collectionName",
      "deletes": [
         {
            "q": {"example": 3},
            "limit": 1
         },
         {
            "q": {"example": 4},
            "limit": 1
         }
      ]
   }

Or, pulling out the ``"deletes"`` argument out of the command document and into
``Payload Type 1``.
The ``Payload Type 0`` would then be::

   {
      "delete": "collectionName",
      "$db": "databaseName"
   }

And ``Payload Type 1``::

   identifier: delete
   documents: {"q": {"example": 3}, "limit": 1}{"q": {"example": 4}, "limit": 1}


Note that the BSON documents are placed immediately after each other, not with any separator.



Test Plan
=========
- Create a single document and insert it over ``OP_MSG``, ensure it works
- Create two documents and insert them over ``OP_MSG``, ensure each document is
  pulled out and presented as document sequence.
- ismaster.maxWriteBatchSize might change and be bumped to 100,000
- Repeat the previous 5 tests as updates, and then deletes.
- Create one small document, and one large 16mb document. Ensure they are
  inserted, updated and deleted in one roundtrip.



Motivation For Change
=====================

MongoDB clients are currently required to work around various issues that
each current opcode has, such as having to determine what sort of node is on
the other end as it affects the actual structure of certain messages.
MongoDB 3.6 introduces a new wire protocol opcode, ``OP_MSG``, which aims to
resolve most historical issues along with providing a future compatible and
extendable opcode. 


Backwards Compatibility
=======================


The isMaster.maxWriteBatchSize is being bumped, which also affects ``OP_QUERY``,
not only ``OP_MSG``. As a sideeffect, write errors will now have the message
truncated, instead of overflowing the maxMessageSize, if the server determines
it would overflow the allowed size. This applies to all commands that write.
The error documents are structurally the same, with the error messages simply
replaced with empty strings.


Reference Implementations
=========================

- mongoc
- .net

Future Work
===========


In the near future, this opcode is expected to be extended and include support for:

* Message checksum (crc32c)
* Output document sequences
* ``moreToCome`` can also be used for other commands, such as ``killCursors`` to
  restore ``OP_KILL_CURSORS`` behaviour as currently any errors/replies are ignored.



Q & A
=====

* Has the maximum number of documents per batch changed ?
   * The maximum number of documents per batch is dictated by the
     ``maxWriteBatchSize`` value returned during the MongoDB Handshake. It is
     likely this value will be bumped from 1,000 to 100,000.
* Has the maximum size of the message changed?
   * No. The maximum message size is still the ``maxMessageSizeBytes`` value
     returned during the MongoDB Handshake.
* Is everything still little-endian?
   * Yes. As with BSON, all MongoDB opcodes must be serialized in
     little-endian format.
* How does fire-and-forget (w=0 / unacknowledged write) work over ``OP_MSG``?
   * The client sets the ``moreToCome`` flag on the request. The server will
     not send a response to such requests.
   * Malformed operation or errors such as duplicate key errors are
     not discoverable and will be swallowed by the server.
   * Write errors due to not-primary will close the connection, which clients
     will pickup on next time it uses the connection. This means at least one
     unacknowledged write operation will be lost as the client does not
     discover the failover until next time the socket is used.
* Should we provide ``runMoreToComeCommand()`` helpers?
  Since the protocol allows any command to be tagged with ``moreToCome``, effectively
  allowing any operation to become ``fire & forget``, it might be a good idea
  to add such helper, rather then adding wire protocol headers as options to the
  existing ``runCommand`` helpers.




Changelog
=========

- 2017-11-12 Specify read preferences for OP_MSG with direct connection
- 2017-08-17 Added the ``User originating command`` section
- 2017-07-18 Published 1.0.0
