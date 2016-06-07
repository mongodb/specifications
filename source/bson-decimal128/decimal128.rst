========================================
BSON Decimal128 Type Handling in Drivers
========================================

:Spec Title: BSON Decimal128 Type Handling In Drivers
:Spec Version: 1.0
:Author: Hannes Magnusson
:Advisory Group: Emily Stolfo and Craig Wilson
:Kernel Advisory: Geert Bosch
:Original Work: David Hatch and Raymond Jacobson
:Status: Approved
:Type: Standards
:Minimum Server Version: 3.4
:Last Modified: 2016-06-06


.. contents::

--------


Abstract
========

MongoDB 3.4 introduces a new BSON type representing high precision decimal
(``"\x13"``), known as Decimal128. 3.4 compatible drivers must support this
type by creating a Value Object for it, possibly with accessor functions for
retrieving its value in data types supported by the respective languages.


Round-tripping Decimal128 types between driver and server MUST not change its
value or representation in any way. Conversion to and from native language
types is complicated and there are many pitfalls to represent Decimal128
precisely in all languages


While many languages offer a native decimal type, the precision of these types
often does not exactly match that of the MongoDB implementation. To ensure
error-free conversion and consistency between official MongoDB drivers, this
specification does not allow automatically converting the ``BSON Decimal128`` type
into a language-defined decimal type.


Language drivers will wrap their native type in value objects by default and
SHOULD offer accessor functions for retrieving its value represented by
language-defined types if appropriate.  A driver that offers the ability to
configure mappings to/from BSON types to native types MAY allow the option to
automatically convert the ``BSON Decimal128`` type to a native type. It should
however be made abundantly clear to the user that converting to native data
types risks incurring data loss.


META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.


Terminology
===========

IEEE 754-2008 128-bit decimal floating point (Decimal128): 
   The Decimal128 specification supports 34 decimal digits of precision, a max
   value of approximately ``10^6145``, and min value of approximately
   ``-10^6145``. This is the new ``BSON Decimal128`` type (``"\x13"``).


Clamping:
   Clamping happens when a value’s exponent is too large for the destination
   format. This works by adding zeros to the coefficient to reduce the exponent to
   the largest usable value.  An overflow occurs if the number of digits required
   is more than allowed in the destination format.


Binary Integer Decimal (BID):
   MongoDB uses this binary encoding for the coefficient as specified in ``IEEE
   754-2008``. The byte order is little-endian, like the rest of the BSON types.


Value Object:
   An immutable container type representing a value (e.g. Decimal128). This Value
   Object MAY provide accessors that retrieve the abstracted value as a different
   type (e.g. casting it).  ``double x = valueObject.getAsDouble();``


Specification
=============


--------------------------------------
BSON Decimal128 implementation details
--------------------------------------

The ``BSON Decimal128`` data type implements the `Decimal Arithmetic Encodings
<http://speleotrove.com/decimal/decbits.html>`_ specification, with certain
exceptions around value integrity.  When a value cannot be represented exactly,
the value will be rejected.


The specification defines several statuses which are meant to signal
exceptional `circumstances <http://speleotrove.com/decimal/daexcep.html>`_,
such as when overflowing occurs, and how to handle them.


``BSON Decimal128`` Value Objects MUST implement these actions for these exceptions:

* Overflow
   * When overflow occurs, the operation MUST emit an error and result in a failure
* Underflow
   * When underflow occurs, the operation MUST emit an error and result in a failure
* Clamping
   * Since clamping does not change the actual value, only the representation
     of it, clamping MUST occur without emitting an error.
* Rounding
   * When the coefficient requires more digits then Decimal128 provides,
     rounding MUST be done without emitting an error, unless it would result in
     inexact rounding, in which case the operation MUST emit an error and
     result in a failure.
* Conversion Syntax
   * Invalid strings MUST emit an error and result in a failure.


It should be noted that the given exponent is a preferred representation. If
the value cannot be stored due to the value of the exponent being too large or
too small, but can be stored using an alternative representation by clamping
and or rounding, a ``BSON Decimal128`` compatible Value Object MUST do so, unless
such operation results in an inexact rounding or other underflow or overflow.


-----------------
Reading from BSON
-----------------

A BSON type ``"\x13"`` MUST be represented by an immutable Value Object by
default and MUST NOT be automatically converted into language native numeric
type by default. A driver that offers users a way to configure the exact type
mapping to and from BSON types MAY allow the ``BSON Decimal128`` type to be
converted to the user configured type.


A driver SHOULD provide accessors for this immutable Value Object, which can
return a language-specific representation of the Decimal128 value, after
converting it into the respective type. For example, Java may choose to provide
``Decimal128.getBigDecimal()``.


All drivers MUST provide an accessor for retrieving the value as a string.
Drivers MAY provide other accessors, retrieving the value as other types.


----------------------------
Serializing and writing BSON
----------------------------

Drivers MUST provide a way of constructing the Value Object, as the driver
representation of the ``BSON Decimal128`` is an immutable Value Object by default.


A driver MUST have a way to construct this Value Object from a string.  For
example, Java MUST provide a method similar to ``Decimal128.valueOf("2.000")``.


A driver that has accessors for different types SHOULD provide a way to
construct the Value Object from those types.


--------------------------
Reading from Extended JSON
--------------------------

The Extended JSON representation of Decimal128 is a document with the key
``$numberDecimal`` and a value of the Decimal128 as a string. Drivers that support
Extended JSON formatting MUST support the ``$numberDecimal`` type specifier.


When an Extended JSON ``$numberDecimal`` is parsed, its type should be the same as
that of a deserialized ``BSON Decimal128``, as described in `Reading from BSON`_.


The Extended JSON ``$numberDecimal`` value follows the same stringification rules
as defined in `From String Representation`_.


------------------------
Writing to Extended JSON
------------------------

The Extended JSON type identifier is ``$numberDecimal``, while the value itself is
a string.  Drivers that support converting values to Extended JSON MUST be able
to convert its Decimal128 value object to Extended JSON.


Converting a Decimal128 Value Object to Extended JSON MUST follow the
conversion rules in `To String Representation`_, and other stringification rules
as when converting Decimal128 Value Object to a String.


---------------------------------------------------------
Operator overloading and math on Decimal128 Value Objects
---------------------------------------------------------

Drivers MUST NOT allow any mathematical operator overloading for the Decimal128
Value Objects. This includes adding two Decimal128 Value Objects and assigning
the result to a new object.


If a user wants to perform mathematical operations on Decimal128 Value Objects,
the user must explicitly retrieve the native language value representations of
the objects and perform the operations on those native representations. The
user will then create a new Decimal128 Value Object and optionally overwrite
the original Decimal128 Value Object.


--------------------------
From String Representation
--------------------------

For finite numbers, we will use the definition at
http://speleotrove.com/decimal/daconvs.html. It has been modified to account
for a different NaN representation and whitespace rules and copied here::


    Strings which are acceptable for conversion to the abstract representation of
    numbers, or which might result from conversion from the abstract representation
    to a string, are called numeric strings.
    
    
    A numeric string is a character string that describes either a finite
    number or a special value.
    * If it describes a finite number, it includes one or more decimal digits,
      with an optional decimal point. The decimal point may be embedded in the
      digits, or may be prefixed or suffixed to them. The group of digits (and
      optional point) thus constructed may have an optional sign (‘+’ or ‘-’)
      which must come before any digits or decimal point. 
    * The string thus described may optionally be followed by an ‘E’
      (indicating an exponential part), an optional sign, and an integer
      following the sign that represents a power of ten that is to be applied.
      The ‘E’ may be in uppercase or lowercase.
    * If it describes a special value, it is one of the case-independent names
      ‘Infinity’, ‘Inf’, or ‘NaN’ (where the first two represent infinity and
      the second represent NaN). The name may be preceded by an optional sign,
      as for finite numbers. 
    * No blanks or other whitespace characters are permitted in a numeric string.
    
    Formally
    
              sign           ::=  ’+’ | ’-’
              digit          ::=  ’0’ | ’1’ | ’2’ | ’3’ | ’4’ | ’5’ | ’6’ | ’7’ |
                                  ’8’ | ’9’
              indicator      ::=  ’e’ | ’E’
              digits         ::=  digit [digit]...
              decimal-part   ::=  digits ’.’ [digits] | [’.’] digits
              exponent-part  ::=  indicator [sign] digits
              infinity       ::=  ’Infinity’ | ’Inf’
              nan            ::=  ’NaN’
              numeric-value  ::=  decimal-part [exponent-part] | infinity
              numeric-string ::=  [sign] numeric-value | [sign] nan
    
    where the characters in the strings accepted for ‘infinity’ and ‘nan’ may be in
    any case.  If an implementation supports the concept of diagnostic information
    on NaNs, the numeric strings for NaNs MAY include one or more digits, as shown
    above.[3]  These digits encode the diagnostic information in an
    implementation-defined manner; however, conversions to and from string for
    diagnostic NaNs should be reversible if possible. If an implementation does not
    support diagnostic information on NaNs, these digits should be ignored where
    necessary. A plain ‘NaN’ is usually the same as ‘NaN0’.
    

    Drivers MAY choose to support signed NaN (sNaN), along with sNaN with
    diagnostic information. 
    
    
    
    Examples::
    Some numeric strings are:
                "0"         -- zero
               "12"         -- a whole number
              "-76"         -- a signed whole number
               "12.70"      -- some decimal places
               "+0.003"     -- a plus sign is allowed, too
              "017."        -- the same as 17
                 ".5"       -- the same as 0.5
               "4E+9"       -- exponential notation
                "0.73e-7"   -- exponential notation, negative power
               "Inf"        -- the same as Infinity
               "-infinity"  -- the same as -Infinity
               "NaN"        -- not-a-Number
    
    Notes:
    1. A single period alone or with a sign is not a valid numeric string.
    2. A sign alone is not a valid numeric string.
    3. Significant (after the decimal point) and insignificant leading zeros
           are permitted.


------------------------
To String Representation
------------------------

For finite numbers, we will use the definition at
http://speleotrove.com/decimal/daconvs.html. It has been copied here::


    The coefficient is first converted to a string in base ten using the characters
    0 through 9 with no leading zeros (except if its value is zero, in which case a
    single 0 character is used).
    
    
    Next, the adjusted exponent is calculated; this is the exponent, plus the
    number of characters in the converted coefficient, less one. That is,
    exponent+(clength-1), where clength is the length of the coefficient in decimal
    digits.
    
    
    If the exponent is less than or equal to zero and the adjusted exponent is
    greater than or equal to -6, the number will be converted to a character form
    without using exponential notation. In this case, if the exponent is zero then
    no decimal point is added. Otherwise (the exponent will be negative), a decimal
    point will be inserted with the absolute value of the exponent specifying the
    number of characters to the right of the decimal point. ‘0’ characters are
    added to the left of the converted coefficient as necessary. If no character
    precedes the decimal point after this insertion then a conventional ‘0’
    character is prefixed.
    
    
    Otherwise (that is, if the exponent is positive, or the adjusted exponent is
    less than -6), the number will be converted to a character form using
    exponential notation. In this case, if the converted coefficient has more than
    one digit a decimal point is inserted after the first digit. An exponent in
    character form is then suffixed to the converted coefficient (perhaps with
    inserted decimal point); this comprises the letter ‘E’ followed immediately by
    the adjusted exponent converted to a character form. The latter is in base ten,
    using the characters 0 through 9 with no leading zeros, always prefixed by a
    sign character (‘-’ if the calculated exponent is negative, ‘+’ otherwise).
    

This corresponds to the following code snippet:


  .. code:: c

    var adjusted_exponent = _exponent + (clength - 1);
    if (_exponent > 0 || adjusted_exponent < -6) {
        // exponential notation
    } else {
        // character form without using exponential notation
    }


For special numbers such as infinity or the not a number (NaN) variants, the
below table is used:


==============================  ============
     Value                         String
==============================  ============
Positive Infinite                 Infinity
Negative Infinite                 -Infinity
Positive NaN                      NaN
Negative NaN                      NaN
Signaled NaN                      NaN
Negative Signaled NaN             NaN
NaN with a payload                NaN
Signaled NaN with a payload       NaN
==============================  ============



Finally, there are certain other invalid representations that must be treated
as zeros, as per ``IEEE 754-2008``. The tests will verify that each special value
has been accounted for.


The server log files as well as the Extended JSON Format for Decimal128 use
this format.


Motivation for Change
=====================

BSON already contains support for ``double`` (``"\x01"``), but this type is
insufficient for certain values that require strict precision and
representation, such as money, where it is necessary to perform exact decimal
rounding.


The new BSON type is the 128-bit ``IEEE 754-2008`` decimal floating point number,
which is specifically designed to cope with these issues.


Design Rationale
================

For simplicity and consistency between drivers, drivers must not automatically
convert this type into a native type by default. This also ensures original
data preservation, which is crucial to Decimal128. It is however recommended
that drivers offer a way to convert the Value Object to a native type through
accessors, and to create a new BSON type from native types.  This forces the
user to explicitly do the conversion and thus understand the difference between
the MongoDB type and possible language precision and representation.
Representations via conversions done outside MongoDB are not guaranteed to be
identical.


Backwards Compatibility
=======================

There should be no backwards compatibility concerns. This specification merely
deals with how to encode and decode BSON/Extended JSON Decimal128.


Reference Implementations
=========================

* `Libbson <https://github.com/mongodb/libbson/blob/master/src/bson/bson-decimal128.c>`_
* `Ruby <https://github.com/estolfo/bson-ruby/blob/RUBY-1098-decimal128/lib/bson/decimal128.rb>`_
* `.NET <https://github.com/craiggwilson/mongo-csharp-driver/tree/decimal>`_
* `PyMongo <https://github.com/mongodb/mongo-python-driver/tree/decimal>`_
* `Node <https://github.com/mongodb/js-bson/blob/0.5/lib/bson/decimal128.js>`_
* `Java <https://github.com/mongodb/mongo-java-driver/tree/decimal>`_


Tests
=====

See the `README <tests/README.md>`_ for tests.


Q&A
===

* Is it true Decimal128 doesn’t normalize the value?
   * Yes. As a result of non-normalization rules of the Decimal128 data type,
     precision is represented exactly. For example, ‘2.00’ always remains
     stored as 200E-2 in Decimal128, and it differs from the representation of
     ‘2.0’ (20E-1). These two values compare equally, but represent different
     ideas. 
* How does Decimal128 "2.000" look in the shell?
   * NumberDecimal("2.000")
* Should a driver avoid sending Decimal128 values to pre-3.4 servers?
   * No
* Is there a wire version bump or something for Decimal128?
   * No
