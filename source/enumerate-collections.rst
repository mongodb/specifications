.. role:: javascript(code)
  :language: javascript

=======================
Enumerating Collections
=======================

:Spec: SPEC-54
:Title: Enumerating Collections
:Authors: Derick Rethans
:Status: Draft
:Type: Standards
:Server Versions: 1.8-2.7.5, 2.8.0-rc3 and later
:Last Modified: December 12, 2014
:Version: 0.2

.. contents::

--------

Abstract
========

A driver can contain a feature to enumerate all collections belonging to a
database. This specification defines how collections should be enumerated.

META
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

The driver needs to implement different methods of enumeration depending on
MongoDB server version. From MongoDB 2.7.6, the server implements a
``listCollections`` command that MUST be used if available. For the non-MMAP
storage engines that come with 2.8, this will be the only way how their
collections can be enumerated. For earlier MongoDB server versions, the driver
SHOULD simply query against the ``systems.namespaces`` collection.


Pre MongoDB 2.7.6 versions
--------------------------

On MongoDB versions prior to 2.7.6, the only way to enumerate collections for
a database is by querying the ``system.namespaces`` collection::

    db.system.namespaces.find()

This query returns a list of documents through a normal query cursor, which
always include a ``name`` field and optionally a ``options`` field.

Each document describes a name space. Among collections, these name spaces
also include special collections (containing ``.system.`` or ``.oplog.`` in the
name). The returned documents also include indexes (containing a ``$`` in the
name). Index names MUST NOT be returned while enumerating collections through
``db.system.namespaces.find()``.

MongoDB versions 2.7.6 to 2.8.0-rc2
-----------------------------------

MAY be supported, but this is not necessary. These versions allow the
``listCollections`` command, but return results as a single document, but not
as a cursor. This spec does not cover these versions.

Post MongoDB 2.8.0-rc3 versions
-------------------------------

In versions 2.8.0-rc3 and later, the ``listCollections`` command returns a
cursor::

    $ use test
    $ db.runCommand( { listCollections: 1 } );

The command also accepts options.

The ``filter`` option, which acts like a query against the returned collection
documents. You can i.e. use the following to only list the collections
beginning with ``test``::

    $ db.runCommand( { listCollections: 1, filter: { name: /^test/ } } );

Or to find all capped collections::

    $ db.runCommand( { listCollections: 1, filter: { 'options.capped': true } } );

The ``cursor.batchSize`` option, which allows you to set how many initial
collections should be returned as part of the cursor specification document
that comes back from the server. This first batch is part of the returned
structure in the ``firstBatch`` key (see more about return types further on).

The command returns a cursor definition structure::

    {
        cursor: {
            id: <long>,
            ns: <string>,
            firstBatch: [<object>, <object>, ...]
        },
        ok: 1
    }

With the ``cursor.id`` and ``cursor.ns`` fields you can retrieve further index
information structures.

The command also returns the field ``ok`` to
signal whether the command was executed successfully.

This will return the first 25 collection descriptions as part of the returned
document::

    $ db.runCommand( { listCollections: 1, cursor : { batchSize: 25 } } );


Filters
-------

Pre MongoDB 2.7.6 servers, which require querying ``system.namespaces``,
return the name of a collection prefixed with the database name.

Post MongoDB 2.7.6 servers, which have ``listCollections`` implemented,
return the name of a collection **without** the database name prefixed to it.

Because of this, drivers MUST prefix filters against the ``name`` field with
the database name for pre MongoDB 2.7.6 servers. Because prefixing causes
issues with regular expressions, a driver MUST NOT allow a regular expression
as the match value for the ``name`` field in the filter for pre MongoDB
2.7.6 drivers.

For example, to list all collections with a "listCollections" method, you
would do the following with the ``filter`` argument::

  if filter.name is set:
    if server version < 2.7.6
      if typeof filter.name != string

        throw "value type not accepted" (as it needs to be a static string)

      else
        filter.name = "dbname." + filter.name

Filtering against the ``options`` field of a collection has no
restrictions.

Return types
~~~~~~~~~~~~

For servers that support the ``listCollections`` command, the return types
differ depending on server version. Versions 2.7.6 to 2.8.0-rc2 return a single
document containing all the results, but versions 2.8.0-rc3 and later return a
cursor description. As per the draft specification__, the format that is
returned is the same as for any other command cursor::

    {
        cursor: {
            id: <long>,
            ns: <string>,
            firstBatch: [<object>, <object>, ...]
        },
        ok: 1
    }

The number of objects in the ``firstBatch`` field depends on the
``cursor.batchSize`` option.

__ https://docs.google.com/a/10gen.com/document/d/1u6UuUvInvnHeAAeVNfTDBD6rtn_lkb0kCDn6ejK6hDk/edit

Drivers MAY expose methods to return collection names as an array. If your
driver already has such a method, its return type MUST NOT be changed in order
to prevent breaking backwards compatibility.

Drivers SHOULD expose (a) method(s) to return collection information through a
cursor, where the information for each collection is represented by a single
document.


Enumeration: getting collection names
-------------------------------------

With both the pre and post 2.7.6 versions having a different way to enumerate
all collections, drivers SHOULD implement their enumeration according to the
following algorithm (just like the
`shell does <https://github.com/mongodb/mongo/blob/f32ba54f971c045fb589fe4c3a37da77dc486cee/src/mongo/shell/db.js#L550>`_)::

  run the listCollections command, with the filter if given
    if res.code == 59 || res.code == 13390:
      fall back to querying system.namespaces.

    if !res.ok:
      if res.errmsg && res.errmsg.startsWith( "no such cmd" ):
        fall back to querying system.namespaces.

      else:
        throw listCollections command failed exception

    loop through res.cursor.firstBatch

    use getmore with res.cursor.id and res.cursor.ns information to loop over
    remaing results

If you need to fall back to querying ``system.namespaces``, then you need to
filter out all return documents that contain a ``$`` in the ``name`` field.

*Note:* Still trying to find out why there is an exception for ``".oplog.$"``
in there.

Alternatively, and if a driver already implements checking MongoDB versions, a
driver MAY alternatively implement it as::

  if server version >= 2.7.6
    run the listCollections command, with the filter if given
      if res.code == 59 || res.code == 13390:
        throw listCollections command failed exception

      if res.errmsg && res.errmsg.startsWith( "no such cmd" ):
        throw listCollections command failed exception

    loop through res.cursor.firstBatch

    use getmore with res.cursor.id and res.cursor.ns information to loop over
    remaing results

  else
    fall back to querying system.namespaces.

Driver methods
--------------

Method names are suggestions. If a driver already has a method to perform the
specific task, there is no need to change it; otherwise, use an idiomatic
variant that fits the language the driver is for.

All methods:

- SHOULD be on the database object.
- MUST allow a filter to be passed to include only requested collections.
- MAY allow the ``cursor.firstBatch`` option to be passed.
- MUST use the *same* return type (ie, array or cursor) whether either a
  pre-2.7.6 server, a post-2.7.6 or a post-2.8.0-rc3 server is being used.

getCollectionNames
~~~~~~~~~~~~~~~~~~

Drivers MAY implement a method to enumerate all collections, and return only
the collection names.

Example return::

    [
        "me",
        "oplog.rs",
        "replset.minvalid",
        "startup_log",
        "system.indexes",
        "system.replset"
    ]

getCollectionInfo
~~~~~~~~~~~~~~~~~

Drivers MAY implement a method to return the full ``name/options`` pairs that
are returned from both ``listCollections`` (in the ``res.cursor.firstBatch``
field, and subsequent retrieved documents through getmore on the cursor
constructed from ``res.cursor.ns`` and ``res.cursor.id``), and the query
result for ``system.namespaces``.

The returned result for each variant MUST be equivalent, and each collection
that is returned MUST use the field names ``name`` and ``options``.

Example return (a cursor which returns documents, not a simple array)::

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


listCollections
~~~~~~~~~~~~~~~

Drivers MAY implement a method that returns a collection object for each
returned collection, if the driver has such a concept. 

Example return (in PHP, but abbreviated)::

    array(6) {
      [0] => class MongoCollection#6 { }
      [1] => class MongoCollection#7 { }
      [2] => class MongoCollection#8 { }
      [3] => class MongoCollection#9 { }
      [4] => class MongoCollection#10 { }
      [5] => class MongoCollection#11 { }
    }

Replicasets
~~~~~~~~~~~

- ``listCollections`` can be run on a secondary
- querying ``system.namespaces`` on a secondary requires slaveOkay to be set.
- Drivers MUST run ``listCollections`` on the primary node in "replicaset"
  mode, unless directly connected to a secondary node in "standalone" mode.


Test Plan
=========

Configurations
--------------

- standalone node
- replica set primary node
- replica set secondary node
- mongos node

Preparation
-----------

For each of the configurations:

- Create a (new) database
- Create a collection and a capped collection
- Create an index on each of the two collections
- Insert at least one document in each of the two collections

Tests
-----

- Run the driver's method that returns a list of collection names, and:

  - verify that *all* collection names are represented in the result
  - verify that there are no duplicate collection names
  - there are no returned collections that do not exist
  - there are no returned collections containing an '$'

- Run the driver's method that returns a list of collection names, pass a
  filter of ``{ 'options.capped': true }``, and:

  - verify that *only* names of capped collections are represented in the result
  - verify that there are no duplicate collection names
  - there are no returned collections that do not exist
  - there are no returned collections containing an '$'


Backwards Compatibility
=======================

There should be no backwards compatibility concerns. This SPEC merely deals
with how to enumerate collections in future versions of MongoDB.


Reference Implementation
========================

The shell implements the first algorithm for falling back if the
``listCollections`` command does not exist
(`<https://github.com/mongodb/mongo/blob/f32ba54f971c045fb589fe4c3a37da77dc486cee/src/mongo/shell/db.js#L550>`_).


Version History
===============

Version 0.2 Changes

    - Update with the server change to return a cursor for
      ``listCollections``.

Version 0.1 Changes

    - Initial draft
