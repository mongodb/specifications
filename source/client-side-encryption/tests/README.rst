============================
Client Side Encryption Tests
============================

.. contents::

----

Introduction
============

This document describes the format of the driver spec tests included in the JSON
and YAML files included in this directory.

Additional prose tests, that are not represented in the spec tests, are described
and MUST be implemented by all drivers.

TODO
----
- Add remaining tests.
- Once limitations of query parsing in mongocryptd are known, add tests to exercise those limitations.

Spec Test Format
================

The spec tests format is an extension of transactions spec tests with some additions:

- A ``json_schema`` to set on the collection used for operations.

- A ``key_vault_data`` of data that should be inserted in the key vault collection before each test.

- Introduction ``client_side_encryption_opts`` to `clientOptions`

- Addition of `$db` to command in `command_started_event`

- Addition of `$type` to command_started_event and outcome.

Each YAML file has the following keys:

.. |txn| replace:: Unchanged. See `Transactions spec tests <https://github.com/mongodb/specifications/blob/master/source/transactions/tests/README.rst>`_

- ``runOn`` |txn|_

- ``database_name`` |txn|_

- ``collection_name`` |txn|_

- ``data`` |txn|_

- ``json_schema`` A JSONSchema that should be set on the collection (using ``createCollection``) before each test run. 

- ``key_vault_data`` The data that should exist in the key vault collection under test before each test run.

- ``tests``: An array of tests that are to be run independently of each other.
  Each test will have some or all of the following fields:

  - ``description``: |txn|_

  - ``skipReason``: |txn|_

  - ``clientOptions``: Optional, parameters to pass to MongoClient().

    - ``client_side_encryption_opts``: Optional

      - ``kms_providers`` A dictionary of KMS providers to set on the key vault ("aws" or "local")

        - ``aws`` The AWS KMS provider. An empty object. Drivers MUST fill in AWS credentials from the environment.

        - ``local`` The local KMS provider.

          - ``key`` A 64 byte local key.

      - ``schema_map``: Optional, a map from namespaces to local JSON schemas.

  - ``operations``: Array of documents, each describing an operation to be
    executed. Each document has the following fields:

    - ``name``: |txn|_

    - ``object``: |txn|_

    - ``collectionOptions``: |txn|_

    - ``command_name``: |txn|_

    - ``arguments``: |txn|_

    - ``result``: |txn|_

  - ``expectations``: |txn|_

  - ``outcome``: |txn|_



Use as integration tests
========================

Do the following before running spec tests:

- Start the mongocryptd process.
- Start a mongod process with **server version 4.1.9 or later**.
- Place credentials to an AWS IAM user (access key ID + secret access key) somewhere in the environment outside of tracked code. (If testing on evergreen, project variables are a good place).

Load each YAML (or JSON) file using a Canonical Extended JSON parser.

Then for each element in ``tests``:

#. If the``skipReason`` field is present, skip this test completely.
#. If the ``key_vault_data`` field is present:
   #. Drop the ``admin.datakeys`` collection using writeConcern "majority".
   #. Insert the data specified into the ``admin.datakeys`` with write concern "majority".
#. Create a MongoClient using ``clientOptions``.
   #. If ``client_side_encryption_opts`` includes ``aws`` as a KMS provider, pass in AWS credentials from the environment.
#. Create a collection object from the MongoClient, using the ``database_name``
   and ``collection_name`` fields from the YAML file.
#. Drop the test collection, using writeConcern "majority".
#. If the YAML file contains a ``data`` array, insert the documents in ``data``
   into the test collection, using writeConcern "majority".
#. If ``failPoint`` is specified, its value is a configureFailPoint command.
   Run the command on the admin database to enable the fail point.

   - When testing against a sharded cluster run this command on ALL mongoses.

#. Set Command Monitoring listeners on the MongoClient.
#. For each element in ``operations``:

   - Enter a "try" block or your programming language's closest equivalent.
   - Create a Database object from the MongoClient, using the ``database_name``
     field at the top level of the test file.
   - Create a Collection object from the Database, using the
     ``collection_name`` field at the top level of the test file.
     If ``collectionOptions`` is present create the Collection object with the
     provided options. Otherwise create the object with the default options.
   - Execute the named method on the provided ``object``, passing the
     arguments listed.
   - If the driver throws an exception / returns an error while executing this
     series of operations, store the error message and server error code.
   - If the result document has an "errorContains" field, verify that the
     method threw an exception or returned an error, and that the value of the
     "errorContains" field matches the error string. "errorContains" is a
     substring (case-insensitive) of the actual error message.

     If the result document has an "errorCodeName" field, verify that the
     method threw a command failed exception or returned an error, and that
     the value of the "errorCodeName" field matches the "codeName" in the
     server error response.

     If the result document has an "errorLabelsContain" field, verify that the
     method threw an exception or returned an error. Verify that all of the
     error labels in "errorLabelsContain" are present in the error or exception
     using the ``hasErrorLabel`` method.

     If the result document has an "errorLabelsOmit" field, verify that the
     method threw an exception or returned an error. Verify that none of the
     error labels in "errorLabelsOmit" are present in the error or exception
     using the ``hasErrorLabel`` method.
   - If the operation returns a raw command response, eg from ``runCommand``,
     then compare only the fields present in the expected result document.
     Otherwise, compare the method's return value to ``result`` using the same
     logic as the CRUD Spec Tests runner.

#. If the test includes a list of command-started events in ``expectations``,
   compare them to the actual command-started events using the
   same logic as the Command Monitoring Spec Tests runner.
#. If ``failPoint`` is specified, disable the fail point to avoid spurious
   failures in subsequent tests. The fail point may be disabled like so::

    db.adminCommand({
        configureFailPoint: <fail point name>,
        mode: "off"
    });

   - When testing against a sharded cluster run this command on ALL mongoses.

#. For each element in ``outcome``:

   - If ``name`` is "collection", create a new MongoClient *without encryption*
     and verify that the test collection contains exactly the documents in the 
     ``data`` array. Ensure this find reads the latest data by using
     **primary read preference** with **local read concern** even when the
     MongoClient is configured with another read preference or read concern.


Prose Tests
===========

TODO: in progress.