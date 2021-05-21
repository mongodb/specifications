==================
Handling of DBRefs
==================

:Spec Title: Handling of DBRefs
:Spec Version: 1.0
:Author: Jeremy Mikola
:Status: Draft
:Type: Standards
:Last Modified: 2021-05-21

.. contents::

--------

Abstract
========

DBRefs are a convention for expressing a reference to another document as an
embedded document (i.e. BSON type 0x03). Several drivers provide a model class
for encoding and/or decoding DBRef documents. This specification will both
define the structure of a DBRef and provide guidance for implementing model
classes in drivers that choose to do so.


META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`__.

This specification presents documents as Extended JSON. Although JSON fields are
unordered, the order of fields presented herein should be considered pertinent.
This is especially relevant for the `Test Plan`_.


Specification
=============


DBRef Structure
---------------

A DBRef is an embedded document with the following fields:

- ``$ref``: required string field. Contains the name of the collection where
  the referenced document resides. This MUST be the first field in the DBRef.
- ``$id``: required field. Contians the value of the ``_id`` field of the
  referenced document. This MUST be the second field in the DBRef.
- ``$db``: optional string field. Contains the name of the database where the
  referenced document resides. If specified, this MUST be the third field in the
  DBRef. If omitted, the referenced document is assumed to reside in the same
  database as the DBRef.
- Extra, optional fields may follow after ``$id`` or ``$db`` (if specified).
  There are no inherent restrictions on extra field names; however, older server
  versions may impose their own restrictions (e.g. no dots or dollars).

DBRefs have no relation to the deprecated DBPointer BSON type (i.e. type 0x0C).


Examples of Valid DBRefs
~~~~~~~~~~~~~~~~~~~~~~~~

The following examples are all valid DBRefs:

.. code:: typescript

  // Basic DBRef with only $ref and $id fields
  { "$ref": "coll0", "$id": { "$oid": "60a6fe9a54f4180c86309efa" } }

  // DBRef $id is not necessarily an ObjectId
  { "$ref": "coll0", "$id": 1 }

  // DBRef with optional $db field
  { "$ref": "coll0", "$id": 1, "$db": "db0" }

  // DBRef with extra, optional fields (with or without $db)
  { "$ref": "coll0", "$id": 1, "$db": "db0", "foo": "bar" }
  { "$ref": "coll0", "$id": 1, "foo": true }

  // Extra field names have no inherent restrictions
  { "$ref": "coll0", "$id": 1, "$foo": "bar" }
  { "$ref": "coll0", "$id": 1, "foo.bar": 0 }

Examples of Invalid DBRefs
~~~~~~~~~~~~~~~~~~~~~~~~~~

The following examples are all invalid DBRefs:

.. code:: typescript

  // Required fields are omitted
  { "$ref": "coll0" }
  { "$id": { "$oid": "60a6fe9a54f4180c86309efa" } }

  // Invalid types for $ref or $db
  { "$ref": true, "$id": 1 }
  { "$ref": "coll0", "$id": 1, "$db": 1 }

  // Fields are out of order
  { "$id": 1, "$ref": "coll0" }


Implementing a DBRef Model
--------------------------

Drivers MAY provide a model class for encoding and/or decoding DBRef documents.
For those drivers that do, this section defines expected behavior of that class.
This section does not prohibit drivers from implementing additional
functionality, provided it does not conflict with any of these guidelines.


Constructing a DBRef model
~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers MAY provide an API for constructing a DBRef model directly from its
constituent parts. If so:

- Drivers MUST solicit a string value for ``$ref``.

- Drivers MUST solicit an arbitary value for ``$id``. Drivers SHOULD NOT enforce
  any restrictions on this value; however, this may be necessary if the driver
  is unable to differentiate between certain BSON types (e.g. ``null``,
  ``undefined``) and the parameter being unspecified.

- Drivers SHOULD solicit an optional string value for ``$db``.

- Drivers MUST require ``$ref`` and ``$db`` (if specfied) to be strings but
  MUST NOT enforce any `naming restrictions`_ on the string values.

- Drivers MAY solicit extra, optional fields.

.. _naming restrictions: https://docs.mongodb.com/manual/reference/limits/#naming-restrictions

Decoding a BSON document to a DBRef model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers MAY support explicit and/or implicit decoding. An example of explicit
decoding might be a DBRef model constructor that takes a BSON document. An
example of implicit decoding might be configuring the driver's BSON codec to
automatically convert embedded documents that comply with the `DBRef Structure`_
into a DBRef model.

Drivers that provide implicit decoding MUST provide some way for applications to
opt out and allow DBRefs to be decoded like any other embedded document.

When decoding a BSON document to a DBRef model:

- Drivers MUST require ``$ref`` and ``$id`` to be present.

- Drivers MUST require ``$ref`` and ``$db`` (if present) to be strings but
  MUST NOT enforce any `naming restrictions`_ on the string values.

- Drivers MUST accept any BSON type for ``$id`` and MUST NOT enforce any
  restrictions on its value.

- Drivers MUST preserve extra, optional fields (beyond ``$ref``, ``$id``, and
  ``$db``) and MUST provide some way to access those fields via the DBRef model.
  For example, an accessor method that returns the original BSON document
  (including ``$ref``, etc.) would fulfill this requirement.

If a BSON document cannot be implicitly decoded to a DBRef model, it MUST be
left as-is (like any other embedded document). If a BSON document cannot be
explicitly decoded to a DBRef model, the driver MUST raise an error.


Encoding a DBRef model to a BSON document
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers MAY support explicit and/or implicit encoding. An example of explicit
encoding might be a DBRef method that returns its corresponding representation
as a BSON document. An example of implicit encoding might be configuring the
driver's BSON codec to automatically convert DBRef models to the corresponding
BSON document representation as needed.

If a driver supports implicit decoding of BSON to a DBRef model, it SHOULD also
support implicit encoding. Doing so will allow applications to more easily
round-trip DBRefs through the driver.

When encoding a DBRef model to BSON document:

- Drivers MUST encode all fields in the order defined in `DBRef Structure`_.

- Drivers MUST encode ``$ref`` and ``$id``. If ``$db`` was specified, it MUST be
  encoded after ``$id``. If any extra, optional fields were specified, they MUST
  be encoded after ``$id`` or ``$db``.

- If the DBRef includes any extra, optional fields after ``$id`` or ``$db``,
  drivers SHOULD attempt to preserve the original order of those fields relative
  to one another.


Test Plan
=========

The test plan consists of a series of prose tests. These tests are only relevant
to drivers that provide a DBRef model class.

The documents in these tests are presented as Extended JSON for readability;
however, readers should consider the field order pertinent when translating to
BSON (or their language equivalent).


Decoding
--------

These tests are only relevant to drivers that allow decoding into a DBRef model.
Drivers SHOULD implement these tests for both explicit and implicit decoding
code paths as needed.

1. Valid documents MUST be decoded to a DBRef model. For each of the following:

   a. ``{ "$ref": "coll0", "$id": { "$oid": "60a6fe9a54f4180c86309efa" } }``
   b. ``{ "$ref": "coll0", "$id": 1 }``
   c. ``{ "$ref": "coll0", "$id": null }``
   d. ``{ "$ref": "coll0", "$id": 1, "$db": "db0" }``

   Assert that each document is successfully decoded to a DBRef model. Assert
   that the ``$ref``, ``$id``, and ``$db`` (if applicable) fields have their
   expected value.

2. Valid documents with extra fields MUST be decoded to a DBRef model and the
   model MUST provide some way to access those extra fields. For each of the
   following:

   a. ``{ "$ref": "coll0", "$id": 1, "$db": "db0", "foo": "bar" }``
   b. ``{ "$ref": "coll0", "$id": 1, "foo": true, "bar": false }``
   c. ``{ "$ref": "coll0", "$id": 1, "meta": { "foo": 1, "bar": 2 } }``
   d. ``{ "$ref": "coll0", "$id": 1, "$foo": "bar" }``
   e. ``{ "$ref": "coll0", "$id": 1, "foo.bar": 0 }``

   Assert that each document is successfully decoded to a DBRef model. Assert
   that the ``$ref``, ``$id``, and ``$db`` (if applicable) fields have their
   expected value. Assert that it is possible to access all extra fields and
   that those fields have their expected value.

3. Documents with out of order fields that are otherwise valid MUST be decoded
   to a DBRef model. For each of the following:

   a. ``{ "$id": 1, "$ref": "coll0" }``
   b. ``{ "$db": "db0", "$ref": "coll0", "$id": 1 }``
   c. ``{ "foo": 1, "$id": 1, "$ref": "coll0" }``
   d. ``{ "foo": 1, "$ref": "coll0", "$id": 1, "$db": "db0" }``
   e. ``{ "foo": 1, "$ref": "coll0", "$id": 1, "$db": "db0", "bar": 1 }``

   Assert that each document is successfully decoded to a DBRef model. Assert
   that the ``$ref``, ``$id``, ``$db`` (if applicable), and any extra fields (if
   applicable) have their expected value.

4. Documents missing required fields MUST NOT be decoded to a DBRef model. For
   each of the following:

   a. ``{ "$ref": "coll0" }``
   b. ``{ "$id": { "$oid": "60a6fe9a54f4180c86309efa" } }``
   c. ``{ "$db": "db0" }``

   Assert that each document is not decoded to a DBRef model. In the context of
   implicit decoding, the document MUST be left as-is. In the context of
   explicit decoding, the DBRef decoding method MUST raise an error.

5. Documents with invalid types for ``$ref`` or ``$db`` MUST NOT be decoded to a
   DBRef model. For each of the following:

   a. ``{ "$ref": true, "$id": 1 }``
   b. ``{ "$ref": "coll0", "$id": 1, "$db": 1 }``

   Assert that each document is not decoded to a DBRef model. In the context of
   implicit decoding, the document MUST be left as-is. In the context of
   explicit decoding, the DBRef decoding method MUST raise an error.


Encoding
--------

These tests are only relevant to drivers that allow encoding a DBRef model.
Drivers SHOULD implement these tests for both explicit and implicit encoding
code paths as needed.

Drivers MAY use any method to create the DBRef model for each test (e.g.
constructor, explicit decoding method).

Drivers MAY skip tests that cannot be implemented as written (e.g. DBRef model
constructor does not support extra, optional fields and the driver also does not
support explicit/implicit decoding).

1. Encoding DBRefs with basic fields. For each of the following:

   a. ``{ "$ref": "coll0", "$id": { "$oid": "60a6fe9a54f4180c86309efa" } }``
   b. ``{ "$ref": "coll0", "$id": 1 }``
   c. ``{ "$ref": "coll0", "$id": null }``
   d. ``{ "$ref": "coll0", "$id": 1, "$db": "db0" }``

   Assert that each DBRef model is successfully encoded to a BSON document.
   Assert that the ``$ref``, ``$id``, and ``$db`` (if applicable) fields appear
   in the correct order and have their expected values.

2. Encoding DBRefs with extra, optional fields. For each of the following:

   a. ``{ "$ref": "coll0", "$id": 1, "$db": "db0", "foo": "bar" }``
   b. ``{ "$ref": "coll0", "$id": 1, "foo": true, "bar": false }``
   c. ``{ "$ref": "coll0", "$id": 1, "meta": { "foo": 1, "bar": 2 } }``
   d. ``{ "$ref": "coll0", "$id": 1, "$foo": "bar" }``
   e. ``{ "$ref": "coll0", "$id": 1, "foo.bar": 0 }``

   Assert that each DBRef model is successfully encoded to a BSON document.
   Assert that the ``$ref``, ``$id``, ``$db`` (if applicable), and any extra
   fields appear in the correct order and have their expected values.

3. Encoding DBRefs re-orders any out of order fields during decoding. This test
   MUST NOT use a constructor that solicits fields individually. For each of the
   following:

   a. ``{ "$id": 1, "$ref": "coll0" }``
   b. ``{ "$db": "db0", "$ref": "coll0", "$id": 1 }``
   c. ``{ "foo": 1, "$id": 1, "$ref": "coll0" }``
   d. ``{ "foo": 1, "$ref": "coll0", "$id": 1, "$db": "db0" }``
   e. ``{ "foo": 1, "$ref": "coll0", "$id": 1, "$db": "db0", "bar": 1 }``

   Assert that each document is successfully decoded to a DBRef model and then
   successfully encoded back to a BSON document. Assert that the order of fields
   in each encoded BSON document matches the following, respectively:

   a. ``{ "$ref": "coll0", "$id": 1 }``
   b. ``{ "$ref": "coll0", "$id": 1, "$db": "db0" }``
   c. ``{ "$ref": "coll0", "$id": 1, "foo": 1 }``
   d. ``{ "$ref": "coll0", "$id": 1, "$db": "db0", "foo": 1}``
   e. ``{ "$ref": "coll0", "$id": 1, "$db": "db0", "foo": 1, "bar": 1 }``


Design Rationale
================

In contrast to always encoding DBRefs with the correct field order, decoding
permits fields to be out of order (provided the document is otherwise valid).
This follows the `robustness principle`_ in having the driver be liberal in what
it accepts and conservative in what it emits. This does mean that round-tripping
an out of order DBRef through a driver could result in its field order being
changed; however, this behavior is consistent with existing behavior in drivers
that model DBRefs (e.g. C#, Java, Node, Python, Ruby) and applications can opt
out of implicit decoding if desired.

.. _robustness principle: https://en.wikipedia.org/wiki/Robustness_principle


Change Log
==========

This section is intentionally blank.
