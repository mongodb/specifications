# BSON Binary Subtype 9 - Vector

- Status: Accepted
- Minimum Server Version: N/A

______________________________________________________________________

## Abstract

This document describes a new *Vector* subtype (9) for BSON Binary items, used to compactly represent ordered
collections of uniformly-typed elements. A framework is presented for future type extensibility, but adoption complexity
is limited by allowing support for only a restricted set of element types at first:

- 1-bit unsigned integers
- 8-bit signed integers
- 32-bit floating point

## Meta

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

Hexadecimal values are shown here with a `0x` prefix.

Bit strings are grouped with insignificant whitespace for readability.

## Terms

*BSON Array* - Arrays are a fundamental container type in BSON for ordered sequences, implemented as item type `4`. Each
element can have an arbitrary data type. The encoding is relatively high-overhead, due to both the non-uniform types and
the required element name strings.

*BSON Binary* - BSON Binary items (type `5`) are a container for a variable-length byte sequence with extensible
interpretation, according to an 8-bit *subtype*.

*BSON Binary Vector* - A BSON Binary item of subtype `9`. Also referred to here as a Vector.

## Motivation for Change

BSON does not on its own provide a densely packed encoding for numeric data of uniform data type. Numbers stored in a
BSON Array have high space overhead, owing to the item name and type included with each value. This specification offers
an alternative collection type with improved performance and limited complexity.

### Goals

- Vectors provide improved resource efficiency compared to BSON Arrays.
- Every Vector is guaranteed to represent a sequence of elements with uniform type and size.
- Vectors may be reliably compared for equality by comparing their encoded BSON Binary representation.
- Implementation complexity should be minimal.

### Non-Goals

- No changes to Extended JSON representation are defined. Vectors will serialize to generic Binary items with base64
    encoding: `{"$binary": {"base64": ... , "subType": "9" }}`.
- The Vector is a 1-dimensional container. Applications may implement multi-dimensional arrays efficiently by bundling a
    Vector with additional metadata, but this usage is not standardized here.
- Comprehensive support for all possible data types and bit/byte ordering is not a goal. This specification prefers to
    reduce complexity by limiting the set of allowed types and providing no unnecessary data formatting options.
- Vectors within a BSON document are NOT designed for "zero copy" access by direct architecture-specific load or store.
    Typically multi-byte values will not be aligned as required, and they may need byte order conversion. Internal
    padding for alignment is not supported, as this would impact comparison stability.
- Vectors do not include any data compression features. Applications may see benefit from careful choice of an external
    compression algorithm.
- Vectors do not provide any new comparison methods. Identical Vector values must compare as identical encoded BSON
    Binary byte strings. Vectors are never equal to Arrays, even when they represent the same numeric elements.
- Vectors do not guarantee that element types defined in the future will always be scalar numbers, only that Vector
    elements always have identical type and size.

## Specification

### Scope

- This specification defines the meaning of the data bytes in BSON Binary items of subtype `9`.
- The first two data bytes form a header, with meaning defined here.
- This specification defines validity criteria for accepting or rejecting byte strings.
- Drivers may optionally implement conversions between BSON Array and Vector types. This specification defines rules
    that must be followed when conversions are implemented.
- This specification includes JSON tests with valid documents, invalid documents, and expected conversion results.
- Drivers SHOULD provide low-overhead APIs for producing and consuming Vector data in the closest compatible language
    types, without conversions more expensive than copying or byte-swapping. These APIs are not standardized across
    languages.
- Drivers MAY provide facilities for converting between BSON Binary Vector and BSON Array representations. When they
    choose to do so, they MUST ensure compliance using the provided tests. Drivers MUST NOT automatically convert
    between representations.

### Header Format

Every valid Vector begins with one of the following 2-byte header patterns:

| Header bytes | Alias       | Description                                                                     |
| ------------ | ----------- | ------------------------------------------------------------------------------- |
| `0x03 0x00`  | INT8        | signed bytes                                                                    |
| `0x27 0x00`  | FLOAT32     | single precision (32-bit) floating point, least significant byte first          |
| `0x10 0x00`  | PACKED_BITS | single-bit integers, most significant bit first, exact multiple of 8 bits total |
| `0x10 0x01`  | PACKED_BITS | as above, final 1 bit ignored                                                   |
| `0x10` ...   | PACKED_BITS | ...                                                                             |
| `0x10 0x07`  | PACKED_BITS | as above, final 7 bits ignored                                                  |

Drivers MAY choose to interpret the header bytes as a structure with internal fields:

| Size   | Location                            | Description |
| ------ | ----------------------------------- | ----------- |
| 4 bits | First byte, most significant half   | Type code   |
| 4 bits | First byte, least significant half  | Size code   |
| 5 bits | Second byte, most significant part  | (reserved)  |
| 3 bits | Second byte, least significant part | Padding     |

The generic interpretation of Padding refers to the number of items that should be ignored from what would have been the
end of the Vector, regardless of item size and bit order.

| Type code | Description                                     |
| --------- | ----------------------------------------------- |
| 0         | Signed integer, two's complement representation |
| 1         | Unsigned integer                                |
| 2         | Floating point, IEEE 754 representation         |
| 3 .. 15   | (reserved)                                      |

| Size code | Bits per element   |
| --------- | ------------------ |
| 0         | 1                  |
| 1         | (reserved for 2)   |
| 2         | (reserved for 4)   |
| 3         | 8                  |
| 4         | (reserved for 12)  |
| 5         | (reserved for 16)  |
| 6         | (reserved for 24)  |
| 7         | 32                 |
| 8         | (reserved for 48)  |
| 9         | (reserved for 64)  |
| 10        | (reserved for 96)  |
| 11        | (reserved for 128) |
| 12        | (reserved for 192) |
| 13        | (reserved for 256) |
| 14        | (reserved for 384) |
| 15        | (reserved for 512) |

### Validity Criteria

To be valid, a Vector MUST be 2 bytes long or longer. Its header MUST be one of the valid bit patterns above. In
particular, the second byte MUST be nonzero only as necessary to represent Padding values between 0 and 7 for
PACKED_BITS vectors. Vectors with no elements MUST have a Padding value of 0.

When Padding is nonzero, drivers SHOULD ensure the unused bits in the final byte are zero.

The contents of individual elements MUST NOT be considered when checking the validity of a Vector. Unused bits in the
final byte are not considered part of any element.

Vectors MUST NOT include any unnecessary trailing bytes. For example, FLOAT32 Vectors must include an exact multiple of
4 bytes after the 2-byte header.

Drivers MUST validate Vector metadata when provided through the API. For example, if a PACKED_BIT Vector is constructed
from a byte array paired with a Padding value:

- The driver MUST ensure Padding is zero if the byte array is empty
- The driver SHOULD ensure the unused bits in the final byte are zero
- If the API allows Padding values outside the valid range of 0..7 inclusve, these must be rejected at runtime.

Drivers MUST validate Vector metadata when creating an API representation from a stored BSON Binary item. A PACKED_BIT
value would have its Padding and length validated as above. A FLOAT32 Vector would be rejected for a nonzero second
header byte, or a length that isn't 2 plus a multiple of 4.

### Type Conversions

Type conversion is an optional feature.

Drivers may provide conversions between BSON Array and BSON Binary Vector representations. Drivers MUST only perform
this conversion as requested, not automatically.

#### Packing

PACKED_BITS values MAY be optionally losslessly unpacked to a wider data type of the driver's choosing, for more
convenient access. Drivers MUST provide a way to access PACKED_BITS without unpacking. In languages with compile-time
abstraction, drivers SHOULD provide an abstract data type for manipulating elements in PACKED_BITS without unpacking. If
abstraction is not practical, drivers can instead provide direct access to the byte array and 'Padding' value.

#### Integer Values

INT8 and PACKED_BITS values may be losslessly represented as BSON int32 elements.

When converting BSON int32 or int64 elements to INT8 or PACKED_BITS, out-of-range values MUST cause conversion to fail.

There is no defined conversion from floating point to integer. Conversion from BSON double to an integer Vector MUST
fail.

#### Floating Point Values

There is no defined conversion from integer to floating point. Conversion from BSON int32 or int64 to a FLOAT32 Vector
MUST fail.

When converting BSON double elements to FLOAT32, the driver MUST round to the nearest representable values.

### Data Formats

#### INT8 (`0x03 0x00`)

Signed 1-byte integers in two's complement encoding, representing values from -128 to 127 inclusive.

#### FLOAT32 (`0x27 0x00`)

Single-precision floating point values in the IEEE 754 `binary32` format. 4 bytes, least significant byte first.

#### PACKED_BITS (`0x10 0x00` .. `0x10 0x07`)

Integers 0 and 1 represented by individual bits packed into bytes, most significant bit first.

Padding indicates how many of the least significant bits from the last byte do not encode any element. Drivers MUST
always set these non-encoding bits in the last byte to zero. Drivers SHOULD ensure these bits are zero when checking a
Vector for validity. Vectors with no data bytes MUST have a Padding of zero.

Note that the bit order and byte order in this specification are opposite. Byte order is "little-endian" to match common
CPU architectures, whereas bit order is "big-endian" for left-to-right readability.

Implementations may choose to implement accessors for packed bits using machine words larger than 8 bits for performance
reasons. If so, they MUST not impose any additional constraints on data length or alignment.

### Examples

- `0x10 0x04 0xee 0xe0`

    - Header: PACKED_BITS, Padding=4
    - Data bytes: `0xee 0xe0`
        - The same bytes in binary, most-significant bit first: `1110 1110 1110 0000`
        - Discarding Padding (4) bits from the end, which SHOULD be zero: `1110 1110 1110`
    - Unpacked representation, 12 elements: `[1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0]`

- `0x10 0x07 0x80`

    - Header: PACKED_BITS, Padding=7
    - Data byte: `0x80`
    - Unpacked representation, 1 element: `[1]`

- `0x10 0x00 0xf0 0x42`

    - Header: PACKED_BITS, Padding=0
    - Data bytes: `0xf0 0x42`
        - The same bytes in binary, most-significant bit first: `1111 0000 0100 0010`
    - Unpacked representation, 16 elements: `[1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]`

- `0x03 0x00 0xff 0x00 0x01`

    - Header bytes: INT8
    - Data bytes: `0xff 0x00 0x01`
    - Unpacked representation, 3 elements: `[-1, 0, 1]`

- `0x27 0x00 0x00 0x00 0x80 0x3f 0x34 0x12 0x80 0x7f`

    - Header: FLOAT32
    - Data bytes: `0x00 0x00 0x80 0x3f 0x34 0x12 0x80 0x7f`
        - The same bytes as two 32-bit words, least significant byte first: `0x3f800000 0x7f801234`
        - The same 32-bit words interpreted as IEEE 754 `binary32`: `1.0 NaN(0x001234)`
    - Unpacked representation, 2 elements: `[1.0, NaN]`

## Test Plan

See the [README](tests/README.md) for tests.
