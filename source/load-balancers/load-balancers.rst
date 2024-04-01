
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

.. _load balancer support: ./auth.md#load-balancer-support

`Abstract`_
***********

.. _abstract: ./auth.md#abstract

`Meta`_
*******

.. _meta: ./auth.md#meta

`Specification`_
****************

.. _specification: ./auth.md#specification

`Terms`_
========

.. _terms: ./auth.md#terms

`Sdam`_
-------

.. _sdam: ./auth.md#sdam

`Service`_
----------

.. _service: ./auth.md#service

`Mongoclient Configuration`_
============================

.. _mongoclient configuration: ./auth.md#mongoclient-configuration

`Loadbalanced`_
---------------

.. _loadbalanced: ./auth.md#loadbalanced

`Uri Validation`_
-----------------

.. _uri validation: ./auth.md#uri-validation

`Dns Seedlist Discovery`_
-------------------------

.. _dns seedlist discovery: ./auth.md#dns-seedlist-discovery

`Server Discovery Logging And Monitoring`_
==========================================

.. _server discovery logging and monitoring: ./auth.md#server-discovery-logging-and-monitoring

`Monitoring`_
-------------

.. _monitoring: ./auth.md#monitoring

`Log Messages`_
---------------

.. _log messages: ./auth.md#log-messages

`Driver Sessions`_
==================

.. _driver sessions: ./auth.md#driver-sessions

`Session Support`_
------------------

.. _session support: ./auth.md#session-support

`Session Expiration`_
---------------------

.. _session expiration: ./auth.md#session-expiration

`Data-bearing Server Type`_
---------------------------

.. _data-bearing server type: ./auth.md#data-bearing-server-type

`Server Selection`_
===================

.. _server selection: ./auth.md#server-selection

`Connection Pooling`_
=====================

.. _connection pooling: ./auth.md#connection-pooling

`Connection Establishment`_
---------------------------

.. _connection establishment: ./auth.md#connection-establishment

`Connection Pinning`_
---------------------

.. _connection pinning: ./auth.md#connection-pinning

`Behaviour With Cursors`_
-------------------------

.. _behaviour with cursors: ./auth.md#behaviour-with-cursors

`Behaviour With Transactions`_
------------------------------

.. _behaviour with transactions: ./auth.md#behaviour-with-transactions

`Connection Tracking`_
----------------------

.. _connection tracking: ./auth.md#connection-tracking

`Error Handling`_
=================

.. _error handling: ./auth.md#error-handling

`Initial Handshake Errors`_
---------------------------

.. _initial handshake errors: ./auth.md#initial-handshake-errors

`Post-handshake Errors`_
------------------------

.. _post-handshake errors: ./auth.md#post-handshake-errors

`Events`_
=========

.. _events: ./auth.md#events

`Downstream Visible Behavioral Changes`_
========================================

.. _downstream visible behavioral changes: ./auth.md#downstream-visible-behavioral-changes

`Q&a`_
======

.. _q&a: ./auth.md#q-a

`Why Use A Connection String Option Instead Of A New Uri Scheme?`_
------------------------------------------------------------------

.. _why use a connection string option instead of a new uri scheme?: ./auth.md#why-use-a-connection-string-option-instead-of-a-new-uri-scheme

`Why Explicitly Opt-in To This Behaviour Instead Of Letting Mongos Inform The Driver Of The Load Balancer?`_
------------------------------------------------------------------------------------------------------------

.. _why explicitly opt-in to this behaviour instead of letting mongos inform the driver of the load balancer?: ./auth.md#why-explicitly-opt-in-to-this-behaviour-instead-of-letting-mongos-inform-the-driver-of-the-load-balancer

`Why Does This Specification Instruct Drivers To Not Check Connections Back Into The Connection Pool In Some Circumstances?`_
-----------------------------------------------------------------------------------------------------------------------------

.. _why does this specification instruct drivers to not check connections back into the connection pool in some circumstances?: ./auth.md#why-does-this-specification-instruct-drivers-to-not-check-connections-back-into-the-connection-pool-in-some-circumstances

`What Reason Has A Client Side Connection Reaper For Idle Cursors Not Been Put Into This Specification?`_
---------------------------------------------------------------------------------------------------------

.. _what reason has a client side connection reaper for idle cursors not been put into this specification?: ./auth.md#what-reason-has-a-client-side-connection-reaper-for-idle-cursors-not-been-put-into-this-specification

`Why Are We Requiring Mongos Servers To Add A New Serviceid Field In Hello Responses Rather Than Reusing The Existing Topologyversion.processid?`_
--------------------------------------------------------------------------------------------------------------------------------------------------

.. _why are we requiring mongos servers to add a new serviceid field in hello responses rather than reusing the existing topologyversion.processid?: ./auth.md#why-are-we-requiring-mongos-servers-to-add-a-new-serviceid-field-in-hello-responses-rather-than-reusing-the-existing-topologyversion-processid

`Why Does This Specification Not Address Load Balancer Restarts Or Maintenance?`_
---------------------------------------------------------------------------------

.. _why does this specification not address load balancer restarts or maintenance?: ./auth.md#why-does-this-specification-not-address-load-balancer-restarts-or-maintenance

`Design Rationales`_
====================

.. _design rationales: ./auth.md#design-rationales

`Alternative Designs`_
======================

.. _alternative designs: ./auth.md#alternative-designs

`Service Proxy Detection`_
--------------------------

.. _service proxy detection: ./auth.md#service-proxy-detection

`Changelog`_
************

.. _changelog: ./auth.md#changelog

