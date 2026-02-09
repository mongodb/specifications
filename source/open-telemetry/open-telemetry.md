# OpenTelemetry

- Title: OpenTelemetry
- Status: Accepted
- Minimum Server Version: N/A

______________________________________________________________________

## Abstract

This specification defines requirements for drivers' OpenTelemetry integration and behavior. Drivers will trace database
commands and driver operations with a pre-defined set of attributes when OpenTelemetry is enabled and configured in an
application.

## META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

### Terms

**Host Application**

An application that uses the MongoDB driver.

**Span**

A Span represents a single operation within a trace. Spans can be nested to form a trace tree. Each trace contains a
root span, which typically describes the entire operation and, optionally, one or more sub-spans for its sub-operations.

Spans encapsulate:

- The span name
- An immutable SpanContext that uniquely identifies the Span
- A parent span in the form of a Span, SpanContext, or null
- A SpanKind
- A start timestamp
- An end timestamp
- Attributes
- A list of links to other Spans
- A list of timestamped Events
- A Status

### Implementation Requirements

#### External Dependencies

**OpenTelemetry API and SDK**

OpenTelemetry offers two components for implementing instrumentation – API and SDK. The OpenTelemetry API provides all
the necessary types and method signatures. If there is no OpenTelemetry SDK available at runtime, API methods are
no-ops. OpenTelemetry SDK is an actual implementation of the API. If the SDK is available, API methods do work.

Drivers MAY add a dependency to the corresponding OpenTelemetry API. This is the recommended way for implementing
OpenTelemetry in libraries. Alternatively, drivers can implement OpenTelemetry support using any suitable tools within
the driver ecosystem. Drivers MUST NOT add a dependency to OpenTelemetry SDK.

#### Enabling, Disabling, and Configuring OpenTelemetry

OpenTelemetry SHOULD be disabled by default.

Drivers SHOULD support configuring OpenTelemetry on multiple levels.

- **MongoClient Level**: Drivers SHOULD provide a configuration option for `MongoClient`'s Configuration/Settings that
    enables or disables tracing for operations and commands executed with this client. This option MUST override
    settings on higher levels. This configuration can be implemented with a `MongoClient` option. See
    [Client Options](#client-options) section below.
- **Driver Level**: Drivers SHOULD provide a global setting that enables or disables OpenTelemetry for all `MongoClient`
    instances (excluding those that explicitly override the setting). This configuration SHOULD be implemented with an
    environment variable `OTEL_#{LANG}_INSTRUMENTATION_MONGODB_ENABLED`. Drivers MAY provide other means to globally
    disable OpenTelemetry that are more suitable for their language ecosystem. This option MUST override settings on the
    higher level.
- **Host Application Level**: If the host application enables OpenTelemetry for all available instrumentations (e.g.,
    Ruby), and a driver can detect this, OpenTelemetry SHOULD be enabled in the driver.

Drivers MUST NOT try to detect whether the OpenTelemetry SDK library is available, and enable tracing based on this.
Drivers MUST NOT add means that configure OpenTelemetry SDK (e.g., setting a specific exporter). Drivers MUST NOT add
means that configure OpenTelemetry on the host application level (e.g., setting a specific sampler).

<span id="client-options"></span>

##### `MongoClient` Options for configuring OpenTelemetry on the client level

Drivers SHOULD add new options to `MongoClient` for configuring OpenTelemetry as described above. These options SHOULD
be a dictionary that groups all OpenTelemetry-related options, the name of the dictionary SHOULD be `tracing`. The
dictionary SHOULD contain at least the following options:

- `enabled`: A boolean that enables or disables OpenTelemetry for this `MongoClient` instance. Default is `false` (i.e.,
    use the driver-level setting).
- `query_text_max_length`: An integer that sets the maximum length of the `db.query.text` attribute of command spans.
    Default is `0` (i.e., do not add the attribute).

#### Environment Variables for configuring OpenTelemetry

Drivers SHOULD support configuration of OpenTelemetry on the driver level via at least the following environment
variables:

- `OTEL_#{LANG}_INSTRUMENTATION_MONGODB_ENABLED`: enables OpenTelemetry when set to `1`, `true`, `yes`.
- `OTEL_#{LANG}_INSTRUMENTATION_MONGODB_QUERY_TEXT_MAX_LENGTH`: An integer that sets the maximum length of the
    `db.query.text` attribute of command spans. Default is `0` (i.e., do not add the attribute).

#### Tracer Attributes

If a driver creates a Tracer using OpenTelemetry API, drivers MUST use the following attributes:

- `name`: A string that identifies the driver. It can be the name of a driver's component (e.g., "mongo", "PyMongo") or
    a package name (e.g., "com.mongo.Driver"). Drivers SHOULD select a name that is idiomatic for their language and
    ecosystem. Drivers SHOULD follow the Instrumentation Scope guidance.
- `version`: A string that represents internal driver version. The version formatting is not defined; drivers SHOULD
    apply the same formatting as the use for `client.driver.version` attribute of the
    [handshake](https://github.com/mongodb/specifications/blob/master/source/mongodb-handshake/handshake.md#clientdriverversion).

#### Instrumenting Driver Operations

When a user calls the driver's public API, the driver MUST create a span for every driver operation. Drivers MUST start
the span as soon as possible so that the span’s duration reflects all activities made by the driver, such as server
selection and serialization/deserialization.

The span for the operation MUST be created within the current span of the host application, with the exceptions listed
below.

##### Transactions

When a user starts a transaction with `startTransaction`, the driver SHOULD create a span for the pseudo operation
`transaction`. This span MUST have only one attribute `db.system.name` with the value `mongodb`. All operations executed
within the transaction SHOULD be nested to the `transaction` span.

When a user commits or aborts a transaction with `commitTransaction` or `abortTransaction`, the driver SHOULD finish the
`transaction` span.

##### `withTransaction`

In case of `withTransaction` operation spans for operations that are executed inside the callbacks SHOULD be nested into
the `withTransaction` span.

##### Operation Span Name

The span name SHOULD be:

- `driver_operation_name db.collection_name` if the operation is executed on a collection (e.g.,
    `collection.findOneAndDelete(filter)` will report `findAndModify warehouse_db.users_coll`).

**Note**: since the `findOneAndDelete` operation is implemented as a `findAndModify` command, the operation name in the
span is `findAndModify`. This ensures consistency between drivers when naming operations. See the
[covered operations](#covered-operations) table below for mapping of public API methods to operation names.

- `driver_operation_name db` if there is no specific collection for the operation (e.g., `runCommand warehouse`).

##### Operation Span Kind

Span kind MUST be "client".

##### Operation Span Attributes

Spans SHOULD have the following attributes:

| Attribute              | Type     | Description                                                                | Requirement Level     |
| :--------------------- | :------- | :------------------------------------------------------------------------- | :-------------------- |
| `db.system.name`       | `string` | MUST be 'mongodb'                                                          | Required              |
| `db.namespace`         | `string` | The database name                                                          | Required if available |
| `db.collection.name`   | `string` | The collection being accessed within the database stated in `db.namespace` | Required if available |
| `db.operation.name`    | `string` | The name of the driver operation being executed                            | Required              |
| `db.operation.summary` | `string` | Equivalent to span name                                                    | Required              |

Not all attributes are available at the moment of span creation. Drivers need to add attributes at later stages, which
requires an operation span to be available throughout the complete operation lifecycle.

###### db.namespace

This attribute SHOULD be set to current database name except for operations executing against admin db ex: (transaction,
client `bulkWrite`) operations.

Examples:

- `find` on `test.users` → `test`
- `runCommand` on `admin` → `admin`
- `commitTransaction` → `admin`
- `abortTransaction` → `admin`
- client `bulkWrite` → `admin`

The name of this attribute is defined in the
[OpenTelemetry Specifications](https://opentelemetry.io/docs/specs/semconv/registry/attributes/db/#db-namespace). In
order to be compliant with these, we use this name even though the term `namespace` has a different
[meaning](https://www.mongodb.com/docs/manual/reference/glossary/) for MongoDB.

###### db.collection.name

This attribute should be set to the user's collection if the operation is executing against a collection, this field is
omitted for commands running against `admin` database or commands that do not target a specific collection.

Examples:

- `find` on `test.users` → `users`
- `runCommand` on `admin` → *omitted*
- `commitTransaction` → *omitted*
- `abortTransaction` → *omitted*
- client `bulkWrite` → *omitted*

##### Exceptions

If the driver operation fails with an exception, drivers MUST record an exception to the current operation span. This
does not relate to exceptions that happen on the server command level (see below). Those exceptions MUST be recorded to
the corresponding command span.

When recording an exception, drivers SHOULD add the following attributes to the span, when the content for the attribute
if available:

- `exception.message`
- `exception.type`
- `exception.stacktrace`

#### Instrumenting Server Commands

Drivers MUST create a span for every server command sent to the server as a result of a public API call, except for
sensitive commands as listed in the command logging and monitoring specification.

Spans for commands MUST be nested to the span for the corresponding driver operation span. If the command is being
retried, the driver MUST create a separate span for each retry; all the retries MUST be nested to the same operation
span.

##### Command Span Name

The span name SHOULD be the command name. For example, `find`, `insert`, `update`, etc.

##### Command Span Kind

Span kind MUST be "client".

##### Command Span Attributes

Spans SHOULD have the following attributes:

| Attribute                         | Type     | Description                                                                                                                                              | Requirement Level            |
| :-------------------------------- | :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------- |
| `db.system.name`                  | `string` | MUST be 'mongodb'                                                                                                                                        | Required                     |
| `db.namespace`                    | `string` | The database name                                                                                                                                        | Required if available        |
| `db.collection.name`              | `string` | The collection being accessed within the database stated in `db.namespace`                                                                               | Required if available        |
| `db.command.name`                 | `string` | The name of the server command being executed                                                                                                            | Required                     |
| `db.response.status_code`         | `string` | MongoDB error code represented as a string. This attribute should be added only if an error happens.                                                     | Required if an error happens |
| `server.port`                     | `int64`  | Server port number                                                                                                                                       | Required                     |
| `server.address`                  | `string` | Name of the database host, or IP address if name is not known                                                                                            | Required                     |
| `network.transport`               | `string` | MUST be 'tcp' or 'unix' depending on the protocol                                                                                                        | Required                     |
| `db.query.summary`                | `string` | (see explanation below)                                                                                                                                  | Required                     |
| `db.mongodb.server_connection_id` | `int64`  | Server connection id                                                                                                                                     | Required if available        |
| `db.mongodb.driver_connection_id` | `int64`  | Local connection id                                                                                                                                      | Required if available        |
| `db.query.text`                   | `string` | Database command that was sent to the server. Content should be equivalent to the `document` field of the CommandStartedEvent of the command monitoring. | Conditional                  |
| `db.mongodb.cursor_id`            | `int64`  | If a cursor is created or used in the operation                                                                                                          | Required if available        |
| `db.mongodb.lsid`                 | `string` | Logical session id                                                                                                                                       | Required if available        |
| `db.mongodb.txn_number`           | `int64`  | Transaction number                                                                                                                                       | Required if available        |

Besides the attributes listed in the table above, drivers MAY add other attributes from the
[Semantic Conventions for Databases](https://opentelemetry.io/docs/specs/semconv/registry/attributes/db/) that are
applicable to MongoDB.

###### db.namespace

This attribute SHOULD be set to current database name except for operations executing against admin db ex: (transaction,
client `bulkWrite`) operations.

Examples:

- `find` on `test.users` → `test`
- `runCommand` on `admin` → `admin`
- `commitTransaction` → `admin`
- `abortTransaction` → `admin`
- client `bulkWrite` → `admin`

The name of this attribute is defined in the
[OpenTelemetry Specifications](https://opentelemetry.io/docs/specs/semconv/registry/attributes/db/#db-namespace). In
order to be compliant with these, we use this name even though the term `namespace` has a different
[meaning](https://www.mongodb.com/docs/manual/reference/glossary/) for MongoDB.

###### db.collection.name

This attribute should be set to the user's collection if the operation is executing against a collection, this field is
omitted for commands running against `admin` database or commands that do not target a specific collection.

Examples:

- `find` on `test.users` → `users`
- `runCommand` on `admin` → *omitted*
- `commitTransaction` → *omitted*
- `abortTransaction` → *omitted*
- client `bulkWrite` → *omitted*

###### db.query.summary

This attribute SHOULD contain:

- `command_name db.collection_name` if the command is executed on a collection.
- `command_name db` if there is no specific collection for the command.
- `command_name admin` in other cases (e.g., commands executed against `admin` database, transaction or client
    `bulkWrite`).

###### db.query.text

This attribute contains the full database command executed serialized to extended JSON. If not truncated, the content of
this attribute SHOULD be equivalent to the `document` field of the CommandStartedEvent of the command monitoring
excluding the following fields: `lsid`, `$db`, `$clusterTime`, `signature`.

Drivers MUST NOT add this attribute by default. Drivers MUST provide a toggle to enable this attribute. This
configuration can be implemented with an environment variable
`OTEL_#{LANG}_INSTRUMENTATION_MONGODB_QUERY_TEXT_MAX_LENGTH` set to a positive integer value. The attribute will be
added and truncated to the provided value (similar to the Logging specification).

On the `MongoClient` level this configuration can be implemented with a `MongoClient` option, for example,
`tracing.query_text_max_length`.

###### db.mongodb.cursor_id

If the command returns a cursor, or uses a cursor, the `cursor_id` attribute SHOULD be added.

##### Exceptions

If the server command fails with an exception, drivers MUST record an exception to the current command span. When
recording an exception, drivers SHOULD add the following attributes to the span, when the content for the attribute if
available:

- `exception.message`
- `exception.type`
- `exception.stacktrace`

## Motivation for Change

A common complaint from our support team is that they don't know how to easily get debugging information from drivers.
Some drivers provide debug logging, but others do not. For drivers that do provide it, the log messages produced and the
mechanisms for enabling debug logging are inconsistent.

OpenTelemetry is currently the industry standard for instrumenting, generating, and collecting telemetry data (metrics,
logs, and traces). By instrumenting our drivers natively, we allow our end users to collect traces in a
batteries-included way, with the additional benefits that the tracing is developed and maintained in-house, and conforms
to the open-source standard for tracing. This also ensures that traces generated on the client-side on driver operations
can tie into other traces, thus giving our end users a broader picture of the network hops that a single request might
take.

## Test Plan

See [OpenTelemetry Tests](tests/README.md) for the test plan.

## Covered operations

The OpenTelemetry specification covers all driver operations including but not limited to the following operations:

| Operation                | Test                                                                           |
| :----------------------- | :----------------------------------------------------------------------------- |
| `aggregate`              | [tests/operation/aggregate.yml](tests/operation/aggregate.yml)                 |
| `findAndModify`          | [tests/operation/find_and_modify.yml](tests/operation/find_and_modify.yml)     |
| `bulkWrite`              | [tests/operation/bulk_write.yml](tests/operation/bulk_write.yml)               |
| `commitTransaction`      | [tests/transaction/core_api.yml](tests/transaction/core_api.yml)               |
| `abortTransaction`       | [tests/transaction/core_api.yml](tests/transaction/core_api.yml)               |
| `withTransaction`        | [tests/transaction/convenient.yml](tests/transaction/convenient.yml)           |
| `createCollection`       | [tests/operation/create_collection.yml](tests/operation/create_collection.yml) |
| `createIndexes`          | [tests/operation/create_indexes.yml](tests/operation/create_indexes.yml)       |
| `distinct`               | [tests/operation/distinct.yml](tests/operation/distinct.yml)                   |
| `dropCollection`         | [tests/operation/drop_collection.yml](tests/operation/drop_collection.yml)     |
| `dropIndexes`            | [tests/operation/drop_indexes.yml](tests/operation/drop_indexes.yml)           |
| `find`                   | [tests/operation/find.yml](tests/operation/find.yml)                           |
| `listCollections`        | [tests/operation/list_collections.yml](tests/operation/list_collections.yml)   |
| `listDatabases`          | [tests/operation/list_databases.yml](tests/operation/list_databases.yml)       |
| `listIndexes`            | [tests/operation/list_indexes.yml](tests/operation/list_indexes.yml)           |
| `mapReduce`              | [tests/operation/map_reduce.yml](tests/operation/map_reduce.yml)               |
| `estimatedDocumentCount` | [tests/operation/count.yml](tests/operation/count.yml)                         |
| `insert`                 | [tests/operation/insert.yml](tests/operation/insert.yml)                       |
| `delete`                 | [tests/operation/delete.yml](tests/operation/delete.yml)                       |
| `update`                 | [tests/operation/update.yml](tests/operation/update.yml)                       |
| `createSearchIndexes`    | [tests/operation/atlas_search.yml](tests/operation/atlas_search.yml)           |
| `dropSearchIndex`        | [tests/operation/atlas_search.yml](tests/operation/atlas_search.yml)           |
| `updateSearchIndex`      | [tests/operation/delete.yml](tests/operation/delete.yml)                       |
| `delete`                 | [tests/operation/atlas_search.yml](tests/operation/atlas_search.yml)           |

## Backwards Compatibility

Introduction of OpenTelemetry in new driver versions should not significantly affect existing applications that do not
enable OpenTelemetry. However, since the no-op tracing operation may introduce some performance degradation (though it
should be negligible), customers should be informed of this feature and how to disable it completely.

If a driver is used in an application that has OpenTelemetry enabled, customers will see traces from the driver in their
OpenTelemetry backends. This may be unexpected and MAY cause negative effects in some cases (e.g., the OpenTelemetry
backend MAY not have enough capacity to process new traces). Customers should be informed of this feature and how to
disable it completely.

## Security Implication

Drivers MUST take care to avoid exposing sensitive information (e.g. authentication credentials) in traces. Drivers
SHOULD follow the
[Security](https://github.com/mongodb/specifications/blob/master/source/command-logging-and-monitoring/command-logging-and-monitoring.md#security)
guidance of the Command Logging and Monitoring spec.

## Future Work

### Query Parametrization

It might be beneficial to implement query parametrization for the `db.query.text` attribute.

One might want to replace dynamic values in queries with placeholders. For example, the query

```json
{ find: "users", filter: { age: { $gt: 30 } } }
```

will be transformed to

```json
{ find: "users", filter: { age: { $gt: "?" } } }
```

for purposes of obfuscating queries in traces or query aggregation.

In the case of CSFLE, the query might already have BSON binary values (with the encrypted subtype) by the time the query
is sent along for tracing, which can also be considered a form of parameterization. In that case, a driver could easily
replace those binary values with placeholders (assuming the encrypted blobs are irrelevant for logging).

## Design Rationale

### No URI options

Enabling tracing may have performance and security implications. Copying and using a connection string that enables
tracing may have unexpected negative outcome.

Further, we already have two attributes that configure tracing, and we expect there might be more.

A URI options can be added later if we realise our users need it, while the opposite is not easily accomplished.

## Changelog

- 2026-02-09: Renamed `db.system` to `db.system.name` according to the corresponding update of OpenTelemetry semantic
    conventions.
