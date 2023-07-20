.. role:: javascript(code)
  :language: javascript

=========================================
SDAM Logging and Monitoring Specification
=========================================

:Status: Accepted
:Minimum Server Version: 2.4

.. contents::

--------

Abstract
========

The SDAM logging and monitoring specification defines a set of behaviors in the driver for providing runtime information about server discovery and monitoring (SDAM) in log messages, as well as in events that users can consume programmatically, either directly or by integrating with third-party APM libraries.

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

  The term ``Server`` refers to the implementation in the driver's language of an abstraction of a mongod or mongos process, or a load balancer, as defined by the
  `SDAM specification <https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#server>`_.

-------------
Specification
-------------

--------
Guidance
--------

Documentation
-------------

The documentation provided in the code below is merely for driver authors and SHOULD NOT be taken as required documentation for the driver.

Messages and Events
-------------------

All drivers MUST implement the specified event types as well as log messages.

Implementation details are noted below when a specific implementation is required. Within each event and log message, all properties are REQUIRED unless noted otherwise.

Naming
------

All drivers MUST name types, properties, and log message values as defined in the following sections. Exceptions to this rule are noted in the appropriate section. Class and interface names may vary according to the driver and language best practices.

Publishing and Subscribing
--------------------------

The driver SHOULD publish events in a manner that is standard to the driver's language publish/subscribe patterns and is not strictly mandated in this specification.

Similarly, as described in the `logging specification <../logging/logging.rst#implementation-requirements>`_ the driver SHOULD emit log messages in a manner that is standard for the language.

----------
Guarantees
----------

Event Order and Concurrency
---------------------------

Events and log messages MUST be published in the order that their corresponding changes are processed in the driver.
Events MUST NOT be published concurrently for the same topology ID or server ID, but MAY be published concurrently for differing topology IDs and server IDs.

Heartbeats
----------

The driver MUST guarantee that every ``ServerHeartbeatStartedEvent`` has either a correlating ``ServerHeartbeatSucceededEvent`` or ``ServerHeartbeatFailedEvent``, and that
every "server heartbeat started" log message has either a correlating "server heartbeat succeeded" or "server heartbeat failed" log message.

Drivers that use the streaming heartbeat protocol MUST publish a ``ServerHeartbeatStartedEvent`` and "server heartbeat started" log message before attempting to read the next
``hello`` or legacy hello exhaust response.

Error Handling
--------------

If an exception occurs while sending the ``hello`` or legacy hello operation to the server, the driver MUST generate a ``ServerHeartbeatFailedEvent`` and "server heartbeat failed"
log message with the exception or message and re-raise the exception. The SDAM mandated retry of the ``hello`` or legacy hello call should be visible to consumers.

Topology IDs
------------

These MUST be a unique value that is specific to the Topology for which the events and log messages are emitted. The language may decide how to generate the value and what type the value is,
as long as it is unique to the Topology. The ID MUST be created once when the Topology is created and remain the same until the Topology is destroyed.


Initial Server Description
--------------------------

``ServerDescription`` objects MUST be initialized with a default description in an “unknown” state, guaranteeing that the previous description in the events and log messages will never be null.

----------
Events API
----------

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
     - Published when the server monitor's connection is closed and the server is shutdown.
   * - ``TopologyClosedEvent``
     - When a topology is shut down - this MUST be the last SDAM event fired.
   * - ``ServerHeartbeatStartedEvent``
     - Published when the server monitor sends its ``hello`` or legacy hello call to the server.
   * - ``ServerHeartbeatSucceededEvent``
     - Published on successful completion of the server monitor's ``hello`` or legacy hello call.
   * - ``ServerHeartbeatFailedEvent``
     - Published on failure of the server monitor's ``hello`` or legacy hello call, either with an ok: 0 result or a socket exception from the connection.


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
   * Fired when the server monitor's ``hello`` or legacy hello command is started - immediately before
   * the ``hello`` or legacy hello command is serialized into raw BSON and written to the socket.
   */
  interface ServerHeartbeatStartedEvent {

   /**
     * Returns the connection id for the command. The connection id is the unique
     * identifier of the driver's Connection object that wraps the socket. For languages that
     * do not have this object, this MUST a string of “hostname:port” or an object that
     * that contains the hostname and port as attributes.
     *
     * The name of this field is flexible to match the object that is returned from the driver.
     * Examples are, but not limited to, 'address', 'serverAddress', 'connectionId',
     */
    connectionId: ConnectionId;

   /**
     * Determines if this heartbeat event is for an awaitable ``hello`` or legacy hello.
     */
    awaited: Boolean;

  }

  /**
   * Fired when the server monitor's ``hello`` or legacy hello succeeds.
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
   * Fired when the server monitor's ``hello`` or legacy hello fails, either with an “ok: 0” or a socket exception.
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


The ``TopologyDescription`` object MUST expose the new methods defined in the API below, in order for subscribers to take action on certain conditions based on the driver options.

``TopologyDescription`` objects MAY have additional methods and properties.

.. code:: typescript

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

The following table describes the rules for determining if a topology type has readable or
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
| LoadBalanced          | ``true``                               | ``true``                               |
+-----------------------+----------------------------------------+----------------------------------------+

------------
Log Messages
------------
Please refer to the `logging specification <../logging/logging.rst>`_ for details on logging implementations in general, including log levels, log
components, and structured versus unstructured logging.

Drivers MUST support logging of SDAM information via the following types of log messages. These messages MUST be logged at ``Debug`` level and use
the ``topology`` log component.

A number of the log messages are intended to match the information contained in the events above. However, note that a log message regarding a server
description change (which would correspond to ``ServerDescriptionChangedEvent``) has been intentionally omitted since the information it would contain
is redundant with ``TopologyDescriptionChangedEvent`` and the equivalent log message.

Drivers MAY implement SDAM logging support via an event subscriber if it is convenient to do so.

The types used in the structured message definitions below are demonstrative, and drivers MAY use similar types instead so long as the information
is present (e.g. a double instead of an integer, or a string instead of an integer if the structured logging framework does not support numeric types.)

Common Fields
-------------
The following key-value pairs are common to all or several log messages and MUST be included in the "applicable messages":

.. list-table::
   :header-rows: 1
   :widths: 1 1 1 1

   * - Key
     - Applicable Messages
     - Suggested Type
     - Value

   * - topologyId
     - All messages
     - Flexible
     - The driver's unique ID for this topology as discussed in `Topology IDs <#topology-ids>`_. The type
       is flexible depending on the driver's choice of type for topology ID. 

   * - serverHost
     - Log messages specific to a particular server, including heartbeat-related messages
     - String
     - The hostname, IP address, or Unix domain socket path for the endpoint the pool is for.

   * - serverPort
     - Log messages specific to a particular server, including heartbeat-related messages
     - Int
     - (Only present for server-specific log messages) The port for the endpoint the pool is for. Optional; not present for Unix domain sockets. When
       the user does not specify a port and the default (27017) is used, the driver SHOULD include it here. 

   * - driverConnectionId
     - Heartbeat-related log messages 
     - Int
     - The driver-generated ID for the monitoring connection as defined in the 
       `connection monitoring and pooling specification <../connection-monitoring-and-pooling/connection-monitoring-and-pooling.rst>`_. Unlike
       ``connectionId`` in the above events, this field MUST NOT contain the host/port; that information MUST be in the above fields,
       ``serverHost`` and ``serverPort``. This field is optional for drivers that do not implement CMAP if they do have an equivalent concept of
       a connection ID.

   * - serverConnectionId
     - Heartbeat-related log messages
     - Int
     - The server's ID for the monitoring connection, if known. This value will be unknown and can be omitted in certain cases, e.g. the first
       "heartbeat started" message for a monitoring connection. Only present on server versions 4.2+.

"Starting Topology Monitoring" Log Message
------------------------------------------
This message MUST be published under the same circumstances as a ``TopologyOpeningEvent`` as detailed in `Events API <#events-api>`_.

In addition to the relevant common fields, these messages MUST contain the following key-value pair:

.. list-table::
   :header-rows: 1
   :widths: 1 1 1

   * - Key
     - Suggested Type
     - Value

   * - message
     - String
     - "Starting topology monitoring"

The unstructured form SHOULD be as follows, using the values defined in the structured format above to fill in placeholders as appropriate:

  Starting monitoring for topology with ID {{topologyId}}

"Stopped Topology Monitoring" Log Message
------------------------------------------
This message MUST be published under the same circumstances as a ``TopologyClosedEvent`` as detailed in `Events API <#events-api>`_.

In addition to the relevant common fields, these messages MUST contain the following key-value pair:

.. list-table::
   :header-rows: 1
   :widths: 1 1 1

   * - Key
     - Suggested Type
     - Value

   * - message
     - String
     - "Stopped topology monitoring"

The unstructured form SHOULD be as follows, using the values defined in the structured format above to fill in placeholders as appropriate:

  Stopped monitoring for topology with ID {{topologyId}}

"Starting Server Monitoring" Log Message
----------------------------------------
This message MUST be published under the same circumstances as a ``ServerOpeningEvent`` as detailed in `Events API <#events-api>`_.

In addition to the relevant common fields, these messages MUST contain the following key-value pair:

.. list-table::
   :header-rows: 1
   :widths: 1 1 1

   * - Key
     - Suggested Type
     - Value

   * - message
     - String
     - "Starting server monitoring"

The unstructured form SHOULD be as follows, using the values defined in the structured format above to fill in placeholders as appropriate:

  Starting monitoring for server {{serverHost}}:{{serverPort}} in topology with ID {{topologyId}}

"Stopped Server Monitoring" Log Message
----------------------------------------
This message MUST be published under the same circumstances as a ``ServerClosedEvent`` as detailed in `Events API <#events-api>`_.

In addition to the relevant common fields, these messages MUST contain the following key-value pair:

.. list-table::
   :header-rows: 1
   :widths: 1 1 1

   * - Key
     - Suggested Type
     - Value

   * - message
     - String
     - "Stopped server monitoring"

The unstructured form SHOULD be as follows, using the values defined in the structured format above to fill in placeholders as appropriate:

  Stopped monitoring for server {{serverHost}}:{{serverPort}} in topology with ID {{topologyId}}

"Topology Description Changed" Log Message
------------------------------------------
This message MUST be published under the same circumstances as a ``TopologyDescriptionChangedEvent`` as detailed in `Events API <#events-api>`.

In addition to the relevant common fields, these messages MUST contain the following key-value pairs:

.. list-table::
   :header-rows: 1
   :widths: 1 1 1

   * - Key
     - Suggested Type
     - Value

   * - message
     - String
     - "Topology description changed"

   * - previousDescription
     - String 
     - A string representation of the previous description of the topology. The format is flexible and could be e.g. the ``toString()`` implementation
       for a driver's topology description type, or an extended JSON representation of the topology object.

   * - newDescription
     - String 
     - A string representation of the new description of the server. The format is flexible and could be e.g. the ``toString()`` implementation
       for a driver's topology description type, or an extended JSON representation of the topology object.

The unstructured form SHOULD be as follows, using the values defined in the structured format above to fill in placeholders as appropriate:

  Description changed for topology with ID {{topologyId}}. Previous description: {{previousDescription}}. New description: {{newDescription}}

"Server Heartbeat Started" Log Message
--------------------------------------
This message MUST be published under the same circumstances as a ``ServerHeartbeatStartedEvent`` as detailed in `Events API <#events-api>`_.

In addition to the relevant common fields, these messages MUST contain the following key-value pairs:

.. list-table::
   :header-rows: 1
   :widths: 1 1 1

   * - Key
     - Suggested Type
     - Value

   * - message
     - String
     - "Server heartbeat started"

   * - awaited
     - Boolean 
     - Whether this log message is for an awaitable hello or legacy "hello".

The unstructured form SHOULD be as follows, using the values defined in the structured format above to fill in placeholders as appropriate:

  Heartbeat started for {{serverHost}}:{{serverPort}} on connection with driver-generated ID {{driverConnectionId}} and server-generated ID
  {{serverConnectionId}} in topology with ID {{topologyId}}. Awaited: {{awaited}}

"Server Heartbeat Succeeded" Log Message
----------------------------------------
This message MUST be published under the same circumstances as a ``ServerHeartbeatSucceededEvent`` as detailed in `Events API <#events-api>`_.

In addition to the relevant common fields, these messages MUST contain the following key-value pairs:

.. list-table::
   :header-rows: 1
   :widths: 1 1 1

   * - Key
     - Suggested Type
     - Value

   * - message
     - String
     - "Server heartbeat succeeded"

   * - awaited
     - Boolean 
     - Whether this log message is for an awaitable hello or legacy "hello".

   * - durationMS
     - Int
     - The execution time for the heartbeat in milliseconds. See ``ServerHeartbeatSucceededEvent`` in `Events API <#events-api>`_ for details
       on calculating this value.

   * - reply
     - String
     - Relaxed extended JSON representation of the reply to the heartbeat command.     

The unstructured form SHOULD be as follows, using the values defined in the structured format above to fill in placeholders as appropriate:

  Heartbeat succeeded in {{durationMS}} ms for {{serverHost}}:{{serverPort}}  on connection with driver-generated ID {{driverConnectionId}}
  and server-generated ID {{serverConnectionId}}  in topology with ID {{topologyId}}. Awaited: {{awaited}}. Reply: {{reply}}

"Server Heartbeat Failed" Log Message
-------------------------------------
This message MUST be published under the same circumstances as a ``ServerHeartbeatFailedEvent`` as detailed in `Events API <#events-api>`_.

In addition to the relevant common fields, these messages MUST contain the following key-value pairs:

.. list-table::
   :header-rows: 1
   :widths: 1 1 1

   * - Key
     - Suggested Type
     - Value

   * - message
     - String
     - "Server heartbeat failed"

   * - awaited
     - Boolean 
     - Whether this log message is for an awaitable hello or legacy "hello".

   * - durationMS
     - Int
     - The execution time for the heartbeat in milliseconds. See ``ServerHeartbeatFailedEvent`` in `Events API <#events-api>`_ for details
       on calculating this value.

   * - failure
     - Flexible
     - The error. The type and format of this value is flexible; see the `logging specification <../logging/logging.rst#representing-errors-in-log-messages>`_ 
       for details on representing errors in log messages. If the command is considered sensitive, the error MUST be redacted and replaced with a 
       language-appropriate alternative for a redacted error, e.g. an empty string, empty document, or null.

The unstructured form SHOULD be as follows, using the values defined in the structured format above to fill in placeholders as appropriate:

  Heartbeat failed in {{durationMS}} ms for {{serverHost}}:{{serverPort}} on connection with driver-generated ID {{driverConnectionId}} and
  server-generated ID {{serverConnectionId}} in topology with ID {{topologyId}}. Awaited: {{awaited}}. Failure: {{failure}}

-----
Tests
-----

See the `README <https://github.com/mongodb/specifications/server-discovery-and-monitoring/tests/monitoring/README.rst>`_.


Changelog
=========

:2023-03-31: Renamed to include "logging" in the title. Reorganized contents and made consistent with CLAM spec, and added requirements
             for SDAM log messages. 
:2022-10-05: Remove spec front matter and reformat changelog.
:2021-05-06: Updated to use modern terminology.
:2020-04-20: Add rules for streaming heartbeat protocol and add "awaited" field to heartbeat events.
:2018:12-12: Clarified table of rules for readable/writable servers
:2016-08-31: Added table of rules for determining if topology has readable/writable servers.
:2016-10-11: TopologyDescription objects MAY have additional methods and properties.

----

.. Section for links.

.. _Server Discovery And Monitoring: server-discovery-and-monitoring.rst
