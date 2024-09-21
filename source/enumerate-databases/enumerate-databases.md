# Enumerating Databases

- Status: Accepted
- Minimum Server Version: 3.6

______________________________________________________________________

## Abstract

A driver can provide functionality to enumerate all databases on a server. This specification defines several methods
for enumerating databases.

## META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

### Terms

**MongoClient**

Driver object representing a connection to MongoDB. This is the root object of a driver's API and MAY be named
differently in some drivers.

**MongoDatabase**

Driver object representing a database and the operations that can be performed on it. MAY be named differently in some
drivers.

**Iterable**

An object or data structure that is a sequence of elements that can be iterated over. This spec is flexible on what that
means as different drivers will have different requirements, types, and idioms.

**Document**

An object or data structure used by the driver to represent a BSON document. This spec is flexible on what that means as
different drivers will have different requirements, types, and idioms.

### Naming Deviations

This specification defines names for methods. To the extent possible, drivers SHOULD use the defined names. However,
where a driver or language's naming conventions would conflict, drivers SHOULD honor their existing conventions. For
example, a driver may use `list_databases` instead of `listDatabases`.

### Filters

Drivers SHOULD support the `filter` option when implementing the
[listDatabases](https://www.mongodb.com/docs/manual/reference/command/listDatabases/) database command. The `filter`
option is a query predicate that determines which databases are listed in the command result. You can specify a
condition on any of the database fields returned in the command output:

- `name`
- `sizeOnDisk`
- `empty`
- `shards`

For example, to list only databases whose names begin with "foo":

```javascript
db.adminCommand({listDatabases: 1, filter: {name: /^foo/}});
```

### AuthorizedDatabases

MongoDB 4.0.5 added an `authorizedDatabases` boolean option to the
[listDatabases](https://www.mongodb.com/docs/manual/reference/command/listDatabases/) database command, which can be
used to limit the command result to only include databases the user is authorized to use. Drivers SHOULD support the new
`authorizedDatabases` option when implementing the
[listDatabases](https://www.mongodb.com/docs/manual/reference/command/listDatabases/) database command.

The possible values for `authorizedDatabases` are:

- unspecified (missing entirely from the command document sent to the server)
- `false`
- `true`

See the server's [listDatabases](https://www.mongodb.com/docs/manual/reference/command/listDatabases/) documentation for
an explanation of what each value means.

### Comment

MongoDB 4.4 introduced a `comment` option to the `listDatabases` command. This option enables users to specify a comment
as an arbitrary BSON type to help trace the operation through the database profiler, currentOp and logs. The default is
to not send a value. If a comment is provided on pre-4.4 servers, the comment should still be attached and the driver
should rely on the server to provide an error to the user.

```javascript
db.getSiblingDB("admin").runCommand({listDatabases: 1, comment: "hi there"})
```

### Driver Methods

If a driver already has a method to perform one of the listed tasks, there is no need to change it. Do not break
backwards compatibility when adding new methods.

All methods SHOULD be implemented on the MongoClient object.

All methods MUST apply timeouts per the
[Client Side Operations Timeout](../client-side-operations-timeout/client-side-operations-timeout.md) specification.

#### Enumerating Full Database Information

The [listDatabases](https://www.mongodb.com/docs/manual/reference/command/listDatabases/) database command returns an
array of documents, each of which contains information about a database on the MongoDB server. Additionally, the command
reports the aggregate sum of all database sizes (in bytes). Consider the following example:

```javascript
db.getSiblingDB("admin").runCommand({listDatabases:1})
    {
        "databases" : [
            {
                "name" : "admin",
                "sizeOnDisk" : 83886080,
                "empty" : false
            },
            {
                "name" : "local",
                "sizeOnDisk" : 83886080,
                "empty" : false
            }
        ],
        "totalSize" : 167772160,
        "ok" : 1
    }
```

Drivers SHOULD implement a MongoClient method that returns an Iterable of database specifications (e.g. model object,
document type), each of which correspond to an element in the databases array of the `listDatabases` command result.
This method SHOULD be named `listDatabases`.

Drivers MAY report `totalSize` (e.g. through an additional output variable on the `listDatabases` method), but this is
not necessary.

Drivers SHOULD support the `filter`, `authorizedDatabases` and `comment` options when implementing this method.

#### Enumerating Database Names

MongoDB 3.6 introduced a `nameOnly` boolean option to the `listDatabases` database command, which limits the command
result to only include database names. Consider the following example:

```
> db.getSiblingDB("admin").runCommand({listDatabases:1,nameOnly:true})
{
    "databases" : [
        { "name" : "admin" },
        { "name" : "local" }
    ],
    "ok" : 1
}
```

Drivers MAY implement a MongoClient method that returns an Iterable of strings, each of which corresponds to a name in
the databases array of the `listDatabases` command result. This method SHOULD be named `listDatabaseNames`.

Drivers SHOULD support the `filter`, `authorizedDatabases` and `comment` options when implementing this method.

#### Enumerating MongoDatabase Objects

Drivers MAY implement a MongoClient method that returns an Iterable of MongoDatabase types, each of which corresponds to
a name in the databases array of the `listDatabases` command result. This method MAY be named `listMongoDatabases`.

Any MongoDatabase objects returned by this method SHOULD inherit the same MongoClient options that would otherwise be
inherited by selecting an individual MongoDatabase through MongoClient (e.g. read preference, write concern).

Drivers SHOULD specify the `nameOnly` option when executing the `listDatabases` command for this method.

Drivers SHOULD support the `filter`, `authorizedDatabases` and `comment` options when implementing this method.

### Replica Sets

The `listDatabases` command may be run on a secondary node. Drivers MUST run the `listDatabases` command only on the
primary node in replica set topology, unless directly connected to a secondary node in Single topology.

## Test Plan

### Test Environments

The test plan should be executed against the following servers:

- Standalone
- Replica set primary
- Replica set secondary
- Sharding router (i.e. mongos)

### Test Cases

The following scenarios should be run for each test environment:

- Execute the method to enumerate full database information (e.g. `listDatabases()`)
  - Verify that the method returns an Iterable of Document types
  - Verify that all databases on the server are present in the result set
  - Verify that the result set does not contain duplicates
- Execute the method to enumerate database names (e.g. `listDatabaseNames()`)
  - Verify that the method returns an Iterable of strings
  - Verify that all databases on the server are present in the result set
  - Verify that the result set does not contain duplicates
- Execute the method to enumerate MongoDatabase objects (e.g. `listMongoDatabases()`)
  - Verify that the method returns an Iterable of MongoDatabase objects
  - Verify that all databases on the server are present in the result set
  - Verify that the result set does not contain duplicates

## Motivation for Change

Although most drivers provide a `listDatabases` command helper in their API, there was previously no spec for a database
enumeration. MongoDB 3.6 introduced a `nameOnly` option to the `listDatabases` database command. The driver API should
to be expanded to support this option.

## Design Rationale

The design of this specification is inspired by the
[Collection Enumeration](../enumerate-collections/enumerate-collections.md) and
[Index Management](../index-management/index-management.md) specifications. Since most drivers already implement a
`listDatabases` command helper in some fashion, this spec is flexible when it comes to existing APIs.

## Backwards Compatibility

There should be no backwards compatibility concerns. This specification merely deals with how to enumerate databases in
future versions of MongoDB and allows flexibility for existing driver APIs.

## Reference Implementation

TBD

## Q & A

### Why is reporting the total size of all databases optional?

Although the `listDatabases` command provides two results, a `databases` array and `totalSize` integer, the array of
database information documents is the primary result. Returning a tuple or composite result type from a `listDatabases`
driver method would complicate the general use case, as opposed to an optional output argument (if supported by the
language). Furthermore, the `totalSize` value can be calculated client-side by summing all `sizeOnDisk` fields in the
array of database information documents.

## Changelog

- 2024-07-26: Migrated from reStructuredText to Markdown. Removed note that applied to pre-3.6 servers.

- 2022-10-05: Remove spec front matter and reformat changelog. Also reverts the minimum server version to 3.6, which is
  where `nameOnly` and `filter` options were first introduced for `listDatabases`.

- 2022-08-17: Clarify the behavior of comment on pre-4.4 servers.

- 2022-02-01: Support comment option in listDatabases command

- 2022-01-19: Require that timeouts be applied per the client-side operations timeout spec.

- 2019-11-20: Support authorizedDatabases option in listDatabases command

- 2017-10-30: Support filter option in listDatabases command
