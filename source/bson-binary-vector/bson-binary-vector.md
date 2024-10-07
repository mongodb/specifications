# BSON Binary Subtype 9 - Vector

- Status: Pending
- Minimum Server Version: N/A

______________________________________________________________________

## Abstract

This document describes the subtype of the Binary BSON type used for efficient storage and retrieval of vectors. Vectors
here refer to densely packed arrays of numbers, all of the same type.

## Motivation

These representations correspond to the numeric types supported by popular numerical libraries for vector processing,
such as NumPy, PyTorch, TensorFlow and Apache Arrow. Storing and retrieving vector data using the same densely packed
format used by these libraries can result in significant memory savings and processing efficiency.

### META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

This specification introduces a new BSON binary subtype, the vector, with value `"\x09"`.

Drivers SHOULD provide idiomatic APIs to translate between arrays of numbers and this BSON Binary specification.

### Data Types

Each vector can take one of multiple data types (dtypes). The following table lists the dtypes implemented.

| Vector data type | Alias      | Bits per vector element | [Arrow Data Type](https://arrow.apache.org/docs/cpp/api/datatype.html) (for illustration) |
| ---------------- | ---------- | ----------------------- | ----------------------------------------------------------------------------------------- |
| `0x03`           | INT8       | 8                       | INT8                                                                                      |
| `0x27`           | FLOAT32    | 32                      | FLOAT                                                                                     |
| `0x10`           | PACKED_BIT | 1     `*`               | BOOL                                                                                      |

`*` A Binary Quantized (PACKED_BIT) Vector is a vector of 0s and 1s (bits), but it is represented in memory as a list of
integers in \[0, 255\]. So, for example, the vector `[0, 255]` would be shorthand for the 16-bit vector
`[0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1]`. The idea is that each number (a uint8) can be stored as a single byte. Of course,
some languages, Python for one, do not have an uint8 type, so must be represented as an int in memory, but not on disk.

### Byte padding

As not all data types have a bit length equal to a multiple of 8, and hence do not fit squarely into a certain number of
bytes, a second piece of metadata, the "padding" is included. This instructs the driver of the number of bits in the
final byte that are to be ignored. It is the least-significant bits that are ignored.

### Binary structure

Following the binary subtype `\x09` a two-element byte array of metadata precedes the packed numbers.

- The first byte (dtype) describes its data type. The table above shows those that MUST be implemented. This table may
  increase. dtype is an unsigned integer.

- The second byte (padding) prescribes the number of bits to ignore in the final byte of the value. It is a non-negative
  integer. It must be present, even in cases where it is not applicable, and set to zero.

- The remainder contains the actual vector elements packed according to dtype.

All values use the little-endian format.

#### Example

Let's take a vector `[238, 224]` of dtype PACKED_BIT (`\x10`) with a padding of `4`.

In hex, it looks like this: `b"\x10\x04\xee\xe0"`: 1 byte for dtype, 1 for padding, and 1 for each uint8.

We can visualize the binary representation like so:

<table border="1" cellspacing="0" cellpadding="5">
  <tr>
    <td colspan="8">1st byte: dtype (from list in previous table) </td>
    <td colspan="8">2nd byte: padding (values in [0,7])</td>
    <td colspan="8">1st uint8: 238</td>
    <td colspan="8">2nd uint8: 224</td>
  </tr>
  <tr>
    <td>0</td>
    <td>0</td>
    <td>0</td>
    <td>1</td>
    <td>0</td>
    <td>0</td>
    <td>0</td>
    <td>0</td>
    <td>0</td>
    <td>0</td>
    <td>0</td>
    <td>0</td>
    <td>0</td>
    <td>1</td>
    <td>0</td>
    <td>0</td>
    <td>1</td>
    <td>1</td>
    <td>1</td>
    <td>0</td>
    <td>1</td>
    <td>1</td>
    <td>1</td>
    <td>0</td>
    <td>1</td>
    <td>1</td>
    <td>1</td>
    <td>0</td>
    <td>0</td>
    <td>0</td>
    <td>0</td>
    <td>0</td>
  </tr>
</table>

Finally, after we remove the last 4 bits of padding, the actual bit vector has a length of 12 and looks like this!

| 1   | 1   | 1   | 0   | 1   | 1   | 1   | 0   | 1   | 1   | 1   | 0   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Reference Implementation

- PYTHON (PYTHON-4577) [pymongo.binary](https://github.com/mongodb/mongo-python-driver/blob/master/bson/binary.py)

## Test Plan

See the [README](tests/README.md) for tests.

## FAQ

- What MongoDB Server version does this apply to?
  - Files in the "specifications" repository have no version scheme. They are not tied to a MongoDB server version.
- In PACKED_BIT, why would one choose to use integers in \[0, 256)?
  - This follows a well-established precedent for packing binary-valued arrays into bytes (8 bits), This technique is
    widely used across different fields, such as data compression, communication protocols, and file formats, where you
    want to store or transmit binary data more efficiently by grouping 8 bits into a single byte (uint8). For an example
    in Python, see
    [numpy.unpackbits](https://numpy.org/doc/2.0/reference/generated/numpy.unpackbits.html#numpy.unpackbits).
