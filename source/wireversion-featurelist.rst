====================================
Server Wire version and Feature List
====================================

.. list-table::
   :header-rows: 1

   * - Server version
     - Wire version
     - Feature List

   * - 2.4 and before
     - 0
     - Text search

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
     - | List collections
       | List indexes
       | SCRAM-SHA1
       | explain command 

   * - 3.2
     - 4
     - | (find/getMore/killCursors) commands
       | findAndModify take write concern
       | Commands take read concern
       | Document-level validation
 
   * - 3.4
     - 5
     - | Commands take write concern
       | Commands take collation 

   * - 3.6
     - 6
     - | Supports OP_MSG
       | ChangeStream support
       | Retryable Writes
       | Causally Consistent Reads
       | Logical Sessions


For more information see MongoDB Server repo: https://github.com/mongodb/mongo/blob/master/src/mongo/db/wire_version.h
