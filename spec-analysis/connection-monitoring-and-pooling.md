# Analysis: connection-monitoring-and-pooling

## Missing Tests

- [ ] Fork detection: pool MUST clear connections and close all after fork — not expressible in unified test format
- [ ] Load-balanced pool clearing MUST increment per-`serviceId` generation and MUST NOT transition pool to "paused" —
    no YAML test
- [ ] Load-balanced `serviceId`-to-generation map management during handshake — no test
- [ ] `SystemOverloadedError` and `RetryableError` labels MUST be added to network errors during connection
    establishment — no test (recent addition: 2025-11-21)
- [ ] `interruptInUseConnections=true` in pool clear: in-use connections MUST be interrupted — only pending connections
    tested
- [ ] Background thread: idle connection expiration via `maxIdleTimeMS` — existence tested, actual timeout enforcement
    not tested
- [ ] Stale connection from cleared `serviceId` (load-balanced) MUST be detected and closed
- [ ] `pendingConnectionCount` MUST be decremented in correct order relative to marking connection available — ordering
    not validated

## Ambiguities

- **`interruptInUseConnections` scope**: "Interrupt connections whose generation is ≤ generation at the moment of clear
    (before increment)" — ambiguous: connections created before the clear, or connections with a matching generation
    number?
- **Non-blocking close timing**: "Closing SHOULD be non-blocking, performed at a later time" — how long is "later"? Can
    the application depend on socket closure before the next operation?
- **`maxConnecting` slot for failed connections**: Does a connection that fails during TLS handshake (after
    `ConnectionCreatedEvent`, before `ConnectionReadyEvent`) consume a `maxConnecting` slot?
- **`waitQueueTimeoutMS` vs. CSOT interaction**: Both are mentioned as governing checkout timeout. Which takes
    precedence?
- **`SystemOverloadedError` label boundary**: Error labels added during "connection establishment or `hello`" but NOT
    during authentication — where exactly does authentication begin relative to handshake?

## Inconsistencies

- **Connection state tracking**: States ("pending", "available", "in use", "closed") are defined but spec says "not
    required that drivers include this field" — creates ambiguity about whether drivers must track state explicitly for
    correctness.
- **`ready()` idempotency**: MUST return immediately and MUST NOT emit `PoolReadyEvent` if already ready — but when
    paused→ready, event MUST be emitted "before background thread resumes." Atomicity and ordering requirements for
    state transitions are underspecified.
- **WaitQueue eviction error type**: Tests show `PoolClearedError` for evicted requests, but spec says "return errors
    indicating that the pool was cleared" — not all cleared-queue errors are necessarily `PoolClearedError`.
- **Available connection iteration order**: Spec says search for non-perished connection but doesn't specify order
    (FIFO, LIFO, random) — creates potential inconsistency across drivers.

## Notes

- 35 YAML unit-style tests in `cmap-format/` for pool creation, checkout, check-in, clearing. 2 logging tests in
    `/logging` subdirectory.
- 5 prose tests (configuration, URI, event subscription) — ~12% of critical coverage is manual. Fork behavior is
    fundamentally untestable in unified format.
- Load balancer mode is a significant feature but `serviceId`-based tracking tests are absent — likely requires a
    specific deployment topology.
- Backpressure error labels (2025-11-21 changelog) appear to have no corresponding test coverage yet.
