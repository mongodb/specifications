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
- A list of Links to other Spans
- A list of timestamped Events
- A Status.

**Tracer**

A Tracer is responsible for creating spans, and using a tracer is the only way to create a span. A Tracer is not
responsible for configuration; this should be the responsibility of the TracerProvider instead.

**OpenTelemetry API and SDK**

OpenTelemetry offers two components for implementing instrumentation – API and SDK. The OpenTelemetry API provides all
the necessary types and method signatures. If there is no OpenTelemetry SDK available at runtime, API methods are no-op.
OpenTelemetry SDK is an actual implementation of the API. If the SDK is available, API methods do work.

### Implementation Requirements

#### External Dependencies

Drivers MAY add a dependency to the corresponding OpenTelemetry API. This is the recommended way for implementing
OpenTelemetry in libraries. Alternatively, drivers can implement OpenTelemetry support using any suitable tools within
the driver ecosystem. Drivers MUST NOT add a dependency to OpenTelemetry SDK.

#### Enabling and Disabling OpenTelemetry

OpenTelemetry SHOULD be disabled by default.

Drivers SHOULD support configuring OpenTelemetry on multiple levels.

- **MongoClient Level**: Drivers SHOULD provide a configuration option for `MongoClient`'s Configuration/Settings that
    enables or disables tracing for operations and commands executed with this client. This option MUST override
    settings on higher levels.
- **Driver Level**: Drivers SHOULD provide a global setting that enables or disables OpenTelemetry for all `MongoClient`
    instances (excluding those that explicitly override the setting). This configuration can be implemented with an
    environment variable `OTEL_#{LANG}_INSTRUMENTATION_MONGODB_ENABLED`. Drivers MAY provide other means to globally
    disable OpenTelemetry that are more suitable for their language ecosystem. This option MUST override settings on the
    higher level.
- **Host Application Level**: If the host application enables OpenTelemetry for all available instrumentations (e.g.,
    Ruby), and a driver can detect this, OpenTelemetry SHOULD be enabled in the driver.

Drivers MUST NOT try to detect whether the OpenTelemetry SDK library is available, and enable tracing based on this.

#### Tracer Attributes

If a driver creates a Tracer using OpenTelemetry API, drivers MUST use the following attributes:

- `name`: A string that identifies the driver. It can be the name of a driver's component (e.g., "mongo", "PyMongo") or
    a package name (e.g., "com.mongo.Driver"). Drivers SHOULD select a name that is idiomatic for their language and
    ecosystem. Drivers SHOULD follow the Instrumentation Scope guidance.
- `version`: The version of the driver.

#### Instrumenting Driver Operations

When a user calls the driver's public API, the driver MUST create a span for every driver operation. Drivers MUST start
the span as soon as possible so that the span’s duration reflects all activities made by the driver, such as server
selection and serialization/deserialization.

##### `withTransaction`

The `withTransaction` operation is a special case because it may include other operations that are executed "in scope"
of `withTransaction`. In this case, spans for operations that are executed inside the callbacks SHOULD be nested into
the `withTransaction` span.

##### Span Name

The span name SHOULD be:

- `driver_operation_name db.collection_name` if the command is executed on a collection (e.g.,
    `findOneAndDelete warehouse.users`).
- `db.driver_operation_name` if there is no specific collection for the command (e.g., `warehouse.runCommand`).

##### Span Kind

Span kind MUST be "client".

##### Span Attributes

Spans SHOULD have the following attributes:

| Attribute              | Type     | Description                                                                | Requirement Level     |
| :--------------------- | :------- | :------------------------------------------------------------------------- | :-------------------- |
| `db.system`            | `string` | MUST be 'mongodb'                                                          | Required              |
| `db.namespace`         | `string` | The database name                                                          | Required if available |
| `db.collection.name`   | `string` | The collection being accessed within the database stated in `db.namespace` | Required if available |
| `db.operation.name`    | `string` | The name of the driver operation being executed                            | Required              |
| `db.operation.summary` | `string` | Equivalent to span name                                                    | Required              |
| `db.mongodb.cursor_id` | `int64`  | If a cursor is created or used in the operation                            | Required if available |

Not all attributes are available at the moment of span creation. Drivers need to add attributes at later stages, which
requires an operation span to be available throughout the complete operation lifecycle.

##### Exceptions

If the driver operation fails with an exception, drivers MUST record an exception to the current operation span. When
recording an exception, drivers SHOULD add the following attributes to the span, when the content for the attribute if
available:

- `exception.message`
- `exception.type`
- `exception.stacktrace`

#### Instrumenting Server Commands

Drivers MUST create a span for every server command sent to the server as a result of a public API call, except for
sensitive commands as listed in the command logging and monitoring specification.

Spans for commands MUST be nested to the span for the corresponding driver operation span. If the command is being
retried, the driver MUST create a separate span for each retry.

##### Span Name

The span name SHOULD be:

- `server_command db.collection_name` if the command is executed on a collection (e.g.,
    `findAndModify warehouse.users`).
- `db.server_command` if there is no specific collection for the command.

##### Span Kind

Span kind MUST be "client".

##### Span Attributes

Spans SHOULD have the following attributes:

| Attribute                         | Type     | Description                                                                                                                                                                                        | Requirement Level            |
| :-------------------------------- | :------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------- |
| `db.system`                       | `string` | MUST be 'mongodb'                                                                                                                                                                                  | Required                     |
| `db.namespace`                    | `string` | The database name                                                                                                                                                                                  | Required if available        |
| `db.collection.name`              | `string` | The collection being accessed within the database stated in `db.namespace`                                                                                                                         | Required if available        |
| `db.command.name`                 | `string` | The name of the server command being executed                                                                                                                                                      | Required                     |
| `db.response.status_code`         | `string` | MongoDB error code represented as a string. This attribute should be added only if an error happens.                                                                                               | Required if an error happens |
| `error.type`                      | `string` | Describes a class of error the operation ended with. This attribute should be added only if an error happens. Examples: `timeout; java.net.UnknownHostException; server_certificate_invalid; 500`. | Required if an error happens |
| `server.port`                     | `int64`  | Server port number                                                                                                                                                                                 | Required                     |
| `server.address`                  | `string` | Name of the database host, or IP address if name is not known                                                                                                                                      | Required                     |
| `network.transport`               | `string` | MUST be 'tcp' or 'unix' depending on the protocol                                                                                                                                                  | Required                     |
| `db.query.summary`                | `string` | Equivalent to span name                                                                                                                                                                            | Required                     |
| `db.mongodb.server_connection_id` | `int64`  | Server connection id                                                                                                                                                                               | Required if available        |
| `db.mongodb.driver_connection_id` | `int64`  | Local connection id                                                                                                                                                                                | Required if available        |
| `db.query.text`                   | `string` | Database command that was sent to the server. Content should be equivalent to the `document` field of the CommandStartedEvent of the command monitoring.                                           | Conditional                  |
| `db.mongodb.cursor_id`            | `int64`  | If a cursor is created or used in the operation                                                                                                                                                    | Required if available        |

##### db.response.status_code and error.type

These attributes should be added only if the command was not successful. The content of `error.type` is language
specific; a driver decides what best describes the error.

##### db.query.text

This attribute contains the full database command executed serialized to extended JSON. If not truncated, the content of
this attribute SHOULD be equivalent to the `document` field of the CommandStartedEvent of the command

Drivers MUST NOT add this attribute by default. Drivers MUST provide a toggle to enable this attribute. This
configuration can be implemented with an environment variable
`OTEL_#{LANG}_INSTRUMENTATION_MONGODB_QUERY_TEXT_MAX_LENGTH` set to a positive integer value. The attribute will be
added and truncated to the provided value (similar to the Logging specification).

##### db.mongodb.cursor_id

If the command returns a cursor, or uses a cursor, the `cursor_id` attribute SHOULD be added.

##### Exception Handling

Exceptions SHOULD be added to the parent span of the command span, which is the driver operation span.

## Motivation for Change

A common complaint from our support team is that they don't know how to easily get debugging information from drivers.
Some drivers provide debug logging, but others do not. For drivers that do provide it, the log messages produced and the
mechanisms for enabling debug logging are inconsistent.

Although users can implement their own debug logging support via existing driver events (SDAM, APM, etc), this requires
code changes. It is often difficult to quickly implement and deploy such changes in production at the time they are
needed, and to remove the changes afterward. Additionally, there are useful scenarios to log that do not correspond to
existing events. Standardizing on debug log messages that drivers produce and how to enable/configure logging will
provide TSEs, CEs, and MongoDB users an easier way to get debugging information out of our drivers, facilitate support
of drivers for our internal teams, and improve our documentation around troubleshooting.

## Test Plan

TODO

## Backwards Compatibility

Introduction of OpenTelemetry in new driver versions should not significantly affect existing applications that do not
enable OpenTelemetry. However, since the no-op tracing operation may introduce some performance degradation (though it
should be negligible), customers should be informed of this feature and how to disable it completely.

If a driver is used in an application that has OpenTelemetry enabled, customers will see traces from the driver in their
OpenTelemetry backends. This may be unexpected and MAY cause negative effects in some cases (e.g., the OpenTelemetry
backend MAY not have enough capacity to process new traces). Customers should be informed of this feature and how to
disable it completely.

## Security Implication

Drivers MUST take care to avoid exposing sensitive information (e.g. authentication credentials) in traces.
