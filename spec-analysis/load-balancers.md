# Analysis: load-balancers

## Missing Tests

- [ ] Drivers MUST throw an exception if the connection string contains more than one host with `loadBalanced=true`
    (§URI Validation)
- [ ] `killCursors` MUST be executed on the same pinned connection when cursor is closed (§Behaviour With Cursors)
- [ ] If `getMore` fails with a network error, the connection MUST remain pinned to the cursor (§Behaviour With Cursors)
- [ ] Two concurrent transactions from different sessions MUST NOT share a connection (§Behaviour With Transactions)
- [ ] Connection pool MUST track connection purpose in three categories: cursors, transactions, other (§Connection
    Tracking)
- [ ] `WaitQueueTimeoutError` MUST include a detailed message with connection breakdown (§Connection Tracking) — error
    message format not validated
- [ ] Pre-handshake errors MUST NOT perform SDAM error handling (§Initial Handshake Errors)
- [ ] Pool clearing after handshake errors MUST be scoped to `serviceId` only (§Initial Handshake Errors)

## Ambiguities

- **`loadBalanced=false` vs. omitted**: Spec says default is `false` but doesn't clarify whether driver code
    distinguishes explicit `false` from omitted.
- **SRV lookup timing for validation**: Drivers doing async SRV lookup may only discover the host count error during
    first operation, not at `MongoClient` construction. Spec acknowledges this but doesn't define the required timing.
- **`logicalSessionTimeoutMinutes` in LB mode**: Spec says ignore it, but if the server returns a non-null value, should
    the driver warn or silently ignore?
- **Concurrent `next()` and `close()` on pinned cursor**: Spec allows either documenting that it's unsupported OR
    preventing it — drivers may choose differently.

## Inconsistencies

- **Static topology vs. dynamic pool changes**: Monitoring section describes a "static" topology, but Error Handling
    section allows dynamic pool clearing scoped to `serviceId`. Interaction between a static topology and dynamic pool
    changes is underspecified.
- **Cursor pinning vs. transaction pinning**: Both sections describe pinning, but the interaction when a transaction
    opens a cursor is not clarified. Does transaction pinning override cursor pinning?
- **transactions.yml vs. cursors.yml**: Both test pinning but the interaction (transaction that opens a cursor) is not
    tested.

## Notes

- 8 unified test files (cursors, event-monitoring, connection-establishment, server-selection, sdam-error-handling,
    transactions, wait-queue-timeouts).
- `serviceId` isolation for pool clearing is tested in `sdam-error-handling.yml` but coverage is sparse.
- Read preference: LoadBalancer servers MUST be treated like mongos — tested in `server-selection.yml` but only basic
    read preference types.
