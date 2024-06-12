# BSON

Latest version of the specification can be found at <https://bsonspec.org/spec.html>.

----

## Specification Version 1.1
BSON is a binary format in which zero or more ordered key/value pairs are stored as a single entity. We call this entity a document.

The following grammar specifies version 1.1 of the BSON standard. We've written the grammar using a pseudo-BNF syntax. Valid BSON data is represented by the document non-terminal.

### Basic Types
The following basic types are used as terminals in the rest of the grammar. Each type must be serialized in little-endian format.
```
byte	1 byte (8-bits)
signed_byte(n)	8-bit, two's complement signed integer for which the value is n
unsigned_byte(n)	8-bit unsigned integer for which the value is n
int32	4 bytes (32-bit signed integer, two's complement)
int64	8 bytes (64-bit signed integer, two's complement)
uint64	8 bytes (64-bit unsigned integer)
double	8 bytes (64-bit IEEE 754-2008 binary floating point)
decimal128	16 bytes (128-bit IEEE 754-2008 decimal floating point)
```

### Non-terminals
The following specifies the rest of the BSON grammar. Note that we use the * operator as shorthand for repetition (e.g. (byte*2) is byte byte). When used as a unary operator, * means that the repetition can occur 0 or more times.

```
document	::=	int32 e_list unsigned_byte(0)	BSON Document. int32 is the total number of bytes comprising the document.
e_list	::=	element e_list
|	""
element	::=	signed_byte(1) e_name double	64-bit binary floating point
|	signed_byte(2) e_name string	UTF-8 string
|	signed_byte(3) e_name document	Embedded document
|	signed_byte(4) e_name document	Array
|	signed_byte(5) e_name binary	Binary data
|	signed_byte(6) e_name	Undefined (value) — Deprecated
|	signed_byte(7) e_name (byte*12)	ObjectId
|	signed_byte(8) e_name unsigned_byte(0)	Boolean - false
|	signed_byte(8) e_name unsigned_byte(1)	Boolean - true
|	signed_byte(9) e_name int64	UTC datetime
|	signed_byte(10) e_name	Null value
|	signed_byte(11) e_name cstring cstring	Regular expression - The first cstring is the regex pattern, the second is the regex options string. Options are identified by characters, which must be stored in alphabetical order. Valid option characters are i for case insensitive matching, m for multiline matching, s for dotall mode ("." matches everything), x for verbose mode, and u to make "\w", "\W", etc. match Unicode.
|	signed_byte(12) e_name string (byte*12)	DBPointer — Deprecated
|	signed_byte(13) e_name string	JavaScript code
|	signed_byte(14) e_name string	Symbol — Deprecated
|	signed_byte(15) e_name code_w_s	JavaScript code with scope — Deprecated
|	signed_byte(16) e_name int32	32-bit integer
|	signed_byte(17) e_name uint64	Timestamp
|	signed_byte(18) e_name int64	64-bit integer
|	signed_byte(19) e_name decimal128	128-bit decimal floating point
|	signed_byte(-1) e_name	Min key
|	signed_byte(127) e_name	Max key
e_name	::=	cstring	Key name
string	::=	int32 (byte*) unsigned_byte(0)	String - The int32 is the number of bytes in the (byte*) plus one for the trailing null byte. The (byte*) is zero or more UTF-8 encoded characters.
cstring	::=	(byte*) unsigned_byte(0)	Zero or more modified UTF-8 encoded characters followed by the null byte. The (byte*) MUST NOT contain unsigned_byte(0), hence it is not full UTF-8.
binary	::=	int32 subtype (byte*)	Binary - The int32 is the number of bytes in the (byte*).
subtype	::=	unsigned_byte(0)	Generic binary subtype
|	unsigned_byte(1)	Function
|	unsigned_byte(2)	Binary (Old)
|	unsigned_byte(3)	UUID (Old)
|	unsigned_byte(4)	UUID
|	unsigned_byte(5)	MD5
|	unsigned_byte(6)	Encrypted BSON value
|	unsigned_byte(7)	Compressed BSON column
|	unsigned_byte(8)	Sensitive
|	unsigned_byte(128)—unsigned_byte(255)	User defined
code_w_s	::=	int32 string document	Code with scope — Deprecated
```

### Notes

- Array - The document for an array is a normal BSON document with integer values for the keys, starting with 0 and continuing sequentially. For example, the array ['red', 'blue'] would be encoded as the document {'0': 'red', '1': 'blue'}. The keys must be in ascending numerical order.
- UTC datetime - The int64 is UTC milliseconds since the Unix epoch.
- Timestamp - Special internal type used by MongoDB replication and sharding. First 4 bytes are an increment, second 4 are a timestamp.
- Min key - Special type which compares lower than all other possible BSON element values.
- Max key - Special type which compares higher than all other possible BSON element values.
- Generic binary subtype - This is the most commonly used binary subtype and should be the 'default' for drivers and tools.
- Compressed BSON Column - Compact storage of BSON data. This data type uses delta and delta-of-delta compression and run-length-encoding for efficient element storage. Also has an encoding for sparse arrays containing missing values.
- The BSON "binary" or "BinData" datatype is used to represent arrays of bytes. It is somewhat analogous to the Java notion of a ByteArray. BSON binary values have a subtype. This is used to indicate what kind of data is in the byte array. Subtypes from 0 to 127 are predefined or reserved. Subtypes from 128 to 255 are user-defined.
  - unsigned_byte(2) Binary (Old) - This used to be the default subtype, but was deprecated in favor of subtype 0. Drivers and tools should be sure to handle subtype 2 appropriately. The structure of the binary data (the byte* array in the binary non-terminal) must be an int32 followed by a (byte*). The int32 is the number of bytes in the repetition.
  - unsigned_byte(3) UUID (Old) - This used to be the UUID subtype, but was deprecated in favor of subtype 4. Drivers and tools for languages with a native UUID type should handle subtype 3 appropriately.
  - unsigned_byte(128)—unsigned_byte(255) User defined subtypes. The binary data can be anything.
- Code with scope - Deprecated. The int32 is the length in bytes of the entire code_w_s value. The string is JavaScript code. The document is a mapping from identifiers to values, representing the scope in which the string should be evaluated.