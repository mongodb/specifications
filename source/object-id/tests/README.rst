===========================
ObjectID Machine Hash Tests
===========================

The ``vectors.yml`` and ``vectors.json`` test files can be used to verify the
implementation of the 24-bit variant of the FNV1a hash that the ObjectID
specification requires for hashing the machine ID part of the ObjectID.

The ``vectors`` array contains an object for each of the test cases from the
`FNV-1a test suite`_. Each element contains a vector, and its corresponding
24-bit hash.

The test vector is either represented in the ``vector`` field as an ordinary
string, or in the ``vectorHex`` field in case it has non-ASCII characters. The
``vectorHex`` field is a conversion of each character of the vector into its
corresponding ASCII value in ``%02x`` form.

The hash is presented by the conversion of the 24-bit hash value into a
hexadecimal base akin to ``sprintf("%06x", $hash);``.

.. _`FNV-1a test suite`: http://www.isthe.com/chongo/src/fnv/test_fnv.c

Misc Files
----------

``convert-hash-vectors-to-yml.php`` converts the `FNV-1a test suite` into the
``vectors.yml`` file, which contains our 24-bit variant of the FNV-1a 32-bit
test vectors.

``verify-vectors.yml`` has a simple implementation to verify whether the hash
for each element can be re-created from the generated ``vectors.yml`` file.

``vectors.json`` was created through the standard ``make`` process for
converting YAML into JSON files.
