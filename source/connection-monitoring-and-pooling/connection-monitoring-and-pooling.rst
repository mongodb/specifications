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
:Last Modified: 2021-05-26
:Version: 1.5.1

.. contents::

Abstract
========

Drivers currently support a variety of options that allow users to configure connection pooling behavior. Users are confused by drivers supporting different subsets of these options. Additionally, drivers implement their connection pools differently, making it difficult to design cross-driver pool functionality. By unifying and codifying pooling options and behavior across all drivers, we will increase user comprehension and code base maintainability.

META 
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Definitions
===========

Connection
~~~~~~~~~~~~~~

A Connection (when linked) refers to the ``Connection`` type defined in the
`Connection Pool Members`_ section of this specification. It does not refer to an actual TCP
connection to an Endpoint. A ``Connection`` will attempt to create and wrap such
a TCP connection over the course of its existence, but it is not equivalent to
one nor does it wrap an active one at all times.

For the purposes of testing, a mocked ``Connection`` type could be used with the
pool that never actually creates a TCP connection or performs any I/O.

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
       *  The maximum number of Connections that may be associated
       *  with a pool at a given time. This includes in use and
       *  available connections.
       *  If specified, MUST be an integer >= 0.
       *  A value of 0 means there is no limit.
       *  Defaults to 100.
       */
      maxPoolSize?: number;

      /**
       *  The minimum number of Connections that MUST exist at any moment
       *  in a single connection pool.
       *  If specified, MUST be an integer >= 0. If maxPoolSize is > 0
       *  then minPoolSize must be <= maxPoolSize
       *  Defaults to 0.
       */
      minPoolSize?: number;

      /**
       *  The maximum amount of time a Connection should remain idle
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
       *  for a Connection to become available.
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

A driver-defined wrapper around a single TCP connection to an Endpoint. A `Connection`_ has the following properties:

-  **Single Endpoint:** A `Connection`_ MUST be associated with a single Endpoint. A `Connection`_ MUST NOT be associated with multiple Endpoints.
-  **Single Lifetime:** A `Connection`_ MUST NOT be used after it is closed.
-  **Single Owner:** A `Connection`_ MUST belong to exactly one Pool, and MUST NOT be shared across multiple pools
-  **Single Track:** A `Connection`_ MUST limit itself to one request / response at a time. A `Connection`_ MUST NOT multiplex/pipeline requests to an Endpoint.
-  **Monotonically Increasing ID:** A `Connection`_ MUST have an ID number associated with it. `Connection`_ IDs within a Pool MUST be assigned in order of creation, starting at 1 and increasing by 1 for each new Connection.
-  **Valid Connection:** A connection MUST NOT be checked out of the pool until it has successfully and fully completed a MongoDB Handshake and Authentication as specified in the `Handshake <https://github.com/mongodb/specifications/blob/master/source/mongodb-handshake/handshake.rst>`__, `OP_COMPRESSED <https://github.com/mongodb/specifications/blob/master/source/compression/OP_COMPRESSED.rst>`__, and `Authentication <https://github.com/mongodb/specifications/blob/master/source/auth/auth.rst>`__ specifications.
-  **Perishable**: it is possible for a `Connection`_ to become **Perished**. A `Connection`_ is considered perished if any of the following are true:

   -  **Stale:** The `Connection`_ 's generation does not match the generation of the parent pool
   -  **Idle:** The `Connection`_ is currently "available" (as defined below) and has been for longer than **maxIdleTimeMS**.
   -  **Errored:** The `Connection`_ has experienced an error that indicates it is no longer recommended for use. Examples include, but are not limited to:

      -  Network Error
      -  Network Timeout
      -  Endpoint closing the connection
      -  Driver-Side Timeout
      -  Wire-Protocol Error

.. code:: typescript

    interface Connection {
      /**
       *  An id number associated with the Connection
       */
      id: number;

      /**
       *  The address of the pool that owns this Connection
       */
      address: string;

      /**
       *  An integer representing the “generation” of the pool
       *  when this Connection was created.
       */
      generation: number;

      /**
       * The current state of the Connection.
       *
       * Possible values are the following:
       *   - "pending":       The Connection has been created but has not yet been established. Contributes to
       *                      totalConnectionCount and pendingConnectionCount.
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
      state: "pending" | "available" | "in use" | "closed";
    }

WaitQueue
---------

A concept that represents pending requests for `Connections <#connection>`_. When a thread requests a `Connection <#connection>`_ from a Pool, the thread enters the Pool's WaitQueue. A thread stays in the WaitQueue until it either receives a `Connection <#connection>`_ or times out. A WaitQueue has the following traits:

-  **Thread-Safe**: When multiple threads attempt to enter or exit a WaitQueue, they do so in a thread-safe manner.
-  **Ordered/Fair**: When `Connections <#connection>`_ are made available, they are issued out to threads in the order that the threads entered the WaitQueue.
-  **Timeout aggressively:** If **waitQueueTimeoutMS** is set, members of a WaitQueue MUST timeout if they are enqueued for longer than waitQueueTimeoutMS. Members of a WaitQueue MUST timeout aggressively, and MUST leave the WaitQueue immediately upon timeout.

The implementation details of a WaitQueue are left to the driver.
Example implementations include:

-  A fair Semaphore
-  A Queue of callbacks

Connection Pool
---------------

A driver-defined entity that encapsulates all non-monitoring
`Connections <#connection>`_ associated with a single Endpoint. The pool
has the following properties:

-  **Thread Safe:** All Pool behaviors MUST be thread safe.
-  **Not Fork-Safe:** A Pool is explicitly not fork-safe. If a Pool detects that is it being used by a forked process, it MUST immediately clear itself and update its pid
-  **Single Owner:** A Pool MUST be associated with exactly one Endpoint, and MUST NOT be shared between Endpoints.
-  **Emit Events:** A Pool MUST emit pool events when dictated by this spec (see `Connection Pool Monitoring <#connection-pool-monitoring>`__). Users MUST be able to subscribe to emitted events in a manner idiomatic to their language and driver.
-  **Closeable:** A Pool MUST be able to be manually closed. When a Pool is closed, the following behaviors change:

   -  Checking in a `Connection <#connection>`_ to the Pool automatically closes the `Connection <#connection>`_
   -  Attempting to check out a `Connection <#connection>`_ from the Pool results in an Error

-  **Clearable:** A Pool MUST be able to be cleared. Clearing the pool marks all pooled and checked out `Connections <#connection>`_ as stale and lazily closes them as they are checkedIn or encountered in checkOut. Additionally, all requests are evicted from the WaitQueue and return errors that are considered non-timeout network errors.

-  **Pausable:** A Pool MUST be able to be paused and resumed. A Pool is paused automatically when it is cleared, and it can be resumed by being marked as "ready". While the Pool is paused, it exhibits the following behaviors:

   -  Attempting to check out a `Connection <#connection>`_ from the Pool results in a non-timeout network error
   -  Connections are not created in the background to satisfy minPoolSize

-  **Capped:** a pool is capped if **maxPoolSize** is set to a non-zero value. If a pool is capped, then its total number of `Connections <#connection>`_ (including available and in use) MUST NOT exceed **maxPoolSize**
-  **Rate-limited:** A Pool MUST limit the number of connections being created at a given time to be 2 (maxConnecting). 


.. code:: typescript

    interface ConnectionPool {
      /**
       *  The Queue of threads waiting for a Connection to be available
       */
      waitQueue: WaitQueue;
    
      /**
       *  A generation number representing the SDAM generation of the pool.
       */
      generation: number;

      /**
       * A map representing the various generation numbers for various services
       * when in load balancer mode.
       */
      serviceGenerations: Map<ObjectId, [number, number]>;

      /**
       * The state of the pool.
       *
       * Possible values are the following:
       *   - "paused":        The initial state of the pool. Connections may not be checked out nor can they
       *                      be established in the background to satisfy minPoolSize. Clearing a pool
       *                      transitions it to this state.
       *
       *   - "ready":         The healthy state of the pool. It can service checkOut requests and create
       *                      connections in the background. The pool can be set to this state via the
       *                      ready() method.
       *
       *   - "closed":        The pool is destroyed. No more Connections may ever be checked out nor any
       *                      created in the background. The pool can be set to this sate via the close()
       *                      method. The pool cannot transition to any other state after being closed.
       */
      state: "paused" | "ready" | "closed";
    
      // Any of the following connection counts may be computed rather than
      // actually stored on the pool.

      /**
       *  An integer expressing how many total Connections
       *  ("pending" + "available" + "in use") the pool currently has
       */
      totalConnectionCount: number;
    
      /**
       *  An integer expressing how many Connections are currently
       *  available in the pool.
       */
      availableConnectionCount: number;

      /**
       *  An integer expressing how many Connections are currently
       *  being established.
       */
      pendingConnectionCount: number;

      /**
       *  Returns a Connection for use
       */
      checkOut(): Connection;

      /**
       *  Check in a Connection back to the Connection pool
       */
      checkIn(connection: Connection): void;

      /**
       *  Mark all current Connections as stale, clear the WaitQueue, and mark the pool as "paused".
       *  No connections may be checked out or created in this pool until ready() is called again.
       */
      clear(): void;

      /**
       *  Mark the pool as "ready", allowing checkOuts to resume and connections to be created in the background.
       *  A pool can only transition from "paused" to "ready". A "closed" pool
       *  cannot be marked as "ready" via this method.
       */
      ready(): void;

      /**
       *  Marks the pool as "closed", preventing the pool from creating and returning new Connections
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

When a pool is created, its state MUST initially be set to "paused". Even if
minPoolSize is set, the pool MUST NOT begin being `populated
<#populating-the-pool-with-a-connection-internal-implementation>`_ with
`Connections <#connection>`_ until it has been marked as "ready". SDAM will mark
the pool as "ready" on each successful check. See `Connection Pool Management`_
section in the SDAM specification for more information.

.. code::

    set generation to 0
    set state to "paused"
    emit PoolCreatedEvent

Closing a Connection Pool
-------------------------

When a pool is closed, it MUST first close all available `Connections <#connection>`_ in that pool. This results in the following behavior changes:

-  In use `Connections <#connection>`_ MUST be closed when they are checked in to the closed pool.
-  Attempting to check out a `Connection <#connection>`_ MUST result in an error.

.. code::

    mark pool as "closed"
    for connection in availableConnections:
      close connection
    emit PoolClosedEvent

Marking a Connection Pool as Ready
----------------------------------

Connection Pools start off as "paused", and they are marked as "ready" by
monitors after they perform successful server checks. Once a pool is "ready",
it can start checking out `Connections <#connection>`_ and populating them in
the background.

If the pool is already "ready" when this method is invoked, then this
method MUST immediately return and MUST NOT emit a PoolReadyEvent.

.. code::

   mark pool as "ready"
   emit PoolReadyEvent
   resume background thread

Note that resuming the background thread after emitting PoolReadyEvent is of the essence,
and it must be the case that no observer is able to observe actions of the background thread
related to creating new connections before observing the PoolReadyEvent event.

Creating a Connection (Internal Implementation)
-----------------------------------------------

When creating a `Connection <#connection>`_, the initial `Connection <#connection>`_ is in a
“pending” state. This only creates a “virtual” `Connection <#connection>`_, and
performs no I/O. 

.. code::

    connection = new Connection()
    increment totalConnectionCount
    increment pendingConnectionCount
    set connection state to "pending"
    emit ConnectionCreatedEvent
    return connection

Establishing a Connection (Internal Implementation)
---------------------------------------------------

Before a `Connection <#connection>`_ can be marked as either "available" or "in use", it
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

When a `Connection <#connection>`_ is closed, it MUST first be marked as "closed",
removing it from being counted as "available" or "in use". Once that is
complete, the `Connection <#connection>`_ can perform whatever teardown is
necessary to close its underlying socket. The Driver SHOULD perform this
teardown in a non-blocking manner, such as via the use of a background
thread or async I/O.

.. code::

    original state = connection state
    set connection state to "closed"

    if original state is "available":
      decrement availableConnectionCount
    else if original state is "pending":
      decrement pendingConnectionCount

    decrement totalConnectionCount
    emit ConnectionClosedEvent

    # The following can happen at a later time (i.e. in background
    # thread) or via non-blocking I/O.
    connection.socket.close()

Marking a Connection as Available (Internal Implementation)
-----------------------------------------------------------

A `Connection <#connection>`_ is "available" if it is able to be checked out. A
`Connection <#connection>`_ MUST NOT be marked as "available" until it has been
established. The pool MUST keep track of the number of currently
available `Connections <#connection>`_.

.. code::

   increment availableConnectionCount
   set connection state to "available"
   add connection to availableConnections


Populating the Pool with a Connection (Internal Implementation)
---------------------------------------------------------------

"Populating" the pool involves preemptively creating and establishing a
`Connection <#connection>`_ which is marked as "available" for use in future
operations. This process is used to help ensure the number of established
connections managed by the pool is at least minPoolSize.

Populating the pool MUST NOT block any application threads. For example, it
could be performed on a background thread or via the use of non-blocking/async
I/O. Populating the pool MUST NOT be performed unless the pool is "ready".

If an error is encountered while populating a connection, it MUST be handled
via the SDAM machinery according to the `Application Errors`_ section in the
SDAM specification.

.. code::

   wait until pendingConnectionCount < maxConnecting and pool is "ready"
   create connection
   try:
     establish connection
     mark connection as available
   except error:
     # Defer error handling to SDAM.
     topology.handle_pre_handshake_error(error)

Checking Out a Connection
-------------------------

A Pool MUST have a method that allows the driver to check out a `Connection`_.
Checking out a `Connection`_ involves submitting a request to the WaitQueue and,
once that request reaches the front of the queue, having the Pool find or create
a `Connection`_ to fulfill that request. If waitQueueTimeoutMS is specified,
then requests MUST time out after spending waitQueueTimeoutMS or longer in the
WaitQueue without receiving a `Connection`_.

To service a request for a `Connection`_, the Pool MUST first iterate over the
list of available `Connections <#connection>`_, searching for a non-perished one
to be returned. If a perished `Connection`_ is encountered, such a `Connection`_
MUST be closed (as described in `Closing a Connection
<#closing-a-connection-internal-implementation>`_) and the iteration of
available `Connections <#connection>`_ MUST continue until either a non-perished
available `Connection`_ is found or the list of available `Connections
<#connection>`_ is exhausted.

If the list is exhausted, the total number of `Connections <#connection>`_ is
less than maxPoolSize, and pendingConnectionCount < maxConnecting, the pool MUST
create a `Connection`_, establish it, mark it as "in use" and return it. If
totalConnectionCount == maxPoolSize or pendingConnectionCount == maxConnecting,
then the pool MUST wait to service the request until neither of those two
conditions are met or until a `Connection`_ becomes available, re-entering the
checkOut loop in either case. This waiting MUST NOT prevent `Connections
<#connection>`_ from being checked into the pool. Additionally, the Pool MUST
NOT service any newer checkOut requests before fulfilling the original one which
could not be fulfilled. For drivers that implement the WaitQueue via a fair
semaphore, a condition variable may also be needed to to meet this
requirement. Waiting on the condition variable SHOULD also be limited by the
WaitQueueTimeout, if the driver supports one and it was specified by the user.

If the pool is "closed" or "paused", any attempt to check out a `Connection
<#connection>`_ MUST throw an Error. The error thrown as a result of the pool
being "paused" MUST be considered a retryable error and MUST NOT be an error
that marks the SDAM state unknown.

If minPoolSize is set, the `Connection <#connection>`_ Pool MUST have at least
minPoolSize total `Connections <#connection>`_ while it is "ready". If the pool does
not implement a background thread, the checkOut method is responsible for
`populating the pool
<#populating-the-pool-with-a-connection-internal-implementation>`_ with enough
`Connections <#connection>`_ such that this requirement is met.

A `Connection <#connection>`_ MUST NOT be checked out until it is
established. In addition, the Pool MUST NOT prevent other threads from checking
out `Connections <#connection>`_ while establishing a `Connection
<#connection>`_.

Before a given `Connection <#connection>`_ is returned from checkOut, it must be marked as
"in use", and the pool's availableConnectionCount MUST be decremented.

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
          if pendingConnectionCount < maxConnecting:
            connection = create connection
          else:
            # this waiting MUST NOT prevent other threads from checking Connections
            # back in to the pool.
            wait until pendingConnectionCount < maxConnecting or a connection is available
            continue
          
    except pool is "closed":
      emit ConnectionCheckOutFailedEvent(reason="poolClosed")
      throw PoolClosedError
    except pool is "paused":
      emit ConnectionCheckOutFailedEvent(reason="connectionError")
      throw PoolClearedError
    except timeout:
      emit ConnectionCheckOutFailedEvent(reason="timeout")
      throw WaitQueueTimeoutError
    finally:
      # This must be done in all drivers
      leave wait queue

    # If there is no background thread, the pool MUST ensure that
    # there are at least minPoolSize total connections.
    # This MUST be done in a non-blocking manner
    while totalConnectionCount < minPoolSize:
      populate the pool with a connection

    # If the Connection has not been established yet (TCP, TLS,
    # handshake, compression, and auth), it must be established
    # before it is returned.
    # This MUST NOT block other threads from acquiring connections.
    if connection state is "pending":
      try:
        establish connection
      except connection establishment error:
        emit ConnectionCheckOutFailedEvent(reason="error")
        decrement totalConnectionCount
        throw
      finally:
        decrement pendingConnectionCount
    else:
        decrement availableConnectionCount
    set connection state to "in use"
    emit ConnectionCheckedOutEvent
    return connection

Checking In a Connection
------------------------

A Pool MUST have a method of allowing the driver to check in a
`Connection <#connection>`_. The driver MUST NOT be allowed to check in a
`Connection <#connection>`_ to a Pool that did not create that `Connection <#connection>`_, and
MUST throw an Error if this is attempted.

When the `Connection <#connection>`_ is checked in, it MUST be `closed
<#closing-a-connection-internal-implementation>`_ if any of the following are
true:

-  The `Connection <#connection>`_ is perished.
-  The pool has been closed.

Otherwise, the `Connection <#connection>`_ is marked as available.

.. code::

    emit ConnectionCheckedInEvent
    if connection is perished OR pool is closed:
      close connection
    else:
      mark connection as available

Clearing a Connection Pool
--------------------------

A Pool MUST have a method of clearing all `Connections <#connection>`_ when
instructed. Rather than iterating through every `Connection <#connection>`_,
this method should simply increment the generation of the Pool, implicitly
marking all current `Connections <#connection>`_ as stale. It should also
transition the pool's state to "paused" to halt the creation of new connections
until it is marked as "ready" again. The checkOut and checkIn algorithms will
handle clearing out stale `Connections <#connection>`_. If a user is subscribed
to Connection Monitoring events, a PoolClearedEvent MUST be emitted after
incrementing the generation / marking the pool as "paused". If the pool is
already "paused" when it is cleared, then the pool MUST NOT emit a PoolCleared
event.

A Pool MUST also have a method of clearing all `Connections <#connection>`_ for a
specific ``serviceId`` for use when in load balancer mode. This method increments
the generation of the pool for that specific ``serviceId`` in the generation map.

As part of clearing the pool, the WaitQueue MUST also be cleared, meaning all
requests in the WaitQueue MUST fail with errors indicating that the pool was
cleared while the checkOut was being performed. The error returned as a result
of the pool being cleared MUST be considered a retryable error and MUST NOT be
an error that marks the SDAM state unknown. Clearing the WaitQueue MUST happen
eagerly so that any operations waiting on `Connections <#connection>`_ can retry
as soon as possible. The pool MUST NOT rely on WaitQueueTimeoutMS to clear
requests from the WaitQueue.

Load Balancer Mode
------------------

For load-balanced deployments, pools MUST maintain a map from ``serviceId`` to a
tuple of (generation, connection count) where the connection count refers to the
total number of connections that exist for a specific ``serviceId``. The pool MUST
remove the entry for a ``serviceId`` once the connection count reaches 0.
Once the MongoDB handshake is done, the connection MUST get the
generation number that applies to its ``serviceId`` from the map and update the
map to increment the connection count for this ``serviceId``.

See the `Load Balancer Specification <../load-balancers/load-balancers.rst#connection-pooling>`__ for details.


Forking
-------

A `Connection <#connection>`_ is explicitly not fork-safe. The proper behavior in the case of a fork is to ResetAfterFork by:

-  clear all Connection Pools in the child process
-  closing all `Connections <#connection>`_ in the child-process.

Drivers that support forking MUST document that `Connections <#connection>`_ to an Endpoint are not fork-safe, and document the proper way to ResetAfterFork in the driver.

Drivers MAY aggressively ResetAfterFork if the driver detects it has been forked.

Optional Behaviors
------------------

The following features of a Connection Pool SHOULD be implemented if they make sense in the driver and driver's language.

Background Thread
^^^^^^^^^^^^^^^^^

A Pool SHOULD have a background Thread that is responsible for
monitoring the state of all available `Connections <#connection>`_. This background
thread SHOULD

-  Populate `Connections <#connection>`_ to ensure that the pool always satisfies minPoolSize
-  Remove and close perished available `Connections <#connection>`_.

Conceptually, the aforementioned activities are organized into sequential Background Thread Runs of unspecified duration.
A Run MUST do as much work as readily available and then end instead of waiting for more work.
For example, instead of waiting for pendingConnectionCount to become less than maxConnecting when satisfying minPoolSize,
a Run MUST either proceed with the rest of its duties, e.g., closing available perished connections, or end.

Marking a pool as `ready <#marking-a-connection-pool-as-ready>`__ MUST start a new Run as soon as possible.

The duration of intervals between the end of one Run and the beginning of the next Run is not specified,
but the
`Test Format and Runner Specification <https://github.com/mongodb/specifications/tree/master/source/connection-monitoring-and-pooling/tests>`__
may restrict this duration, or introduce other restrictions to facilitate testing.

withConnection
^^^^^^^^^^^^^^

A Pool SHOULD implement a scoped resource management mechanism idiomatic to their language to prevent `Connections <#connection>`_ from not being checked in. Examples include `Python's "with" statement <https://docs.python.org/3/whatsnew/2.6.html#pep-343-the-with-statement>`__ and `C#'s "using" statement <https://docs.microsoft.com/en-us/dotnet/csharp/language-reference/keywords/using-statement>`__. If implemented, drivers SHOULD use this method as the default method of checking out and checking in `Connections <#connection>`_.

.. _connection-pool-monitoring-1:

Connection Pool Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~

All drivers that implement a connection pool MUST provide an API that allows users to subscribe to events emitted from the pool. If a user subscribes to Connection Monitoring events, these events MUST be emitted when specified in “Connection Pool Behaviors”. Events SHOULD be created and subscribed to in a manner idiomatic to their language and driver.

Events
------

See the `Load Balancer Specification <../load-balancers/load-balancers.rst#events>`__ for details on the ``serviceId`` field.

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
     *  Emitted when a Connection Pool is marked as ready.
     */
    interface PoolReadyEvent {
      /**
       *  The ServerAddress of the Endpoint the pool is attempting to connect to.
       */
      address: string;
    }

    /**
     *  Emitted when a Connection Pool is cleared
     */
    interface PoolClearedEvent {
      /**
       *  The ServerAddress of the Endpoint the pool is attempting to connect to.
       */
      address: string;

      /**
       * The service id for which the pool was cleared for in load balancing mode.
       * See load balancer specification for more information about this field.
       */
      serviceId: Optional<ObjectId>
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
     *  Thrown when the driver attempts to check out a
     *  Connection from a paused Connection Pool
     */
    interface PoolClearedError extends RetryableError {
      message: 'Connection pool for <pool address> was cleared because another operation failed with: <original error which cleared the pool>';
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

-  ConnectionCreated adds a new “pending” `Connection <#connection>`_, meaning
   the totalConnectionCount and pendingConnectionCount increase by one
-  ConnectionReady establishes that the `Connection <#connection>`_ is ready for use, meaning the availableConnectionCount increases by one

ConnectionClosed indicates that the `Connection <#connection>`_ is no longer a member of the pool, decrementing totalConnectionCount and potentially availableConnectionCount. After this point, the `Connection <#connection>`_ is no longer a part of the pool. Further hypothetical events would not indicate a change to the state of the pool, so they are not specified here.

Why are waitQueueSize and waitQueueMultiple deprecated?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These options were originally only implemented in three drivers (Java, C#, and Python), and provided little value. While these fields would allow for faster diagnosis of issues in the connection pool, they would not actually prevent an error from occurring. 

Additionally, these options have the effect of prioritizing older requests over newer requests, which is not necessarily the behavior that users want. They can also result in cases where queue access oscillates back and forth between full and not full. If a driver has a full waitQueue, then all requests for `Connections <#connection>`_ will be rejected. If the client is continually spammed with requests, you could wind up with a scenario where as soon as the waitQueue is no longer full, it is immediately filled. It is not a favorable situation to be in, partially b/c it violates the fairness guarantee that the waitQueue normally provides. 

Because of these issues, it does not make sense to `go against driver mantras and provide an additional knob <../../README.rst#>`__. We may eventually pursue an alternative configurations to address wait queue size in `Advanced Pooling Behaviors <#advanced-pooling-behaviors>`__.

Users that wish to have this functionality can achieve similar results by utilizing other methods to limit concurrency. Examples include implementing either a thread pool or an operation queue with a capped size in the user application. Drivers that need to deprecate ``waitQueueSize`` and/or ``waitQueueMultiple`` SHOULD refer users to these examples.

Why is waitQueueTimeoutMS optional for some drivers?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We are anticipating eventually introducing a single client-side timeout mechanism, making us hesitant to introduce another granular timeout control. Therefore, if a driver/language already has an idiomatic way to implement their timeouts, they should leverage that mechanism over implementing waitQueueTimeoutMS.

Why must populating the pool require the use of a background thread or async I/O?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Without the use of a background thread, the pool is `populated
<#populating-the-pool-with-a-connection-internal-implementation>`_ with enough
connections to satisfy minPoolSize during checkOut. `Connections <#connection>`_
are established as part of populating the pool though, so if `Connection
<#connection>`_ establishment were done in a blocking fashion, the first
operations after a clearing of the pool would experience unacceptably high
latency, especially for larger values of minPoolSize. Thus, populating the pool
must occur on a background thread (which is acceptable to block) or via the
usage of non-blocking (async) I/O.

Why should closing a connection be non-blocking?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because idle and perished `Connections <#connection>`_ are cleaned up as part of
checkOut, performing blocking I/O while closing such `Connections <#connection>`_
would block application threads, introducing unnecessary latency. Once
a `Connection <#connection>`_ is marked as "closed", it will not be checked out
again, so ensuring the socket is torn down does not need to happen
immediately and can happen at a later time, either via async I/O or a
background thread. 

Why can the pool be paused?
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The distinction between the "paused" state and the "ready" state allows the pool
to determine whether or not the endpoint it is associated with is available or
not. This enables the following behaviors:

1. The pool can halt the creation of background connection establishments until
   the endpoint becomes available again. Without the "paused" state, the pool
   would have no way of determining when to begin establishing background
   connections again, so it would just continually attempt, and often fail, to
   create connections until minPoolSize was satisfied, even after repeated
   failures. This could unnecessarily waste resources both server and driver side.

2. The pool can evict requests that enter the WaitQueue after the pool was
   cleared but before the server was in a known state again. Such requests can
   occur when a server is selected at the same time as it becomes marked as
   Unknown in highly concurrent workloads. Without the "paused" state, the pool
   would attempt to service these requests, since it would assume they were
   routed to the pool because its endpoint was available, not because of a race
   between SDAM and Server Selection. These requests would then likely fail with
   potentially high latency, again wasting resources both server and driver side.

Why not emit PoolCleared events when clearing a paused pool?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a pool is already paused when it is cleared, that means it was previously
cleared and no new connections have been created since then. Thus, clearing the
pool in this case is essentially a no-op, so there is no need to notify any
listeners that it has occurred. The generation is still incremented, however, to
ensure future errors that caused the duplicate clear will stop attempting to
clear the pool again. This situation is possible if the pool is cleared by the
background thread after it encounters an error establishing a connection, but
the ServerDescription for the endpoint was not updated accordingly yet.

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

-  Having each Endpoint representation in the driver create and manage a separate dedicated `Connection <#connection>`_ for monitoring purposes
-  Having each Endpoint representation in the driver maintain a separate pool of maxPoolSize 1 for monitoring purposes.
-  Having each Pool maintain a dedicated `Connection <#connection>`_ for monitoring purposes, with an API to expose that Connection.

Advanced Pooling Behaviors
~~~~~~~~~~~~~~~~~~~~~~~~~~

This spec does not address all advanced pooling behaviors like predictive pooling or aggressive `Connection <#connection>`_ creation. Future work may address this.

Add support for OP_MSG exhaustAllowed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Exhaust Cursors may require changes to how we close `Connections <#connection>`_ in the future, specifically to add a way to close and remove from its pool a `Connection <#connection>`_ which has unread exhaust messages.


Change log
==========
:2020-12-17: Introduce "paused" and "ready" states. Clear WaitQueue on pool clear.

:2020-09-24: Introduce maxConnecting requirement

:2020-09-03: Clarify Connection states and definition. Require the use of a
             background thread and/or async I/O. Add tests to ensure
             ConnectionReadyEvents are fired after ConnectionCreatedEvents.

:2019-06-06: Add "connectionError" as a valid reason for
             ConnectionCheckOutFailedEvent

:2021-4-12: Adding in behaviour for load balancer mode.

:2021-05-26: Formalize the behavior of a `Background Thread <#background-thread>`__.

.. Section for links.

.. _Application Errors: /source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#application-errors
.. _Connection Pool Management: /source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#connection-pool-management
