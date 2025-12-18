# Snapshot Reads Specification

- Status: Accepted
- Minimum Server Version: 5.0

______________________________________________________________________

## Abstract

Version 5.0 of the server introduces support for read concern level "snapshot" (non-speculative) for read commands
outside of transactions, including on secondaries. This spec builds upon the
[Sessions Specification](./driver-sessions.md) to define how an application requests "snapshot" level read concern and
how a driver interacts with the server to implement snapshot reads.

## Definitions

### META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

### Terms

**ClientSession**

The driver object representing a client session and the operations that can be performed on it.

**MongoClient**

The root object of a driver's API. MAY be named differently in some drivers.

**MongoCollection**

The driver object representing a collection and the operations that can be performed on it. MAY be named differently in
some drivers.

**MongoDatabase**

The driver object representing a database and the operations that can be performed on it. MAY be named differently in
some drivers.

**ServerSession**

The driver object representing a server session.

**Session**

A session is an abstract concept that represents a set of sequential operations executed by an application that are
related in some way. This specification defines how sessions are used to implement snapshot reads.

**Snapshot reads**

Reads with read concern level `snapshot` that occur outside of transactions on both the primary and secondary nodes,
including in sharded clusters. Snapshots reads are majority committed reads.

**Snapshot timestamp**

Snapshot timestamp, representing timestamp of the first supported read operation (i.e. find/aggregate/distinct) in the
session. The server creates a cursor in response to a snapshot find/aggregate command and reports `atClusterTime` within
the `cursor` field in the response. For the distinct command the server adds a top-level `atClusterTime` field to the
response. The `atClusterTime` field represents the timestamp of the read and is guaranteed to be majority committed.

## Specification

An application requests snapshot reads by creating a `ClientSession` with options that specify that snapshot reads are
desired and optionally specifying a `snapshotTime`. An application then passes the session as an argument to methods in
the `MongoDatabase` and `MongoCollection` classes. Read operations (find/aggregate/distinct) performed against that
session will be read from the same snapshot.

## High level summary of the API changes for snapshot reads

Snapshot reads are built on top of client sessions.

Applications will start a new client session for snapshot reads and possibly retrieve the snapshot time like this:

```typescript
options = new SessionOptions(snapshot = true, snapshotTime = timestampValue);
session = client.startSession(options);
snapshotTime = session.snapshotTime;
```

All read operations performed using this session will be read from the same snapshot.

If no value is provided for `snapshot` a value of false is implied. `snapshotTime` is an optional parameter and if not
passed the snapshot time will be set internally after the first find/aggregate/distinct operation inside the session.

There are no MongoDatabase, MongoClient, or MongoCollection API changes.

## SessionOptions changes

`SessionOptions` change summary

```typescript
class SessionOptions {
    Optional<bool> snapshot;
    Optional<BsonTimestamp> snapshotTime;

    // other options defined by other specs
}
```

In order to support snapshot reads two properties called `snapshot` and `snapshotTime` are added to `SessionOptions`.
Applications set `snapshot` when starting a client session to indicate whether they want snapshot reads and optionally
set `snapshotTime` to specify the desired snapshot time beforehand. All read operations performed using that client
session will share the same snapshot.

Each new member is documented below.

### snapshot

Applications set `snapshot` when starting a session to indicate whether they want snapshot reads.

Note that the `snapshot` property is optional. The default value of this property is false.

Snapshot reads and causal consistency are mutually exclusive. Therefore if `snapshot` is set to true,
`causalConsistency` must be false. Client MUST throw an error if both `snapshot` and `causalConsistency` are set to
true. Snapshot reads are supported on both primaries and secondaries.

### snapshotTime

Applications set `snapshotTime` when starting a snapshot session to specify the desired snapshot time.

Note that the `snapshotTime` property is optional. The default value of this property is null.

Client MUST throw an error if `snapshotTime` is set and `snapshot` is not set to true.

## ClientSession changes

A readonly property called `snapshotTime` will be added to `ClientSession` that allows applications to retrieve the
snapshot time of the session:

```typescript
class ClientSession {
    readonly Optional<BsonTimestamp> snapshotTime;

    // other options defined by other specs
}
```

The `snapshotTime` field MUST be immutable; in APIs that expose `snapshotTime` with  a getter, attempting to read it on a
non-snapshot session MUST raise an error.

Transactions are not allowed with snapshot sessions. Calling `session.startTransaction(options)` on a snapshot session
MUST raise an error.

## ReadConcern changes

`snapshot` added to [ReadConcernLevel enumeration](../read-write-concern/read-write-concern.md#read-concern).

## Server Commands

There are no new server commands related to snapshot reads. Instead, snapshot reads are implemented by:

1. If `snapshotTime` is specified in `SessionOptions`, saving the value in a `snapshotTime` property of the
    `ClientSession`.
2. If `snapshotTime` is not specified in `SessionOptions`, saving the `atClusterTime` returned by 5.0+ servers for the
    first find/aggregate/distinct operation in a `snapshotTime` property of the `ClientSession` object. Drivers MUST
    save `atClusterTime` in the `ClientSession` object.
3. Passing that `snapshotTime` in the `atClusterTime` field of the `readConcern` field for subsequent snapshot read
    operations (i.e. find/aggregate/distinct commands).

## Server Command Responses

For find/aggregate commands the server returns `atClusterTime` within the `cursor` field of the response.

```typescript
{
    ok : 1 or 0,
    ... // the rest of the command reply
    cursor : {
        ... // the rest of the cursor reply
        atClusterTime : <BsonTimestamp>
    }
}
```

For distinct commands the server returns `atClusterTime` as a top-level field in the response.

```typescript
{
    ok : 1 or 0,
    ... // the rest of the command reply
    atClusterTime : <BsonTimestamp>
}
```

The `atClusterTime` timestamp MUST be stored in the `ClientSession` to later be passed as the `atClusterTime` field of
the `readConcern` with a `snapshot` level in subsequent read operations.

## Server Errors

1. The server may reply to read commands with a `SnapshotTooOld(239)` error if the client's `atClusterTime` value is not
    available in the server's history.
2. The server will return `InvalidOptions(72)` error if both `atClusterTime` and `afterClusterTime` options are set to
    true.
3. The server will return `InvalidOptions(72)` error if the command does not support readConcern.level "snapshot".

## Snapshot Read Commands

For snapshot reads the driver MUST first obtain `atClusterTime` from the server response of a find/aggregate/distinct
command, by specifying `readConcern` with `snapshot` level field, and store it as `snapshotTime` in the `ClientSession`
object.

```typescript
{
    find : <string>, // or other read command
    ... // the rest of the command parameters
    readConcern :
    {
        level : "snapshot"
    }
}
```

For subsequent reads in the same session, the driver MUST send the `snapshotTime` saved in the `ClientSession` as the
value of the `atClusterTime` field of the `readConcern` with a `snapshot` level:

```typescript
{
    find : <string>, // or other read command
    ... // the rest of the command parameters
    readConcern :
    {
        level : "snapshot",
        atClusterTime : <BsonTimestamp>
    }
}
```

Lists of commands that support snapshot reads:

1. find
2. aggregate
3. distinct

## Sending readConcern to the server on all commands

Drivers MUST set the readConcern `level` and `atClusterTime` fields (as outlined above) on all commands in a snapshot
session, including commands that do not accept a readConcern (e.g. insert, update). This ensures that the server will
return an error for invalid operations, such as writes, within a session configured for snapshot reads.

## Requires MongoDB 5.0+

Snapshot reads require MongoDB 5.0+. When the connected server's maxWireVersion is less than 13, drivers MUST throw an
exception with the message "Snapshot reads require MongoDB 5.0 or later".

## Motivation

To support snapshot reads. Only supported with server version 5.0+ or newer.

## Design Rationale

The goal is to modify the driver API as little as possible so that existing programs that don't need snapshot reads
don't have to be changed. This goal is met by defining a `SessionOptions` field that applications use to start a
`ClientSession` that can be used for snapshot reads. Alternative explicit approach of obtaining `atClusterTime` from
`cursor` object and passing it to read concern object was considered initially. A session-based approach was chosen as
it aligns better with the existing API, and requires minimal API changes. Future extensibility for snapshot reads would
be best served by a session-based approach, as no API changes will be required.

## Backwards Compatibility

The API changes to support snapshot reads extend the existing API but do not introduce any backward breaking changes.
Existing programs that don't use snapshot reads continue to compile and run correctly.

## Reference Implementation

C# driver will provide the reference implementation. The corresponding ticket is
[CSHARP-3668](https://jira.mongodb.org/browse/CSHARP-3668).

## Q&A

## Changelog

- 2025-12-17: Clarify snapshotTime semantics: the field is immutable, and accessing it on a non-snapshot session is an error.
- 2025-09-23: Exposed snapshotTime to applications.
- 2024-05-08: Migrated from reStructuredText to Markdown.
- 2021-06-15: Initial version.
- 2021-06-28: Raise client side error on < 5.0.
- 2021-06-29: Send readConcern with all snapshot session commands.
- 2021-07-16: Grammar revisions. Change SHOULD to MUST for startTransaction error to comply with existing tests.
- 2021-08-09: Updated client-side error spec tests to use correct syntax for `test.expectEvents`
- 2022-10-05: Remove spec front matter
