.. role:: javascript(code)
  :language: javascript

================
Index Management
================

:Spec: 79
:Title: Index Management
:Authors: Durran Jordan
:Status: Approved
:Type: Standards
:Minimum Server Version: 2.4
:Last Modified: Oct 11, 2016
:Version: 1.5

.. contents::

--------

Specification
=============

The index management spec defines a set of behaviour in the drivers for creating, removing and viewing indexes in a collection. It defines implementation details when required but also provides flexibilty in the driver in that one or both of 2 unique APIs can be chosen to be implemented.


-----------
Definitions
-----------

META
----

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.


Terms
-----

Collection
  The term ``Collection`` references the object in the driver that represents a collection on the server.

Cursor
  The term ``Cursor`` references the driver's cursor object.

Iterable
  The term ``Iterable`` is to describe an object that is a sequence of elements that can be iterated over.

Document
  The term ``Document`` refers to the implementation in the driver's language of a BSON document.

Result
  The term ``Result`` references the object that is normally returned by the driver as the result of a command execution. In the case of situations where an actual command is not executed, rather an insert or a query, an object that adheres to the same interface must be returned with as much information as possible that could be obtained from the operation.

--------
Guidance
--------

Documentation
-------------

The documentation provided in code below is merely for driver authors and SHOULD NOT be taken as required documentation for the driver.


Operations
----------

All drivers MUST offer at least one of the sections of operations, the Standard API or the Index View API. The driver MAY elect to have both. Implementation details are noted in the comments when a specific implementation is required. Within each API, all methods are REQUIRED unless noted otherwise in the comments.


Operation Parameters
--------------------

All drivers MUST include the specified parameters in each operation, with the exception of the options parameter which is OPTIONAL. As of 3.4 (see https://jira.mongodb.org/browse/SERVER-769) the server validates options passed to the createIndexes command -- drivers should be aware when testing that passing arbitrary options when the driver does not validate them could fail on the server.

Naming
------

All drivers MUST name operations and parameters as defined in the following sections. Exceptions to this rule are noted in the appropriate section. Class and interface names may vary according to the driver and language best practices.

Deviations
**********

Acceptable naming deviations should fall within the basic style of the language. For example, ``createIndex`` would be a required name in Java, where camel-case method names are used, but in Ruby ``create_index`` would be acceptable.


Index Name Generation
---------------------

When the client generates a name for an index based on the keys, The driver MUST generate the name as key-direction pairs, separated by underscores. For example, the key ``{ name: 1, dob: -1 }`` MUST generate an index name of ``name_1_dob_-1``.

Note there is one exception to this rule on the ``_id`` field. The server uses an index name with no direction, ``_id_``, which cannot be overridden.

------------
Standard API
------------

.. code:: typescript

  interface Collection {

    /**
     * This is a convenience method for creating a single index. This MUST call the
     * createIndexes method and pass the provided specification document in a
     * sequence to that method with the same options.
     *
     * @return The name of the created index.
     *
     * @note Drivers MAY opt to implement this method signature, the signature that
     *   takes an IndexModel as a parameter, or for those languages with method
     *   overloading MAY decide to implement both.
     */
    createIndex(keys: Document, options: IndexOptions): String;

    /**
     * @see Comments above.
     */
    createIndex(model: IndexModel): String

    /**
     * Creates multiple indexes in the collection.
     *
     * For MongoDB 2.6 and higher this method MUST execute a createIndexes command.
     *
     * For MongoDB 2.4 this method MUST insert the index specifications directly into
     * the system.indexes collection. The write concern provided provided to the server
     * MUST be { w: 1 }.
     *
     * The driver MAY choose NOT to support creating indexes on 2.4 and if so, MUST
     * document the method as such.
     *
     * Note that in MongoDB server versions >= 3.0.0, the server will create the
     * indexes in parallel.
     *
     * As of 3.4 (see https://jira.mongodb.org/browse/SERVER-769) the server validates
     * options passed to the createIndexes command.
     *
     * @return The names of all the indexes that were created.
     */
    createIndexes(models: Iterable<IndexModel>): Iterable<String>;

    /**
     * Drops a single index from the collection by the index name.
     *
     * In all server versions this MUST execute a dropIndexes command.
     *
     * @note If the string passed is '*', the driver MUST raise an error since
     *   more than one index would be dropped.
     */
    dropIndex(name: String): Result;

    /**
     * Attempts to drop a single index from the collection given the keys and options.
     *
     * In all server versions this MUST execute a dropIndexes command.
     *
     * This is OPTIONAL until partial indexes are implemented.
     *
     * @note Drivers MAY opt to implement this method signature, the signature that
     *   takes an IndexModel as a parameter, or for those languages with method
     *   overloading MAY decide to implement both.
     */
    dropIndex(keys: Document, options: IndexOptions): Result;

    /**
     * @see Comments above.
     */
    dropIndex(model: IndexModel): Result;

    /**
     * Drops all indexes in the collection.
     */
    dropIndexes(): Result;

    /**
     * Gets index information for all indexes in the collection. This should be
     * implemented as specified in the Enumerate Indexes specification:
     *
     * @see https://github.com/mongodb/specifications/blob/master/source/enumerate-indexes.rst
     *
     * @note Where the enumerate indexes spec gives the option of returning a
     *   Cursor or Array for backwards compatibility - here the driver MUST always
     *   return a Cursor.
     */
    listIndexes(): Cursor;
  }


Examples
--------

Create an index in a collection.

Ruby:

.. code:: ruby

  collection.create_index({ name: 1 }, { unique: true })

Java:

.. code:: java

  collection.createIndex(new Document("name", 1), new IndexOptions().unique(true));

Produces the shell equivalent (>= 2.6.0) of:

.. code:: javascript

  db.runCommand({
    createIndexes: "users",
    indexes: [
      { key: { name: 1 }, name: "name_1", unique: true }
    ]
  });

Create multiple indexes in a collection.

Ruby:

.. code:: ruby

  collection.create_indexes([
    { key: { name: 1 }, unique: true },
    { key: { age: -1 }, name: "age" }
  ])

Java:

.. code:: java

  collection.createIndexes(asList(
    new IndexModel(new Document("name", 1), new IndexOptions().unique(true)),
    new IndexModel(new Document("age", -1), new IndexOptions().name("age"))
  ));

Produces the shell equivalent (>= 2.6.0) of:

.. code:: javascript

  db.runCommand({
    createIndexes: "users",
    indexes: [
      { key: { name: 1 }, name: "name_1", unique: true },
      { key: { age: -1 }, name: "age" }
    ]
  });

Drop an index in a collection.

Ruby:

.. code:: ruby

  collection.drop_index("age")

Java:

.. code:: java

  collection.dropIndex("age");

Produces the shell equivalent of:

.. code:: javascript

  db.runCommand({ dropIndexes: "users", index: "age" });

Drop all indexes in a collection.

Ruby:

.. code:: ruby

  collection.drop_indexes

Java:

.. code:: java

  collection.dropIndexes();

Produces the shell equivalent of:

.. code:: javascript

  db.runCommand({ dropIndexes: "users", index: "*" });

List all indexes in a collection.

Ruby:

.. code:: ruby

  collection.list_indexes

Java:

.. code:: java

  collection.listIndexes();

Produces the shell equivalent (>= 3.0.0) of:

.. code:: javascript

  db.runCommand({ listIndexes: "users" });

--------------
Index View API
--------------

.. code:: typescript

  interface Collection {

    /**
     * Returns the index view for this collection.
     */
    indexes(): IndexView;
  }

  interface IndexView extends Iterable<Document> {

    /**
     * Enumerates the index information for all indexes in the collection. This should be
     * implemented as specified in the Enumerate Indexes specification, although the naming
     * requirement is dropped in favor of the driver language standard for handling iteration
     * over a sequence of objects.
     *
     * @see https://github.com/mongodb/specifications/blob/master/source/enumerate-indexes.rst
     *
     * @note For drivers that cannot make the IndexView iterable, they MUST implement a list
     *   method. See below.
     */
    iterator(): Iterator<Document>;

    /**
     * For drivers that cannot make IndexView iterable, they MUST implement this method to
     * return a list of indexes. In the case of async drivers, this MAY return a Future<Cursor>
     *  or language/implementation equivalent.
     *
     * @note Where the enumerate indexes spec gives the option of returning a
     *   Cursor or Array for backwards compatibility - here the driver MUST always
     *   return a Cursor.
     */
    list(): Cursor;

    /**
     * This is a convenience method for creating a single index. This MUST call the
     * createMany method and pass the provided specification document in a
     * sequence to that method with the same options.
     *
     * @return The name of the created index.
     *
     * @note Drivers MAY opt to implement this method signature, the signature that
     *   takes an IndexModel as a parameter, or for those languages with method
     *   overloading MAY decide to implement both.
     */
    createOne(keys: Document, options: IndexOptions): String;

    /**
     * @see Comments above.
     */
    createOne(model: IndexModel): String

    /**
     * Creates multiple indexes in the collection.
     *
     * For MongoDB 2.6 and higher this method MUST execute a createIndexes command.
     *
     * For MongoDB 2.4 this method MUST insert the index specifications directly into
     * the system.indexes collection. The write concern provided provided to the server
     * MUST be { w: 1 }.
     *
     * The driver MAY choose NOT to support creating indexes on 2.4 and if so, MUST
     * document the method as such.
     *
     * @return The names of the created indexes.
     *
     * @note Each specification document becomes the "key" field in the document that
     *   is inserted or the command.
     *
     * Note that in MongoDB server versions >= 3.0.0, the server will create the
     * indexes in parallel.
     */
    createMany(models: Iterable<IndexModel>): Iterable<String>;

    /**
     * Drops a single index from the collection by the index name.
     *
     * In all server versions this MUST execute a dropIndexes command.
     *
     * @note If the string passed is '*', the driver MUST raise an error since
     *   more than one index would be dropped.
     */
    dropOne(name: String): Result;

    /**
     * Attempts to drop a single index from the collection given the keys and options.
     * This is OPTIONAL until partial indexes are implemented.
     *
     * In all server versions this MUST execute a dropIndexes command.
     *
     * @note Drivers MAY opt to implement this method signature, the signature that
     *   takes an IndexModel as a parameter, or for those languages with method
     *   overloading MAY decide to implement both.
     */
    dropOne(keys: Document, options: IndexOptions): Result;

    /**
     * @see Comments above.
     */
    dropOne(model: IndexModel): Result;

    /**
     * Drops all indexes in the collection.
     */
    dropAll(): Result;
  }


Examples
--------

Create an index in a collection.

Ruby:

.. code:: ruby

  collection.indexes.create_one({ name: 1 }, { unique: true })

Java:

.. code:: java

  collection.indexes().createOne(new Document("name", 1), new IndexOptions().unique(true));

Produces the shell equivalent (>= 2.6.0) of:

.. code:: javascript

  db.runCommand({
    createIndexes: "users",
    indexes: [
      { key: { name: 1 }, name: "name_1", unique: true }
    ]
  });

Create multiple indexes in a collection.

Ruby:

.. code:: ruby

  collection.indexes.create_many([
    { key: { name: 1 }, unique: true },
    { key: { age: -1 }, name: "age" }
  ])

Java:

.. code:: java

  collection.indexes().createMany(asList(
    new IndexModel(new Document("name", 1), new IndexOptions().unique(true),
    new IndexModel(new Document("age", -1), new IndexOptions().name("age")
  ));

Produces the shell equivalent (>= 2.6.0) of:

.. code:: javascript

  db.runCommand({
    createIndexes: "users",
    indexes: [
      { key: { name: 1 }, name: "name_1", unique: true },
      { key: { age: -1 }, name: "age" }
    ]
  });

Drop an index in a collection.

Ruby:

.. code:: ruby

  collection.indexes.drop_one("age")

Java:

.. code:: java

  collection.indexes().dropOne("age");

Produces the shell equivalent of:

.. code:: javascript

  db.runCommand({ dropIndexes: "users", index: "age" });

Drop all indexes in a collection.

Ruby:

.. code:: ruby

  collection.indexes.drop_all

Java:

.. code:: java

  collection.indexes().dropAll();

Produces the shell equivalent of:

.. code:: javascript

  db.runCommand({ dropIndexes: "users", index: "*" });

List all indexes in a collection.

Ruby:

.. code:: ruby

  collection.indexes.each do |document|
    p document
  end

Java:

.. code:: java

  for (BsonDocument document: collection.indexes()) {
    /* ... */
  }

Produces the shell equivalent (>= 3.0.0) of:

.. code:: javascript

  var indexes = db.runCommand({ listIndexes: "users" });
  for (index in indexes) {
    console.log(index);
  }


---------------------
Common API Components
---------------------

.. code:: typescript

  interface IndexModel {

    /**
     * Contains the required keys for the index.
     */
    keys: Document;

    /**
     * Contains the options for the index.
     */
    options: IndexOptions;
  }

  interface IndexOptions {

    /**
     * Optionally tells the server to build the index in the background and not block
     * other tasks.
     */
    background: Boolean;

    /**
     * Optionally specifies the length in time, in seconds, for documents to remain in
     * a collection.
     */
    expireAfter: Int32;

    /**
     * Optionally specify a specific name for the index outside of the default generated
     * name. If none is provided then the name is generated in the format "[field]_[direction]".
     *
     * Note that if an index is created for the same key pattern with different collations,
     * a name must be provided by the user to avoid ambiguity.
     *
     * @example For an index of name: 1, age: -1, the generated name would be "name_1_age_-1".
     */
    name: String;

    /**
     * Optionally tells the index to only reference documents with the specified field in
     * the index.
     */
    sparse: Boolean;

    /**
     * Optionally used only in MongoDB 3.0.0 and higher. Specifies the storage engine
     * to store the index in.
     */
    storageEngine: String;

    /**
     * Optionally forces the index to be unique.
     */
    unique: Boolean;

    /**
     * Optionally specifies the index version number, either 0 or 1.
     */
    version: Int32;

    /**
     * Optionally specifies the default language for text indexes.
     * Is english if none is provided.
     */
    defaultLanguage: String;

    /**
     * Optionally Specifies the field in the document to override the language.
     */
    languageOverride: String;

    /**
     * Optionally provides the text index version number.
     *
     * MongoDB 2.4 can only support version 1.
     *
     * MongoDB 2.6 and higher may support version 1 or 2.
     */
    textVersion: Int32;

    /**
     * Optionally specifies fields in the index and their corresponding weight values.
     */
    weights: Document;

    /**
     * Optionally specifies the 2dsphere index version number.
     *
     * MongoDB 2.4 can only support version 1.
     *
     * MongoDB 2.6 and higher may support version 1 or 2.
     */
    sphereVersion: Int32;

    /**
     * Optionally specifies the precision of the stored geo hash in the 2d index, from 1 to 32.
     */
    bits: Int32;

    /**
     * Optionally sets the maximum boundary for latitude and longitude in the 2d index.
     */
    max: Double;

    /**
     * Optionally sets the minimum boundary for latitude and longitude in the index in a
     * 2d index.
     */
    min: Double;

    /**
     * Optionally specifies the number of units within which to group the location values
     * in a geo haystack index.
     */
    bucketSize: Int32;

    /**
     * Optionally specifies a filter for use in a partial index. Only documents that match the
     * filter expression are included in the index.
     */
    partialFilterExpression: Document;

    /**
     * Optionally specifies a collation to use for the index in MongoDB 3.4 and higher.
     * If not specified, no collation is sent and the default collation of the collection
     * server-side is used.
     */
    collation: Document;
  }


----------------------
Backwards Compatibilty
----------------------

This specification makes no attempts to be backwards compatible as the target drivers to implement this spec are all next generation.


---------
Q & A
---------

Q: Where is write concern?
  The createIndexes and dropIndexes commands take a write concern that indicates how the write is acknowledged. Since all operations defined in this specification are performed on a collection, it's uncommon that two different index operations on the same collection would use a different write concern. As such, the most natural place to indicate write concern is on the client, the database, or the collection itself and not the operations within it.

  However, it might be that a driver needs to expose write concern to a user per operation for various reasons. It is permitted to allow a write concern option, but the driver may need to provide a separate parameter for some helpers, since the writeConcern is a top-level command option, not part of an indexModel's indexOptions. For example, whereas the write concern could possibly be included in the indexOptions parameter for createIndex() and extracted in the method implementation, it would be ambiguous to specify write concern for one or more models passed to createIndexes(). The driver would therefore most likely choose to allow the option as a separate parameter for createIndexes().

Q: Do the index operations support maxTimeMS?
  The listIndexes(), createIndexes() and dropIndexes() commands allow the maxTimeMS option, though supporting it as an option is not addressed by this specification. As is discussed above for write concern, the driver may choose to expose this top-level command option; however, for some helpers, the driver may need a separate command options parameter. For other helpers, it may choose to extract maxTimeMS from the indexOptions.

Changelog
---------

17 SEP 2015:
  - Added ``partialFilterExpression`` attribute to ``IndexOptions`` in order to support partial indexes.
  - Fixed "provides" typo.
19 MAY 2016:
  - Added ``collation`` attribute to ``IndexOptions`` in order to support setting a collation on an index.
8 AUG 2016:
  - Fixed ``collation`` language to not mention a collection default.
11 OCT 2016:
  - Added note on 3.4 servers validation options passed to ``createIndexes``.
11 OCT 2016:
  - Add note on server generated name for the _id index.
31 MAY 2017:
  - Add Q & A addressing write concern and maxTimeMS option.
7 JUN 2017:
  - Include listIndexes() in Q&A about maxTimeMS.
