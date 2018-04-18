.. role:: javascript(code)
  :language: javascript

======================
Read and Write Concern
======================

:Spec: 135
:Title: Read and Write Concern
:Authors: Craig Wilson
:Advisors: Jesse Davis, Hannes Magnusson, Anna Herlihy
:Status: Approved
:Type: Standards
:Server Versions: 2.4+
:Last Modified: December 18, 2017
:Version: 1.5

.. contents::

--------

Abstract
========

A driver must support configuring and sending read concern and write concerns
to a server. This specification defines the API drivers must implement as well as how that API is translated into messages for communication with the server.

META
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Terminology
===========

MaxWireVersion
    The ``maxWireVersion`` value reported by the ``ismaster`` command.
Server Selection
    The process of selecting a server to read or write from. See https://github.com/mongodb/specifications/tree/master/source/server-selection.

Specification
=============


This specification includes guidance for implementing `Read Concern`_ and `Write Concern`_ in a driver. It does not define how read and write concern behave or are implemented on the server.

------------
Read Concern
------------

For naming and deviation guidance, see the `CRUD specification <https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#naming>`_. Defined below are the constructs for drivers.

.. code:: typescript

  enum ReadConcernLevel {
      /**
       * This is rendered as "local" (lower-case) on the wire.
       */
      local,

      /**
       * This is rendered as "majority" (lower-case) on the wire.
       */
      majority,

      /**
       * This is rendered as "linearizable" (lower-case) on the wire.
       */
      linearizable

      /**
       * This is rendered as "available" (lower-case) on the wire.
       */
      available
  }

  class ReadConcern {
    /**
     * The level of the read concern.
     */
    level: Optional<ReadConcernLevel | String>
  }

The read concern option is available for the following operations: 

- ``find`` command
- ``aggregate`` command
- ``distinct`` command
- ``count`` command
- ``parallelCollectionScan`` command
- ``geoNear`` command
- ``geoSearch`` command
- ``mapReduce`` command with {out : inline} output option

``aggregate`` command with $out and ``mapReduce`` command with "out" set to anything other than "inline" do not support readConcern.

Unknown Levels and Additional Options for String Based ReadConcerns
-------------------------------------------------------------------

For forward compatibility, a driver MUST NOT raise an error when a user provides an unknown ``level`` or additional options. The driver relies on the server to validate levels and other contents of the read concern.


Server’s Default Read Concern
-----------------------------

When a ``ReadConcern`` is created but no values are specified, it should be considered the server’s default ``ReadConcern``.

:javascript:`readConcern: { }` is not the same as  :javascript:`readConcern: { level=“local” }`. The former is the server’s default ``ReadConcern`` while the latter is the user explicitly specifying a ``ReadConcern`` with a ``level`` of “local”.


On the Wire
-----------

Read Commands
~~~~~~~~~~~~~

Read commands that support ``ReadConcern`` take a named parameter spelled (case-sensitively) ``readConcern``. See command documentation for further examples. 

If the ``Client``, ``Database``, or ``Collection`` being operated on either has no ``ReadConcern`` set, or has the server default ``ReadConcern``:

- If the  ``ReadConcern`` specified for the command is the server default, the driver MUST omit that ``ReadConcern`` when sending the command.
- If the ``ReadConcern`` specified for the command is any ``ReadConcern`` besides the server default, the driver MUST include that ``ReadConcern`` when sending the command.

If the ``Client``, ``Database``, or ``Collection`` being operated on has a non-default ``ReadConcern`` specified, then the driver MUST include the command's ``ReadConcern`` when sending the command. This includes if the command specifies the server default ``ReadConcern``, so that the command can override the ``Client``, ``Database``, or ``Collection``'s ``ReadConcern`` to use the server default instead.

.. note::
    While the default ``ReadConcern`` MUST be omitted, an explicitly specified ``ReadConcern`` of :javascript:`readConcern: { level: “local” }` MUST NOT be omitted.


Generic Command Method
~~~~~~~~~~~~~~~~~~~~~~

If your driver offers a generic ``RunCommand`` method on your ``database`` object, ``ReadConcern`` MUST NOT be applied automatically to any command. A user wishing to use a ``ReadConcern`` in a generic command must supply it manually.


Errors
~~~~~~

``ReadConcern`` errors from a server MUST NOT be handled by a driver. There is nothing a driver can do about them and any such errors will get propagated to the user via normal error handling.


Location Specification
----------------------

Via Code
~~~~~~~~

``ReadConcern`` SHOULD be specifiable at the ``Client``, ``Database``, and ``Collection`` levels. Unless specified, the value MUST be inherited from its parent and SHOULD NOT be modifiable on an existing ``Client``, ``Database``, and ``Collection``. In addition, a driver MAY allow it to be specified on a per-operation basis in accordance with the CRUD specification. 

For example:

.. code:: typescript

    var client = new MongoClient({ readConcern: { level: "local" } });

    // db1's readConcern level is "local".
    var db1 = client.getDatabase("db1");

    // col1's readConcern level is "local"
    var col1 = db1.getCollection("col_name");

    // db2's readConcern level is "majority".
    var db2 = client.getDatabase("db_name", { readConcern: { level: "majority" } });

    // col2's readConcern level is "majority"
    var col2 = db2.getCollection("col_name");

    // col3's readConcern level is the server’s default read concern
    var col3 = db2.getCollection("col_name", { readConcern: { } });


Via Connection String
~~~~~~~~~~~~~~~~~~~~~

Options
    * ``readConcernLevel`` - defines the level for the read concern.

For example:

.. code:: 

    mongodb://server:27017/db?readConcernLevel=majority

Errors
------

MaxWireVersion < 4
    Only the server’s default ``ReadConcern`` is support by ``MaxWireVersion`` < 4. When using other ``readConcernLevels`` with clients reporting ``MaxWireVersion`` < 4, the driver MUST raise an error. This check MUST happen after server selection has occurred in the case of mixed version clusters. It is up to users to appropriately define a ``ReadPreference`` such that intermittent errors do not occur.

.. note::

   ``ReadConcern`` is only supported for commands.

-------------
Write Concern
-------------

For naming and deviation guidance, see the `CRUD specification <https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#naming>`_. Below are defined the constructs for drivers.

.. code:: typescript
  
  class WriteConcern {
    /**
     * If true, wait for the the write operation to get committed to the journal. When unspecified, a driver
     * MUST NOT send "j".
     *
     * @see http://docs.mongodb.org/manual/core/write-concern/#journaled
     */
    journal: Optional<Boolean>,

    /**
     * When an integer, specifies the number of nodes that should acknowledge the write      
     * and MUST be greater than or equal to 0.
     * When a string, indicates tags. "majority" is defined, but users 
     * could specify other custom error modes.
     * When not specified, a driver MUST NOT send "w".
     */
    w: Optional<Int32 | String>,

    /**
     * If the write concern is not satisfied within the specified timeout (in milliseconds), 
     * the operation will return an error.
     * The value MUST be greater than or equal to 0.
     * When not specified, a driver should not send "wtimeout".
     *
     * @see http://docs.mongodb.org/manual/core/write-concern/#timeouts
     */
    wtimeoutMS: Optional<Int64>
  }


FSync
-----

FSync SHOULD be considered deprecated.  Those drivers supporting the deprecated ``fsync`` option SHOULD treat ``fsync`` identically to ``journal`` in terms of consistency with ``w`` and whether a ``WriteConcern`` that specifies ``fsync`` is acknowledged or unacknowledged.


Server’s Default WriteConcern
-----------------------------

When a ``WriteConcern`` is created but no values are specified, it should be considered the server’s default ``WriteConcern``.

The server has a settings field called ``getLastErrorDefaults`` which allows a user to customize the default behavior of a ``WriteConcern``. Because of this, :javascript:`writeConcern: { }` is not the same as :javascript:`writeConcern: {w: 1}`. Sending :javascript:`{w:1}` overrides that default. As another example, :javascript:`writeConcern: { }` is not the same as :javascript:`writeConcern: {journal: false}`.
    

Inconsistent WriteConcern
-------------------------

Drivers SHOULD raise an error when an inconsistent ``WriteConcern`` is specified. The following is an exhaustive list of inconsistent ``WriteConcerns``:

.. code:: typescript

   writeConcern = { w: 0, journal: true };

If, for the sake of backwards compatibility, the driver allows inconsistent write concerns where ``w`` equals 0 but ``journal`` is set to ``true``, the driver MUST treat it as an ``Acknowledged WriteConcern``.


Unacknowledged WriteConcern
---------------------------

An ``Unacknowledged WriteConcern`` is when (``w`` equals 0) AND (``journal`` is not set or is ``false``). 

These criteria indicates that the user does not care about errors from the server.

Examples:

.. code:: typescript

   writeConcern = { w: 0 }; // Unacknowledged
   writeConcern = { w: 0, journal: false }; // Unacknowledged
   writeConcern = { w: 0, wtimeoutMS: 100 }; // Unacknowledged 


On the Wire
-----------

OP_INSERT, OP_DELETE, OP_UPDATE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``WriteConcern`` is implemented by sending the ``getLastError``(GLE) command directly after the operation. Drivers SHOULD piggy-back the GLE onto the same buffer as the operation. Regardless, GLE MUST be sent on the same connection as the initial write operation.

When a user has not specified a ``WriteConcern`` or has specified the server’s default ``WriteConcern``, drivers MUST send the GLE command without arguments. For example: :javascript:`{ getLastError: 1 }`

Drivers MUST NOT send a GLE for an ``Unacknowledged WriteConcern``. In this instance, the server will not send a reply.

See the ``getLastError`` command documentation for other formatting.


Write Commands
~~~~~~~~~~~~~~

The ``insert``, ``delete``, and ``update`` commands take a named parameter, ``writeConcern``. See the command documentation for further examples.

When a user has not specified a ``WriteConcern`` or has specified the server’s default ``WriteConcern``, drivers MUST omit the ``writeConcern`` parameter from the command.

All other ``WriteConcerns``, including the ``Unacknowledged WriteConcern``, MUST be sent with the ``writeConcern`` parameter.

.. note::
    Drivers MAY use ``OP_INSERT``, ``OP_UPDATE``, and ``OP_DELETE`` when an ``Unacknowledged WriteConcern`` is used.

Generic Command Method
~~~~~~~~~~~~~~~~~~~~~~

If your driver offers a generic ``RunCommand`` method on your ``database`` object, ``WriteConcern`` MUST NOT be applied automatically to any command. A user wishing to use a ``WriteConcern`` in a generic command must manually include it in the command document passed to the method.

The generic command method MUST NOT check the user's command document for a ``WriteConcern`` nor check whether the server is new enough to support a write concern for the command. The method simply sends the user's command to the server as-is.

Find And Modify
~~~~~~~~~~~~~~~

The ``findAndModify`` command takes a named parameter, ``writeConcern``. See command documentation for further examples.

If writeConcern is specified for the Collection, ``writeConcern`` MUST be omitted when sending ``findAndModify`` with MaxWireVersion < 4.

If the findAndModify helper accepts writeConcern as a parameter, the driver MUST raise an error with MaxWireVersion < 4.

.. note ::
    Driver documentation SHOULD include a warning in their server 3.2 compatible releases that an elevated ``WriteConcern`` may cause performance degradation when using ``findAndModify``. This is because ``findAndModify`` will now be honoring a potentially high latency setting where it did not before.

Other commands that write
~~~~~~~~~~~~~~~~~~~~~~~~~

Command helper methods for commands that write, other than those discussed above,
MAY accept a write concern or write concern options in their parameter list.
If the helper accepts a write concern, the driver MUST error if the selected server's MaxWireVersion < 5 and a
write concern has explicitly been specified.

Helper methods that apply the write concern inherited from the Collection or Database, SHOULD check whether the
selected server's MaxWireVersion >= 5 and if so, include the inherited write concern in the command on the wire.
If the selected server's MaxWireVersion < 5, these methods SHOULD silently omit the write concern from the command
on the wire.

These commands that write are:
  * ``aggregate`` with ``$out``
  * ``copydb``
  * ``create``
  * ``createIndexes``
  * ``drop``
  * ``dropDatabase``
  * ``dropIndexes``
  * ``mapReduce`` with ``$out``
  * ``clone``
  * ``cloneCollection``
  * ``cloneCollectionAsCapped``
  * ``collMod``
  * ``convertToCapped``
  * ``renameCollection``

Errors
~~~~~~

Server errors associated with ``WriteConcern`` return successful responses with a ``writeConcernError`` field indicating the issue. For example,

.. code:: typescript

    rs0:PRIMARY> db.runCommand({insert: "foo", documents: [{x:1}], writeConcern: { w: "blah"}})
    {
        "ok" : 1,
        "n" : 1,
        "lastOp" : Timestamp(1441992923, 1),
        "electionId" : ObjectId("55f30e4cffffffffffffffff"),
        "writeConcernError" : {
            "code" : 79,
            "errmsg" : "No write concern mode named 'blah' found in replica set configuration"
        }
    }

Drivers SHOULD parse server replies for a "writeConcernError" field and report the error
only in the command-specific helper methods for commands that write, from the list above.
For example, helper methods for "findAndModify" or "aggregate" SHOULD parse the server reply
for "writeConcernError".

Drivers SHOULD report writeConcernErrors however they report other server errors:
by raising an exception, returning "false", or another idiom that is consistent with other server errors.

Drivers SHOULD NOT parse server replies for "writeConcernError" in generic command methods.

(Reporting of writeConcernErrors is more complex for bulk operations,
see the Bulk API Spec.)

Location Specification
----------------------

Via Code
~~~~~~~~

``WriteConcern`` SHOULD be specifiable at the ``Client``, ``Database``, and ``Collection`` levels. Unless specified, the value MUST be inherited from its parent and SHOULD NOT be modifiable on an existing ``Client``, ``Database``, and ``Collection``. In addition, a driver MAY allow it to be specified on a per-operation basis in accordance with the CRUD specification.

For example:

.. code:: typescript

    var client = new MongoClient({ writeConcern: { w: 2 } });

    // db1's writeConcern is {w: 2}.
    var db1 = client.getDatabase("db1");

    // col1's writeConcern is {w: 2}.
    var col1 = db1.getCollection("col_name");

    // db2's writeConcern is {journal: true}.
    var db2 = client.getDatabase("db_name", { writeConcern: { journal: true } });

    // col2's writeConcern {journal: true}.
    var col2 = db2.getCollection("col_name");

    // col3's writeConcern is the server’s default write concern.
    var col3 = db2.getCollection("col_name", { writeConcern: { } });

    // Override col3's writeConcern.
    col3.drop({ writeConcern: { w: 3 } });


Via Connection String
~~~~~~~~~~~~~~~~~~~~~

Options
    * ``w`` - corresponds to ``w`` in the class definition.
    * ``journal`` - corresponds to ``journal`` in the class definition.
    * ``wtimeoutMS`` - corresponds to ``wtimeoutMS`` in the class definition.

For example:

.. code:: 

    mongodb://server:27017/db?w=3

    mongodb://server:27017/db?journal=true

    mongodb://server:27017/db?wtimeoutMS=1000

    mongodb://server:27017/db?w=majority&wtimeoutMS=1000



Backwards Compatibility
=======================

There should be no backwards compatibility concerns. This specification merely deals with how to specify read and write concerns.

Test Plan
=========

Yaml tests are located here: https://github.com/mongodb/specifications/tree/master/source/read-write-concern/tests

Below are English descriptions of other items that should be tested:

-----------
ReadConcern
-----------

1. Commands supporting a read concern MUST raise an error when MaxWireVersion is less than 4 and a non-default, non-local read concern is specified.
2. Commands supporting a read concern MUST NOT send the default read concern to the server.
3. Commands supporting a read concern MUST send any non-default read concern to the server.

------------
WriteConcern
------------

1. Commands supporting a write concern MUST NOT send the default write concern to the server.
2. Commands supporting a write concern MUST send any non-default acknowledged write concern to the server, either in the command or as a getLastError.
3. On ServerVersion less than 2.6, drivers MUST NOT send a getLastError command for an Unacknowledged write concern.
4. FindAndModify helper methods MUST NOT send a write concern when the MaxWireVersion is less than 4.
5. Helper methods for other commands that write MUST NOT send a write concern when the MaxWireVersion is less than 5.

Reference Implementation
========================

These are currently under construction.


Q & A
=====

Q: Why is specifying a non-default ``ReadConcern`` for servers < 3.2 an error while a non-default write concern gets ignored in ``findAndModify``?
  ``findAndModify`` is an existing command and since ``WriteConcern`` may be defined globally, anyone using ``findAndModify`` in their applications with a non-default ``WriteConcern`` defined globally would have all their ``findAndModify`` operations fail.

Q: Why does a driver send :javascript:`{ readConcern: { level: “local” } }` to the server when that is the server’s default?
  First, to mirror how ``WriteConcern`` already works, ``ReadConcern() does not equal ReadConcern(level=local)`` in the same way that ``WriteConcern() does not equal WriteConcern(w=1)``. This is true for ``WriteConcern`` because the server’s default could be set differently. While this setting does not currently exist for ``ReadConcern``, it is a possible eventuality and it costs a driver nothing to be prepared for it.
  Second, it makes sense that if a user doesn’t specify a ``ReadConcern``, we don’t send one and if a user does specify a ``ReadConcern``, we do send one. If the user specifies level=”local”, for instance, we send it.

Version History
===============

  - 2015-10-16: ReadConcern of local is no longer allowed to be used when talking with MaxWireVersion < 4.
  - 2016-05-20: Added note about helpers for commands that write accepting a writeConcern parameter.
  - 2016-06-17: Added "linearizable" to ReadConcern levels.
  - 2016-07-15: Command-specific helper methods for commands that write SHOULD check the server's MaxWireVersion
    and decide whether to send writeConcern.
    Advise drivers to parse server replies for writeConcernError
    and raise an exception if found,
    only in command-specific helper methods that take a writeConcern parameter,
    not in generic command methods.
    Don't mention obscure commands with no helpers.
  - 2016-08-06: Further clarify that command-specific helper methods for commands that write
    take write concern options in their parameter lists, and relax from SHOULD to MAY.
  - 2017-03-13: reIndex silently ignores writeConcern in MongoDB 3.4 and returns
    an error if writeConcern is included with MongoDB 3.5+. See
    `SERVER-27891 <https://jira.mongodb.org/browse/SERVER-27891>`_.
  - 2017-11-17 : Added list of commands that support readConcern 
  - 2017-12-18 : Added "available" to Readconcern level. 
