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
format used by these libraries can result in up to 8x memory savings and orders of magnitude improvement in processing
efficiency.

`*` Succinctly put, a Binary Quantized Vector is just a vector of 0s and 1s (bits), but it is often represented as a
list of uint8 (int in Python). So, for example, the vector `[255, 0]` would be shorthand for the 16 bit vector
`[1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0]`.\
The authors are well-aware of the inherent ambiguity here. This is a
market-standard, unfortunately. Change is inevitable.

## META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

This spec introduces a new BSON binary subtype, the vector, with value `"\x09"`. Each vector can take one of multiple
data types (dtypes). The following table lists the first dtypes implemented.

| Vector data type | Alias      | Bits per vector element | [PyArrow Data Type](https://arrow.apache.org/docs/cpp/api/datatype.html) (for illustration) |
| ---------------- | ---------- | ----------------------- | ------------------------------------------------------------------------------------------- |
| `0x03`           | INT8       | 8                       | INT8                                                                                        |
| `0x27`           | FLOAT32    | 32                      | FLOAT                                                                                       |
| `0x10`           | PACKED_BIT | 1     `*`               | BOOL                                                                                        |

As not all data types have a bit length equal to a multiple of 8, and hence do not fit squarely into a certain number of
bytes, a second piece of metadata, the "padding" is included. This instructs the driver of the number of bits in the
final byte that are to be ignored.

The binary structure the vector subtype's value is this. Following the binary subtype `0x09` is a two-element byte
array.

- The first byte (dtype) describes its data type, such as float32 or int8. The table above shows the implemented
  initially implemented in Python. The complete list of data types runs from `0x02` to `0x4b`

- The second byte (padding) prescribes the number of bits to ignore in the final byte of the value.Ω

- The remainder contains the actual vector elements packed according to dtype.

All values use the little-endian format.

## Reference Implementation

Please consult the Python driver's `pymongo.binary` module. Prose tests described below can be found in
`test.test_bson.TestBSON.test_vector`.

## Prose Tests

The following tests have not yet been automated, but MUST still be tested.

### 1. Standard encoding / decoding from a list of numbers

For each data type, the API must provide an idiomatic way to consume a list of that type that encodes to BSON and
decodes back to its original form.

### 2. JSON functionality

For each data type, the API must provide an idiomatic way to consume a list of that type that dumps to JSON and loads
back to its original form.

### 3. PACKED_BIT (Binary Quantized) Vector Tests

PACKED_BIT vectors must provide a method to consume a list of integers in \[0, 255\] that actually is a representation
of a vector of 0s and 1s (plus additionally padding if appropriate) and reproduce these inputs.

PACKED_BIT vectors should also be able to be output in an idiomatic format (e.g. `List[int]`, `List<Integer>`) the true
mathematical representation of the vector. This being a vector of 0s and 1s with any additional elements from padding
discarded.

### 4. Invalid cases

Because we the vector represents data types that are often not native to a driver's language, it is important that
invalid numbers are trapped.

- For `INT8`, only numbers within `[-128, 127]` are permitted.
- For `PACKED_BIT`, only numbers within `[0, 255]` are permitted.
