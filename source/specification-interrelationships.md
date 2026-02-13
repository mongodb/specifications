# MongoDB Driver Specification Interrelationships

**Status**: Informational  
**Version**: 1.0  
**Last Updated**: 2026-02-13

---

## Purpose

This document analyzes the dependencies and coupling between MongoDB driver specifications. It helps specification authors understand how changes in one specification may cascade to others, and provides guidance for managing cross-specification complexity.

---

## Table of Contents

- [Overview](#overview)
- [Specification Tiers](#specification-tiers)
- [Common Dependency Patterns](#common-dependency-patterns)
- [Specific Examples of Cross-Specification Changes](#specific-examples-of-cross-specification-changes)
- [Why This Creates Inefficiency](#why-this-creates-inefficiency)
- [Recommendations](#recommendations)

---

## Overview

MongoDB driver specifications are highly interconnected. A change to one specification often requires coordinated changes across multiple other specifications. This document maps these relationships to help specification authors:

1. **Understand impact**: Know which specs are affected by a change
2. **Plan changes**: Anticipate the scope of cross-specification work
3. **Review efficiently**: Know which specs to review together
4. **Reduce coupling**: Identify opportunities to simplify dependencies

### The Challenge

Complex features often require:
- Modifications to 5-10 different specifications
- Cross-references that create circular dependencies
- Duplicate information described from different perspectives
- Coordination across multiple teams and reviewers

---

## Specification Tiers

Specifications can be organized into tiers based on how many other specifications depend on them.

### Tier 1: Foundation Specifications (Most Referenced)

These are the core specs that almost everything else depends on. Changes here have the widest impact.

#### 1. Driver Sessions (`sessions/driver-sessions.md`)

**Referenced by**:
- Transactions
- Retryable Writes
- Retryable Reads
- Causal Consistency
- Run Command
- Change Streams
- CRUD Operations
- Client-Side Operations Timeout

**Why central**: Provides `lsid` (logical session ID) required for transactions, retryable operations, and causal consistency. Also manages cluster time for causal consistency.

**Impact of changes**: Any change to session lifecycle, session pooling, or `lsid` attachment affects ~8+ other specifications.

**Key concepts**:
- Logical session ID (`lsid`)
- Server session pooling
- Cluster time tracking
- Operation time tracking
- Implicit vs. explicit sessions

---

#### 2. Server Discovery and Monitoring - SDAM (`server-discovery-and-monitoring/server-discovery-and-monitoring.md`)

**Referenced by**:
- Retryable Reads
- Retryable Writes
- Server Selection
- Connection Monitoring and Pooling
- Transactions
- Load Balancers
- Initial DNS Seedlist Discovery

**Why central**: Defines topology types, server states, and monitoring that determines operation routing and retry eligibility.

**Impact of changes**: Changes to topology detection, server state transitions, or monitoring behavior cascade to retry logic, server selection, and connection management.

**Key concepts**:
- Topology types (Standalone, ReplicaSet, Sharded, LoadBalanced)
- Server types (Primary, Secondary, Mongos, etc.)
- Server monitoring (`hello` command)
- Topology state machine
- RTT (round-trip time) tracking

---

#### 3. Read and Write Concern (`read-write-concern/read-write-concern.md`)

**Referenced by**:
- CRUD
- Transactions
- Run Command
- Retryable Reads
- Retryable Writes
- Server Selection
- Client-Side Operations Timeout

**Why central**: Defines consistency and durability guarantees that are inherited across Client → Database → Collection → Operation hierarchy.

**Impact of changes**: Changes affect how operations are constructed, validated, and how defaults are inherited.

**Key concepts**:
- Read concern levels (local, majority, linearizable, snapshot, available)
- Write concern (w, j, wtimeout)
- Inheritance chain
- Validation rules

---

#### 4. Server Selection (`server-selection/server-selection.md`)

**Referenced by**:
- CRUD
- Transactions
- Retryable Reads
- Retryable Writes
- Change Streams
- Load Balancers
- Client-Side Operations Timeout

**Why central**: Determines which server receives each operation based on read preference, topology state, and server health.

**Impact of changes**: Changes affect operation routing across all operation types.

**Key concepts**:
- Read preference modes
- Tag sets
- Max staleness
- Latency window
- Selection algorithm

---

### Tier 2: Cross-Cutting Concerns (High Coupling)

These specs interact with many others but aren't quite as foundational as Tier 1.

#### 5. Retryable Writes (`retryable-writes/retryable-writes.md`)

**Depends on**:
- Driver Sessions (lsid + txnNumber)
- SDAM (topology checks, retryable server determination)
- Command Monitoring (events)
- CRUD (supported operations)
- Server Selection (selecting different server for retry)

**Referenced by**:
- Transactions (shares txnNumber mechanism)
- Run Command (command construction)
- Unified Test Format (test coverage)
- Client-Side Operations Timeout (timeout across retries)

**Coupling points**:
- Must coordinate with transactions (can't retry operations in a transaction)
- Shares session's txnNumber with transactions
- Depends on SDAM for determining retry eligibility
- Must respect CSOT timeouts across retry attempts

**Key concepts**:
- `retryWrites` URI option
- Transaction numbers (`txnNumber`)
- `RetryableWriteError` label
- Supported operations list
- Retry once on different server

---

#### 6. Retryable Reads (`retryable-reads/retryable-reads.md`)

**Depends on**:
- Driver Sessions (lsid)
- SDAM (topology checks, retryable server determination)
- CRUD (find, aggregate, etc.)
- Change Streams (change stream operations)
- Client-Side Operations Timeout (timeout across retries)
- Server Selection (selecting different server for retry)

**Referenced by**:
- Run Command (command construction)
- Unified Test Format (test coverage)

**Coupling points**:
- Similar structure to Retryable Writes but for read operations
- Must coordinate with Change Streams (resumable change streams)
- Depends on SDAM for determining retry eligibility
- Must respect CSOT timeouts

**Key concepts**:
- `retryReads` URI option
- Supported read operations
- Retryable error determination
- Retry once on retryable errors

---

#### 7. Transactions (`transactions/transactions.md`)

**Depends on**:
- Driver Sessions (required - transactions must have explicit session)
- Read and Write Concern (transaction-level concerns)
- SDAM (topology requirements, server pinning)
- Retryable Writes (shares txnNumber mechanism)
- Server Selection (pinning to server)
- Run Command (command construction with transaction fields)
- Connection Monitoring and Pooling (connection pinning)

**Referenced by**:
- CRUD (operations in transactions)
- Unified Test Format (transaction testing)
- Versioned API (API version in transactions)
- Client-Side Operations Timeout (transaction timeout)

**Coupling points**:
- Extremely high coupling - touches sessions, concerns, retry logic, command construction, SDAM
- Shares `txnNumber` mechanism with retryable writes
- Requires server and connection pinning
- Has its own state machine that interacts with session state

**Key concepts**:
- Transaction API (startTransaction, commitTransaction, abortTransaction)
- Transaction state machine
- Transaction fields (txnNumber, autocommit, startTransaction)
- Error labels (TransientTransactionError, UnknownTransactionCommitResult)
- Server and connection pinning

---

#### 8. Run Command (`run-command/run-command.md`)

**Depends on**:
- Driver Sessions (lsid attachment)
- Transactions (transaction field attachment)
- Read and Write Concern (concern attachment)
- Retryable Reads/Writes (txnNumber attachment)
- Versioned API (API version attachment)
- Client-Side Operations Timeout (timeout attachment)
- Server Selection ($readPreference attachment)

**Referenced by**:
- Most operation specifications (CRUD, Change Streams, etc.)

**Coupling points**:
- Central point where all operation context comes together
- Must know how to attach fields from 7+ different specifications
- Rules for field attachment depend on combinations of features

**Key concepts**:
- `runCommand` and `runCursorCommand` APIs
- Global command arguments ($db, lsid, $clusterTime, $readPreference)
- Transaction field attachment rules
- Command construction order

---

#### 9. Client-Side Operations Timeout - CSOT (`client-side-operations-timeout/client-side-operations-timeout.md`)

**Depends on**:
- Driver Sessions (session checkout timeout)
- Transactions (transaction timeout vs operation timeout)
- Retryable Reads/Writes (timeout across retry attempts)
- Connection Monitoring and Pooling (connection checkout timeout)
- SDAM (server selection timeout)
- Server Selection (selection timeout)

**Referenced by**:
- CRUD (operation-level timeout)
- Run Command (maxTimeMS attachment)
- Change Streams (timeout for getMore)
- GridFS (timeout for multi-operation workflows)

**Coupling points**:
- Affects timeout calculation across all operations
- Must track time across server selection, connection checkout, network round trips, and retries
- Different timeout semantics for different operation types

**Key concepts**:
- `timeoutMS` URI option and MongoClient option
- Timeout inheritance
- Remaining timeout calculation
- Timeout behavior for cursors and change streams

---

### Tier 3: Feature Specifications (Moderate Coupling)

These specs implement features using the foundation and cross-cutting specs.

#### 10. CRUD (`crud/crud.md`)

**Depends on**:
- Read and Write Concern (operation-level concerns)
- Driver Sessions (explicit and implicit sessions)
- Retryable Reads/Writes (retry behavior)
- Server Selection (read preference)
- Client-Side Operations Timeout (operation timeout)
- Collation (string comparison)

**Referenced by**:
- Unified Test Format (CRUD testing)
- Transactions (CRUD operations in transactions)
- Change Streams (aggregate operation)

**Coupling points**:
- Implements the dependency chain but doesn't define core behavior
- Must handle all combinations of sessions, transactions, retries, concerns, timeouts

**Key concepts**:
- CRUD API (insertOne, find, updateOne, etc.)
- Bulk write operations
- Cursor iteration
- Operation options

---

#### 11. Change Streams (`change-streams/change-streams.md`)

**Depends on**:
- Driver Sessions (session for change stream)
- CRUD (aggregate command)
- Retryable Reads (resuming on errors)
- Server Selection (read preference)
- Client-Side Operations Timeout (timeout for getMore)

**Referenced by**:
- Unified Test Format (change stream testing)

**Coupling points**:
- Uses aggregate with $changeStream stage
- Automatic resumption on retryable errors
- Resume token management

**Key concepts**:
- Watch API
- Resume tokens
- Change stream events
- Resumption logic

---

#### 12. Connection Monitoring and Pooling - CMAP (`connection-monitoring-and-pooling/connection-monitoring-and-pooling.md`)

**Depends on**:
- SDAM (pool per server, clearing on topology changes)
- Client-Side Operations Timeout (connection checkout timeout)
- Load Balancers (connection pinning)

**Referenced by**:
- Retryable Reads/Writes (connection errors trigger retries)
- Driver Sessions (connection pinning for transactions)
- Transactions (connection pinning)

**Coupling points**:
- Pool lifecycle tied to SDAM topology changes
- Connection checkout timeout interacts with CSOT
- Connection pinning for load balancers and transactions

**Key concepts**:
- Connection pool per server
- Connection lifecycle (created, ready, closed)
- Pool configuration (minPoolSize, maxPoolSize)
- CMAP events

---

## Common Dependency Patterns

These patterns show how changes cascade across multiple specifications.

### Pattern 1: Command Construction Chain

```
Run Command → Sessions → Transactions → Retryable Writes → CSOT → Versioned API
```

**When this matters**: Adding a new global command argument

**Affected specs**:
1. **Run Command**: How to attach the new argument
2. **Driver Sessions**: If the argument is session-related
3. **Transactions**: If the argument affects transaction commands
4. **Retryable Operations**: If the argument affects retry behavior
5. **CSOT**: If the argument affects timeout calculation
6. **Versioned API**: If the argument is part of the stable API

**Example**: When `timeoutMS` was added (CSOT), it required changes to all of these specs.

---

### Pattern 2: Error Handling Chain

```
SDAM (server errors) → Retryable Reads/Writes → Transactions → CRUD → Command Monitoring
```

**When this matters**: Adding a new retryable error code or error label

**Affected specs**:
1. **SDAM**: Error classification and server state transitions
2. **Retryable Reads/Writes**: Retry logic for the new error
3. **Transactions**: Transaction error labels (TransientTransactionError)
4. **CRUD**: How operations handle the error
5. **Command Monitoring**: Error event details

**Example**: When a new error code is made retryable, all these specs need updates.

---

### Pattern 3: Session Lifecycle Chain

```
Sessions → Transactions → Retryable Writes → Causal Consistency → CRUD
```

**When this matters**: Changing session timeout, pooling, or lifecycle behavior

**Affected specs**:
1. **Driver Sessions**: Core timeout/lifecycle logic
2. **Transactions**: Transaction session timeout and state
3. **Retryable Writes**: Session refresh for retries
4. **Causal Consistency**: Session consistency guarantees
5. **CRUD**: Implicit session creation and management

**Example**: Changing how implicit sessions are created affects all operation types.

---

### Pattern 4: Topology Change Chain

```
SDAM → Server Selection → Connection Pooling → Retryable Operations → Load Balancers
```

**When this matters**: Adding a new topology type or changing topology detection

**Affected specs**:
1. **SDAM**: Topology detection and state machine
2. **Server Selection**: Selection rules for new topology
3. **Connection Pooling**: Pool behavior for topology (e.g., clearing pools)
4. **Retryable Operations**: Retry rules for topology
5. **Load Balancers**: If related to load balancing

**Example**: Adding LoadBalanced topology type required changes to all of these.

---

## Specific Examples of Cross-Specification Changes

### Example 1: Adding Client-Side Operations Timeout (CSOT)

The CSOT specification required coordinated changes to:

1. ✓ **Driver Sessions** - Session checkout timeout
2. ✓ **Transactions** - Transaction timeout vs operation timeout semantics
3. ✓ **Retryable Reads** - Timeout across retry attempts
4. ✓ **Retryable Writes** - Timeout across retry attempts
5. ✓ **Connection Monitoring and Pooling** - Connection checkout timeout
6. ✓ **CRUD** - Operation-level timeout
7. ✓ **Run Command** - Timeout attachment to commands (maxTimeMS)
8. ✓ **Change Streams** - Timeout for getMore operations
9. ✓ **GridFS** - Timeout for multi-operation workflows
10. ✓ **Server Selection** - Server selection timeout
11. ✓ **URI Options** - New `timeoutMS` option

**Total**: 11 specifications required changes

**Challenges**:
- Each spec needed to define timeout behavior for its domain
- Timeout calculation rules had to be consistent across all specs
- Interaction with existing timeout options had to be specified
- Test coverage needed across all affected specs

---

### Example 2: Adding Load Balancer Support

Required coordinated changes to:

1. ✓ **SDAM** - New LoadBalanced topology type
2. ✓ **Server Selection** - Selection rules for load balancers
3. ✓ **Connection Monitoring and Pooling** - Connection pinning behavior
4. ✓ **Driver Sessions** - Session pinning to connections
5. ✓ **Transactions** - Transaction pinning (already pins, but new rules)
6. ✓ **Retryable Reads** - Retry restrictions with load balancers
7. ✓ **Retryable Writes** - Retry restrictions with load balancers
8. ✓ **URI Options** - New `loadBalanced` option
9. ✓ **Connection String** - Validation rules for load balanced mode
10. ✓ **Initial DNS Seedlist Discovery** - SRV records with load balancers

**Total**: 10 specifications required changes

**Challenges**:
- New topology type affected core SDAM logic
- Connection pinning was a new concept that affected multiple specs
- Retry behavior had to be restricted in load balanced mode
- Validation rules to prevent incompatible options

---

### Example 3: Adding Stable API (Versioned API)

Required coordinated changes to:

1. ✓ **Run Command** - Attach apiVersion, apiStrict, apiDeprecationErrors to commands
2. ✓ **Driver Sessions** - API version with cluster time
3. ✓ **Transactions** - API version in transaction commands
4. ✓ **Connection String** - API version options in URI
5. ✓ **URI Options** - New API version options
6. ✓ **Command Monitoring** - API version in command events
7. ✓ **MongoClient** - ServerApi configuration

**Total**: 7 specifications required changes

**Challenges**:
- API version fields had to be attached to all commands
- Interaction with existing features (sessions, transactions) had to be specified
- Validation rules for API version requirements

---

## Why This Creates Inefficiency

The high degree of coupling between specifications creates several challenges:

### 1. Circular Dependencies

Specifications reference each other bidirectionally, making it difficult to understand or change one in isolation.

**Example**:
- Sessions spec says "see Transactions for transaction usage"
- Transactions spec says "see Sessions for session lifecycle"
- Retryable Writes spec says "see Sessions for txnNumber" and "see Transactions for interaction"
- All three share the `txnNumber` concept but describe it from different angles

### 2. Scattered Requirements

A single feature's requirements are distributed across 5-10 specifications, making it hard to understand the complete picture.

**Example**: To understand how a retryable write works in a transaction with a timeout, you must read:
- Driver Sessions (lsid, txnNumber)
- Transactions (transaction state, autocommit)
- Retryable Writes (retry logic, but note it doesn't apply in transactions)
- CSOT (timeout calculation)
- Run Command (how all fields are attached)
- SDAM (which servers are eligible)

### 3. Inconsistent Abstraction Levels

Some specs are low-level (wire protocol details) while others are high-level (API design), but they cross-reference each other, creating confusion about what belongs where.

**Example**:
- CRUD spec (high-level API) references Retryable Writes (mid-level behavior)
- Retryable Writes references Run Command (low-level wire protocol)
- Run Command references Sessions (mid-level state management)

### 4. Duplicate Information

The same behavior is described in multiple specs from different perspectives, leading to:
- Maintenance burden (update in multiple places)
- Risk of inconsistency (specs get out of sync)
- Confusion (which description is authoritative?)

**Example**: "How to attach lsid to a command" is described in:
- Driver Sessions spec
- Run Command spec
- Transactions spec
- Retryable Writes spec
- Retryable Reads spec

### 5. Testing Complexity

The Unified Test Format must understand all specifications, creating a mega-spec that references everything and becomes a bottleneck for changes.

### 6. Version Skew

When one spec changes, cross-references in other specs may not be updated immediately, leading to:
- Outdated cross-references
- Confusion about which version of a spec applies
- Difficulty tracking dependencies

### 7. Review Bottlenecks

Changes that affect multiple specs require:
- Coordination across multiple teams
- Multiple PRs that must be reviewed together
- Risk of merging some but not all changes
- Long review cycles

---

## Recommendations

Based on this analysis, here are recommendations for managing specification complexity:

### Short-Term Improvements

#### 1. Add Explicit Dependency Declarations

At the top of each specification, add a clear dependency section:

```markdown
## Dependencies

### Required Dependencies
This specification depends on and MUST be read in conjunction with:
- [Driver Sessions](../sessions/driver-sessions.md) - For lsid and session lifecycle
- [SDAM](../server-discovery-and-monitoring/...) - For topology requirements

### Optional Dependencies
This specification references but does not require:
- [Command Monitoring](../command-logging-and-monitoring/...) - For observability

### Dependents
This specification is referenced by:
- [CRUD](../crud/crud.md)
- [Transactions](../transactions/transactions.md)
```

**Benefits**:
- Makes coupling visible
- Helps reviewers understand impact
- Could be machine-readable for tooling

#### 2. Create Dependency Diagrams

Add visual diagrams showing specification relationships. This could be:
- A single diagram in the README
- Per-spec diagrams showing immediate dependencies
- Interactive visualization tool

#### 3. Consolidate Cross-References

Instead of duplicating information, use a single source of truth and reference it:

**Bad** (current):
- Sessions spec: "Attach lsid like this: ..."
- Transactions spec: "Attach lsid like this: ..."
- Retryable Writes spec: "Attach lsid like this: ..."

**Good** (proposed):
- Run Command spec: "Attach lsid like this: ..." (single source of truth)
- Sessions spec: "See Run Command for how to attach lsid"
- Transactions spec: "See Run Command for how to attach lsid"

#### 4. Version Cross-References

When referencing another spec, include the version:

```markdown
See [Driver Sessions v1.2](../sessions/driver-sessions.md) for session lifecycle.
```

This makes it clear which version of the dependency is expected.

### Medium-Term Improvements

#### 5. Create a Non-Normative Implementation Guide

Create a separate, non-normative guide that explains how specifications fit together (like the `driver-implementation-guide.md` created in this conversation).

**Benefits**:
- Provides narrative flow without affecting normative specs
- Can be updated independently
- Helps new implementers understand the big picture

#### 6. Consolidate Highly Coupled Specs

Consider merging specifications that are extremely tightly coupled:

**Candidate for consolidation**: Sessions + Transactions + Retryable Operations
- These three share `lsid` and `txnNumber`
- They have circular dependencies
- Changes to one almost always affect the others
- Could become "Operation Context Specification" with chapters for each

**Benefits**:
- Eliminates circular references
- Single source of truth for shared concepts
- Easier to maintain consistency

**Risks**:
- Large document (~3000 lines)
- Requires migration effort
- Need consensus across teams

#### 7. Separate Wire Protocol from API Specs

Create clearer separation between:
- **Wire Protocol Specs**: How to construct commands and interpret responses
- **API Specs**: What methods drivers expose to users
- **Behavior Specs**: How features work (retry logic, session lifecycle, etc.)

This would reduce cross-level references.

### Long-Term Improvements

#### 8. Specification Composition Tool

Build tooling that:
- Parses specification dependencies
- Validates cross-references
- Generates combined views (e.g., "show me everything about retryable writes")
- Detects circular dependencies
- Tracks version compatibility

#### 9. Modular Specification Format

Adopt a format that supports:
- Importing sections from other specs
- Versioned dependencies
- Conditional inclusion (e.g., "if implementing transactions, include this section")

#### 10. Specification Impact Analysis

When proposing a change, require an impact analysis:
- Which specs are affected?
- What changes are needed in each?
- What's the migration path?
- What's the testing burden?

This could be a template for specification proposals.

---

## Conclusion

MongoDB driver specifications are highly interconnected, with changes often cascading across 5-10 specifications. This creates inefficiency, confusion, and coordination overhead.

The root causes are:
- **Circular dependencies** between core specs (Sessions ↔ Transactions ↔ Retryable Operations)
- **Scattered requirements** across multiple specs
- **Duplicate information** described from different angles
- **Mixed abstraction levels** (wire protocol ↔ API ↔ behavior)

Short-term improvements (dependency declarations, diagrams, consolidated cross-references) can help manage the current complexity.

Medium-term improvements (implementation guide, consolidating highly coupled specs) can reduce the coupling.

Long-term improvements (tooling, modular format) can fundamentally change how specifications are authored and maintained.

The non-normative **Driver Implementation Guide** created alongside this document demonstrates one approach: providing a narrative view that helps implementers understand how specifications fit together, while keeping the normative specifications as the authoritative source of requirements.

---

## Appendix: Specification Dependency Graph

### Visual Representation

```
                    ┌─────────────────┐
                    │  Driver Sessions│
                    │   (Tier 1)      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
      ┌──────────┐   ┌──────────┐   ┌──────────┐
      │Retryable │   │Transaction│   │  Causal  │
      │  Writes  │   │  (Tier 2) │   │Consistency│
      │(Tier 2)  │   └─────┬────┘   └──────────┘
      └────┬─────┘         │
           │               │
           └───────┬───────┘
                   │
                   ▼
            ┌──────────┐
            │   CRUD   │
            │ (Tier 3) │
            └──────────┘

    ┌─────────────┐      ┌──────────────┐
    │    SDAM     │─────▶│   Server     │
    │  (Tier 1)   │      │  Selection   │
    └──────┬──────┘      │  (Tier 1)    │
           │             └──────┬───────┘
           │                    │
           ▼                    │
    ┌─────────────┐            │
    │ Connection  │◀───────────┘
    │   Pooling   │
    │  (Tier 3)   │
    └─────────────┘

         ┌──────────────┐
         │ Run Command  │◀─── All operation specs
         │  (Tier 2)    │
         └──────────────┘
                ▲
                │
         (depends on Sessions, Transactions,
          Retryable Ops, CSOT, Versioned API)
```

### Dependency Matrix

| Spec | Sessions | SDAM | Read/Write Concern | Server Selection | Transactions | Retryable Writes | Retryable Reads | Run Command | CSOT |
|------|----------|------|-------------------|------------------|--------------|------------------|-----------------|-------------|------|
| **Sessions** | - | ✓ | | | | | | | |
| **SDAM** | | - | | | | | | | |
| **Read/Write Concern** | | | - | | | | | | |
| **Server Selection** | | ✓ | ✓ | - | | | | | |
| **Transactions** | ✓ | ✓ | ✓ | ✓ | - | ✓ | | ✓ | |
| **Retryable Writes** | ✓ | ✓ | | ✓ | | - | | ✓ | ✓ |
| **Retryable Reads** | ✓ | ✓ | | ✓ | | | - | ✓ | ✓ |
| **Run Command** | ✓ | | ✓ | ✓ | ✓ | ✓ | ✓ | - | ✓ |
| **CSOT** | ✓ | ✓ | | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| **CRUD** | ✓ | | ✓ | ✓ | | ✓ | ✓ | ✓ | ✓ |

✓ = Depends on (row depends on column)

This matrix shows the dense interconnection between core specifications.

