.. role:: javascript(code)
  :language: javascript

=============================
SDAM Monitoring Specification
=============================

:Spec: 222
:Title: SDAM Monitoring Specification
:Spec Version: Same as the `Server Discovery And Monitoring`_ spec
:Author: Durran Jordan
:Spec Lead: Durran Jordan
:Advisory Group: Jeff Yemin, Craig Wilson, Jesse Davis
:Status: Approved
:Type: Standards
:Minimum Server Version: 2.4
:Last Modified: 06-May-2021

.. contents::

--------

Abstract
========

The SDAM monitoring specification defines a set of behaviour in the drivers for providing runtime information about server discovery and monitoring events (SDAM) to any 3rd party library as well internal driver use, such as logging.

-----------
Definitions
-----------

META
----

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Terms
-----

``ServerAddress``

  The term ``ServerAddress`` refers to the implementation in the driver's language of a server host/port pair. This may be an object or a string. The name of this object is NOT REQUIRED.

``TopologyType``

  The term ``TopologyType`` refers to the implementation in the driver's language of a topology type (standalone, sharded, etc.). This may be a string or object. The name of the object is NOT REQUIRED.

``Server``

  The term ``Server`` refers to the implementation in the driver’s language of either an abstraction of a connection to a single mongod or mongos process, as defined by the `SDAM specification <https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#server>`_.

-------------
Specification
-------------

Events
------
This specification defines 9 main events that MUST be published in the scenarios described. 6 of these events are the core behaviour within the cluster lifecycle, and the remaining 3 server heartbeat events are fired from the server monitor and follow the guidelines for publishing in the command monitoring specification.

Events that MUST be published (with their conditions) are as follows.

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Event Type
     - Condition
   * - ``TopologyOpeningEvent``
     - When a topology description is initialized - this MUST be the first SDAM event fired.
   * - ``ServerOpeningEvent``
     - Published when the server description is instantiated with its defaults, and MUST be the first operation to happen after the defaults are set. This is before the Monitor is created and the Monitor socket connection is opened.
   * - ``ServerDescriptionChangedEvent``
     - When the old server description is not equal to the new server description
   * - ``TopologyDescriptionChangedEvent``
     - When the old topology description is not equal to the new topology description.
   * - ``ServerClosedEvent``
     - Published when the server monitor’s connection is closed and the server is shutdown.
   * - ``TopologyClosedEvent``
     - When a topology is shut down - this MUST be the last SDAM event fired.
   * - ``ServerHeartbeatStartedEvent``
     - Published when the server monitor sends its ``hello`` or legacy hello call to the server.
   * - ``ServerHeartbeatSucceededEvent``
     - Published on successful completion of the server monitor’s ``hello`` or legacy hello call.
   * - ``ServerHeartbeatFailedEvent``
     - Published on failure of the server monitor’s ``hello`` or legacy hello call, either with an ok: 0 result or a socket exception from the connection.


Operations
----------
All drivers MUST implement the API. Implementation details are noted in the comments when a specific implementation is required. Within each API, all methods are REQUIRED unless noted otherwise in the comments.

Naming
------
All drivers MUST name operations, parameters and topic names as defined in the following sections. Exceptions to this rule are noted in the appropriate section. Class and interface names may vary according to the driver and language best practices.

Documentation
-------------
The documentation provided in code below is merely for driver authors and SHOULD NOT be taken as required documentation for the driver.

--------
Guidance
--------

Publishing and Subscribing
--------------------------

The driver SHOULD publish events in a manner that is standard to the driver's language publish/subscribe patterns and is not strictly mandated in this specification.

----------
Guarantees
----------

Event Order and Concurrency
---------------------------

Events MUST be published in the order they were applied in the driver.
Events MUST NOT be published concurrently for the same topology id or server id, but MAY be published concurrently for differing topology ids and server ids.

Heartbeats
----------

The driver MUST guarantee that every ServerHeartbeatStartedEvent has either a correlating ServerHeartbeatSucceededEvent or ServerHeartbeatFailedEvent.

Drivers that use the streaming heartbeat protocol MUST publish a ServerHeartbeatStartedEvent before attempting to read the next ``hello`` or legacy hello exhaust response.

Error Handling
--------------

If an exception occurs while sending the ``hello`` or legacy hello operation to the server, the driver MUST generate a ServerHeartbeatFailedEvent with the exception or message and re-raise the exception. The SDAM mandated retry of the ``hello`` or legacy hello call should be visible to consumers.

Topology Ids
------------

These MUST be a unique value that is specific to the Topology in which the events are fired. The language may decide how to generate the value and what type the value is, as long as it is unique to the Topology. The id MUST be created once when the Topology is created and remain the same until the Topology is destroyed.

Topology Description
--------------------

The TopologyDescription object MUST expose the new methods defined in the API below, in order for subscribers to take action on certain conditions based on the driver options.

TopologyDescription objects MAY have additional methods and properties.

Initial Server Description
--------------------------

ServerDescriptions MUST be initialized with a default description in an “unknown” state, guaranteeing that the previous description in the events will never be null.

---
API
---

.. code:: typescript

  /**
   * Published when server description changes, but does NOT include changes to the RTT.
   */
  interface ServerDescriptionChangedEvent {

    /**
     * Returns the address (host/port pair) of the server.
     */
    address: ServerAddress;

    /**
     * Returns a unique identifier for the topology.
     */
    topologyId: Object;

    /**
     * Returns the previous server description.
     */
    previousDescription: ServerDescription;

    /**
     * Returns the new server description.
     */
    newDescription: ServerDescription;
  }

 /**
   * Published when server is initialized.
   */
  interface ServerOpeningEvent {

    /**
     * Returns the address (host/port pair) of the server.
     */
    address: ServerAddress;

    /**
     * Returns a unique identifier for the topology.
     */
    topologyId: Object;
  }

 /**
   * Published when server is closed.
   */
  interface ServerClosedEvent {

    /**
     * Returns the address (host/port pair) of the server.
     */
    address: ServerAddress;

    /**
     * Returns a unique identifier for the topology.
     */
    topologyId: Object;
  }

  /**
   * Published when topology description changes.
   */
  interface TopologyDescriptionChangedEvent {

    /**
     * Returns a unique identifier for the topology.
     */
    topologyId: Object;

    /**
     * Returns the old topology description.
     */
    previousDescription: TopologyDescription;

    /**
     * Returns the new topology description.
     */
    newDescription: TopologyDescription;
  }

  /**
   * Published when topology is initialized.
   */
  interface TopologyOpeningEvent {

    /**
     * Returns a unique identifier for the topology.
     */
    topologyId: Object;
  }

  /**
   * Published when topology is closed.
   */
  interface TopologyClosedEvent {

    /**
     * Returns a unique identifier for the topology.
     */
    topologyId: Object;
  }

  /**
   * Fired when the server monitor’s ``hello`` or legacy hello command is started - immediately before
   * the ``hello`` or legacy hello command is serialized into raw BSON and written to the socket.
   */
  interface ServerHeartbeatStartedEvent {

   /**
     * Returns the connection id for the command. The connection id is the unique
     * identifier of the driver’s Connection object that wraps the socket. For languages that
     * do not have this object, this MUST a string of “hostname:port” or an object that
     * that contains the hostname and port as attributes.
     *
     * The name of this field is flexible to match the object that is returned from the driver.
     * Examples are, but not limited to, ‘address’, ‘serverAddress’, ‘connectionId’,
     */
    connectionId: ConnectionId;

   /**
     * Determines if this heartbeat event is for an awaitable ``hello`` or legacy hello.
     */
    awaited: Boolean;

  }

  /**
   * Fired when the server monitor’s ``hello`` or legacy hello succeeds.
   */
  interface ServerHeartbeatSucceededEvent {

   /**
     * Returns the execution time of the event in the highest possible resolution for the platform.
     * The calculated value MUST be the time to send the message and receive the reply from the server,
     * including BSON serialization and deserialization. The name can imply the units in which the
     * value is returned, i.e. durationMS, durationNanos.
     *
     * When the awaited field is false, the time measurement used MUST be the
     * same measurement used for the RTT calculation. When the awaited field is
     * true, the time measurement is not used for RTT calculation.
     */
    duration: Int64;

    /**
     * Returns the command reply.
     */
    reply: Document;

   /**
     * Returns the connection id for the command. For languages that do not have this,
     * this MUST return the driver equivalent which MUST include the server address and port.
     * The name of this field is flexible to match the object that is returned from the driver.
     */
    connectionId: ConnectionId;

   /**
     * Determines if this heartbeat event is for an awaitable ``hello`` or legacy hello. If
     * true, then the duration field cannot be used for RTT calculation
     * because the command blocks on the server.
     */
    awaited: Boolean;

  }

  /**
   * Fired when the server monitor’s ``hello`` or legacy hello fails, either with an “ok: 0” or a socket exception.
   */
  interface ServerHeartbeatFailedEvent {

   /**
     * Returns the execution time of the event in the highest possible resolution for the platform.
     * The calculated value MUST be the time to send the message and receive the reply from the server,
     * including BSON serialization and deserialization. The name can imply the units in which the
     * value is returned, i.e. durationMS, durationNanos.
     */
    duration: Int64;

   /**
     * Returns the failure. Based on the language, this SHOULD be a message string,
     * exception object, or error document.
     */
    failure: String,Exception,Document;

   /**
     * Returns the connection id for the command. For languages that do not have this,
     * this MUST return the driver equivalent which MUST include the server address and port.
     * The name of this field is flexible to match the object that is returned from the driver.
     */
    connectionId: ConnectionId;

   /**
     * Determines if this heartbeat event is for an awaitable ``hello`` or legacy hello. If
     * true, then the duration field cannot be used for RTT calculation
     * because the command blocks on the server.
     */
    awaited: Boolean;
  }

  /**
   * Describes the current topology.
   */
  interface TopologyDescription {

    /**
     * Determines if the topology has a readable server available. See the table in the
     * following section for behaviour rules.
     */
    hasReadableServer(readPreference: Optional<ReadPreference>): Boolean

    /**
     * Determines if the topology has a writable server available. See the table in the
     * following section for behaviour rules.
     */
    hasWritableServer(): Boolean
  }

-------------------------------------------------------
Determining If A Topology Has Readable/Writable Servers
-------------------------------------------------------

The following table describes the behaviour of determining if a topology type has readable or
writable servers. If no read preference is passed to ``hasReadableServer``, the driver MUST default
the value to the default read preference, ``primary``, or treat the call as if ``primary`` was provided.

+-----------------------+----------------------------------------+----------------------------------------+
| Topology Type         | ``hasReadableServer``                  | ``hasWritableServer``                  |
+=======================+========================================+========================================+
| Unknown               | ``false``                              | ``false``                              |
+-----------------------+----------------------------------------+----------------------------------------+
| Single                | ``true`` if the server is available    | ``true`` if the server is available    |
+-----------------------+----------------------------------------+----------------------------------------+
| ReplicaSetNoPrimary   | | Called with ``primary``: ``false``   | ``false``                              |
|                       | | Called with any other option: uses   |                                        |
|                       |   the read preference to determine if  |                                        |
|                       |   any server in the cluster is         |                                        |
|                       |   suitable for reading.                |                                        |
|                       | | Called with no option: ``false``     |                                        |
+-----------------------+----------------------------------------+----------------------------------------+
| ReplicaSetWithPrimary | | Called with any valid option: uses   | ``true``                               |
|                       |   the read preference to determine if  |                                        |
|                       |   any server in the cluster is         |                                        |
|                       |   suitable for reading.                |                                        |
|                       | | Called with no option: ``true``      |                                        |
+-----------------------+----------------------------------------+----------------------------------------+
| Sharded               | ``true`` if 1+ servers are available   | ``true`` if 1+ servers are available   |
+-----------------------+----------------------------------------+----------------------------------------+

--------
Examples
--------

A Ruby subscriber to topology description changed events that logs the events.

Ruby:

.. code:: ruby

  class TopologyDescriptionChangedSubscriber

    def completed(event)
      new_description = event.new_description
      if (!new_description.has_writable_server?)
        LOGGER.warn('New topology description contains no writable server.')
      end
    end
  end

-----
Tests
-----

See the `README <https://github.com/mongodb/specifications/server-discovery-and-monitoring/tests/monitoring/README.rst>`_.


Changelog
=========

- 30 APR 2021: Updated to use modern terminology.
- 20 APR 2020: Add rules for streaming heartbeat protocol and add "awaited" field to heartbeat events.
- 12 DEC 2018: Clarified table of rules for readable/writable servers
- 31 AUG 2016: Added table of rules for determining if topology has readable/writable servers.
- 11 OCT 2016: TopologyDescription objects MAY have additional methods and properties.

.. Section for links.

.. _Server Discovery And Monitoring: server-discovery-and-monitoring.rst
