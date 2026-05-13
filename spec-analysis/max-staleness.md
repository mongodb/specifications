# Analysis: max-staleness

## Missing Tests

- [ ] Any visible server with `maxWireVersion < 5` (but > 0) when `maxStalenessSeconds` is set — current tests only use
    wire version 0 for PossiblePrimary/Unknown
- [ ] `maxStalenessSeconds=-1` in URI parsed as "no maximum staleness" (equivalent to absent)
- [ ] Tag set + staleness interaction when no primary is known — limited to one `PrimaryPreferred_tags` test in
    ReplicaSetNoPrimary
- [ ] Negative staleness estimate handling — spec says staleness "could be temporarily negative" but no test exercises
    this path

## Ambiguities

- **Implicit primary mode + `maxStalenessSeconds`**: "Combining `maxStalenessSeconds` with mode `primary` MUST be
    invalid" — does this apply to the implicit/default primary mode (no explicit mode in URI), or only explicit
    `primary`? Tests only cover explicit mode.
- **"Available server" definition**: "If any server's maxWireVersion is less than 5..." — "available" is used without
    being defined in this spec. References Server Selection spec but should define or link inline.

## Inconsistencies

- **`heartbeatFrequencyMS` in tests**: Several tests omit it, relying on driver defaults. Spec specifies different
    defaults for single-threaded (60s) vs. multi-threaded (10s) drivers, but no test validates the staleness threshold
    calculation with these different defaults.
- **PossiblePrimary + low wire version**: `OneKnownTwoUnavailable.yml` correctly ignores PossiblePrimary/Unknown with
    wire version 0, but no test covers those server types with 0 < wire version < 5.

## Notes

- 32 test files well-focused on staleness formula calculation. Error tests (`MaxStalenessTooSmall`,
    `MaxStalenessWithModePrimary`, `ZeroMaxStaleness`) are well-covered.
- No prose tests. CSRS (config server replica set) opTime filtering is noted as router/shard behavior — not driver
    responsibility.
