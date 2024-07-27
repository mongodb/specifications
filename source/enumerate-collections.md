# Enumerating Collections

- Status: Accepted
- Minimum Server Version: 1.8

______________________________________________________________________

## Abstract

A driver can contain a feature to enumerate all collections belonging to a database. This specification defines how
collections should be enumerated.

## META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

### Terms

**MongoClient**\
Driver object representing a connection to MongoDB. This is the root object of a driver's API and MAY
be named differently in some drivers.

**Iterable**\
An object or data structure that is a sequence of elements that can be iterated over. This spec is
flexible on what that means as different drivers will have different requirements, types, and idioms.

### listCollections Database Command

The `listCollections` command returns a cursor:

```javascript
db.runCommand( { listCollections: 1 } );
```

The command also accepts options.

The `filter` option, which acts like a query against the returned collection documents. You can i.e. use the following
to only list the collections beginning with `test`:

```javascript
db.runCommand( { listCollections: 1, filter: { name: /^test/ } } );
```

Or to find all capped collections:

```javascript
db.runCommand( { listCollections: 1, filter: { 'options.capped': true } } );
```

The `cursor.batchSize` option, which allows you to set how many initial collections should be returned as part of the
cursor specification document that comes back from the server. This first batch is part of the returned structure in the
`firstBatch` key (see more about return types further on).

The command returns a cursor definition structure:

```javascript
{
    cursor: {
        id: <long>,
        ns: <string>,
        firstBatch: [<object>, <object>, ...]
    },
    ok: 1
}
```

With the `cursor.id` and `cursor.ns` fields you can retrieve further collection information structures.

The command also returns the field `ok` to signal whether the command was executed successfully.

This will return the first 25 collection descriptions as part of the returned document:

```javascript
db.runCommand( { listCollections: 1, cursor : { batchSize: 25 } } );
```

MongoDB 4.4 introduced a `comment` option to the `listCollections` database command. This option enables users to
specify a comment as an arbitrary BSON type to help trace the operation through the database profiler, currentOp and
logs. The default is to not send a value. If a comment is provided on pre-4.4 servers, the comment should still be
attached and the driver should rely on the server to provide an error to the user.

Example of usage of the comment option:

```javascript
db.runCommand({"listCollections": 1, "comment": "hi there"})
```

Any comment set on a `listCollections` command is inherited by any subsequent `getMore` commands run on the same
`cursor.id` returned from the `listCollections` command. Therefore, drivers MUST NOT attach the comment to subsequent
getMore commands on a cursor.

#### Return types

The `listCollections` command returns a cursor description. The format that is returned is the same as for any other
command cursor:

```javascript
{
    cursor: {
        id: <long>,
        ns: <string>,
        firstBatch: [<object>, <object>, ...]
    },
    ok: 1
}
```

The number of objects in the `firstBatch` field depends on the `cursor.batchSize` option.

Drivers MAY expose methods to return collection names as an array. If your driver already has such a method, its return
type MUST NOT be changed in order to prevent breaking backwards compatibility.

Drivers SHOULD expose (a) method(s) to return collection information through a cursor, where the information for each
collection is represented by a single document.

### Driver methods

Drivers SHOULD use the method name `listCollections` for a method that returns all collections with a cursor return
type. Drivers MAY use an idiomatic variant that fits the language the driver is for.

If a driver already has a method to perform one of the listed tasks, there is no need to change it. Do not break
backwards compatibility when adding new methods.

All methods:

- SHOULD be on the database object.
- MUST allow a filter to be passed to include only requested collections.
- MAY allow the `cursor.batchSize` option to be passed.
- SHOULD allow the `comment` option to be passed.
- MUST apply timeouts per the
  [Client Side Operations Timeout](./client-side-operations-timeout/client-side-operations-timeout.md) specification.

All methods that return cursors MUST support the timeout options documented in
[Client Side Operations Timeout: Cursors](./client-side-operations-timeout/client-side-operations-timeout.md#cursors).

#### Getting Collection Names

Drivers MAY implement a MongoClient method that returns an Iterable of strings, where each string corresponds to a
collection name. This method SHOULD be named `listCollectionNames`.

MongoDB 4.0 introduced a `nameOnly` boolean option to the `listCollections` database command, which limits the command
result to only include collection names. NOTE: `nameOnly` is applied before any filter is applied.

Example return:

```javascript
[
    "me",
    "oplog.rs",
    "replset.minvalid",
    "startup_log",
    "system.indexes",
    "system.replset"
]
```

Server version between 2.7.6 (inclusive) and 4.0 (exclusive) do not support the `nameOnly` option for the
`listCollections` command and will ignore it without raising an error. Therefore, drivers MUST always specify the
`nameOnly` option when they only intend to access collection names from the `listCollections` command result, except
drivers MUST NOT set `nameOnly` if a filter specifies any keys other than `name`.

MongoDB 4.0 also added an `authorizedCollections` boolean option to the `listCollections` command, which can be used to
limit the command result to only include collections the user is authorized to use. Drivers MAY allow users to set the
`authorizedCollections` option on the `listCollectionNames` method.

#### Getting Full Collection Information

Drivers MAY implement a method to return the full `name/options` pairs that are returned from both `listCollections` (in
the `res.cursor.firstBatch` field, and subsequent retrieved documents through getmore on the cursor constructed from
`res.cursor.ns` and `res.cursor.id`), and the query result for `system.namespaces`.

The returned result for each variant MUST be equivalent, and each collection that is returned MUST use the field names
`name` and `options`.

In MongoDB 4.4, the `ns` field was removed from the index specifications, so the index specification included in the
`idIndex` field of the collection information will no longer contain an `ns` field.

- For drivers that report those index specifications in the form of documents or dictionaries, no special handling is
  necessary, but any documentation of the contents of the documents/dictionaries MUST indicate that the `ns` field will
  no longer be present in MongoDB 4.4+. If the contents of the documents/dictionaries are undocumented, then no special
  mention of the `ns` field is necessary.
- For drivers that report those index specifications in the form of statically defined models, the driver MUST manually
  populate the `ns` field of the models with the appropriate namespace if the server does not report it in the
  `listCollections` command response. The `ns` field is not required to be a part of the models, however.

Example return (a cursor which returns documents, not a simple array):

```javascript
{
    "name" : "me", "options" : { "flags" : 1 }
},
{
    "name" : "oplog.rs", "options" : { "capped" : true, "size" : 10485760, "autoIndexId" : false }
},
{
    "name" : "replset.minvalid", "options" : { "flags" : 1 }
},
{
    "name" : "startup_log", "options" : { "capped" : true, "size" : 10485760 }
},
{
    "name" : "system.indexes", "options" : { }
},
{
    "name" : "system.replset", "options" : { "flags" : 1 }
}
```

When returning this information as a cursor, a driver SHOULD use the method name `listCollections` or an idiomatic
variant.

Drivers MAY allow the `nameOnly` and `authorizedCollections` options to be passed when executing the `listCollections`
command for this method.

#### Returning a List of Collection Objects

Drivers MAY implement a method that returns a collection object for each returned collection, if the driver has such a
concept. This method MAY be named `listMongoCollections`.

Example return (in PHP, but abbreviated):

```javascript
array(6) {
  [0] => class MongoCollection#6 { }
  [1] => class MongoCollection#7 { }
  [2] => class MongoCollection#8 { }
  [3] => class MongoCollection#9 { }
  [4] => class MongoCollection#10 { }
  [5] => class MongoCollection#11 { }
}
```

Drivers MUST specify true for the `nameOnly` option when executing the `listCollections` command for this method, except
drivers MUST NOT set `nameOnly` if a filter specifies any keys other than `name`.

Drivers MAY allow the `authorizedCollections` option to be passed when executing the `listCollections` command for this
method

#### Replica Sets

- `listCollections` can be run on a secondary node.
- Querying `system.indexes` on a secondary node requires secondaryOk to be set.
- Drivers MUST run `listCollections` on the primary node when in a replica set topology, unless directly connected to a
  secondary node in Single topology.

## Test Plan

### Configurations

- standalone node
- replica set primary node
- replica set secondary node
- mongos node

### Preparation

For each of the configurations:

- Create a (new) database
- Create a collection and a capped collection
- Create an index on each of the two collections
- Insert at least one document in each of the two collections

### Tests

- Run the driver's method that returns a list of collection names (e.g. `listCollectionNames()`):
  - verify that *all* collection names are represented in the result
  - verify that there are no duplicate collection names
  - there are no returned collections that do not exist
  - there are no returned collections containing an '$'
- Run the driver's method that returns a list of collection names (e.g. `listCollectionNames()`), pass a filter of
  `{ 'options.capped': true }`, and:
  - verify that *only* names of capped collections are represented in the result
  - verify that there are no duplicate collection names
  - there are no returned collections that do not exist
  - there are no returned collections containing an '$'

## Backwards Compatibility

There should be no backwards compatibility concerns. This SPEC merely deals with how to enumerate collections in future
versions of MongoDB.

## Reference Implementation

The shell implements the first algorithm for falling back if the `listCollections` command does not exist
(<https://github.com/mongodb/mongo/blob/f32ba54f971c045fb589fe4c3a37da77dc486cee/src/mongo/shell/db.js#L550>).

## Changelog

- 2024-07-26: Migrated from reStructuredText to Markdown. Drop description of behavior for MongoDB 2.x servers.

- 2022-10-05: Remove spec front matter and reformat changelog.

- 2022-09-15: Clarify the behavior of `comment` on pre-4.4 servers.

- 2022-02-01: Add `comment` option to `listCollections` command.

- 2022-01-20: Require that timeouts be applied per the client-side operations\
  timeout spec.

- 2021-12-17: Support `authorizedCollections` option in `listCollections`\
  command.

- 2021-04-22: Update to use secondaryOk.

- 2020-03-18: MongoDB 4.4 no longer includes `ns` field in `idIndex` field\
  for `listCollections` responses.

- 2019-03-21: The method that returns a list of collection names should be named\
  `listCollectionNames`. The method that
  returns a list of collection objects may be named `listMongoCollections`.

- 2018-07-03: Clarify that `nameOnly` must not be used with filters other than\
  `name`.

- 2018-05-18: Support `nameOnly` option in `listCollections` command.

- 2017-09-27: Clarify reason for filtering collection names containing '$'.

- 2015-01-14: Clarify trimming of database name. Put preferred method name for\
  listing collections with a cursor as
  return value.

- 2014-12-18: Update with the server change to return a cursor for\
  `listCollections`.
