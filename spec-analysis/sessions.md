# Analysis: sessions

## Missing Tests

- [ ] Drivers MUST clear the session pool without sending `endSessions` after fork (§Server Session Pool)
- [ ] An implicit session MUST be returned to the pool immediately after operation completion
- [ ] Multiple calls to `endSession` MUST be allowed without error (§endSession)
- [ ] Operations attempted on an ended `ClientSession` MUST report an error (§endSession)
- [ ] `lsid` MUST NOT be appended to commands sent during connection opening/authentication (§Exceptions to sending
    lsid)
- [ ] Drivers MUST NOT gossip cluster time on SDAM commands (§Gossipping the cluster time) — negative test

## Ambiguities

- **`lastUse` timing**: "Updated every time the session ID is sent to the server" — does "sent" mean the lsid was
    appended, or that the server successfully acknowledged the command? Edge case: socket write fails after appending
    lsid.
- **One-minute staleness threshold**: Spec does not define clock precision or how clock skew affects the "one minute
    left" reuse decision.
- **`endSession` vs dispose pattern**: "SHOULD support that in addition to OR instead of `endSession`" — can a driver
    provide only dispose and omit `endSession`?
- **Cluster time comparison with null**: When both MongoClient and ClientSession cluster times are null, what is sent?
    Spec says "greater of... (either could be null)" without defining null semantics.

## Inconsistencies

- **`advanceClusterTime` vs. MongoClient cluster time**: `advanceClusterTime` allows applications to set arbitrary
    cluster time, but MongoClient clock is only advanced from server responses. An invalid application-supplied cluster
    time could leak into a session.
- **Dirty session handling in pool algorithm**: Spec says mark sessions dirty on network error but the pool acquisition
    algorithm doesn't mention checking the dirty flag. Dirty sessions should be silently discarded, but this is not
    documented in the algorithm section.
- **snapshot-sessions.yml vs. spec**: Tests reference snapshot sessions but the main `sessions.md` doesn't have a
    snapshot section — it delegates to `snapshot-sessions.md`. Integration between the two is unclear.

## Notes

- 7 unified test files. Prose tests (5 items) cover pool LIFO, cluster time, explicit/implicit sessions.
- Prose test 2 (Pool is LIFO) and Prose test 3 (clusterTime in commands) require APM inspection — not easily automated
    in unified format.
