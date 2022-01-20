====================================
Server Wire version and Feature List
====================================

.. list-table::
   :header-rows: 1

   * - Server version
     - Wire version
     - Feature List

   * - 2.6
     - 1
     - | Aggregation cursor
       | Auth commands

   * - 2.6
     - 2
     - | Write commands (insert/update/delete)
       | Aggregation $out pipeline operator

   * - 3.0
     - 3
     - | listCollections
       | listIndexes
       | SCRAM-SHA-1
       | explain command

   * - 3.2
     - 4
     - | (find/getMore/killCursors) commands
       | currentOp command
       | fsyncUnlock command
       | findAndModify take write concern
       | Commands take read concern
       | Document-level validation
       | explain command supports distinct and findAndModify

   * - 3.4
     - 5
     - | Commands take write concern
       | Commands take collation

   * - 3.6
     - 6
     - | Supports OP_MSG
       | Collection-level ChangeStream support
       | Retryable Writes
       | Causally Consistent Reads
       | Logical Sessions
       | update "arrayFilters" option

   * - 4.0
     - 7
     - | ReplicaSet transactions
       | Database and cluster-level change streams and startAtOperationTime option

   * - 4.2
     - 8
     - | Sharded transactions
       | Aggregation $merge pipeline operator
       | update "hint" option

   * - 4.4
     - 9
     - | Streaming protocol for SDAM
       | ResumableChangeStreamError error label
       | delete "hint" option
       | findAndModify "hint" option
       | createIndexes "commitQuorum" option

   * - 5.0
     - 13
     - | Consistent $collStats count behavior on sharded and non-sharded topologies
       | $out and $merge on secondaries (technically FCV 4.4+)
       
   * - 5.1
     - 14
     - |
     
   * - 5.2
     - 15
     - |
     
   * - 5.3
     - 16
     - |

In server versions 5.0 and earlier, the wire version was defined as a numeric literal in `src/mongo/db/wire_version.h <https://github.com/mongodb/mongo/blob/master/src/mongo/db/wire_version.h>`_. Since server version 5.1 (`SERVER-58346 <https://jira.mongodb.org/browse/SERVER-58346>`_), the wire version is derived from the number of releases since 4.0 (using `src/mongo/util/version/releases.h.tpl <https://github.com/mongodb/mongo/blob/master/src/mongo/util/version/releases.h.tpl>`_ and `src/mongo/util/version/releases.yml <https://github.com/mongodb/mongo/blob/master/src/mongo/util/version/releases.yml>`_).
