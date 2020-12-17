======================
Client Side Encryption
======================

:Title: Client Side Encryption
:Author: Kevin Albertson
:Spec Lead: Jeff Yemin
:Approvers: Bernie Hackett, David Golden, David Storch
:Advisory Group: A\. Jesse Jiryu Davis, Kenn White, Scott L'Hommedieu, Mark Benvenuto, Bernie Hackett, Samantha Ritter, Matt Broadstone
:Status: Accepted
:Type: Standards
:Minimum Server Version: 4.2
:Last Modified: October 19, 2020
:Version: 1.3.0

.. contents::

--------

Abstract
========

MongoDB 4.2 introduced support for client side encryption, guaranteeing
that sensitive data can only be encrypted and decrypted with access to both
MongoDB and a separate key management provider (supporting AWS, Azure, GCP
and a local provider). Once enabled, data can be seamlessly encrypted
and decrypted with minimal application code changes.

META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Terms
=====

encrypted MongoClient
   A MongoClient with client side encryption enabled.

data key
   A key used to encrypt and decrypt BSON values. Data keys are
   encrypted with a key management service (e.g. AWS KMS) and stored within a document in the
   MongoDB key vault collection (see `Key vault collection schema for data keys`_ for a description of the data key document). Therefore, a client needs access to both
   MongoDB and the external KMS service to utilize a data key.

MongoDB key vault collection
   A MongoDB collection designated to contain data keys. This can either be co-located with the data-bearing cluster, or in a separate external MongoDB cluster.

Key Management Service (KMS)
   An external service providing fixed-size encryption/decryption. Only data keys are encrypted and decrypted with KMS. Only AWS KMS (and a local service) is supported.

Customer Master Key (CMK)
   The underlying key AWS KMS uses to encrypt and decrypt. See `AWS Key Management Service Concepts <https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#master_keys>`_.

schema
   A MongoDB JSON Schema (either supplied by
   the server or client-side) which may include metadata about encrypted
   fields. This is a JSON Schema based on draft 4 of the JSON Schema
   specification, `as documented in the MongoDB
   manual. <https://docs.mongodb.com/manual/reference/operator/query/jsonSchema/>`_.

libmongocrypt
   A library, written in C, that coordinates communication,
   does encryption/decryption, caches key and schemas. `Located here <https://github.com/mongodb/libmongocrypt>`_.

mongocryptd
   A local process the driver communicates with to determine
   how to encrypt values in a command.

ciphertext
   One of the data formats of `BSON binary subtype 6 <https://github.com/mongodb/specifications/tree/master/source/client-side-encryption/subtype6.rst>`_, representing an encoded BSON document containing
   encrypted ciphertext and metadata.

Introduction
============

Client side encryption enables users to specify what fields in a
collection must be encrypted, and the driver automatically encrypts
commands and decrypts results. Automatic encryption is enterprise only.
But users can manually encrypt and decrypt with a new ClientEncryption
object.

Client side encryption requires MongoDB 4.2 compatible drivers, and is
only supported against 4.2 or higher servers. See `Why is a 4.2 server required?`_.

The following shows basic usage of the new API.

.. code:: python

   # The schema map identifies fields on collections that must undergo encryption.

   schema_map = open("./schemas.json", "r").read()

   # AWS KMS is used to decrypt data keys stored in the key vault collection.

   aws_creds = open("./aws_credentials.json", "r").read()

   # A client is configured for automatic encryption and decryption by passing
   # AutoEncryptionOpts. Automatic encryption is an enterprise only feature.

   opts = AutoEncryptionOpts(
       kms_providers={"aws": aws_creds},
       key_vault_namespace="db.datakeys",
       schema_map=schema_map)

   db = MongoClient(auto_encryption_opts=opts).db

   # Commands are encrypted, as determined by the JSON Schema from the schema_map.
   db.coll.insert_one({"ssn": "457-55-5462"})

   # Replies are decrypted.
   print(db.coll.find_one()) # { "ssn": "457-55-5462" } but stored and transported as ciphertext.

   # A ClientEncryption object is used for explicit encryption, decryption, and creating data keys.
   opts = ClientEncryptionOpts(kms_providers=kms, key_vault_namespace="db.datakeys")
   clientencryption = ClientEncryption(client, opts)

   # Use a ClientEncryption to create new data keys.
   # The master key identifies the CMK on AWS KMS to use for encrypting the data key.
   master_key = open("./aws_masterkey.json", "r").read()
   opts = DataKeyOpts (master_key=master_key)
   created_key_id = clientencryption.create_data_key("aws", opts)

   # Use a ClientEncryption to explicitly encrypt and decrypt.
   opts = EncryptOpts(key_id=created_key_id,
       algorithm="AEAD_AES_256_CBC_HMAC_SHA_512-Random")
   encrypted = clientencryption.encrypt("secret text", opts)
   decrypted = clientencryption.decrypt(encrypted)

There are many moving parts to client side encryption with lots of
similar sounding terms. Before proceeding to implement the
specification, the following background should provide some context.

The driver interacts with multiple components to implement client side
encryption.

.. image:: includes/components.png

The driver communicates with…

-  **MongoDB cluster** to get remote JSON Schemas.
-  **MongoDB key vault collection** to get encrypted data keys and create new data
   keys.
-  **A KMS Provider** to decrypt fetched data keys and encrypt new data keys.
-  **mongocryptd** to ask what values in BSON commands must be
   encrypted.

The MongoDB key vault may be the same as the MongoDB cluster. Users may
choose to have data key stored on a separate MongoDB cluster, or
co-locate with their data.

MongoDB Key Vault collection
----------------------------
The key vault collection is a special MongoDB collection containing key
documents. See the appendix section `Key vault collection schema for data keys`_
for a description of the documents.

The key material in the key vault collection is encrypted with a separate
KMS service. Therefore, encryption and decryption requires access to a
MongoDB cluster and the KMS service.

KMS Provider
------------
A KMS provider (AWS KMS, Azure Key Vault, GCP KMS, or the local provider) is
used to decrypt data keys after fetching from the MongoDB Key Vault, and
encrypt newly created data keys.

mongocryptd
-----------
mongocryptd is a singleton local process needed for auto
encryption. It speaks the MongoDB wire protocol and the driver uses
mongocryptd by connecting with a MongoClient. By default, the driver
will attempt to automatically spawn mongocryptd. If the MongoClient is
configured with `extraOptions.mongocryptdBypassSpawn=true`, or 
`AutoEncryptionOpts.bypassAutoEncryption=true` then the driver will not 
attempt to spawn mongocryptd. The mongocryptd process is
responsible for self terminating after idling for a time period.

libmongocrypt
-------------
libmongocrypt is a C library providing crypto and coordination with
external components. `Located here <https://github.com/mongodb/libmongocrypt>`_.

**libmongocrypt is responsible for…**

-  orchestrating an internal state machine.
-  asking the driver to perform I/O, then handling the responses.

   -  includes constructing KMS HTTP requests and parsing KMS responses.

-  doing encryption and decryption.
-  caching data keys.
-  caching results of listCollections.
-  creating key material.

**The driver is responsible for…**

-  performing all I/O needed at every state:

   -  speaking to mongocryptd to mark commands.

   -  fetching encrypted data keys from key vault collection (mongod).

   -  running listCollections on mongod.

   -  decrypting encrypted data keys with KMS over TLS.

-  doing I/O asynchronously as needed.

See `Why require including a C library?`_.

User facing API
===============

Drivers MUST NOT preclude future options from being added to any of the
new interfaces.

Drivers MAY represent the options types in a way that is idiomatic to
the driver or language. E.g. options MAY be a BSON document or
dictionary type. The driver MAY forego validating options and instead
defer validation to the underlying implementation.

Drivers MAY deviate the spelling of option names to conform to their
language's naming conventions and implement options in an idiomatic way
(e.g. keyword arguments, builder classes, etc.).

MongoClient Changes
-------------------

.. code:: typescript

   class MongoClient {
      MongoClient(... autoEncryptionOpts: AutoEncryptionOpts);

      // Implementation details.
      private mongocrypt_t libmongocrypt_handle; // Handle to libmongocrypt.
      private Optional<MongoClient> mongocryptd_client; // Client to mongocryptd.
      private MongoClient keyvault_client; // Client used to run find on the key vault collection. This is either an external MongoClient or internal_client.
      private MongoClient metadata_client; // Client used to run listCollections. This is either an external MongoClient or internal_client.
      private Optional<MongoClient> internal_client; // An internal MongoClient. Created if no external keyVaultClient and/or metadataClient was set.
   }

   class AutoEncryptionOpts {
      keyVaultClient: Optional<MongoClient>;
      keyVaultNamespace: String;
      kmsProviders: Map<String, Map<String, Value>>;
      schemaMap: Optional<Map<String, Document>>; // Maps namespace to a local schema
      bypassAutoEncryption: Optional<Boolean>; // Default false.
      extraOptions: Optional<Map<String, Value>>;
      metadataClient: Optional<MongoClient>;
   }

A MongoClient can be configured to automatically encrypt collection
commands and decrypt results.

Drivers MUST document that auto encryption is an enterprise-only
feature and that auto encryption only occurs on collection level
operations by including the following in the driver documentation for
AutoEncryptionOpts:

   Automatic encryption is an enterprise only feature that only applies to
   operations on a collection. Automatic encryption is not supported for
   operations on a database or view, and operations that are not bypassed
   will result in error (see `libmongocrypt: Auto Encryption Whitelist`_).
   To bypass automatic encryption for all operations, set
   bypassAutoEncryption=true in AutoEncryptionOpts.

Explicit encryption/decryption and automatic decryption is a community
feature. A MongoClient configured with bypassAutoEncryption=true will
still automatically decrypt.

Drivers MUST document that auto encryption requires the authenticated
user to have the listCollections privilege action by including the
following in the driver documentation for MongoClient.

   Automatic encryption requires the authenticated user to have the
   `listCollections privilege
   action <https://docs.mongodb.com/manual/reference/command/listCollections/#dbcmd.listCollections>`__.

See `Why is client side encryption configured on a MongoClient?`_

keyVaultNamespace
^^^^^^^^^^^^^^^^^
The key vault collection namespace refers to a collection that contains all
data keys used for encryption and decryption (aka the key vault collection).
Data keys are stored as documents in a special MongoDB collection. Data
keys are protected with encryption by a KMS provider (AWS KMS, Azure key
vault, GCP KMS, or a local master key).

metadataClient
^^^^^^^^^^^^^^
A client used to run ``listCollections`` to determine whether a collection has
an associated JSON schema with encrypted fields specified.

If a ``metadataClient`` is not passed in, and
``bypassAutomaticEncryption=false``, the ``metadataClient`` is set to an
internal ``MongoClient``. See `keyVaultClient, metadataClient, and the internal
MongoClient`_ for configuration behavior.

Drivers MUST document this behavior, using the following as a template:

   If ``metadataClient`` is not passed as an option, and
   ``bypassAutomaticEncryption=false``, a separate ``MongoClient`` is used
   internally. It is configured using the options of the parent ``MongoClient``
   with the ``AutoEncryptionOpts`` omitted.

See `What's the deal with metadataClient, keyVaultClient, and the internal client?`_

keyVaultClient
^^^^^^^^^^^^^^
The key vault collection is assumed to reside on the same MongoDB
cluster as indicated by the connecting URI. But the optional
keyVaultClient can be used to route data key queries to a separate
MongoDB cluster.

If a ``keyVaultClient`` is not passed, the ``keyVaultClient`` is set to an
internal ``MongoClient``. See `keyVaultClient, metadataClient, and the internal
MongoClient`_ for configuration behavior.

Drivers MUST document this behavior, using the following as a template:

   If ``keyVaultClient`` is not passed as an option, a separate ``MongoClient``
   is used internally. It is configured using the options of the parent
   ``MongoClient`` with the ``AutoEncryptionOpts`` omitted.

See `What's the deal with metadataClient, keyVaultClient, and the internal client?`_

keyVaultClient, metadataClient, and the internal MongoClient
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If a ``keyVaultClient`` is not passed, it is set to an internal ``MongoClient``.

If a ``metadataClient`` is not passed, and ``bypassAutomaticEncryption=false``,
it is set to an internal ``MongoClient``. If ``bypassAutomaticEncryption=true``,
the option is ignored since ``listCollections`` is only run during automatic
encryption.

If neither are passed, they are set to the same internal ``MongoClient``.

The internal ``MongoClient`` MUST be configured with the same options as the
parent ``MongoClient`` with the ``AutoEncryptionOpts`` excluded.

The following pseudo-code describes the configuration behavior:

.. code::
   def getOrCreateInternalClient (client, clientOpts):
      if client.internalClient != None:
         return client.internalClient
      internalClientOpts = copy(clientOpts)
      internalClientOpts.autoEncryptionOpts = None
      client.internalClient = MongoClient (internalClientOpts)

   def configureAutoEncryptionClients (client, clientOpts):
      if clientOpts.autoEncryptionOpts.keyVaultClient != None:
         client.keyVaultClient = clientOpts.autoEncryptionOpts.keyVaultClient
      else:
         client.keyVaultClient = getOrCreateInternalClient (client, clientOpts)

      if clientOpts.autoEncryptionOpts.bypassAutomaticEncryption:
         # metadataClient not needed. It is not an error if a user passed metadataClient.
         return

      if clientOpts.autoEncryptionOpts.metadataClient != None:
         client.metadataClient = clientOpts.autoEncryptionOpts.metadataClient
      else:
         client.metadataClient = getOrCreateInternalClient (client, clientOpts)

kmsProviders
^^^^^^^^^^^^
Multiple KMS providers may be specified. The kmsProviders map values differ by
provider ("aws", "azure", "gcp", and "local"). The "local" provider is configured
with master key material. The external providers are configured with credentials
to authenticate.

.. code:: typescript

   aws: {
      accessKeyId: String,
      secretAccessKey: String
   }

   azure: {
      tenantId: String,
      clientId: String,
      clientSecret: String,
      identityPlatformEndpoint: Optional<String> // Defaults to login.microsoftonline.com
   }

   gcp: {
      email: String,
      privateKey: byte[] or String, // May be passed as a base64 encoded string.
      endpoint: Optional<String> // Defaults to oauth2.googleapis.com
   }

   local: {
      key: byte[96] or String // The master key used to encrypt/decrypt data keys. May be passed as a base64 encoded string.
   }

See `Why are extraOptions and kmsProviders maps?`_

schemaMap
^^^^^^^^^
Automatic encryption is configured with an "encrypt" field in a
collection's JSONSchema. By default, a collection's JSONSchema is
periodically polled with the listCollections command. But a JSONSchema
may be specified locally with the schemaMap option. Drivers MUST
document that a local schema is more secure and MUST include the
following in the driver documentation for MongoClient:

   Supplying a schemaMap provides more security than relying on JSON
   Schemas obtained from the server. It protects against a malicious server
   advertising a false JSON Schema, which could trick the client into
   sending unencrypted data that should be encrypted.

Drivers MUST document that a local schema only applies to client side
encryption, and specifying JSON Schema features unrelated to encryption
will result in error. Drivers MUST include the following in the driver
documentation for MongoClient:

   Schemas supplied in the schemaMap only apply to configuring automatic
   encryption for client side encryption. Other validation rules in the
   JSON schema will not be enforced by the driver and will result in an
   error.

bypassAutoEncryption
^^^^^^^^^^^^^^^^^^^^

Drivers MUST disable auto encryption when the 'bypassAutoEncryption'
option is true and not try to spawn mongocryptd. Automatic encryption 
may be disabled with the bypassAutoEncryption option. 
See `Why is there a bypassAutoEncryption?`_.

extraOptions
^^^^^^^^^^^^
The extraOptions relate to the mongocryptd process, an implementation
detail described in the `Implementation`_ section:

.. code:: typescript

   {
      // Defaults to "mongodb://localhost:27020".
      mongocryptdURI: Optional<String>,

      // Defaults to false.
      mongocryptdBypassSpawn: Optional<Boolean>,

      // Used for spawning. Defaults to empty string and spawns mongocryptd from system path.
      mongocryptdSpawnPath: Optional<String>,

      // Passed when spawning mongocryptd. If omitted, this defaults to ["--idleShutdownTimeoutSecs=60"]
      mongocryptdSpawnArgs: Optional<Array[String]>
   }

Drivers MUST implement extraOptions in a way that allows
deprecating/removing options in the future without an API break, such as
with a BSON document or map type instead of a struct type with fixed
fields. See `Why are extraOptions and kmsProviders maps?`_.

ClientEncryption
----------------

.. code:: typescript

   class ClientEncryption {
      ClientEncryption(opts: ClientEncryptionOpts);

      // Creates a new key document and inserts into the key vault collection.
      // Returns the \_id of the created document as a UUID (BSON binary subtype 4).
      createDataKey(kmsProvider: String, opts: Optional<DataKeyOpts>): Binary;

      // Encrypts a BSONValue with a given key and algorithm.
      // Returns an encrypted value (BSON binary of subtype 6). The underlying implementation may return an error for prohibited BSON values.
      encrypt(value: BSONValue, opts: EncryptOpts): Binary;

      // Decrypts an encrypted value (BSON binary of subtype 6). Returns the original BSON value.
      decrypt(value: Binary): BSONValue;

      // Implementation details.
      private mongocrypt_t libmongocrypt_handle;
      private MongoClient keyvault_client;
   }

   class ClientEncryptionOpts {
      keyVaultClient: MongoClient;
      keyVaultNamespace: String;
      kmsProviders: Map<String, Map<String, Value>>;
   }

The ClientEncryption encapsulates explicit operations on a key vault
collection that cannot be done directly on a MongoClient. Similar to
configuring auto encryption on a MongoClient, it is
constructed with a MongoClient (to a MongoDB cluster containing the key
vault collection), KMS provider configuration, and keyVaultNamespace. It
provides an API for explicitly encrypting and decrypting values, and
creating data keys. It does not provide an API to query keys from the key
vault collection, as this can be done directly on the MongoClient.

See `Why do we have a separate top level type for ClientEncryption?`_ and `Why do we need to pass a client to create a ClientEncryption?`_.

DataKeyOpts
-----------

.. code:: typescript

   class DataKeyOpts {
      masterKey: Optional<Document>
      keyAltNames: Optional<Array[String]> // An alternative to \_id to reference a key.
   }

masterKey
^^^^^^^^^
The masterKey document identifies a KMS-specific key used to encrypt the new data
key. If the kmsProvider is "aws" it is required and has the following fields:

.. code:: typescript

   {
      region: String,
      key: String, // The Amazon Resource Name (ARN) to the AWS customer master key (CMK).
      endpoint: Optional<String> // An alternate host identifier to send KMS requests to. May include port number. Defaults to "kms.<region>.amazonaws.com"
   }

If the kmsProvider is "azure" the masterKey is required and has the following fields:

.. code:: typescript

   {
      keyVaultEndpoint: String, // Host with optional port. Example: "example.vault.azure.net".
      keyName: String,
      keyVersion: Optional<String> // A specific version of the named key, defaults to using the key's primary version.
   }

If the kmsProvider is "gcp" the masterKey is required and has the following fields:

.. code:: typescript

   {
      projectId: String,
      location: String,
      keyRing: String,
      keyName: String,
      keyVersion: Optional<String>, // A specific version of the named key, defaults to using the key's primary version.
      endpoint: Optional<String> // Host with optional port. Defaults to "cloudkms.googleapis.com".
   }

If the kmsProvider is "local" the masterKey is not applicable.

Drivers MUST document the expected fields in the masterKey document for the
"aws", "azure", and "gcp" KMS providers. Additionally, they MUST document that
masterKey is **required** for these providers and is not optional.

The value of `endpoint` or `keyVaultEndpoint` is a host name with optional port
number separated by a colon. E.g. "kms.us-east-1.amazonaws.com" or
"kms.us-east-1.amazonaws.com:443". It is assumed that the host name is not an IP
address or IP literal. Though drivers MUST NOT inspect the value of "endpoint"
that a user sets when creating a data key, a driver will inspect it when
connecting to KMS to determine a port number if present.

keyAltNames
^^^^^^^^^^^
An optional list of string alternate names used to reference a key. If a
key is created with alternate names, then encryption may refer to the
key by the unique alternate name instead of by \_id. The following
example shows creating and referring to a data key by alternate name:

.. code:: python

   opts = DataKeyOpts(keyAltNames=["name1"])
   clientencryption.create_data_key ("local", opts)
   # reference the key with the alternate name
   opts = EncryptOpts(keyAltName="name1", algorithm="AEAD_AES_256_CBC_HMAC_SHA_512-Random")
   clientencryption.encrypt("457-55-5462", opts)

EncryptOpts
-----------

.. code:: typescript

   class EncryptOpts {
      keyId : Optional<Binary>
      keyAltName: Optional<String>
      algorithm: String
   }

Explicit encryption requires a key and algorithm. Keys are either
identified by \_id or by alternate name. Exactly one is required.

keyId
^^^^^
Identifies a data key by \_id. The value is a UUID (binary subtype 4).

keyAltName
^^^^^^^^^^
Identifies a key vault collection document by 'keyAltName'.

algorithm
^^^^^^^^^
The string "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic" or
"AEAD_AES_256_CBC_HMAC_SHA_512-Random"

User facing API: When Auto Encryption Fails
===========================================

Auto encryption requires parsing the MongoDB query language client side
(with the mongocryptd process). For unsupported operations, an exception
will propagate to prevent the possibility of the client sending
unencrypted data that should be encrypted. Drivers MUST include the
following in the documentation for MongoClient:

   If automatic encryption fails on an operation, use a MongoClient
   configured with bypassAutoEncryption=true and use
   ClientEncryption.encrypt() to manually encrypt values.

For example, currently an aggregate with $lookup into a foreign
collection is unsupported (mongocryptd returns an error):

.. code:: python

   opts = AutoEncryptionOpts (
      key_vault_namespace="keyvault.datakeys",
      kms_providers=kms)
   client = MongoClient(auto_encryption_opts=opts)
   accounts = client.db.accounts
   results = accounts.aggregate([
      {
         "$lookup": {
         "from": "people",
         "pipeline": [
            {
               "$match": {
                  "ssn": "457-55-5462"
               }
            }
         ],
         "as": "person"
      }
   ]) # Raises an error

   print (next(results)["person"]["ssn"])

In this case, the user should use explicit encryption on a client
configured to bypass auto encryption. (Note, automatic decryption still
occurs).

.. code:: python

   opts = AutoEncryptionOpts (
      key_vault_namespace="keyvault.datakeys",
      kms_providers=kms,
      bypass_auto_encryption=True)
   client = MongoClient(auto_encryption_opts=opts)

   opts = ClientEncryptionOpts (
      key_vault_client=client,
      key_vault_namespace="keyvault.datakeys",
      kms_providers=kms,
      bypass_auto_encryption=True)
   client_encryption = ClientEncryption(opts)

   accounts = client.db.accounts
   results = accounts.aggregate([
      {
         "$lookup": {
         "from": "people",
         "pipeline": [
            {
               "$match": {
                  "ssn": client_encryption.encrypt("457-55-5462", EncryptOpts(key_alt_name="ssn", algorithm="AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"))
               }
            }
         ],
         "as": "person"
      }
   ]) # Throws an exception

   print (next(results)["person"]["ssn"])

User facing API: View limitations
=================================

Users cannot use auto encryption with views. Attempting to do so results
in an exception. Drivers do not need to validate when the user is
attempting to enable auto encryption on a view, but may defer to the
underlying implementation.

Although auto encryption does not work on views, users may still use
explicit encrypt and decrypt functions on views on a MongoClient without
auto encryption enabled.

See `Why do operations on views fail?`_.

Implementation
==============

Drivers MUST integrate with libmongocrypt. libmongocrypt exposes a
simple state machine to perform operations. Follow `the guide to integrating libmongocrypt <https://github.com/mongodb/libmongocrypt/blob/master/integrating.md>`_.

Drivers SHOULD take a best-effort approach to store sensitive data
securely when interacting with KMS since responses may include decrypted
data key material (e.g. use secure malloc if available).

All errors from the MongoClient to mongocryptd MUST be distinguished in
some way (e.g. exception type) to make it easier for users to
distinguish when a command fails due to auto encryption limitations.

All errors from the MongoClient interacting with the key vault
collection MUST be distinguished in some way (e.g. exception type) to
make it easier for users to distinguish when a command fails due to
behind-the-scenes operations required for encryption or decryption.

Integrating with libmongocrypt
==============================

Each ClientEncryption instance MUST have one handle to libmongocrypt.
See the `The guide to integrating libmongocrypt <https://github.com/mongodb/libmongocrypt/blob/master/integrating.md>`__
for more information.

libmongocrypt exposes logging capabilities. If a driver provides a
logging mechanism, it MUST enable this logging and integrate. E.g. if
your driver exposes a logging callback that a user can set, it SHOULD be
possible to get log messages from libmongocrypt.

Drivers MUST propagate errors from libmongocrypt in whatever way is
idiomatic to the driver (exception, error object, etc.). These errors
MUST be distinguished in some way (e.g. exception type) to make it
easier for users to distinguish when a command fails due to client side
encryption.

Managing mongocryptd
====================
If a MongoClient is configured for Client Side Encryption 
(eg. bypassAutoEncryption=false), then by default 
(unless mongocryptdBypassSpawn=true), mongocryptd MUST be
spawned by the driver. Spawning MUST include the command line argument
--idleShutdownTimeoutSecs. If the user does not supply one through
extraOptions.mongocryptdSpawnArgs (which may be either in the form
"--idleShutdownTimeoutSecs=60" or as two consecutive arguments
["--idleShutdownTimeoutSecs", 60], then the driver MUST append
--idleShutdownTimeoutSecs=60 to the arguments. This tells mongocryptd
to automatically terminate after 60 seconds of non-use. The stdout
and stderr of the spawned process MUST not be exposed in the driver (e.g.
redirect to /dev/null). Users can pass the argument --logpath to
extraOptions.mongocryptdSpawnArgs if they need to inspect mongocryptd
logs.

Upon construction, the MongoClient MUST create a MongoClient to
mongocryptd configured with serverSelectionTimeoutMS=1000.

If spawning is necessary, the driver MUST spawn mongocryptd whenever
server selection on the MongoClient to mongocryptd fails. If the
MongoClient fails to connect after spawning, the server selection error
is propagated to the user.

Single-threaded drivers MUST connect with `serverSelectionTryOnce=false <../server-selection/server-selection.rst#serverselectiontryonce>`_
, connectTimeoutMS=1000, and MUST bypass `cooldownMS <../server-discovery-and-monitoring/server-discovery-and-monitoring.rst#cooldownms>`_ when connecting to mongocryptd. See `Why are serverSelectionTryOnce and cooldownMS disabled for single-threaded drivers connecting to mongocryptd?`_.

If the ClientEncryption is configured with mongocryptdBypassSpawn=true,
then the driver is not responsible for spawning mongocryptd. If server
selection ever fails when connecting to mongocryptd, the server
selection error is propagated to the user.

ClientEncryption
================
The new ClientEncryption type interacts uses libmongocrypt to perform
encryption and decryption, and to implement
ClientEncryption.createDataKey(), ClientEncryption.encrypt(), and
ClientEncryption.decrypt(). See the `libmongocrypt API documentation <https://github.com/mongodb/libmongocrypt/blob/master/src/mongocrypt.h.in>`_ for more information.

The ClientEncryption contains a MongoClient connected to the MongoDB
cluster containing the key vault collection. It does not contain a
MongoClient to mongocryptd.

Note, aside from createDataKey(), there is no new API for querying,
updating, or removing data keys. Much of this can be done with existing
CRUD operations.

Key Vault collection
====================
The key vault collection is the specially designated collection
containing encrypted data keys. There is no default collection (user
must specify). The key vault collection is used for automatic and
explicit encryption/decryption as well as
ClientEncryption.createDataKey().

For ClientEncryption.createDataKey(), the new document MUST be inserted
into the key vault collection with write concern majority.

For encrytion/decryption that requires keys from the key vault
collection, the find operation MUST be done with read concern majority.

Auto encrypt and decrypt
========================
An encrypted MongoClient automatically encrypts values for filtering and
decrypts results.

The driver MUST use libmongocrypt to initiate auto encryption and decryption.
Create the BSON command meant to be sent over the wire, then pass that through
the libmongocrypt state machine and use the returned BSON command in its place.
The state machine is created with the libmongocrypt function
``mongocrypt_ctx_new`` and initialized with a ``mongocrypt_ctx_encrypt_init`` or
``mongocrypt_ctx_decrypt_init``. See the `libmongocrypt API documentation
<https://github.com/mongodb/libmongocrypt/blob/master/src/mongocrypt.h.in>`_ for
more information. 

An encrypted MongoClient configured with bypassAutoEncryption MUST NOT
attempt automatic encryption for any command.

Otherwise, an encrypted MongoClient MUST attempt to auto encrypt all
commands. Note, the underlying implementation may determine no
encryption is necessary, or bypass many checks if the command is deemed
to not possibly contain any encrypted data (e.g. ping). See the appendix
section: `libmongocrypt: Auto Encryption Whitelist`_.

An encrypted MongoClient MUST attempt to auto decrypt the results of all
commands.

Drivers MUST raise an error when attempting to auto encrypt a command if
the maxWireVersion is less than 8. The error message MUST contain
"Auto-encryption requires a minimum MongoDB version of 4.2".

Note, all client side features (including all of ``ClientEncryption``)
are only supported against 4.2 or higher servers. However, errors are
only raised for automatic encryption/decryption against older servers.
See `Why is a 4.2 server required?`_.

Interaction with Command Monitoring
===================================
Unencrypted data MUST NOT appear in the data of any command monitoring
events. Encryption MUST occur before generating a CommandStartedEvent,
and decryption MUST occur after generating a CommandSucceededEvent.

Size limits for Write Commands
==============================
Automatic encryption requires the driver to serialize write commands as
a single BSON document before automatically encrypting with libmongocrypt
(analogous to constructing `OP_MSG payload type 0 <https://github.com/mongodb/specifications/blob/70628e30c96361346f7b6872571c0ec4d54846cb/source/message/OP_MSG.rst#sections>`_, not a document sequence).
Automatic encryption returns a single (possibly modified) BSON document as the
command to send.

Because automatic encryption increases the size of commands, the driver
MUST split bulk writes at a reduced size limit before undergoing automatic
encryption. The write payload MUST be split at 2MiB (2097152). Where batch
splitting occurs relative to automatic encryption is implementation-dependent.

Drivers MUST not reduce the size limits for a single write before automatic
encryption. I.e. if a single document has size larger than 2MiB (but less than
`maxBsonObjectSize`) proceed with automatic encryption.

Drivers MUST document the performance limitation of enabling client side
encryption by including the following documentation in MongoClient:

   Enabling Client Side Encryption reduces the maximum write batch size
   and may have a negative performance impact.

Appendix
========

Appendix terms
--------------

intent-to-encrypt marking
   One of the data formats of BSON binary
   subtype 6, representing an encoded BSON document containing plaintext
   and metadata.

Key vault collection schema for data keys
-----------------------------------------
Data keys are stored in the MongoDB key vault collection with the following schema:

============ ================ ==========================================================================================================
**Name**     **Type**         **Description**
\_id         UUID             A unique identifier for the key.
version      Int64            A numeric identifier for the schema version of this document. Implicitly 0 if unset.
keyAltNames  Array of strings Alternate names to search for keys by. Used for a per-document key scenario in support of GDPR scenarios.
keyMaterial  BinData          Encrypted data key material, BinData type General
creationDate Date             The datetime the wrapped key was imported into the Key Database.
updateDate   Date             The datetime the wrapped key was last modified. On initial import, this value will be set to creationDate.
status       Int              0 = enabled, 1 = disabled
masterKey    Document         Per provider master key definition, see below
============ ================ ==========================================================================================================

masterKey contents
^^^^^^^^^^^^^^^^^^

======== ======== ========================================================================
**Name** **Type** **Description**
provider "aws"
key      String   AWS ARN. Only applicable for "aws" provider.
region   String   AWS Region that contains AWS ARN. Only applicable for "aws" provider.
endpoint String   Alternate AWS endpoint (needed for FIPS endpoints)
======== ======== ========================================================================

================= ======== ===============================================================
**Name**          **Type** **Description**
provider          "azure"
keyVaultEndpoint  String   Required key vault endpoint. (e.g. "example.vault.azure.net")
keyName           String   Required key name.
keyVersion        String   Optional key version.
================= ======== ===============================================================

========== ======== ======================================================================
**Name**   **Type** **Description**
provider   "gcp"
projectId  String   Required project ID.
location   String   Required location name (e.g. "global")
keyRing    String   Required key ring name.
keyName    String   Required key name.
keyVersion String   Optional key version.
endpoint   String   Optional, KMS URL, defaults to https://cloudkms.googleapis.com
========== ======== ======================================================================

======== ======== ========================================================================
**Name** **Type** **Description**
provider "local"
======== ======== ========================================================================

Data keys are needed for encryption and decryption. They are identified
in the intent-to-encrypt marking and ciphertext. Data keys may be
retrieved by querying the "_id" with a UUID or by querying the
"keyAltName" with a string.

Note, "status" is unused and is purely informational.

Example data key document
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code::

   {
      "_id" : UUID("00000000-0000-0000-0000-000000000000"),
      "status" : 1,
      "masterKey" : {
         "provider" : "aws",
         "key" : "arn:aws...",
         "region" : "us-east-1"
      },
      "updateDate" : ISODate("2019-03-18T22:53:50.483Z"),
      "keyMaterial" : BinData(0,"AQICAH..."),
      "creationDate" : ISODate("2019-03-18T22:53:50.483Z"),
      "keyAltNames" : [
         "altname",
         "another_altname"
      ]
   }

BSON binary subtype 6
---------------------

BSON Binary Subtype 6 has a one byte leading identifier. The following
is a quick reference.

.. code:: typescript

   struct {
      uint8 subtype;
      [more data - see individual type definitions]
   }

Type 0: Intent-to-encrypt marking
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: typescript

   struct {
      uint8 subtype = 0;
      [ bson ];
   }

Types 1 and 2: Ciphertext
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: typescript

   struct {
      uint8 subtype = (1 or 2);
      uint8 key_uuid[16];
      uint8 original_bson_type;
      uint32 ciphertext_length;
      uint8 ciphertext[ciphertext_length];
   }

See `Driver Spec: BSON Binary Subtype 6 <https://github.com/mongodb/specifications/tree/master/source/client-side-encryption/subtype6.rst>`_ for more information.

JSONSchema "encrypt"
--------------------

The additional support for encryption in JSONSchema will be documented
in the MongoDB manual. But the following is an example:

.. code:: typescript

   encrypt : {
      bsonType: "int"
      algorithm: "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
      keyId: [UUID(...)]
   }

Each field is briefly described as follows:

========= ======================= ===============================================================================================
**Name**  **Type**                **Description**
bsonType  string                  The bsonType of the underlying encrypted field.
algorithm string                  "AEAD_AES_256_CBC_HMAC_SHA_512-Random" or "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
keyId     string or array of UUID If string, it is a JSON pointer to a field with a scalar value identifying a key by keyAltName.

                                  If array, an array of eligible keys.
========= ======================= ===============================================================================================

libmongocrypt: Prohibitions and warnings
----------------------------------------

libmongocrypt MUST validate options. The following noteworthy cases are
prohibited:

-  Explicit encryption using the deterministic algorithm on any of the
   following types:

   -  array

   -  document

   -  code with scope

   -  single value types: undefined, MinKey, MaxKey, Null

   -  decimal128

   -  double

   -  bool

-  Explicit encryption on a BSON binary subtype 6.

The following cases MUST warn:

-  A local schema that does not include encrypted fields.

libmongocrypt: Collection info caching
--------------------------------------

libmongocrypt will cache the collection infos so encryption with remote
schemas need not run listCollections every time. Collection infos (or
lack thereof) are cached for one minute. This is not configurable. After
expiration, subsequent attempts to encrypt will result in libmongocrypt
requesting a new collection info.

A collection info result indicates if the collection is really a view.
If it is, libmongocrypt returns an error since it does not know the
schema of the underlying collection.

A collection info with validators that aside from one top level
$jsonSchema are considered an error.

libmongocrypt: Data key caching
-------------------------------

Data keys are cached in libmongocrypt for one minute. This is not
configurable, and there is no maximum number of keys in the cache. The
data key material is stored securely. It will not be paged to disk and
the memory will be properly zero'ed out after freeing.

libmongocrypt: Crypto implementation
------------------------------------

libmongocrypt uses AEAD_SHA256_CBC_HMAC512 for both "randomized" and
"deterministic" encryption algorithms. It is described in this `IETF document draft <https://tools.ietf.org/html/draft-mcgrew-aead-aes-cbc-hmac-sha2-05>`__.
For "randomized", libmongocrypt securely creates a random IV. For
"deterministic", libmongocrypt securely creates a random IV key and any
given encryption operation will derive the IV from the IV key and the
field plaintext data.

libmongocrypt: Auto Encryption Whitelist
----------------------------------------

libmongocrypt determines whether or not the command requires encryption
(i.e. is sent to mongocryptd) based on the table below. Commands not
listed in this table will result in an error returned by libmongocrypt.

======================== ===========
**Command**              **Action**
aggregate (collection)   AUTOENCRYPT
count                    AUTOENCRYPT
distinct                 AUTOENCRYPT
delete                   AUTOENCRYPT
find                     AUTOENCRYPT
findAndModify            AUTOENCRYPT
getMore                  BYPASS
insert                   AUTOENCRYPT
update                   AUTOENCRYPT
authenticate             BYPASS
getnonce                 BYPASS
logout                   BYPASS
isMaster                 BYPASS
abortTransaction         BYPASS
commitTransaction        BYPASS
endSessions              BYPASS
startSession             BYPASS
create                   BYPASS
createIndexes            BYPASS
drop                     BYPASS
dropDatabase             BYPASS
dropIndexes              BYPASS
killCursors              BYPASS
listCollections          BYPASS
listDatabases            BYPASS
listIndexes              BYPASS
renameCollection         BYPASS
explain                  AUTOENCRYPT
ping                     BYPASS
killAllSessions          BYPASS
killSessions             BYPASS
killAllSessionsByPattern BYPASS
refreshSessions          BYPASS
======================== ===========

All AUTOENCRYPT commands are sent to mongocryptd, even if there is no
JSONSchema. This is to ensure that commands that reference other
collections (e.g. aggregate with $lookup) are handled properly.

Test Plan
=========
See the `README.rst <https://github.com/mongodb/specifications/blob/5ea8e02dfc7096c0ad78c3fadded8e66470a4c19/source/client-side-encryption/tests/README.rst>`_ in the test directory.

Rationale
=========

Design Principles
-----------------
In addition to the `Driver
Mantras <https://github.com/mongodb/specifications#driver-mantras>`__
there are design principles specific to this project.

1. Make encryption easy to enable
---------------------------------
Users should be able to enable encryption with minimal application
change.

2. Minimize risk of exposing sensitive data
-------------------------------------------
Storing or querying with unencrypted data can have dire consequences,
because users may not be made aware immediately. When in doubt, we
should error. It should be clear to the user when an operation gets
encrypted and when one doesn't.

3. Minimize API
---------------
The first version of Client Side Encryption is to get signal. If it
becomes popular, further improvements will be made (removing mongocryptd
process, support for more queries, better performance). But the public
API we provide now will stick around for the long-term. So let's keep it
minimal to accomplish our goals.

How did we arrive at this API?
------------------------------
The API for client side encryption underwent multiple iterations during
the design process.

Why is client side encryption configured on a MongoClient?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There is state that must be shared among all auto encrypted collections:
the MongoClient to mongocryptd and the handle to libmongocrypt (because
key caching + JSONSchema caching occurs in libmongocrypt).

Why not make auto encryption "opt-in"?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Because auto encryption is specified with a collection JSONSchema, we
cannot auto encrypt database or client operations. So we cannot know if
the user is passing sensitive data as a filter to a database/client
change stream or a currentOp command for example. We also must always
fail on view operations. We considered making auto encryption opt-in for
collections. But we decided against this. It is much simpler for users
to enable auto encryption without enumerating all collections with
encryption in the common case of using remote JSONSchemas.

Note, this takes the trade-off of a better user experience over less
safety. If a user mistakenly assumes that auto encryption occurs on a
database, or on a collection doing a $(graph)lookup on a collection with
auto encryption, they may end up sending unencrypted data.

Why are auto encrypted collections configured at level of MongoClient?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a previous iteration of the design, we proposed enabling auto
encryption only in db.getCollection() for better usability. But this
better aligns with our design principles.

-  Safer. Users won't forget to enable auto encryption on one call to
   db.getCollection()
-  Easier. It only requires changing MongoClient code instead of every
   db.getCollection()

Why do we have a separate top level type for ClientEncryption?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The encrypt/decrypt and createDataKey functions were originally placed
on MongoClient. But, then we'd have API that depends on optional
configuration. A new top level type seemed warranted.

Why not pass the ClientEncryption into db.getCollection() to enable auto encryption?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As it is now, a ClientEncryption and a MongoClient cannot share state
(libmongocrypt handle or MongoClient to mongocryptd). Foreseeably, they
could share state if auto encryption was enabled by passing a ClientEncryption
object like:

db.getCollection ("coll", { autoEncrypt: { clientEncryption:
clientEncryption } })

But this would require a MongoCollection to peek into the internals of a
ClientEncryption object. This is messy and language dependent to
implement and makes mocking out the ClientEncryption difficult for tests.

Why do we need to pass a client to create a ClientEncryption?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We need to support an external key vault collection (i.e. on another MongoDB
cluster).

Why are extraOptions and kmsProviders maps?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Because we don't want AWS as part of the public types and we don't want
to put mongocryptd options as types since mongocryptd is an
implementation detail we'd like to hide as much as possible.

Why is there a bypassAutoEncryption?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

bypassAutoEncryption still supports auto decryption. In cases where
mongocryptd cannot analyze a query, it's still useful to provide auto
decryption. Just like static program analysis cannot always prove that a
runtime invariant holds, mongocryptd cannot always prove that a query
will be safe with respect to encryption at runtime.

Why not require compatibility between mongocryptd and the server?
-----------------------------------------------------------------

It isn't necessary or unsafe if mongocryptd parses an old version of
MQL. Consider what happens when we add a new operator, $newOperator. If
it properly encrypts a value in the $newOperator expression and sends it
to an old server that doesn't have $newOperator, that's a mistake but
not a security hole. Also if the app passes a query with $newOperator to
mongocryptd, and mongocryptd doesn't know about $newOperator, then it
will error, "Unrecognized operator $newOperator" or something. Also a
mistake, not a security hole.

So long as mongocryptd errors on unrecognized expressions, we don't need
version compatibility between the mongocryptd and server for the sake of
security.

Why cache keys?
---------------

We can't re-fetch the key on each operation, the performance goal for
this project requires us to cache. We do need a revocation mechanism,
based upon periodic checking from the client. Initially this window will
not be configurable. See future work: `Make the key caching window configurable`__.

Why require including a C library?
----------------------------------

-  libmongocrypt deduplicates a lot of the work: JSONSchema cache, KMS
   message construction/parsing, key caching, and encryption/decryption.
-  We are convinced that the next version of field-level encryption will
   remove mongocryptd in place of a C library to do query parsing. That
   will necessitate drivers using a C library. If we use libmongocrypt
   now, that upgrade path is much easier.
-  Our "best-effort" of storing decrypted key material securely is best
   accomplished with a C library.
-  Having crypto done in one centralized C library makes it much easier
   to audit the crypto code.

Why warn if a local schema does not have encrypted fields?
----------------------------------------------------------

Because that is the only use of local schemas. No other JSONSchema
validators have any function. It's likely the user misconfigured
encryption.

Why limit to one top-level $jsonSchema?
---------------------------------------

-  If we allow siblings, we can run into cases where the user specifies
   a top-level $and/$or or any arbitrary match-expression that could
   have nested $jsonSchema's.
-  Furthermore, the initial version of mongocryptd is only implementing
   query analysis when the validator consists of a single $jsonSchema
   predicate. This helps to simplify the mongocryptd logic, and unifies
   it with the case where users configure their schemas directly in the
   driver.

Why not allow schemas to be configured at runtime?
--------------------------------------------------

We could have something like Collection::setEncryptionSchema(), but
users can simply recreate the client to set new local schemas.

Why not support other AWS auth mechanisms?
------------------------------------------

We could potentially authenticate against AWS in a more sophisticated
way, like read credentials from ~/.aws/credentials or assuming a role
with EC2 instance metadata. But we've decided to implement the simplest
authentication mechanism for v1, and defer more sophisticated ones as
future work.

Why not pass a URI for external key vault collections instead of a MongoClient?
-------------------------------------------------------------------------------

Some configuration on a MongoClient can only be done programmatically.
E.g. in Java TLS configuration can only be done at runtime since it is
abstracted in an SSLContext which cannot be accessed or altered by the
driver.

What happened to multiple key vault collections?
------------------------------------------------

An earlier revision of this specification supported multiple active key
vaults with the notion of a "key vault collection alias". The key vault
collection alias identified one of possibly many key vault collections
that stored the key to decrypt the ciphertext. However, enforcing one
key vault collection is a reasonable restriction for users. There isn't
clear value in having multiple key vault collections. And having active
multiple key vault collections is not necessary to migrate key vault
collections.

Why auto encrypt a command instead of a wire protocol message?
--------------------------------------------------------------

-  It is significantly easier to implement communication in drivers if
   libmongocrypt gives back BSON object that can be passed to run
   command.
-  mongocryptd cannot return document sequences, so it will return an
   array of documents anyway.
-  Though it is foreseeable that a driver can take the final result of
   encryption and turn it into an OP_MSG document sequence, it does not
   seem worthwhile to impose extra complexity in this case.

Why is a failure to decrypt always an error?
--------------------------------------------

In the original design we proposed *not* to error if decryption failed
due to a missing key. But, it's not clear this is a needed
functionality, it goes against our principle of "Minimize API", and
there's a simple recourse for users: bypass mongocryptd and explicitly
decrypt instead.

Why are there no APM events for mongocryptd?
--------------------------------------------

Though it may be helpful for debugging to expose APM events for
mongocryptd, mongocryptd is an implementation detail we'd like to have
the freedom to remove in the future. So we want to expose mongocryptd as
little as possible.

Why aren't we creating a unique index in the key vault collection?
------------------------------------------------------------------

There should be a unique index on keyAltNames. Although GridFS
automatically creates indexes as a convenience upon first write, it has
been problematic before. It requires the createIndex privilege, which a
user might not have if they are just querying the key vault collection
with find and adding keys with insert.

Why do operations on views fail?
--------------------------------

Currently, the driver does not resolve the entire view pipeline, which
would be necessary to know the schema of the underlying collection. But,
the driver does know whether or not a namespace is a view based on the
response to listCollections. And the driver will run listCollections on
all namespaces omitted from the schemaMap.

Why is a 4.2 server required?
-----------------------------

Limiting to 4.2 reduces testing complexity. Additionally The ``encrypt``
subdocument in JSON schema is only supported on 4.2 or higher servers.
Although not technically necessary for client side encryption, it does
provide a fallback against accidentally sending unencrypted data from
misconfigured clients.

Why are serverSelectionTryOnce and cooldownMS disabled for single-threaded drivers connecting to mongocryptd?
-------------------------------------------------------------------------------------------------------------

By default, single threaded clients set serverSelectionTryOnce to true, which
means server selection fails if a topology scan fails the first time (i.e. it
will not make repeat attempts until serverSelectionTimeoutMS expires). This
behavior is overriden since there may be a small delay between spawning
mongocryptd (which the driver may be responsible for) and for mongocryptd to
listen on sockets. See the Server Selection spec description of `serverSelectionTryOnce <../server-selection/server-selection.rst#serverselectiontryonce>`_.

Similarly, single threaded clients will by default wait for 5 second cooldown
period after failing to connect to a server before making another attempt.
Meaning if the first attempt to mongocryptd fails to connect, then the user
would observe a 5 second delay. This is not configurable in the URI, so this
must be overriden internally. Since mongocryptd is a local process, there should
only be a very short delay after spawning mongocryptd for it to start listening
on sockets. See the SDAM spec description of `cooldownMS <../source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#cooldownms>`_.

Because single threaded drivers may exceed ``serverSelectionTimeoutMS`` by the
duration of the topology scan, ``connectTimeoutMS`` is also reduced.

What's the deal with metadataClient, keyVaultClient, and the internal client?
-----------------------------------------------------------------------------

When automatically encrypting a command, the driver runs:
- a ``listCollections`` command to determine if the target collection
has a remote schema. This uses the ``metadataClient``.
- a ``find`` against the key vault collection to fetch keys. This uses the
``keyVaultClient``.

Why not reuse the parent MongoClient?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These operations MUST NOT reuse the same connection pool as the parent
``MongoClient`` configured with automatic encryption to avoid possible deadlock
situations.

Drivers supporting a connection pool (see `CMAP specification
</source/connection-monitoring-and-pooling/connection-monitoring-and-pooling.rst>`_)
support an option for limiting the connection pool size: ``maxPoolSize``.

Drivers need to check out a connection before serializing the command. If the
``listCollections`` or ``find`` command during automatic encryption uses the same
connection pool as the parent MongoClient, the application is susceptible to
deadlocks.

Using the same connection pool causes automatic encryption to check out multiple
connections from the pool when processing a single command. If maxPoolSize=1,
this is an immediate deadlock. If maxPoolSize=2, and two threads check out the
first connection, they will deadlock attempting to check out the second.

Why are keyVaultClient and metadataClient separate exposed options?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``keyVaultClient`` supports the use case where the key vault collection is
stored on a MongoDB cluster separate from the data-bearing cluster.

The ``metadataClient`` is only used for ``listCollections`` against the
data-bearing cluster.

``listCollections`` responses are cached by libmongocrypt for one minute.

The use pattern of the ``metadataClient`` will likely greatly differ from
the parent ``MongoClient``.

This is an exposed option to provide a way for users to configure (e.g. set a
lower ``minPoolSize`` to avoid additional connections).

Why is the metadataClient not needed if bypassAutoEncryption=true
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Because automatic decryption does not require the JSON schema.
``listCollections`` is not run during automatic encryption.

Can the keyVaultClient and the metadataClient be set to the same MongoClient?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Technically yes, but not all drivers support this. In some drivers, the
``keyVaultClient`` and ``metadataClient`` is configured by passing client
options, instead of a client object.

Can the metadataClient serve as the internal client when no keyVaultClient is set?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

No, it was decided against since it adds complexity to the API without a clear
benefit.

The ``metadataClient`` and ``keyVaultClient`` currently serve separate distinct
purposes from the user's perspective.

The ``keyVaultClient`` fetches keys from the key vault collection.
The ``metadataClient`` runs ``listCollections`` to check for remote schemas.

The behavior is that if a ``metadataClient`` is set, but a ``keyVaultClient``
is not set, an internal client will be created to serve as the ``keyVaultClient``.

Future work
===========

Make libmonogocrypt cache window configurable
---------------------------------------------
There's a principle at MongoDB, "no knobs", that we should honor
wherever possible. Configurability is bad, mandating one well-chosen
value is good. But if our default caching behavior is discovered
unsuitable for some use cases we may add configuration as part of future
work.

APM events for encryption or key service interaction
----------------------------------------------------
APM events include the encrypted data before it is sent to the server,
or before it is decrypted in a reply. Therefore, app developers can
determine whether or not encryption occurred by inspecting the values in
their command monitoring events. However, it might be useful to offer
separate "encryption" and "decryption" events, as well as interactions
with the key service.

Remove mongocryptd
------------------
A future version plans to remove the mongocryptd process and fold the
logic into libmongocrypt. Therefore, this spec mandates that drivers use
libmongocrypt to abstract encryption logic, deduplicate work, and to
provide a simpler future path to removing mongocryptd.

Support external key vault collection discovery
-----------------------------------------------
The only way to configure an external key vault collection is by passing a
MongoClient.

For apps like Compass, where it may not be possible for users to
configure this app side, there should ideally be enough information in
the database to decrypt data. (Excluding KMS credentials, which are
still passed as MongoClient options).

We may want to store a URI to the external key vault collection somewhere
in the data bearing cluster, so clients can connect to the external key vault
collection without additional user supplied configuration.

Batch listCollections requests on expired schema cache entries
--------------------------------------------------------------

Currently libmongocrypt will refresh schemas one at a time.

Add a maximum size for the JSONSchema/key cache.
------------------------------------------------

They're unbounded currently.

Recalculate message size bounds dynamically
-------------------------------------------

Instead of using one reduced maxMessageSizeBytes, libmongocrypt could
hide the complexity of properly resplitting bulk writes after
encryption. It could use a simple back-off algorithm: try marking a
command with maxMessageSizeBytes=24MB. If after marking we determine
that's too large, try again with maxMessageSizeBytes=12MB and so on. And
in the end libmongocrypt would create multiple OP_MSGs to send.

Changelog
=========

+------------+------------------------------------------------------------+
| 2020-12-12 | Add metadataClient option and internal client              |
| 2020-10-19 | Add 'azure' and 'gcp' KMS providers                        |
| 2019-10-11 | Add 'endpoint' to AWS masterkey                            |
| 2019-12-17 | Clarified bypassAutoEncryption and managing mongocryptd    |
+------------+------------------------------------------------------------+
