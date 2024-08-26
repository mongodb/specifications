# Summary

[Introduction](README.md)
[Mantras](driver-mantras.md)

# Specifications

- [Serialization]()
  - [BSON](BSON.md)
  - [ObjectId](objectid.md)
  - [Decimal128](bson-decimal128/decimal128.md)
  - [UUID](uuid.md)
  - [DBRef](dbref.md)
  - [Extended JSON](extended-json.md)

---

- [Communication]()
  - [`OP_MSG`](message/OP_MSG.md)
  - [Command Execution](run-command/run-command.md)
  - [Connection String](connection-string/connection-string-spec.md)
  - [URI Options](uri-options/uri-options.md)
  - [OCSP](ocsp-support/ocsp-support.md)
  - [Initial Handshake](mongodb-handshake/handshake.md)
  - [Wire Compression](compression/OP_COMPRESSED.md)
  - [SOCKS5](socks5-support/socks5.md)
  - [Initial DNS Seedlist Discovery](initial-dns-seedlist-discovery/initial-dns-seedlist-discovery.md)

---

- [Connectivity]()
  - [Server Discovery and Monitoring](server-discovery-and-monitoring/server-discovery-and-monitoring.md)
  - [Connection Monitoring and Pooling](connection-monitoring-and-pooling/connection-monitoring-and-pooling.md)
  - [Load Balancer Support](load-balancers/load-balancers.md)

---

- [Availability]()
  - [Server Monitoring](server-discovery-and-monitoring/server-monitoring.md)
  - [`SRV` Polling for mongos Discovery](polling-srv-records-for-mongos-discovery/polling-srv-records-for-mongos-discovery.md)
  - [Server Selection](server-selection/server-selection.md)
  - [Max Staleness](max-staleness/max-staleness.md)

---

- [Resilience]()
  - [Retryability]()
    - [Reads](retryable-reads/retryable-reads.md)
    - [Writes](retryable-writes/retryable-writes.md)
  - [CSOT](client-side-operations-timeout/client-side-operations-timeout.md)
  - [Consistency]()
    - [Sessions](sessions/driver-sessions.md)
    - [Causal Consistency](causal-consistency/causal-consistency.md)
    - [Snapshot Reads](sessions/snapshot-sessions.md)
    - [Transactions](transactions/transactions.md)
    - [Convenient Transactions API](transactions-convenient-api/transactions-convenient-api.md))

---

- [Programmability]()
  - [Resource Management]()
    - [Databases](enumerate-databases.md)
    - [Collections](enumerate-collections.md)
    - [Indexes](index-management/index-management.md)
  - [Data Management]()
    - [CRUD](crud/crud.md)
    - [Collation](collation/collation.md)
    - [Write Commands](server_write_commands.md)
    - [Bulk API](driver-bulk-update.md)
    - [Bulk Write](crud/bulk-write.md)
    - [R/W Concern](read-write-concern/read-write-concern.md)
  - [Cursors]()
    - [Change Streams](change-streams/change-streams.md)
    - [`find`/`getMore`/`killCursors`](find_getmore_killcursors_commands.md)
  - [GridFS](gridfs/gridfs-spec.md)
  - [Stable API](versioned-api/versioned-api.md)
  - [Security]()
    - [Client Side Encryption](client-side-encryption/client-side-encryption.md)
    - [BSON Binary Subtype 6](client-side-encryption/subtype6.md))

---

- [Observability]()
  - [Command Logging and Monitoring](command-logging-and-monitoring/command-logging-and-monitoring.md)
  - [SDAM Logging and Monitoring](server-discovery-and-monitoring/server-discovery-and-monitoring-logging-and-monitoring.md)
  - [Standardized Logging](logging/logging.md)
  - [Connection Pool Logging](connection-monitoring-and-pooling/connection-monitoring-and-pooling.md)

---

- [Testability]()
  - [Unified Test Format](unified-test-format/unified-test-format.md)
  - [Atlas Data Federation Testing](atlas-data-lake-testing/tests/README.md)
  - [Performance Benchmarking](benchmarking/benchmarking.md)
  - [BSON Corpus](bson-corpus/bson-corpus.md)
  - [Replication Event Resilience](connections-survive-step-down/tests/README.md)
  - [FAAS Automated Testing](faas-automated-testing/faas-automated-testing.md)
  - [Atlas Serverless Testing](serverless-testing/README.md)
