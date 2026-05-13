# Analysis: enumerate-databases

## Missing Tests

- [ ] `listDatabases` SHOULD return an `Iterable` of database specification models or documents
- [ ] `listDatabases` SHOULD support `filter`, `authorizedDatabases`, and `comment` options
- [ ] `listDatabaseNames` SHOULD return an `Iterable` of strings
- [ ] `listDatabaseNames` SHOULD support `filter`, `authorizedDatabases`, and `comment` options
- [ ] `listMongoDatabases` SHOULD specify `nameOnly=true` when executing the `listDatabases` command
- [ ] `MongoDatabase` objects from `listMongoDatabases` SHOULD inherit `MongoClient` options (read preference, write
    concern)
- [ ] `listDatabases` MUST run on the primary in a replica set topology, unless directly connected to a secondary in a
    Single topology
- [ ] `listDatabases` MUST apply timeouts per the Client Side Operations Timeout spec — **no existing tests cover this**
- [ ] Results MUST NOT contain duplicate database names
- [ ] `authorizedDatabases` option: test all three states (unspecified/missing, `false`, `true`)
- [ ] Filter SHOULD support predicates on: `name`, `sizeOnDisk`, `empty`, `shards`

## Ambiguities

- **Option inheritance semantics**: "MongoDatabase objects SHOULD inherit the same MongoClient options that would
    otherwise be inherited" — does this copy options at creation time or maintain a dynamic reference? What happens if
    `MongoClient` options change after the call?
- **`nameOnly` with complex filter**: Spec says "SHOULD specify `nameOnly`" but, unlike `enumerate-collections`, does
    not state an exception for non-name filters. Should `nameOnly` still be set even when a filter on other fields is
    provided?
- **`authorizedDatabases` semantics**: Three values are defined but the spec only references server documentation
    without explaining driver-level behavior for each value.

## Inconsistencies

- **Timeout requirement without tests**: Spec REQUIRES timeout application per CSOT but the Test Plan has NO tests for
    timeout behavior.
- **"Minimum Server Version: 3.6" vs pre-3.6 references**: The Changelog mentions "Removed note that applied to pre-3.6
    servers" but the header still implies support starts at 3.6, while other sections discuss older behavior.

## Notes

- RST stub at `source/enumerate-databases.rst` redirects to the .md file — can be cleaned up.
- Test Plan only has 3 test cases; more comprehensive coverage is needed.
- Good Q&A section explaining design decisions around `totalSize` reporting.
