# Client Side Encryption Tests

______________________________________________________________________

## Introduction

This document describes the format of the driver spec tests included in the JSON and YAML files included in the `legacy`
sub-directory. Tests in the `unified` directory are written using the
[Unified Test Format](../../unified-test-format/unified-test-format.md).

The `timeoutMS.yml`/`timeoutMS.json` files in this directory contain tests for the `timeoutMS` option and its
application to the client-side encryption feature. Drivers MUST only run these tests after implementing the
[Client Side Operations Timeout](../../client-side-operations-timeout/client-side-operations-timeout.md) specification.

Additional prose tests, that are not represented in the spec tests, are described and MUST be implemented by all
drivers.

Running spec and prose tests require that the driver and server both support Client-Side Field Level Encryption. CSFLE
is supported when all of the following are true:

- Server version is 4.2.0 or higher. Legacy spec test runners can rely on `runOn.minServerVersion` for this check.
- Driver has libmongocrypt enabled
- At least one of [crypt_shared](../client-side-encryption.md#crypt_shared) and/or
    [mongocryptd](../client-side-encryption.md#mongocryptd) is available.

## Spec Test Format

The spec tests format is an extension of the
[transactions spec legacy test format](../../transactions/tests/legacy-test-format.md) with some additions:

- A `json_schema` to set on the collection used for operations.
- An `encrypted_fields` to set on the collection used for operations.
- A `key_vault_data` of data that should be inserted in the key vault collection before each test.
- Introduction `autoEncryptOpts` to `clientOptions`
- Addition of `$db`to command in`command_started_event`
- Addition of `$$type` to `command_started_event` and outcome.

The semantics of `$$type` is that any actual value matching one of the types indicated by either a BSON type string or
an array of BSON type strings is considered a match.

For example, the following matches a command_started_event for an insert of a document where `random` must be of type
`binData`:

```text
- command_started_event:
    command:
      insert: *collection_name
      documents:
        - { random: { $$type: "binData" } }
      ordered: true
    command_name: insert
```

The following matches a command_started_event for an insert of a document where `random` must be of type `binData` or
`string`:

```text
- command_started_event:
    command:
      insert: *collection_name
      documents:
        - { random: { $$type: ["binData", "string"] } }
      ordered: true
    command_name: insert
```

The values of `$$type` correspond to
[these documented string representations of BSON types](https://www.mongodb.com/docs/manual/reference/bson-types/).

Each YAML file has the following keys:

- `runOn` Unchanged from Transactions spec tests.
- `database_name` Unchanged from Transactions spec tests.
- `collection_name` Unchanged from Transactions spec tests.
- `data` Unchanged from Transactions spec tests.
- `json_schema` A JSON Schema that should be set on the collection (using `createCollection`) before each test run.
- `encrypted_fields` An encryptedFields option that should be set on the collection (using `createCollection`) before
    each test run.
- `key_vault_data` The data that should exist in the key vault collection under test before each test run.
- `tests`: An array of tests that are to be run independently of each other. Each test will have some or all of the
    following fields:
    - `description`: Unchanged from Transactions spec tests.
    - `skipReason`: Unchanged from Transactions spec tests.
    - `useMultipleMongoses`: Unchanged from Transactions spec tests.
    - `failPoint`: Unchanged from Transactions spec tests.
    - `clientOptions`: Optional, parameters to pass to MongoClient().
        - `autoEncryptOpts`: Optional
            - `kmsProviders` A dictionary of KMS providers to set on the key vault ("aws" or "local")
                - `aws` The AWS KMS provider. An empty object. Drivers MUST fill in AWS credentials (`accessKeyId`,
                    `secretAccessKey`) from the environment.
                - `azure` The Azure KMS provider credentials. An empty object. Drivers MUST fill in Azure credentials
                    (`tenantId`, `clientId`, and `clientSecret`) from the environment.
                - `gcp` The GCP KMS provider credentials. An empty object. Drivers MUST fill in GCP credentials (`email`,
                    `privateKey`) from the environment.
                - `local` or `local:name2` The local KMS provider.
                    - `key` A 96 byte local key.
                - `kmip` The KMIP KMS provider credentials. An empty object. Drivers MUST fill in KMIP credentials (`endpoint`,
                    and TLS options).
            - `schemaMap`: Optional, a map from namespaces to local JSON schemas.
            - `keyVaultNamespace`: Optional, a namespace to the key vault collection. Defaults to "keyvault.datakeys".
            - `bypassAutoEncryption`: Optional, a boolean to indicate whether or not auto encryption should be bypassed.
                Defaults to `false`.
            - `encryptedFieldsMap` An optional document. The document maps collection namespace to `EncryptedFields`
                documents.
    - `operations`: Array of documents, each describing an operation to be executed. Each document has the following
        fields:
        - `name`: Unchanged from Transactions spec tests.
        - `object`: Unchanged from Transactions spec tests.. Defaults to "collection" if omitted.
        - `collectionOptions`: Unchanged from Transactions spec tests.
        - `command_name`: Unchanged from Transactions spec tests.
        - `arguments`: Unchanged from Transactions spec tests.
        - `result`: Same as the Transactions spec test format with one addition: if the operation is expected to return an
            error, the `result` document may contain an `isTimeoutError` boolean field. If `true`, the test runner MUST
            assert that the error represents a timeout due to the use of the `timeoutMS` option. If `false`, the test runner
            MUST assert that the error does not represent a timeout.
    - `expectations`: Unchanged from Transactions spec tests.
    - `outcome`: Unchanged from Transactions spec tests.

## Credentials

Test credentials are available in AWS Secrets Manager. See
<https://wiki.corp.mongodb.com/display/DRIVERS/Using+AWS+Secrets+Manager+to+Store+Testing+Secrets> for more background
on how the secrets are managed.

Test credentials to KMS are located in "drivers/csfle".

Test credentials to create environments are available in "drivers/gcpkms" and "drivers/azurekms".

## Use as integration tests

Do the following before running spec tests:

- If available for the platform under test, obtain a [crypt_shared](../client-side-encryption.md#crypt_shared) binary
    and place it in a location accessible to the tests. Refer to:
    [Using crypt_shared](../client-side-encryption.md#enabling-crypt_shared)
- Start the mongocryptd process.
- Start a mongod process with **server version 4.2.0 or later**.
- Place credentials somewhere in the environment outside of tracked code. (If testing on evergreen, project variables
    are a good place).
- Start a KMIP test server on port 5698 by running
    [drivers-evergreen-tools/.evergreen/csfle/kms_kmip_server.py](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/csfle/kms_kmip_server.py).

Load each YAML (or JSON) file using a Canonical Extended JSON parser.

If the test file name matches the regular expression `fle2-Range-.*-Correctness`, drivers MAY skip the test on macOS.
The `fle2-Range` tests are very slow on macOS and do not provide significant additional test coverage.

Then for each element in `tests`:

1. If the `skipReason` field is present, skip this test completely.

2. If the `key_vault_data` field is present:

    1. Drop the `keyvault.datakeys` collection using writeConcern "majority".
    2. Insert the data specified into the `keyvault.datakeys` with write concern "majority".

3. Create a MongoClient.

4. Create a collection object from the MongoClient, using the `database_name` and `collection_name` fields from the YAML
    file. Drop the collection with writeConcern "majority". If a `json_schema` is defined in the test, use the
    `createCollection` command to explicitly create the collection:

    ```typescript
    {"create": <collection>, "validator": {"$jsonSchema": <json_schema>}}
    ```

    If `encrypted_fields` is defined in the test, the required collections and index described in
    [Create and Drop Collection Helpers](../client-side-encryption.md#queryable-encryption-create-and-drop-collection-helpers)
    must be created:

    - Use the `dropCollection` helper with `encrypted_fields` as an option and writeConcern "majority".
    - Use the `createCollection` helper with `encrypted_fields` as an option.

5. If the YAML file contains a `data` array, insert the documents in `data` into the test collection, using writeConcern
    "majority".

6. Create a **new** MongoClient using `clientOptions`.

    1. If `autoEncryptOpts` includes `aws`, `awsTemporary`, `awsTemporaryNoSessionToken`, `azure`, `gcp`, and/or `kmip`
        as a KMS provider, pass in credentials from the environment.
        - `awsTemporary`, and `awsTemporaryNoSessionToken` require temporary AWS credentials. These can be retrieved using
            the csfle
            [set-temp-creds.sh](https://github.com/mongodb-labs/drivers-evergreen-tools/tree/master/.evergreen/csfle)
            script.

        - `aws`, `awsTemporary`, and `awsTemporaryNoSessionToken` are mutually exclusive.

            `aws` should be substituted with:

            ```javascript
            "aws": {
                 "accessKeyId": <set from environment>,
                 "secretAccessKey": <set from environment>
            }
            ```

            `awsTemporary` should be substituted with:

            ```javascript
            "aws": {
                 "accessKeyId": <set from environment>,
                 "secretAccessKey": <set from environment>
                 "sessionToken": <set from environment>
            }
            ```

            `awsTemporaryNoSessionToken` should be substituted with:

            ```javascript
            "aws": {
                "accessKeyId": <set from environment>,
                "secretAccessKey": <set from environment>
            }
            ```

            `gcp` should be substituted with:

            ```javascript
            "gcp": {
                "email": <set from environment>,
                "privateKey": <set from environment>,
            }
            ```

            `azure` should be substituted with:

            ```javascript
            "azure": {
                "tenantId": <set from environment>,
                "clientId": <set from environment>,
                "clientSecret": <set from environment>,
            }
            ```

            `local` should be substituted with:

            ```javascript
            "local": { "key": <base64 decoding of LOCAL_MASTERKEY> }
            ```

            `kmip` should be substituted with:

            ```javascript
            "kmip": { "endpoint": "localhost:5698" }
            ```

            Configure KMIP TLS connections to use the following options:

            - `tlsCAFile` (or equivalent) set to
                [drivers-evergreen-tools/.evergreen/x509gen/ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem).
                This MAY be configured system-wide.
            - `tlsCertificateKeyFile` (or equivalent) set to
                [drivers-evergreen-tools/.evergreen/x509gen/client.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/client.pem).

            The method of passing TLS options for KMIP TLS connections is driver dependent.
    2. If `autoEncryptOpts` does not include `keyVaultNamespace`, default it to `keyvault.datakeys`.

7. For each element in `operations`:

    - Enter a "try" block or your programming language's closest equivalent.

    - Create a Database object from the MongoClient, using the `database_name` field at the top level of the test file.

    - Create a Collection object from the Database, using the `collection_name` field at the top level of the test file.
        If `collectionOptions` is present create the Collection object with the provided options. Otherwise create the
        object with the default options.

    - Execute the named method on the provided `object`, passing the arguments listed.

    - If the driver throws an exception / returns an error while executing this series of operations, store the error
        message and server error code.

    - If the result document has an "errorContains" field, verify that the method threw an exception or returned an
        error, and that the value of the "errorContains" field matches the error string. "errorContains" is a substring
        (case-insensitive) of the actual error message.

        If the result document has an "errorCodeName" field, verify that the method threw a command failed exception or
        returned an error, and that the value of the "errorCodeName" field matches the "codeName" in the server error
        response.

        If the result document has an "errorLabelsContain" field, verify that the method threw an exception or returned an
        error. Verify that all of the error labels in "errorLabelsContain" are present in the error or exception using
        the `hasErrorLabel` method.

        If the result document has an "errorLabelsOmit" field, verify that the method threw an exception or returned an
        error. Verify that none of the error labels in "errorLabelsOmit" are present in the error or exception using the
        `hasErrorLabel` method.

    - If the operation returns a raw command response, eg from `runCommand`, then compare only the fields present in the
        expected result document. Otherwise, compare the method's return value to `result` using the same logic as the
        CRUD Spec Tests runner.

8. If the test includes a list of command-started events in `expectations`, compare them to the actual command-started
    events using the same logic as the
    [Command Monitoring spec legacy test runner](../../command-logging-and-monitoring/tests/README.md).

9. For each element in `outcome`:

    - If `name` is "collection", create a new MongoClient *without encryption* and verify that the test collection
        contains exactly the documents in the `data` array. Ensure this find reads the latest data by using **primary
        read preference** with **local read concern** even when the MongoClient is configured with another read
        preference or read concern.

The spec test MUST be run with *and* without auth.

## Using `crypt_shared`

On platforms where [crypt_shared](../client-side-encryption.md#crypt_shared) is available, drivers should prefer to test
with the `crypt_shared` library instead of spawning mongocryptd.

[crypt_shared](../client-side-encryption.md#crypt_shared) is released alongside the server.
[crypt_shared](../client-side-encryption.md#crypt_shared) is only available in versions 6.0 and above.

mongocryptd is released alongside the server. mongocryptd is available in versions 4.2 and above.

Drivers MUST run all tests with mongocryptd on at least one platform for all tested server versions.

Drivers MUST run all tests with [crypt_shared](../client-side-encryption.md#crypt_shared) on at least one platform for
all tested server versions. For server versions < 6.0, drivers MUST test with the latest major release of
[crypt_shared](../client-side-encryption.md#crypt_shared). Using the latest major release of
[crypt_shared](../client-side-encryption.md#crypt_shared) is supported with older server versions.

Note that some tests assert on mongocryptd-related behaviors (e.g. the `mongocryptdBypassSpawn` test).

Drivers under test should load the [crypt_shared](../client-side-encryption.md#crypt_shared) library using either the
`cryptSharedLibPath` public API option (as part of the AutoEncryption `extraOptions`), or by setting a special search
path instead.

Some tests will require *not* using [crypt_shared](../client-side-encryption.md#crypt_shared). For such tests, one
should ensure that `crypt_shared` will not be loaded. Refer to the client-side-encryption documentation for information
on "disabling" `crypt_shared` and setting library search paths.

> [!NOTE]
> The [crypt_shared](../client-side-encryption.md#crypt_shared) dynamic library can be obtained using the
> [mongodl](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/mongodl.py) Python script
> from [drivers-evergreen-tools](https://github.com/mongodb-labs/drivers-evergreen-tools/):
>
> ```shell
> $ python3 mongodl.py --component=crypt_shared --version=<VERSION> --out=./crypt_shared/
> ```
>
> Other versions of `crypt_shared` are also available. Please use the `--list` option to see versions.

## Prose Tests

Tests for the ClientEncryption type are not included as part of the YAML tests.

In the prose tests LOCAL_MASTERKEY refers to the following base64:

```text
Mng0NCt4ZHVUYUJCa1kxNkVyNUR1QURhZ2h2UzR2d2RrZzh0cFBwM3R6NmdWMDFBMUN3YkQ5aXRRMkhGRGdQV09wOGVNYUMxT2k3NjZKelhaQmRCZGJkTXVyZG9uSjFk
```

Perform all applicable operations on key vault collections (e.g. inserting an example data key, or running a find
command) with readConcern/writeConcern "majority".

### 1. Custom Key Material Test

1. Create a `MongoClient` object (referred to as `client`).

2. Using `client`, drop the collection `keyvault.datakeys`.

3. Create a `ClientEncryption` object (referred to as `client_encryption`) with `client` set as the `keyVaultClient`.

4. Using `client_encryption`, create a data key with a `local` KMS provider and the following custom key material (given
    as base64):

    ```text
    xPTAjBRG5JiPm+d3fj6XLi2q5DMXUS/f1f+SMAlhhwkhDRL0kr8r9GDLIGTAGlvC+HVjSIgdL+RKwZCvpXSyxTICWSXTUYsWYPyu3IoHbuBZdmw2faM3WhcRIgbMReU5
    ```

5. Find the resulting key document in `keyvault.datakeys`, save a copy of the key document, then remove the key document
    from the collection.

6. Replace the `_id` field in the copied key document with a UUID with base64 value `AAAAAAAAAAAAAAAAAAAAAA==` (16 bytes
    all equal to `0x00`) and insert the modified key document into `keyvault.datakeys` with majority write concern.

7. Using `client_encryption`, encrypt the string `"test"` with the modified data key using the
    `AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic` algorithm and assert the resulting value is equal to the following
    (given as base64):

    ```text
    AQAAAAAAAAAAAAAAAAAAAAACz0ZOLuuhEYi807ZXTdhbqhLaS2/t9wLifJnnNYwiw79d75QYIZ6M/aYC1h9nCzCjZ7pGUpAuNnkUhnIXM3PjrA==
    ```

### 2. Data Key and Double Encryption

First, perform the setup.

1. Create a MongoClient without encryption enabled (referred to as `client`). Enable command monitoring to listen for
    command_started events.

2. Using `client`, drop the collections `keyvault.datakeys` and `db.coll`.

3. Create the following:

    - A MongoClient configured with auto encryption (referred to as `client_encrypted`)
    - A `ClientEncryption` object (referred to as `client_encryption`)

    Configure both objects with the following KMS providers:

    ```javascript
    {
       "aws": {
          "accessKeyId": <set from environment>,
          "secretAccessKey": <set from environment>
       },
       "azure": {
          "tenantId": <set from environment>,
          "clientId": <set from environment>,
          "clientSecret": <set from environment>,
       },
       "gcp": {
          "email": <set from environment>,
          "privateKey": <set from environment>,
       }
       "local": { "key": <base64 decoding of LOCAL_MASTERKEY> },
       "kmip": { "endpoint": "localhost:5698" }
    }
    ```

    Configure KMIP TLS connections to use the following options:

    - `tlsCAFile` (or equivalent) set to
        [drivers-evergreen-tools/.evergreen/x509gen/ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem).
        This MAY be configured system-wide.
    - `tlsCertificateKeyFile` (or equivalent) set to
        [drivers-evergreen-tools/.evergreen/x509gen/client.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/client.pem).

    The method of passing TLS options for KMIP TLS connections is driver dependent.

    Configure both objects with `keyVaultNamespace` set to `keyvault.datakeys`.

    Configure the `MongoClient` with the following `schema_map`:

    ```javascript
    {
      "db.coll": {
        "bsonType": "object",
        "properties": {
          "encrypted_placeholder": {
            "encrypt": {
              "keyId": "/placeholder",
              "bsonType": "string",
              "algorithm": "AEAD_AES_256_CBC_HMAC_SHA_512-Random"
            }
          }
        }
      }
    }
    ```

    Configure `client_encryption` with the `keyVaultClient` of the previously created `client`.

For each KMS provider (`aws`, `azure`, `gcp`, `local`, and `kmip`), referred to as `provider_name`, run the following
test.

1. Call `client_encryption.createDataKey()`.
    - Set keyAltNames to `["<provider_name>_altname"]`.

    - Set the masterKey document based on `provider_name`.

        For "aws":

        ```javascript
        {
          region: "us-east-1",
          key: "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0"
        }
        ```

        For "azure":

        ```javascript
        {
          "keyVaultEndpoint": "key-vault-csfle.vault.azure.net",
          "keyName": "key-name-csfle"
        }
        ```

        For "gcp":

        ```javascript
        {
          "projectId": "devprod-drivers",
          "location": "global",
          "keyRing": "key-ring-csfle",
          "keyName": "key-name-csfle"
        }
        ```

        For "kmip":

        ```javascript
        {}
        ```

        For "local", do not set a masterKey document.

    - Expect a BSON binary with subtype 4 to be returned, referred to as `datakey_id`.

    - Use `client` to run a `find` on `keyvault.datakeys` by querying with the `_id` set to the `datakey_id`.

    - Expect that exactly one document is returned with the "masterKey.provider" equal to `provider_name`.

    - Check that `client` captured a command_started event for the `insert` command containing a majority writeConcern.
2. Call `client_encryption.encrypt()` with the value `"hello <provider_name>"`, the algorithm
    `AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic`, and the `key_id` of `datakey_id`.
    - Expect the return value to be a BSON binary subtype 6, referred to as `encrypted`.
    - Use `client_encrypted` to insert `{ _id: "<provider_name>", "value": <encrypted> }` into `db.coll`.
    - Use `client_encrypted` to run a find querying with `_id` of `"<provider_name>"` and expect `value` to be
        `"hello <provider_name>"`.
3. Call `client_encryption.encrypt()` with the value `"hello <provider_name>"`, the algorithm
    `AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic`, and the `key_alt_name` of `<provider_name>_altname`.
    - Expect the return value to be a BSON binary subtype 6. Expect the value to exactly match the value of `encrypted`.
4. Test explicit encrypting an auto encrypted field.
    - Use `client_encrypted` to attempt to insert `{ "encrypted_placeholder": <encrypted> }`
    - Expect an exception to be thrown, since this is an attempt to auto encrypt an already encrypted value.

### 3. External Key Vault Test

Run the following tests twice, parameterized by a boolean `withExternalKeyVault`.

1. Create a MongoClient without encryption enabled (referred to as `client`).

2. Using `client`, drop the collections `keyvault.datakeys` and `db.coll`. Insert the document
    [external/external-key.json](../external/external-key.json) into `keyvault.datakeys`.

3. Create the following:

    - A MongoClient configured with auto encryption (referred to as `client_encrypted`)
    - A `ClientEncryption` object (referred to as `client_encryption`)

    Configure both objects with the `local` KMS providers as follows:

    ```javascript
    { "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } }
    ```

    Configure both objects with `keyVaultNamespace` set to `keyvault.datakeys`.

    Configure `client_encrypted` to use the schema [external/external-schema.json](../external/external-schema.json) for
    `db.coll` by setting a schema map like: `{ "db.coll": <contents of external-schema.json> }`

    If `withExternalKeyVault == true`, configure both objects with an external key vault client. The external client MUST
    connect to the same MongoDB cluster that is being tested against, except it MUST use the username `fake-user` and
    password `fake-pwd`.

4. Use `client_encrypted` to insert the document `{"encrypted": "test"}` into `db.coll`. If
    `withExternalKeyVault == true`, expect an authentication exception to be thrown. Otherwise, expect the insert to
    succeed.

5. Use `client_encryption` to explicitly encrypt the string `"test"` with key ID `LOCALAAAAAAAAAAAAAAAAA==` and
    deterministic algorithm. If `withExternalKeyVault == true`, expect an authentication exception to be thrown.
    Otherwise, expect the insert to succeed.

### 4. BSON Size Limits and Batch Splitting

First, perform the setup.

1. Create a MongoClient without encryption enabled (referred to as `client`).

2. Using `client`, drop and create the collection `db.coll` configured with the included JSON schema
    [limits/limits-schema.json](../limits/limits-schema.json).

3. Using `client`, drop the collection `keyvault.datakeys`. Insert the document
    [limits/limits-key.json](../limits/limits-key.json)

4. Create a MongoClient configured with auto encryption (referred to as `client_encrypted`)

    Configure with the `local` KMS provider as follows:

    ```javascript
    { "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } }
    ```

    Configure with the `keyVaultNamespace` set to `keyvault.datakeys`.

Using `client_encrypted` perform the following operations:

1. Insert `{ "_id": "over_2mib_under_16mib", "unencrypted": <the string "a" repeated 2097152 times> }`.

    Expect this to succeed since this is still under the `maxBsonObjectSize` limit.

2. Insert the document [limits/limits-doc.json](../limits/limits-doc.json) concatenated with
    `{ "_id": "encryption_exceeds_2mib", "unencrypted": < the string "a" repeated (2097152 - 2000) times > }` Note:
    limits-doc.json is a 1005 byte BSON document that encrypts to a ~10,000 byte document.

    Expect this to succeed since after encryption this still is below the normal maximum BSON document size. Note, before
    auto encryption this document is under the 2 MiB limit. After encryption it exceeds the 2 MiB limit, but does NOT
    exceed the 16 MiB limit.

3. Bulk insert the following:

    - `{ "_id": "over_2mib_1", "unencrypted": <the string "a" repeated (2097152) times> }`
    - `{ "_id": "over_2mib_2", "unencrypted": <the string "a" repeated (2097152) times> }`

    Expect the bulk write to succeed and split after first doc (i.e. two inserts occur). This may be verified using
    [command monitoring](../../command-logging-and-monitoring/command-logging-and-monitoring.md).

4. Bulk insert the following:

    - The document [limits/limits-doc.json](../limits/limits-doc.json) concatenated with
        `{ "_id": "encryption_exceeds_2mib_1", "unencrypted": < the string "a" repeated (2097152 - 2000) times > }`
    - The document [limits/limits-doc.json](../limits/limits-doc.json) concatenated with
        `{ "_id": "encryption_exceeds_2mib_2", "unencrypted": < the string "a" repeated (2097152 - 2000) times > }`

    Expect the bulk write to succeed and split after first doc (i.e. two inserts occur). This may be verified using
    [command logging and monitoring](../../command-logging-and-monitoring/command-logging-and-monitoring.md).

5. Insert `{ "_id": "under_16mib", "unencrypted": <the string "a" repeated 16777216 - 2000 times>`.

    Expect this to succeed since this is still (just) under the `maxBsonObjectSize` limit.

6. Insert the document [limits/limits-doc.json](../limits/limits-doc.json) concatenated with
    `{ "_id": "encryption_exceeds_16mib", "unencrypted": < the string "a" repeated (16777216 - 2000) times > }`

    Expect this to fail since encryption results in a document exceeding the `maxBsonObjectSize` limit.

Optionally, if it is possible to mock the maxWriteBatchSize (i.e. the maximum number of documents in a batch) test that
setting maxWriteBatchSize=1 and inserting the two documents `{ "_id": "a" }, { "_id": "b" }` with `client_encrypted`
splits the operation into two inserts.

### 5. Views Are Prohibited

1. Create a MongoClient without encryption enabled (referred to as `client`).

2. Using `client`, drop and create a view named `db.view` with an empty pipeline. E.g. using the command
    `{ "create": "view", "viewOn": "coll" }`.

3. Create a MongoClient configured with auto encryption (referred to as `client_encrypted`)

    Configure with the `local` KMS provider as follows:

    ```javascript
    { "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } }
    ```

    Configure with the `keyVaultNamespace` set to `keyvault.datakeys`.

4. Using `client_encrypted`, attempt to insert a document into `db.view`. Expect an exception to be thrown containing
    the message: "cannot auto encrypt a view".

### 6. Corpus Test

The corpus test exhaustively enumerates all ways to encrypt all BSON value types. Note, the test data includes BSON
binary subtype 4 (or standard UUID), which MUST be decoded and encoded as subtype 4. Run the test as follows.

1. Create a MongoClient without encryption enabled (referred to as `client`).

2. Using `client`, drop and create the collection `db.coll` configured with the included JSON schema
    [corpus/corpus-schema.json](../corpus/corpus-schema.json).

3. Using `client`, drop the collection `keyvault.datakeys`. Insert the documents
    [corpus/corpus-key-local.json](../corpus/corpus-key-local.json),
    [corpus/corpus-key-aws.json](../corpus/corpus-key-aws.json),
    [corpus/corpus-key-azure.json](../corpus/corpus-key-azure.json),
    [corpus/corpus-key-gcp.json](../corpus/corpus-key-gcp.json), and
    [corpus/corpus-key-kmip.json](../corpus/corpus-key-kmip.json).

4. Create the following:

    - A MongoClient configured with auto encryption (referred to as `client_encrypted`)
    - A `ClientEncryption` object (referred to as `client_encryption`)

    Configure both objects with `aws`, `azure`, `gcp`, `local`, and `kmip` KMS providers as follows:

    ```javascript
    {
        "aws": { <AWS credentials> },
        "azure": { <Azure credentials> },
        "gcp": { <GCP credentials> },
        "local": { "key": <base64 decoding of LOCAL_MASTERKEY> },
        "kmip": { "endpoint": "localhost:5698" }
    }
    ```

    Configure KMIP TLS connections to use the following options:

    - `tlsCAFile` (or equivalent) set to
        [drivers-evergreen-tools/.evergreen/x509gen/ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem).
        This MAY be configured system-wide.
    - `tlsCertificateKeyFile` (or equivalent) set to
        [drivers-evergreen-tools/.evergreen/x509gen/client.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/client.pem).

    The method of passing TLS options for KMIP TLS connections is driver dependent.

    Where LOCAL_MASTERKEY is the following base64:

    ```text
    Mng0NCt4ZHVUYUJCa1kxNkVyNUR1QURhZ2h2UzR2d2RrZzh0cFBwM3R6NmdWMDFBMUN3YkQ5aXRRMkhGRGdQV09wOGVNYUMxT2k3NjZKelhaQmRCZGJkTXVyZG9uSjFk
    ```

    Configure both objects with `keyVaultNamespace` set to `keyvault.datakeys`.

5. Load [corpus/corpus.json](../corpus/corpus.json) to a variable named `corpus`. The corpus contains subdocuments with
    the following fields:

    - `kms` is `aws`, `azure`, `gcp`, `local`, or `kmip`
    - `type` is a BSON type string
        [names coming from here](https://www.mongodb.com/docs/manual/reference/operator/query/type/))
    - `algo` is either `rand` or `det` for random or deterministic encryption
    - `method` is either `auto`, for automatic encryption or `explicit` for explicit encryption
    - `identifier` is either `id` or `altname` for the key identifier
    - `allowed` is a boolean indicating whether the encryption for the given parameters is permitted.
    - `value` is the value to be tested.

    Create a new BSON document, named `corpus_copied`. Iterate over each field of `corpus`.

    - If the field name is `_id`, `altname_aws`, `altname_local`, `altname_azure`, `altname_gcp`, or `altname_kmip` copy
        the field to `corpus_copied`.

    - If `method` is `auto`, copy the field to `corpus_copied`.

    - If `method` is `explicit`, use `client_encryption` to explicitly encrypt the value.

        - Encrypt with the algorithm described by `algo`.
        - If `identifier` is `id`
            - If `kms` is `local` set the key_id to the UUID with base64 value `LOCALAAAAAAAAAAAAAAAAA==`.
            - If `kms` is `aws` set the key_id to the UUID with base64 value `AWSAAAAAAAAAAAAAAAAAAA==`.
            - If `kms` is `azure` set the key_id to the UUID with base64 value `AZUREAAAAAAAAAAAAAAAAA==`.
            - If `kms` is `gcp` set the key_id to the UUID with base64 value `GCPAAAAAAAAAAAAAAAAAAA==`.
            - If `kms` is `kmip` set the key_id to the UUID with base64 value `KMIPAAAAAAAAAAAAAAAAAA==`.
        - If `identifier` is `altname`
            - If `kms` is `local` set the key_alt_name to "local".
            - If `kms` is `aws` set the key_alt_name to "aws".
            - If `kms` is `azure` set the key_alt_name to "azure".
            - If `kms` is `gcp` set the key_alt_name to "gcp".
            - If `kms` is `kmip` set the key_alt_name to "kmip".

        If `allowed` is true, copy the field and encrypted value to `corpus_copied`. If `allowed` is false. verify that an
        exception is thrown. Copy the unencrypted value to to `corpus_copied`.

6. Using `client_encrypted`, insert `corpus_copied` into `db.coll`.

7. Using `client_encrypted`, find the inserted document from `db.coll` to a variable named `corpus_decrypted`. Since it
    should have been automatically decrypted, assert the document exactly matches `corpus`.

8. Load [corpus/corpus_encrypted.json](../corpus/corpus-encrypted.json) to a variable named `corpus_encrypted_expected`.
    Using `client` find the inserted document from `db.coll` to a variable named `corpus_encrypted_actual`.

    Iterate over each field of `corpus_encrypted_expected` and check the following:

    - If the `algo` is `det`, that the value equals the value of the corresponding field in `corpus_encrypted_actual`.
    - If the `algo` is `rand` and `allowed` is true, that the value does not equal the value of the corresponding field
        in `corpus_encrypted_actual`.
    - If `allowed` is true, decrypt the value with `client_encryption`. Decrypt the value of the corresponding field of
        `corpus_encrypted` and validate that they are both equal.
    - If `allowed` is false, validate the value exactly equals the value of the corresponding field of `corpus` (neither
        was encrypted).

9. Repeat steps 1-8 with a local JSON schema. I.e. amend step 4 to configure the schema on `client_encrypted` with the
    `schema_map` option.

### 7. Custom Endpoint Test

#### Setup

For each test cases, start by creating two `ClientEncryption` objects. Recreate the `ClientEncryption` objects for each
test case.

Create a `ClientEncryption` object (referred to as `client_encryption`)

Configure with `keyVaultNamespace` set to `keyvault.datakeys`, and a default MongoClient as the `keyVaultClient`.

Configure with KMS providers as follows:

```javascript
{
      "aws": {
         "accessKeyId": <set from environment>,
         "secretAccessKey": <set from environment>
      },
      "azure": {
         "tenantId": <set from environment>,
         "clientId": <set from environment>,
         "clientSecret": <set from environment>,
         "identityPlatformEndpoint": "login.microsoftonline.com:443"
      },
      "gcp": {
         "email": <set from environment>,
         "privateKey": <set from environment>,
         "endpoint": "oauth2.googleapis.com:443"
      },
      "kmip" {
         "endpoint": "localhost:5698"
      }
}
```

Create a `ClientEncryption` object (referred to as `client_encryption_invalid`)

Configure with `keyVaultNamespace` set to `keyvault.datakeys`, and a default MongoClient as the `keyVaultClient`.

Configure with KMS providers as follows:

```javascript
{
      "azure": {
         "tenantId": <set from environment>,
         "clientId": <set from environment>,
         "clientSecret": <set from environment>,
         "identityPlatformEndpoint": "doesnotexist.invalid:443"
      },
      "gcp": {
         "email": <set from environment>,
         "privateKey": <set from environment>,
         "endpoint": "doesnotexist.invalid:443"
      },
      "kmip": {
         "endpoint": "doesnotexist.invalid:5698"
      }
}
```

Configure KMIP TLS connections to use the following options:

- `tlsCAFile` (or equivalent) set to
    [drivers-evergreen-tools/.evergreen/x509gen/ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem).
    This MAY be configured system-wide.
- `tlsCertificateKeyFile` (or equivalent) set to
    [drivers-evergreen-tools/.evergreen/x509gen/client.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/client.pem).

The method of passing TLS options for KMIP TLS connections is driver dependent.

#### Test cases

1. Call `client_encryption.createDataKey()` with "aws" as the provider and the following masterKey:

    ```javascript
    {
      region: "us-east-1",
      key: "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0"
    }
    ```

    Expect this to succeed. Use the returned UUID of the key to explicitly encrypt and decrypt the string "test" to
    validate it works.

2. Call `client_encryption.createDataKey()` with "aws" as the provider and the following masterKey:

    ```javascript
    {
      region: "us-east-1",
      key: "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0",
      endpoint: "kms.us-east-1.amazonaws.com"
    }
    ```

    Expect this to succeed. Use the returned UUID of the key to explicitly encrypt and decrypt the string "test" to
    validate it works.

3. Call `client_encryption.createDataKey()` with "aws" as the provider and the following masterKey:

    ```javascript
    {
      region: "us-east-1",
      key: "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0",
      endpoint: "kms.us-east-1.amazonaws.com:443"
    }
    ```

    Expect this to succeed. Use the returned UUID of the key to explicitly encrypt and decrypt the string "test" to
    validate it works.

4. Call `client_encryption.createDataKey()` with "kmip" as the provider and the following masterKey:

    ```javascript
    {
      "keyId": "1",
      "endpoint": "localhost:12345"
    }
    ```

    Expect this to fail with a socket connection error.

5. Call `client_encryption.createDataKey()` with "aws" as the provider and the following masterKey:

    ```javascript
    {
      region: "us-east-1",
      key: "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0",
      endpoint: "kms.us-east-2.amazonaws.com"
    }
    ```

    Expect this to fail with an exception.

6. Call `client_encryption.createDataKey()` with "aws" as the provider and the following masterKey:

    ```javascript
    {
      region: "us-east-1",
      key: "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0",
      endpoint: "doesnotexist.invalid"
    }
    ```

    Expect this to fail with a network exception indicating failure to resolve "doesnotexist.invalid".

7. Call `client_encryption.createDataKey()` with "azure" as the provider and the following masterKey:

    ```javascript
    {
       "keyVaultEndpoint": "key-vault-csfle.vault.azure.net",
       "keyName": "key-name-csfle"
    }
    ```

    Expect this to succeed. Use the returned UUID of the key to explicitly encrypt and decrypt the string "test" to
    validate it works.

    Call `client_encryption_invalid.createDataKey()` with the same masterKey. Expect this to fail with a network
    exception indicating failure to resolve "doesnotexist.invalid".

8. Call `client_encryption.createDataKey()` with "gcp" as the provider and the following masterKey:

    ```javascript
    {
      "projectId": "devprod-drivers",
      "location": "global",
      "keyRing": "key-ring-csfle",
      "keyName": "key-name-csfle",
      "endpoint": "cloudkms.googleapis.com:443"
    }
    ```

    Expect this to succeed. Use the returned UUID of the key to explicitly encrypt and decrypt the string "test" to
    validate it works.

    Call `client_encryption_invalid.createDataKey()` with the same masterKey. Expect this to fail with a network
    exception indicating failure to resolve "doesnotexist.invalid".

9. Call `client_encryption.createDataKey()` with "gcp" as the provider and the following masterKey:

    ```javascript
    {
      "projectId": "devprod-drivers",
      "location": "global",
      "keyRing": "key-ring-csfle",
      "keyName": "key-name-csfle",
      "endpoint": "doesnotexist.invalid:443"
    }
    ```

    Expect this to fail with an exception with a message containing the string: "Invalid KMS response".

10. Call `client_encryption.createDataKey()` with "kmip" as the provider and the following masterKey:

    ```javascript
    {
      "keyId": "1"
    }
    ```

    Expect this to succeed. Use the returned UUID of the key to explicitly encrypt and decrypt the string "test" to
    validate it works.

    Call `client_encryption_invalid.createDataKey()` with the same masterKey. Expect this to fail with a network
    exception indicating failure to resolve "doesnotexist.invalid".

11. Call `client_encryption.createDataKey()` with "kmip" as the provider and the following masterKey:

    ```javascript
    {
      "keyId": "1",
      "endpoint": "localhost:5698"
    }
    ```

    Expect this to succeed. Use the returned UUID of the key to explicitly encrypt and decrypt the string "test" to
    validate it works.

12. Call `client_encryption.createDataKey()` with "kmip" as the provider and the following masterKey:

    ```javascript
    {
      "keyId": "1",
      "endpoint": "doesnotexist.invalid:5698"
    }
    ```

    Expect this to fail with a network exception indicating failure to resolve "doesnotexist.invalid".

### 8. Bypass Spawning mongocryptd

> [!NOTE]
> CONSIDER: To reduce the chances of tests interfering with each other, drivers MAY use a different port for each test
> in this group, and include it in `--pidfilepath`. The interference may come from the fact that once spawned by a test,
> `mongocryptd` stays up and running for some time.

#### Via loading shared library

The following tests that loading [crypt_shared](../client-side-encryption.md#crypt_shared) bypasses spawning
mongocryptd.

> [!NOTE]
> IMPORTANT: This test requires the [crypt_shared](../client-side-encryption.md#crypt_shared) library be loaded. If the
> [crypt_shared](../client-side-encryption.md#crypt_shared) library is not available, skip the test.

1. Create a MongoClient configured with auto encryption (referred to as `client_encrypted`)

    Configure the required options. Use the `local` KMS provider as follows:

    ```javascript
    { "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } }
    ```

    Configure with the `keyVaultNamespace` set to `keyvault.datakeys`.

    Configure `client_encrypted` to use the schema [external/external-schema.json](../external/external-schema.json) for
    `db.coll` by setting a schema map like: `{ "db.coll": <contents of external-schema.json> }`

    Configure the following `extraOptions`:

    ```javascript
    {
      "mongocryptdURI": "mongodb://localhost:27021/?serverSelectionTimeoutMS=1000",
      "mongocryptdSpawnArgs": [ "--pidfilepath=bypass-spawning-mongocryptd.pid", "--port=27021"],
      "cryptSharedLibPath": "<path to shared library>",
      "cryptSharedLibRequired": true
    }
    ```

    Drivers MAY pass a different port if they expect their testing infrastructure to be using port 27021. Pass a port
    that should be free.

2. Use `client_encrypted` to insert the document `{"unencrypted": "test"}` into `db.coll`. Expect this to succeed.

3. Validate that mongocryptd was not spawned. Create a MongoClient to localhost:27021 (or whatever was passed via
    `--port`) with serverSelectionTimeoutMS=1000. Run a handshake command and ensure it fails with a server selection
    timeout.

> [!NOTE]
> IMPORTANT: If [crypt_shared](../client-side-encryption.md#crypt_shared) is visible to the operating system's library
> search mechanism, the expected server error generated by the `Via mongocryptdBypassSpawn`, `Via bypassAutoEncryption`,
> `Via bypassQueryAnalysis` tests will not appear because libmongocrypt will load the `crypt_shared` library instead of
> consulting mongocryptd. For the following tests, it is required that libmongocrypt *not* load `crypt_shared`. Refer to
> the client-side-encryption document for more information on "disabling" `crypt_shared`. Take into account that once
> loaded, for example, by another test, `crypt_shared` cannot be unloaded and may be used by `MongoClient`, thus making
> the tests misbehave in unexpected ways.

#### Via mongocryptdBypassSpawn

The following tests that setting `mongocryptdBypassSpawn=true` really does bypass spawning mongocryptd.

1. Insert the document [external/external-key.json](../external/external-key.json) into `keyvault.datakeys` with
    majority write concern. This step is not required to run this test, and drivers MAY skip it. But if the driver
    misbehaves, then not having the encryption fully set up may complicate the process of figuring out what is wrong.

2. Create a MongoClient configured with auto encryption (referred to as `client_encrypted`)

    Configure the required options. Use the `local` KMS provider as follows:

    ```javascript
    { "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } }
    ```

    Configure with the `keyVaultNamespace` set to `keyvault.datakeys`.

    Configure `client_encrypted` to use the schema [external/external-schema.json](../external/external-schema.json) for
    `db.coll` by setting a schema map like: `{ "db.coll": <contents of external-schema.json> }`

    Configure the following `extraOptions`:

    ```javascript
    {
      "mongocryptdBypassSpawn": true
      "mongocryptdURI": "mongodb://localhost:27021/?serverSelectionTimeoutMS=1000",
      "mongocryptdSpawnArgs": [ "--pidfilepath=bypass-spawning-mongocryptd.pid", "--port=27021"]
    }
    ```

    Drivers MAY pass a different port if they expect their testing infrastructure to be using port 27021. Pass a port
    that should be free.

3. Use `client_encrypted` to insert the document `{"encrypted": "test"}` into `db.coll`. Expect a server selection error
    propagated from the internal MongoClient failing to connect to mongocryptd on port 27021.

#### Via bypassAutoEncryption

The following tests that setting `bypassAutoEncryption=true` really does bypass spawning mongocryptd.

1. Create a MongoClient configured with auto encryption (referred to as `client_encrypted`)

    Configure the required options. Use the `local` KMS provider as follows:

    ```javascript
    { "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } }
    ```

    Configure with the `keyVaultNamespace` set to `keyvault.datakeys`.

    Configure with `bypassAutoEncryption=true`.

    Configure the following `extraOptions`:

    ```javascript
    {
      "mongocryptdSpawnArgs": [ "--pidfilepath=bypass-spawning-mongocryptd.pid", "--port=27021"]
    }
    ```

    Drivers MAY pass a different value to `--port` if they expect their testing infrastructure to be using port 27021.
    Pass a port that should be free.

2. Use `client_encrypted` to insert the document `{"unencrypted": "test"}` into `db.coll`. Expect this to succeed.

3. Validate that mongocryptd was not spawned. Create a MongoClient to localhost:27021 (or whatever was passed via
    `--port`) with serverSelectionTimeoutMS=1000. Run a handshake command and ensure it fails with a server selection
    timeout.

#### Via bypassQueryAnalysis

Repeat the steps from the "Via bypassAutoEncryption" test, replacing "bypassAutoEncryption=true" with
"bypassQueryAnalysis=true".

### 9. Deadlock Tests

The following tests only apply to drivers that have implemented a connection pool (see the
[Connection Monitoring and Pooling](../../connection-monitoring-and-pooling/connection-monitoring-and-pooling.md)
specification).

There are multiple parameterized test cases. Before each test case, perform the setup.

#### Setup

Create a `MongoClient` for setup operations named `client_test`.

Create a `MongoClient` for key vault operations with `maxPoolSize=1` named `client_keyvault`. Capture command started
events.

Using `client_test`, drop the collections `keyvault.datakeys` and `db.coll`.

Insert the document [external/external-key.json](../external/external-key.json) into `keyvault.datakeys` with majority
write concern.

Create a collection `db.coll` configured with a JSON schema
[external/external-schema.json](../external/external-schema.json) as the validator, like so:

```typescript
{"create": "coll", "validator": {"$jsonSchema": <json_schema>}}
```

Create a `ClientEncryption` object, named `client_encryption` configured with: - `keyVaultClient`=`client_test` -
`keyVaultNamespace`="keyvault.datakeys" - `kmsProviders`=`{ "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } }`

Use `client_encryption` to encrypt the value "string0" with `algorithm`="AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic"
and `keyAltName`="local". Store the result in a variable named `ciphertext`.

Proceed to run the test case.

Each test case configures a `MongoClient` with automatic encryption (named `client_encrypted`).

Each test must assert the number of unique `MongoClient` objects created. This can be accomplished by capturing
`TopologyOpeningEvent`, or by checking command started events for a client identifier (not possible in all drivers).

#### Running a test case

- Create a `MongoClient` named `client_encrypted` configured as follows:

    - Set `AutoEncryptionOpts`:

        - `keyVaultNamespace="keyvault.datakeys"`
        - `kmsProviders`=`{ "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } }`
        - Append `TestCase.AutoEncryptionOpts` (defined below)

    - Capture command started events.

    - Set `maxPoolSize=TestCase.MaxPoolSize`

- If the testcase sets `AutoEncryptionOpts.bypassAutoEncryption=true`:

    - Use `client_test` to insert `{ "_id": 0, "encrypted": <ciphertext> }` into `db.coll`.

- Otherwise:

    - Use `client_encrypted` to insert `{ "_id": 0, "encrypted": "string0" }`.

- Use `client_encrypted` to run a `findOne` operation on `db.coll`, with the filter `{ "_id": 0 }`.

- Expect the result to be `{ "_id": 0, "encrypted": "string0" }`.

- Check captured events against `TestCase.Expectations`.

- Check the number of unique `MongoClient` objects created is equal to `TestCase.ExpectedNumberOfClients`.

#### Case 1

- MaxPoolSize: 1

- AutoEncryptionOpts:

    - bypassAutoEncryption=false
    - keyVaultClient=unset

- Expectations:

    - Expect `client_encrypted` to have captured four `CommandStartedEvent`:
        - a listCollections to "db".
        - a find on "keyvault".
        - an insert on "db".
        - a find on "db"

- ExpectedNumberOfClients: 2

#### Case 2

- MaxPoolSize: 1

- AutoEncryptionOpts:

    - bypassAutoEncryption=false
    - keyVaultClient=client_keyvault

- Expectations:

    - Expect `client_encrypted` to have captured three `CommandStartedEvent`:

        - a listCollections to "db".
        - an insert on "db".
        - a find on "db"

    - Expect `client_keyvault` to have captured one `CommandStartedEvent`:

        - a find on "keyvault".

- ExpectedNumberOfClients: 2

#### Case 3

- MaxPoolSize: 1

- AutoEncryptionOpts:

    - bypassAutoEncryption=true
    - keyVaultClient=unset

- Expectations:

    - Expect `client_encrypted` to have captured three `CommandStartedEvent`:
        - a find on "db"
        - a find on "keyvault".

- ExpectedNumberOfClients: 2

#### Case 4

- MaxPoolSize: 1

- AutoEncryptionOpts:

    - bypassAutoEncryption=true
    - keyVaultClient=client_keyvault

- Expectations:

    - Expect `client_encrypted` to have captured two `CommandStartedEvent`:

        - a find on "db"

    - Expect `client_keyvault` to have captured one `CommandStartedEvent`:

        - a find on "keyvault".

- ExpectedNumberOfClients: 1

#### Case 5

Drivers that do not support an unlimited maximum pool size MUST skip this test.

- MaxPoolSize: 0

- AutoEncryptionOpts:

    - bypassAutoEncryption=false
    - keyVaultClient=unset

- Expectations:

    - Expect `client_encrypted` to have captured five `CommandStartedEvent`:
        - a listCollections to "db".
        - a listCollections to "keyvault".
        - a find on "keyvault".
        - an insert on "db".
        - a find on "db"

- ExpectedNumberOfClients: 1

#### Case 6

Drivers that do not support an unlimited maximum pool size MUST skip this test.

- MaxPoolSize: 0

- AutoEncryptionOpts:

    - bypassAutoEncryption=false
    - keyVaultClient=client_keyvault

- Expectations:

    - Expect `client_encrypted` to have captured three `CommandStartedEvent`:

        - a listCollections to "db".
        - an insert on "db".
        - a find on "db"

    - Expect `client_keyvault` to have captured one `CommandStartedEvent`:

        - a find on "keyvault".

- ExpectedNumberOfClients: 1

#### Case 7

Drivers that do not support an unlimited maximum pool size MUST skip this test.

- MaxPoolSize: 0

- AutoEncryptionOpts:

    - bypassAutoEncryption=true
    - keyVaultClient=unset

- Expectations:

    - Expect `client_encrypted` to have captured three `CommandStartedEvent`:
        - a find on "db"
        - a find on "keyvault".

- ExpectedNumberOfClients: 1

#### Case 8

Drivers that do not support an unlimited maximum pool size MUST skip this test.

- MaxPoolSize: 0

- AutoEncryptionOpts:

    - bypassAutoEncryption=true
    - keyVaultClient=client_keyvault

- Expectations:

    - Expect `client_encrypted` to have captured two `CommandStartedEvent`:

        - a find on "db"

    - Expect `client_keyvault` to have captured one `CommandStartedEvent`:

        - a find on "keyvault".

- ExpectedNumberOfClients: 1

### 10. KMS TLS Tests

The following tests that connections to KMS servers with TLS verify peer certificates.

The two tests below make use of mock KMS servers which can be run on Evergreen using
[the mock KMS server script](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/csfle/kms_http_server.py).
Drivers can set up their local Python environment for the mock KMS server by running
[the virtualenv activation script](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/csfle/activate-kmstlsvenv.sh).

To start two mock KMS servers, one on port 9000 with
[ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem) as a CA file and
[expired.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/expired.pem) as a
cert file, and one on port 9001 with
[ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem) as a CA file and
[wrong-host.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/wrong-host.pem)
as a cert file, run the following commands from the `.evergreen/csfle` directory:

```shell
. ./activate_venv.sh
python -u kms_http_server.py --ca_file ../x509gen/ca.pem --cert_file ../x509gen/expired.pem --port 9000 &
python -u kms_http_server.py --ca_file ../x509gen/ca.pem --cert_file ../x509gen/wrong-host.pem --port 9001 &
```

#### Setup

For both tests, do the following:

1. Start a `mongod` process with **server version 4.2.0 or later**.
2. Create a `MongoClient` for key vault operations.
3. Create a `ClientEncryption` object (referred to as `client_encryption`) with `keyVaultNamespace` set to
    `keyvault.datakeys`.

#### Invalid KMS Certificate

1. Start a mock KMS server on port 9000 with
    [ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem) as a CA
    file and
    [expired.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/expired.pem)
    as a cert file.

2. Call `client_encryption.createDataKey()` with "aws" as the provider and the following masterKey:

    ```javascript
    {
       "region": "us-east-1",
       "key": "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0",
       "endpoint": "127.0.0.1:9000",
    }
    ```

    Expect this to fail with an exception with a message referencing an expired certificate. This message will be
    language dependent. In Python, this message is "certificate verify failed: certificate has expired". In Go, this
    message is "certificate has expired or is not yet valid". If the language of implementation has a single, generic
    error message for all certificate validation errors, drivers may inspect other fields of the error to verify its
    meaning.

#### Invalid Hostname in KMS Certificate

1. Start a mock KMS server on port 9001 with
    [ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem) as a CA
    file and
    [wrong-host.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/wrong-host.pem)
    as a cert file.

2. Call `client_encryption.createDataKey()` with "aws" as the provider and the following masterKey:

    ```javascript
    {
       "region": "us-east-1",
       "key": "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0",
       "endpoint": "127.0.0.1:9001",
    }
    ```

    Expect this to fail with an exception with a message referencing an incorrect or unexpected host. This message will
    be language dependent. In Python, this message is "certificate verify failed: IP address mismatch, certificate is
    not valid for '127.0.0.1'". In Go, this message is "cannot validate certificate for 127.0.0.1 because it doesn't
    contain any IP SANs". If the language of implementation has a single, generic error message for all certificate
    validation errors, drivers may inspect other fields of the error to verify its meaning.

### 11. KMS TLS Options Tests

#### Setup

Start a `mongod` process with **server version 4.2.0 or later**.

Four mock KMS server processes must be running:

1. The mock
    [KMS HTTP server](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/csfle/kms_http_server.py).

    Run on port 9000 with
    [ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem) as a CA
    file and
    [expired.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/expired.pem)
    as a cert file.

    Example:

    ```shell
    python -u kms_http_server.py --ca_file ../x509gen/ca.pem --cert_file ../x509gen/expired.pem --port 9000
    ```

2. The mock
    [KMS HTTP server](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/csfle/kms_http_server.py).

    Run on port 9001 with
    [ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem) as a CA
    file and
    [wrong-host.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/wrong-host.pem)
    as a cert file.

    Example:

    ```shell
    python -u kms_http_server.py --ca_file ../x509gen/ca.pem --cert_file ../x509gen/wrong-host.pem --port 9001
    ```

3. The mock
    [KMS HTTP server](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/csfle/kms_http_server.py).

    Run on port 9002 with
    [ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem) as a CA
    file and
    [server.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/server.pem) as
    a cert file.

    Run with the `--require_client_cert` option.

    Example:

    ```shell
    python -u kms_http_server.py --ca_file ../x509gen/ca.pem --cert_file ../x509gen/server.pem --port 9002 --require_client_cert
    ```

4. The mock
    [KMS KMIP server](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/csfle/kms_kmip_server.py).

Create the following `ClientEncryption` objects.

Configure each with `keyVaultNamespace` set to `keyvault.datakeys`, and a default MongoClient as the `keyVaultClient`.

1. Create a `ClientEncryption` object named `client_encryption_no_client_cert` with the following KMS providers:

    ```javascript
    {
          "aws": {
             "accessKeyId": <set from environment>,
             "secretAccessKey": <set from environment>
          },
          "azure": {
             "tenantId": <set from environment>,
             "clientId": <set from environment>,
             "clientSecret": <set from environment>,
             "identityPlatformEndpoint": "127.0.0.1:9002"
          },
          "gcp": {
             "email": <set from environment>,
             "privateKey": <set from environment>,
             "endpoint": "127.0.0.1:9002"
          },
          "kmip" {
             "endpoint": "127.0.0.1:5698"
          }
    }
    ```

    Add TLS options for the `aws`, `azure`, `gcp`, and `kmip` providers to use the following options:

    - `tlsCAFile` (or equivalent) set to
        [ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem). This MAY
        be configured system-wide.

2. Create a `ClientEncryption` object named `client_encryption_with_tls` with the following KMS providers:

    ```javascript
    {
          "aws": {
             "accessKeyId": <set from environment>,
             "secretAccessKey": <set from environment>
          },
          "azure": {
             "tenantId": <set from environment>,
             "clientId": <set from environment>,
             "clientSecret": <set from environment>,
             "identityPlatformEndpoint": "127.0.0.1:9002"
          },
          "gcp": {
             "email": <set from environment>,
             "privateKey": <set from environment>,
             "endpoint": "127.0.0.1:9002"
          },
          "kmip" {
             "endpoint": "127.0.0.1:5698"
          }
    }
    ```

    Add TLS options for the `aws`, `azure`, `gcp`, and `kmip` providers to use the following options:

    - `tlsCAFile` (or equivalent) set to
        [ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem). This MAY
        be configured system-wide.
    - `tlsCertificateKeyFile` (or equivalent) set to
        [client.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/client.pem)

3. Create a `ClientEncryption` object named `client_encryption_expired` with the following KMS providers:

    ```javascript
    {
          "aws": {
             "accessKeyId": <set from environment>,
             "secretAccessKey": <set from environment>
          },
          "azure": {
             "tenantId": <set from environment>,
             "clientId": <set from environment>,
             "clientSecret": <set from environment>,
             "identityPlatformEndpoint": "127.0.0.1:9000"
          },
          "gcp": {
             "email": <set from environment>,
             "privateKey": <set from environment>,
             "endpoint": "127.0.0.1:9000"
          },
          "kmip" {
             "endpoint": "127.0.0.1:9000"
          }
    }
    ```

    Add TLS options for the `aws`, `azure`, `gcp`, and `kmip` providers to use the following options:

    - `tlsCAFile` (or equivalent) set to
        [ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem). This MAY
        be configured system-wide.

4. Create a `ClientEncryption` object named `client_encryption_invalid_hostname` with the following KMS providers:

    ```javascript
    {
          "aws": {
             "accessKeyId": <set from environment>,
             "secretAccessKey": <set from environment>
          },
          "azure": {
             "tenantId": <set from environment>,
             "clientId": <set from environment>,
             "clientSecret": <set from environment>,
             "identityPlatformEndpoint": "127.0.0.1:9001"
          },
          "gcp": {
             "email": <set from environment>,
             "privateKey": <set from environment>,
             "endpoint": "127.0.0.1:9001"
          },
          "kmip" {
             "endpoint": "127.0.0.1:9001"
          }
    }
    ```

    Add TLS options for the `aws`, `azure`, `gcp`, and `kmip` providers to use the following options:

    - `tlsCAFile` (or equivalent) set to
        [ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem). This MAY
        be configured system-wide.

5. Create a `ClientEncryption` object named `client_encryption_with_names` with the following KMS providers:

    ```javascript
    {
          "aws:no_client_cert": {
             "accessKeyId": <set from environment>,
             "secretAccessKey": <set from environment>
          },
          "azure:no_client_cert": {
             "tenantId": <set from environment>,
             "clientId": <set from environment>,
             "clientSecret": <set from environment>,
             "identityPlatformEndpoint": "127.0.0.1:9002"
          },
          "gcp:no_client_cert": {
             "email": <set from environment>,
             "privateKey": <set from environment>,
             "endpoint": "127.0.0.1:9002"
          },
          "kmip:no_client_cert": {
             "endpoint": "127.0.0.1:5698"
          },
          "aws:with_tls": {
             "accessKeyId": <set from environment>,
             "secretAccessKey": <set from environment>
          },
          "azure:with_tls": {
             "tenantId": <set from environment>,
             "clientId": <set from environment>,
             "clientSecret": <set from environment>,
             "identityPlatformEndpoint": "127.0.0.1:9002"
          },
          "gcp:with_tls": {
             "email": <set from environment>,
             "privateKey": <set from environment>,
             "endpoint": "127.0.0.1:9002"
          },
          "kmip:with_tls": {
             "endpoint": "127.0.0.1:5698"
          }
    }
    ```

    Support for named KMS providers requires libmongocrypt 1.9.0.

    Add TLS options for the `aws:no_client_cert`, `azure:no_client_cert`, `gcp:no_client_cert`, and `kmip:no_client_cert`
    providers to use the following options:

    - `tlsCAFile` (or equivalent) set to
        [ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem). This MAY
        be configured system-wide.

    Add TLS options for the `aws:with_tls`, `azure:with_tls`, `gcp:with_tls`, and `kmip:with_tls` providers to use the
    following options:

    - `tlsCAFile` (or equivalent) set to
        [ca.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/ca.pem). This MAY
        be configured system-wide.
    - `tlsCertificateKeyFile` (or equivalent) set to
        [client.pem](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/x509gen/client.pem)

#### Case 1: AWS

Call `client_encryption_no_client_cert.createDataKey()` with "aws" as the provider and the following masterKey:

```javascript
{
   region: "us-east-1",
   key: "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0"
   endpoint: "127.0.0.1:9002"
}
```

Expect an error indicating TLS handshake failed.

Call `client_encryption_with_tls.createDataKey()` with "aws" as the provider and the following masterKey:

```javascript
{
   region: "us-east-1",
   key: "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0"
   endpoint: "127.0.0.1:9002"
}
```

Expect an error from libmongocrypt with a message containing the string: "parse error". This implies TLS handshake
succeeded.

Call `client_encryption_expired.createDataKey()` with "aws" as the provider and the following masterKey:

```javascript
{
   region: "us-east-1",
   key: "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0"
   endpoint: "127.0.0.1:9000"
}
```

Expect an error indicating TLS handshake failed due to an expired certificate.

Call `client_encryption_invalid_hostname.createDataKey()` with "aws" as the provider and the following masterKey:

```javascript
{
   region: "us-east-1",
   key: "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0"
   endpoint: "127.0.0.1:9001"
}
```

Expect an error indicating TLS handshake failed due to an invalid hostname.

#### Case 2: Azure

Call `client_encryption_no_client_cert.createDataKey()` with "azure" as the provider and the following masterKey:

```javascript
{ 'keyVaultEndpoint': 'doesnotexist.invalid', 'keyName': 'foo' }
```

Expect an error indicating TLS handshake failed.

Call `client_encryption_with_tls.createDataKey()` with "azure" as the provider and the same masterKey.

Expect an error from libmongocrypt with a message containing the string: "HTTP status=404". This implies TLS handshake
succeeded.

Call `client_encryption_expired.createDataKey()` with "azure" as the provider and the same masterKey.

Expect an error indicating TLS handshake failed due to an expired certificate.

Call `client_encryption_invalid_hostname.createDataKey()` with "azure" as the provider and the same masterKey.

Expect an error indicating TLS handshake failed due to an invalid hostname.

#### Case 3: GCP

Call `client_encryption_no_client_cert.createDataKey()` with "gcp" as the provider and the following masterKey:

```javascript
{ 'projectId': 'foo', 'location': 'bar', 'keyRing': 'baz', 'keyName': 'foo' }
```

Expect an error indicating TLS handshake failed.

Call `client_encryption_with_tls.createDataKey()` with "gcp" as the provider and the same masterKey.

Expect an error from libmongocrypt with a message containing the string: "HTTP status=404". This implies TLS handshake
succeeded.

Call `client_encryption_expired.createDataKey()` with "gcp" as the provider and the same masterKey.

Expect an error indicating TLS handshake failed due to an expired certificate.

Call `client_encryption_invalid_hostname.createDataKey()` with "gcp" as the provider and the same masterKey.

Expect an error indicating TLS handshake failed due to an invalid hostname.

#### Case 4: KMIP

Call `client_encryption_no_client_cert.createDataKey()` with "kmip" as the provider and the following masterKey:

```javascript
{ }
```

Expect an error indicating TLS handshake failed.

Call `client_encryption_with_tls.createDataKey()` with "kmip" as the provider and the same masterKey.

Expect success.

Call `client_encryption_expired.createDataKey()` with "kmip" as the provider and the same masterKey.

Expect an error indicating TLS handshake failed due to an expired certificate.

Call `client_encryption_invalid_hostname.createDataKey()` with "kmip" as the provider and the same masterKey.

Expect an error indicating TLS handshake failed due to an invalid hostname.

#### Case 5: `tlsDisableOCSPEndpointCheck` is permitted

This test does not apply if the driver does not support the the option `tlsDisableOCSPEndpointCheck`.

Create a `ClientEncryption` object with the following KMS providers:

> ```javascript
> {
>       "aws": {
>          "accessKeyId": "foo",
>          "secretAccessKey": "bar"
>       }
> }
> ```
>
> Add TLS options for the `aws` with the following options:
>
> - `tlsDisableOCSPEndpointCheck` (or equivalent) set to `true`.

Expect no error on construction.

#### Case 6: named KMS providers apply TLS options

##### Named AWS

Call `client_encryption_with_names.createDataKey()` with "aws:no_client_cert" as the provider and the following
masterKey.

```javascript
{
   region: "us-east-1",
   key: "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0"
   endpoint: "127.0.0.1:9002"
}
```

Expect an error indicating TLS handshake failed.

Call `client_encryption_with_names.createDataKey()` with "aws:with_tls" as the provider and the same masterKey.

Expect an error from libmongocrypt with a message containing the string: "parse error". This implies TLS handshake
succeeded.

##### Named Azure

Call `client_encryption_with_names.createDataKey()` with "azure:no_client_cert" as the provider and the following
masterKey:

```javascript
{ 'keyVaultEndpoint': 'doesnotexist.invalid', 'keyName': 'foo' }
```

Expect an error indicating TLS handshake failed.

Call `client_encryption_with_names.createDataKey()` with "azure:with_tls" as the provider and the same masterKey.

Expect an error from libmongocrypt with a message containing the string: "HTTP status=404". This implies TLS handshake
succeeded.

##### Named GCP

Call `client_encryption_with_names.createDataKey()` with "gcp:no_client_cert" as the provider and the following
masterKey:

```javascript
{ 'projectId': 'foo', 'location': 'bar', 'keyRing': 'baz', 'keyName': 'foo' }
```

Expect an error indicating TLS handshake failed.

Call `client_encryption_with_names.createDataKey()` with "gcp:with_tls" as the provider and the same masterKey.

Expect an error from libmongocrypt with a message containing the string: "HTTP status=404". This implies TLS handshake
succeeded.

##### Named KMIP

Call `client_encryption_with_names.createDataKey()` with "kmip:no_client_cert" as the provider and the following
masterKey:

```javascript
{ }
```

Expect an error indicating TLS handshake failed.

Call `client_encryption_with_names.createDataKey()` with "kmip:with_tls" as the provider and the same masterKey.

Expect success.

### 12. Explicit Encryption

The Explicit Encryption tests require MongoDB server 7.0+. The tests must not run against a standalone.

> [!NOTE]
> MongoDB Server 7.0 introduced a backwards breaking change to the Queryable Encryption (QE) protocol: QEv2.
> libmongocrypt 1.8.0 is configured to use the QEv2 protocol.

Before running each of the following test cases, perform the following Test Setup.

#### Test Setup

Load the file
[encryptedFields.json](https://github.com/mongodb/specifications/tree/master/source/client-side-encryption/etc/data/encryptedFields.json)
as `encryptedFields`.

Load the file
[key1-document.json](https://github.com/mongodb/specifications/tree/master/source/client-side-encryption/etc/data/keys/key1-document.json)
as `key1Document`.

Read the `"_id"` field of `key1Document` as `key1ID`.

Drop and create the collection `db.explicit_encryption` using `encryptedFields` as an option. See
[FLE 2 CreateCollection() and Collection.Drop()](../client-side-encryption.md#create-collection-helper).

Drop and create the collection `keyvault.datakeys`.

Insert `key1Document` in `keyvault.datakeys` with majority write concern.

Create a MongoClient named `keyVaultClient`.

Create a ClientEncryption object named `clientEncryption` with these options:

```typescript
class ClientEncryptionOpts {
   keyVaultClient: <keyVaultClient>,
   keyVaultNamespace: "keyvault.datakeys",
   kmsProviders: { "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } },
}
```

Create a MongoClient named `encryptedClient` with these `AutoEncryptionOpts`:

```typescript
class AutoEncryptionOpts {
   keyVaultNamespace: "keyvault.datakeys",
   kmsProviders: { "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } },
   bypassQueryAnalysis: true,
}
```

#### Case 1: can insert encrypted indexed and find

Use `clientEncryption` to encrypt the value "encrypted indexed value" with these `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Indexed",
   contentionFactor: 0,
}
```

Store the result in `insertPayload`.

Use `encryptedClient` to insert the document `{ "encryptedIndexed": <insertPayload> }` into `db.explicit_encryption`.

Use `clientEncryption` to encrypt the value "encrypted indexed value" with these `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Indexed",
   queryType: "equality",
   contentionFactor: 0,
}
```

Store the result in `findPayload`.

Use `encryptedClient` to run a "find" operation on the `db.explicit_encryption` collection with the filter
`{ "encryptedIndexed": <findPayload> }`.

Assert one document is returned containing the field `{ "encryptedIndexed": "encrypted indexed value" }`.

#### Case 2: can insert encrypted indexed and find with non-zero contention

Use `clientEncryption` to encrypt the value "encrypted indexed value" with these `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Indexed",
   contentionFactor: 10,
}
```

Store the result in `insertPayload`.

Use `encryptedClient` to insert the document `{ "encryptedIndexed": <insertPayload> }` into `db.explicit_encryption`.

Repeat the above steps 10 times to insert 10 total documents. The `insertPayload` must be regenerated each iteration.

Use `clientEncryption` to encrypt the value "encrypted indexed value" with these `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Indexed",
   queryType: "equality",
   contentionFactor: 0,
}
```

Store the result in `findPayload`.

Use `encryptedClient` to run a "find" operation on the `db.explicit_encryption` collection with the filter
`{ "encryptedIndexed": <findPayload> }`.

Assert less than 10 documents are returned. 0 documents may be returned. Assert each returned document contains the
field `{ "encryptedIndexed": "encrypted indexed value" }`.

Use `clientEncryption` to encrypt the value "encrypted indexed value" with these `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Indexed",
   queryType: "equality",
   contentionFactor: 10,
}
```

Store the result in `findPayload2`.

Use `encryptedClient` to run a "find" operation on the `db.explicit_encryption` collection with the filter
`{ "encryptedIndexed": <findPayload2> }`.

Assert 10 documents are returned. Assert each returned document contains the field
`{ "encryptedIndexed": "encrypted indexed value" }`.

#### Case 3: can insert encrypted unindexed

Use `clientEncryption` to encrypt the value "encrypted unindexed value" with these `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Unindexed",
}
```

Store the result in `insertPayload`.

Use `encryptedClient` to insert the document `{ "_id": 1, "encryptedUnindexed": <insertPayload> }` into
`db.explicit_encryption`.

Use `encryptedClient` to run a "find" operation on the `db.explicit_encryption` collection with the filter
`{ "_id": 1 }`.

Assert one document is returned containing the field `{ "encryptedUnindexed": "encrypted unindexed value" }`.

#### Case 4: can roundtrip encrypted indexed

Use `clientEncryption` to encrypt the value "encrypted indexed value" with these `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Indexed",
   contentionFactor: 0,
}
```

Store the result in `payload`.

Use `clientEncryption` to decrypt `payload`. Assert the returned value equals "encrypted indexed value".

#### Case 5: can roundtrip encrypted unindexed

Use `clientEncryption` to encrypt the value "encrypted unindexed value" with these `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Unindexed",
}
```

Store the result in `payload`.

Use `clientEncryption` to decrypt `payload`. Assert the returned value equals "encrypted unindexed value".

### 13. Unique Index on keyAltNames

The following setup must occur before running each of the following test cases.

#### Setup

1. Create a `MongoClient` object (referred to as `client`).

2. Using `client`, drop the collection `keyvault.datakeys`.

3. Using `client`, create a unique index on `keyAltNames` with a partial index filter for only documents where
    `keyAltNames` exists using writeConcern "majority".

    The command should be equivalent to:

    ```typescript
    db.runCommand(
    {
        createIndexes: "datakeys",
        indexes: [
        {
            name: "keyAltNames_1",
            key: { "keyAltNames": 1 },
            unique: true,
            partialFilterExpression: { keyAltNames: { $exists: true } }
        }
        ],
        writeConcern: { w: "majority" }
    }
    )
    ```

4. Create a `ClientEncryption` object (referred to as `client_encryption`) with `client` set as the `keyVaultClient`.

5. Using `client_encryption`, create a data key with a `local` KMS provider and the keyAltName "def".

#### Case 1: createDataKey()

1. Use `client_encryption` to create a new local data key with a keyAltName "abc" and assert the operation does not
    fail.
2. Repeat Step 1 and assert the operation fails due to a duplicate key server error (error code 11000).
3. Use `client_encryption` to create a new local data key with a keyAltName "def" and assert the operation fails due to
    a duplicate key server error (error code 11000).

#### Case 2: addKeyAltName()

1. Use `client_encryption` to create a new local data key and assert the operation does not fail.
2. Use `client_encryption` to add a keyAltName "abc" to the key created in Step 1 and assert the operation does not
    fail.
3. Repeat Step 2, assert the operation does not fail, and assert the returned key document contains the keyAltName "abc"
    added in Step 2.
4. Use `client_encryption` to add a keyAltName "def" to the key created in Step 1 and assert the operation fails due to
    a duplicate key server error (error code 11000).
5. Use `client_encryption` to add a keyAltName "def" to the existing key, assert the operation does not fail, and assert
    the returned key document contains the keyAltName "def" added during Setup.

### 14. Decryption Events

Before running each of the following test cases, perform the following Test Setup.

#### Test Setup

Create a MongoClient named `setupClient`.

Drop and create the collection `db.decryption_events`.

Create a ClientEncryption object named `clientEncryption` with these options:

```typescript
class ClientEncryptionOpts {
   keyVaultClient: <setupClient>,
   keyVaultNamespace: "keyvault.datakeys",
   kmsProviders: { "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } },
}
```

Create a data key with the "local" KMS provider. Storing the result in a variable named `keyID`.

Use `clientEncryption` to encrypt the string "hello" with the following `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId: <keyID>,
   algorithm: "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic",
}
```

Store the result in a variable named `ciphertext`.

Copy `ciphertext` into a variable named `malformedCiphertext`. Change the last byte to a different value. This will
produce an invalid HMAC tag.

Create a MongoClient named `encryptedClient` with these `AutoEncryptionOpts`:

```typescript
class AutoEncryptionOpts {
   keyVaultNamespace: "keyvault.datakeys",
   kmsProviders: { "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } },
}
```

Configure `encryptedClient` with "retryReads=false". Register a listener for CommandSucceeded events on
`encryptedClient`. The listener must store the most recent `CommandSucceededEvent` reply for the "aggregate" command.
The listener must store the most recent `CommandFailedEvent` error for the "aggregate" command.

#### Case 1: Command Error

Use `setupClient` to configure the following failpoint:

```typescript
{
    "configureFailPoint": "failCommand",
    "mode": {
        "times": 1
    },
    "data": {
        "errorCode": 123,
        "failCommands": [
            "aggregate"
        ]
    }
}
```

Use `encryptedClient` to run an aggregate on `db.decryption_events`.

Expect an exception to be thrown from the command error. Expect a `CommandFailedEvent`.

#### Case 2: Network Error

Use `setupClient` to configure the following failpoint:

```typescript
{
    "configureFailPoint": "failCommand",
    "mode": {
        "times": 1
    },
    "data": {
        "errorCode": 123,
        "closeConnection": true,
        "failCommands": [
            "aggregate"
        ]
    }
}
```

Use `encryptedClient` to run an aggregate on `db.decryption_events`.

Expect an exception to be thrown from the network error. Expect a `CommandFailedEvent`.

#### Case 3: Decrypt Error

Use `encryptedClient` to insert the document `{ "encrypted": <malformedCiphertext> }` into `db.decryption_events`.

Use `encryptedClient` to run an aggregate on `db.decryption_events` with an empty pipeline.

Expect an exception to be thrown from the decryption error. Expect a `CommandSucceededEvent`. Expect the
`CommandSucceededEvent.reply` to contain BSON binary for the field `cursor.firstBatch.encrypted`.

#### Case 4: Decrypt Success

Use `encryptedClient` to insert the document `{ "encrypted": <ciphertext> }` into `db.decryption_events`.

Use `encryptedClient` to run an aggregate on `db.decryption_events` with an empty pipeline.

Expect no exception. Expect a `CommandSucceededEvent`. Expect the `CommandSucceededEvent.reply` to contain BSON binary
for the field `cursor.firstBatch.encrypted`.

### 15. On-demand AWS Credentials

These tests require valid AWS credentials. Refer:
[Automatic AWS Credentials](../client-side-encryption.md#automatic-credentials).

For these cases, create a [ClientEncryption](../client-side-encryption.md#clientencryption) object $C$ with the
following options:

```typescript
class ClientEncryptionOpts {
   keyVaultClient: <setupClient>,
   keyVaultNamespace: "keyvault.datakeys",
   kmsProviders: { "aws": {} },
}
```

#### Case 1: Failure

Do not run this test case in an environment where AWS credentials are available (e.g. via environment variables or a
metadata URL). (Refer: [Obtaining credentials for AWS](../../auth/auth.md#obtaining-credentials))

Attempt to create a datakey with $C$ using the `"aws"` KMS provider. Expect this to fail due to a lack of KMS provider
credentials.

#### Case 2: Success

For this test case, the environment variables `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` must be defined and set to
a valid set of AWS credentials.

Use the client encryption to create a datakey using the `"aws"` KMS provider. This should successfully load and use the
AWS credentials that were defined in the environment.

### 16. Rewrap

#### Case 1: Rewrap with separate ClientEncryption

When the following test case requests setting `masterKey`, use the following values based on the KMS provider:

For "aws":

```javascript
{
   "region": "us-east-1",
   "key": "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0"
}
```

For "azure":

```javascript
{
   "keyVaultEndpoint": "key-vault-csfle.vault.azure.net",
   "keyName": "key-name-csfle"
}
```

For "gcp":

```javascript
{
   "projectId": "devprod-drivers",
   "location": "global",
   "keyRing": "key-ring-csfle",
   "keyName": "key-name-csfle"
}
```

For "kmip":

```javascript
{}
```

For "local", do not set a masterKey document.

Run the following test case for each pair of KMS providers (referred to as `srcProvider` and `dstProvider`). Include
pairs where `srcProvider` equals `dstProvider`.

1. Drop the collection `keyvault.datakeys`.

2. Create a `ClientEncryption` object named `clientEncryption1` with these options:

    ```typescript
    class ClientEncryptionOpts {
       keyVaultClient: <new MongoClient>,
       keyVaultNamespace: "keyvault.datakeys",
       kmsProviders: <all KMS providers>,
    }
    ```

3. Call `clientEncryption1.createDataKey` with `srcProvider` and these options:

    ```typescript
    class DataKeyOpts {
       masterKey: <depends on srcProvider>,
    }
    ```

    Store the return value in `keyID`.

4. Call `clientEncryption1.encrypt` with the value "test" and these options:

    ```typescript
    class EncryptOpts {
       keyId : keyID,
       algorithm: "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic",
    }
    ```

    Store the return value in `ciphertext`.

5. Create a `ClientEncryption` object named `clientEncryption2` with these options:

    ```typescript
    class ClientEncryptionOpts {
       keyVaultClient: <new MongoClient>,
       keyVaultNamespace: "keyvault.datakeys",
       kmsProviders: <all KMS providers>,
    }
    ```

6. Call `clientEncryption2.rewrapManyDataKey` with an empty `filter` and these options:

    ```typescript
    class RewrapManyDataKeyOpts {
       provider: dstProvider,
       masterKey: <depends on dstProvider>,
    }
    ```

    Assert that the returned `RewrapManyDataKeyResult.bulkWriteResult.modifiedCount` is 1.

7. Call `clientEncryption1.decrypt` with the `ciphertext`. Assert the return value is "test".

8. Call `clientEncryption2.decrypt` with the `ciphertext`. Assert the return value is "test".

#### Case 2: RewrapManyDataKeyOpts.provider is not optional

Drivers MAY chose not to implement this prose test if their implementation of `RewrapManyDataKeyOpts` makes it
impossible by design to omit `RewrapManyDataKeyOpts.provider` when `RewrapManyDataKeyOpts.masterKey` is set.

1. Create a `ClientEncryption` object named `clientEncryption` with these options:

    ```typescript
    class ClientEncryptionOpts {
       keyVaultClient: <new MongoClient>,
       keyVaultNamespace: "keyvault.datakeys",
       kmsProviders: <all KMS providers>,
    }
    ```

2. Call `clientEncryption.rewrapManyDataKey` with an empty `filter` and these options:

    ```typescript
    class RewrapManyDataKeyOpts {
       masterKey: {}
    }
    ```

    Assert that `clientEncryption.rewrapManyDataKey` raises a client error indicating that the required
    `RewrapManyDataKeyOpts.provider` field is missing.

### 17. On-demand GCP Credentials

Refer: [Automatic GCP Credentials](../client-side-encryption.md#obtaining-gcp-credentials).

For these cases, create a [ClientEncryption](../client-side-encryption.md#clientencryption) object $C$ with the
following options:

```typescript
class ClientEncryptionOpts {
   keyVaultClient: <setupClient>,
   keyVaultNamespace: "keyvault.datakeys",
   kmsProviders: { "gcp": {} },
}
```

#### Case 1: Failure

Do not run this test case in an environment with a GCP service account is attached (e.g. any
[GCE equivalent runtime](https://google.aip.dev/auth/4115)). This may be run in an AWS EC2 instance.

Attempt to create a datakey with $C$ using the `"gcp"` KMS provider and following `DataKeyOpts`:

```typescript
class DataKeyOpts {
   masterKey: {
      "projectId": "devprod-drivers",
      "location": "global",
      "keyRing": "key-ring-csfle",
      "keyName": "key-name-csfle",
   }
}
```

Expect the attempt to obtain `"gcp"` credentials from the environment to fail.

#### Case 2: Success

This test case must run in a Google Compute Engine (GCE) Virtual Machine with a service account attached. See
[drivers-evergreen-tools/.evergreen/csfle/gcpkms](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/csfle/gcpkms)
for scripts to create a GCE instance for testing. The Evergreen task SHOULD set a `batchtime` of 14 days to reduce how
often this test case runs.

Attempt to create a datakey with $C$ using the `"gcp"` KMS provider and following `DataKeyOpts`:

```typescript
class DataKeyOpts {
   masterKey: {
      "projectId": "devprod-drivers",
      "location": "global",
      "keyRing": "key-ring-csfle",
      "keyName": "key-name-csfle",
   }
}
```

This should successfully load and use the GCP credentials of the service account attached to the virtual machine.

Expect the key to be successfully created.

### 18. Azure IMDS Credentials

Refer: [Automatic Azure Credentials](../client-side-encryption.md#obtaining-an-access-token-for-azure-key-vault)

The test cases for IMDS communication are specially designed to not require an Azure environment, while still exercising
the core of the functionality. The design of these test cases encourages an implementation to separate the concerns of
IMDS communication from the logic of KMS key manipulation. The purpose of these test cases is to ensure drivers will
behave appropriately regardless of the behavior of the IMDS server.

For these IMDS credentials tests, a simple stand-in IMDS-imitating HTTP server is available in drivers-evergreen-tools,
at `.evergreen/csfle/fake_azure.py`. `fake_azure.py` is a very simple `bottle.py` application. For the easiest use, it
is recommended to execute it through `bottle.py` (which is a sibling file in the same directory):

```shell
python .evergreen/csfle/bottle.py fake_azure:imds
```

This will run the `imds` Bottle application defined in the `fake_azure` Python module. `bottle.py` accepts additional
command line arguments to control the bind host and TCP port (use `--help` for more information).

For each test case, follow the process for obtaining the token as outlined in the
[automatic Azure credentials section](../client-side-encryption.md#obtaining-an-access-token-for-azure-key-vault) with
the following changes:

1. Instead of the standard IMDS TCP endpoint of `169.254.169.254:80`, communicate with the running `fake_azure` HTTP
    server.
2. For each test case, the behavior of the server may be controlled by attaching an additional HTTP header to the sent
    request: `X-MongoDB-HTTP-TestParams`.

#### Case 1: Success

Do not set an `X-MongoDB-HTTP-TestParams` header.

Upon receiving a response from `fake_azure`, the driver must decode the following information:

1. HTTP status will be `200 Okay`.
2. The HTTP body will be a valid JSON string.
3. The access token will be the string `"magic-cookie"`.
4. The expiry duration of the token will be seventy seconds.
5. The token will have a resource of `"https://vault.azure.net"`

#### Case 2: Empty JSON

This case addresses a server returning valid JSON with invalid content.

Set `X-MongoDB-HTTP-TestParams` to `case=empty-json`.

Upon receiving a response:

1. HTTP status will be `200 Okay`
2. The HTTP body will be a valid JSON string.
3. There will be no access token, expiry duration, or resource.

The test case should ensure that this error condition is handled gracefully.

#### Case 3: Bad JSON

This case addresses a server returning malformed JSON.

Set `X-MongoDB-HTTP-TestParams` to `case=bad-json`.

Upon receiving a response:

1. HTTP status will be `200 Okay`
2. The response body will contain a malformed JSON string.

The test case should ensure that this error condition is handled gracefully.

#### Case 4: HTTP 404

This case addresses a server returning a "Not Found" response. This is documented to occur spuriously within an Azure
environment.

Set `X-MongoDB-HTTP-TestParams` to `case=404`.

Upon receiving a response:

1. HTTP status will be `404 Not Found`.
2. The response body is unspecified.

The test case should ensure that this error condition is handled gracefully.

#### Case 5: HTTP 500

This case addresses an IMDS server reporting an internal error. This is documented to occur spuriously within an Azure
environment.

Set `X-MongoDB-HTTP-TestParams` to `case=500`.

Upon receiving a response:

1. HTTP status code will be `500`.
2. The response body is unspecified.

The test case should ensure that this error condition is handled gracefully.

#### Case 6: Slow Response

This case addresses an IMDS server responding very slowly. Drivers should not halt the application waiting on a peer to
communicate.

Set `X-MongoDB-HTTP-TestParams` to `case=slow`.

The HTTP response from the `fake_azure` server will take at least 1000 seconds to complete. The request should fail with
a timeout.

### 19. Azure IMDS Credentials Integration Test

Refer: [Automatic Azure Credentials](../client-side-encryption.md#obtaining-an-access-token-for-azure-key-vault)

For these cases, create a [ClientEncryption](../client-side-encryption.md#clientencryption) object $C$ with the
following options:

```typescript
class ClientEncryptionOpts {
   keyVaultClient: <setupClient>,
   keyVaultNamespace: "keyvault.datakeys",
   kmsProviders: { "azure": {} },
}
```

#### Case 1: Failure

Do not run this test case in an Azure environment with an attached identity. This may be run in an AWS EC2 instance.

Attempt to create a datakey with $C$ using the `"azure"` KMS provider and following `DataKeyOpts`:

```typescript
class DataKeyOpts {
   masterKey: {
      "keyVaultEndpoint": "https://keyvault-drivers-2411.vault.azure.net/keys/",
      "keyName": "KEY-NAME",
   }
}
```

Expect the attempt to obtain `"azure"` credentials from the environment to fail.

#### Case 2: Success

This test case must run in an Azure environment with an attached identity. See
[drivers-evergreen-tools/.evergreen/csfle/azurekms](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/csfle/azurekms)
for scripts to create a Azure instance for testing. The Evergreen task SHOULD set a `batchtime` of 14 days to reduce how
often this test case runs.

Attempt to create a datakey with $C$ using the `"azure"` KMS provider and following `DataKeyOpts`:

```typescript
class DataKeyOpts {
   masterKey: {
      "keyVaultEndpoint": "https://keyvault-drivers-2411.vault.azure.net/keys/",
      "keyName": "KEY-NAME",
   }
}
```

This should successfully load and use the Azure credentials of the service account attached to the virtual machine.

Expect the key to be successfully created.

### 20. Bypass creating mongocryptd client when shared library is loaded

> [!NOTE]
> IMPORTANT: If [crypt_shared](../client-side-encryption.md#crypt_shared) is not visible to the operating system's
> library search mechanism, this test should be skipped.

The following tests that a mongocryptd client is not created when shared library is in-use.

1. Start a new thread (referred to as `listenerThread`)

2. On `listenerThread`, create a TcpListener on 127.0.0.1 endpoint and port 27021. Start the listener and wait for
    establishing connections. If any connection is established, then signal about this to the main thread.

    Drivers MAY pass a different port if they expect their testing infrastructure to be using port 27021. Pass a port
    that should be free.

3. Create a MongoClient configured with auto encryption (referred to as `client_encrypted`)

    Configure the required options. Use the `local` KMS provider as follows:

    ```javascript
    { "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } }
    ```

    Configure with the `keyVaultNamespace` set to `keyvault.datakeys`.

    Configure the following `extraOptions`:

    ```javascript
    {
      "mongocryptdURI": "mongodb://localhost:27021/?serverSelectionTimeoutMS=1000"
    }
    ```

4. Use `client_encrypted` to insert the document `{"unencrypted": "test"}` into `db.coll`.

5. Expect no signal from `listenerThread`.

### 21. Automatic Data Encryption Keys

The Automatic Data Encryption Keys tests require MongoDB server 7.0+. The tests must not run against a standalone.

> [!NOTE]
> MongoDB Server 7.0 introduced a backwards breaking change to the Queryable Encryption (QE) protocol: QEv2.
> libmongocrypt 1.8.0 is configured to use the QEv2 protocol.

For each of the following test cases, assume `DB` is a valid open database handle, and assume a
[ClientEncryption](../client-side-encryption.md#clientencryption) object `CE` created using the following options:

```javascript
clientEncryptionOptions: {
   keyVaultClient: <new MongoClient>,
   keyVaultNamespace: "keyvault.datakeys",
   kmsProviders: {
      local: { key: base64Decode(LOCAL_MASTERKEY) },
      aws: {
         accessKeyId: <set from environment>,
         secretAccessKey: <set from environment>
      },
   },
}
```

Run each test case with each of these KMS providers: `aws`, `local`. The KMS provider name is referred to as
`kmsProvider`. When testing `aws`, use the following as the `masterKey` option:

```javascript
{
   region: "us-east-1",
   key: "arn:aws:kms:us-east-1:579766882180:key/89fcc2c4-08b0-4bd9-9f25-e30687b580d0"
}
```

When testing `local`, set `masterKey` to `null`.

#### Case 1: Simple Creation and Validation

This test is the most basic to verify that
[CreateEncryptedCollection](../client-side-encryption.md#create-encrypted-collection-helper) created a collection with
queryable encryption enabled. It verifies that the server rejects an attempt to insert plaintext in an encrypted fields.

1. Create a new create-collection options $Opts$ including the following:

    ```typescript
    {
       encryptedFields: {
          fields: [{
             path: "ssn",
             bsonType: "string",
             keyId: null
          }]
       }
    }
    ```

2. Invoke $CreateEncryptedCollection(CE, DB, "testing1", Opts, kmsProvider, masterKey)$ to obtain a new collection
    $Coll$. Expect success.

3. Attempt to insert the following document into `Coll`:

    ```typescript
    {
       ssn: "123-45-6789"
    }
    ```

4. Expect an error from the insert operation that indicates that the document failed validation. This error indicates
    that the server expects to receive an encrypted field for `ssn`, but we tried to insert a plaintext field via a
    client that is unaware of the encryption requirements.

#### Case 2: Missing `encryptedFields`

The [CreateEncryptedCollection](../client-side-encryption.md#create-encrypted-collection-helper) helper should not
create a regular collection if there are no `encryptedFields` for the collection being created. Instead, it should
generate an error indicated that the `encryptedFields` option is missing.

1. Create a new empty create-collection options $Opts$. (i.e. it must not contain any `encryptedFields` options.)
2. Invoke $CreateEncryptedCollection(CE, DB, "testing1", Opts, kmsProvider, masterKey)$.
3. Expect the invocation to fail with an error indicating that `encryptedFields` is not defined for the collection, and
    expect that no collection was created within the database. It would be *incorrect* for
    [CreateEncryptedCollection](../client-side-encryption.md#create-encrypted-collection-helper) to create a regular
    collection without queryable encryption enabled.

#### Case 3: Invalid `keyId`

The [CreateEncryptedCollection](../client-side-encryption.md#create-encrypted-collection-helper) helper only inspects
`encryptedFields.fields` for `keyId` of `null`.
[CreateEncryptedCollection](../client-side-encryption.md#create-encrypted-collection-helper) should forward all other
data as-is, even if it would be malformed. The server should generate an error when attempting to create a collection
with such invalid settings.

> [!NOTE]
> This test is not required if the type system of the driver has a compile-time check that fields' `keyId`s are of the
> correct type.

1. Create a new create-collection options $Opts$ including the following:

    ```typescript
    {
       encryptedFields: {
          fields: [{
             path: "ssn",
             bsonType: "string",
             keyId: false,
          }]
       }
    }
    ```

2. Invoke $CreateEncryptedCollection(CE, DB, "testing1", Opts, kmsProvider, masterKey)$.

3. Expect an error from the server indicating a validation error at `create.encryptedFields.fields.keyId`, which must be
    a UUID and not a boolean value.

#### Case 4: Insert encrypted value

This test is continuation of the case 1 and provides a way to complete inserting with encrypted value.

1. Create a new create-collection options $Opts$ including the following:

    ```typescript
    {
       encryptedFields: {
          fields: [{
             path: "ssn",
             bsonType: "string",
             keyId: null
          }]
       }
    }
    ```

2. Invoke $CreateEncryptedCollection(CE, DB, "testing1", Opts, kmsProvider, masterKey)$ to obtain a new collection
    $Coll$ and data key $key1$. Expect success.

3. Use $CE$ to explicitly encrypt the string "123-45-6789" using algorithm $Unindexed$ and data key $key1$. Refer result
    as $encryptedPayload$.

4. Attempt to insert the following document into `Coll`:

    ```typescript
    {
       ssn: <encryptedPayload>
    }
    ```

    Expect success.

### 22. Range Explicit Encryption

The Range Explicit Encryption tests utilize Queryable Encryption (QE) range protocol V2 and require MongoDB server
8.0.0-rc14+ for [SERVER-91889](https://jira.mongodb.org/browse/SERVER-91889) and libmongocrypt 1.11.0+ for
[MONGOCRYPT-705](https://jira.mongodb.org/browse/MONGOCRYPT-705). The tests must not run against a standalone.

Each of the following test cases must pass for each of the supported types (`DecimalNoPrecision`, `DecimalPrecision`,
`DoublePrecision`, `DoubleNoPrecision`, `Date`, `Int`, and `Long`), unless it is stated the type should be skipped.

Tests for `DecimalNoPrecision` must only run against a replica set. `DecimalNoPrecision` queries are expected to take a
long time and may exceed the default mongos timeout.

Before running each of the following test cases, perform the following Test Setup.

#### Test Setup

Load the file for the specific data type being tested `range-encryptedFields-<type>.json`. For example, for `Int` load
[range-encryptedFields-Int.json](https://github.com/mongodb/specifications/blob/master/source/client-side-encryption/etc/data/range-encryptedFields-Int.json)
as `encryptedFields`.

Load the file
[key1-document.json](https://github.com/mongodb/specifications/tree/master/source/client-side-encryption/etc/data/keys/key1-document.json)
as `key1Document`.

Read the `"_id"` field of `key1Document` as `key1ID`.

Drop and create the collection `db.explicit_encryption` using `encryptedFields` as an option. See
[FLE 2 CreateCollection() and Collection.Drop()](../client-side-encryption.md#create-collection-helper).

Drop and create the collection `keyvault.datakeys`.

Insert `key1Document` in `keyvault.datakeys` with majority write concern.

Create a MongoClient named `keyVaultClient`.

Create a ClientEncryption object named `clientEncryption` with these options:

```typescript
class ClientEncryptionOpts {
   keyVaultClient: <keyVaultClient>,
   keyVaultNamespace: "keyvault.datakeys",
   kmsProviders: { "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } },
}
```

Create a MongoClient named `encryptedClient` with these `AutoEncryptionOpts`:

```typescript
class AutoEncryptionOpts {
   keyVaultNamespace: "keyvault.datakeys",
   kmsProviders: { "local": { "key": <base64 decoding of LOCAL_MASTERKEY> } },
   bypassQueryAnalysis: true,
}
```

The remaining tasks require setting `RangeOpts`. [Test Setup: RangeOpts](#test-setup-rangeopts) lists the values to use
for `RangeOpts` for each of the supported data types.

Use `clientEncryption` to encrypt these values: 0, 6, 30, and 200. Ensure the type matches that of the encrypted field.
For example, if the encrypted field is `encryptedDoubleNoPrecision` encrypt the value 6.0.

Encrypt using the following `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Range",
   contentionFactor: 0,
   rangeOpts: <RangeOpts for Type>,
}
```

Use `encryptedClient` to insert the following documents into `db.explicit_encryption`:

```javascript
{ "_id": 0, "encrypted<Type>": <encrypted 0> }
{ "_id": 1, "encrypted<Type>": <encrypted 6> }
{ "_id": 2, "encrypted<Type>": <encrypted 30> }
{ "_id": 3, "encrypted<Type>": <encrypted 200> }
```

#### Test Setup: RangeOpts

This section lists the values to use for `RangeOpts` for each of the supported data types, since each data type requires
a different `RangeOpts`.

Each test listed in the cases below must pass for all supported data types unless it is stated the type should be
skipped.

1. DecimalNoPrecision

    ```typescript
    class RangeOpts {
       trimFactor: 1,
       sparsity: 1,
    }
    ```

2. DecimalPrecision

    ```typescript
    class RangeOpts {
       min: { "$numberDecimal": "0" },
       max: { "$numberDecimal": "200" },
       trimFactor: 1,
       sparsity: 1,
       precision: 2,
    }
    ```

3. DoubleNoPrecision

    ```typescript
    class RangeOpts {
       trimFactor: 1
       sparsity: 1,
    }
    ```

4. DoublePrecision

    ```typescript
    class RangeOpts {
       min: { "$numberDouble": "0" },
       max: { "$numberDouble": "200" },
       trimFactor: 1,
       sparsity: 1,
       precision: 2,
    }
    ```

5. Date

    ```typescript
    class RangeOpts {
       min: {"$date": { "$numberLong": "0" } } ,
       max: {"$date": { "$numberLong": "200" } },
       trimFactor: 1,
       sparsity: 1,
    }
    ```

6. Int

    ```typescript
    class RangeOpts {
       min: {"$numberInt": "0" } ,
       max: {"$numberInt": "200" },
       trimFactor: 1,
       sparsity: 1,
    }
    ```

7. Long

    ```typescript
    class RangeOpts {
       min: {"$numberLong": "0" } ,
       max: {"$numberLong": "200" },
       trimFactor: 1,
       sparsity: 1,
    }
    ```

#### Case 1: can decrypt a payload

Use `clientEncryption.encrypt()` to encrypt the value 6. Ensure the type matches that of the encrypted field. For
example, if the encrypted field is `encryptedLong` encrypt a BSON int64 type, not a BSON int32 type.

Encrypt using the following `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Range",
   contentionFactor: 0,
   rangeOpts: <RangeOpts for Type>,
}
```

Store the result in `insertPayload`.

Use `clientEncryption` to decrypt `insertPayload`. Assert the returned value equals 6 and has the expected type.

> [!NOTE]
> The type returned by `clientEncryption.decrypt()` may differ from the input type to `clientEncryption.encrypt()`
> depending on how the driver unmarshals BSON numerics to language native types. Example: a driver may unmarshal a BSON
> int64 to a numeric type that does not distinguish between int64 and int32.

#### Case 2: can find encrypted range and return the maximum

Use `clientEncryption.encryptExpression()` to encrypt this query:

```javascript
// Convert 6 and 200 to the encrypted field type
{ "$and": [ { "encrypted<Type>": { "$gte": 6 } }, { "encrypted<Type>": { "$lte": 200 } } ] }
```

Encrypt using the following `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Range",
   queryType: "range",
   contentionFactor: 0,
   rangeOpts: <RangeOpts for Type>,
}
```

Store the result in `findPayload`.

Use `encryptedClient` to run a "find" operation on the `db.explicit_encryption` collection with the filter `findPayload`
and sort the results by `_id`.

Assert the following three documents are returned:

```javascript
// Convert 6, 30, and 200 to the encrypted field type
{ "_id": 1, "encrypted<Type>": 6 }
{ "_id": 2, "encrypted<Type>": 30 }
{ "_id": 3, "encrypted<Type>": 200 }
```

#### Case 3: can find encrypted range and return the minimum

Use `clientEncryption.encryptExpression()` to encrypt this query:

```javascript
// Convert 0 and 6 to the encrypted field type
{ "$and": [ { "encrypted<Type>": { "$gte": 0 } }, { "encrypted<Type>": { "$lte": 6 } } ] }
```

Encrypt using the following `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Range",
   queryType: "range",
   contentionFactor: 0,
   rangeOpts: <RangeOpts for Type>,
}
```

Store the result in `findPayload`.

Use `encryptedClient` to run a "find" operation on the `db.explicit_encryption` collection with the filter `findPayload`
and sort the results by `_id`.

Assert the following two documents are returned:

```javascript
// Convert 0 and 6 to the encrypted field type
{ "_id": 0, "encrypted<Type>": 0 }
{ "_id": 1, "encrypted<Type>": 6 }
```

#### Case 4: can find encrypted range with an open range query

Use `clientEncryption.encryptExpression()` to encrypt this query:

```javascript
// Convert 30 to the encrypted field type
{ "$and": [ { "encrypted<Type>": { "$gt": 30 } } ] }
```

Encrypt using the following `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Range",
   queryType: "range",
   contentionFactor: 0,
   rangeOpts: <RangeOpts for Type>,
}
```

Store the result in `findPayload`.

Use `encryptedClient` to run a "find" operation on the `db.explicit_encryption` collection with the filter `findPayload`
and sort the results by `_id`.

Assert the following document is returned:

```javascript
// Convert 200 to the encrypted field type
{ "_id": 3, "encrypted<Type>": 200 }
```

#### Case 5: can run an aggregation expression inside $expr

Use `clientEncryption.encryptExpression()` to encrypt this query:

```javascript
// Convert 30 to the encrypted field type
{ "$and": [ { "$lt": [ "$encrypted<Type>", 30 ] } ] } }
```

Encrypt using the following `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Range",
   queryType: "range",
   contentionFactor: 0,
   rangeOpts: <RangeOpts for Type>,
}
```

Store the result in `findPayload`.

Use `encryptedClient` to run a "find" operation on the `db.explicit_encryption` collection with the filter
`{ "$expr": <findPayload> }` and sort the results by `_id`.

Assert the following two documents are returned:

```javascript
// Convert 0 and 6 to the encrypted field type
{ "_id": 0, "encrypted<Type>": 0 }
{ "_id": 1, "encrypted<Type>": 6 }
```

#### Case 6: encrypting a document greater than the maximum errors

This test case should be skipped if the encrypted field is `encryptedDoubleNoPrecision` or
`encryptedDecimalNoPrecision`.

Use `clientEncryption.encrypt()` to encrypt the value 201. Ensure the type matches that of the encrypted field.

Encrypt using the following `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Range",
   contentionFactor: 0,
   rangeOpts: <RangeOpts for Type>,
}
```

Assert that an error was raised because 201 is greater than the maximum value in `RangeOpts`.

#### Case 7: encrypting a value of a different type errors

This test case should be skipped if the encrypted field is `encryptedDoubleNoPrecision` or
`encryptedDecimalNoPrecision`.

Use `clientEncryption.encrypt()` to encrypt the value 6 with a type that does not match that of the encrypted field.

If the encrypted field is `encryptedInt` use a BSON double type. Otherwise, use a BSON int32 type.

Encrypt using the following `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Range",
   contentionFactor: 0,
   rangeOpts: <RangeOpts for Type>,
}
```

Ensure that `RangeOpts` corresponds to the type of the encrypted field (i.e. expected type) and not that of the value
being passed to `clientEncryption.encrypt()`.

Assert that an error was raised.

#### Case 8: setting precision errors if the type is not double or Decimal128

This test case should be skipped if the encrypted field is `encryptedDoublePrecision`, `encryptedDoubleNoPrecision`,
`encryptedDecimalPrecision`, or `encryptedDecimalNoPrecision`.

Use `clientEncryption.encrypt()` to encrypt the value 6. Ensure the type matches that of the encrypted field.

Add `{ precision: 2 }` to the encrypted field's `RangeOpts` (see: [Test Setup: RangeOpts](#test-setup-rangeopts)).

Encrypt using the following `EncryptOpts`:

```typescript
class EncryptOpts {
   keyId : <key1ID>,
   algorithm: "Range",
   contentionFactor: 0,
   rangeOpts: <RangeOpts for Type with precision added>,
}
```

Assert that an error was raised.

### 23. Range Explicit Encryption applies defaults

This test requires libmongocrypt with changes in
[14ccd9ce](https://github.com/mongodb/libmongocrypt/commit/14ccd9ce8a030158aec07f63e8139d34b95d88e6)
([MONGOCRYPT-698](https://jira.mongodb.org/browse/MONGOCRYPT-698)).

#### Test Setup

Create a MongoClient named `keyVaultClient`.

Create a ClientEncryption object named `clientEncryption` with these options:

```typescript
class ClientEncryptionOpts {
   keyVaultClient: keyVaultClient,
   keyVaultNamespace: "keyvault.datakeys",
   kmsProviders: { "local": { "key": "<base64 decoding of LOCAL_MASTERKEY>" } },
}
```

Create a key with `clientEncryption.createDataKey`. Store the returned key ID in a variable named `keyId`.

Call `clientEncryption.encrypt` to encrypt the int32 value `123` with these options:

```typescript
class EncryptOpts {
   keyId : keyId,
   algorithm: "Range",
   contentionFactor: 0,
   rangeOpts: RangeOpts {
      min: 0,
      max: 1000
   }
}
```

Store the result in a variable named `payload_defaults`.

#### Case 1: Uses libmongocrypt defaults

Call `clientEncryption.encrypt` to encrypt the int32 value `123` with these options:

```typescript
class EncryptOpts {
   keyId : keyId,
   algorithm: "Range",
   contentionFactor: 0,
   rangeOpts: RangeOpts {
      min: 0,
      max: 1000,
      sparsity: 2,
      trimFactor: 6
   }
}
```

Assert the returned payload size equals the size of `payload_defaults`.

> [!NOTE]
> Do not compare the payload contents. The payloads include random data. The `trimFactor` and `sparsity` directly affect
> the payload size.

#### Case 2: Accepts `trimFactor` 0

Call `clientEncryption.encrypt` to encrypt the int32 value `123` with these options:

```typescript
class EncryptOpts {
   keyId : keyId,
   algorithm: "Range",
   contentionFactor: 0,
   rangeOpts: RangeOpts {
      min: 0,
      max: 1000,
      trimFactor: 0
   }
}
```

Assert the returned payload size is greater than the size of `payload_defaults`.

> [!NOTE]
> Do not compare the payload contents. The payloads include random data. The `trimFactor` and `sparsity` directly affect
> the payload size.

### 24. KMS Retry Tests

The following tests that certain AWS, Azure, and GCP KMS operations are retried on transient errors.

This test uses a mock server with configurable failpoints to simulate network failures. To start the server:

```shell
python -u kms_failpoint_server.py --port 9003
```

See the [TLS tests](#10-kms-tls-tests) for running the mock server on Evergreen. See
[the mock server implementation](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/4ba50d373652b6fb39239745664637e33e2b01e6/.evergreen/csfle/kms_failpoint_server.py)
and the
[C driver tests](https://github.com/mongodb/mongo-c-driver/blob/d934cd5de55af65220816e4fd01ce3f9c0ef1cd4/src/libmongoc/tests/test-mongoc-client-side-encryption.c#L6295)
for how to configure failpoints.

#### Setup

1. Start a `mongod` process with **server version 4.2.0 or later**.
2. Start the failpoint KMS server with: `python -u kms_failpoint_server.py --port 9003`.
3. Create a `MongoClient` for key vault operations.
4. Create a `ClientEncryption` object (referred to as `client_encryption`) with `keyVaultNamespace` set to
    `keyvault.datakeys`.

The failpoint server is configured using HTTP requests. Example request to simulate a network failure:

`curl -X POST https://localhost:9003/set_failpoint/network -d '{"count": 1}' --cacert drivers-evergreen-tools/.evergreen/x509gen/ca.pem`

To simulate an HTTP failure, replace `network` with `http`.

When the following test cases request setting `masterKey`, use the following values based on the KMS provider:

For "aws":

```javascript
{
   "region": "foo",
   "key": "bar",
   "endpoint": "127.0.0.1:9003",
}
```

For "azure":

```javascript
{
   "keyVaultEndpoint": "127.0.0.1:9003",
   "keyName": "foo",
}
```

For "gcp":

```javascript
{
   "projectId": "foo",
   "location": "bar",
   "keyRing": "baz",
   "keyName": "qux",
   "endpoint": "127.0.0.1:9003"
}
```

#### Case 1: createDataKey and encrypt with TCP retry

1. Configure the mock server to simulate one network failure.
2. Call `client_encryption.createDataKey()` with "aws" as the provider. Expect this to succeed. Store the returned key
    ID in a variable named `keyId`.
3. Configure the mock server to simulate another network failure.
4. Call `clientEncryption.encrypt` with the following `EncryptOpts` to encrypt the int32 value `123` with the newly
    created key:
    ```typescript
    class EncryptOpts {
       keyId : <keyID>,
       algorithm: "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic",
    }
    ```
    Expect this to succeed.

Repeat this test with the `azure` and `gcp` masterKeys.

#### Case 2: createDataKey and encrypt with HTTP retry

1. Configure the mock server to simulate one HTTP failure.
2. Call `client_encryption.createDataKey()` with "aws" as the provider. Expect this to succeed. Store the returned key
    ID in a variable named `keyId`.
3. Configure the mock server to simulate another HTTP failure.
4. Call `clientEncryption.encrypt` with the following `EncryptOpts` to encrypt the int32 value `123` with the newly
    created key:
    ```typescript
    class EncryptOpts {
       keyId : <keyID>,
       algorithm: "AEAD_AES_256_CBC_HMAC_SHA_512-Deterministic",
    }
    ```
    Expect this to succeed.

Repeat this test with the `azure` and `gcp` masterKeys.

#### Case 3: createDataKey fails after too many retries

1. Configure the mock server to simulate four network failures.
2. Call `client_encryption.createDataKey()` with "aws" as the provider. Expect this to fail.

Repeat this test with the `azure` and `gcp` masterKeys.

### 25. Test $lookup

All tests require libmongocrypt 1.13.0, server 7.0+, and must be skipped on standalone. Tests define more constraints.

The syntax `<filename.json>` is used to refer to the content of the corresponding file in `../etc/data/lookup`.

#### Setup

Create an encrypted MongoClient named `encryptedClient` configured with:

```python
AutoEncryptionOpts(
    keyVaultNamespace="db.keyvault",
    kmsProviders={"local": { "key": "<base64 decoding of LOCAL_MASTERKEY>" }}
)
```

Use `encryptedClient` to drop `db.keyvault`. Insert `<key-doc.json>` into `db.keyvault` with majority write concern.

Use `encryptedClient` to drop and create the following collections:

- `db.csfle` with options: `{ "validator": { "$jsonSchema": "<schema-csfle.json>"}}`.
- `db.csfle2` with options: `{ "validator": { "$jsonSchema": "<schema-csfle2.json>"}}`.
- `db.qe` with options: `{ "encryptedFields": "<schema-qe.json>"}`.
- `db.qe2` with options: `{ "encryptedFields": "<schema-qe2.json>"}`.
- `db.no_schema` with no options.
- `db.no_schema2` with no options.

Create an unencrypted MongoClient named `unencryptedClient`.

Insert documents with `encryptedClient`:

- `{"csfle": "csfle"}` into `db.csfle`
    - Use `unencryptedClient` to retrieve it. Assert the `csfle` field is BSON binary.
- `{"csfle2": "csfle2"}` into `db.csfle2`
    - Use `unencryptedClient` to retrieve it. Assert the `csfle2` field is BSON binary.
- `{"qe": "qe"}` into `db.qe`
    - Use `unencryptedClient` to retrieve it. Assert the `qe` field is BSON binary.
- `{"qe2": "qe2"}` into `db.qe2`
    - Use `unencryptedClient` to retrieve it. Assert the `qe2` field is BSON binary.
- `{"no_schema": "no_schema"}` into `db.no_schema`
- `{"no_schema2": "no_schema2"}` into `db.no_schema2`

#### Case 1: `db.csfle` joins `db.no_schema`

Test requires server 8.1+ and mongocryptd/crypt_shared 8.1+.

Recreate `encryptedClient` with the same `AutoEncryptionOpts` as the setup. (Recreating prevents schema caching from
impacting the test).

Run an aggregate operation on `db.csfle` with the following pipeline:

```json
[
    {"$match" : {"csfle" : "csfle"}},
    {
        "$lookup" : {
            "from" : "no_schema",
            "as" : "matched",
            "pipeline" : [ {"$match" : {"no_schema" : "no_schema"}}, {"$project" : {"_id" : 0}} ]
        }
    },
    {"$project" : {"_id" : 0}}
]
```

Expect one document to be returned matching: `{"csfle" : "csfle", "matched" : [ {"no_schema" : "no_schema"} ]}`.

#### Case 2: `db.qe` joins `db.no_schema`

Test requires server 8.1+ and mongocryptd/crypt_shared 8.1+.

Recreate `encryptedClient` with the same `AutoEncryptionOpts` as the setup. (Recreating prevents schema caching from
impacting the test).

Run an aggregate operation on `db.qe` with the following pipeline:

```json
[
    {"$match" : {"qe" : "qe"}},
    {
       "$lookup" : {
          "from" : "no_schema",
          "as" : "matched",
          "pipeline" :
             [ {"$match" : {"no_schema" : "no_schema"}}, {"$project" : {"_id" : 0, "__safeContent__" : 0}} ]
       }
    },
    {"$project" : {"_id" : 0, "__safeContent__" : 0}}
]
```

Expect one document to be returned matching: `{"qe" : "qe", "matched" : [ {"no_schema" : "no_schema"} ]}`.

#### Case 3: `db.no_schema` joins `db.csfle`

Test requires server 8.1+ and mongocryptd/crypt_shared 8.1+.

Recreate `encryptedClient` with the same `AutoEncryptionOpts` as the setup. (Recreating prevents schema caching from
impacting the test).

Run an aggregate operation on `db.no_schema` with the following pipeline:

```json
[
    {"$match" : {"no_schema" : "no_schema"}},
    {
        "$lookup" : {
            "from" : "csfle",
            "as" : "matched",
            "pipeline" : [ {"$match" : {"csfle" : "csfle"}}, {"$project" : {"_id" : 0}} ]
        }
    },
    {"$project" : {"_id" : 0}}
]
```

Expect one document to be returned matching: `{"no_schema" : "no_schema", "matched" : [ {"csfle" : "csfle"} ]}`.

#### Case 4: `db.no_schema` joins `db.qe`

Test requires server 8.1+ and mongocryptd/crypt_shared 8.1+.

Recreate `encryptedClient` with the same `AutoEncryptionOpts` as the setup. (Recreating prevents schema caching from
impacting the test).

Run an aggregate operation on `db.no_schema` with the following pipeline:

```json
[
   {"$match" : {"no_schema" : "no_schema"}},
   {
      "$lookup" : {
         "from" : "qe",
         "as" : "matched",
         "pipeline" : [ {"$match" : {"qe" : "qe"}}, {"$project" : {"_id" : 0, "__safeContent__" : 0}} ]
      }
   },
   {"$project" : {"_id" : 0}}
]
```

Expect one document to be returned matching: `{"no_schema" : "no_schema", "matched" : [ {"qe" : "qe"} ]}`.

#### Case 5: `db.csfle` joins `db.csfle2`

Test requires server 8.1+ and mongocryptd/crypt_shared 8.1+.

Recreate `encryptedClient` with the same `AutoEncryptionOpts` as the setup. (Recreating prevents schema caching from
impacting the test).

Run an aggregate operation on `db.csfle` with the following pipeline:

```json
[
   {"$match" : {"csfle" : "csfle"}},
   {
      "$lookup" : {
         "from" : "csfle2",
         "as" : "matched",
         "pipeline" : [ {"$match" : {"csfle2" : "csfle2"}}, {"$project" : {"_id" : 0}} ]
      }
   },
   {"$project" : {"_id" : 0}}
]
```

Expect one document to be returned matching: `{"csfle" : "csfle", "matched" : [ {"csfle2" : "csfle2"} ]}`.

#### Case 6: `db.qe` joins `db.qe2`

Test requires server 8.1+ and mongocryptd/crypt_shared 8.1+.

Recreate `encryptedClient` with the same `AutoEncryptionOpts` as the setup. (Recreating prevents schema caching from
impacting the test).

Run an aggregate operation on `db.qe` with the following pipeline:

```json
[
   {"$match" : {"qe" : "qe"}},
   {
      "$lookup" : {
         "from" : "qe2",
         "as" : "matched",
         "pipeline" : [ {"$match" : {"qe2" : "qe2"}}, {"$project" : {"_id" : 0, "__safeContent__" : 0}} ]
      }
   },
   {"$project" : {"_id" : 0, "__safeContent__" : 0}}
]
```

Expect one document to be returned matching: `{"qe" : "qe", "matched" : [ {"qe2" : "qe2"} ]}`.

#### Case 7: `db.no_schema` joins `db.no_schema2`

Test requires server 8.1+ and mongocryptd/crypt_shared 8.1+.

Recreate `encryptedClient` with the same `AutoEncryptionOpts` as the setup. (Recreating prevents schema caching from
impacting the test).

Run an aggregate operation on `db.no_schema` with the following pipeline:

```json
[
    {"$match" : {"no_schema" : "no_schema"}},
    {
        "$lookup" : {
            "from" : "no_schema2",
            "as" : "matched",
            "pipeline" : [ {"$match" : {"no_schema2" : "no_schema2"}}, {"$project" : {"_id" : 0}} ]
        }
    },
    {"$project" : {"_id" : 0}}
]
```

Expect one document to be returned matching:
`{"no_schema" : "no_schema", "matched" : [ {"no_schema2" : "no_schema2"} ]}`.

#### Case 8: `db.csfle` joins `db.qe`

Test requires server 8.1+ and mongocryptd/crypt_shared 8.1+.

Recreate `encryptedClient` with the same `AutoEncryptionOpts` as the setup. (Recreating prevents schema caching from
impacting the test).

Run an aggregate operation on `db.csfle` with the following pipeline:

```json
[
    {"$match" : {"csfle" : "qe"}},
    {
        "$lookup" : {
            "from" : "qe",
            "as" : "matched",
            "pipeline" : [ {"$match" : {"qe" : "qe"}}, {"$project" : {"_id" : 0}} ]
        }
    },
    {"$project" : {"_id" : 0}}
]
```

Expect an exception to be thrown with a message containing the substring `not supported`.

#### Case 9: test error with \<8.1

This case requires mongocryptd/crypt_shared \<8.1.

Recreate `encryptedClient` with the same `AutoEncryptionOpts` as the setup. (Recreating prevents schema caching from
impacting the test).

Run an aggregate operation on `db.csfle` with the following pipeline:

```json
[
    {"$match" : {"csfle" : "csfle"}},
    {
        "$lookup" : {
            "from" : "no_schema",
            "as" : "matched",
            "pipeline" : [ {"$match" : {"no_schema" : "no_schema"}}, {"$project" : {"_id" : 0}} ]
        }
    },
    {"$project" : {"_id" : 0}}
]
```

Expect an exception to be thrown with a message containing the substring `Upgrade`.

### 26. Custom AWS Credentials

These tests require valid AWS credentials for the remote KMS provider via the secrets manager (FLE_AWS_KEY and
FLE_AWS_SECRET). These tests MUST NOT run inside an AWS environment that has the same credentials set in order to
properly ensure the tests would fail using on-demand credentials.

#### Case 1: ClientEncryption with `credentialProviders` and incorrect `kmsProviders`

Create a MongoClient named `setupClient`.

Create a [ClientEncryption](../client-side-encryption.md#clientencryption) object with the following options:

```typescript
class ClientEncryptionOpts {
  keyVaultClient: <setupClient>,
  keyVaultNamespace: "keyvault.datakeys",
  kmsProviders: { "aws": { "accessKeyId": <set from secrets manager>, "secretAccessKey": <set from secrets manager> } },
  credentialProviders: { "aws": <default provider from AWS SDK> }
}
```

Assert that an error is thrown.

#### Case 2: ClientEncryption with `credentialProviders` works

Create a MongoClient named `setupClient`.

Create a [ClientEncryption](../client-side-encryption.md#clientencryption) object with the following options:

```typescript
class ClientEncryptionOpts {
  keyVaultClient: <setupClient>,
  keyVaultNamespace: "keyvault.datakeys",
  kmsProviders: { "aws": {} },
  credentialProviders: { "aws": <object/function that returns valid credentials from the secrets manager> }
}
```

Use the client encryption to create a datakey using the "aws" KMS provider. This should successfully load and use the
AWS credentials that were provided by the secrets manager for the remote provider. Assert the datakey was created and
that the custom credential provider was called at least once.

An example of this in Node.js:

```typescript
import { ClientEncryption, MongoClient } from 'mongodb';

let calledCount = 0;
const masterKey = {
  region: '<aws region>',
  key: '<key for arn>'
};
const keyVaultClient = new MongoClient(process.env.MONGODB_URI);
const options = {
  keyVaultNamespace: 'keyvault.datakeys',
  kmsProviders: { aws: {} },
  credentialProviders: {
    aws: async () => {
      calledCount++;
      return {
        accessKeyId: process.env.FLE_AWS_KEY,
        secretAccessKey: process.env.FLE_AWS_SECRET
      };
    }
  }
};
const clientEncryption = new ClientEncryption(keyVaultClient, options);
const dk = await clientEncryption.createDataKey('aws', { masterKey });
expect(dk).to.be.a(Binary);
expect(calledCount).to.be.greaterThan(0);
```

#### Case 3: `AutoEncryptionOpts` with `credentialProviders` and incorrect `kmsProviders`

Create a `MongoClient` object with the following options:

```typescript
class AutoEncryptionOpts {
  autoEncryption: {
    keyVaultNamespace: "keyvault.datakeys",
    kmsProviders: { "aws": { "accessKeyId": <set from secrets manager>, "secretAccessKey": <set from secrets manager> } },
    credentialProviders: { "aws": <default provider from AWS SDK> }
  }
}
```

Assert that an error is thrown.
