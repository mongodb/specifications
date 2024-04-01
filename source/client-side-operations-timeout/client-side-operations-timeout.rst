
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

.. _client side operations timeout: ./client-side-operations-timeout.md#client-side-operations-timeout

`Abstract`_
***********

.. _abstract: ./client-side-operations-timeout.md#abstract

`Meta`_
*******

.. _meta: ./client-side-operations-timeout.md#meta

`Specification`_
****************

.. _specification: ./client-side-operations-timeout.md#specification

`Terms`_
========

.. _terms: ./client-side-operations-timeout.md#terms

`Mongoclient Configuration`_
============================

.. _mongoclient configuration: ./client-side-operations-timeout.md#mongoclient-configuration

`Timeoutms`_
------------

.. _timeoutms: ./client-side-operations-timeout.md#timeoutms

`Backwards Breaking Considerations`_
------------------------------------

.. _backwards breaking considerations: ./client-side-operations-timeout.md#backwards-breaking-considerations

`Deprecations`_
---------------

.. _deprecations: ./client-side-operations-timeout.md#deprecations

`Timeout Behavior`_
===================

.. _timeout behavior: ./client-side-operations-timeout.md#timeout-behavior

`Operations`_
-------------

.. _operations: ./client-side-operations-timeout.md#operations

`Validation And Overrides`_
---------------------------

.. _validation and overrides: ./client-side-operations-timeout.md#validation-and-overrides

`Errors`_
---------

.. _errors: ./client-side-operations-timeout.md#errors

`Error Transformations`_
^^^^^^^^^^^^^^^^^^^^^^^^

.. _error transformations: ./client-side-operations-timeout.md#error-transformations

`Blocking Sections For Operation Execution`_
--------------------------------------------

.. _blocking sections for operation execution: ./client-side-operations-timeout.md#blocking-sections-for-operation-execution

`Server Selection`_
-------------------

.. _server selection: ./client-side-operations-timeout.md#server-selection

`Command Execution`_
--------------------

.. _command execution: ./client-side-operations-timeout.md#command-execution

`Batching`_
-----------

.. _batching: ./client-side-operations-timeout.md#batching

`Retryability`_
---------------

.. _retryability: ./client-side-operations-timeout.md#retryability

`Client Side Encryption`_
-------------------------

.. _client side encryption: ./client-side-operations-timeout.md#client-side-encryption

`Background Connection Pooling`_
================================

.. _background connection pooling: ./client-side-operations-timeout.md#background-connection-pooling

`Server Monitoring`_
====================

.. _server monitoring: ./client-side-operations-timeout.md#server-monitoring

`Cursors`_
==========

.. _cursors: ./client-side-operations-timeout.md#cursors

`Non-tailable Cursors`_
-----------------------

.. _non-tailable cursors: ./client-side-operations-timeout.md#non-tailable-cursors

`Tailable Cursors`_
-------------------

.. _tailable cursors: ./client-side-operations-timeout.md#tailable-cursors

`Tailable Non-awaitdata Cursors`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _tailable non-awaitdata cursors: ./client-side-operations-timeout.md#tailable-non-awaitdata-cursors

`Tailable Awaitdata Cursors`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _tailable awaitdata cursors: ./client-side-operations-timeout.md#tailable-awaitdata-cursors

`Change Streams`_
-----------------

.. _change streams: ./client-side-operations-timeout.md#change-streams

`Sessions`_
===========

.. _sessions: ./client-side-operations-timeout.md#sessions

`Session Checkout`_
-------------------

.. _session checkout: ./client-side-operations-timeout.md#session-checkout

`Convenient Transactions Api`_
------------------------------

.. _convenient transactions api: ./client-side-operations-timeout.md#convenient-transactions-api

`Gridfs Api`_
=============

.. _gridfs api: ./client-side-operations-timeout.md#gridfs-api

`Runcommand`_
=============

.. _runcommand: ./client-side-operations-timeout.md#runcommand

`Test Plan`_
************

.. _test plan: ./client-side-operations-timeout.md#test-plan

`Motivation For Change`_
************************

.. _motivation for change: ./client-side-operations-timeout.md#motivation-for-change

`Design Rationale`_
*******************

.. _design rationale: ./client-side-operations-timeout.md#design-rationale

`Timeoutms Cannot Be Changed To Unset Once It’s Specified`_
===========================================================

.. _timeoutms cannot be changed to unset once it’s specified: ./client-side-operations-timeout.md#timeoutms-cannot-be-changed-to-unset-once-its-specified

`Serverselectiontimeoutms Is Not Deprecated`_
=============================================

.. _serverselectiontimeoutms is not deprecated: ./client-side-operations-timeout.md#serverselectiontimeoutms-is-not-deprecated

`Connecttimeoutms Is Not Deprecated`_
=====================================

.. _connecttimeoutms is not deprecated: ./client-side-operations-timeout.md#connecttimeoutms-is-not-deprecated

`Timeoutms Overrides Deprecated Timeout Options`_
=================================================

.. _timeoutms overrides deprecated timeout options: ./client-side-operations-timeout.md#timeoutms-overrides-deprecated-timeout-options

`Maxtimems Is Not Added For Mongocryptd`_
=========================================

.. _maxtimems is not added for mongocryptd: ./client-side-operations-timeout.md#maxtimems-is-not-added-for-mongocryptd

`Maxtimems Accounts For Server Rtt`_
====================================

.. _maxtimems accounts for server rtt: ./client-side-operations-timeout.md#maxtimems-accounts-for-server-rtt

`Monitoring Threads Do Not Use Timeoutms`_
==========================================

.. _monitoring threads do not use timeoutms: ./client-side-operations-timeout.md#monitoring-threads-do-not-use-timeoutms

`Runcommand Behavior`_
======================

.. _runcommand behavior: ./client-side-operations-timeout.md#runcommand-behavior

`Why Don’t Drivers Use Backoff/jitter Between Retry Attempts?`_
===============================================================

.. _why don’t drivers use backoff/jitter between retry attempts?: ./client-side-operations-timeout.md#why-dont-drivers-use-backoff-jitter-between-retry-attempts

`Cursor Close() Methods Refresh Timeoutms`_
===========================================

.. _cursor close() methods refresh timeoutms: ./client-side-operations-timeout.md#cursor-close-methods-refresh-timeoutms

`Non-tailable Cursor Behavior`_
===============================

.. _non-tailable cursor behavior: ./client-side-operations-timeout.md#non-tailable-cursor-behavior

`Tailable Cursor Behavior`_
===========================

.. _tailable cursor behavior: ./client-side-operations-timeout.md#tailable-cursor-behavior

`Change Stream Behavior`_
=========================

.. _change stream behavior: ./client-side-operations-timeout.md#change-stream-behavior

`Withtransaction Communicates Timeoutms Via Clientsession`_
===========================================================

.. _withtransaction communicates timeoutms via clientsession: ./client-side-operations-timeout.md#withtransaction-communicates-timeoutms-via-clientsession

`Withtransaction Refreshes The Timeout For Aborttransaction`_
=============================================================

.. _withtransaction refreshes the timeout for aborttransaction: ./client-side-operations-timeout.md#withtransaction-refreshes-the-timeout-for-aborttransaction

`Gridfs Streams Behavior`_
==========================

.. _gridfs streams behavior: ./client-side-operations-timeout.md#gridfs-streams-behavior

`Timeoutms Cannot Be Overridden For Startsession Calls`_
========================================================

.. _timeoutms cannot be overridden for startsession calls: ./client-side-operations-timeout.md#timeoutms-cannot-be-overridden-for-startsession-calls

`Drivers Use Minimum Rtt To Short Circuit Operations`_
======================================================

.. _drivers use minimum rtt to short circuit operations: ./client-side-operations-timeout.md#drivers-use-minimum-rtt-to-short-circuit-operations

`Future Work`_
**************

.. _future work: ./client-side-operations-timeout.md#future-work

`Modify Gridfs Streams Behavior Via New Options`_
=================================================

.. _modify gridfs streams behavior via new options: ./client-side-operations-timeout.md#modify-gridfs-streams-behavior-via-new-options

`Changelog`_
************

.. _changelog: ./client-side-operations-timeout.md#changelog
