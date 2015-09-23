.. role:: javascript(code)
  :language: javascript

===============
SDAM Monitoring
===============

:Spec: 222
:Title: SDAM Monitoring
:Authors: Durran Jordan
:Status: Draft
:Type: Standards
:Minimum Server Version: 2.4
:Last Modified: September 23, 2015

.. contents::

--------

Specification
=============

The SDAM monitoring specification defines a set of behaviour in the drivers for providing runtime information about server discovery and monitoring events (SDAM) to any 3rd party library as well internal driver use, such as logging.

-----------
Definitions
-----------

META
----

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.


Terms
-----

ServerDescription
  The term ``ServerDescription`` refers to the implementation in the driver's language of a server description. See: `SDAM Specification <https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#id24>`_. The driver is NOT REQUIRED to use this name.

TopologyDescription
  The term ``TopologyDescription`` refers to the implementation in the driver's language of a topology description. See: `SDAM Specification 2119 <https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#topologydescription>`_. The driver is NOT REQUIRED to use this name.


--------
Guidance
--------

Documentation
-------------

The documentation provided in code below is merely for driver authors and SHOULD NOT be taken as required documentation for the driver.


Operations
----------

All drivers MUST implement the API. Implementation details are noted in the comments when a specific implementation is required. Within each API, all methods are REQUIRED unless noted otherwise in the comments.


Operation Parameters
--------------------

All drivers MUST include the specified parameters in each operation, with the exception of the options parameter which is OPTIONAL.


Naming
------

All drivers MUST name operations, parameters and topic names as defined in the following sections. Exceptions to this rule are noted in the appropriate section. Class and interface names may vary according to the driver and language best practices.


Publishing & Subscribing
------------------------

The driver SHOULD publish events in a manner that is standard to the driver's language publish/subscribe patterns and is not strictly mandated in this specification.


Guarantees
----------

If a server's description changes, then a ``ServerDescriptionChangedEvent`` MUST be published. If a topology's description changes then a ``TopologyDescriptionChangedEvent`` MUST be published. These both MUST include changes from an unknown state to any other state.

---
API
---

.. code:: typescript

  interface ServerDescriptionChangedEvent {

    /**
     * Returns the previous server description.
     */
    previousDescription: ServerDescription;

    /**
     * Returns the new server description.
     */
    newDescription: ServerDescription;
  }

  interface TopologyDescriptionChangedEvent {

    /**
     * Returns the previous topology description.
     */
    previousDescription: TopologyDescription;

    /**
     * Returns the new topology description.
     */
    newDescription: TopologyDescription;
  }

