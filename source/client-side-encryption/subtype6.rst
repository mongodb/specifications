=====================
BSON Binary Subtype 6
=====================

:Title: BSON Binary Subtype 6
:Author: Kevin Albertson
:Spec Lead: A\. Jesse Jiryu Davis
:Approvers: Bernie Hackett, Dan Pasette, David Storch, Eliot Horowitz, Kenn White, Mark Benvenuto, Scott L'Hommedieu
:Advisory Group: A\. Jesse Jiryu Davis, Kenn White, Scott L'Hommedieu, Mark Benvenuto, Bernie Hackett
:Status: Accepted
:Type: Standards
:Minimum Server Version: 4.2
:Last Modified: June 14, 2019
:Version: 1.0.0

.. contents::

--------

Abstract
========

Client side encryption requires a new binary subtype to store (1)
encrypted ciphertext with metadata, and (2) binary markings indicating
what values must be encrypted in a document. (1) is stored in the
server, but (2) is only used in the communication protocol between
libmongocrypt and mongocryptd described in `Driver Spec: Client Side Encryption
Encryption <https://github.com/mongodb/specifications/tree/master/source/client-side-encryption/client-side-encryption.rst>`_.

META
====
The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”,
“SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this
document are to be interpreted as described in \`RFC 2119
<https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============
This spec introduces a new BSON binary subtype with value 6. The binary
has multiple formats determined by the first byte, but are all related
to FLE. The first byte indicates the type and layout of the remaining
data.

All values are represented in little endian. The payload is generally
optimized for storage size. The exception is the intent-to-encrypt
markings which are only used between libmongocrypt and mongocryptd and
never persisted.

.. code:: typescript

   struct {
      uint8 subtype;
      [more data - see individual type definitions]
   }

================ ======== ====================
**Name**         **Type** **Description**
subtype          uint8    Type of blob format.
================ ======== ====================

======== ================================================== =====================================================================================================================
**Type** **Name**                                           **Blob Description**
0        Intent-to-encrypt marking.                         Contains unencrypted data that will be encrypted (by libmongocrypt) along with metadata describing how to encrypt it.
1        AEAD_AES_CBC_HMAC_SHA512 deterministic ciphertext. The metadata and encrypted data for deterministic encrypted data.
2        AEAD_AES_CBC_HMAC_SHA512 randomized ciphertext.    The metadata and encrypted data for random encrypted data.
======== ================================================== =====================================================================================================================

Type 0: Intent-to-encrypt marking
---------------------------------

.. code:: typescript

   struct {
      uint8 subtype = 0;
      [ bson ];
   }

bson is the raw bytes of the following BSON document:

======== ============= =========== =========================================================================================================================================================================
**Name** **Long Name** **Type**    **Description**
v        value         any         Value to encrypt.
a        algorithm     int32       Encryption algorithm to use. Same as fle_blob_subtype: 1 for deterministic, 2 for randomized.
ki       keyId         UUID        Optional. Used to query the key vault by \_id. If omitted, then "ka" must be specified.
ka       keyAltName    BSON scalar Optional. Used to query the key vault by keyAltName. If omitted, then "ki" must be specified. This can be any BSON value other than an object, array, or code with scope.
======== ============= =========== =========================================================================================================================================================================

Types 1 and 2: Ciphertext
-------------------------

.. code:: typescript

   struct {
      uint8 subtype = (1 or 2);
      uint8 key_uuid[16];
      uint8 original_bson_type;
      uint8 ciphertext[ciphertext_length];
   }

================== ===================================================================
**Name**           **Description**
subtype            Type of blob format and encryption algorithm used.
key_uuid[16]       The value of \_id for the key used to decrypt the ciphertext.
original_bson_type The byte representing the original BSON type of the encrypted data.
ciphertext[]       The encrypted ciphertext (includes IV prepended).
================== ===================================================================

Test Plan
=========

Covered in `Driver Spec: Client Side Encryption
Encryption <https://github.com/mongodb/specifications/tree/master/source/client-side-encryption/client-side-encryption.rst>`_.

Design Rationale
================

Why not use a new BSON type?
----------------------------
An alternative to using a new binary subtype would be introducing a new
BSON type. This would be a needless backwards breaking change. Since FLE
is largely a client side feature, it should be possible to store
encrypted data in old servers.

Plus, encrypted ciphertext is inherently a binary blob. Packing metadata
inside isolates all of the encryption related data into one BSON value
that can be treated as an opaque blob in most contexts.

Why not use separate BSON binary subtypes instead of a nested subtype?
----------------------------------------------------------------------
If we used separate subtypes, we'd need to reserve three (and possibly
more in the future) of our 124 remaining subtypes.

Why are intent-to-encrypt markings needed?
------------------------------------------
Intent-to-encrypt markings provide a simple way for mongocryptd to
communicate what values need to be encrypted to libmongocrypt.
Alternatively, mongocryptd could respond with a list of field paths. But
field paths are difficult to make unambiguous, and even the query
language is not always consistent.

What happened to the "key vault alias"?
---------------------------------------
In an earlier revision of this specification the notion of a "key vault
alias". The key vault alias identified one of possibly many key vaults
that stored the key to decrypt the ciphertext. However, enforcing one
key vault is a reasonable restriction for users. Users can migrate from
one key vault to another without ciphertext data including a key vault
alias. If we find a future need for multiple key vaults, we can easily
introduce a new format with the fle_blob_subtype.

Why distinguish between "deterministic" and "randomized" when they
contain the same fields?

Deterministic and randomized ciphertext supports different behavior.
Deterministic ciphertext supports exact match queries but randomized
does not.

Why is the original BSON type not encrypted?
--------------------------------------------

Exposing the underlying BSON type gives some validation of the data that
is encrypted. A JSONSchema on the server can validate that the
underlying encrypted BSON type is correct.

Reference Implementation
========================

libmongocrypt and mongocryptd will be the reference implementation of
how BSON binary subtype 6 is used.

Security Implication
====================

It would be a very bad security flaw if intent-to-encrypt markings were
confused with ciphertexts. This could lead to a marking inadvertently
being stored on a server – meaning that plaintext is stored where
ciphertext should have been.

Therefore, the leading byte of the BSON binary subtype distinguishes
between marking and ciphertext.


