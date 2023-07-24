.. role:: javascript(code)
  :language: javascript

================
Index Management
================

:Status: Accepted
:Minimum Server Version: 3.6

.. contents::

--------

Specification
=============

The index management spec defines a set of behaviour in the drivers for creating, removing and viewing indexes in a collection. It defines implementation details when required but also provides flexibility in the driver in that one or both of 2 unique APIs can be chosen to be implemented.


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

All drivers MUST include the specified parameters in each operation. This does not preclude a driver from offering more. A driver SHOULD NOT require a user to specify the options parameter if they wish to use the server defaults.

As of 3.4 (see https://jira.mongodb.org/browse/SERVER-769) the server validates options passed to the ``createIndexes`` command -- drivers should be aware when testing that passing arbitrary options when the driver does not validate them could fail on the server.

Deviations
----------

A non-exhaustive list of acceptable deviations are as follows:

* Using named parameters in place of an options hash or class. For instance, ``collection.create_index({x: 1}, commit_quorum="majority")``.

* When using an ``Options`` class, if multiple ``Options`` classes are structurally equatable, it is permissible to consolidate them into one with a clear name. For instance, it would be permissible to use the name ``CreateIndexOptions`` as the options for ``createIndex`` and ``createIndexes``.

Naming
------

All drivers MUST name operations and parameters as defined in the following sections. Exceptions to this rule are noted in the appropriate section. Class and interface names may vary according to the driver and language best practices.

Naming Deviations
-----------------

When deviating from a defined name, an author should consider if the altered name is recognizable and discoverable to the user of another driver.

A non-exhaustive list of acceptable naming deviations are as follows:

* Using "maxTimeMS" as an example, .NET would use "MaxTime" where it's type is a TimeSpan structure that includes units. However, calling it "MaximumTime" would not be acceptable.

* Using "CreateIndexOptions" as an example, Javascript wouldn't need to name it while other drivers might prefer to call it "CreateIndexArgs" or "CreateIndexParams".

* Acceptable naming deviations should fall within the basic style of the language. For example, ``createIndex`` would be a required name in Java, where camel-case method names are used, but in Ruby ``create_index`` would be acceptable.


Index Name Generation
---------------------

When the client generates a name for an index based on the keys, the driver MUST generate the name as key-direction pairs, separated by underscores. For example, the key ``{ name: 1, dob: -1 }`` MUST generate an index name of ``name_1_dob_-1``.

Note there is one exception to this rule on the ``_id`` field. The server uses an index name with no direction, ``_id_``, which cannot be overridden.

Timeouts
--------

Drivers MUST enforce timeouts for all operations per the `Client Side
Operations Timeout
<client-side-operations-timeout/client-side-operations-timeout.rst>`__
specification. All operations that return cursors MUST support the timeout
options documented in the `Cursors
<client-side-operations-timeout/client-side-operations-timeout.rst#Cursors>`__
section of that specification.

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
     *
     * @note Drivers MAY combine the two options types into a single one. If the options are
     *   explicitly typed, the combined options type MUST be named CreateIndexOptions or an acceptable
     *   variation.
     */
    createIndex(keys: Document, indexOptions: Optional<IndexOptions>, options: Optional<CreateIndexOptions>): String;

    /**
     * @see Comments above.
     */
    createIndex(model: IndexModel, options: Optional<CreateIndexOptions>): String

    /**
     * Creates multiple indexes in the collection.
     * 
     * In all server versions, this MUST execute a createIndexes command.
     *
     * @return The names of all the indexes that were created.
     */
    createIndexes(models: Iterable<IndexModel>, options: Optional<CreateIndexesOptions>): Iterable<String>;

    /**
     * Drops a single index from the collection by the index name.
     *
     * In all server versions this MUST execute a dropIndexes command.
     *
     * @note If the string passed is '*', the driver MUST raise an error since
     *   more than one index would be dropped.
     */
    dropIndex(name: String, options: Optional<DropIndexOptions>): Result;

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
     *
     * @note Drivers MAY combine the two options types into a single one. If the options are
     *   explicitly typed, the combined options type MUST be named DropIndexOptions or an acceptable
     *   variation.
     */
    dropIndex(keys: Document, indexOptions: IndexOptions, options: Optional<DropIndexOptions>): Result;

    /**
     * @see Comments above.
     */
    dropIndex(model: IndexModel, options: Optional<DropIndexOptions>): Result;

    /**
     * Drops all indexes in the collection.
     */
    dropIndexes(options: Optional<DropIndexesOptions>): Result;

    /**
     * Gets index information for all indexes in the collection. The behavior for 
     * enumerating indexes is described in the :ref:`Enumerating Indexes` section.
     *
     */
    listIndexes(options: Optional<ListIndexesOptions>): Cursor;
  }

  interface CreateIndexOptions {
    /**
     * Specifies how many data-bearing members of a replica set, including the primary, must
     * complete the index builds successfully before the primary marks the indexes as ready.
     *
     * This option accepts the same values for the "w" field in a write concern plus "votingMembers",
     * which indicates all voting data-bearing nodes.
     *
     * This option is only supported by servers >= 4.4. Drivers MUST manually raise an error if this option
     * is specified when creating an index on a pre 4.4 server. See the Q&A section for the rationale behind this.
     *
     * @note This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     *
     * @since MongoDB 4.4
     */
    commitQuorum: Optional<Int32 | String>;

    /**
     * The maximum amount of time to allow the index build to take before returning an error.
     *
     * @note This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     */
    maxTimeMS: Optional<Int64>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * @see https://www.mongodb.com/docs/manual/reference/command/createIndexes/
     *
     * @since MongoDB 4.4
     */
    comment: Optional<any>;
  }

  interface CreateIndexesOptions {
    // same as CreateIndexOptions
  }

  interface DropIndexOptions {
   /**
     * The maximum amount of time to allow the index drop to take before returning an error.
     *
     * @note This option is sent only if the caller explicitly provides a value. The default is to not send a value.
     */
    maxTimeMS: Optional<Int64>;

    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * @see https://www.mongodb.com/docs/manual/reference/command/dropIndexes/
     *
     * @since MongoDB 4.4
     */
    comment: Optional<any>;
  }

  interface DropIndexesOptions {
    // same as DropIndexOptions
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
    indexes(options: Optional<ListIndexesOptions>): IndexView;
  }

  interface IndexView extends Iterable<Document> {

    /**
     * Enumerates the index information for all indexes in the collection. This should be
     * implemented as described in the :ref:`Enumerate Indexes` section, although the naming
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
     *  If drivers are unable to make the IndexView iterable, they MAY opt to provide the options for 
     *  listing search indexes via the `list` method instead of the `Collection.listSearchIndexes` method.

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
     *
     * @note Drivers MAY combine the two options types into a single one. If the options are
     *   explicitly typed, the combined options type MUST be named CreateOneIndexOptions or an acceptable
     *   variation.
     */
    createOne(keys: Document, indexOptions: IndexOptions, options: Optional<CreateOneIndexOptions>): String;

    /**
     * @see Comments above.
     */
    createOne(model: IndexModel, options: Optional<CreateOneIndexOptions>): String

    /**
     * Creates multiple indexes in the collection.
     *
     * For all server versions this method MUST execute a createIndexes command.
     *
     * @return The names of the created indexes.
     *
     * @note Each specification document becomes the "key" field in the document that
     *   is inserted or the command.
     *   
     */
    createMany(models: Iterable<IndexModel>, options: Optional<CreateManyIndexesOptions>): Iterable<String>;

    /**
     * Drops a single index from the collection by the index name.
     *
     * In all server versions this MUST execute a dropIndexes command.
     *
     * @note If the string passed is '*', the driver MUST raise an error since
     *   more than one index would be dropped.
     */
    dropOne(name: String, options: Optional<DropOneIndexOptions>): Result;

    /**
     * Attempts to drop a single index from the collection given the keys and options.
     * This is OPTIONAL until partial indexes are implemented.
     *
     * In all server versions this MUST execute a dropIndexes command.
     *
     * @note Drivers MAY opt to implement this method signature, the signature that
     *   takes an IndexModel as a parameter, or for those languages with method
     *   overloading MAY decide to implement both.
     *
     * @note Drivers MAY combine the two options types into a single one. If the options are
     *   explicitly typed, the combined options type MUST be named DropOneIndexOptions or an acceptable
     *   variation.
     */
    dropOne(keys: Document, indexOptions: IndexOptions, options: Optional<DropOneIndexOptions>): Result;

    /**
     * @see Comments above.
     */
    dropOne(model: IndexModel, options: Optional<DropOneIndexOptions>): Result;

    /**
     * Drops all indexes in the collection.
     */
    dropAll(options: Optional<DropAllIndexesOptions>): Result;
  }

  interface CreateOneIndexOptions {
    // same as CreateIndexOptions in the Standard API
  }

  interface CreateManyIndexesOptions {
    // same as CreateIndexesOptions in the Standard API
  }

  interface DropOneIndexOptions {
    // same as DropIndexOptions in the Standard API
  }

  interface DropAllIndexesOptions {
    // same as DropIndexesOptions in the Standard API
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
     *
     * @note Starting in MongoDB 4.2, this option is ignored by the server.
     * @see https://www.mongodb.com/docs/manual/reference/command/createIndexes/
     * @deprecated 4.2
     */
    background: Boolean;

    /**
     * Optionally specifies the length in time, in seconds, for documents to remain in
     * a collection.
     */
    expireAfterSeconds: Int32;

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
     * Optionally used only in MongoDB 3.0.0 and higher. Allows users to configure the storage
     * engine on a per-index basis when creating an index.
     */
    storageEngine: Document;

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
     * Is 'english' if none is provided.
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
    textIndexVersion: Int32;

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
    2dsphereIndexVersion: Int32;

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
     * filter expression are included in the index. New in MongoDB 3.2.
     */
    partialFilterExpression: Document;

    /**
     * Optionally specifies a collation to use for the index in MongoDB 3.4 and higher.
     * If not specified, no collation is sent and the default collation of the collection
     * server-side is used.
     */
    collation: Document;

    /**
     * Optionally specifies the wildcard projection of a wildcard index.
     */
    wildcardProjection: Document;

    /**
     * Optionally specifies that the index should exist on the target collection but should not be used by the query
     * planner when executing operations.
     *
     * This option is only supported by servers >= 4.4.
     */
    hidden: Boolean;

    /**
     * Optionally specifies that this index is clustered.  This is not a valid option to provide to
     * 'createIndexes', but can appear in the options returned for an index via 'listIndexes'.  To
     * create a clustered index, create a new collection using the 'clusteredIndex' option.
     *
     * This options is only supported by servers >= 6.0.
     */
     clustered: Boolean;
  }

  interface ListIndexesOptions {
    /**
     * Enables users to specify an arbitrary comment to help trace the operation through
     * the database profiler, currentOp and logs. The default is to not send a value.
     *
     * If a comment is provided, drivers MUST attach this comment to all
     * subsequent getMore commands run on the same cursor.
     *
     * @see https://www.mongodb.com/docs/manual/reference/command/listIndexes/
     *
     * @since MongoDB 4.4
     */
    comment: Optional<any>;

    /**
     * Configures the batch size of the cursor returned from the ``listIndexes`` command.
     * 
     * @note drivers MAY chose to support batchSize on the ListIndexesOptions.
     */
    batchSize: Optional<Int32>;
  }

-------------------
Enumerating Indexes
-------------------

For all server versions, drivers MUST run a ``listIndexes`` command when enumerating indexes.

Drivers SHOULD use the method name ``listIndexes`` for a method that returns
all indexes with a cursor return type. Drivers MAY use an idiomatic variant
that fits the language the driver is for.  An exception is made for drivers implementing the
index view API.

In MongoDB 4.4, the ``ns`` field was removed from the index specifications returned from the ``listIndexes`` command.

- For drivers that report those index specifications in the form of documents or dictionaries, no special handling is
  necessary, but any documentation of the contents of the documents/dictionaries MUST indicate that the ``ns`` field
  will no longer be present in MongoDB 4.4+. If the contents of the documents/dictionaries are undocumented, then no
  special mention of the ``ns`` field is necessary.
- For drivers that report those index specifications in the form of statically defined models, the driver MUST manually populate
  the ``ns`` field of the models with the appropriate namespace if the server does not report it in the ``listIndexes`` command
  response. The ``ns`` field is not required to be a part of the models, however.

Getting Index Names
-------------------

Drivers MAY implement a method to enumerate all indexes, and return only
the index names.  The helper operates the same as the following example:

Example::

	> a = [];
	[ ]
	> db.runCommand( { listIndexes: 'poiConcat' } ).indexes.forEach(function(i) { a.push(i.name); } );
	> a
	[ "_id_", "ty_1", "l_2dsphere", "ts_1" ]

--------------
Search Indexes
--------------

Server 7.0 introduced three new server commands and a new aggregation stage to facilitate management of search indexes.  Drivers MUST provide 
an API similar to the existing index management API specifically for search indexes.  Drivers MAY choose to implement either the standard
API or the index view API.

Search Index Management Helper Options
--------------------------------------

There are currently no supported options for any of the search index management commands.  To future proof
drivers implementations so that any options added in the future do not constitute a breaking change to drivers,
empty options structs have been added as placeholders.  If a driver's language has a mechanism to add options 
in a non-breaking manner (i.e., method overloading) drivers MAY omit the empty options structs from their
search index management helpers.

``listSearchIndexes`` is implemented using an aggregation pipeline.  The list helper MUST support a driver's aggregation
options as outline in the `CRUD specification <https://github.com/mongodb/specifications/blob/master/source/crud/crud.rst#read>`_.  Drivers MAY combine the aggregation options with
any future ``listSearchIndexes`` stage options, if that is idiomatic for a driver's language.

Asynchronicity
--------------

The search index commands are asynchronous and return from the server before the index is successfully updated, created or dropped.
In order to determine when an index has been created / updated, users are expected to run the ``listSearchIndexes`` repeatedly
until index changes appear.

An example, from Javascript:

.. code:: typescript

  const name = await collection.createSearchIndex({ definition: { ... fill out definition } })
  while (!(await collection.listSearchIndexes({ name }).hasNext())) {
    await setTimeout(1000);
  }

Where are read concern and write concern?
-----------------------------------------

These commands internally proxy the search index management commands to a separate process that runs alongside an Atlas cluster.  As such, read concern and 
write concern are not relevant for the search index management commands.

Consistency with Existing APIs
------------------------------

Drivers SHOULD strive for a search index management API that is as consistent with their existing index management API as much as possible.


NamespaceNotFound Errors
------------------------

Some drivers suppress NamespaceNotFound errors for CRUD helpers.  Drivers MAY suppress NamespaceNotFound errors from 
the search index management helpers.

Drivers MUST suppress NamespaceNotFound errors for the ``dropSearchIndex`` helper.  Drop operations should be idempotent:

.. code:: typescript

  await collection.dropSearchIndex('my-test-index');
  // subsequent calls should behave the same for the user as the first call
  await collection.dropSearchIndex('my-test-index');
  await collection.dropSearchIndex('my-test-index');


Common Interfaces
-----------------

.. code:: typescript

  interface SearchIndexModel {
    // The definition for this index.
    definition: Document;

    // The name for this index, if present.
    name: Optional<string>;
  }

  /**
   * The following interfaces are empty but are provided as placeholders for drivers that cannot 
   * add options in a non-breaking manner, if options are added in the future.
   */
  interface CreateSearchIndexOptions {} 
  interface UpdateSearchIndexOptions {}
  interface ListSearchIndexOptions {}
  interface DropSearchIndexOptions {}

Standard API for Search Indexes
-------------------------------

.. code:: typescript

  interface Collection {
    /**
     * Convenience method for creating a single search index.
     * 
     * @return The name of the created search index
     * 
     * @note Drivers MAY opt to implement this method signature, the signature that
     *   takes an SearchIndexModel as a parameter, or for those languages with method
     *   overloading MAY decide to implement both.
     */
    createSearchIndex(definition: Document, name: Optional<string>, options: Optional<CreateSearchIndexOptions>): String;

    /**
     * Convenience method for creating a single index.
     * 
     * @return The name of the created search index
     * 
     * @note Drivers MAY opt to implement this method signature, the signature that
     *   takes an name and a definition as parameters, or for those languages with method
     *   overloading MAY decide to implement both.
     */
    createSearchIndex(model: SearchIndexModel, options: Optional<CreateSearchIndexOptions>): String;

    /**
     * Creates multiple search indexes on the collection.
     * 
     * @return An iterable of the newly created index names.
     */
    createSearchIndexes(models: Iterable<SearchIndexModel>, options: CreateSearchIndexOptions): Iterable<String>;

    /**
     * Updates the search index with the given name to use the provided 
     * definition.
     */
    updateSearchIndex(name: String, definition: Document, options: Optional<UpdateSearchIndexOptions>): void;

    /**
     * Drops the search index with the given name.
     */
    dropSearchIndex(name: String, options: Optional<DropSearchIndexOptions>): void;

    /**
     * Gets index information for one or more search indexes in the collection.
     *
     * If name is not specified, information for all indexes on the specified collection will be returned.
     */
    listSearchIndexes(name: Optional<String>, aggregationOptions: Optional<AggregationOptions>, listIndexOptions: Optional<ListSearchIndexOptions>): Cursor<Document>;
  }

Index View API for Search Indexes
---------------------------------

.. code:: typescript

  interface Collection {
    /**
     * Returns the search index view for this collection.
     */
    searchIndexes(name: Optional<String>, aggregateOptions: Optional<AggregationOptions>, options: Optional<ListSearchIndexOptions>): SearchIndexView;
  }

  interface SearchIndexView extends Iterable<Document> {
    /**
     * Enumerates the index information for all search indexes in the collection. 
     *
     * @note For drivers that cannot make the IndexView iterable, they MUST implement a list
     *   method. See below.
     */
    iterator(): Iterator<Document>;

    /**
     * For drivers that cannot make SearchIndexView iterable, they MUST implement this method to
     * return a list of indexes. In the case of async drivers, this MAY return a Future<Cursor>
     *  or language/implementation equivalent.
     *  
     *  If drivers are unable to make the SearchIndexView iterable, they MAY opt to provide the options for 
     *  listing search indexes via the `list` method instead of the `Collection.listSearchIndexes` method.
     */
    list(): Cursor<Document>;


    /**
     * This is a convenience method for creating a single index.
     *
     * @return The name of the created index.
     *
     * @note Drivers MAY opt to implement this method signature, the signature that
     *   takes an SearchIndexModel as a parameter, or for those languages with method
     *   overloading MAY decide to implement both.
     */
    createOne(definition: Document, name: Optional<string>, options: Optional<CreateSearchIndexOptions>): String;

    /**
     * This is a convenience method for creating a single index.
     *
     * @return The name of the created index.
     *
     * @note Drivers MAY opt to implement this method signature, the signature that
     *   takes an name and a definition as parameters, or for those languages with method
     *   overloading MAY decide to implement both.
     */
    createOne(model: SearchIndexModel, options: Optional<CreateSearchIndexOptions>): String;

    /**
     * Creates multiple search indexes in the collection.
     *
     * @return The names of the created indexes.
     */
    createMany(models: Iterable<SearchIndexModel>, options: Optional<CreateSearchIndexOptions>): Iterable<String>;

    /**
     * Drops a single search index from the collection by the index name.
     */
    dropOne(name: String, options: Optional<DropSearchIndexOptions>): Result;

    /**
     * Updates a single search index from the collection by the index name.
     */
    updateOne(name: String, definition: Document, options: Optional<UpdateSearchIndexOptions>): Result;
  }

---------
Q & A
---------

Q: Where is write concern?
  The ``createIndexes`` and ``dropIndexes`` commands take a write concern that indicates how the write is acknowledged. Since all operations defined in this specification are performed on a collection, it's uncommon that two different index operations on the same collection would use a different write concern. As such, the most natural place to indicate write concern is on the client, the database, or the collection itself and not the operations within it.

  However, it might be that a driver needs to expose write concern to a user per operation for various reasons. It is permitted to allow a write concern option, but since writeConcern is a top-level command option, it MUST NOT be specified as part of an ``IndexModel`` passed into the helper. It SHOULD be specified via the options parameter of the helper. For example, it would be ambiguous to specify write concern for one or more models passed to ``createIndexes()``, but it would not be to specify it via the ``CreateIndexesOptions``.

Q: What does the commitQuorum option do?
  Prior to MongoDB 4.4, secondaries would simply replicate index builds once they were completed on the primary. Building indexes requires an exclusive lock on the collection being indexed, so the secondaries would be blocked from replicating all other operations while the index build took place. This would introduce replication lag correlated to however long the index build took.

  Starting in MongoDB 4.4, secondaries build indexes simultaneously with the primary, and after starting an index build, the primary will wait for a certain number of data-bearing nodes, including itself, to have completed the build before it commits the index. ``commitQuorum`` configures this node requirement. Once the index is committed, all the secondaries replicate the commit too. If a secondary had already completed the index build, the commit will be quick, and no new replication lag would be introduced. If a secondary had not finished building the index before the primary committed it (e.g. if ``commitQuorum: 0`` was used), then that secondary may lag behind the primary while it finishes building and committing the index.

  The server-default value for ``commitQuorum`` is "votingMembers", which means the primary will wait for all voting data-bearing nodes to complete building the index before it commits it.

Q: Why would a user want to specify a non-default ``commitQuorum``?
  Like ``w: "majority"``, ``commitQuorum: "votingMembers"`` doesn't consider non-voting data-bearing nodes such as analytics nodes. If a user wanted to ensure these nodes didn't lag behind, then they would specify ``commitQuorum: <total number of data-bearing nodes, including non-voting nodes>``. Alternatively, if they wanted to ensure only specific non-voting nodes didn't lag behind, they could specify a `custom getLastErrorMode based on the nodes' tag sets <https://www.mongodb.com/docs/manual/reference/replica-configuration/#rsconf.settings.getLastErrorModes>`_ (e.g. ``commitQuorum: <custom getLastErrorMode name>``).

  Additionally, if a user has a high tolerance for replication lag, they can set a lower value for ``commitQuorum``. This is useful for situations where certain secondaries take longer to build indexes than the primaries, and the user doesn't care if they lag behind.

Q: What is the difference between write concern and ``commitQuorum``?
  While these two options share a lot in terms of how they are specified, they configure entirely different things. ``commitQuorum`` determines how much new replication lag an index build can tolerably introduce, but it says nothing of durability. Write concern specifies the durability requirements of an index build, but it makes no guarantees about introducing replication lag.

  For instance, an index built with ``writeConcern: { w: 1 }, commitQuorum: "votingMembers"`` could possibly be rolled back, but it will not introduce any new replication lag. Likewise, an index built with ``writeConcern: { w: "majority", j: true }, commitQuorum: 0`` will not be rolled back, but it may cause the secondaries to lag. To ensure the index is both durable and will not introduce replication lag on any data-bearing voting secondary, ``writeConcern: { w: "majority", j: true }, commitQuorum: "votingMembers"`` must be used.

  Also note that, since indexes are built simultaneously, higher values of ``commitQuorum`` are not as expensive as higher values of ``writeConcern``.

Q: Why does the driver manually throw errors if the ``commitQuorum`` option is specified against a pre 4.4 server?
  Starting in 3.4, the server validates all options passed to the ``createIndexes`` command, but due to a bug in versions 4.2.0-4.2.5 of the server (SERVER-47193), specifying ``commitQuorum`` does not result in an error. The option is used interally by the server on those versions, and its value could have adverse effects on index builds. To prevent users from mistakenly specifying this option, drivers manually verify it is only sent to 4.4+ servers.

Changelog
---------

:2015-09-17: Added ``partialFilterExpression`` attribute to ``IndexOptions`` in
             order to support partial indexes. Fixed "provides" typo.
:2016-05-19: Added ``collation`` attribute to ``IndexOptions`` in order to
             support setting a collation on an index.
:2016-08-08: Fixed ``collation`` language to not mention a collection default.
:2016-10-11: Added note on 3.4 servers validation options passed to
             ``createIndexes``. Add note on server generated name for the _id
             index.
:2017-05-31: Add Q & A addressing write concern and maxTimeMS option.
:2017-06-07: Include listIndexes() in Q&A about maxTimeMS.
:2019-04-24: Added ``wildcardProjection`` attribute to ``IndexOptions`` in order
             to support setting a wildcard projection on a wildcard index.
:2020-03-30: Added options types to various helpers. Introduced ``commitQuorum``
             option. Added deprecation message for ``background`` option.
:2022-01-19: Require that timeouts be applied per the client-side operations
             timeout spec.
:2022-02-01: Added comment field to helper methods.
:2022-02-10: Specified that ``getMore`` command must explicitly send inherited
             comment.
:2022-04-18: Added the ``clustered`` attribute to ``IndexOptions`` in order to
             support clustered collections.
:2022-10-05: Remove spec front matter and reformat changelog.
:2023-05-10:  Merge index enumeration and index management specs and get rid of references 
             to legacy server versions.
:2023-05-18:  Add the search index management API.
:2023-07-17:  Add search index management clarifications.