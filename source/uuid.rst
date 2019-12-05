=============================
Handling of Native UUID Types
=============================

:Spec Title: Handling of Native UUID Types
:Spec Version: 1.0
:Author: Jeff Yemin
:Lead: Bernie Hackett
:Advisory Group: Shane Harvey, Oleg Pudeyev, Robert Stam
:Informed: drivers@
:Status: Accepted
:Type: Standards
:Last Modified: 2019-11-19

.. contents::

--------

Abstract
========

The Java, C#, and Python drivers natively support platform types for UUID, all of which by default encode them to and decode them from BSON binary subtype 3.  However, each encode the bytes in a different order from the others. To improve interoperability, BSON binary subtype 4 was introduced and defined the byte order according to `RFC 4122 <https://tools.ietf.org/html/rfc4122#section-4.1.2>`_, and a mechanism to configure each driver to encode UUIDs this way was added to each driver. The legacy representation remained as the default for each driver.
 
This specification moves MongoDB drivers further towards the standard UUID representation by requiring an application relying on native UUID support to explicitly specify the representation it requires.

Drivers that support native UUID types will additionally create helpers on their BsonBinary class that will aid in conversion to and from the platform native UUID type.

META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in
`RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

Terms
-----

UUID
    A Universally Unique IDentifier

BsonBinary
   An object that wraps an instance of a BSON binary value 

Naming Deviations
-----------------

All drivers MUST name operations, objects, and parameters as defined in the following sections.

The following deviations are permitted:

* Drivers can use the platform's name for a UUID.  For instance, in C# the platform class is Guid, whereas in Java it is UUID.
* Drivers can use a "to" prefix instead of an "as" prefix for the BsonBinary method names.

Explicit encoding and decoding
------------------------------

Any driver with a native UUID type MUST add the following UuidRepresentation enumeration, and associated methods to its BsonBinary (or equivalent) class:

.. code:: typescript
   
   /**
           
   enum UuidRepresentation {

      /**
       * An unspecified representation of UUID.  Essentially, this is the null 
       * representation value. This value is not required for languages that      
       * have better ways of indicating, or preventing use of, a null value.
       */
      UNSPECIFIED("unspecified"),

      /**
       * The canonical representation of UUID according to RFC 4122, 
       * section 4.1.2 
       * 
       * It encodes as BSON binary subtype 4
      */
      STANDARD("standard"),

      /**
       * The legacy representation of UUID used by the C# driver.
       *
       * In this representation the order of bytes 0-3 are reversed, the 
       * order of bytes 4-5 are reversed, and the order of bytes 6-7 are 
       * reversed.
       *
       * It encodes as BSON binary subtype 3
       */
      C_SHARP_LEGACY("csharpLegacy"),
      
      /**
       * The legacy representation of UUID used by the Java driver.
       *
       * In this representation the order of bytes 0-7 are reversed, and the 
       * order of bytes 8-15 are reversed.
       *
       * It encodes as BSON binary subtype 3
       */
      JAVA_LEGACY("javaLegacy"),

     /**
      * The legacy representation of UUID used by the Python driver.
      *
      * As with STANDARD, this representation conforms with RFC 4122, section
      * 4.1.2 
      *
      * It encodes as BSON binary subtype 3
      */
      PYTHON_LEGACY("pythonLegacy")
   }

   class BsonBinary {
      /* 
       * Construct from a UUID using the standard UUID representation
       * [Specification] This constructor SHOULD be included but MAY be 
       *                 omitted if it creates backwards compatibility issues
       */
      constructor(Uuid uuid) 

      /*
       * Construct from a UUID using the given UUID representation.
       *
       * The representation must not be equal to UNSPECIFIED
       */
      constructor(Uuid uuid, UuidRepresentation representation)
    
      /*
       * Decode a subtype 4 binary to a UUID, erroring when the subtype is not 4.
       */
      Uuid asUuid()  
   
      /*
       * Decode a subtype 3 or 4 to a UUID, according to the UUID    
       * representation, erroring when subtype does not match the
       * representation.
       */
      Uuid asUuid(UuidRepresentation representation)
   }

Implicit decoding and encoding
------------------------------

A new driver for a language with a native UUID type MUST NOT implicitly encode from or decode to the native UUID type.  Rather, explicit conversion MUST be used as described in the previous section.

Drivers that already do such implicit encoding and decoding SHOULD support a URI option, uuidRepresentation, which controls the default behavior of the UUID codec. Alternatively, a driver MAY specify the UUID representation via global state. 



.. list-table::
   :header-rows: 1
   :widths: 1 1 3 1 1

   * - Value
     - Default?
     - Encode to
     - Decode subtype 4 to
     - Decode subtype 3 to
     
   * - unspecified
     - yes
     - raise error 
     - BsonBinary
     - BsonBinary

   * - standard
     - no
     - BSON binary subtype 4 
     - native UUID
     - BsonBinary

   * - csharpLegacy
     - no
     - BSON binary subtype 3 with C# legacy byte order 
     - BsonBinary
     - native UUID

   * - javaLegacy
     - no
     - BSON binary subtype 3 with Java legacy byte order 
     - BsonBinary
     - native UUID

   * - pythonLegacy
     - no
     - BSON binary subtype 3 with standard byte order 
     - BsonBinary
     - native UUID

For scenarios where the application makes the choice (e.g. a POJO with a field of type UUID), or when serializers are strongly typed and are constrained to always return values of a certain type, the driver will raise an exception in cases where otherwise it would be required to decode to a different type (e.g. BsonBinary instead of UUID or vice versa).

Note also that none of the above applies when decoding to strictly typed maps, e.g. a Map<String, BsonValue> like Java or .NET's BsonDocument class.  In those cases the driver is always decoding to BsonBinary, and applications would use the asUuid methods to explicitly convert from BsonBinary to UUID.


Implementation Notes
--------------------

Since changing the default UUID representation can reasonably be considered a backwards-breaking change, drivers that implement the full specification should stage implementation according to semantic versioning guidelines.  Specifically, support for this specification can be added to a minor release, but with several exceptions: 

The default UUID representation should be left as is (e.g. JAVA_LEGACY for the Java driver) rather than be changed to UNSPECIFIED.  In a subsequent major release, the default UUID representation can be changed to UNSPECIFIED (along with appropriate documentation indicating the backwards-breaking change).
Subtype 4 BSON Binary values should continue to be decoded to native UUID values regardless of UUID representation


Test Plan
=========

The test plan consists of a series of prose tests.  They all operate on the same UUID, with the String representation of "00112233-4455-6677-8899-aabbccddeeff".

Explicit encoding
-----------------

1. Create a BsonBinary instance with the given UUID
   
   a. Assert that the BsonBinary instance's subtype is equal to 4 and data equal to the hex-encoded string "00112233445566778899AABBCCDDEEFF"

2. Create a BsonBinary instance with the given UUID and UuidRepresentation equal to STANDARD

   a. Assert that the BsonBinary instance's subtype is equal to 4 and data equal to the hex-encoded string "00112233445566778899AABBCCDDEEFF"

3. Create a BsonBinary instance with the given UUID and UuidRepresentation equal to JAVA_LEGACY

   a. Assert that the BsonBinary instance's subtype is equal to 3 and data equal to the hex-encoded string "7766554433221100FFEEDDCCBBAA9988"

4. Create a BsonBinary instance with the given UUID and UuidRepresentation equal to CSHARP_LEGACY
   
   a. Assert that the BsonBinary instance's subtype is equal to 3 and data equal to the hex-encoded string "33221100554477668899AABBCCDDEEFF"

5. Create a BsonBinary instance with the given UUID and UuidRepresentation equal to PYTHON_LEGACY

   a. Assert that the BsonBinary instance's subtype is equal to 3 and data equal to the hex-encoded string "00112233445566778899AABBCCDDEEFF"

6. Create a BsonBinary instance with the given UUID and UuidRepresentation equal to UNSPECIFIED

   a. Assert that an error is raised

Explicit Decoding
-----------------

1. Create a BsonBinary instance with subtype equal to 4 and data equal to the hex-encoded string "00112233445566778899AABBCCDDEEFF"

   a. Assert that a call to BsonBinary.asUuid() returns the given UUID
   b. Assert that a call to BsonBinary.asUuid(STANDARD) returns the given UUID
   c. Assert that a call to BsonBinary.asUuid(UNSPECIFIED) raises an error
   d. Assert that a call to BsonBinary.asUuid(JAVA_LEGACY) raises an error
   e. Assert that a call to BsonBinary.asUuid(CSHARP_LEGACY) raises an error
   f. Assert that a call to BsonBinary.asUuid(PYTHON_LEGACY) raises an error

2. Create a BsonBinary instance with subtype equal to 3 and data equal to the hex-encoded string "7766554433221100FFEEDDCCBBAA9988"
   
   a. Assert that a call to BsonBinary.asUuid() raises an error
   b. Assert that a call to BsonBinary.asUuid(STANDARD) raised an error
   c. Assert that a call to BsonBinary.asUuid(UNSPECIFIED) raises an error
   d. Assert that a call to BsonBinary.asUuid(JAVA_LEGACY) returns the given UUID

3. Create a BsonBinary instance with subtype equal to 3 and data equal to the hex-encoded string "33221100554477668899AABBCCDDEEFF"

   a. Assert that a call to BsonBinary.asUuid() raises an error
   b. Assert that a call to BsonBinary.asUuid(STANDARD) raised an error
   c. Assert that a call to BsonBinary.asUuid(UNSPECIFIED) raises an error
   d. Assert that a call to BsonBinary.asUuid(CSHARP_LEGACY) returns the given UUID

4. Create a BsonBinary instance with subtype equal to 3 and data equal to the hex-encoded string "00112233445566778899AABBCCDDEEFF"

   a. Assert that a call to BsonBinary.asUuid() raises an error
   b. Assert that a call to BsonBinary.asUuid(STANDARD) raised an error
   c. Assert that a call to BsonBinary.asUuid(UNSPECIFIED) raises an error
   d. Assert that a call to BsonBinary.asUuid(PYTHON_LEGACY) returns the given UUID

Implicit encoding
-----------------

1. Set the uuidRepresentation of the client to "javaLegacy". Insert a document with an "_id" key set to the given native UUID value.

   a. Assert that the actual value inserted is a BSON binary with subtype 3 and data equal to the hex-encoded string "7766554433221100FFEEDDCCBBAA9988"

2. Set the uuidRepresentation of the client to "charpLegacy". Insert a document with an "_id" key set to the given native UUID value.

   a. Assert that the actual value inserted is a BSON binary with subtype 3 and data equal to the hex-encoded string "33221100554477668899AABBCCDDEEFF"

3. Set the uuidRepresentation of the client to "pythonLegacy". Insert a document with an "_id" key set to the given native UUID value.

   a. Assert that the actual value inserted is a BSON binary with subtype 3 and data equal to the hex-encoded string "00112233445566778899AABBCCDDEEFF"

4. Set the uuidRepresentation of the client to "standard". Insert a document with an "_id" key set to the given native UUID value.

   a. Assert that the actual value inserted is a BSON binary with subtype 4 and data equal to the hex-encoded string "00112233445566778899AABBCCDDEEFF"

5. Set the uuidRepresentation of the client to "unspecified". Insert a document with an "_id" key set to the given native UUID value.

   a. Assert that a BSON serialization exception is thrown

Implicit Decoding
-----------------

1. Set the uuidRepresentation of the client to "javaLegacy". Insert a document containing two fields. The "standard" field should contain a BSON Binary created by creating a BsonBinary instance with the given UUID and the STANDARD UuidRepresentation.  The "legacy" field should contain a BSON Binary created by creating a BsonBinary instance with the given UUID and the JAVA_LEGACY UuidRepresentation. Find the document.

   a. Assert that the value of the "standard" field is of type BsonBinary and is equal to the inserted value.
   b. Assert that the value of the "legacy" field is of the native UUID type and is equal to the given UUID

   Repeat this test with the uuidRepresentation of the client set to "csharpLegacy" and "pythonLegacy".

2. Set the uuidRepresentation of the client to "standard". Insert a document containing two fields. The "standard" field should contain a BSON Binary created by creating a BsonBinary instance with the given UUID and the STANDARD UuidRepresentation.  The "legacy" field should contain a BSON Binary created by creating a BsonBinary instance with the given UUID and the PYTHON_LEGACY UuidRepresentation. Find the document.
  
   a. Assert that the value of the "standard" field is of the native UUID type and is equal to the given UUID
   b. Assert that the value of the "legacy" field is of type BsonBinary and is equal to the inserted value.

3. Set the uuidRepresentation of the client to "unspecified". Insert a document containing two fields. The "standard" field should contain a BSON Binary created by creating a BsonBinary instance with the given UUID and the STANDARD UuidRepresentation.  The "legacy" field should contain a BSON Binary created by creating a BsonBinary instance with the given UUID and the PYTHON_LEGACY UuidRepresentation. Find the document.

   a. Assert that the value of the "standard" field is of type BsonBinary and is equal to the inserted value
   b. Assert that the value of the "legacy" field is of type BsonBinary and is equal to the inserted value.

   Repeat this test with the uuidRepresentation of the client set to "csharpLegacy" and "pythonLegacy".

Note: the assertions will be different in the release prior to the major release, to avoid breaking changes.  Adjust accordingly!

Q & A
=====

What's the rationale for the deviations allowed by the specification?
---------------------------------------------------------------------

In short, the C# driver has existing behavior that make it infeasible to work the same as other drivers.

The C# driver has a global serialization registry. Since it's global and not per-MongoClient, it's not feasible to override the UUID representation on a per-MongoClient basis, since doing so would require a per-MongoClient registry.  Instead, the specification allows for a global override so that the C# driver can implement the specification.

Additionally, the C# driver has an existing configuration parameter that controls the behavior of BSON readers and writers at a level below the serializers. This configuration affects the semantics of the existing BsonBinary class in a way that doesn't allow for the constructor(UUID) mentioned in the specification.  For this reason, that constructor is specified as optional.
