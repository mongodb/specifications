=====================
Enumerating Databases
=====================

:Spec Title: Enumerating Databases
:Spec Version: 1.0
:Author: Jeremy Mikola
:Status: Draft
:Type: Standards
:Minimum Server Version: 3.6
:Last Modified: 2017-08-28

.. contents::

--------

Abstract
========

A driver can provide functionality to enumerate all databases on a server. This
specification defines several methods for enumerating databases.

META
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

Terms
-----

MongoClient
   Driver object representing a connection to MongoDB. This is the root object
   of a driver’s API and MAY be named differently in some drivers.

MongoDatabase
   Driver object representing a database and the operations that can be
   performed on it. MAY be named differently in some drivers.

Iterable
   An object or data structure that is a sequence of elements that can be
   iterated over. This spec is flexible on what that means as different drivers
   will have different requirements, types, and idioms.

Document
   An object or data structure used by the driver to represent a BSON document.
   This spec is flexible on what that means as different drivers will have
   different requirements, types, and idioms.

Naming Deviations
-----------------

This specification defines names for methods. To the extent possible, drivers
SHOULD use the defined names. However, where a driver or language’s naming
conventions would conflict, drivers SHOULD honor their existing conventions. For
example, a driver may use ``list_databases`` instead of ``listDatabases``.

Driver Methods
--------------

If a driver already has a method to perform one of the listed tasks, there is no
need to change it. Do not break backwards compatibility when adding new methods.

All methods SHOULD be implemented on the MongoClient object.

Enumerating Full Database Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `listDatabases`_ database command returns an array of documents, each of
which contains information about a database on the MongoDB server. Additionally,
the command reports the aggregate sum of all database sizes (in bytes). Consider
the following example:

.. _listDatabases: https://docs.mongodb.com/manual/reference/command/listDatabases/

::

  > db.getSiblingDB("admin").runCommand({listDatabases:1})
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

Drivers SHOULD implement a MongoClient method that returns an Iterable of
database specifications (e.g. model object, document type), each of which
correspond to an element in the databases array of the ``listDatabases`` command
result. This method SHOULD be named ``listDatabases``.

Drivers MAY report ``totalSize`` (e.g. through an additional output variable on
the ``listDatabases`` method), but this is not necessary.

Enumerating Database Names
~~~~~~~~~~~~~~~~~~~~~~~~~~

MongoDB 3.6 introduced a ``nameOnly`` boolean option to the ``listDatabases``
database command, which limits the command result to only include database
names. Consider the following example:

::

  > db.getSiblingDB("admin").runCommand({listDatabases:1,nameOnly:true})
  {
      "databases" : [
          { "name" : "admin" },
          { "name" : "local" }
      ],
      "ok" : 1
  }

Drivers MAY implement a MongoClient method that returns an Iterable of strings,
each of which corresponds to a name in the databases array of the
``listDatabases`` command result. This method SHOULD be named
``listDatabaseNames``.

Older versions of the server that do not support the ``nameOnly`` option for the
``listDatabases`` command will ignore it without raising an error. Therefore,
drivers SHOULD always specify the ``nameOnly`` option when they only intend to
access database names from the ``listDatabases`` command result.

Enumerating MongoDatabase Objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers MAY implement a MongoClient method that returns an Iterable of
MongoDatabase types, each of which corresponds to a name in the databases array
of the ``listDatabases`` command result. This method MAY be named
``listMongoDatabases``.

Any MongoDatabase objects returned by this method SHOULD inherit the same
MongoClient options that would otherwise be inherited by selecting an individual
MongoDatabase through MongoClient (e.g. read preference, write concern).

Drivers SHOULD specify the ``nameOnly`` option when executing the
``listDatabases`` command for this method.

Replica Sets
------------

The ``listDatabases`` command may be run on a secondary. Drivers MUST run the
``listDatabases`` command only on the primary node in “replicaset” mode, unless
directly connected to a secondary node in “standalone” mode.

Test Plan
=========

Test Environments
-----------------

The test plan should be executed against the following servers:

* Standalone
* Replica set primary
* Replica set secondary
* Sharding router (i.e. mongos)

Test Cases
----------

The following scenarios should be run for each test environment:

* Execute the method to enumerate full database information (e.g.
  ``listDatabases()``)
  - Verify that the method returns an Iterable of Document types
  - Verify that all databases on the server are present in the result set
  - Verify that the result set does not contain duplicates
* Execute the method to enumerate database names (e.g. ``listDatabaseNames()``)
  - Verify that the method returns an Iterable of strings
  - Verify that all databases on the server are present in the result set
  - Verify that the result set does not contain duplicates
* Execute the method to enumerate MongoDatabase objects (e.g.
  ``listMongoDatabases()``)
  - Verify that the method returns an Iterable of MongoDatabase objects
  - Verify that all databases on the server are present in the result set
  - Verify that the result set does not contain duplicates

Motivation for Change
=====================

Although most drivers provide a ``listDatabases`` command helper in their API,
there was previously no spec for a database enumeration. MongoDB 3.6 introduced
a ``nameOnly`` option to the ``listDatabases`` database command. The driver API
should to be expanded to support this option.

Design Rationale
================

The design of this specification is inspired by the `Collection Enumeration`_
and `Index Enumeration`_ specifications. Since most drivers already implement a
``listDatabases`` command helper in some fashion, this spec is flexible when it
comes to existing APIs.

.. _Collection Enumeration: ./enumerate-collections.rst
.. _Index Enumeration: ./enumerate-indexes.rst

Backwards Compatibility
=======================

There should be no backwards compatibility concerns. This specification merely
deals with how to enumerate databases in future versions of MongoDB and allows
flexibility for existing driver APIs.

Reference Implementation
========================

TBD

Q & A
=====

Why is reporting the total size of all databases optional?
----------------------------------------------------------

Although the ``listDatabases`` command provides two results, a ``databases``
array and ``totalSize`` integer, the array of database information documents is
the primary result. Returning a tuple or composite result type from a
``listDatabases`` driver method would complicate the general use case, as
opposed to an optional output argument (if supported by the language).
Furthermore, the ``totalSize`` value can be calculated client-side by summing
all ``sizeOnDisk`` fields in the array of database information documents.

Changes
=======

Nothing yet.
