.. role:: javascript(code)
  :language: javascript

======================
Read and Write Concern
======================

:Spec: 135
:Title: Read and Write Concern
:Authors: Craig Wilson
:Status: Draft
:Type: Standards
:Server Versions: 2.4+
:Last Modified: August 31, 2015
:Version: 0.1

.. contents::

--------

Abstract
========

A driver must support configuring and sending read concern and write concerns
to a server. This specification indicates how to accomplish this.

META
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

This specification includes guidance for `Read Concern`_ and `Write Concern`_.


------------
Read Concern
------------

For naming and deviation guidance, see the CRUD specification. Below are defined the constructs for drivers.

.. code:: typescript
  
  enum ReadConcernLevel {
      /**
       * This will issue a read  that retrieves data committed by the primary node. This level was the only 
       * read behavior prior to 3.2. 
       * This is rendered as "local" on the wire.
       */
      Local

      /**
       * Returns a view of the data on the primary committed by a majority of the nodes 
       * of the cluster and provides a guarantee that data read will not be rolled back.
       * This is rendered as "majority" on the wire.
       */
      Majority
  }

  class ReadConcern {
    /**
     * The level of the read concern.
     */
    Level: Optional<ReadConcernLevel | String>
  }


Default Value
-------------

When a ``ReadConcern`` is created but no values are specified, it should be considered the default ``ReadConcern``.


On the Wire
-----------

Read Commands
~~~~~~~~~~~~~

When using the read commands that support ``ReadConcern``, ``ReadConcern`` is specified as a named parameter, ``readConcern``. See the command documentation for further examples.

The default ``ReadConcern`` is specified by omitting the ``readConcern`` parameter.


Location Specification
----------------------

Via Code
~~~~~~~~

``ReadConcern`` SHOULD be specifiable at the ``Client``, ``Database``, and ``Collection`` levels. Unless specified, the value MUST be inherited from its parent. In addition, a driver may allow it to be specified on a per-operation basis in accordance with the CRUD specification.

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

    // col3's readConcern level is "local"
    var col3 = db2.getCollection("col_name", { readConcern: { level: "local" } });


Via Connection String
~~~~~~~~~~~~~~~~~~~~~

Options
    * ``readConcernLevel`` - defines the level for the read concern.

For example:

.. code:: 

    mongodb://server:27017/db?readConcernLevel=majority

Errors
------

Wire Version < 5
    If a ``ReadConcernLevel`` of anything but ``Local`` is specified, the driver MUST raise an error. This check MUST happen after server selection has occurred in the case of mixed version clusters. It is up to users to appropriately define a ``ReadPreference`` such that intermitent errors do not occur.


-------------
Write Concern
-------------

For naming and deviation guidance, see the CRUD specification. Below are defined the constructs for drivers.

.. code:: typescript
  
  class WriteConcern {
    /**
     * If true, wait for the the write operation to get committed to the journal. When unspecified, a driver
     * should not send "j".
     *
     * @see http://docs.mongodb.org/manual/core/write-concern/#journaled
     */
    J: Optional<Boolean>,

    /**
     * When an integer, specifies the number of nodes that should acknowledge the write.
     * When a string, indicates a named mode. "majority" is defined, but users could specify other
     * custom error modes.
     * When not specified, a driver should not send "w".
     */
    W: Optional<Int32 | String>,

    /**
     * If the write concern is not satisfied within the specified timeout, the operation returns
     * will return an error.
     * When not specified, a driver should not send "wtimeout".
     *
     * @see http://docs.mongodb.org/manual/core/write-concern/#timeouts
     */
    WTimeoutMS: Optional<Int64>
  }


Default Value
-------------

When a ``WriteConcern`` is created but no values are specified, it should be considered the default ``WriteConcern``.

.. note:: 
    :javascript:`writeConcern: { }` is not the same as :javascript:`writeConcern: {w: 1}`. The server's ``getLastErrorDefaults`` can be re-defined. Sending :javascript:`{w:1}` overrides that default while sending :javascript:`{ }` indicates to use the default.

Unacknowledged Write Concern
----------------------------

An ``Unacknowledged WriteConcern`` is specified with a "w" value of 0. This indicates that the user does not care about any errors from the server.

On the Wire
-----------

OP_INSERT, OP_DELETE, OP_UPDATE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``WriteConcern`` is implemented by drivers by sending the ``getLastError``(GLE) command directly after the operation. Drivers SHOULD piggy-back the GLE onto the same buffer as the operation.

The default ``WriteConcern`` is specified by sending the GLE command without arguments. For example: :javascript:`{ getLastError: 1 }`

An ``Unacknowledged WriteConcern`` is specified by NOT sending a GLE. In this instance, the server will not send a reply.

See the ``getLastError`` command documentation for other formatting.


Write Commands
~~~~~~~~~~~~~~

When using the ``insert``, ``delete``, or ``update`` commands, ``WriteConcern`` is specified as a named parameter, ``writeConcern``. See the command documentation for further examples.

The default ``WriteConcern`` is specified by omitting the ``writeConcern`` parameter.

An ``Unacknowledged WriteConcern`` is specified by sending ``{writeConcern: { w: 0 } }``.


Find And Modify
~~~~~~~~~~~~~~~

When using the ``findAndModify`` command, ``WriteConcern`` is specified as a named parameter, ``writeConcern``. See the command documentation for further examples.

On servers < 3.2, any non-default ``WriteConcern`` MUST be ignored. 

Location Specification
----------------------

Via Code
~~~~~~~~

``WriteConcern`` SHOULD be specifiable at the ``Client``, ``Database``, and ``Collection`` levels. Unless specified, the value MUST be inherited from its parent. In addition, a driver may allow it to be specified on a per-operation basis in accordance with the CRUD specification.

For example:

.. code:: typescript

    var client = new MongoClient({ writeConcern: { w: 2 } });

    // db1's writeConcern is {w: 2}.
    var db1 = client.getDatabase("db1");

    // col1's writeConcern is {w: 2}.
    var col1 = db1.getCollection("col_name");

    // db2's writeConcern is {j: true}.
    var db2 = client.getDatabase("db_name", { writeConcern: { j: true } });

    // col2's writeConcern {j: true}.
    var col2 = db2.getCollection("col_name");

    // col3's writeConcern is its default value.
    var col3 = db2.getCollection("col_name", { writeConcern: { } });


Via Connection String
~~~~~~~~~~~~~~~~~~~~~

Options
    * ``w`` - corresponds to ``W`` in the class definition.
    * ``j`` - corresponds to ``J`` in the class definition..
    * ``wtimeout`` - corresponds to ``WTimeoutMS`` in the class definition.

For example:

.. code:: 

    mongodb://server:27017/db?w=3

    mongodb://server:27017/db?j=true

    mongodb://server:27017/db?wtimeout=1000

    mongodb://server:27017/db?w=majority&wtimeout=1000



Backwards Compatibility
=======================

There should be no backwards compatibility concerns. This SPEC merely deals with how to specify read and write concerns.


Reference Implementation
========================


Q & A
=====

Q: Where is ``afterOpTime`` in ``ReadConcern``?
  ``afterOpTime`` is not a user facing feature.

Q: Where is ``fsync`` in ``WriteConcern``?
  ``fsync`` has been deprecated and should not be used. ``Journal`` is the de-facto replacement.

Q: Why is specifying a non-default readConcern for servers < 3.2 an error while a non-default write concern gets ignored?
  ``findAndModify`` is an existing command and since ``WriteConcern`` is defined globally, anyone using ``findAndModify`` in their applications with a non-default ``WriteConcern`` declared globally would have all their ``findAndModify`` operations fail.


Version History
===============

Version 0.1 Changes

    - Initial draft
