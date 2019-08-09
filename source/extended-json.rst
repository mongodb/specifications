=============
Extended JSON
=============

:Spec: 587
:Spec-ticket: SPEC-587
:Title: Extended JSON
:Author: Luke Lovett, David Golden
:Spec Lead: David Golden, Jeff Yemin
:Advisory Group: Jeff Yemin, Christian Kvalheim, Hannes Magnusson, Matt Broadstone, Jesse Davis
:Status: Proposed
:Type: Standards
:Last Modified: July 20, 2017
:Version: 2.0.0

.. contents::

--------

Abstract
========

MongoDB Extended JSON is a string format for representing BSON documents. This
specification defines the canonical format for representing each BSON type in
the Extended JSON format. Thus, a tool that implements Extended JSON will be
able to parse the output of any tool that emits Canonical Extended JSON.  It also
defines a Relaxed Extended JSON format that improves readability at the expense
of type information preservation.

META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Naming
------

Acceptable naming deviations should fall within the basic style of the
language. For example, ``CanonicalExtendedJSON`` would be a name in Java, where
camel-case method names are used, but in Ruby ``canonical_extended_json`` would
be acceptable.

Terms
=====

*Type wrapper object* - a JSON value consisting of an object with one or more
``$``-prefixed keys that collectively encode a BSON type and its corresponding
value using only JSON value primitives.

*Extended JSON* - A general term for one of many string formats based on the
JSON standard that describes how to represent BSON documents in JSON using
standard JSON types and/or type wrapper objects. This specification gives a
formal definition to variations of such a format.

*Relaxed Extended JSON* - A string format based on the JSON standard that
describes BSON documents. Relaxed Extended JSON emphasizes readability and
interoperability at the expense of type preservation.

*Canonical Extended JSON* - A string format based on the JSON standard that
describes BSON documents. Canonical Extended JSON emphasizes type preservation
at the expense of readability and interoperability.

*Legacy Extended JSON* - A string format based on the JSON standard that
describes a BSON document. The Legacy Extended JSON format does not describe
a specific, standardized format, and many tools, drivers, and libraries
implement Extended JSON in conflicting ways.

Specification
=============

Extended JSON Format
--------------------

The Extended JSON grammar extends the JSON grammar as defined in `section 2`_ of
the `JSON specification`_ by augmenting the possible JSON values as defined in
`Section 3`_. This specification defines two formats for Extended JSON:

* Canonical Extended JSON
* Relaxed Extended JSON

An Extended JSON value MUST conform to one of these two formats as described
in the table below.

.. _section 2: https://tools.ietf.org/html/rfc7159#section-2
.. _section 3: https://tools.ietf.org/html/rfc7159#section-3

Notes on grammar
................

* Key order:

  * Keys within Canonical Extended JSON type wrapper objects SHOULD be emitted
    in the order described.

  * Keys within Relaxed Extended JSON type wrapper objects are unordered.

* Terms in *italics* represent types defined elsewhere in the table or in the
  `JSON specification`_.

* JSON *numbers* (as defined in `Section 6`_ of the JSON specification) include
  both integer and floating point types.  For the purpose of this document, we
  define the following subtypes:

  * Type *integer* means a JSON *number* without *frac* or *exp* components;
    this is expressed in the JSON spec grammer as ``[minus] int``.

  * Type *non-integer* means a JSON *number* that is not an *integer*; it
    must include either a *frac* or *exp* component or both.

  * Type *pos-integer* means a non-negative JSON *number* without *frac*
    or *exp* components; this is expressed in the JSON spec grammar as ``int``.

* A *hex string* is a JSON *string* that contains only hexadecimal
  digits [0-9a-f].  It SHOULD be emitted lower-case, but MUST be read
  in a case-insensitive fashion.

* <Angle brackets> detail the contents of a value, including type information.

* \[Square brackets\] specify a type constraint that restricts the specification
  to a particular range or set of values.

.. _section 6: https://tools.ietf.org/html/rfc7159#section-6

Conversion table
................

+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|**BSON 1.1 Type or  |**Canonical Extended JSON Format**                        |**Relaxed Extended JSON Format**                       |
|Convention**        |                                                          |                                                       |
+====================+==========================================================+=======================================================+
|ObjectId            |{"$oid": <ObjectId bytes as 24-character, big-endian *hex | <Same as Canonical Extended JSON>                     |
|                    |string*>}                                                 |                                                       |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Symbol              |{"$symbol": *string*}                                     | <Same as Canonical Extended JSON>                     |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|String              |*string*                                                  | <Same as Canonical Extended JSON>                     |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Int32               |{"$numberInt": <32-bit signed integer as a *string*>}     | *integer*                                             |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Int64               |{"$numberLong": <64-bit signed integer as a *string*>}    | *integer*                                             |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Double \[finite\]   |{"$numberDouble": <64-bit signed floating point as a      | *non-integer*                                         |
|                    |decimal *string*>}                                        |                                                       |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Double              |{"$numberDouble": <One of the *strings*: "Infinity",      | <Same as Canonical Extended JSON>                     |
|\[non-finite\]      |"-Infinity", or "NaN">}                                   |                                                       |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Decimal128          |{"$numberDecimal": <decimal as a *string*>} [#]_          | <Same as Canonical Extended JSON>                     |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Binary              |{"$binary": {"base64": <base64-encoded (with padding as   | <Same as Canonical Extended JSON>                     |
|                    |``=``) payload as a *string*>, "subType": <BSON binary    |                                                       |
|                    |type as a one- or two-character *hex string*>}}           |                                                       |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Code                |{"$code": *string*}                                       | <Same as Canonical Extended JSON>                     |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|CodeWScope          |{"$code": *string*, "$scope": *Document*}                 | <Same as Canonical Extended JSON>                     |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Document            |*object* (with Extended JSON extensions)                  | <Same as Canonical Extended JSON>                     |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Timestamp           |{"$timestamp": {"t": *pos-integer*, "i": *pos-integer*}}  | <Same as Canonical Extended JSON>                     |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Regular Expression  |{"$regularExpression": {pattern: *string*,                | <Same as Canonical Extended JSON>                     |
|                    |"options": <BSON regular expression options as a *string* |                                                       |
|                    |or "" [#]_>}}                                             |                                                       |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|DBPointer           |{"$dbPointer": {"$ref": <namespace [#]_ as a *string*>,   | <Same as Canonical Extended JSON>                     |
|                    |"$id": *ObjectId*}}                                       |                                                       |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Datetime            |{"$date": {"$numberLong": <64-bit signed integer          | {"$date": <ISO-8601 Internet Date/Time Format         |
|\[year from 1970    |giving millisecs relative to the epoch, as a *string*>}}  | as decribed in RFC-3339 [#]_ with maximum time        |
|to 9999 inclusive\] |                                                          | precision of milliseconds [#]_ as a *string*>}        |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Datetime            |{"$date": {"$numberLong": <64-bit signed integer          | <Same as Canonical Extended JSON>                     |
|\[year before 1970  |giving millisecs relative to the epoch, as a *string*>}}  |                                                       |
|or after 9999\]     |                                                          |                                                       |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|DBRef [#]_          |{"$ref": <collection name as a *string*>, "$id":          | <Same as Canonical Extended JSON>                     |
|                    |<Extended JSON for the id>}                               |                                                       |
|Note: this is not   |                                                          |                                                       |
|technically a BSON  |If the generator supports DBRefs with a database          |                                                       |
|type, but it is a   |component, and the database component is nonempty:        |                                                       |
|common convention.  |                                                          |                                                       |
|                    |{"$ref": <collection name as a *string*>,                 |                                                       |
|                    | "$id": <Extended JSON for the id>,                       |                                                       |
|                    | "$db": <database name as a *string*>}                    |                                                       |
|                    |                                                          |                                                       |
|                    |DBRefs may also have other fields that do not begin with  |                                                       |
|                    |``$``, which MUST appear after ``$id`` and ``$db`` (if    |                                                       |
|                    |supported).                                               |                                                       |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|MinKey              |{"$minKey": 1}                                            | <Same as Canonical Extended JSON>                     |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|MaxKey              |{"$maxKey": 1}                                            | <Same as Canonical Extended JSON>                     |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Undefined           |{"$undefined": *true*}                                    | <Same as Canonical Extended JSON>                     |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Array               |*array*                                                   | <Same as Canonical Extended JSON>                     |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Boolean             |*true* or *false*                                         | <Same as Canonical Extended JSON>                     |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+
|Null                |*null*                                                    | <Same as Canonical Extended JSON>                     |
+--------------------+----------------------------------------------------------+-------------------------------------------------------+

.. [#] This MUST conform to the `Decimal128 specification`_

.. [#] BSON Regular Expression options MUST be in alphabetical order.

.. [#] See https://docs.mongodb.com/manual/reference/glossary/#term-namespace

.. [#] See https://tools.ietf.org/html/rfc3339#section-5.6

.. [#] Fractional seconds SHOULD have exactly 3 decimal places if the fractional part
   is non-zero.  Otherwise, fractional seconds SHOULD be omitted if zero.

.. [#] See https://docs.mongodb.com/manual/reference/database-references/#dbrefs

.. _Decimal128 specification: https://github.com/mongodb/specifications/blob/master/source/bson-decimal128/decimal128.rst#writing-to-extended-json

Representation of Non-finite Numeric Values
...........................................

Following the `Extended JSON format for the Decimal128 type`_, non-finite numeric
values are encoded as follows:

+----------------------------------------+----------------------------------------+
|**Value**                               |**String**                              |
+========================================+========================================+
|Positive Infinity                       |``Infinity``                            |
+----------------------------------------+----------------------------------------+
|Negative Infinity                       |``-Infinity``                           |
+----------------------------------------+----------------------------------------+
|NaN (all variants)                      |``NaN``                                 |
+----------------------------------------+----------------------------------------+

.. _Extended JSON format for the Decimal128 type: https://github.com/mongodb/specifications/blob/master/source/bson-decimal128/decimal128.rst#to-string-representation

For example, a BSON floating-point number with a value of negative infinity
would be encoded as Extended JSON as follows::

  {"$numberDouble": "-Infinity"}

Parsers
-------

An Extended JSON parser (hereafter just "parser") is a tool that transforms an
Extended JSON string into another representation, such as BSON or a
language-native data structure.

By default, a parser MUST accept values in either Canonical Extended JSON
format or Relaxed Extended JSON format as described in this specification. A
parser MAY allow users to restrict parsing to only Canonical Extended JSON
format or only Relaxed Extended JSON format.

A parser MAY also accept strings that adhere to other formats, such as
Legacy Extended JSON formats emitted by old versions of mongoexport or
other tools, but only if explicitly configured to do so.

A parser that accepts Legacy Extended JSON MUST be configurable such that a JSON
text of a MongoDB query filter containing the `regex`_ query operator can be
parsed, e.g.::

    { "$regex": {
        "$regularExpression" : { "pattern": "foo*", "options": "" }
      },
      "$options" : "ix"
    }

or::

    { "$regex": {
        "$regularExpression" : { "pattern": "foo*", "options": "" }
      }
    }

A parser that accepts Legacy Extended JSON MUST be configurable such that a JSON
text of a MongoDB query filter containing the `type`_ query operator can be
parsed, e.g.::

    { "zipCode" : { $type : 2 } }

or::

    { "zipCode" : { $type : "string" } }

A parser SHOULD support at least 200 `levels of nesting`_ in an Extended JSON
document but MAY set other limits on strings it can accept as defined in
`section 9`_ of the `JSON specification`_.

When parsing a JSON object other than the top-level object, the presence of a
``$``-prefixed key indicates the object could be a type wrapper object as
described in the Extended JSON `Conversion table`_.  In such a case, the parser
MUST follow these rules, unless configured to allow Legacy Extended JSON,
in which case it SHOULD follow these rules:

* Parsers MUST NOT consider key order as having significance. For example,
  the document ``{"$code": "function(){}", "$scope": {}}`` must be considered
  identical to ``{"$scope": {}, "$code": "function(){}"}``.

* If the parsed object contains any of the special **keys** in the Conversion
  table such as ``"$binary"``, ``"$timestamp"``, etc., then it must contain
  exactly the keys of a type wrapper. Any missing or extra keys constitute an
  error.

* If the **keys** of the parsed object exactly match the **keys** of a type
  wrapper in the Conversion table, and the **values** of the parsed object have
  the correct type for the type wrapper as described in the Conversion table,
  then the parser MUST interpret the parsed object as a type wrapper object of
  the corresponding type.

* If the **keys** of the parsed object exactly match the **keys** of a type
  wrapper in the Conversion table, but any of the **values** are of an incorrect
  type, then the parser MUST report an error.

.. _regex: https://docs.mongodb.com/manual/reference/operator/query/regex/

.. _type: https://docs.mongodb.com/manual/reference/operator/query/type/

.. _section 9: https://tools.ietf.org/html/rfc7159#section-9

.. _JSON specification: https://tools.ietf.org/html/rfc7159

Special rules for parsing JSON numbers
......................................

The Relaxed Extended JSON format uses JSON numbers for several different
BSON types.  In order to allow parsers to use language-native JSON decoders
(which may not distinguish numeric type when parsing), the following rules apply
to parsing JSON numbers:

* If the number is a *non-integer*, parsers SHOULD interpret it as BSON Double.

* If the number is an *integer*, parsers SHOULD interpret it as being of the
  smallest BSON integer type that can represent the number exactly.  If a parser
  is unable to represent the number exactly as an integer (e.g.  a large 64-bit
  number on a 32-bit platform), it MUST interpret it as a BSON Double even if
  this results in a loss of precision.  The parser MUST NOT interpret it as a
  BSON String containing a decimal representation of the number.

Generators
----------

An Extended JSON generator (hereafter just "generator") produces strings in an
Extended JSON format.

A generator MUST allow users to produce strings in either the Canonical
Extended JSON format or the Relaxed Extended JSON format.  If generators
provide a default format, the default SHOULD be the Relaxed Extended JSON
format.

A generator MAY be capable of exporting strings that adhere to other
formats, such as Legacy Extended JSON formats.

A generator SHOULD support at least 100 `levels of nesting`_ in a BSON
document.

Transforming BSON
.................

Given a BSON document (e.g. a buffer of bytes meeting the requirements of the
BSON specification), a generator MUST use the corresponding JSON values or
Extended JSON type wrapper objects for the BSON type given in the Extended JSON
`Conversion table`_ for the desired format.  When transforming a BSON document
into Extended JSON text, a generator SHOULD emit the JSON keys and values in
the same order as given in the BSON document.

Transforming Language-Native data
.................................

Given language-native data (e.g. type primitives, container types, classes,
etc.), if there is a semantically-equivalent BSON type for a given
language-native type, a generator MUST use the corresponding JSON values or
Extended JSON type wrapper objects for the BSON type given in the Extended JSON
`Conversion table`_ for the desired format.  For example, a Python ``datetime``
object must be represented the same as a BSON datetime type.  A generator
SHOULD error if a language-native type has no semantically-equivalent BSON
type.

Format and Method Names
.......................

The following format names SHOULD be used for selecting formats for generator
output:

* ``canonicalExtendedJSON`` (references Canonical Extended JSON as described in
  this specification)

* ``relaxedExtendedJSON`` (references Relaxed Extended JSON as described in
  this specification)

* ``legacyExtendedJSON`` (if supported: references Legacy Extended JSON,
  with implementation-defined behavior)

Generators MAY use these format names as part of function/method names or MAY
use them as arguments or constants, as needed.

If a generator provides a generic `to_json` or `to_extended_json` method, it
MUST default to producing Relaxed Extended JSON or MUST be deprecated in
favor of a spec-compliant method.

Restrictions and limitations
----------------------------

Extended JSON is designed primarily for testing and human inspection of BSON
documents.  It is not designed to reliably round-trip BSON documents.  One
fundamental limitation is that JSON objects are inherently unordered and
BSON objects are ordered.

Further, Extended JSON uses ``$``-prefixed keys in type wrappers and has no
provision for escaping a leading ``$`` used elsewhere in a document.  This
means that the Extended JSON representation of a document with ``$``-prefixed
keys could be indistinguishable from another document with a type wrapper with
the same keys.

Extended JSON formats SHOULD NOT be used in contexts where ``$``-prefixed keys
could exist in BSON documents (with the exception of the DBRef convention,
which is accounted for in this spec).

Test Plan
=========

Drivers, tools, and libraries can test their compliance to this specification by
running the tests in version 2.0 and above of the `BSON Corpus Test Suite`_.

.. _BSON Corpus Test Suite: https://github.com/mongodb/specifications/blob/master/source/bson-corpus/bson-corpus.rst

Examples
========

Canonical Extended JSON Example
-------------------------------

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
    "RegularExpression": new BsonRegularExpression("foo*", "xi"),
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
         "$binary": {
             "base64": "o0w498Or7cijeBSpkquNtg==",
             "subType": "03"
         }
     },
     "BinaryUserDefined": {
         "$binary": {
             "base64": "AQIDBAU=",
             "subType": "80"
         }
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
         "$timestamp": { "t": 42, "i": 1 }
     },
     "RegularExpression": {
         "$regularExpression": {
             "pattern": "foo*",
             "options": "ix"
         }
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
     "DBRefNoDB": {
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

Relaxed Extended JSON Example
-----------------------------

In Relaxed Extended JSON, the example document is transformed similarly
to Canonical Extended JSON, with the exception of the following
keys (newlines and spaces added for readability)::

  {
     ...
     "Int32": 42,
     "Int64": 42,
     "Double": 42.42,
     ...
     "DatetimeEpoch": {
         "$date": "1970-01-01T00:00:00.000Z"
     },
     ...
  }

Motivation for Change
=====================

There existed many Extended JSON parser and generator implementations prior to
this specification that used conflicting formats, since there was no agreement
on the precise format of Extended JSON. This resulted in problems where the
output of some generators could not be consumed by some parsers.

MongoDB drivers needed a single, standard Extended JSON format for testing that
covers all BSON types.  However, there were BSON types that had no defined
Extended JSON representation.  This spec primarily addresses that need, but
provides for slightly broader use as well.

Design Rationale
================

Of Relaxed and Canonical Formats
--------------------------------

There are various use cases for expressing BSON documents in a text rather
that binary format.  They broadly fall into two categories:

* Type preserving: for things like testing, where one has to describe the
  expected form of a BSON document, it's helpful to be able to precisely
  specify expected types.  In particular, numeric types need to differentiate
  between Int32, Int64 and Double forms.

* JSON-like: for things like a web API, where one is sending a document (or a
  projection of a document) that only uses ordinary JSON type primitives, it's
  desirable to represent numbers in the native JSON format.  This output is
  also the most human readable and is useful for debugging and documentation.

The two formats in this specification address these two categories of use cases.

Of Parsers and Generators
-------------------------

Parsers need to accept any valid Extended JSON string that a generator can
produce.  Parsers and generators are permitted to accept and output strings in
other formats as well for backwards compatibility.

.. _levels of nesting:

Acceptable nesting depth has implications for resource usage so unlimited
nesting is not permitted.

Generators support at least 100 levels of nesting in a BSON document
being transformed to Extended JSON. This aligns with MongoDB's own limitation of
100 levels of nesting.

Parsers support at least 200 levels of nesting in Extended JSON text,
since the Extended JSON language can double the level of apparent nesting of a
BSON document by wrapping certain types in their own documents.

Of Canonical Type Wrapper Formats
---------------------------------

Prior to this specification, BSON types fell into three categories with respect
to Legacy Extended JSON:

1. A single, portable representation for the type already existed.

2. Multiple representations for the type existed among various Extended JSON
   generators, and those representations were in conflict with each other or
   with current portability goals.

3. No Legacy Extended JSON representation existed.

If a BSON type fell into category (1), this specification just declares that
form to be canonical, since all drivers, tools, and libraries already know how
to parse or output this form.  There are two exceptions:

RegularExpression
.................

The form ``{"$regex: <string>, $options: <string>"}`` has until this
specification been canonical. The change to ``{"$regularExpression":
{pattern: <string>, "options": <string>"}}`` is motivated by a conflict between
the previous canonical form and the ``$regex`` MongoDB query operator. The form
specified here disambiguates between the two, such that a parser can accept any
MongoDB query filter, even one containing the ``$regex`` operator.

Binary
......

The form ``{"$binary": "AQIDBAU=", "$type": "80"}`` has until this specification
been canonical. The change to ``{"$binary": {"base64": "AQIDBAU=", "subType":
"80"}}`` is motivated by a conflict between the previous canonical form and the
``$type`` MongoDB query operator. The form specified here disambiguates between
the two, such that a parser can accept any MongoDB query filter, even one
containing the ``$type`` operator.

Reconciled type wrappers
........................

If a BSON type fell into category (2), this specification selects a new common
representation for the type to be canonical. Conflicting formats were gathered
by surveying a number of Extended JSON generators, including the MongoDB Java
Driver (version 3.3.0), the MongoDB Python Driver (version 3.4.0.dev0), the
MongoDB Extended JSON module on NPM (version 1.7.1), and each minor version of
mongoexport from 2.4.14 through 3.3.12. When possible, we set the "strict"
option on the JSON codec. The following BSON types had conflicting Extended JSON
representations:

Binary
''''''

Some implementations write the Extended JSON form of a Binary object with a
strict two-hexadecimal digit subtype (e.g. they output a leading ``0`` for
subtypes < 16). However, the NPM mongodb-extended-json module and Java driver
use a single hexadecimal digit to represent subtypes less than 16. This
specification makes both one- and two-digit representations acceptable.

Code
''''

Mongoexport 2.4 does not quote the ``Code`` value when writing out the extended
JSON form of a BSON Code object. All other implementations do so. This spec
canonicalises the form where the Javascript code is quoted, since the latter
form adheres to the JSON specification and the former does not. As an
additional note, the NPM mongodb-extended-json module uses the form ``{"code":
"<javascript code>"}, omitting the dollar sign (``$``) from the key. This
specification does not accomodate the eccentricity of a single library.

CodeWithScope
'''''''''''''

In addition to the same variants as BSON Code types, there are other variations
when turning CodeWithScope objects into Extended JSON. Mongoexport 2.4 and 2.6
omit the scope portion of CodeWithScope if it is empty, making the output
indistinguishable from a Code type. All other implementations include the empty
scope. This specification therefore canonicalises the form where the scope is
always included. The presence of ``$scope`` is what differentiates Code from
CodeWithScope.

Datetime
''''''''

Mongoexport 2.4 and the Java driver always transform a Datetime object into an
Extended JSON string of the form ``{"$date": <ms since epoch>}``. This form has
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

In Relaxed Extended JSON format, this specification provides for ISO-8601
representation for better readability, but limits it to a portable subset, from
the epoch to the end of the largest year that can be represented with four
digits.  This should encompass most typical use of dates in applications.

DBPointer
'''''''''

Mongoexport 2.4 and 2.6 use the form ``{"$ref": <namespace>, "$id": <hex
string>}``. All other implementations studied include the canonical ``ObjectId``
form: ``{"$ref": <namespace>, "$id": {"$oid": <hex string>}}``. Neither of these
forms are distinguishable from that of DBRef, so this specification creates a
new format: ``{"$dbPointer": {"$ref": <namespace>, "$id": {"$oid": <hex
string>}}}``.

Newly-added type wrappers
.........................

If a BSON type fell into category (3), above, this specification creates a type
wrapper format for the type. The following new Extended JSON type wrappers are
introduced by this spec:

* ``$dbPointer`` - See above.

* ``$numberInt`` - This is used to preserve the "int32" BSON type in Canonical
  Extended JSON. Without using ``$numberInt``, this type will be
  indistinguishable from a double in certain languages where the distinction
  does not exist, such as Javascript.

* ``$numberDouble`` - This is used to preserve the ``double`` type in Canonical
  Extended JSON, as some JSON generators might omit a trailing ".0" for
  integral types.  It also supports representing non-finite values like NaN or
  Infinity which are prohibited in the JSON specification for numbers.

* ``$symbol`` - The use of the ``$symbol`` key preserves the symbol type in
  Canonical Extended JSON, distinguishing it from JSON strings.

Reference Implementation
========================

[*Canonical Extended JSON format reference implementation needs to be updated*]

PyMongo implements the Canonical Extended JSON format, which must be chosen by
selecting the right option on the ``JSONOptions`` object::

  from bson.json_util import dumps, DatetimeRepresentation, CANONICAL_JSON_OPTIONS

  dumps(document, json_options=CANONICAL_JSON_OPTIONS)

[*Relaxed Extended JSON format reference implementation is TBD*]

Implementation Notes
====================

JSON File Format
----------------

Some applications like mongoexport may wish to write multiple Extended JSON
documents to a single file. One way to do this is to list each JSON document
one-per-line. When doing this, it is important to ensure that special characters
like newlines are encoded properly (e.g. ``\n``).

Duplicate Keys
--------------

The BSON specification does not prohibit duplicate key names within the same
BSON document, but provides no semantics for the interpretation of duplicate
keys. The JSON specification says that names within an object should be unique,
and many JSON libraries are incapable of handling this scenario.

This specification is silent on the matter, so as not to conflict with a future
change by either specification.

Future Work
===========

This specification will need to be amended if future BSON types are added to the
BSON specification.

Q&A
===

**Q**. Why was version 2 of the spec necessary?

**A**. After Version 1 was released, several stakeholders raised concerns that
not providing an option to output BSON numbers as ordinary JSON numbers limited
the utility of Extended JSON for common historical uses.  We decided to provide
a second format option and more clearly distinguish the use cases (and
limitations) inherent in each format.

**Q**. My BSON parser doesn't distinguish every BSON type. Does my Extended
JSON generator need to distinguish these types?

**A**. No. Some BSON parsers do not emit a unique type for each BSON type,
making round-tripping BSON through such libraries impossible without changing
the document. For example, a ``DBPointer`` will be parsed into a ``DBRef`` by
PyMongo. In such cases, a generator must emit the Extended JSON form for
whatever type the BSON parser emitted. It does not need to preserve type
information when that information has been lost by the BSON parser.

**Q**. How can implementations which require backwards compatibility with Legacy
Extended JSON, in which BSON regular expressions were represented with
``$regex``, handle parsing of extended JSON test representing a MongoDB query
filter containing the ``$regex`` operator?

**A**. An implementation can handle this in a number of ways:

- Introduce an enumeration that determines the behavior of the parser. If the
  value is LEGACY, it will parse ``$regex`` and not treat ``$regularExpression``
  specially, and if the value is CANONICAL, it will parse ``$regularExpression``
  and not treat ``$regex`` specially.
- Support both legacy and canonical forms in the parser without requiring the
  application to specify one or the other. Making that work for the ``$regex``
  query operator use case will require that the rules set forth in the 1.0.0
  version of this specification are followed for ``$regex``; specifically, that
  a document with a ``$regex`` key whose value is a JSON object should be
  parsed as a normal document and not reported as an error.

**Q**. How can implementations which require backwards compatibility with Legacy
Extended JSON, in which BSON binary values were represented like ``{"$binary":
"AQIDBAU=", "$type": "80"}``, handle parsing of extended JSON test representing
a MongoDB query filter containing the ``$type`` operator?

**A**. An implementation can handle this in a number of ways:

- Introduce an enumeration that determines the behavior of the parser. If the
  value is LEGACY, it will parse the new binary form and not treat the legacy
  one specially, and if the value is CANONICAL, it will parse the new form and
  not treat the legacy form specially.
- Support both legacy and canonical forms in the parser without requiring the
  application to specify one or the other. Making that work for the ``$type``
  query operator use case will require that the rules set forth in the 1.0.0
  version of this specification are followed for ``$type``; specifically, that
  a document with a ``$type`` key whose value is an integral type, or a
  document with a ``$type`` key but without a ``$binary`` key, should be
  parsed as a normal document and not reported as an error.

**Q**. Sometimes I see the term "extjson" used in other specifications. Is
"extjson" related to this specification?

**A**. Yes, "extjson" is short for "Extended JSON".

Changes
=======

v2.0.0
------

* Added "Relaxed" format.

* Changed BSON timestamp type wrapper back to ``{"t": *int*, "i": *int*}`` for
  backwards compatibility.  (The change in v1 to unsigned 64-bit string was
  premature optimization.)

* Changed BSON regular expression type wrapper to
  ``{"$regularExpression": {pattern: *string*, "options": *string*"}}``.

* Changed BSON binary type wrapper to
  ``{"$binary": {"base64": <base64-encoded payload as a *string*>,
  "subType": <BSON binary type as a one- or two-character *hex string*>}}``

* Added "Restrictions and limitations" section.

* Clarified parser and generator rules.
