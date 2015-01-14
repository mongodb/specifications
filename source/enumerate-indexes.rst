.. role:: javascript(code)
  :language: javascript

===================
Enumerating Indexes
===================

:Spec: 106
:Spec-ticket: SPEC-53
:Title: Enumerating Indexes
:Authors: Derick Rethans
:Status: Draft
:Type: Standards
:Server Versions: 1.8-2.7.5, 2.8.0-rc3 and later
:Last Modified: January 15, 2015
:Version: 0.3

.. contents::

--------

Abstract
========

A driver can contain a feature to enumerate all indexes belonging to a
collection. This specification defines how indexes should be enumerated.

META
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

The driver needs to implement different methods of enumeration depending on
MongoDB server version. From MongoDB 2.7.6, the server implements a
``listIndexes`` command that MUST be used if available. For the non-MMAP
storage engines that come with 2.8, this will be the only way how their indexes
can be enumerated. For earlier MongoDB server versions, the driver SHOULD
simply query against the ``system.indexes`` collection of a database and only
include indexes for the collection that the method is called on (by specifying
``ns: 'dbname.collection'`` when querying against ``system.indexes``).


Pre MongoDB 2.7.6 versions
--------------------------

On MongoDB versions prior to 2.7.6, the only way to enumerate indexes for
a collection is by querying the ``system.indexes`` collection::

	$ use test
	$ db.system.indexes.find( { 'ns' : 'test.collectionName' } )

This query returns a list of documents which always include a ``v`` field, a
``key`` field, a ``name`` field and an ``ns`` field.

Each returned document describes one index::

	{
		"v" : 1,
		"key" : {
			"l" : "2dsphere"
		},
		"name" : "l_2dsphere",
		"ns" : "test.collectionName",
		"2dsphereIndexVersion" : 2
	}

MongoDB versions 2.7.6 to 2.8.0-rc2
-----------------------------------

MAY be supported, but this is not necessary. These versions allow the
``listIndexes`` command, but return results as a single document, but not
as a cursor. This spec does not cover these versions.


Post MongoDB 2.8.0-rc3 versions
-------------------------------

In versions 2.8.0-rc3 and later, the ``listIndexes`` command returns a
cursor::

	$ use test
	$ db.runCommand( { listIndexes: 'collectionName' } );

The value for the ``listIndexes`` is the collection name. Unlike pre-2.7.6
versions, this is *not* the full namespace name.

The command returns a cursor definition structure::

    {
        cursor: {
            id: <long>,
            ns: <string>,
            firstBatch: [<object>, <object>, ...]
        },
        ok: 1
    }

The ``cursor.firstBatch`` field contains an initial list of index information
structures, for example::

    {
        cursor: {
            id: <long>,
            ns: <string>,
            firstBatch: [
                {
                    "v" : 1,
                    "key" : {
                        "x" : 1
                    },
                    "name" : "x_1",
                    "ns" : "test.collectionName",
                },
                {
                    "v" : 1,
                    "key" : {
                        "l" : "2dsphere"
                    },
                    "name" : "l_2dsphere",
                    "ns" : "test.collectionName",
                    "2dsphereIndexVersion" : 2
                },
            ]
        },
        ok: 1
    }

With the ``cursor.id`` and ``cursor.ns`` fields you can retrieve further index
information structures.

The command also returns the field ``ok`` to
signal whether the command was executed successfully.

This will return the first 25 index descriptions as part of the returned
document::

    $ db.runCommand( { listIndexes: 'collectionName', cursor : { batchSize: 25 } } );

Return types
~~~~~~~~~~~~

For servers that support the ``listIndexes`` command, the return types
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

Drivers MAY expose methods to return index information structures as an array.
If your driver already has such a method, its return type MUST NOT be changed
in order to prevent breaking backwards compatibility.

Drivers SHOULD expose (a) method(s) to return index information through a
cursor, where the information for each index is represented by a single
document.


Enumeration: getting index information
--------------------------------------

With both the pre and post 2.7.6 versions having a different way to enumerate
indexes for a collection, drivers SHOULD implement their enumeration according to the
following algorithm (just like the
`shell does <https://github.com/mongodb/mongo/blob/f32ba54f971c045fb589fe4c3a37da77dc486cee/src/mongo/shell/collection.js#L942>`_)::

  run the listIndexes command while specifying the collection name
    if res.code == 59 || res.code == 13390:
      fall back to querying system.indexes.

    if res.code == 26
      return an empty array

    if !res.ok:
      if res.errmsg && res.errmsg.startsWith( "no such cmd" ):
        fall back to querying system.indexes.

      else:
        throw listIndexes command failed exception

    loop through res.cursor.firstBatch

    use getmore with res.cursor.id and res.cursor.ns information to loop over
    remaing results

If you need to fall back to querying ``system.indexes``, then you need 
specify the full namespaces name (``dbName.collectionName``) as query criterion.

Alternatively, and if a driver already implements checking MongoDB versions, a
driver MAY alternatively implement it as::

  if server version >= 2.7.6
    run the listIndexes command, with the given collection name
      if res.code == 26
        return an empty array

      if res.code == 59 || res.code == 13390:
        throw listIndexes command failed exception

      if res.errmsg && res.errmsg.startsWith( "no such cmd" ):
        throw listIndexes command failed exception

    loop through res.cursor.firstBatch

    use getmore with res.cursor.id and res.cursor.ns information to loop over
    remaing results

  else
    fall back to querying system.indexes, and return each returned document
    as an element

Driver methods
--------------

Drivers SHOULD use the method name ``listIndexes`` for a method that returns
all indexes with a cursor return type. Drivers MAY use an idiomatic variant
that fits the language the driver is for.

If a driver already has a method to perform one of the listed tasks, there is
no need to change a method name. Do not break backwards compatibility when
adding new methods.

All methods:

- MUST be on the collection object.
- MAY allow the ``cursor.firstBatch`` option to be passed.
- MUST use the *same* return type (ie, array or cursor) whether either a
  pre-2.7.6 server, a post-2.7.6 or a post-2.8.0-rc3 server is being used.
- MAY emulate returning a cursor for pre-2.8.0-rc3 servers.

Getting Index Names
~~~~~~~~~~~~~~~~~~~

Drivers MAY implement a method to enumerate all indexes, and return only
the index names. 

Example::

	> a = [];
	[ ]
	> db.runCommand( { listIndexes: 'poiConcat' } ).indexes.forEach(function(i) { a.push(i.name); } );
	> a
	[ "_id_", "ty_1", "l_2dsphere", "ts_1" ]

Getting Full Index Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers MAY implement a method to return the full index specifications that are
returned from both ``listIndexes`` (in the ``res.cursor.firstBatch`` field, and
subsequent retrieved documents through getmore on the cursor constructed from
``res.cursor.ns`` and ``res.cursor.id``), and the query result for
``system.indexes``.

The returned result for each variant MUST be equivalent, and each index
that is returned MUST use the field names ``v``, ``key``, ``name`` and ``ns``.
If the result contains additional fields, they MUST be included verbatim (like
``2dsphereIndexVersion`` in the example below).

Example return (a cursor which returns documents, not a simple array)::

    {
        "v" : 1,
        "key" : { "_id" : 1 },
        "name" : "_id_",
        "ns" : "demo.poiConcat"
    },
    {
        "v" : 1,
        "key" : { "ty" : NumberLong(1) },
        "name" : "ty_1",
        "ns" : "demo.poiConcat"
    },
    {
        "v" : 1,
        "key" : { "l" : "2dsphere" },
        "name" : "l_2dsphere",
        "ns" : "demo.poiConcat",
        "2dsphereIndexVersion" : 2
    },
    {
        "v" : 1,
        "key" : { "ts" : NumberLong(1) },
        "name" : "ts_1",
        "ns" : "demo.poiConcat"
    }

When returning this information as a cursor, a driver SHOULD use the
method name ``listIndexes`` or an idiomatic variant.

Replicasets
~~~~~~~~~~~

- ``listIndexes`` can be run on a secondary
- querying ``system.indexes`` on a secondary requires slaveOkay to be set.
- Drivers MUST run ``listIndexes`` on the primary node in "replicaset"
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
- Create a collection
- Create a single column index, a compound index, and a unique index
- Insert at least one document containing all the fields that the above
  indicated indexes act on

Tests
-----

- Run the driver's method that returns a list of index names, and:

  - verify that *all* index names are represented in the result
  - verify that there are no duplicate index names
  - there are no returned indexes that do not exist

- Run the driver's method that returns a list of index information records, and:

  - all the indexes are represented in the result
  - the "unique" flags show up for the unique index
  - there are no duplicates in the returned list


Backwards Compatibility
=======================

There should be no backwards compatibility concerns. This SPEC merely deals
with how to enumerate indexes in future versions of MongoDB.


Reference Implementation
========================

The shell implements the first algorithm for falling back if the
``listIndexes`` command does not exist
(`<https://github.com/mongodb/mongo/blob/f32ba54f971c045fb589fe4c3a37da77dc486cee/src/mongo/shell/collection.js#L942>`_).


Version History
===============

Version 0.3 Changes

    - Put preferred method name for listing indexes with a cursor as return
      value.

Version 0.2 Changes

    - Update with the server change to return a cursor for
      ``listIndexes``.

Version 0.1 Changes

    - Initial draft
