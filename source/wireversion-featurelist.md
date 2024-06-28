# Server Wire version and Feature List

<table>
<thead>
<tr class="header">
<th>Server version</th>
<th>Wire version</th>
<th>Feature List</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>2.6</td>
<td>1</td>
<td><div class="line-block">Aggregation cursor<br />
Auth commands</div></td>
</tr>
<tr class="even">
<td>2.6</td>
<td>2</td>
<td><div class="line-block">Write commands (insert/update/delete)<br />
Aggregation $out pipeline operator</div></td>
</tr>
<tr class="odd">
<td>3.0</td>
<td>3</td>
<td><div class="line-block">listCollections<br />
listIndexes<br />
SCRAM-SHA-1<br />
explain command</div></td>
</tr>
<tr class="even">
<td>3.2</td>
<td>4</td>
<td><div class="line-block">(find/getMore/killCursors) commands<br />
currentOp command<br />
fsyncUnlock command<br />
findAndModify take write concern<br />
Commands take read concern<br />
Document-level validation<br />
explain command supports distinct and findAndModify</div></td>
</tr>
<tr class="odd">
<td>3.4</td>
<td>5</td>
<td><div class="line-block">Commands take write concern<br />
Commands take collation</div></td>
</tr>
<tr class="even">
<td>3.6</td>
<td>6</td>
<td><div class="line-block">Supports OP_MSG<br />
Collection-level ChangeStream support<br />
Retryable Writes<br />
Causally Consistent Reads<br />
Logical Sessions<br />
update "arrayFilters" option</div></td>
</tr>
<tr class="odd">
<td>4.0</td>
<td>7</td>
<td><div class="line-block">ReplicaSet transactions<br />
Database and cluster-level change streams and startAtOperationTime
option</div></td>
</tr>
<tr class="even">
<td>4.2</td>
<td>8</td>
<td><div class="line-block">Sharded transactions<br />
Aggregation $merge pipeline operator<br />
update "hint" option</div></td>
</tr>
<tr class="odd">
<td>4.4</td>
<td>9</td>
<td><div class="line-block">Streaming protocol for SDAM<br />
ResumableChangeStreamError error label<br />
delete "hint" option<br />
findAndModify "hint" option<br />
createIndexes "commitQuorum" option</div></td>
</tr>
<tr class="even">
<td>5.0</td>
<td>13</td>
<td><div class="line-block">$out and $merge on secondaries (technically
FCV 4.4+)</div></td>
</tr>
<tr class="odd">
<td>5.1</td>
<td>14</td>
<td><div class="line-block"></div></td>
</tr>
<tr class="even">
<td>5.2</td>
<td>15</td>
<td><div class="line-block"></div></td>
</tr>
<tr class="odd">
<td>5.3</td>
<td>16</td>
<td><div class="line-block"></div></td>
</tr>
</tbody>
</table>

In server versions 5.0 and earlier, the wire version was defined as a
numeric literal in
[src/mongo/db/wire_version.h](https://github.com/mongodb/mongo/blob/master/src/mongo/db/wire_version.h).
Since server version 5.1
([SERVER-58346](https://jira.mongodb.org/browse/SERVER-58346)), the wire
version is derived from the number of releases since 4.0 (using
[src/mongo/util/version/releases.h.tpl](https://github.com/mongodb/mongo/blob/master/src/mongo/util/version/releases.h.tpl)
and
[src/mongo/util/version/releases.yml](https://github.com/mongodb/mongo/blob/master/src/mongo/util/version/releases.yml)).