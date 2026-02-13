# MongoDB Driver Implementation Guide

**Status**: Non-Normative  
**Version**: 1.0  
**Last Updated**: 2026-02-13

---

## About This Guide

This guide provides a narrative introduction to implementing a MongoDB driver. It explains concepts progressively, building from foundational ideas to advanced features. 

**This guide is NOT a specification.** It is intended to help you understand how the various MongoDB driver specifications fit together and build a mental model of driver architecture. For normative requirements, always consult the individual specifications linked throughout this document.

### How to Use This Guide

- **If you're new to MongoDB drivers**: Read this guide sequentially to build understanding
- **If you're implementing a feature**: Use this guide to understand context, then consult the relevant specifications for precise requirements
- **If you're debugging**: Use this guide to understand how components interact

### Normative vs. Non-Normative

- **Normative specifications** (the individual spec files) contain precise requirements using RFC 2119 keywords (MUST, SHOULD, MAY)
- **This guide** uses plain language to explain concepts and is explicitly non-normative
- When in doubt, the individual specifications are authoritative

---

## Table of Contents

### Part I: Foundations
1. [Introduction to MongoDB Drivers](#part-i-foundations)
2. [The Wire Protocol: How Drivers Talk to MongoDB](#chapter-2-the-wire-protocol)
3. [BSON: MongoDB's Data Format](#chapter-3-bson)
4. [Connection Management](#chapter-4-connection-management)

### Part II: Server Interaction
5. [Server Discovery and Monitoring (SDAM)](#part-ii-server-interaction)
6. [Server Selection: Choosing Where to Send Operations](#chapter-6-server-selection)
7. [Connection Pooling (CMAP)](#chapter-7-connection-pooling)

### Part III: Building Operations
8. [Understanding Operation Context](#part-iii-building-operations)
9. [Driver Sessions: The Foundation](#chapter-9-driver-sessions)
10. [Transactions: Multi-Statement ACID Operations](#chapter-10-transactions)
11. [Retryable Operations: Handling Transient Failures](#chapter-11-retryable-operations)
12. [Command Construction: Putting It All Together](#chapter-12-command-construction)

### Part IV: Core Operations
13. [CRUD Operations](#part-iv-core-operations)
14. [Read and Write Concerns](#chapter-14-read-and-write-concerns)
15. [Collation and Internationalization](#chapter-15-collation)

### Part V: Advanced Features
16. [Change Streams: Watching for Changes](#part-v-advanced-features)
17. [Client-Side Operations Timeout (CSOT)](#chapter-17-csot)
18. [GridFS: Storing Large Files](#chapter-18-gridfs)
19. [Client-Side Encryption](#chapter-19-client-side-encryption)

### Part VI: Observability and Testing
20. [Command Monitoring and Logging](#part-vi-observability-and-testing)
21. [Connection Monitoring (CMAP Events)](#chapter-21-connection-monitoring)
22. [Testing Your Driver](#chapter-22-testing)

### Part VII: Additional Topics
23. [Authentication](#part-vii-additional-topics)
24. [Stable API (Versioned API)](#chapter-24-stable-api)
25. [Load Balancer Support](#chapter-25-load-balancers)
26. [SOCKS5 Proxy Support](#chapter-26-socks5)

---

# Part I: Foundations

## Chapter 1: Introduction to MongoDB Drivers

### What is a MongoDB Driver?

A MongoDB driver is a library that allows applications to communicate with MongoDB servers. It handles:

- **Connection management**: Establishing and maintaining connections to MongoDB servers
- **Protocol translation**: Converting application-level operations into wire protocol messages
- **Data serialization**: Encoding/decoding data between your language's types and BSON
- **Error handling**: Managing network failures, server errors, and retry logic
- **Topology awareness**: Discovering servers and routing operations appropriately

### The Driver Architecture Stack

Think of a driver as having several layers, from lowest to highest:

```
┌─────────────────────────────────────┐
│   Application API (CRUD, etc.)     │  ← What users call
├─────────────────────────────────────┤
│   Operation Construction            │  ← Building commands
├─────────────────────────────────────┤
│   Session & Transaction Management  │  ← Operation context
├─────────────────────────────────────┤
│   Server Selection                  │  ← Choosing a server
├─────────────────────────────────────┤
│   Connection Pooling                │  ← Managing connections
├─────────────────────────────────────┤
│   Server Discovery (SDAM)           │  ← Topology monitoring
├─────────────────────────────────────┤
│   Wire Protocol (OP_MSG)            │  ← Network communication
├─────────────────────────────────────┤
│   BSON Encoding/Decoding            │  ← Data serialization
└─────────────────────────────────────┘
```

This guide will walk through these layers from bottom to top, building your understanding progressively.

### Key Principles

Before diving in, understand these core principles from the [Driver Mantras](driver-mantras.md):

1. **Drivers are thin wrappers**: Don't add business logic; expose MongoDB's capabilities
2. **Consistency across languages**: Similar APIs across all drivers (within language idioms)
3. **Fail fast**: Validate early, report errors clearly
4. **Performance matters**: Minimize overhead, reuse connections, batch when possible

---

## Chapter 2: The Wire Protocol

### How Drivers Talk to MongoDB

At the lowest level, drivers communicate with MongoDB using a binary protocol over TCP connections. Understanding this protocol helps you understand why certain design decisions were made in higher layers.

### OP_MSG: The Modern Protocol

Since MongoDB 3.6, all communication uses the **OP_MSG** protocol. It's a flexible message format that supports:

- **Commands**: All operations are expressed as commands (e.g., `{find: "collection", filter: {...}}`)
- **Document sequences**: Efficient bulk operations
- **Metadata**: Flags and checksums for reliability

**Key insight**: When you call `collection.find({x: 1})`, your driver:
1. Constructs a command document: `{find: "collection", filter: {x: 1}}`
2. Wraps it in an OP_MSG message
3. Sends it over a TCP connection
4. Receives an OP_MSG response
5. Extracts the result documents

**Normative specification**: [OP_MSG specification](https://github.com/mongodb/specifications/blob/master/source/message/OP_MSG.md)

### The Command Pattern

Everything in modern MongoDB is a command. Even operations that feel like "queries" are actually commands:

- `find` command (not a query)
- `insert` command
- `update` command
- `aggregate` command
- `hello` command (for server discovery)

This uniformity simplifies driver implementation. You need one mechanism to send commands and receive responses.

### Global Command Arguments

Some arguments can be attached to any command:

- `$db`: The database name
- `lsid`: Logical session ID (more on this in Chapter 9)
- `txnNumber`: Transaction number for retryable operations (Chapter 11)
- `$clusterTime`: For causal consistency (Chapter 9)
- `$readPreference`: For routing reads (Chapter 6)

**Key insight**: These "global" arguments are why sessions, transactions, and retryable operations can work across all operation types without changing each command's core structure.

---

## Chapter 3: BSON

### MongoDB's Data Format

BSON (Binary JSON) is how MongoDB stores and transmits data. Your driver must encode application data to BSON and decode BSON to application types.

### Why BSON Matters to Driver Design

BSON isn't just an implementation detail—it affects your driver's API:

1. **Type system**: BSON has types your language might not (e.g., Decimal128, ObjectId)
2. **Ordering**: BSON documents are ordered; maps/dictionaries might not be
3. **Size limits**: BSON documents have a 16MB limit
4. **Binary subtypes**: UUID, encrypted data, vectors have special encodings

### Essential BSON Types

Your driver must support these core types:

- **Basic types**: int32, int64, double, string, boolean, null
- **Documents**: Embedded documents (nested objects)
- **Arrays**: Ordered lists
- **Binary**: Byte arrays with subtypes (generic, UUID, encrypted, vector)
- **ObjectId**: 12-byte unique identifiers
- **DateTime**: UTC milliseconds since epoch
- **Decimal128**: High-precision decimal numbers

**Normative specifications**:
- [BSON Corpus](bson-corpus/bson-corpus.md) - Test cases for BSON encoding/decoding
- [ObjectId](bson-objectid/objectid.md) - ObjectId generation
- [Decimal128](bson-decimal128/decimal128.md) - Decimal128 handling
- [UUID](bson-binary-uuid/uuid.md) - UUID encoding
- [Binary Vector](bson-binary-vector/bson-binary-vector.md) - Vector encoding

### Extended JSON

For debugging and testing, drivers should support Extended JSON—a human-readable JSON representation of BSON.

**Normative specification**: [Extended JSON](extended-json/extended-json.md)

---

## Chapter 4: Connection Management

### The Connection Lifecycle

Before your driver can send commands, it needs a TCP connection to a MongoDB server. Connection management is critical for performance and reliability.

### Basic Connection Flow

1. **DNS resolution**: Resolve hostname to IP address
2. **TCP connection**: Establish TCP socket
3. **TLS handshake**: If using TLS (recommended for production)
4. **Authentication**: Authenticate the connection (Chapter 23)
5. **Connection ready**: Can now send commands

### Connection Strings

Users configure drivers with a connection string (URI):

```
mongodb://username:password@host1:27017,host2:27017/database?replicaSet=myRS&tls=true
```

This encodes:
- **Hosts**: Where to connect
- **Credentials**: Authentication info
- **Options**: Configuration (TLS, replica set name, timeouts, etc.)

**Normative specifications**:
- [Connection String](connection-string/connection-string-spec.md) - URI parsing
- [URI Options](uri-options/uri-options.md) - All supported options

### Why Not Just Open Connections on Demand?

Opening connections is expensive (DNS, TCP handshake, TLS, auth). That's why drivers use connection pooling (Chapter 7).

---

# Part II: Server Interaction

## Chapter 5: Server Discovery and Monitoring (SDAM)

### The Challenge: MongoDB Isn't Just One Server

MongoDB deployments come in different topologies:

- **Standalone**: Single server (development/testing)
- **Replica Set**: Multiple servers with automatic failover
- **Sharded Cluster**: Distributed data across shards, accessed via mongos routers
- **Load Balanced**: Servers behind a load balancer

Your driver must:
1. **Discover** what topology it's connected to
2. **Monitor** server health and state changes
3. **Adapt** when servers go down or new ones are added

### How SDAM Works

SDAM is a state machine that maintains a view of the topology:

```
┌─────────────────────────────────────┐
│  Topology Description               │
│  - Type: ReplicaSetWithPrimary      │
│  - Servers:                         │
│    • server1: Primary (RTT: 5ms)    │
│    • server2: Secondary (RTT: 12ms) │
│    • server3: Secondary (RTT: 8ms)  │
└─────────────────────────────────────┘
```

The driver:
1. Sends `hello` commands to each server periodically (every 10 seconds by default)
2. Updates the topology description based on responses
3. Detects failures, elections, and topology changes

### Why This Matters

SDAM is foundational because:
- **Server Selection** (Chapter 6) uses the topology description to choose servers
- **Retryable Operations** (Chapter 11) use it to determine if retry is possible
- **Connection Pooling** (Chapter 7) creates pools per server

**Normative specification**: [Server Discovery and Monitoring](server-discovery-and-monitoring/server-discovery-and-monitoring.md)

### Key Concepts

- **Topology Type**: Unknown, Standalone, ReplicaSetNoPrimary, ReplicaSetWithPrimary, Sharded, LoadBalanced
- **Server Type**: Unknown, Standalone, Mongos, RSPrimary, RSSecondary, RSArbiter, RSGhost
- **Server Description**: State of a single server (type, RTT, tags, etc.)
- **Topology Description**: State of the entire deployment

---

## Chapter 6: Server Selection

### Choosing Where to Send Operations

Now that SDAM maintains a topology description, how does your driver choose which server to use for an operation?

### Read Preference

For read operations, users can specify a **read preference**:

- **primary**: Read from the primary only (default)
- **primaryPreferred**: Read from primary if available, otherwise a secondary
- **secondary**: Read from a secondary only
- **secondaryPreferred**: Read from secondary if available, otherwise primary
- **nearest**: Read from the server with lowest latency

### The Selection Algorithm

Server selection is a filtering process:

1. **Start with all servers** in the topology
2. **Filter by topology type** (e.g., in a replica set, filter to appropriate servers)
3. **Filter by read preference** (e.g., if `secondary`, remove primary)
4. **Filter by tag sets** (optional: user-specified server tags)
5. **Filter by latency** (remove servers outside the latency window)
6. **Choose randomly** from remaining servers (for load distribution)

### Write Operations

Writes always go to specific servers:
- **Replica Set**: Primary only
- **Sharded Cluster**: Mongos router(s)
- **Standalone**: The standalone server

### Why This Matters

Server selection interacts with:
- **Retryable operations**: If selection fails, should we retry? (Chapter 11)
- **Transactions**: All operations in a transaction go to the same server (Chapter 10)
- **CSOT**: Selection must respect timeouts (Chapter 17)

**Normative specification**: [Server Selection](server-selection/server-selection.md)

---

## Chapter 7: Connection Pooling

### Why Pool Connections?

Opening a connection is expensive (100-500ms with TLS and auth). If every operation opened a new connection, performance would be terrible.

**Connection pooling** solves this: maintain a pool of ready-to-use connections per server.

### The Pool Lifecycle

```
┌─────────────────────────────────┐
│  Connection Pool (server1)      │
│  ┌─────┐ ┌─────┐ ┌─────┐       │
│  │Conn1│ │Conn2│ │Conn3│       │  ← Available connections
│  └─────┘ └─────┘ └─────┘       │
│                                 │
│  In use: 2 connections          │
│  Available: 3 connections       │
│  Max pool size: 100             │
└─────────────────────────────────┘
```

### Pool Operations

1. **Check out**: Get a connection from the pool
   - If available connections exist, return one
   - If pool not at max size, create a new connection
   - Otherwise, wait (with timeout)

2. **Check in**: Return a connection to the pool
   - Connection becomes available for reuse

3. **Clear**: Remove all connections (e.g., on network error or topology change)

### Connection Monitoring and Pooling (CMAP)

The CMAP specification defines:
- Pool lifecycle and configuration
- Connection lifecycle (created, ready, closed)
- Events for observability (Chapter 21)
- Behavior during errors and topology changes

**Normative specification**: [Connection Monitoring and Pooling](connection-monitoring-and-pooling/connection-monitoring-and-pooling.md)

### Key Configuration

- **minPoolSize**: Minimum connections to maintain (default: 0)
- **maxPoolSize**: Maximum connections allowed (default: 100)
- **maxIdleTimeMS**: Close idle connections after this time
- **waitQueueTimeoutMS**: How long to wait for a connection

### Interaction with Other Features

- **Sessions**: May pin connections (Chapter 9)
- **Transactions**: Pin to a single connection (Chapter 10)
- **Load Balancers**: Always pin connections (Chapter 25)
- **CSOT**: Checkout timeout counts toward operation timeout (Chapter 17)

---

# Part III: Building Operations

This is where things get interesting. You now understand how to connect to servers, discover topology, select servers, and manage connection pools. Now let's build operations.

## Chapter 8: Understanding Operation Context

### The Problem: Operations Need Context

When you send a command to MongoDB, it's not just the command itself. You need to attach context:

- **Which session?** (for causally consistent reads, transactions)
- **Which transaction?** (if in a transaction)
- **Is this retryable?** (attach transaction number)
- **What's the timeout?** (for CSOT)
- **What API version?** (for Stable API)

This context is spread across multiple specifications (Sessions, Transactions, Retryable Operations, CSOT, Stable API), which is why they're so interconnected.

### The Mental Model

Think of operation context as layers you add to a command:

```
Base command: {find: "users", filter: {age: {$gt: 18}}}

+ Session layer:     lsid: {...}
+ Transaction layer: txnNumber: 1, autocommit: false
+ Timeout layer:     maxTimeMS: 5000
+ API layer:         apiVersion: "1"

Final command: {
  find: "users",
  filter: {age: {$gt: 18}},
  lsid: {...},
  txnNumber: 1,
  autocommit: false,
  maxTimeMS: 5000,
  apiVersion: "1"
}
```

The next few chapters explain each layer.

---

## Chapter 9: Driver Sessions

### What is a Session?

A **driver session** (or **client session**) is a logical session that groups related operations. It's the foundation for:

- **Causal consistency**: Ensuring you read your own writes
- **Transactions**: Multi-statement ACID operations
- **Retryable writes**: Exactly-once semantics

### Server Sessions vs. Driver Sessions

- **Driver session**: An object in your driver (e.g., `ClientSession` class)
- **Server session**: A resource on the server identified by an `lsid` (logical session ID)

When you create a driver session, the driver allocates a server session (an `lsid`) from a pool.

### Session Lifecycle

```python
# User creates a session
session = client.start_session()

# Driver allocates an lsid
# lsid = {id: <UUID>}

# User performs operations with the session
collection.find_one({...}, session=session)
# Driver attaches: lsid: {id: <UUID>}

# User ends the session
session.end_session()
# Driver returns lsid to pool for reuse
```

### Implicit vs. Explicit Sessions

- **Explicit session**: User creates and passes to operations
- **Implicit session**: Driver creates automatically for operations without a session

**Key insight**: Even if the user doesn't create a session, the driver creates an implicit one and attaches an `lsid` to commands. This enables server-side features like retryable writes.

### Causal Consistency

Sessions track **cluster time** and **operation time** to ensure causal consistency:

```
Operation 1: insert({x: 1})
  → Server returns: operationTime: T1, $clusterTime: {clusterTime: T1, ...}
  → Session records: operationTime = T1

Operation 2: find({x: 1})
  → Driver attaches: lsid: {...}, $clusterTime: {clusterTime: T1, ...}
  → Server ensures read sees writes up to T1
```

This guarantees you read your own writes, even if reading from a secondary.

### Session Pooling

Creating server sessions is cheap, but drivers still pool them for efficiency. When a driver session ends, the `lsid` goes back to a pool for reuse.

**Normative specification**: [Driver Sessions](sessions/driver-sessions.md)

---

## Chapter 10: Transactions

### Multi-Statement ACID Operations

Transactions allow you to execute multiple operations atomically. Either all operations succeed, or none do.

### The Transaction API

```python
session = client.start_session()

# Start a transaction
session.start_transaction(
    read_concern=ReadConcern("snapshot"),
    write_concern=WriteConcern(w="majority")
)

try:
    # All operations use the session
    accounts.update_one({_id: 1}, {$inc: {balance: -100}}, session=session)
    accounts.update_one({_id: 2}, {$inc: {balance: +100}}, session=session)

    # Commit the transaction
    session.commit_transaction()
except Exception:
    # Abort on error
    session.abort_transaction()
finally:
    session.end_session()
```

### How Transactions Work

When you start a transaction, the driver:

1. **Sets transaction state** on the session (starting → in_progress)
2. **Attaches transaction fields** to commands:
   - `lsid`: The session ID
   - `txnNumber`: A monotonically increasing transaction number
   - `autocommit: false`: Indicates this is part of a transaction
   - `startTransaction: true`: On the first operation only

3. **Pins to a server**: All operations go to the same server (mongos or primary)
4. **Pins to a connection**: All operations use the same connection

### Transaction State Machine

```
          start_transaction()
    ┌──────────────────────────┐
    │                          ▼
STARTING ──first op──▶ IN_PROGRESS ──commit──▶ COMMITTED
                           │
                           └──abort──▶ ABORTED
```

### Transaction Numbers (txnNumber)

Each retryable write or transaction gets a unique `txnNumber` on the session. This number:
- Increments monotonically
- Allows the server to detect duplicate operations
- Enables exactly-once semantics

**Key insight**: Transaction numbers are shared between transactions and retryable writes. Both use the same mechanism for idempotency.

### Retrying Transactions

Transactions can fail with transient errors (network issues, elections). The driver labels these with `TransientTransactionError`, and applications can retry the entire transaction.

Some operations also get `UnknownTransactionCommitResult` if the commit outcome is uncertain.

### Interaction with Other Features

- **Sessions**: Transactions require an explicit session
- **Retryable Writes**: Transaction operations are not individually retryable (the whole transaction is)
- **Read/Write Concern**: Transactions have their own read/write concerns
- **Server Selection**: Transactions pin to a server and connection

**Normative specification**: [Transactions](transactions/transactions.md)

---

## Chapter 11: Retryable Operations

### Handling Transient Failures

Networks are unreliable. Servers can fail. Elections happen. Your driver should handle these gracefully by retrying operations automatically.

### Retryable Writes

Certain write operations can be retried safely:
- `insertOne`, `updateOne`, `deleteOne`, `replaceOne`
- `insertMany` (if ordered: false)
- `findAndModify` operations
- `bulkWrite` (with restrictions)

When enabled (`retryWrites=true` in URI), the driver:

1. **Attaches transaction context**: `lsid` + `txnNumber`
2. **Sends the operation**
3. **If it fails with a retryable error**: Retry once on a different server
4. **Server deduplicates**: Using `lsid` + `txnNumber`, server knows if it already executed this operation

### Retryable Reads

Read operations can also be retried:
- `find`, `aggregate`, `distinct`, `count`
- `listCollections`, `listDatabases`, `listIndexes`
- Change stream operations

When enabled (`retryReads=true` in URI), the driver retries once on retryable errors.

### What Makes an Error Retryable?

**Retryable errors** include:
- Network errors (connection closed, timeout)
- Server errors with specific codes (e.g., NotWritablePrimary, InterruptedDueToReplStateChange)
- Errors with the `RetryableWriteError` label

**Non-retryable errors**:
- Application errors (duplicate key, validation failure)
- Errors in transactions (transaction handles its own retry logic)

### The Retry Process

```
1. Select server A
2. Check out connection
3. Send operation
4. Network error!
5. Mark server A as Unknown (SDAM)
6. Select server B (different server)
7. Check out connection
8. Send operation (with same lsid + txnNumber)
9. Success!
```

### Why lsid + txnNumber?

Without transaction numbers, retrying a write could cause duplicates:
```
Client sends: insert({_id: 1, x: 1})
Server executes it
Network fails before response reaches client
Client retries: insert({_id: 1, x: 1})
Server sees duplicate _id → Error!
```

With transaction numbers:
```
Client sends: insert({_id: 1, x: 1}) + lsid + txnNumber: 1
Server executes it, records (lsid, txnNumber: 1)
Network fails
Client retries: insert({_id: 1, x: 1}) + lsid + txnNumber: 1
Server sees (lsid, txnNumber: 1) already executed → Returns original result!
```

### Retry Limitations

- **Retry once**: Only one retry attempt (not infinite retries)
- **Different server**: Must retry on a different server (when possible)
- **Topology restrictions**: Some topologies don't support retries (e.g., standalone)
- **Timeout**: Retry must complete within the operation timeout (CSOT)

**Normative specifications**:
- [Retryable Writes](retryable-writes/retryable-writes.md)
- [Retryable Reads](retryable-reads/retryable-reads.md)

---

## Chapter 12: Command Construction

### Putting It All Together

Now you understand sessions, transactions, and retryable operations. How do you actually build a command?

### The Command Construction Checklist

When constructing a command, the driver must:

1. **Start with the base command**
   ```javascript
   {find: "users", filter: {age: {$gt: 18}}}
   ```

2. **Add database name**
   ```javascript
   {find: "users", filter: {age: {$gt: 18}}, $db: "mydb"}
   ```

3. **Add session ID** (if session exists)
   ```javascript
   lsid: {id: UUID("...")}
   ```

4. **Add cluster time** (if session has cluster time)
   ```javascript
   $clusterTime: {clusterTime: Timestamp(1234, 5), signature: {...}}
   ```

5. **Add transaction fields** (if in transaction)
   ```javascript
   txnNumber: NumberLong(1),
   autocommit: false,
   startTransaction: true  // only on first operation
   ```

6. **Add transaction number** (if retryable write, not in transaction)
   ```javascript
   txnNumber: NumberLong(2)
   ```

7. **Add read concern** (if applicable)
   ```javascript
   readConcern: {level: "majority"}
   ```

8. **Add write concern** (if applicable)
   ```javascript
   writeConcern: {w: "majority", j: true}
   ```

9. **Add read preference** (if reading from secondary)
   ```javascript
   $readPreference: {mode: "secondary"}
   ```

10. **Add timeout** (if CSOT enabled)
    ```javascript
    maxTimeMS: 5000
    ```

11. **Add API version** (if Stable API configured)
    ```javascript
    apiVersion: "1",
    apiStrict: true
    ```

### The Order Matters

Some fields depend on others:
- Can't add `txnNumber` without `lsid`
- Can't add `autocommit` without being in a transaction
- `startTransaction` only on first operation in transaction

### Example: Complete Command

```javascript
{
  // Base command
  find: "users",
  filter: {age: {$gt: 18}},

  // Database
  $db: "mydb",

  // Session
  lsid: {id: UUID("12345678-1234-1234-1234-123456789abc")},

  // Cluster time (for causal consistency)
  $clusterTime: {
    clusterTime: Timestamp(1234, 5),
    signature: {hash: BinData(...), keyId: 123}
  },

  // Transaction
  txnNumber: NumberLong(1),
  autocommit: false,
  startTransaction: true,

  // Read concern
  readConcern: {level: "snapshot"},

  // Timeout
  maxTimeMS: 5000,

  // API version
  apiVersion: "1"
}
```

**Normative specification**: [Run Command](run-command/run-command.md)

### Why This Is Complex

This is why Sessions, Transactions, and Retryable Operations are so interconnected. They all contribute to command construction, and the rules for what to include depend on the combination of features in use.

---

# Part IV: Core Operations

## Chapter 13: CRUD Operations

Now that you can construct commands with proper context, let's implement the operations users actually call.

### The CRUD API

CRUD stands for Create, Read, Update, Delete. The driver provides a consistent API:

**Create (Insert)**:
```python
collection.insert_one({x: 1})
collection.insert_many([{x: 1}, {x: 2}])
```

**Read (Find)**:
```python
collection.find({x: 1})
collection.find_one({x: 1})
collection.count_documents({x: 1})
```

**Update**:
```python
collection.update_one({x: 1}, {$set: {y: 2}})
collection.update_many({x: 1}, {$set: {y: 2}})
collection.replace_one({x: 1}, {x: 1, y: 2})
```

**Delete**:
```python
collection.delete_one({x: 1})
collection.delete_many({x: 1})
```

### How CRUD Operations Map to Commands

Each CRUD operation maps to a MongoDB command:

- `insert_one` → `insert` command
- `find` → `find` command (+ `getMore` for cursor)
- `update_one` → `update` command
- `delete_one` → `delete` command
- `aggregate` → `aggregate` command

### Cursors

Operations that return multiple documents use **cursors**:

```python
cursor = collection.find({x: 1})
for doc in cursor:
    print(doc)
```

Behind the scenes:
1. Driver sends `find` command
2. Server returns first batch + cursor ID
3. Driver yields documents from batch
4. When batch exhausted, driver sends `getMore` command
5. Repeat until cursor exhausted

### Bulk Write Operations

For efficiency, drivers support bulk writes:

```python
collection.bulk_write([
    InsertOne({x: 1}),
    UpdateOne({x: 1}, {$set: {y: 2}}),
    DeleteOne({x: 2})
])
```

The driver batches these into one or more commands to minimize round trips.

### CRUD and Operation Context

CRUD operations inherit all the operation context:
- Sessions (explicit or implicit)
- Transactions (if in a transaction)
- Retryable operations (if enabled)
- Timeouts (if CSOT enabled)
- Read/write concerns

**Normative specification**: [CRUD](crud/crud.md)

---

## Chapter 14: Read and Write Concerns

### Controlling Consistency and Durability

Read and write concerns let users control the tradeoff between consistency/durability and performance.

### Read Concern

**Read concern** controls what data a read operation sees:

- **local** (default): Read from the primary's or secondary's local data (fastest, but might read data that gets rolled back)
- **majority**: Read data acknowledged by a majority of replica set members (won't be rolled back)
- **linearizable**: Read data that reflects all successful majority-acknowledged writes (strongest consistency, primary only)
- **snapshot**: Read from a consistent snapshot (for transactions)
- **available**: Read from any available data (for sharded clusters)

Example:
```python
collection.find({x: 1}, read_concern=ReadConcern("majority"))
```

### Write Concern

**Write concern** controls acknowledgment of writes:

- **w**: Number of servers that must acknowledge
  - `w: 1` - Primary only (default, fastest)
  - `w: "majority"` - Majority of replica set members (durable)
  - `w: 3` - Three specific servers
- **j**: Whether to wait for journal sync (durability)
- **wtimeout**: How long to wait for acknowledgment

Example:
```python
collection.insert_one({x: 1}, write_concern=WriteConcern(w="majority", j=True))
```

### Inheritance Chain

Read and write concerns inherit from client to database to collection:

```python
client = MongoClient(readConcernLevel="majority")
db = client.mydb  # Inherits majority read concern
collection = db.mycollection  # Inherits majority read concern

# Can override at operation level
collection.find({x: 1}, read_concern=ReadConcern("local"))
```

### Interaction with Transactions

Transactions have their own read and write concerns specified at transaction start:

```python
session.start_transaction(
    read_concern=ReadConcern("snapshot"),
    write_concern=WriteConcern(w="majority")
)
```

**Normative specification**: [Read and Write Concern](read-write-concern/read-write-concern.md)

---

## Chapter 15: Collation

### Internationalization for String Comparison

Different languages have different sorting and comparison rules. **Collation** lets you specify these rules.

Example:
```python
# Case-insensitive search
collection.find(
    {name: "john"},
    collation=Collation(locale="en", strength=2)
)
# Matches "John", "JOHN", "john"
```

Collation affects:
- Sorting (`sort`)
- Comparison operators (`$eq`, `$gt`, etc.)
- Text search
- Aggregation

**Normative specification**: [Collation](collation/collation.md)

---

# Part V: Advanced Features

## Chapter 16: Change Streams

### Watching for Changes

Change streams let applications watch for changes to collections, databases, or entire deployments in real-time.

```python
# Watch for changes
with collection.watch() as stream:
    for change in stream:
        print(change)
        # {operationType: "insert", fullDocument: {x: 1}, ...}
```

### How Change Streams Work

Behind the scenes:
1. Driver sends an `aggregate` command with `$changeStream` stage
2. Server returns a cursor that stays open
3. Driver sends `getMore` commands to fetch new changes
4. Server pushes changes as they occur

### Resume Tokens

Change streams are resumable. Each change includes a **resume token**:

```python
resume_token = None
with collection.watch() as stream:
    for change in stream:
        resume_token = change["_id"]
        process(change)

# Later, resume from where you left off
with collection.watch(resume_after=resume_token) as stream:
    for change in stream:
        process(change)
```

### Change Stream and Retryable Reads

Change streams automatically retry on retryable errors, maintaining the resume token to avoid missing changes.

**Normative specification**: [Change Streams](change-streams/change-streams.md)

---

## Chapter 17: Client-Side Operations Timeout (CSOT)

### Unified Timeout Handling

Historically, MongoDB had many timeout options: `socketTimeoutMS`, `serverSelectionTimeoutMS`, `maxTimeMS`, etc. CSOT unifies these with a single `timeoutMS`.

```python
client = MongoClient("mongodb://localhost", timeoutMS=5000)

# All operations have a 5-second timeout
collection.find_one({x: 1})  # Must complete in 5 seconds
```

### How CSOT Works

The driver tracks time across the entire operation:

```
Total timeout: 5000ms

Server selection: 100ms (4900ms remaining)
Connection checkout: 50ms (4850ms remaining)
Network round trip: 200ms (4650ms remaining)
Cursor iteration (getMore): 300ms (4350ms remaining)
...
```

If time runs out at any point, the operation fails with a timeout error.

### CSOT and Retries

Retries must complete within the original timeout:

```
Total timeout: 5000ms

Attempt 1:
  Server selection: 100ms
  Send operation: 200ms
  Network error! (4700ms remaining)

Attempt 2:
  Server selection: 100ms (4600ms remaining)
  Send operation: 200ms (4400ms remaining)
  Success!
```

### Interaction with Other Features

- **Transactions**: `timeoutMS` applies to the entire transaction
- **Change Streams**: `timeoutMS` applies to each `getMore`, not the entire stream
- **Connection Pooling**: Connection checkout counts toward timeout

**Normative specification**: [Client-Side Operations Timeout](client-side-operations-timeout/client-side-operations-timeout.md)

---

## Chapter 18: GridFS

### Storing Large Files

MongoDB documents have a 16MB size limit. For larger files, use **GridFS**, which splits files into chunks.

```python
fs = GridFSBucket(db)

# Upload a file
with open("large_file.pdf", "rb") as f:
    file_id = fs.upload_from_stream("large_file.pdf", f)

# Download a file
with open("downloaded.pdf", "wb") as f:
    fs.download_to_stream(file_id, f)
```

### How GridFS Works

GridFS uses two collections:
- **fs.files**: Metadata (filename, length, upload date, etc.)
- **fs.chunks**: File chunks (255KB each by default)

```
fs.files:
{_id: ObjectId(...), filename: "large_file.pdf", length: 5000000, chunkSize: 261120}

fs.chunks:
{files_id: ObjectId(...), n: 0, data: BinData(...)}  // First chunk
{files_id: ObjectId(...), n: 1, data: BinData(...)}  // Second chunk
...
```

**Normative specification**: [GridFS](gridfs/gridfs-spec.md)

---

## Chapter 19: Client-Side Encryption

### Encrypting Sensitive Data

Client-side field level encryption (CSFLE) lets you encrypt specific fields before sending them to MongoDB.

```python
client = MongoClient(
    auto_encryption_opts=AutoEncryptionOpts(
        key_vault_namespace="encryption.__keyVault",
        kms_providers={"local": {"key": local_master_key}}
    )
)

# Automatically encrypts ssn field
collection.insert_one({
    name: "Alice",
    ssn: "123-45-6789"  # Encrypted before sending to server
})
```

The server stores encrypted data but can't decrypt it. Only clients with the encryption keys can read the plaintext.

**Normative specification**: [Client-Side Encryption](client-side-encryption/client-side-encryption.md)

---

# Part VI: Observability and Testing

## Chapter 20: Command Monitoring

### Observing Driver Behavior

Command monitoring lets applications observe all commands sent to MongoDB:

```python
class CommandLogger:
    def started(self, event):
        print(f"Command {event.command_name} started")

    def succeeded(self, event):
        print(f"Command {event.command_name} succeeded in {event.duration_micros}μs")

    def failed(self, event):
        print(f"Command {event.command_name} failed: {event.failure}")

client = MongoClient(event_listeners=[CommandLogger()])
```

### Events

- **CommandStartedEvent**: Before sending a command
  - `command_name`, `database_name`, `command` (the full command document)
- **CommandSucceededEvent**: After successful response
  - `duration_micros`, `reply`
- **CommandFailedEvent**: After failure
  - `duration_micros`, `failure`

### Use Cases

- **Logging**: Log all database operations
- **Profiling**: Measure operation performance
- **Debugging**: Inspect exact commands sent
- **Monitoring**: Track slow queries

**Normative specification**: [Command Logging and Monitoring](command-logging-and-monitoring/command-logging-and-monitoring.md)

---

## Chapter 21: Connection Monitoring

### CMAP Events

Connection Monitoring and Pooling (CMAP) events let you observe connection pool behavior:

- **PoolCreatedEvent**: Pool created for a server
- **ConnectionCreatedEvent**: New connection created
- **ConnectionReadyEvent**: Connection ready for use
- **ConnectionCheckedOutEvent**: Connection checked out
- **ConnectionCheckedInEvent**: Connection checked in
- **ConnectionClosedEvent**: Connection closed
- **PoolClearedEvent**: Pool cleared (e.g., on network error)

### Use Cases

- **Monitoring**: Track connection pool health
- **Debugging**: Understand connection lifecycle issues
- **Capacity planning**: See if you're hitting pool limits

**Normative specification**: [Connection Monitoring and Pooling](connection-monitoring-and-pooling/connection-monitoring-and-pooling.md)

---

## Chapter 22: Testing Your Driver

### Unified Test Format

MongoDB provides a comprehensive test suite in a unified format that works across all drivers.

The tests are JSON/YAML files that describe:
- Initial setup (create collections, insert data)
- Operations to perform
- Expected results
- Expected events (command monitoring, CMAP)

Example test:
```yaml
description: "insertOne"
operations:
  - name: insertOne
    object: collection
    arguments:
      document: {_id: 1, x: 1}
    expectResult:
      insertedId: 1
expectEvents:
  - client: client
    events:
      - commandStartedEvent:
          command:
            insert: "collection"
            documents: [{_id: 1, x: 1}]
```

Your driver runs these tests to ensure compliance with specifications.

**Normative specification**: [Unified Test Format](unified-test-format/unified-test-format.md)

### Other Test Formats

- **BSON Corpus**: Test BSON encoding/decoding
- **Connection String Tests**: Test URI parsing
- **Server Discovery and Monitoring Tests**: Test SDAM behavior
- **Retryable Reads/Writes Tests**: Test retry logic

---

# Part VII: Additional Topics

## Chapter 23: Authentication

### Securing Connections

MongoDB supports multiple authentication mechanisms:

- **SCRAM-SHA-256** / **SCRAM-SHA-1**: Username/password (default)
- **MONGODB-X509**: X.509 certificates
- **MONGODB-AWS**: AWS IAM credentials
- **GSSAPI** (Kerberos): Enterprise authentication
- **PLAIN**: LDAP (enterprise)
- **MONGODB-OIDC**: OpenID Connect

Example:
```
mongodb://username:password@localhost/?authMechanism=SCRAM-SHA-256
```

The driver performs authentication during connection establishment (Chapter 4).

**Normative specification**: [Authentication](auth/auth.md)

---

## Chapter 24: Stable API

### API Version Declaration

The Stable API (formerly Versioned API) lets you declare which API version your application uses:

```python
client = MongoClient(
    server_api=ServerApi(version="1", strict=True, deprecation_errors=True)
)
```

This ensures:
- **Compatibility**: Your app continues working across MongoDB versions
- **Strict mode**: Server rejects commands not in the declared API version
- **Deprecation warnings**: Server warns about deprecated features

The driver attaches API version to all commands:
```javascript
{
  find: "collection",
  apiVersion: "1",
  apiStrict: true,
  apiDeprecationErrors: true
}
```

**Normative specification**: [Versioned API](versioned-api/versioned-api.md)

---

## Chapter 25: Load Balancers

### Connecting Through Load Balancers

MongoDB supports deployment behind load balancers. This requires special handling:

```
mongodb://loadbalancer.example.com/?loadBalanced=true
```

Key differences:
- **Single server**: Driver treats it as a single server (no SDAM monitoring)
- **Connection pinning**: Connections are pinned for sessions and transactions
- **No retries**: Some retry scenarios are disabled

**Normative specification**: [Load Balancer Support](load-balancers/load-balancers.md)

---

## Chapter 26: SOCKS5 Proxy Support

### Connecting Through Proxies

Drivers can connect through SOCKS5 proxies:

```
mongodb://localhost/?proxyHost=proxy.example.com&proxyPort=1080
```

The driver establishes the TCP connection through the proxy.

**Normative specification**: [SOCKS5 Support](socks5-support/socks5-support.md)

---

# Conclusion

## You Now Understand Driver Architecture

You've learned how MongoDB drivers work from the ground up:

1. **Wire protocol and BSON**: How drivers communicate with servers
2. **Connection management**: Pooling and lifecycle
3. **Server discovery**: SDAM and topology awareness
4. **Server selection**: Routing operations
5. **Operation context**: Sessions, transactions, retryable operations
6. **Command construction**: Putting it all together
7. **CRUD operations**: The user-facing API
8. **Advanced features**: Change streams, encryption, GridFS
9. **Observability**: Monitoring and events
10. **Testing**: Ensuring compliance

## The Interconnections Make Sense Now

You can see why specifications are so interconnected:

- **Sessions** provide `lsid` for transactions and retryable operations
- **Transactions** use sessions and affect command construction
- **Retryable operations** use sessions and interact with SDAM
- **CSOT** affects all operations, retries, and connection checkout
- **Command construction** must know about all of the above

## Next Steps

To implement a driver:

1. **Start with foundations**: BSON, wire protocol, connections
2. **Add SDAM**: Server discovery and monitoring
3. **Add server selection and pooling**: Infrastructure
4. **Add sessions**: Foundation for advanced features
5. **Add CRUD**: User-facing operations
6. **Add transactions and retryable operations**: Reliability
7. **Add advanced features**: Change streams, encryption, etc.
8. **Add observability**: Monitoring and events
9. **Test thoroughly**: Use the unified test format

## For Normative Requirements

Remember: **This guide is non-normative.** For precise requirements, always consult the individual specifications:

- [Driver Sessions](sessions/driver-sessions.md)
- [Transactions](transactions/transactions.md)
- [Retryable Writes](retryable-writes/retryable-writes.md)
- [Retryable Reads](retryable-reads/retryable-reads.md)
- [CRUD](crud/crud.md)
- [Server Discovery and Monitoring](server-discovery-and-monitoring/server-discovery-and-monitoring.md)
- [Server Selection](server-selection/server-selection.md)
- [Connection Monitoring and Pooling](connection-monitoring-and-pooling/connection-monitoring-and-pooling.md)
- And all the others linked throughout this guide

Good luck building your MongoDB driver!


