=================================
Connection Monitoring and Pooling
=================================

:Title: Connection Monitoring and Pooling
:Author: Dan Aprahamian
:Advisory Group: Jeff Yemin, Matt Broadstone
:Approvers: Bernie Hackett, Dan Pasette, Jeff Yemin, Matt Broadstone, Sam Rossi, Scott L'Hommedieu
:Status: Accepted
:Type: Standards
:Minimum Server Version: N/A
:Last Modified: June 11, 2019
:Version: 1.1.0

.. contents::

Abstract
========

Drivers currently support a variety of options that allow users to configure connection pooling behavior. Users are confused by drivers supporting different subsets of these options. Additionally, drivers implement their connection pools differently, making it difficult to design cross-driver pool functionality. By unifying and codifying pooling options and behavior across all drivers, we will increase user comprehension and code base maintainability.

META 
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Definitions
===========

``Connection``
~~~~~~~~~~~~~~

A ``Connection`` (when code-formatted) refers to the ``Connection``
type defined in this specification. It does not refer to an actual
TCP/IP connection to an Endpoint. A ``Connection`` will attempt to
create and wrap such a connection over the course of its existence,
but it is not equivalent to one nor does it wrap an active one at all
times.

For the purposes of testing, a mocked ``Connection`` type could be
used with the pool that never actually creates a TCP/IP connection or
performs any I/O.

Endpoint
~~~~~~~~

For convenience, an Endpoint refers to either a **mongod** or **mongos** instance.

Thread
~~~~~~

For convenience, a Thread refers to:

-  A shared-address-space process (a.k.a. a thread) in multi-threaded drivers
-  An Execution Frame / Continuation in asynchronous drivers
-  A goroutine in Go

Behavioral Description
======================

Which Drivers this applies to
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This specification is solely concerned with drivers that implement a connection pool. A driver SHOULD implement a connection pool, but is not required to.

Connection Pool Options
~~~~~~~~~~~~~~~~~~~~~~~

All drivers that implement a connection pool MUST implement and conform to the same MongoClient options. There can be slight deviation in naming to make the options idiomatic to the driver language.

Connection Pool Behaviors
~~~~~~~~~~~~~~~~~~~~~~~~~

All driver connection pools MUST provide an API that allows the driver to check out a connection, check in a connection back to the pool, and clear all connections in the pool. This API is for internal use only, and SHOULD NOT be documented as a public API.

Connection Pool Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~

All drivers that implement a connection pool MUST provide an API that allows users to subscribe to events emitted from the pool.

Detailed Design
===============

.. _connection-pool-options-1:

Connection Pool Options
~~~~~~~~~~~~~~~~~~~~~~~

Drivers that implement a Connection Pool MUST support the following ConnectionPoolOptions:

.. code:: typescript

    interface ConnectionPoolOptions {
      /**
       *  The maximum number of connections that may be associated
       *  with a pool at a given time. This includes in use and
       *  available connections.
       *  If specified, MUST be an integer >= 0.
       *  A value of 0 means there is no limit.
       *  Defaults to 100.
       */
      maxPoolSize?: number;

      /**
       *  The minimum number of connections that MUST exist at any moment
       *  in a single connection pool.
       *  If specified, MUST be an integer >= 0. If maxPoolSize is > 0
       *  then minPoolSize must be <= maxPoolSize
       *  Defaults to 0.
       */
      minPoolSize?: number;

      /**
       *  The maximum amount of time a connection should remain idle
       *  in the connection pool before being marked idle.
       *  If specified, MUST be a number >= 0.
       *  A value of 0 means there is no limit.
       *  Defaults to 0.
       */
      maxIdleTimeMS?: number;
    }

Additionally, Drivers that implement a Connection Pool MUST support the following ConnectionPoolOptions UNLESS that driver meets ALL of the following conditions:

-  The driver/language currently has an idiomatic timeout mechanism implemented
-  The timeout mechanism conforms to `the aggressive requirement of timing out a thread in the WaitQueue <#w1dcrm950sbn>`__

.. code:: typescript

    interface ConnectionPoolOptions {
      /**
       *  The maximum amount of time a thread can wait for a connection
       *  to become available.
       *  If specified, MUST be a number >= 0.
       *  A value of 0 means there is no limit.
       *  Defaults to 0.
       */
      waitQueueTimeoutMS?: number;
    }

These options MUST be specified at the MongoClient level, and SHOULD be named in a manner idiomatic to the driver's language. All connection pools created by a MongoClient MUST use the same ConnectionPoolOptions.

When parsing a mongodb connection string, a user MUST be able to specify these options using the default names specified above.

Deprecated Options
------------------

The following ConnectionPoolOptions are considered deprecated. They MUST NOT be implemented if they do not already exist in a driver, and they SHOULD be deprecated and removed from drivers that implement them as early as possible:

.. code:: typescript

    interface ConnectionPoolOptions {
      /**
       *  The maximum number of threads that can simultaneously wait
       *  for a connection to become available.
       */
      waitQueueSize?: number;

      /**
       *  An alternative way of setting waitQueueSize, it specifies
       *  the maximum number of threads that can wait per connection.
       *  waitQueueSize === waitQueueMultiple \* maxPoolSize
       */
      waitQueueMultiple?: number
    }

Connection Pool Members
~~~~~~~~~~~~~~~~~~~~~~~

Connection
----------

A driver-defined wrapper around a single TCP/IP connection to an Endpoint. A ``Connection`` has the following properties:

-  **Single Endpoint:** A ``Connection`` MUST be associated with a single Endpoint. A ``Connection`` MUST NOT be associated with multiple Endpoints.
-  **Single Lifetime:** A ``Connection`` MUST NOT be used after it is closed.
-  **Single Owner:** A ``Connection`` MUST belong to exactly one Pool, and MUST NOT be shared across multiple pools
-  **Single Track:** A ``Connection`` MUST limit itself to one request / response at a time. A ``Connection`` MUST NOT multiplex/pipeline requests to an Endpoint.
-  **Monotonically Increasing ID:** A ``Connection`` MUST have an ID number associated with it. ``Connection`` IDs within a Pool MUST be assigned in order of creation, starting at 1 and increasing by 1 for each new Connection.
-  **Valid Connection:** A connection MUST NOT be checked out of the pool until it has successfully and fully completed a MongoDB Handshake and Authentication as specified in the `Handshake <https://github.com/mongodb/specifications/blob/master/source/mongodb-handshake/handshake.rst>`__, `OP_COMPRESSED <https://github.com/mongodb/specifications/blob/master/source/compression/OP_COMPRESSED.rst>`__, and `Authentication <https://github.com/mongodb/specifications/blob/master/source/auth/auth.rst>`__ specifications.
-  **Perishable**: it is possible for a connection to become **Perished**. A connection is considered perished if any of the following are true:

   -  **Stale:** The connection's generation does not match the generation of the parent pool
   -  **Idle:** The connection is currently "available" and has been for longer than **maxIdleTimeMS**.
   -  **Errored:** The connection has experienced an error that indicates the connection is no longer recommended for use. Examples include, but are not limited to:

      -  Network Error
      -  Network Timeout
      -  Endpoint closing the connection
      -  Driver-Side Timeout
      -  Wire-Protocol Error

.. code:: typescript

    interface Connection {
      /**
       *  An id number associated with the connection
       */
      id: number;

      /**
       *  The address of the pool that owns this connection
       */
      address: string;

      /**
       *  An integer representing the “generation” of the pool
       *  when this connection was created
       */
      generation: number;

      /**
       * The current state of the Connection.
       *
       * Possible values are the following:
       *   - "unestablished": The Connection is empty. It has been created but has not opened a socket or
       *                      performed any I/O. Contributes to totalConnectionCount.
       *
       *   - "available":     The Connection has been established and is waiting in the pool to be checked
       *                      out. Contributes to both totalConnectionCount and availableConnectionCount.
       *
       *   - "in use":        The Connection has been established, checked out from the pool, and has yet
       *                      to be checked back in. Contributes to totalConnectionCount.
       *
       *   - "closed":        The Connection has had its socket closed and cannot be used for any future
       *                      operations. Does not contribute to any connection counts.
       *
       * Note: this field is mainly used for the purposes of describing state
       * in this specification. It is not required that drivers
       * actually include this field in their implementations of Connection.
       */
      state: "unestablished" | "available" | "in use" | "closed";
    }

WaitQueue
---------

A concept that represents pending requests for Connections. When a thread requests a ``Connection`` from a Pool, the thread enters the Pool's WaitQueue. A thread stays in the WaitQueue until it either receives a ``Connection`` or times out. A WaitQueue has the following traits:

-  **Thread-Safe**: When multiple threads attempt to enter or exit a WaitQueue, they do so in a thread-safe manner.
-  **Ordered/Fair**: When connections are made available, they are issued out to threads in the order that the threads entered the WaitQueue.
-  **Timeout aggressively:** If **waitQueueTimeoutMS** is set, members of a WaitQueue MUST timeout if they are enqueued for longer than waitQueueTimeoutMS. Members of a WaitQueue MUST timeout aggressively, and MUST leave the WaitQueue immediately upon timeout.

The implementation details of a WaitQueue are left to the driver.
Example implementations include:

-  A fair Semaphore
-  A Queue of callbacks

Connection Pool
---------------

A driver-defined entity that encapsulates all non-monitoring Connections associated with a single Endpoint. The pool has the following properties:

-  **Thread Safe:** All Pool behaviors MUST be thread safe.
-  **Not Fork-Safe:** A Pool is explicitly not fork-safe. If a Pool detects that is it being used by a forked process, it MUST immediately clear itself and update its pid
-  **Single Owner:** A Pool MUST be associated with exactly one Endpoint, and MUST NOT be shared between Endpoints.
-  **Emit Events:** A Pool MUST emit pool events when dictated by this spec (see `Connection Pool Monitoring <#connection-pool-monitoring>`__). Users MUST be able to subscribe to emitted events in a manner idiomatic to their language and driver.
-  **Closeable:** A Pool MUST be able to be manually closed. When a Pool is closed, the following behaviors change:

   -  Checking in a ``Connection`` to the Pool automatically closes the Connection
   -  Attempting to check out a ``Connection`` from the Pool results in an Error

-  **Capped:** a pool is capped if **maxPoolSize** is set to a non-zero value. If a pool is capped, then its total number of Connections (including available and in use) MUST NOT exceed **maxPoolSize**

.. code:: typescript

    interface ConnectionPool {
      /**
       *  The Queue of threads waiting for a Connection to be available
       */
      waitQueue: WaitQueue;
    
      /**
       *  A generation number representing the SDAM generation of the pool
       */
      generation: number;
    
      /**
       *  An integer expressing how many total Connections
       *  (active + in use) the pool currently has
       */
      totalConnectionCount: number;
    
      /**
       *  An integer expressing how many Connections are currently
       *  available in the pool.
       */
      availableConnectionCount: number;

      /**
       *  Returns a Connection for use
       */
      checkOut(): Connection;

      /**
       *  Check in a Connection back to the Connection pool
       */
      checkIn(connection: Connection): void;

      /**
       *  Mark all current Connections as stale.
       */
      clear(): void;

      /**
       *  Closes the pool, preventing the pool from creating and returning new Connections
       */
      close(): void;
    }

.. _connection-pool-behaviors-1:

Connection Pool Behaviors
~~~~~~~~~~~~~~~~~~~~~~~~~

Creating a Connection Pool
--------------------------

This specification does not define how a pool is to be created, leaving it
up to the driver. Creation of a connection pool is generally an implementation
detail of the driver, i.e., is not a part of the public API of the driver.
The SDAM specification defines `when
<https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#connection-pool-creation>`_
the driver should create connection pools.

Once a pool is created, if minPoolSize is set, the pool MUST
immediately begin populating enough Connections such that
totalConnections >= minPoolSize. These Connections MUST be populated
in a non-blocking manner, such as via the use of a background thread
or asynchronous I/O.

.. code::

    set generation to 0
    emit PoolCreatedEvent
    if minPoolSize is set:
      # this MAY be performed on a background thread
      # if it is not performed on a background thread, this MUST
      # utilize non-blocking I/O.
      while totalConnectionCount < minPoolSize:
        populate pool with a connection

Closing a Connection Pool
-------------------------

When a pool is closed, it MUST first close all available ``Connections`` in that pool. This results in the following behavior changes:

-  In use ``Connections`` MUST be closed when they are checked in to the closed pool.
-  Attempting to check out a ``Connection`` MUST result in an error.

.. code::

    mark pool as CLOSED
    for connection in availableConnections:
      close connection
    emit PoolClosedEvent

Creating a Connection (Internal Implementation)
-----------------------------------------------

When creating a ``Connection``, the initial ``Connection`` is in an
“unestablished” state. This only creates a “virtual” ``Connection``, and
performs no I/O. 

.. code::

    connection = new Connection()
    increment total connection count
    set connection state to "unestablished"
    emit ConnectionCreatedEvent
    return connection

Establishing a Connection (Internal Implementation)
---------------------------------------------------

Before a ``Connection`` can be marked as "available" or "in use", it
must be established. This process involves performing the initial
handshake, handling OP_COMPRESSED, and performing authentication.

.. code::

    try:
      connect connection via TCP / TLS
      perform connection handshake
      handle OP_COMPRESSED
      perform connection authentication
      emit ConnectionReadyEvent
      return connection
    except error:
      close connection
      throw error # Propagate error in manner idiomatic to language.


Closing a Connection (Internal Implementation)
----------------------------------------------

When a ``Connection`` is closed, it MUST first be marked as "closed",
removing it from being counted as "available" or "in use". One that is
complete, the ``Connection`` can perform whatever teardown is
necessary to close its underlying socket. The Driver MUST perform this
teardown in a non-blocking manner, such as via the use of a background
thread or async I/O.

.. code::

    decrement total connection count
    if connection state is "available":
      decrement available connection count
    set connection state to "closed"
    emit ConnectionClosedEvent

    # The following can happen at a later time (i.e. in background
    # thread) or via non-blocking I/O.
    connection.socket.close()

Marking a Connection as Available (Internal Implementation)
-----------------------------------------------------------

A ``Connection`` is "available" if it is able to be checked out. A
``Connection`` MUST NOT be marked as "available" until it has been
established. The pool MUST keep track of the number of currently
available ``Connections``.

.. code::

   add connection to availableConnections
   increment available connection count
   set connection state to "available"


Populating the Pool with a Connection (Internal Implementation)
---------------------------------------------------------------

If minPoolSize is set, the pool MUST ensure that it always has at
least minPoolSize total ``Connections``. In order to achieve this, it needs to
be able to create ``Connections`` that begin as checked in instead of checked
out (i.e. "populate the pool"). Performing this process MUST NOT
block any application threads. For example, it could be performed on a
background thread or via the use of non-blocking I/O.

.. code::

   create connection
   establish connection
   mark connection as available


Checking Out a Connection
-------------------------

A Pool MUST have a method of allowing the driver to check out a ``Connection``. Checking out a ``Connection`` involves entering the WaitQueue and waiting for a ``Connection`` to become available. If the thread times out in the WaitQueue, an error is thrown.

If, in the process of iterating available ``Connections`` in the pool
by the checkOut method, a perished ``Connection`` is encountered, such
a ``Connection`` MUST be closed and the iteration of available
``Connections`` MUST continue until either a non-perished available
``Connection`` is found or the list of available ``Connections`` is
exhausted. If no ``Connections`` are available and the total number of
``Connections`` is less than maxPoolSize, the pool MUST create and
return a new ``Connection``.

If the pool is closed, any attempt to check out a ``Connection`` MUST throw an Error, and any items in the waitQueue MUST be removed from the waitQueue and throw an Error.

If minPoolSize is set, the ``Connection`` Pool MUST always have at
least minPoolSize total ``Connections``. If the pool does not
implement a background thread, the checkOut method is responsible for
ensuring this requirement.

A ``Connection`` MUST NOT be checked out until it is established. In
addition, the Pool MUST NOT block other threads from checking out
``Connections`` while establishing a ``Connection``.

Before returning a ``Connection``, it must be marked as "in use". This
MUST decrement the pool's available ``Connection`` count.

.. code::

    connection = Null
    emit ConnectionCheckOutStartedEvent
    try:
      enter WaitQueue
      wait until at top of wait queue
      # Note that in a lock-based implementation of the wait queue would
      # only allow one thread in the following block at a time
      while connection is Null:
        if a connection is available:
          while connection is Null and a connection is available:
            connection = next available connection
            if connection is perished:
              close connection
              connection = Null
        else if totalConnectionCount < maxPoolSize:
          connection = create connection
        # If there is no background thread, the pool MUST ensure that
        # there are at least minPoolSize total connections.
        # This MUST be done in a non-blocking manner
        while totalConnectionCount < minPoolSize:
          populate the pool with a connection
          
    except pool is closed:
      emit ConnectionCheckOutFailedEvent(reason="poolClosed")
      throw PoolClosedError
    except timeout:
      emit ConnectionCheckOutFailedEvent(reason="timeout")
      throw WaitQueueTimeoutError
    finally:
      # This must be done in all drivers
      leave wait queue

    # If the connection has not been connected yet, the connection
    # (TCP, TLS, handshake, compression, and auth) must be performed
    # before the connection is returned. This MUST NOT block other threads
    # from acquiring connections.
    if connection state is "unestablished":
      try:
        establish connection
      except connection establishment error:
        emit ConnectionCheckOutFailedEvent(reason="error")
        throw

    decrement available connection count
    set connection state to "in use"
    emit ConnectionCheckedOutEvent
    return connection

Checking In a Connection
------------------------

A Pool MUST have a method of allowing the driver to check in a
``Connection``. The driver MUST NOT be allowed to check in a
``Connection`` to a Pool that did not create that ``Connection``, and
MUST throw an Error if this is attempted.

When the ``Connection`` is checked in, it is closed if any of the following are true:

-  The ``Connection`` is perished.
-  The pool has been closed.

Otherwise, the ``Connection`` is marked as available.

.. code::

    emit ConnectionCheckedInEvent
    if connection is perished OR pool is closed:
      close connection
    else:
      mark connection as available

Clearing a Connection Pool
--------------------------

A Pool MUST have a method of clearing all ``Connections`` when instructed. Rather than iterating through every ``Connection``, this method should simply increment the generation of the Pool, implicitly marking all current ``Connections`` as stale. The checkOut and checkIn algorithms will handle clearing out stale ``Connections``. If a user is subscribed to Connection Monitoring events, a PoolClearedEvent MUST be emitted after incrementing the generation.

Forking
-------

A ``Connection`` is explicitly not fork-safe. The proper behavior in the case of a fork is to ResetAfterFork by:

-  clear all Connection Pools in the child process
-  closing all ``Connections`` in the child-process.

Drivers that support forking MUST document that ``Connections`` to an Endpoint are not fork-safe, and document the proper way to ResetAfterFork in the driver.

Drivers MAY aggressively ResetAfterFork if the driver detects it has been forked.

Optional Behaviors
------------------

The following features of a Connection Pool SHOULD be implemented if they make sense in the driver and driver's language.

Background Thread
^^^^^^^^^^^^^^^^^

A Pool SHOULD have a background Thread that is responsible for
monitoring the state of all available ``Connections``. This background
thread SHOULD

-  Populate ``Connections`` to ensure that the pool always satisfies **minPoolSize**
-  Remove and close perished available ``Connections``.

withConnection
^^^^^^^^^^^^^^

A Pool SHOULD implement a scoped resource management mechanism idiomatic to their language to prevent ``Connections`` from not being checked in. Examples include `Python's "with" statement <https://docs.python.org/3/whatsnew/2.6.html#pep-343-the-with-statement>`__ and `C#'s "using" statement <https://docs.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/using-statement>`__. If implemented, drivers SHOULD use this method as the default method of checking out and checking in ``Connections``.

.. _connection-pool-monitoring-1:

Connection Pool Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~

All drivers that implement a connection pool MUST provide an API that allows users to subscribe to events emitted from the pool. If a user subscribes to Connection Monitoring events, these events MUST be emitted when specified in “Connection Pool Behaviors”. Events SHOULD be created and subscribed to in a manner idiomatic to their language and driver.

Events
------


.. code:: typescript

    /**
     *  Emitted when a Connection Pool is created
     */
    interface PoolCreatedEvent {
      /**
       *  The ServerAddress of the Endpoint the pool is attempting to connect to.
       */
      address: string;

      /**
       *  Any non-default pool options that were set on this Connection Pool.
       */
      options: {...}
    }

    /**
     *  Emitted when a Connection Pool is cleared
     */
    interface PoolClearedEvent {
      /**
       *  The ServerAddress of the Endpoint the pool is attempting to connect to.
       */
      address: string;
    }

    /**
     *  Emitted when a Connection Pool is closed
     */
    interface PoolClosedEvent {
      /**
       *  The ServerAddress of the Endpoint the pool is attempting to connect to.
       */
      address: string;
    }

    /**
     *  Emitted when a Connection Pool creates a Connection object.
     *  NOTE: This does not mean that the Connection is ready for use.
     */
    interface ConnectionCreatedEvent { 
      /**
       *  The ServerAddress of the Endpoint the pool is attempting to connect to.
       */
      address: string;
    
      /**
       *  The ID of the Connection
       */
      connectionId: number;
    }

    /**
     *  Emitted when a Connection has finished its setup, and is now ready to use
     */
    interface ConnectionReadyEvent {
      /**
       *  The ServerAddress of the Endpoint the pool is attempting to connect to.
       */
      address: string;
    
      /**
       *  The ID of the Connection
       */
      connectionId: number;
    }

    /**
     *  Emitted when a Connection Pool closes a Connection
     */
    interface ConnectionClosedEvent {
      /**
       *  The ServerAddress of the Endpoint the pool is attempting to connect to.
       */
      address: string;
    
      /**
       *  The ID of the Connection
       */
      connectionId: number;
    
      /**
       * A reason explaining why this Connection was closed.
       * Can be implemented as a string or enum.
       * Current valid values are:
       *   - "stale":           The pool was cleared, making the Connection no longer valid
       *   - "idle":            The Connection became stale by being available for too long
       *   - "error":           The Connection experienced an error, making it no longer valid
       *   - "poolClosed":      The pool was closed, making the Connection no longer valid
       */
      reason: string|Enum;
    }

    /**
     *  Emitted when the driver starts attempting to check out a Connection
     */
    interface ConnectionCheckOutStartedEvent {
      /**
       * The ServerAddress of the Endpoint the pool is attempting
       * to connect to.
       */
      address: string;
    }

    /**
     *  Emitted when the driver's attempt to check out a Connection fails
     */
    interface ConnectionCheckOutFailedEvent {
      /**
       *  The ServerAddress of the Endpoint the pool is attempting to connect to.
       */
      address: string;
    
      /**
       *  A reason explaining why Connection check out failed.
       *  Can be implemented as a string or enum.
       *  Current valid values are:
       *   - "poolClosed":      The pool was previously closed, and cannot provide new Connections
       *   - "timeout":         The Connection check out attempt exceeded the specified timeout
       *   - "connectionError": The Connection check out attempt experienced an error while setting up a new Connection
       */
      reason: string|Enum;
    }

    /**
     *  Emitted when the driver successfully checks out a Connection
     */
    interface ConnectionCheckedOutEvent {
      /**
       *  The ServerAddress of the Endpoint the pool is attempting to connect to.
       */
      address: string;

      /**
       *  The ID of the Connection
       */
      connectionId: number;
    }

    /**
     *  Emitted when the driver checks in a Connection back to the Connection Pool
     */
    interface ConnectionCheckedInEvent {
      /**
       * The ServerAddress of the Endpoint the pool is attempting to connect to.
       */
      address: string;
    
      /**
       *  The ID of the Connection
       */
      connectionId: number;
    }

Connection Pool Errors
~~~~~~~~~~~~~~~~~~~~~~

A connection pool throws errors in specific circumstances. These Errors
MUST be emitted by the pool. Errors SHOULD be created and dispatched in
a manner idiomatic to the Driver and Language.

.. code:: typescript

    /**
     *  Thrown when the driver attempts to check out a
     *  Connection from a closed Connection Pool
     */
    interface PoolClosedError {
      message: 'Attempted to check out a Connection from closed connection pool';
      address: <pool address>;
    }

    /**
     *  Thrown when a driver times out when attempting to check out
     *  a Connection from a Pool
     */
    interface WaitQueueTimeoutError {
      message: 'Timed out while checking out a Connection from connection pool';
      address: <pool address>;
    }

Test Plan
=========

See `tests/README.rst <tests/README.rst>`_

Design Rationale
================

Why do we set minPoolSize across all members of a replicaSet, when most traffic will be against a Primary?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Currently, we are attempting to codify our current pooling behavior with minimal changes, and minPoolSize is currently uniform across all members of a replicaSet. This has the benefit of offsetting connection swarming during a Primary Step-Down, which will be further addressed in our `Advanced Pooling Behaviors <#advanced-pooling-behaviors>`__.

Why do we have separate ConnectionCreated and ConnectionReady events, but only one ConnectionClosed event?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ConnectionCreated and ConnectionReady each involve different state changes in the pool.

-  ConnectionCreated adds a new “unestablished” ``Connection``, meaning the totalConnectionCount increases by one
-  ConnectionReady establishes that the ``Connection`` is ready for use, meaning the availableConnectionCount increases by one

ConnectionClosed indicates that the ``Connection`` is no longer a member of the pool, decrementing totalConnectionCount and potentially availableConnectionCount. After this point, the ``Connection`` is no longer a part of the pool. Further hypothetical events would not indicate a change to the state of the pool, so they are not specified here.

Why are waitQueueSize and waitQueueMultiple deprecated?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These options were originally only implemented in three drivers (Java, C#, and Python), and provided little value. While these fields would allow for faster diagnosis of issues in the connection pool, they would not actually prevent an error from occurring. 

Additionally, these options have the effect of prioritizing older requests over newer requests, which is not necessarily the behavior that users want. They can also result in cases where queue access oscillates back and forth between full and not full. If a driver has a full waitQueue, then all requests for ``Connections`` will be rejected. If the client is continually spammed with requests, you could wind up with a scenario where as soon as the waitQueue is no longer full, it is immediately filled. It is not a favorable situation to be in, partially b/c it violates the fairness guarantee that the waitQueue normally provides. 

Because of these issues, it does not make sense to `go against driver mantras and provide an additional knob <../../README.rst#>`__. We may eventually pursue an alternative configurations to address wait queue size in `Advanced Pooling Behaviors <#advanced-pooling-behaviors>`__.

Users that wish to have this functionality can achieve similar results by utilizing other methods to limit concurrency. Examples include implementing either a thread pool or an operation queue with a capped size in the user application. Drivers that need to deprecate ``waitQueueSize`` and/or ``waitQueueMultiple`` SHOULD refer users to these examples.

Why is waitQueueTimeoutMS optional for some drivers?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We are anticipating eventually introducing a single client-side timeout mechanism, making us hesitant to introduce another granular timeout control. Therefore, if a driver/language already has an idiomatic way to implement their timeouts, they should leverage that mechanism over implementing waitQueueTimeoutMS.

Why must ensuring minPoolSize require the use of a background thread or async I/O?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Without the use of a background thread, minPoolSize is ensured during
checkOut. ``Connections`` may not be checked into the pool before
being established however, so establishment also happens during
checkOut. If it were done in a blocking fashion, the first operations
after a clearing of the pool would experience unacceptably high
latency, especially for larger values of minPoolSize. Thus,
minPoolSize either needs to be ensured via a background thread (which
is acceptable to block) or via the usage of non-blocking (async) I/O.

Backwards Compatibility
=======================

As mentioned in `Deprecated Options <#deprecated-options>`__, some drivers currently implement the options ``waitQueueSize`` and/or ``waitQueueMultiple``. These options will need to be deprecated and phased out of the drivers that have implemented them.


Reference Implementations
=========================

- JAVA (JAVA-3079)
- RUBY (RUBY-1560)

Future Development
==================

SDAM
~~~~

This specification does not dictate how SDAM Monitoring connections are managed. SDAM specifies that “A monitor SHOULD NOT use the client's regular Connection pool”. Some possible solutions for this include:

-  Having each Endpoint representation in the driver create and manage a separate dedicated ``Connection`` for monitoring purposes
-  Having each Endpoint representation in the driver maintain a separate pool of maxPoolSize 1 for monitoring purposes.
-  Having each Pool maintain a dedicated ``Connection`` for monitoring purposes, with an API to expose that Connection.

Advanced Pooling Behaviors
~~~~~~~~~~~~~~~~~~~~~~~~~~

This spec does not address any advanced pooling behaviors like predictive pooling, aggressive ``Connection`` creation, or handling high request volume. Future work may address this.

Add support for OP_MSG exhaustAllowed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Exhaust Cursors may require changes to how we close ``Connections`` in the future, specifically to add a way to close and remove from its pool a ``Connection`` which has unread exhaust messages.


Change log
==========

:2019-06-06: Add "connectionError" as a valid reason for ConnectionCheckOutFailedEvent
