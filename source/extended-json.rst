=============
Extended JSON
=============

:Spec: 587
:Spec-ticket: SPEC-587
:Title: Extended JSON
:Author: Luke Lovett
:Spec Lead: David Golden
:Advisory Group: Mike O'Brien, Christian Kvalheim, Hannes Magnusson
:Status: Accepted
:Type: Standards
:Last Modified: January 23, 2017
:Version: 1.0.0

.. contents::

--------

Abstract
========

MongoDB extended JSON is a string format for representing BSON documents. This
specification defines the canonical format for representing each BSON type in
the extended JSON format. Thus, a tool that implements extended JSON will be
able to parse the output of any tool that emits canonical extended JSON.

META
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Terms
=====

*Historical extended JSON* - A string format based on the JSON standard that
describes a BSON document. The historical extended JSON format does not describe
a specific, standardized format, and many tools, drivers, and libraries
implement extended JSON in conflicting ways.

*Extended JSON* - A string format based on the JSON standard that describes BSON
documents. This specification gives a formal definition to this format.

Specification
=============

Parsers
-------

An extended JSON parser (hereafter just "parser") is a tool that transforms an
extended JSON string into another representation, such as BSON or a
language-specific data structure. A parser MUST accept all strings in the
canonical extended JSON format. A parser MAY also accept strings that adhere to
other formats, such as historical extended JSON formats emitted by old versions
of mongoexport. A parser SHOULD support at least 200 `levels of nesting`_ in an
extended JSON document but MAY set other limits on strings it can accept as
defined in `section 9`_ of the `JSON specification`_.

.. _section 9: https://tools.ietf.org/html/rfc7159#section-9

A parser can generally distinguish JSON representations of BSON types by the
presence of a key that starts with the ``$`` symbol. For example: ``{"$symbol":
"banana"}``. However, not every key that starts with $ will indicate the element
represents some BSON value. If such key names of the element do not exactly
match those of a format given in the `Canonical Format Table`_, the element MUST
be interpreted as an ordinary JSON element. If the key names match, but the
element cannot be parsed for other reasons (e.g. ``{"$timestamp": "-4"}``), then
the parser MUST report an error.

When parsing an extended JSON document, parsers MUST NOT consider key ordering
as having significance. For example, the document ``{"$code": "function(){}",
"$scope": {}}`` must be considered identical to ``{"$scope": {}, "$code":
"function(){}"}``.

.. _JSON specification: https://tools.ietf.org/html/rfc7159

Generators
----------

An extended JSON generator (hereafter just "generator") produces strings in
extended JSON. A generator MUST be able to produce strings that conform strictly
to the canonical extended JSON format. Such generators SHOULD produce such
strings by default. If a generator does not produce strings in the canonical
format by default, then that generator MUST be configurable to use the canonical
format. A generator MAY be capable of exporting strings that adhere to other
formats, such as historical extended JSON formats emitted by old versions of
mongoexport. A generator SHOULD support at least 100 `levels of nesting`_ in a
BSON document.

Transforming BSON
.................

When transforming a BSON value into extended JSON text, a generator MUST use the
corresponding format for the BSON type given in the `Canonical Format
Table`_. When transforming a BSON document into extended JSON text, a generator
SHOULD emit the JSON keys and values in the same order as given in the BSON
document.

Transforming Language-Specific Data Structures
..............................................

When there is a corresponding BSON type for a given language-specific type, a
generator MUST convert this type to extended JSON in a way that corresponds to
the BSON representation. For example, a Python ``datetime`` object must be
represented the same as a BSON datetime type.

Extended JSON Format
--------------------

The extended JSON grammar extends the JSON grammar as defined in `section 2`_ of
the `JSON specification`_ by augmenting the possible JSON values as defined in
`Section 3`_. An extended JSON value MUST conform to one of the formats given in
the second column of the following table:

.. _section 2: https://tools.ietf.org/html/rfc7159#section-2
.. _section 3: https://tools.ietf.org/html/rfc7159#section-3

.. _Canonical Format Table:

Canonical Format Table
----------------------

Notes
.....

* Keys within extended JSON values SHOULD be emitted in the order described. All
  keys MUST be emitted, and any other elements MUST NOT be emitted.
* Types in *italics* are defined elsewhere in the table or in the `JSON
  specification`_.
* Types in <angle brackets> detail the contents of a value.

+--------------------+----------------------------------------------------------+
|**BSON 1.1 Type or  |**Extended JSON Format**                                  |
|Convention**        |                                                          |
+--------------------+----------------------------------------------------------+
|ObjectId            |{"$oid": <ObjectId bytes as 24-character, big-endian *hex |
|                    |string* [#]_>}                                            |
+--------------------+----------------------------------------------------------+
|Symbol              |{"$symbol": *string*}                                     |
+--------------------+----------------------------------------------------------+
|String              |*string*                                                  |
+--------------------+----------------------------------------------------------+
|Int32               |{"$numberInt": <32-bit signed integer as a *string*>}     |
+--------------------+----------------------------------------------------------+
|Int64               |{"$numberLong": <64-bit signed integer as a *string*>}    |
+--------------------+----------------------------------------------------------+
|Double              |{"$numberDouble": <64-bit binary floating point as a      |
|                    |*string*>}                                                |
+--------------------+----------------------------------------------------------+
|Decimal128          |{"$numberDecimal": <decimal as a *string*>} [#]_          |
+--------------------+----------------------------------------------------------+
|Binary              |{"$binary": <base64-encoded (with padding as ``=``)       |
|                    |payload as a *string*>, "$type": <BSON binary type as a   |
|                    |one- or two-character *hex string*>}                      |
+--------------------+----------------------------------------------------------+
|Code                |{"$code": *string*}                                       |
+--------------------+----------------------------------------------------------+
|CodeWScope          |{"$code": *string*, "$scope": *Document*}                 |
+--------------------+----------------------------------------------------------+
|Document            |*object* (with extended JSON extensions)                  |
+--------------------+----------------------------------------------------------+
|Timestamp           |{"$timestamp": <64-bit unsigned integer as a *string*>}   |
+--------------------+----------------------------------------------------------+
|Regex               |{"$regex": *string*, "$options": <BSON regex options as a |
|                    |*string* or "" [#]_>}                                     |
+--------------------+----------------------------------------------------------+
|DBPointer           |{"$dbPointer": {"$ref": <namespace [#]_ as a *string*>,   |
|                    |"$id": *ObjectId*}}                                       |
+--------------------+----------------------------------------------------------+
|Datetime            |{"$date": {"$numberLong": <64-bit signed integer giving ms|
|                    |since the epoch, as a *string*>}}                         |
+--------------------+----------------------------------------------------------+
|DBRef [#]_          |{"$ref": <collection name as a *string*>, "$id":          |
|                    |<extended JSON for the id>}                               |
|Note: this is not   |                                                          |
|technically a BSON  |If the generator supports DBRefs with a database          |
|type, but it is a   |component, and the database component is nonempty:        |
|common convention.  |                                                          |
|                    |{"$ref": <collection name as a *string*>, "$id": <extended|
|                    |JSON for the id>, "$db": <database name as a *string*>}   |
|                    |                                                          |
|                    |DBRefs may also have other fields that do not begin with  |
|                    |``$``, which MUST appear after ``$id`` and ``$db`` (if    |
|                    |supported).                                               |
+--------------------+----------------------------------------------------------+
|MinKey              |{"$minKey": 1}                                            |
+--------------------+----------------------------------------------------------+
|MaxKey              |{"$maxKey": 1}                                            |
+--------------------+----------------------------------------------------------+
|Undefined           |{"$undefined": *true*}                                    |
+--------------------+----------------------------------------------------------+
|Array               |*array*                                                   |
+--------------------+----------------------------------------------------------+
|Boolean             |*true* or *false*                                         |
+--------------------+----------------------------------------------------------+
|Null                |*null*                                                    |
+--------------------+----------------------------------------------------------+

.. [#] A *hex string* is a JSON string that contains only hexadecimal
                digits [0-9a-f] (uppercase is not canonical)
.. [#] This MUST conform to the `Decimal128 specification`_

.. [#] BSON Regex options MUST be in alphabetical order.

.. [#] See https://docs.mongodb.com/manual/reference/glossary/#term-namespace

.. [#] See https://docs.mongodb.com/manual/reference/database-references/#dbrefs

.. _Decimal128 specification: https://github.com/mongodb/specifications/blob/master/source/bson-decimal128/decimal128.rst#writing-to-extended-json

Representation of Special Numeric Values
----------------------------------------

Following the `extended JSON format for the Decimal128 type`_, special numeric
values are encoded as follows:

+----------------------------------------+----------------------------------------+
|**Value**                               |**String**                              |
+----------------------------------------+----------------------------------------+
|Positive Infinity                       |``Infinity``                            |
+----------------------------------------+----------------------------------------+
|Negative Infinity                       |``-Infinity``                           |
+----------------------------------------+----------------------------------------+
|NaN (all variants)                      |``NaN``                                 |
+----------------------------------------+----------------------------------------+

.. _extended JSON format for the Decimal128 type: https://github.com/mongodb/specifications/blob/master/source/bson-decimal128/decimal128.rst#to-string-representation

For example, a BSON floating-point number with a value of negative infinity
would be encoded as extended JSON as follows::

  {"$numberDouble": "-Infinity"}

Option Names
------------

Parsers and generators MAY be configurable to handle both canonical and
historical extended JSON formats. In such a case, the following option names MAY
be used to distinguish between these two formats:

* ``canonicalExtendedJSON`` (references extended JSON as described in this specification)
* ``legacyExtendedJSON`` (references historical extended JSON)

This specification does not require any specific options to be made available.

Extended JSON Example
=====================

Consider the following document, written in Groovy with the MongoDB Java Driver::

  {
    "_id": new ObjectId("57e193d7a9cc81b4027498b5"),
    "Symbol": new BsonSymbol("symbol"),
    "String": "string",
    "Int32": 42,
    "Int64": 42L,
    "Double": 42.42,
    "SpecialFloat": Float.NaN,
    "Decimal": new Decimal128(1234),
    "Binary": UUID.fromString("c8edabc3-f738-4ca3-b68d-ab92a91478a3"),
    "BinaryUserDefined": new Binary((byte) 0x80, new byte[]{1, 2, 3, 4, 5}),
    "Code": new Code("function() {}"),
    "CodeWithScope": new CodeWithScope("function() {}", new Document()),
    "Subdocument": new Document("foo", "bar"),
    "Array": Arrays.asList(1, 2, 3, 4, 5),
    "Timestamp": new BSONTimestamp(42, 1),
    "Regex": new BsonRegularExpression("pattern"),
    "DatetimeEpoch": new Date(0),
    "DatetimePositive": new Date(Long.MAX_VALUE),
    "DatetimeNegative": new Date(Long.MIN_VALUE),
    "True": true,
    "False": false,
    "DBPointer": new BsonDbPointer(
        "db.collection", new ObjectId("57e193d7a9cc81b4027498b1")),
    "DBRef": new DBRef(
        "database", "collection", new ObjectId("57fd71e96e32ab4225b723fb")),
    "DBRefNoDB": new DBRef(
        "collection", new ObjectId("57fd71e96e32ab4225b723fb")),
    "Minkey": new MinKey(),
    "Maxkey": new MaxKey(),
    "Null": null,
    "Undefined": new BsonUndefined()
  }

The above document is transformed into the following (newlines and spaces added
for readability)::

  {
     "_id": {
         "$oid": "57e193d7a9cc81b4027498b5"
     },
     "Symbol": {
         "$symbol": "symbol"
     },
     "String": "string",
     "Int32": {
         "$numberInt": "42"
     },
     "Int64": {
         "$numberLong": "42"
     },
     "Double": {
         "$numberDouble": "42.42"
     },
     "SpecialFloat": {
         "$numberDouble": "NaN"
     },
     "Decimal": {
         "$numberDecimal": "1234"
     },
     "Binary": {
         "$binary": "o0w498Or7cijeBSpkquNtg==",
         "$type": "03"
     },
     "BinaryUserDefined": {
         "$binary": "AQIDBAU=",
         "$type": "80"
     },
     "Code": {
         "$code": "function() {}"
     },
     "CodeWithScope": {
         "$code": "function() {}",
         "$scope": {}
     },
     "Subdocument": {
         "foo": "bar"
     },
     "Array": [
         {"$numberInt": "1"},
         {"$numberInt": "2"},
         {"$numberInt": "3"},
         {"$numberInt": "4"},
         {"$numberInt": "5"}
     ],
     "Timestamp": {
         "$timestamp": "180388626433"
     },
     "Regex": {
         "$regex": "pattern",
         "$options": ""
     },
     "DatetimeEpoch": {
         "$date": {
             "$numberLong": "0"
         }
     },
     "DatetimePositive": {
         "$date": {
             "$numberLong": "9223372036854775807"
         }
     },
     "DatetimeNegative": {
         "$date": {
             "$numberLong": "-9223372036854775808"
         }
     },
     "True": true,
     "False": false,
     "DBPointer": {
         "$dbPointer": {
             "$ref": "db.collection",
             "$id": {
                 "$oid": "57e193d7a9cc81b4027498b1"
             }
         }
     },
     "DBRef": {
         "$ref": "collection",
         "$id": {
             "$oid": "57fd71e96e32ab4225b723fb"
         },
         "$db": "database"
     },
     "DBRefNoDB" {
         "$ref": "collection",
         "$id": {
             "$oid": "57fd71e96e32ab4225b723fb"
         }
     },
     "Minkey": {
         "$minKey": 1
     },
     "Maxkey": {
         "$maxKey": 1
     },
     "Null": null,
     "Undefined": {
         "$undefined": true
     }
  }

Test Plan
=========

Drivers, tools, and libraries can test their compliance to this specification by
running the tests in version 1.3 and above of the `BSON Corpus Test Suite`_.

.. _BSON Corpus Test Suite: https://github.com/mongodb/specifications/blob/master/source/bson-corpus/bson-corpus.rst

Motivation for Change
=====================

There existed many extended JSON parser and generator implementations prior to
this specification that used conflicting formats, since there was no agreement
on the precise format of extended JSON. This resulted in problems where the
output of some generators could not be consumed by some parsers.

Design Rationale
================

Of Parsers and Generators
-------------------------

Parsers MUST accept all strings in canonical extended JSON, and generators MUST
have the ability to output canonical extended JSON. This way, a parser will
always be able to accept strings emitted by a properly configured
generator. Parsers and generators are permitted to accept and output strings in
other formats as well for backwards compatibility.

.. _levels of nesting:

Generators SHOULD support at least 100 levels of nesting in a BSON document
being transformed to extended JSON. This aligns with MongoDB's own limitation of
100 levels of nesting.

Parsers SHOULD support at least 200 levels of nesting in extended JSON text,
since the extended JSON language can double the level of apparent nesting of a
BSON document by wrapping certain types in their own documents.

Of Canonical Formats
--------------------

Prior to this specification, BSON types fell into three categories with respect
to historical extended JSON:

1. A single, portable representation for the type already existed.

2. Multiple representations for the type existed among various extended JSON
   generators, and those representations were in conflict with each other or
   with current portability goals.

3. No historical extended JSON representation existed.

If a BSON type fell into category (1), this specification just declares that
form to be canonical, since all drivers, tools, and libraries already know how
to parse or output this form.

If a BSON type fell into category (2), this specification selects a new common
representation for the type to be canonical. Conflicting formats were gathered
by surveying a number of extended JSON generators, including the MongoDB Java
Driver (version 3.3.0), the MongoDB Python Driver (version 3.4.0.dev0), the
MongoDB Extended JSON module on NPM (version 1.7.1), and each minor version of
mongoexport from 2.4.14 through 3.3.12. When possible, we set the "strict"
option on the JSON codec. The following BSON types had conflicting extended JSON
representations:

Binary
......

Some implementations write the extended JSON form of a Binary object with a
strict two-hexadecimal digit subtype (e.g. they output a leading ``0`` for
subtypes < 16). However, the NPM mongodb-extended-json module and Java driver
use a single hexadecimal digit to represent subtypes less than 16. This
specification makes the two-digit representation canonical.

Code
....

Mongoexport 2.4 does not quote the ``Code`` value when writing out the extended
JSON form of a BSON Code object. All other implementations do so. This spec
canonicalises the form where the Javascript code is quoted, since the latter
form adheres to the JSON specification and the former does not. As an additional
note, the NPM mongodb-extended-json module uses the form ``{"code": "<javascript
code>"}, omitting the dollar sign (``$``) from the key. This form is
indistinguishable from a document that happens to contain the key ``code``, so
this specification does not endorse this form.

CodeWithScope
.............

In addition to the same variants as BSON Code types, there are other variations
when turning CodeWithScope objects into extended JSON. Mongoexport 2.4 and 2.6
omit the scope portion of CodeWithScope if it is empty, making the output
indistinguishable from a Code type. All other implementations include the empty
scope. This specification therefore canonicalises the form where the scope is
always included. The presence of ``$scope`` is what differentiates Code from
CodeWithScope.

Datetime
........

Mongoexport 2.4 and the Java driver always transform a Datetime object into an
extended JSON string of the form ``{"$date": <ms since epoch>}``. This form has
the problem of a potential loss of precision or range on the Datetimes that can
be represented. Mongoexport 2.6 transforms Datetime objects into an extended
JSON string of the form ``{"$date": <ISO-8601 date string in local time>}`` for
dates starting at or after the Unix epoch (UTC). Dates prior to the epoch take
the form ``{"$date": {"$numberLong": "<ms since epoch>"}}``. Starting in version
3.0, mongoexport always turns Datetime objects into strings of the form
``{"$date": <ISO-8601 date string in UTC>}``. The NPM mongodb-extended-json
module does the same. The Python driver can also transform Datetime objects into
strings like ``{"$date": {"$numberLong": "<ms since epoch>"}}``. This
specification canonicalises this form, since this form is the most portable.

DBPointer
.........

Mongoexport 2.4 and 2.6 use the form ``{"$ref": <namespace>, "$id": <hex
string>}``. All other implementations studied include the canonical ``ObjectId``
form: ``{"$ref": <namespace>, "$id": {"$oid": <hex string>}}``. Neither of these
forms are distinguishable from that of DBRef, so this specification creates a
new format: ``{"$dbPointer": {"$ref": <namespace>, "$id": {"$oid": <hex
string>}}}``.

Finally, if a BSON type fell into category (3), this specification proposes a
format for the type. The following new extended JSON forms are introduced by
this spec:

* ``$dbPointer`` - Most generator implementations emit this indistinguishably
  from DBRef, so this specification creates a new format so that the type can be
  round-tripped when possible. See also the discussion above about DBPointer.

* ``$numberInt`` - This is used to preserve the "int" type while round-tripping
  documents to and from extended JSON. Without using ``$numberInt``, this type
  will be indistinguishable from a double in certain languages where the
  distinction does not exist, such as Javascript.

* ``$numberDouble`` - This is used to preserve the ``double`` type while
  round-tripping documents to and from extended JSON and to represent special
  values like NaN or Inf which are not part of the standard JSON specification.

* ``$symbol`` - The use of the ``$symbol`` key preserves the symbol type when
  round-tripping documents to and from extended JSON.

Timestamp Format
................

The extended JSON representation for a BSON timestamp changed from its previous
format of ``{"$timestamp": {"t": <seconds since the epoch>, "i":
<increment>}}``. The old format did not quote the numeric timestamp and
increment, making this form difficult to parse on 32-bit systems. Furthermore,
splitting the timestamp up into two pieces makes the format more difficult to
generate and parse without any gain, since a BSON timestamp is one number, and
the increment and timestamp pieces individually are not friendlier for humans to
read.

Backwards Compatibility
.......................

Although extended JSON parsers are required to accept all strings in canonical
extended JSON format, they may accept strings in other formats as well. This
allows parsers to accept extended JSON emitted by tools that predate this
specification.

Similarly, generators are permitted to output strings in other formats than
canonical extended JSON. This allows such a tool to transform a BSON document
into some interchange format for consumption by a tool that predates this
specification.

Reference Implementation
========================

PyMongo implements the canonical extended JSON format, which must be chosen by
selecting the right option on the ``JSONOptions`` object::

  from bson.json_util import dumps, DatetimeRepresentation, CANONICAL_JSON_OPTIONS

  dumps(document, json_options=CANONICAL_JSON_OPTIONS)

Implementation Notes
====================

JSON File Format
----------------

Some applications like mongoexport may wish to write multiple extended JSON
documents to a single file. One way to do this is to list each JSON document
one-per-line. When doing this, it is important to ensure that special characters
like newlines are encoded properly (e.g. ``\n``).

Duplicate Keys
--------------

The BSON specification allows for duplicate key names within the same BSON
document. The JSON specification says that names within an object should be
unique, and many JSON libraries are incapable of handling this scenario. Please
note there is no defined extended JSON representation for a BSON document that
contains duplicate key names.

Key Escaping
------------

There is no escape mechanism for keys that are prefixed with the dollar sign
(``$``) when parsing extended JSON. In other words, the following Java code
snippet produces two documents that a generator would transform into identical
extended JSON strings::

  new Document("s", new Document("$symbol": "val"))
  new Document("s", new Symbol("val"))

The extended JSON for the above documents is the same::

  {"s": {"$symbol": "val"}}

An extended JSON parser will parse the above as a document with a name ``s``
whose value is a BSON Symbol with the value ``val`` (i.e. the second line of the
above Java code snippet).

Future Work
===========

This specification will need to be amended if future BSON types are added to the
BSON specification.

Q&A
===

*Q*. My BSON parser doesn’t distinguish every BSON type. Does my extended JSON
 generator need to distinguish these types?

*A*. No. Some BSON parsers do not emit a unique type for each BSON type, making
 round-tripping BSON through such libraries impossible without changing the
 document. For example, a ``DBPointer`` will be parsed into a ``DBRef`` by
 PyMongo. In such cases, a generator must emit the extended JSON form for
 whatever type the BSON parser emitted. It does not need to preserve type
 information when that information has been lost by the BSON parser.

*Q*. What if a parser encounters a "malformed" extended JSON string like
 {"$symbol": "banana", "$foo": "peel"}?

*A*. Such a string is not malformed. It does not match any of the extended
 formats described in the Canonical Format Table and therefore is to be
 interpreted as any other JSON object. In other words, ``{"$symbol": "banana",
 "$foo": "peel"}`` is just a JSON object with two keys that map to two strings
 and does not represent a BSON symbol.

*Q*. Sometimes I see the term "extjson" used in other specifications. Is
"extjson" related to this specification?

*A*. Yes, "extjson" is short for "extended JSON".
