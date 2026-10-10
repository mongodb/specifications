# MongoDB Handshake

- Status: Accepted

______________________________________________________________________

## Abstract

MongoDB has the ability to annotate connections with metadata provided by the connecting client. The intent of this
metadata is to be able to identify client level information about the connection, such as application name, driver name
and version. The provided information will be logged through the `mongo[d|s].log` and the profile logs; this should
enable sysadmins to easily backtrack log entries the offending application. The active connection data will also be
queryable through aggregation pipeline, to enable collecting and analyzing driver trends.

After connecting to a MongoDB node a hello command (if Stable API is requested) or a legacy hello command is issued,
followed by authentication, if appropriate. This specification augments this handshake and defines certain arguments
that clients provide as part of the handshake.

This spec furthermore adds a new connection string argument for applications to declare its application name to the
server.

## META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Terms

**hello command**

The command named `hello`. It is the preferred and modern command for handshakes and topology monitoring.

**legacy hello command**

The command named `isMaster`. It is the deprecated equivalent of the `hello` command. It was deprecated in MongoDB 5.0.

**isMaster / ismaster**

The correct casing is `isMaster`, but servers will accept the alternate casing `ismaster`. Other case variations result
in `CommandNotFound`. Drivers MUST take this case variation into account when determining which commands to encrypt,
redact, or otherwise treat specially.

## Specification

### Connection handshake

MongoDB uses the `hello` or `isMaster` commands for handshakes and topology monitoring. `hello` is the modern and
preferred command. `hello` must always be sent using the `OP_MSG` protocol. `isMaster` is referred to as "legacy hello"
and is maintained for backwards compatibility with servers that do not support the `hello` command.

Drivers MUST use the `OP_MSG` protocol for all handshakes. If a [server API version](../versioned-api/versioned-api.md)
is requested or `loadBalanced: True`, drivers MUST also use the `hello` command for the initial handshake. If server API
version is not requested and `loadBalanced: False`, drivers MUST use legacy hello for the first message of the initial
handshake, and include `helloOk:true` in the handshake request.

Drivers MUST include `backpressure: "2"` in their handshake request in order to explicitly version their supported
version of the client backpressure specification. The value of `backpressure` MUST be the string `"2"` and not a literal
number `2`.

If the legacy handshake response includes `helloOk: true`, then subsequent topology monitoring commands MUST use the
`hello` command. If the legacy handshake response does not include `helloOk: true`, then subsequent topology monitoring
commands MUST use the legacy hello command. See the
[Server Discovery and Monitoring spec](../server-discovery-and-monitoring/server-discovery-and-monitoring-summary.md)
for further information.

The initial handshake MUST be performed on every socket to any and all servers upon establishing the connection to
MongoDB, including reconnects of dropped connections and newly discovered members of a cluster. It MUST be the first
command sent over the respective socket. If the command fails the client MUST disconnect. Timeouts MUST be applied to
this command per the
[Client Side Operations Timeout](../client-side-operations-timeout/client-side-operations-timeout.md) specification.

`hello` and legacy hello commands issued after the initial connection handshake MUST NOT contain handshake arguments.
Any subsequent `hello` or legacy hello calls, such as the ones for topology monitoring purposes, MUST NOT include this
argument.

#### Example Implementation

Consider the following pseudo-code for establishing a new connection:

```python
conn = Connection()
conn.connect()  # Connect via TCP / TLS
if stable_api_configured or client_options.load_balanced:
    cmd = {"hello": 1}
else:
    cmd = {"legacy hello": 1, "helloOk": 1}
cmd["backpressure"] = "2"
cmd["client"] = client_metadata
if client_options.compressors:
    cmd["compression"] = client_options.compressors
if client_options.load_balanced:
    cmd["loadBalanced"] = True
creds = client_options.credentials
if creds:
    # Negotiate auth mechanism and perform speculative auth. See Auth spec for details.
    if not creds.has_mechanism_configured():
        cmd["saslSupportedMechs"] = ...
    cmd["speculativeAuthenticate"] = ...

reply = conn.send_command("admin", cmd)

# Store the negotiated compressor, see OP_COMPRESSED spec.
if reply.get("compression"):
    conn.compressor = reply["compression"][0]

# Perform connection authentication. See Auth spec for details.
negotiated_mechs = reply.get("saslSupportedMechs")
speculative_auth = reply.get("speculativeAuthenticate")
conn.authenticate(creds, negotiated_mechs, speculative_auth)
```

#### Hello Command

The initial handshake supports a `client` argument, provided as a BSON object. This object has the following structure:

```javascript
    {
        hello: 1,
        helloOk: true,
        client: {
            /* OPTIONAL. If present, the "name" is REQUIRED */
            application: {
                name: "<string>"
            },
            /* REQUIRED, including all sub fields */
            driver: {
                name: "<string>",
                version: "<string>"
            },
            /* REQUIRED */
            os: {
                type: "<string>",         /* REQUIRED */
                name: "<string>",         /* OPTIONAL */
                architecture: "<string>", /* OPTIONAL */
                version: "<string>"       /* OPTIONAL */
            },
            /* OPTIONAL */
            platform: "<string>",
            /* OPTIONAL */
            env: {
                name: "<string>",         /* OPTIONAL */
                timeout_sec: 42,          /* OPTIONAL */
                memory_mb: 1024,          /* OPTIONAL */
                region: "<string>",       /* OPTIONAL */
                agent: "<string>",        /* OPTIONAL */
                /* OPTIONAL */
                container: {
                    runtime: "<string>",  /* OPTIONAL */
                    orchestrator: "<string>"  /* OPTIONAL */
                }
            }
        }
    }
```

<span id="client-application-name"></span>

#### client.application.name

This value is application configurable.

The application name is printed to the mongod logs upon establishing the connection. It is also recorded in the slow
query logs and profile collections.

The recommended way for applications to provide this value is through the connection URI. The connection string key is
`appname`.

Example connection string:

```text
mongodb://server:27017/db?appname=mongodump
```

This option MAY also be provided on the MongoClient itself, if normal for the driver. It is only valid to set this
attribute before any connection has been made to a server. Any attempt to set `client.application.name` MUST result in
an failure when doing so will either change the existing value, or have any connection to MongoDB reporting inconsistent
values.

Drivers MUST NOT provide a default value for this key.

#### client.driver.name

This value is required and is not application configurable.

The internal driver name. For drivers written on-top of other core drivers, the `appendMetadata()` method can be used to
add package information to an existing MongoClient.

Example:

```text
- "pymongo"
- "mongoc / phongo"
```

#### client.driver.version

This value is required and is not application configurable.

The internal driver version. The version formatting is not defined. For drivers written on-top of other core drivers,
the `appendMetadata()` method can be used to add package information to an existing MongoClient.

Example:

```text
- "1.1.2-beta0"
- "1.4.1 / 1.2.0"
```

#### client.os.type

This value is required and is not application configurable.

The Operating System primary identification type the client is running on. Equivalent to `uname -s` on POSIX systems.
This field is REQUIRED and clients must default to `unknown` when an appropriate value cannot be determined.

Example:

```text
- "Linux"
- "Darwin"
- "Windows"
- "BSD"
- "Unix"
```

#### client.os.name

This value is optional, but RECOMMENDED, it is not application configurable.

Detailed name of the Operating System's, such as fully qualified distribution name. On systemd systems, this is
typically `PRETTY_NAME` of `os-release(5)` (`/etc/os-release`) or the `DISTRIB_DESCRIPTION` (`/etc/lsb-release`,
`lsb_release(1) --description`) on LSB systems. The exact value and method to determine this value is undefined.

Example:

```text
- "Ubuntu 16.04 LTS"
- "macOS"
- "CygWin"
- "FreeBSD"
- "AIX"
```

#### client.os.architecture

This value is optional, but RECOMMENDED, it is not application configurable. The machine hardware name. Equivalent to
`uname -m` on POSIX systems.

Example:

```text
- "x86_64"
- "ppc64le"
```

#### client.os.version

This value is optional and is not application configurable.

The Operating System version.

Example:

```text
- "10"
- "8.1"
- "16.04.1"
```

#### client.platform

This value is optional and is not application configurable.

Driver specific platform details.

Example:

```text
- clang 3.8.0 CFLAGS="-mcpu=power8 -mtune=power8 -mcmodel=medium"
- "Oracle JVM EE 9.1.1"
```

<span id="client-env"></span>

#### client.env

This value is optional and is not application configurable.

Information about the execution environment, including Function-as-a-Service (FaaS) identification, container runtime,
and agentic client (agent) identification.

The contents of `client.env` MUST be adjusted to keep the handshake below the size limit; see
[Limitations](#limitations) for specifics.

If no fields of `client.env` would be populated, `client.env` MUST be entirely omitted.

##### FaaS

FaaS details are captured in the `name`, `timeout_sec`, `memory_mb`, and `region` fields of `client.env`. The `name`
field is determined by which of the following environment variables are populated:

| Name         | Environment Variable                                |
| ------------ | --------------------------------------------------- |
| `aws.lambda` | `AWS_EXECUTION_ENV`[^1] or `AWS_LAMBDA_RUNTIME_API` |
| `azure.func` | `FUNCTIONS_WORKER_RUNTIME`                          |
| `gcp.func`   | `K_SERVICE` or `FUNCTION_NAME`                      |
| `vercel`     | `VERCEL`                                            |

If none of those variables are populated the other FaaS values MUST be entirely omitted. When variables for multiple
`client.env.name` values are present, `vercel` takes precedence over `aws.lambda`; any other combination MUST cause the
other FaaS values to be entirely omitted.

Depending on which `client.env.name` has been selected, other FaaS fields in `client.env` SHOULD be populated:

| Name         | Field                    | Environment Variable              | Expected Type |
| ------------ | ------------------------ | --------------------------------- | ------------- |
| `aws.lambda` | `client.env.region`      | `AWS_REGION`                      | string        |
|              | `client.env.memory_mb`   | `AWS_LAMBDA_FUNCTION_MEMORY_SIZE` | int32         |
| `gcp.func`   | `client.env.memory_mb`   | `FUNCTION_MEMORY_MB`              | int32         |
|              | `client.env.timeout_sec` | `FUNCTION_TIMEOUT_SEC`            | int32         |
|              | `client.env.region`      | `FUNCTION_REGION`                 | string        |
| `vercel`     | `client.env.region`      | `VERCEL_REGION`                   | string        |

Missing variables or variables with values not matching the expected type MUST cause the corresponding `client.env`
field to be omitted and MUST NOT cause a user-visible error.

##### Agent

Agents are AI coding assistants and agentic clients, such as Claude Code, Cursor, and Gemini CLI. Most agents set an
environment variable when they run shell commands or code for a user. `client.env.agent` records which agent, if any,
drives the client. This distinguishes agent-mediated use of MongoDB from direct human use.

`client.env.agent` is a single string. The environment variables below determine its value. Drivers MUST evaluate the
list in order. The first populated variable determines the value. Drivers MUST NOT consider later entries.

| Order | Environment Variable     | `client.env.agent` value |
| ----- | ------------------------ | ------------------------ |
| 1     | `CLAUDECODE`             | `claude_code`            |
| 2     | `CLAUDE_CODE_ENTRYPOINT` | `claude_code`            |
| 3     | `CURSOR_AGENT`           | `cursor`                 |
| 4     | `CODEX_SANDBOX`          | `codex_cli`              |
| 5     | `CLINE_ACTIVE`           | `cline`                  |
| 6     | `GEMINI_CLI`             | `gemini_cli`             |
| 7     | `AUGMENT_AGENT`          | `auggie_cli`             |
| 8     | `OPENCODE`               | `opencode_client`        |
| 9     | `TRAE_AI_SHELL_ID`       | `trae_ai`                |
| 10    | `GOOSE_TERMINAL`         | `goose`                  |
| 11    | `GOOSE_AGENT`            | `goose`                  |
| 12    | `AI_AGENT`               | See below.               |

For entries 1 through 11, `client.env.agent` is the fixed string in the table, whatever the value of the populated
variable. These variables identify a known agent, so the name does not depend on the value.

Entry 12, `AI_AGENT`, is a generic variable that any agent may set. It is evaluated last, so a known agent is always
reported under its fixed name. Normalize its value, then:

- If the normalized value is `1` or `true`, `client.env.agent` MUST be the fixed string `ai_agent`. These values
    identify an agent without naming it.
- Otherwise, `client.env.agent` MUST be the normalized value.

Normalization removes leading and trailing whitespace and converts the value to lowercase. Drivers MUST then truncate
the value to the largest valid UTF-8 prefix of 64 bytes or fewer. Drivers MUST drop a character that does not fit.
Drivers MUST NOT split a character or replace one with U+FFFD.

`AI_AGENT` is the only entry whose value is reported, and therefore the only unbounded one. The 64-byte limit stops a
long value from costing both `client.env.agent` and other fields under [Limitations](#limitations).

> [!NOTE]
> Truncation at a fixed byte count splits a character if the limit falls inside one, and some string APIs then
> substitute U+FFFD, which is lossy and longer than the bytes it replaces. Use an API that truncates on a character
> boundary, or walk back from byte 64 to the start of the character that contains it.

Agents may include version information in this value, so it is not a fixed set of strings. Entries 1 through 11 report a
name from the table, but an agent reports its own `AI_AGENT` value, which is therefore not generically queryable.

A variable is populated if it is present and non-empty after normalization. A whitespace-only value is therefore not
populated. If no variable above is populated, `client.env.agent` MUST be omitted.

Determination of `client.env.agent` MUST NOT cause a user-visible error.

> [!NOTE]
> The variables above, and the names they map to, match the detection that
> [mongosh](https://github.com/mongodb-js/mongosh) implements, so drivers and the shell report the same known agent
> under the same name. New agents will appear over time. Drivers MUST NOT add entries on their own; a change to this
> specification extends the list.
>
> Detection of opencode does not match mongosh, which checks `OPENCODE_CLIENT`. opencode does not set that variable; it
> sets `OPENCODE`. This specification checks `OPENCODE`.
>
> Normalization of `AI_AGENT` does not match mongosh, which keeps whitespace, reports a whitespace-only value, and does
> not truncate. [MONGOSH-3696](https://jira.mongodb.org/browse/MONGOSH-3696) proposes that mongosh adopt the behavior
> above.

##### Container

Container runtime information is captured in `client.env.container`.

`client.env.container.runtime` MUST be set to `"docker"` if the file `.dockerenv` exists in the root directory.

`client.env.container.orchestrator` MUST be set to `"kubernetes"` if the environment variable `KUBERNETES_SERVICE_HOST`
is populated.

If no fields of `client.env.container` would be populated, `client.env.container` MUST be entirely omitted.

If the runtime environment has both FaaS and container information, both must have their metadata included in
`client.env`.

### Speculative Authentication

- Since: 4.4

The initial handshake supports a new argument, `speculativeAuthenticate`, provided as a BSON document. Clients
specifying this argument to `hello` or legacy hello will speculatively include the first command of an authentication
handshake. This command may be provided to the server in parallel with any standard request for supported authentication
mechanisms (i.e. `saslSupportedMechs`). This would permit clients to merge the contents of their first authentication
command with their initial handshake request, and receive the first authentication reply along with the initial
handshake reply.

When the mechanism is `MONGODB-X509`, `speculativeAuthenticate` has the same structure as seen in the MONGODB-X509
conversation section in the [Driver Authentication spec](../auth/auth.md#supported-authentication-methods).

When the mechanism is `SCRAM-SHA-1` or `SCRAM-SHA-256`, `speculativeAuthenticate` has the same fields as seen in the
conversation subsection of the SCRAM-SHA-1 and SCRAM-SHA-256 sections in the
[Driver Authentication spec](../auth/auth.md#supported-authentication-methods) with an additional `db` field to specify
the name of the authentication database.

When the mechanism is `MONGODB-OIDC`, `speculativeAuthenticate` has the same structure as seen in the MONGODB-OIDC
conversation section in the [Driver Authentication spec](../auth/auth.md#supported-authentication-methods).

If the initial handshake command with a `speculativeAuthenticate` argument succeeds, the client should proceed with the
next step of the exchange. If the initial handshake response does not include a `speculativeAuthenticate` reply and the
`ok` field in the initial handshake response is set to 1, drivers MUST authenticate using the standard authentication
handshake.

The `speculativeAuthenticate` reply has the same fields, except for the `ok` field, as seen in the conversation sections
for MONGODB-X509, SCRAM-SHA-1 and SCRAM-SHA-256 in the
[Driver Authentication spec](../auth/auth.md#supported-authentication-methods).

Drivers MUST NOT validate the contents of the `saslSupportedMechs` attribute of the initial handshake reply. Drivers
MUST NOT raise an error if the `saslSupportedMechs` attribute of the reply includes an unknown mechanism.

If an authentication mechanism is not provided either via connection string or code, but a credential is provided,
drivers MUST use the SCRAM-SHA-256 mechanism for speculative authentication and drivers MUST send `saslSupportedMechs`.

Older servers will ignore the `speculativeAuthenticate` argument. New servers will participate in the standard
authentication conversation if this argument is missing.

## Supporting Wrapping Libraries

Drivers MUST allow libraries which wrap the driver to append to the client metadata generated by the driver. The
following class definition defines the options which MUST be supported:

```typescript
class DriverInfoOptions {
    /**
    * The name of the library wrapping the driver.
    */
    name: String;

    /**
    * The version of the library wrapping the driver.
    */
    version: Optional<String>;

    /**
    * Optional platform information for the wrapping driver.
    */
    platform: Optional<String>;
}
```

Two `DriverInfoOptions` objects are considered equal if they would result in the same metadata in the client handshake.
In practice, this means if a field is the empty string (`""`), treat it as unset. Assert that each field is strictly
equal with case sensitive string comparison.

Note that how these options are provided to a driver during `MongoClient` initialization is left up to the implementer.

### Metadata updates after MongoClient initialization

Drivers MUST provide an API that allows appending `DriverInfoOptions` to a `MongoClient` instance after initialization,
adhering to the pattern described below while following idioms of the language of the driver:

```java
interface MongoClient {
  void appendMetadata(DriverInfoOptions driverInfoOptions);
  // other existing members of MongoClient
}
```

After client metadata update, drivers MUST apply updated metadata to newly created connections. Drivers MUST NOT apply
updated metadata to already established connections, create new connections, or close existing connections solely for
the purpose of transferring updated metadata.

### Appending metadata

If `DriverInfoOptions` are provided during or after `MongoClient` initialization, these options MUST NOT replace any
existing metadata values, including driver-generated metadata and previously provided options. The provided options MUST
be appended to their respective fields, and be delimited by a `|` character. For example, when
[Motor](https://www.mongodb.com/docs/drivers/motor/) wraps PyMongo, the following fields are updated to include Motor's
"driver info":

```typescript
{
    client: {
        driver: {
            name: "PyMongo|Motor",
            version: "3.6.0|2.0.0"
        }
    }
}
```

Entries in `driver.name` and `driver.version` MUST correspond one-to-one by index, so that splitting both fields on the
delimiter and pairing them by position recovers which version belongs to which library. Every set of `DriverInfoOptions`
MUST contribute exactly one entry to each field, and an unset field MUST contribute an empty entry rather than being
skipped. Empty entries are significant and MUST NOT be stripped, including when they are trailing. For example, if
`Framework2` reports no version:

```typescript
{
    client: {
        driver: {
            name: "PyMongo|Framework1|Framework2|Framework3",
            version: "3.6.0|1.5||3.5"
        }
    }
}
```

Without the empty entry, `3.5` would appear to belong to `Framework2`.

This requirement does not apply to `platform`, which is a single field with no counterpart to align against.

Some client libraries provide APIs that accept a pre-initialized MongoClient as an argument. In these circumstances, it
is possible for multiple library objects to be associated with the same MongoClient, which could result in the same
metadata being appended multiple times. Drivers MUST ensure that any duplicate `DriverInfoOptions` objects provided to a
MongoClient or appended to a MongoClient do not result in additional metadata being appended. See
[Supporting Wrapping Libraries](#supporting-wrapping-libraries).

Two `DriverInfoOptions` are duplicates only when every field is equal. Drivers MUST NOT compare fields in isolation: two
distinct libraries that happen to report the same version are not duplicates, and both MUST contribute an entry.
Suppressing one of them would break the index correspondence between `driver.name` and `driver.version`.

> [!NOTE]
> All strings provided as part of the driver info MUST NOT contain the delimiter used for metadata concatenation.
> Drivers MUST throw an error if any of these strings contains that character.

### Deviations

Some drivers have already implemented such functionality, and should not be required to make breaking changes to comply
with the requirements set forth here. A non-exhaustive list of acceptable deviations are as follows:

- The name of `DriverInfoOptions` is non-normative, implementers may feel free to name this whatever they like.
- The choice of delimiter is not fixed, `|` is the recommended value, but some drivers currently use `/`.
- For cases where we own a particular stack of drivers (more than two), it may be preferable to accept a *list* of
    strings for each field.

## Limitations

The entire `client` metadata BSON document MUST NOT exceed 512 bytes. This includes all BSON overhead. The
`client.application.name` cannot exceed 128 bytes. MongoDB will return an error if these limits are not adhered to,
which will result in handshake failure. Drivers MUST validate these values and truncate or omit driver provided values
if necessary. Implementers SHOULD cumulatively update fields in the following order until the document is under the size
limit:

1. Omit fields from `env` except `env.name` and `env.agent`.
2. Omit `env.agent`. If `env` then has no remaining fields, omit `env` entirely.
3. Omit fields from `os` except `os.type`.
4. Omit the `env` document entirely.
5. Truncate `platform`.

`env.agent` is omitted before `env.name` because drivers have reported `env.name` since before `env.agent` existed.

Additionally, implementers are encouraged to place high priority information about the platform earlier in the string,
in order to avoid possible truncating of those details.

## Motivation For Change

Being able to annotate individual connections with custom data will allow users and sysadmins to easily correlate events
happening on their MongoDB deployment to a specific application. For support engineers, it furthermore helps identify
potential problems in drivers or client platforms, and paves the way for providing proactive support via Cloud Manager
and/or Atlas to advise customers about out of date driver versions.

## Design Rationale

Drivers run on a multitude of platforms, languages, environments and systems. There is no defined list of data points
that may or may not be valuable to every system. Rather than specifying such a list it was decided we would report the
basics; something that everyone can discover and consider valuable. The obvious requirement here being the driver itself
and its version. Any additional information is generally very system specific. Scala may care to know the Java runtime,
while Python would like to know if it was built with C extensions - and C would like to know the compiler.

Having to define dozens of arguments that may or may not be useful to one or two drivers isn't a good idea. Instead, we
define a `platform` argument that is driver dependent. This value will not have defined value across drivers and is
therefore not generically queryable -- however, it will gain defined schema for that particular driver, and will
therefore over time gain defined structure that can be formatted and value extracted from.

## Backwards Compatibility

The legacy hello command currently ignores arguments. (i.e. If arguments are provided the legacy hello command discards
them without erroring out). Adding client metadata functionality has therefore no backwards compatibility concerns.

This also allows a driver to determine if the `hello` command is supported. On server versions that support the `hello`
command, the legacy hello command with `helloOk: true` will respond with `helloOk: true`. On server versions that do not
support the `hello` command, the `helloOk: true` argument is ignored and the legacy hello response will not contain
`helloOk: true`.

## Reference Implementation

[C Driver](https://github.com/mongodb/mongo-c-driver/blob/master/src/libmongoc/src/mongoc/mongoc-handshake.c).

## Q&A

- The 128 bytes application.name limit, does that include BSON overhead

    - No, just the string itself

- The 512 bytes limit, does that include BSON overhead?

    - Yes

- The 512 bytes limit, does it apply to the full initial handshake document or just the `client` subdocument

    - Just the subdocument

- Should I really try to fill the 512 bytes with data?

    - Not really. The server does not attempt to normalize or compress this data in anyway, so it will hold it in memory
        as-is per connection. 512 bytes for 20,000 connections is ~ 10mb of memory the server will need.

- What happens if I pass new arguments in the legacy hello command to previous MongoDB versions?

    - Nothing. Arguments passed to the legacy hello command to prior versions of MongoDB are not treated in any special
        way and have no effect one way or another.

- Are there wire version bumps or anything accompanying this specification?

    - No

- Does this affect SDAM implementations?

    - Possibly. There are a couple of gotchas. If the application.name is not in the URI...
        - The SDAM monitoring cannot be launched until the user has had the ability to set the application name because the
            application name has to be sent in the initial handshake. This means that the connection pool cannot be
            established until the first user initiated command, or else some connections will have the application name
            while other won't
        - The initial handshake must be called on all sockets, including administrative background sockets to MongoDB

- My language doesn't have `uname`, but does instead provide its own variation of these values, is that OK?

    - Absolutely. As long as the value is identifiable it is fine. The exact method and values are undefined by this
        specification

## Changelog

- 2026-09-22: Add `env.agent` to `client` document for agentic client identification.
- 2026-09-11: Require `driver.name` and `driver.version` entries to correspond by index, and clarify that duplicate
    detection compares whole `DriverInfoOptions`.
- 2026-06-25: Clarify the client backpressure component of the handshake.
- 2026-06-17: Remove pre-4.2 version references.
- 2026-06-11: Clarify that there is no new behavior as a result of only using OP_MSG for all handshakes.
- 2026-06-05: Use OP_MSG for all handshakes.
- 2025-09-04: Clarify that drivers do not append the same metadata multiple times.
- 2025-06-09: Add requirement to allow appending to client metadata after `MongoClient` initialization.
- 2024-11-05: Move handshake prose tests from spec file to prose test file.
- 2024-10-09: Clarify that FaaS and container metadata must both be populated when both are present.
- 2024-08-16: Migrated from reStructuredText to Markdown.
- 2019-11-13: Added section about supporting wrapping libraries
- 2020-02-12: Added section about speculative authentication
- 2021-04-27: Updated to define `hello` and legacy hello
- 2022-01-13: Updated to disallow `hello` using `OP_QUERY`
- 2022-01-19: Require that timeouts be applied per the client-side operations timeout spec.
- 2022-02-24: Rename Versioned API to Stable API
- 2022-10-05: Remove spec front matter and reformat changelog.
- 2023-03-13: Add `env` to `client` document
- 2023-04-03: Simplify truncation for metadata
- 2023-05-04: `AWS_EXECUTION_ENV` must start with `"AWS_Lambda_"`
- 2023-08-24: Added container awareness
- 2024-04-22: Clarify that driver should not validate `saslSupportedMechs` content.

[^1]: `AWS_EXECUTION_ENV` must start with the string `"AWS_Lambda_"`.
