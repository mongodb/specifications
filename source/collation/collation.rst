.. role:: javascript(code)
  :language: javascript

=========
Collation
=========

:Spec: 79
:Title: Collation
:Authors: Emily Stolfo
:Advisory Group: Derick Rethans, Craig Wilson
:Status: Approved
:Type: Standards
:Minimum Server Version: 1.8
:Last Modified: May 15, 2017
:Version: 1.0

.. contents::

--------

Abstract
========

As of MongoDB server version 3.4 (maxWireVersion 5), a collation option is supported by the query system for matching and sorting on language strings in a locale-aware fashion.

A driver MUST support a Collation option for each of the relevant operations in server versions >= 3.4 (maxWireVersion 5) and MUST throw an error if a user supplies a Collation option for the operation and the selected server has maxWireVersion < 5 or if the user is using opcode-based unacknowledged writes.

The CRUD and Index Management specs include the collation option in descriptions of API elements where it is supported. This document provides more details on the specific driver behavior required to handle the collation option. 

META
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Design Rationale
================

-----------------------------------------------------------------------------
Collation is not a setting on a driver Client, Collection, or Database object
-----------------------------------------------------------------------------

MongoDB supports a server-side collation default on a collection. It is problematic to add a default Collation option on a driver’s Collection or Database object, because automatic collection and index creation would bypass any driver object's Collation setting. Additionally, this would have a number of performance implications in the context of bulk writes: any bulk write on a Collection object having a default Collation would require iterating through each operation and adding a Collation document.

After the initial release of server version 3.4, many users will want to apply Collations to all operations on an existing collection. Such users will have to supply the Collation option to each operation explicitly; however, eventually the majority of users wishing to use Collations on all operations on a collection will create a collection with a server-side default. We chose to favor user verbosity right now over abstracting the feature for short-term gains.

--------------------------------------------------------------------------------------------------------
Drivers throw an error if a user supplies Collation and the selected server does not support the feature
--------------------------------------------------------------------------------------------------------

Server versions earlier than 3.4 don't always throw an error if an unknown option is supplied to certain operations. Because a Collation defines how documents are matched and sorted for both read and write operations, behavior differences between server versions are significant. Drivers therefore MUST throw an error if a user specifies a Collation and the selected server has a maxWireVersion < 5 or if using opcode-based unacknowledged writes.

Specification
=============

------------------------
Collation Document Model
------------------------

For naming and deviation guidance, see the `CRUD specification <https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#naming>`_. Defined below are the constructs for drivers. Note that the only required field is ``locale``, but the driver should let the server validate the presence of this field.

.. code:: typescript

  class Collation {
    /**
     * The locale.
     */
    locale: String

    /**
     * The case level.
     */
    caseLevel: Optional<Boolean>

    /**
     * The case ordering.
     */
    caseFirst: Optional<String>

    /**
     * The number of comparison levels to use.
     */
    strength: Optional<Integer>

    /**
     * Whether to order numbers based on numerical order and not collation order.
     */
    numericOrdering: Optional<Boolean>

    /**
     * Whether spaces and punctuation are considered base characters.
     */
    alternate: Optional<String>

    /**
     * Which characters are affected by alternate: “shifted”.
     */
    maxVariable: Optional<String>

    /**
     * If true, normalizes text into Unicode NFD.
     */
    normalization: Optional<Boolean>

    /**
     * Causes secondary differences to be considered in reverse order, as it is done in the French language.
     */
    backwards: Optional<Boolean>
  }

Unknown Options
-------------------------------------------------------------------

For forward compatibility, a driver MUST NOT raise an error when a user provides unknown options or values. The driver MUST NOT validate collation document types; the driver relies on the server to validate values and other contents of the collation document.

Generic Command Method
----------------------

If a driver offers a generic ``RunCommand`` method on the ``database`` object, the driver MUST NOT validate whether the provided command document contains a "collation" subdocument, and MUST NOT check the server's wire version before sending the command including the "collation" subdocument.

---
API
---
The driver helpers that must support a collation option include the create collection helper, any CRUD API components relying on the MongoDB query system (including updates and deletes) and some index management helpers. The CRUD-related commands that take a collation option are:

- aggregate
- count
- distinct
- find (command only)
- findAndModify
- geoNear
- group
- mapReduce
- delete  (command only)
- update (command only)

The collation option is sent to the server in the form of a BSON Document. See the `CRUD specification <https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#naming>`_ for details on supporting the option in the CRUD API.

Driver helpers manipulating or using indexes MUST support a collation option. These include creating, deleting, and hinting an index. See the `Index Management specification  <https://github.com/mongodb/specifications/blob/master/source/index-management.rst>`_ for details.

------------------------
Require maxWireVersion 5
------------------------

Drivers MUST require the server's maxWireVersion >= 5 to support Collations. When a collation is explicitly specified for a server with maxWireVersion < 5, the driver MUST raise an error.

----------------------------------
Opcode-based Unacknowledged Writes
----------------------------------

The driver MUST NOT allow collation with opcodes, because the server doesn't support it. If a driver uses opcode-based writes when the write concern is unacknowledged, the driver MUST raise an error if a collation is explicitly set.

-------------------------------------------
Setting a default collation on a collection
-------------------------------------------

Drivers MUST allow the create command to accept a parameter called “collation”. For example,

.. code:: typescript

	db.command({
		create: “myCollection”,
		collation: {locale: “en_US”}
	});

-------------
BulkWrite API
-------------

If maxWireVersion < 5, the driver MUST inspect each BulkWrite operation model for a collation and MUST raise an error and MUST NOT send any operations to the server if a collation is explicitly specified on an operation. For example, the user will provide BulkWrite operation models as in the following example:

.. code:: typescript

  db.collection.bulkWrite([
    {insertOne: { … }},

    {updateOne: { filter: { name: "PING" },
                          update: { $set: { name: "pong" }},
                          collation: { locale: "en_US", strength: 2 }}},
    {updateMany: {..., collation: {...}}},
    {replaceOne: {..., collation: {...}}},
    {deleteOne: {..., collation: {...}}},
    {deleteMany: {..., collation: {...}}}
  ]);

The driver must inspect each operation for a Collation if maxWireVersion is < 5 and fail the entire bulkWrite if a collation was explicitly specified. In the example above, that means even the insertOne (without Collation) MUST NOT be sent.


Test Plan
=========

There is no specific test plan for driver Collation support; however drivers should test each affected CRUD, Index Management API, and collection creation/modification component to ensure that Collation is a supported option.

https://github.com/mongodb/specifications/blob/master/source/index-management.rst
https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst

In addition, drivers should test that two indexes can be created with identical key patterns and different collations. A custom name must be provided for one of them. Then, the test should ensure that the correct index is dropped when delete_one is called with an index name.

Drivers should also test that errors are raised in each place Collation can be provided to a API method and the selected server has maxWireVersion < 5.


Backwards Compatibility
=======================

There should be no backwards compatibility concerns.


Reference Implementation
========================

Reference Implementation: 
  `RUBY-1126 <https://jira.mongodb.org/browse/RUBY-1126>`_
  `JAVA-2241 <https://jira.mongodb.org/browse/JAVA-2241>`_

Q & A
=====

Q: Insert doesn’t take a collation?
  No, only queries take collation. A collation is a per operation value, it does not affect how the data is stored.
  
Q: Delete and Update take a collation?
  Yes, delete and update operations use the query system to match against a provided delete/update filter. Providing a collation when deleting a document matching ObjectID() doesn’t change anything, but matching a string value would.

Q: How do I create a collection with default collation? Does it affect my existing collection creation helper?
  A collection with a default collation can be created using the create helper and by providing a collation option.


Version History
===============

- 2017-05-15: minor markup fixes in API section.
- 2016-08-31: version 1.0.
