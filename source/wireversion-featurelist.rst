====================================
Server Wire version and Feature List
====================================

+----------------+--------------+---------------------------------------+
| Server version | Wire version | Feature List                          |
+================+==============+=======================================+
| <2.4           | 0            | Text search                           | 
+----------------+--------------+---------------------------------------+
| 2.6            | 1            | Aggregation cursor                    |  
|                |              | Auth commands                         | 
+----------------+--------------+---------------------------------------+
| 2.6            | 2            | Write commands (insert/update/delete) | 
|                |              | Aggregation $out pipeline operator    |
+----------------+--------------+---------------------------------------+
| 3.0            | 3            | List Collections                      |
|                |              | List indexes                          |
|                |              | SCRAM-SHA1                            |
|                |              | Explain command                       |   
+----------------+--------------+---------------------------------------+
| 3.2            | 4            | (find/getMore/killcursors) commands   |
|                |              | findAndModify take write concern      |
|                |              | Commands that take read concern       |
|                |              | Document-level validation             | 
+----------------+--------------+---------------------------------------+
| 3.4            | 5            | Commands that take a write concern    |
|                |              | Commands take collation               |
+----------------+--------------+---------------------------------------+
| 3.6            | 6            | Supports OP_MSG                       |
|                |              | ChangeStream support                  |
|                |              | Retryable Writes                      |
|                |              | Causually Consistent Reads            |
|                |              | Logical Sessions                      |
+----------------+--------------+---------------------------------------+

For more information see MongoDB Server repo: https://github.com/mongodb/mongo/blob/master/src/mongo/db/wire_version.h
