# CRUD Tests

## Introduction

The YAML and JSON files in this directory are platform-independent tests meant to exercise a driver's implementation of
the CRUD specification. These tests utilize the [Unified Test Format](../../unified-test-format/unified-test-format.md).

Several prose tests, which are not easily expressed in YAML, are also presented in this file. Those tests will need to
be manually implemented by each driver.

## Prose Tests

### 1. WriteConcernError.details exposes writeConcernError.errInfo

Test that `writeConcernError.errInfo` in a command response is propagated as `WriteConcernError.details` (or equivalent)
in the driver.

Using a 4.0+ server, set the following failpoint:

```javascript
{
  "configureFailPoint": "failCommand",
  "data": {
    "failCommands": ["insert"],
    "writeConcernError": {
      "code": 100,
      "codeName": "UnsatisfiableWriteConcern",
      "errmsg": "Not enough data-bearing nodes",
      "errInfo": {
        "writeConcern": {
          "w": 2,
          "wtimeout": 0,
          "provenance": "clientSupplied"
        }
      }
    }
  },
  "mode": { "times": 1 }
}
```

Then, perform an insert operation and assert that a WriteConcernError occurs and that its `details` property is both
accessible and matches the `errInfo` object from the failpoint.

### 2. WriteError.details exposes writeErrors\[\].errInfo

Test that `writeErrors[].errInfo` in a command response is propagated as `WriteError.details` (or equivalent) in the
driver.

Using a 5.0+ server, create a collection with
[document validation](https://www.mongodb.com/docs/manual/core/schema-validation/) like so:

```javascript
{
  "create": "test",
  "validator": {
    "x": { $type: "string" }
  }
}
```

Enable [command monitoring](../../command-logging-and-monitoring/command-logging-and-monitoring.rst) to observe
CommandSucceededEvents. Then, insert an invalid document (e.g. `{x: 1}`) and assert that a WriteError occurs, that its
code is `121` (i.e. DocumentValidationFailure), and that its `details` property is accessible. Additionally, assert that
a CommandSucceededEvent was observed and that the `writeErrors[0].errInfo` field in the response document matches the
WriteError's `details` property.
