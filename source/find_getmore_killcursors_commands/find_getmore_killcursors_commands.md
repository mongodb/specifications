# Find, getMore and killCursors commands

- Status: Accepted
- Minimum Server Version: 3.2

## Abstract

The Find, GetMore and KillCursors commands in MongoDB 3.2 or later replace the use of the legacy OP_QUERY, OP_GET_MORE
and OP_KILL_CURSORS wire protocol messages. This specification lays out how drivers should interact with the new
commands when compared to the legacy wire protocol level messages.

## Definitions

### Meta

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

### Terms

#### Document

The term Document refers to the implementation in the driver's language of a BSON document.

#### Command

A BSON document containing the fields making up a MongoDB server command.

#### Wire Protocol

The binary protocol used to talk with MongoDB over a socket. It's made up by the OP_QUERY, OP_GET_MORE, OP_KILL_CURSORS,
OP_INSERT, OP_UPDATE and OP_DELETE.

## Guidance

### Documentation

The documentation provided in code below is merely for driver authors and SHOULD NOT be taken as required documentation
for the driver.

### Implementation

If the **hello** command returns **maxWireVersion >= 4**, drivers:

- MUST implement queries with the `find` command instead of `OP_QUERY`.
- MUST implement cursor operations with the `getMore` and `killCursors` commands instead of `OP_GET_MORE` and
  `OP_KILL_CURSORS`, respectively.
- MUST NOT use OP_QUERY except to execute commands.

## Commands

### find

The [find](https://www.mongodb.com/docs/manual/reference/command/find/) command replaces the query functionality of the
OP_QUERY wire protocol message but cannot execute queries against special collections. Unlike the legacy OP_QUERY wire
protocol message, the **find** command cannot be used to execute other commands.

For a successful command, the document returned from the server has the following format:

```javascript
{
  "cursor": {
    "id": <int64>,
    "ns": <string>,
    "firstBatch": [
      ...
    ]
  },
  "ok": 1
}
```

#### Special Collection names

The find command **does not support querying on system collections**, so if drivers are using any system collections
instead of the inprog, killop, unlock, etc. commands they SHOULD default to using the old-style OP_QUERY.

Any driver that provides helpers for any of the special collections below SHOULD use the replacement commands if
**hello.maxWireVersion >=4** or higher.

| Special collection name        | Replacement Command |
| ------------------------------ | ------------------- |
| `$cmd.sys.inprog`              | currentOp           |
| `$cmd.sys.unlock`              | fsyncUnlock         |
| `<database>.system.indexes`    | listIndexes         |
| `<database>.system.namespaces` | listCollections     |

Special Collection Names

#### Exhaust

This section only applies to drivers that support exhaust cursors.

The exhaust protocol differs based on the server version:

| Server version  | Server behavior                                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------------------------------- |
| 4.0 and earlier | Only supports exhaust over legacy **OP_QUERY**. The **find** command does not support the exhaust flag from **OP_QUERY**. |
| 4.2 to 5.0      | Supports exhaust both over legacy **OP_QUERY** and **OP_MSG**.                                                            |
| 5.1 and later   | Supports exhaust over **OP_MSG**.                                                                                         |

Therefore drivers that implement exhaust cursors:

| Server version  | Driver behavior                                                                                                                    |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 4.0 and earlier | Drivers MUST use legacy **OP_QUERY**.                                                                                              |
| 4.2 to 5.0      | Drivers SHOULD use **OP_MSG** but MAY use legacy **OP_QUERY**.                                                                     |
| 5.1 and later   | Drivers MUST only use **OP_MSG**. Alternatively, drivers MAY fallback to a non-exhaust cursor when an exhaust cursor is requested. |

#### Interactions with OP_QUERY

When sending a find operation as a find command rather than a legacy **OP_QUERY** find only the **secondaryOk** flag is
honored of the flags available in the **flag** field on the wire protocol.

For the **find**, **getMore** and **killCursors** commands the **numberToReturn** field SHOULD be -1. To execute
**find** commands against a secondary the driver MUST set the **secondaryOk** bit for the **find** command to
successfully execute.

The **secondaryOk** flag SHOULD not be set for all follow-up **getMore** and **killCursors** commands. The cursor on the
server keeps the original **secondaryOk** value first set on the **find** command.

More detailed information about the interaction of the **secondaryOk** with **OP_QUERY** can be found in the Server
Selection Spec [Passing a Read Preference](../server-selection/server-selection.md#passing-read-preference-to-mongos).

#### Behavior of Limit, skip and batchSize

The **find** command has different semantics to the existing 3.0 and earlier **OP_QUERY** wire protocol message. The
**limit** field is a hard limit on the total number of documents returned by the cursor no matter what **batchSize** is
provided. This includes other limiting operations, such as the **$limit** aggregation pipeline stage. This differs from
existing **OP_QUERY** behavior where there is no server-side concept of limit and where the driver **MUST** keep track
of the limit on the client side and **MUST** send a **OP_KILL_CURSORS** wire protocol message when the limit is reached.

When setting the **batchSize** on the **find** and **getMore** commands the value of **batchSize** **MUST** be based on
the cursor limit calculations specified in the [CRUD](../crud/crud.md#find) specification.

Note that with 5.0, the server-side handling of cursors with a limit has changed. Before 5.0, some cursors were
automatically closed when the limit was reached (e.g. when running **find** with **limit**), and the reply document did
not include a cursor ID (i.e. `cursor.id` was `0`). Starting with 5.0, all cursor-producing operations will return a
cursor ID if the end of the batch being returned lines up with the limit on the cursor. In this case, drivers **MUST**
ensure the cursor is closed on the server, either by exhausting the cursor or by using **killCursors** to kill it.

In the following example the **limit** is set to **4** and the **batchSize** is set to **3** the following commands are
executed. The last command is either **killCursors** or **getMore**, depending on how a driver ensures the cursor is
closed on 5.0:

```javascript
{find: ..., batchSize:3, limit:4}
{getMore: ..., batchSize:1} // Returns remaining items but leaves cursor open on 5.0+
{...}          // Kills server-side cursor. Necessary on 5.0+
```

If there are not enough documents in the cursor to fulfill the **limit** defined, the cursor runs to exhaustion and is
closed, returning a cursorId of 0 to the client.

Below are are some examples of using **limit**, **skip** and **batchSize**.

We have 100 documents in the collection **t**. We execute the following **find** command in the shell.

```javascript
var b = db.runCommand({find:"t", limit:20, batchSize:10});
db.runCommand({getMore:b.cursor.id, collection:"t", batchSize:20});
```

The **find** command executes and returns the first 10 results. The **getMore** command returns the final 10 results
reaching the **limit** of 20 documents.

The **skip** option works in the same way as the current **OP_QUERY** starting the cursor after skipping **n** number of
documents of the query.

```javascript
var b = db.runCommand({find:"t", limit:20, batchSize:10, skip:85});
db.runCommand({getMore:b.cursor.id, collection:"t", batchSize:20});
```

The **find** command returns the documents 86-95 and the **getMore** returns the last 5 documents.

#### Mapping OP_QUERY behavior to the find command limit and batchSize fields

The way that limit, batchSize and singleBatch are defined for the find command differs from how these were specified in
OP_QUERY and the CRUD spec.

Specifically, *negative* values for **limit** and **batchSize** are no longer allowed and the **singleBatch** option is
used instead of negative values.

In order to have consistency between old and new applications, the following transformations MUST be performed before
adding options to the **find** command:

```
singleBatch = (limit < 0) || (batchSize < 0)
limit       = abs(limit)
if singleBatch:
    batchSize = (limit == 0) ? abs(batchSize) : limit
else:
    batchSize = abs(batchSize)
```

Further, after these transformation:

- If **limit** is zero, it MUST be omitted from **find** options
- If **batchSize** is zero, it MUST be omitted from **find** options
- If **singleBatch** is false, it MUST be omitted from **find** options

#### BatchSize of 1

In 3.2 a batchSize of 1 means return a single document for the find command and it will not destroy the cursor after the
first batch of documents are returned. Given a query returning 4 documents the number of commands issues will be.

1. **find** command with batchSize=1
2. **getMore** command with batchSize=1
3. **getMore** command with batchSize=1
4. **getMore** command with batchSize=1

The driver **SHOULD NOT attempt to emulate the behavior seen in 3.0 or earlier** as the new find command enables the
user expected behavior of allowing the first result to contain a single document when specifying batchSize=1.

#### Tailable cursors

By default, most cursors are non-tailable. For example, a typical `find` cursor is exhausted when all results for the
filter have been returned. MongoDB also supports creating cursors that "tail" or follow the target namespace for new
data. This is done via the `find` command's `tailable` option. Querying a capped collection is one use case for a
tailable cursor. A tailable cursor can receive `getMore` responses with an empty `nextBatch` array, which does not
indicate that the cursor has been exhausted.

Additionally, tailable cursors may "await data" from the server, which means that the server will wait to respond to the
client's `getMore` command until new data is available or some period of time has elapsed, whichever comes first. A
tailable `find` cursor can be configured using the `awaitData` option. The amount of time the server will wait for new
data is based on the `maxTimeMS` field of the `getMore` (or server default if unspecified). If the time does expire an
empty batch will be returned. A `maxTimeMS` field cannot be sent if the cursor was not configured with `awaitData=true`.

To create a tailable `find` cursor you execute the following command:

```typescript
interface FindCommand {
  /** The namespace to run the find command on */
  find: string;
  /** The filter to control what documents are returned */
  filter: BSONDocument;
  /** Informs the server whether to keep the cursor open even when there are no results to satisfy the query */
  tailable?: boolean;
  /**
   * Informs the server whether to block on a `getMore`'s `maxTimeMS` before returning an empty `nextBatch`.
   * This must be set if getMores are to include `maxTimeMS` values.
   */
  awaitData?: boolean;
  /** Controls the amount of milliseconds the server will allow the operations to run for */
  maxTimeMS?: PositiveIntegerNumber;
  // ... Note: additional options unrelated to tailable cursors omitted
}
```

If **maxTimeMS** is not set in FindOptions, the driver SHOULD refrain from setting **maxTimeMS** on the **find** or
**getMore** commands issued by the driver and allow the server to use its internal default value for **maxTimeMS**.

#### Semantics of maxTimeMS for a Driver

In the case of a **non-tailable cursor query** OR **a tailable cursor query with awaitData == false**, the driver MUST
set maxTimeMS on the **find** command and MUST NOT set maxTimeMS on the **getMore** command.

In the case of **a tailable cursor with awaitData == true** the driver MUST provide a Cursor level option named
**maxAwaitTimeMS** (See CRUD specification for details). The **maxTimeMS** option on the **getMore** command MUST be set
to the value of the option **maxAwaitTimeMS**. If no **maxAwaitTimeMS** is specified, the driver SHOULD not set
**maxTimeMS** on the **getMore** command.

### getMore

The [getMore](https://www.mongodb.com/docs/manual/reference/command/getMore/) command replaces the **OP_GET_MORE** wire
protocol message. The query flags passed to OP_QUERY for a getMore command MUST be secondaryOk=true when sent to a
secondary. The OP_QUERY namespace MUST be the same as for the **find** and **killCursors** commands.

```typescript
interface GetMoreCommand {
  /** Set to the nonzero cursor id */
  getMore: int64;
  /** Set to the namespace returned by the initial command response */
  collection: string;
  /**
   * User configurable document count for the batch returned for this getMore.
   * Only attached to command document if nonzero.
   */
  batchSize?: PositiveIntegerNumber;
  /**
   * User configurable time limit enforced by the server.
   */
  maxTimeMS?: PositiveIntegerNumber;
  /**
   * User configurable comment that can be used to identify the operation in logs.
   * This can be any BSON value.
   */
  comment?: BSONValue;
}
```

On success, the getMore command will return the following:

```typescript
interface GetMoreResponse {
  ok: 1;
  cursor: {
    /** The cursor id, this may be equal to zero indicating the cursor is exhausted or closed */
    id: int64;
    /**
     * The namespace the cursor is running on.
     * This value may be different than the namespace the driver started the cursor on, for example, database level aggregations.
     */
    ns: string;
    /**
     * The next batch of documents.
     * This array may be empty, in the case of a tailable cursor, which DOES NOT indicate the cursor is exhausted.
     */
    nextBatch: BSONArray<BSONDocument>;
  }
  // ... Note: additional non-relevant fields omitted
}
```

The driver's local cursor MUST update its `id` and `ns`, as well as store the `nextBatch` from every `getMore` response.

### killCursors

The [killCursors](https://www.mongodb.com/docs/manual/reference/command/killCursors/) command replaces the
**OP_KILL_CURSORS** wire protocol message. The OP_QUERY namespace MUST be the same as for the **find** and **getMore**
commands. The **killCursors** command is optional to implement in **MongoDB 3.2**.

The command response will be as follows:

```javascript
{
  "cursorsKilled": [
    <cursor id 1>
    <cursor id 2>,
    ...
    <cursor id n>
  ],
  "cursorsNotFound": [
    <cursor id 1>
    <cursor id 2>,
    ...
    <cursor id n>
  ],
  "cursorsAlive": [
    <cursor id 1>
    <cursor id 2>,
    ...
    <cursor id n>
  ],
  ok: 1
}
```

The **cursorsAlive** array contain cursors that were not possible to kill. The information SHOULD be ignored by the
driver.

#### Difference from 3.0 OP_KILL_CURSORS

One of the differences with the new **killCursors** command compared to the **OP_KILL_CURSORS** wire protocol message is
that the **killCursors** command returns a response while the **OP_KILL_CURSORS** wire protocol does not.

The **OP_REPLY** message has the following general structure.

```javascript
struct {
    int32     messageLength;  // total message size, including
                              // this

    int32     requestID;      // identifier for this message

    int32     responseTo;     // requestID from the original
                              // request(used in responses from db)

    int32     opCode;         // request type - see table below

    int32     responseFlags;  // bit vector - see details below

    int64     cursorID;       // cursor id if client needs to do
                              // get more's

    int32     startingFrom;   // where in the cursor this reply is
                              // starting

    int32     numberReturned; // number of documents in the reply

    document* documents;      // documents
}
```

For the **find**, **getMore** and **killCursors** MongoDB returns a single document meaning **numberReturned** is set to
**1**. This is in contrast to MongoDB 3.0 and earlier where a **OP_QUERY** query will set **numberReturned** to >= 0.

A driver MUST deserialize the command result and extract the **firstBatch** and **nextBatch** arrays for the **find**
and **getMore** commands to access the returned documents.

The result from the **killCursors** command MAY be safely ignored.

If the driver supports returning **raw** BSON buffers instead of deserialized documents there might be a need to be able
to partially deserialize documents to be able to efficiently provide the behavior in comparison to existing **OP_QUERY**
queryresults.

## Errors

The **find** and **getMore** commands will report errors using the standard mechanism: an "ok: 0" field paired with
"errmsg" and "code" fields. See below for example error responses:

```javascript
db.runCommand({find: "t", sort: {padding: -1}})
```

```javascript
{
  "errmsg" : "exception: Executor error: Overflow sort stage buffered data usage of 41630570 bytes exceeds internal limit of 33554432 bytes",
  "code" : 28616,
  "ok" : 0
}
```

```javascript
db.runCommand({find: "t", foo: "bar"})
```

```javascript
{
  "ok" : 0,
  "errmsg" : "Failed to parse: { find: \"t\", foo: \"bar\" }. Unrecognized field 'foo'.",
  "code" : 2
}
```

Like other commands, the find and getMore commands will not use the OP_REPLY response flags.
[OP_REPLY Documentation](https://www.mongodb.com/docs/meta-driver/latest/legacy/mongodb-wire-protocol/#op-reply)

## FAQ

### Changes in error handling for 3.2 tailable cursor

Tailable cursors pointing to documents in a capped collection that get overwritten will return a zero document result in
MongoDB 3.0 or earlier but will return an error in MongoDB 3.2

### Explain command

There is no equivalent of the `$explain` modifier in the find command. The driver SHOULD use the **explain** command.
Information about the command can be found in the
[Explain command reference](https://www.mongodb.com/docs/manual/reference/command/explain/).

### ReadPreference and Mongos

The **find** command does not include a readPreference field. To pass a readPreference to a **mongos** use the
**$readPreference** field and format your command as.

```javascript
{$query: {find: ...}, $readPreference: {}}
```

This format is general for all commands when executing against a Mongos proxy.

More in depth information about passing read preferences to Mongos can be found in the Server Selection Specification
[Server Selection Specification](../server-selection/server-selection.md#passing-read-preference-to-mongos).

## Changelog

- 2024-07-30: Migrated from reStructuredText to Markdown.

- 2023-05-10: Improve tailable cursor description and update the `getMore` section code blocks.

- 2022-10-05: Remove spec front matter and reformat changelog.

- 2022-02-01: Replace examples/tables for find, getMore, and killCursors with server manual links.

- 2021-12-14: Exhaust cursors may fallback to non-exhaust cursors on 5.1+ servers. Relax requirement of OP_MSG for
  exhaust cursors.

- 2021-08-27: Exhaust cursors must use OP_MSG on 3.6+ servers.

- 2021-04-06: Updated to use hello and secondaryOk.

- 2015-10-21: If no **maxAwaitTimeMS** is specified, the driver SHOULD not set **maxTimeMS** on the **getMore** command.

- 2015-10-13: Added guidance on batchSize values as related to the **getMore** command. Legacy secondaryOk flag SHOULD
  not be set on getMore and killCursors commands. Introduced maxAwaitTimeMS option for setting maxTimeMS on getMore
  commands when the cursor is a tailable cursor with awaitData set.

- 2015-09-30: Legacy secondaryOk flag must be set to true on **getMore** and **killCursors** commands to make drivers
  have same behavior as for OP_GET_MORE and OP_KILL_CURSORS.
