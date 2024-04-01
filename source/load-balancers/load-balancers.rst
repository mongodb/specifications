
.. note::
  This specification has been converted to Markdown and renamed to
  `load-balancers.md <load-balancers.md>`_.  

  Use the link above to access the latest version of the specification as the
  current reStructuredText file will no longer be updated.

  Use the links below to access equivalent section names in the Markdown version of
  the specification.

########################
`Load Balancer Support`_
########################

.. _load balancer support: ./load-balancers.md#load-balancer-support

`Abstract`_
***********

.. _abstract: ./load-balancers.md#abstract

`Meta`_
*******

.. _meta: ./load-balancers.md#meta

`Specification`_
****************

.. _specification: ./load-balancers.md#specification

`Terms`_
========

.. _terms: ./load-balancers.md#terms

`Sdam`_
-------

.. _sdam: ./load-balancers.md#sdam

`Service`_
----------

.. _service: ./load-balancers.md#service

`Mongoclient Configuration`_
============================

.. _mongoclient configuration: ./load-balancers.md#mongoclient-configuration

`Loadbalanced`_
---------------

.. _loadbalanced: ./load-balancers.md#loadbalanced

`Uri Validation`_
-----------------

.. _uri validation: ./load-balancers.md#uri-validation

`Dns Seedlist Discovery`_
-------------------------

.. _dns seedlist discovery: ./load-balancers.md#dns-seedlist-discovery

`Server Discovery Logging And Monitoring`_
==========================================

.. _server discovery logging and monitoring: ./load-balancers.md#server-discovery-logging-and-monitoring

`Monitoring`_
-------------

.. _monitoring: ./load-balancers.md#monitoring

`Log Messages`_
---------------

.. _log messages: ./load-balancers.md#log-messages

`Driver Sessions`_
==================

.. _driver sessions: ./load-balancers.md#driver-sessions

`Session Support`_
------------------

.. _session support: ./load-balancers.md#session-support

`Session Expiration`_
---------------------

.. _session expiration: ./load-balancers.md#session-expiration

`Data-bearing Server Type`_
---------------------------

.. _data-bearing server type: ./load-balancers.md#data-bearing-server-type

`Server Selection`_
===================

.. _server selection: ./load-balancers.md#server-selection

`Connection Pooling`_
=====================

.. _connection pooling: ./load-balancers.md#connection-pooling

`Connection Establishment`_
---------------------------

.. _connection establishment: ./load-balancers.md#connection-establishment

`Connection Pinning`_
---------------------

.. _connection pinning: ./load-balancers.md#connection-pinning

`Behaviour With Cursors`_
-------------------------

.. _behaviour with cursors: ./load-balancers.md#behaviour-with-cursors

`Behaviour With Transactions`_
------------------------------

.. _behaviour with transactions: ./load-balancers.md#behaviour-with-transactions

`Connection Tracking`_
----------------------

.. _connection tracking: ./load-balancers.md#connection-tracking

`Error Handling`_
=================

.. _error handling: ./load-balancers.md#error-handling

`Initial Handshake Errors`_
---------------------------

.. _initial handshake errors: ./load-balancers.md#initial-handshake-errors

`Post-handshake Errors`_
------------------------

.. _post-handshake errors: ./load-balancers.md#post-handshake-errors

`Events`_
=========

.. _events: ./load-balancers.md#events

`Downstream Visible Behavioral Changes`_
========================================

.. _downstream visible behavioral changes: ./load-balancers.md#downstream-visible-behavioral-changes

`Q&a`_
======

.. _q&a: ./load-balancers.md#q-a

`Why Use A Connection String Option Instead Of A New Uri Scheme?`_
------------------------------------------------------------------

.. _why use a connection string option instead of a new uri scheme?: ./load-balancers.md#why-use-a-connection-string-option-instead-of-a-new-uri-scheme

`Why Explicitly Opt-in To This Behaviour Instead Of Letting Mongos Inform The Driver Of The Load Balancer?`_
------------------------------------------------------------------------------------------------------------

.. _why explicitly opt-in to this behaviour instead of letting mongos inform the driver of the load balancer?: ./load-balancers.md#why-explicitly-opt-in-to-this-behaviour-instead-of-letting-mongos-inform-the-driver-of-the-load-balancer

`Why Does This Specification Instruct Drivers To Not Check Connections Back Into The Connection Pool In Some Circumstances?`_
-----------------------------------------------------------------------------------------------------------------------------

.. _why does this specification instruct drivers to not check connections back into the connection pool in some circumstances?: ./load-balancers.md#why-does-this-specification-instruct-drivers-to-not-check-connections-back-into-the-connection-pool-in-some-circumstances

`What Reason Has A Client Side Connection Reaper For Idle Cursors Not Been Put Into This Specification?`_
---------------------------------------------------------------------------------------------------------

.. _what reason has a client side connection reaper for idle cursors not been put into this specification?: ./load-balancers.md#what-reason-has-a-client-side-connection-reaper-for-idle-cursors-not-been-put-into-this-specification

`Why Are We Requiring Mongos Servers To Add A New Serviceid Field In Hello Responses Rather Than Reusing The Existing Topologyversion.processid?`_
--------------------------------------------------------------------------------------------------------------------------------------------------

.. _why are we requiring mongos servers to add a new serviceid field in hello responses rather than reusing the existing topologyversion.processid?: ./load-balancers.md#why-are-we-requiring-mongos-servers-to-add-a-new-serviceid-field-in-hello-responses-rather-than-reusing-the-existing-topologyversion-processid

`Why Does This Specification Not Address Load Balancer Restarts Or Maintenance?`_
---------------------------------------------------------------------------------

.. _why does this specification not address load balancer restarts or maintenance?: ./load-balancers.md#why-does-this-specification-not-address-load-balancer-restarts-or-maintenance

`Design Rationales`_
====================

.. _design rationales: ./load-balancers.md#design-rationales

`Alternative Designs`_
======================

.. _alternative designs: ./load-balancers.md#alternative-designs

`Service Proxy Detection`_
--------------------------

.. _service proxy detection: ./load-balancers.md#service-proxy-detection

`Changelog`_
************

.. _changelog: ./load-balancers.md#changelog
