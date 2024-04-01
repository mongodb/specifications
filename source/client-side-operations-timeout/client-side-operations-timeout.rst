
.. note::
  This specification has been converted to Markdown and renamed to
  `client-side-operations-timeout.md <client-side-operations-timeout.md>`_.  

  Use the link above to access the latest version of the specification as the
  current reStructuredText file will no longer be updated.

  Use the links below to access equivalent section names in the Markdown version of
  the specification.

#################################
`Client Side Operations Timeout`_
#################################

.. _client side operations timeout: ./auth.md#client-side-operations-timeout

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

`Mongoclient Configuration`_
============================

.. _mongoclient configuration: ./auth.md#mongoclient-configuration

`Timeoutms`_
------------

.. _timeoutms: ./auth.md#timeoutms

`Backwards Breaking Considerations`_
------------------------------------

.. _backwards breaking considerations: ./auth.md#backwards-breaking-considerations

`Deprecations`_
---------------

.. _deprecations: ./auth.md#deprecations

`Timeout Behavior`_
===================

.. _timeout behavior: ./auth.md#timeout-behavior

`Operations`_
-------------

.. _operations: ./auth.md#operations

`Validation And Overrides`_
---------------------------

.. _validation and overrides: ./auth.md#validation-and-overrides

`Errors`_
---------

.. _errors: ./auth.md#errors

`Error Transformations`_
^^^^^^^^^^^^^^^^^^^^^^^^

.. _error transformations: ./auth.md#error-transformations

`Blocking Sections For Operation Execution`_
--------------------------------------------

.. _blocking sections for operation execution: ./auth.md#blocking-sections-for-operation-execution

`Server Selection`_
-------------------

.. _server selection: ./auth.md#server-selection

`Command Execution`_
--------------------

.. _command execution: ./auth.md#command-execution

`Batching`_
-----------

.. _batching: ./auth.md#batching

`Retryability`_
---------------

.. _retryability: ./auth.md#retryability

`Client Side Encryption`_
-------------------------

.. _client side encryption: ./auth.md#client-side-encryption

`Background Connection Pooling`_
================================

.. _background connection pooling: ./auth.md#background-connection-pooling

`Server Monitoring`_
====================

.. _server monitoring: ./auth.md#server-monitoring

`Cursors`_
==========

.. _cursors: ./auth.md#cursors

`Non-tailable Cursors`_
-----------------------

.. _non-tailable cursors: ./auth.md#non-tailable-cursors

`Tailable Cursors`_
-------------------

.. _tailable cursors: ./auth.md#tailable-cursors

`Tailable Non-awaitdata Cursors`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _tailable non-awaitdata cursors: ./auth.md#tailable-non-awaitdata-cursors

`Tailable Awaitdata Cursors`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _tailable awaitdata cursors: ./auth.md#tailable-awaitdata-cursors

`Change Streams`_
-----------------

.. _change streams: ./auth.md#change-streams

`Sessions`_
===========

.. _sessions: ./auth.md#sessions

`Session Checkout`_
-------------------

.. _session checkout: ./auth.md#session-checkout

`Convenient Transactions Api`_
------------------------------

.. _convenient transactions api: ./auth.md#convenient-transactions-api

`Gridfs Api`_
=============

.. _gridfs api: ./auth.md#gridfs-api

`Runcommand`_
=============

.. _runcommand: ./auth.md#runcommand

`Test Plan`_
************

.. _test plan: ./auth.md#test-plan

`Motivation For Change`_
************************

.. _motivation for change: ./auth.md#motivation-for-change

`Design Rationale`_
*******************

.. _design rationale: ./auth.md#design-rationale

`Timeoutms Cannot Be Changed To Unset Once It’s Specified`_
===========================================================

.. _timeoutms cannot be changed to unset once it’s specified: ./auth.md#timeoutms-cannot-be-changed-to-unset-once-its-specified

`Serverselectiontimeoutms Is Not Deprecated`_
=============================================

.. _serverselectiontimeoutms is not deprecated: ./auth.md#serverselectiontimeoutms-is-not-deprecated

`Connecttimeoutms Is Not Deprecated`_
=====================================

.. _connecttimeoutms is not deprecated: ./auth.md#connecttimeoutms-is-not-deprecated

`Timeoutms Overrides Deprecated Timeout Options`_
=================================================

.. _timeoutms overrides deprecated timeout options: ./auth.md#timeoutms-overrides-deprecated-timeout-options

`Maxtimems Is Not Added For Mongocryptd`_
=========================================

.. _maxtimems is not added for mongocryptd: ./auth.md#maxtimems-is-not-added-for-mongocryptd

`Maxtimems Accounts For Server Rtt`_
====================================

.. _maxtimems accounts for server rtt: ./auth.md#maxtimems-accounts-for-server-rtt

`Monitoring Threads Do Not Use Timeoutms`_
==========================================

.. _monitoring threads do not use timeoutms: ./auth.md#monitoring-threads-do-not-use-timeoutms

`Runcommand Behavior`_
======================

.. _runcommand behavior: ./auth.md#runcommand-behavior

`Why Don’t Drivers Use Backoff/jitter Between Retry Attempts?`_
===============================================================

.. _why don’t drivers use backoff/jitter between retry attempts?: ./auth.md#why-dont-drivers-use-backoff-jitter-between-retry-attempts

`Cursor Close() Methods Refresh Timeoutms`_
===========================================

.. _cursor close() methods refresh timeoutms: ./auth.md#cursor-close-methods-refresh-timeoutms

`Non-tailable Cursor Behavior`_
===============================

.. _non-tailable cursor behavior: ./auth.md#non-tailable-cursor-behavior

`Tailable Cursor Behavior`_
===========================

.. _tailable cursor behavior: ./auth.md#tailable-cursor-behavior

`Change Stream Behavior`_
=========================

.. _change stream behavior: ./auth.md#change-stream-behavior

`Withtransaction Communicates Timeoutms Via Clientsession`_
===========================================================

.. _withtransaction communicates timeoutms via clientsession: ./auth.md#withtransaction-communicates-timeoutms-via-clientsession

`Withtransaction Refreshes The Timeout For Aborttransaction`_
=============================================================

.. _withtransaction refreshes the timeout for aborttransaction: ./auth.md#withtransaction-refreshes-the-timeout-for-aborttransaction

`Gridfs Streams Behavior`_
==========================

.. _gridfs streams behavior: ./auth.md#gridfs-streams-behavior

`Timeoutms Cannot Be Overridden For Startsession Calls`_
========================================================

.. _timeoutms cannot be overridden for startsession calls: ./auth.md#timeoutms-cannot-be-overridden-for-startsession-calls

`Drivers Use Minimum Rtt To Short Circuit Operations`_
======================================================

.. _drivers use minimum rtt to short circuit operations: ./auth.md#drivers-use-minimum-rtt-to-short-circuit-operations

`Future Work`_
**************

.. _future work: ./auth.md#future-work

`Modify Gridfs Streams Behavior Via New Options`_
=================================================

.. _modify gridfs streams behavior via new options: ./auth.md#modify-gridfs-streams-behavior-via-new-options

`Changelog`_
************

.. _changelog: ./auth.md#changelog

