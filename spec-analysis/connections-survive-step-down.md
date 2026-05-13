# Analysis: connections-survive-step-down

## Important Note

**No main specification file exists.** This component contains only `tests/README.md` with test procedures. There is no
normative document defining what "surviving a step-down" means or what driver behaviors are required.

## Missing Tests (to be implemented as unified test format YAML)

- [ ] **getMore Iteration**: After a primary step-down, subsequent `getMore` calls on an existing cursor succeed without
    new pool entries being created
- [ ] **Not Primary – Keep Connection Pool** (server 4.2+): Error 10107 (`NotPrimary`) keeps the connection pool intact;
    subsequent operations succeed
- [ ] **Not Primary – Reset Connection Pool** (server 4.0): Error 10107 triggers a `PoolClearedEvent`; new connections
    are created
- [ ] **Shutdown in progress – Reset Connection Pool** (server 4.0+): Error 91 (`ShutdownInProgress`) clears the pool
    and increments the connection count
- [ ] **Interrupted at shutdown – Reset Connection Pool** (server 4.0+): Error 11600 (`InterruptedAtShutdown`) clears
    the pool and increments the connection count

## Ambiguities

- **Test setup write concern**: `writeConcern: majority` — what if no secondary is available? Should tests be skipped or
    is the majority write always assumed to succeed?
- **"No new PoolClearedEvent"**: Does "no new event" mean exactly 0 events or ≤1? The alternative check (totalCreated
    unchanged) also needs a clear baseline definition.
- **Server version boundary**: Behavior differs at 4.0 vs 4.2. What about 4.1 (a development version)? Must drivers test
    4.0 behavior if they only support 4.2+?
- **`failCommand` fail point**: Spec does not clarify whether the configuration requires `writeConcern`, whether the
    activation should be verified before proceeding, or what timeout to use if the fail point never fires.

## Inconsistencies

- **CMAP vs serverStatus precedence**: Tests allow either `PoolClearedEvent` (CMAP) or a `serverStatus` check, but do
    not clarify which is authoritative for CMAP-implementing drivers.
- **Scattered server version requirements**: getMore test requires 4.2+, Not Primary Reset requires 4.0, Shutdown tests
    require 4.0+. The component has no minimum version defined in its header.

## Notes

- Suggest creating a proper spec file `connections-survive-step-down.md` that defines normative behavior and references
    SDAM/CMAP specs.
- Test procedures should be converted to unified test format YAML where possible.
- Related specs: SDAM (`server-discovery-and-monitoring`), CMAP (`connection-monitoring-and-pooling`).
