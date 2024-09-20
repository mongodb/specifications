# BSON Binary Subtype 9 - Vector

- Status: Pending
- Minimum Server Version: N/A

______________________________________________________________________

## Abstract

This document describes the addition of a new subtype to the Binary BSON type. This subtype is used for efficient
storage and retrieval of vectors. Vectors here refer to densely packed arrays of numbers, all of the same type.

## Motivation

These representations correspond to the numeric types supported by popular numerical libraries for vector processing,
such as NumPy, PyTorch, TensorFlow and Apache Arrow. Storing and retrieving vector data using the same densely packed
format used by these libraries can result in up to significant memory savings and processing efficiency.

### META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

This specification introduces a new BSON binary subtype, the vector, with value `"\x09"`.

Drivers SHOULD provide idiomatic APIs to translate between arrays of numbers and this BSON Binary specification.

#### Data Types

Each vector can take one of multiple data types (dtypes). The following table lists the first dtypes implemented.

| Vector data type | Alias      | Bits per vector element | [PyArrow Data Type](https://arrow.apache.org/docs/cpp/api/datatype.html) (for illustration) |
| ---------------- | ---------- | ----------------------- | ------------------------------------------------------------------------------------------- |
| `0x03`           | INT8       | 8                       | INT8                                                                                        |
| `0x27`           | FLOAT32    | 32                      | FLOAT                                                                                       |
| `0x10`           | PACKED_BIT | 1     `*`               | BOOL                                                                                        |

`*` A Binary Quantized (PACKED_BIT) Vector is a vector of 0s and 1s (bits), but it is represented in memory as a list of
integers in \[0, 255\]. So, for example, the vector `[0, 255]` would be shorthand for the 16 bit vector
`[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1]`. The idea is that each number (a uint8) can be stored as a single byte. Of course,
some languages, Python for one, do not have an uint8 type, so must be represented as an int in memory, but not on disk.

The authors are well-aware of the inherent ambiguity here, and alternatives. This is a market-standard, unfortunately.
Change is inevitable.

#### Byte padding

As not all data types have a bit length equal to a multiple of 8, and hence do not fit squarely into a certain number of
bytes, a second piece of metadata, the "padding" is included. This instructs the driver of the number of bits in the
final byte that are to be ignored.

#### Binary structure

Following the binary subtype `0x09` is a two-element byte array.

- The first byte (dtype) describes its data type. The table above shows those that MUST be implemented. This table may
  increase.

- The second byte (padding) prescribes the number of bits to ignore in the final byte of the value.

- The remainder contains the actual vector elements packed according to dtype.

All values use the little-endian format.

### Reference Implementation

Please consult the Python driver's
[pymongo.binary](https://github.com/mongodb/mongo-python-driver/blob/master/bson/binary.py) module.

### Test Plan

See the [README](tests/README.md) for tests.
