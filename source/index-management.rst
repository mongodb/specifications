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
:Last Modified: Mar 30, 2020
:Version: 1.6

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
**********

A non-exhaustive list of acceptable deviations are as follows:

* Using named parameters in place of an options hash or class. For instance, ``collection.create_index({x: 1}, commit_quorum="majority")``.

* When using an ``Options`` class, if multiple ``Options`` classes are structurally equatable, it is permissible to consolidate them into one with a clear name. For instance, it would be permissible to use the name ``CreateIndexOptions`` as the options for ``createIndex`` and ``createIndexes``.

Naming
------

All drivers MUST name operations and parameters as defined in the following sections. Exceptions to this rule are noted in the appropriate section. Class and interface names may vary according to the driver and language best practices.

Deviations
**********

When deviating from a defined name, an author should consider if the altered name is recognizable and discoverable to the user of another driver.

A non-exhaustive list of acceptable naming deviations are as follows:

* Using "maxTimeMS" as an example, .NET would use "MaxTime" where it's type is a TimeSpan structure that includes units. However, calling it "MaximumTime" would not be acceptable.

* Using "CreateIndexOptions" as an example, Javascript wouldn't need to name it while other drivers might prefer to call it "CreateIndexArgs" or "CreateIndexParams".

* Acceptable naming deviations should fall within the basic style of the language. For example, ``createIndex`` would be a required name in Java, where camel-case method names are used, but in Ruby ``create_index`` would be acceptable.


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
     * @see https://docs.mongodb.com/manual/reference/command/createIndexes/
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
  }

---------
Q & A
---------

Q: Where is write concern?
  The ``createIndexes`` and ``dropIndexes`` commands take a write concern that indicates how the write is acknowledged. Since all operations defined in this specification are performed on a collection, it's uncommon that two different index operations on the same collection would use a different write concern. As such, the most natural place to indicate write concern is on the client, the database, or the collection itself and not the operations within it.

  However, it might be that a driver needs to expose write concern to a user per operation for various reasons. It is permitted to allow a write concern option, but since writeConcern is a top-level command option, it MUST NOT be specified as part of an ``IndexModel`` passed into the helper. It SHOULD be specified via the options parameter of the helper. For example, it would be ambiguous to specify write concern for one or more models passed to ``createIndexes()``, but it would not be to specify it via the ``CreateIndexesOptions``.

Q: Where is ``ListIndexesOptions``?
  There are no options required by the index enumeration spec for listing indexes, so there is currently no need to define an options type for it. A driver MAY accept options (e.g. ``maxTimeMS``) on the helpers that list indexes, and, if it does, it SHOULD accept them the same way it accepts options for other helpers (e.g. through a ``ListCollectionOptions`` object or acceptable deviation).

Q: What does the commitQuorum option do?
  Prior to MongoDB 4.4, secondaries would simply replicate index builds once they were completed on the primary. Building indexes requires an exclusive lock on the collection being indexed, so the secondaries would be blocked from replicating all other operations while the index build took place. This would introduce replication lag correlated to however long the index build took.

  Starting in MongoDB 4.4, secondaries build indexes simultaneously with the primary, and after starting an index build, the primary will wait for a certain number of data-bearing nodes, including itself, to have completed the build before it commits the index. ``commitQuorum`` configures this node requirement. Once the index is committed, all the secondaries replicate the commit too. If a secondary had already completed the index build, the commit will be quick, and no new replication lag would be introduced. If a secondary had not finished building the index before the primary committed it (e.g. if ``commitQuorum: 0`` was used), then that secondary may lag behind the primary while it finishes building and committing the index.

  The server-default value for ``commitQuorum`` is "votingMembers", which means the primary will wait for all voting data-bearing nodes to complete building the index before it commits it.

Q: Why would a user want to specify a non-default ``commitQuorum``?
  Like ``w: "majority"``, ``commitQuorum: "votingMembers"`` doesn't consider non-voting data-bearing nodes such as analytics nodes. If a user wanted to ensure these nodes didn't lag behind, then they would specify ``commitQuorum: <total number of data-bearing nodes, including non-voting nodes>``. Alternatively, if they wanted to ensure only specific non-voting nodes didn't lag behind, they could specify a `custom getLastErrorMode based on the nodes' tag sets <https://docs.mongodb.com/manual/reference/replica-configuration/#rsconf.settings.getLastErrorModes>`_ (e.g. ``commitQuorum: <custom getLastErrorMode name>``).

  Additionally, if a user has a high tolerance for replication lag, they can set a lower value for ``commitQuorum``. This is useful for situations where certain secondaries take longer to build indexes than the primaries, and the user doesn't care if they lag behind. 

Q: What is the difference between write concern and ``commitQuorum``?
  While these two options share a lot in terms of how they are specified, they configure entirely different things. ``commitQuorum`` determines how much new replication lag an index build can tolerably introduce, but it says nothing of durability. Write concern specifies the durability requirements of an index build, but it makes no guarantees about introducing replication lag.

  For instance, an index built with ``writeConcern: { w: 1 }, commitQuorum: "votingMembers"`` could possibly be rolled back, but it will not introduce any new replication lag. Likewise, an index built with ``writeConcern: { w: "majority", j: true }, commitQuorum: 0`` will not be rolled back, but it may cause the secondaries to lag. To ensure the index is both durable and will not introduce replication lag on any data-bearing voting secondary, ``writeConcern: { w: "majority", j: true }, commitQuorum: "votingMembers"`` must be used.

  Also note that, since indexes are built simultaneously, higher values of ``commitQuorum`` are not as expensive as higher values of ``writeConcern``.

Q: Why does the driver manually throw errors if the ``commitQuorum`` option is specified against a pre 4.4 server?
  Starting in 3.4, the server validates all options passed to the ``createIndexes`` command, but due to a bug in versions 4.2.0-4.2.5 of the server (SERVER-47193), specifying ``commitQuorum`` does not result in an error. The option is used interally by the server on those versions, and its value could have adverse effects on index builds. To prevent users from mistakenly specifying this option, drivers manually verify it is only sent to 4.4+ servers.

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
24 April 2019:
  - Added ``wildcardProjection`` attribute to ``IndexOptions`` in order to support setting a wildcard projection on a wildcard index.
30 MAR 2020:
  - Added options types to various helpers
  - Introduced ``commitQuorum`` option
  - Added deprecation message for ``background`` option.
