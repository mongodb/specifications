# Analysis: enumerate-collections

## Missing Tests

- [ ] `listCollections` supports `filter` option to match collection documents
- [ ] `cursor.batchSize` option MAY be passed to control the initial batch size
- [ ] `comment` option SHOULD be passed to `listCollections` and MUST NOT be attached to subsequent `getMore` calls
- [ ] Methods MUST allow a filter to be passed
- [ ] Methods MUST apply timeouts per the Client Side Operations Timeout spec — **no existing tests cover this**
- [ ] `listCollectionNames` MUST specify `nameOnly=true` when only accessing names
- [ ] `listCollectionNames` MUST NOT set `nameOnly` if the filter specifies keys other than `name`
- [ ] `listMongoCollections` MUST specify `nameOnly=true`
- [ ] `listMongoCollections` MUST NOT set `nameOnly` if the filter specifies keys other than `name`
- [ ] `listCollections` MUST run on the primary in a replica set topology, unless directly connected to a secondary in a
    Single topology
- [ ] Methods MUST NOT return system collections (those containing `$`) from name-based methods

## Ambiguities

- **Varying requirement levels for options**: "MUST allow filter, MAY allow batchSize, SHOULD allow comment" —
    inconsistent; should clarify which options are truly mandatory.
- **`nameOnly` logic (double negative)**: "MUST NOT set `nameOnly` if a filter specifies any keys other than `name`" —
    should be rewritten positively: "Set `nameOnly=true` only when there is no filter or the filter keys include only
    `name`."
- **MongoDB 4.4 `ns` field handling**: Complex conditional logic for when to manually populate `ns` in models vs. when
    the server provides it, with no clear runtime version-detection mechanism.

## Inconsistencies

- **Timeout requirement without tests**: Spec REQUIRES timeout application per CSOT (line 135–136) but the Test Plan has
    NO tests for timeout behavior.
- **Replica set secondary handling**: "listCollections can be run on a secondary node" but also "Drivers MUST run
    listCollections on the primary node in a replica set topology, unless directly connected to a secondary in a Single
    topology." Contradictory phrasing in the same spec.
- **Array vs cursor return type**: Unclear whether existing array-returning methods satisfy the cursor SHOULD
    requirement, or whether a separate cursor-based method is also needed.

## Notes

- RST stub at `source/enumerate-collections.rst` redirects to the .md file — can be cleaned up.
- Header "Minimum Server Version: 1.8" conflicts with feature requirements for 3.6 (`nameOnly`) and 4.0+
    (`authorizedCollections`). Version requirements should be tiered per feature.
- Test Plan (lines 251–281) is prose-only; no JSON/YAML fixtures.
- [DRIVERS-935](https://jira.mongodb.org/browse/DRIVERS-935) (Backlog): collection enumeration specification is out of
    date.
