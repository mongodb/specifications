
.. note::
  This specification has been converted to Markdown and renamed to
  `server-selection.md <server-selection.md>`_.  

  Use the link above to access the latest version of the specification as the
  current reStructuredText file will no longer be updated.

  Use the links below to access equivalent section names in the Markdown version of
  the specification.

###################
`Server Selection`_
###################

.. _server selection: ./auth.md#server-selection

`Abstract`_
***********

.. _abstract: ./auth.md#abstract

`Meta`_
*******

.. _meta: ./auth.md#meta

`Motivation For Change`_
************************

.. _motivation for change: ./auth.md#motivation-for-change

`Specification`_
****************

.. _specification: ./auth.md#specification

`Scope And General Requirements`_
=================================

.. _scope and general requirements: ./auth.md#scope-and-general-requirements

`Terms`_
========

.. _terms: ./auth.md#terms

`Assumptions`_
==============

.. _assumptions: ./auth.md#assumptions

`Mongoclient Configuration`_
============================

.. _mongoclient configuration: ./auth.md#mongoclient-configuration

`Localthresholdms`_
-------------------

.. _localthresholdms: ./auth.md#localthresholdms

`Serverselectiontimeoutms`_
---------------------------

.. _serverselectiontimeoutms: ./auth.md#serverselectiontimeoutms

`Serverselectiontryonce`_
-------------------------

.. _serverselectiontryonce: ./auth.md#serverselectiontryonce

`Socketcheckintervalms`_
------------------------

.. _socketcheckintervalms: ./auth.md#socketcheckintervalms

`Smallestmaxstalenessseconds`_
------------------------------

.. _smallestmaxstalenessseconds: ./auth.md#smallestmaxstalenessseconds

`Serverselector`_
-----------------

.. _serverselector: ./auth.md#serverselector

`Read Preference`_
==================

.. _read preference: ./auth.md#read-preference

`Components Of A Read Preference`_
----------------------------------

.. _components of a read preference: ./auth.md#components-of-a-read-preference

`Mode`_
^^^^^^^

.. _mode: ./auth.md#mode

`Maxstalenessseconds`_
^^^^^^^^^^^^^^^^^^^^^^

.. _maxstalenessseconds: ./auth.md#maxstalenessseconds

`Tag_sets`_
^^^^^^^^^^^

.. _tag_sets: ./auth.md#tag-sets

`Hedge`_
^^^^^^^^

.. _hedge: ./auth.md#hedge

`Read Preference Configuration`_
--------------------------------

.. _read preference configuration: ./auth.md#read-preference-configuration

`Passing Read Preference To Mongos And Load Balancers`_
-------------------------------------------------------

.. _passing read preference to mongos and load balancers: ./auth.md#passing-read-preference-to-mongos-and-load-balancers

`For Op_msg:`_
^^^^^^^^^^^^^^

.. _for op_msg:: ./auth.md#for-op-msg

`For Op_query:`_
^^^^^^^^^^^^^^^^

.. _for op_query:: ./auth.md#for-op-query

`Document Structure`_
^^^^^^^^^^^^^^^^^^^^^

.. _document structure: ./auth.md#document-structure

`Use Of Read Preferences With Commands`_
----------------------------------------

.. _use of read preferences with commands: ./auth.md#use-of-read-preferences-with-commands

`Rules For Server Selection`_
=============================

.. _rules for server selection: ./auth.md#rules-for-server-selection

`Timeouts`_
-----------

.. _timeouts: ./auth.md#timeouts

`Multi-threaded Or Asynchronous Server Selection`_
--------------------------------------------------

.. _multi-threaded or asynchronous server selection: ./auth.md#multi-threaded-or-asynchronous-server-selection

`Operationcount`_
^^^^^^^^^^^^^^^^^

.. _operationcount: ./auth.md#operationcount

`Server Selection Algorithm`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _server selection algorithm: ./auth.md#server-selection-algorithm

`Single-threaded Server Selection`_
-----------------------------------

.. _single-threaded server selection: ./auth.md#single-threaded-server-selection

`Topology Type: Unknown`_
-------------------------

.. _topology type: unknown: ./auth.md#topology-type-unknown

`Topology Type: Single`_
------------------------

.. _topology type: single: ./auth.md#topology-type-single

`Topology Type: Loadbalanced`_
------------------------------

.. _topology type: loadbalanced: ./auth.md#topology-type-loadbalanced

`Topology Types: Replicasetwithprimary Or Replicasetnoprimary`_
---------------------------------------------------------------

.. _topology types: replicasetwithprimary or replicasetnoprimary: ./auth.md#topology-types-replicasetwithprimary-or-replicasetnoprimary

`Read Operations`_
^^^^^^^^^^^^^^^^^^

.. _read operations: ./auth.md#read-operations

`Write Operations`_
^^^^^^^^^^^^^^^^^^^

.. _write operations: ./auth.md#write-operations

`Topology Type: Sharded`_
-------------------------

.. _topology type: sharded: ./auth.md#topology-type-sharded

`Round Trip Times And The Latency Window`_
==========================================

.. _round trip times and the latency window: ./auth.md#round-trip-times-and-the-latency-window

`Calculation Of Average Round Trip Times`_
------------------------------------------

.. _calculation of average round trip times: ./auth.md#calculation-of-average-round-trip-times

`Filtering Suitable Servers Based On The Latency Window`_
---------------------------------------------------------

.. _filtering suitable servers based on the latency window: ./auth.md#filtering-suitable-servers-based-on-the-latency-window

`Checking An Idle Socket After Socketcheckintervalms`_
======================================================

.. _checking an idle socket after socketcheckintervalms: ./auth.md#checking-an-idle-socket-after-socketcheckintervalms

`Requests And Pinning Deprecated`_
==================================

.. _requests and pinning deprecated: ./auth.md#requests-and-pinning-deprecated

`Logging`_
==========

.. _logging: ./auth.md#logging

`Common Fields`_
----------------

.. _common fields: ./auth.md#common-fields

`"server Selection Started" Message`_
-------------------------------------

.. _"server selection started" message: ./auth.md#server-selection-started-message

`"server Selection Succeeded" Message`_
---------------------------------------

.. _"server selection succeeded" message: ./auth.md#server-selection-succeeded-message

`"server Selection Failed" Message`_
------------------------------------

.. _"server selection failed" message: ./auth.md#server-selection-failed-message

`"waiting For Suitable Server To Become Available" Message`_
------------------------------------------------------------

.. _"waiting for suitable server to become available" message: ./auth.md#waiting-for-suitable-server-to-become-available-message

`Implementation Notes`_
***********************

.. _implementation notes: ./auth.md#implementation-notes

`Modes`_
========

.. _modes: ./auth.md#modes

`Primarypreferred And Secondarypreferred`_
------------------------------------------

.. _primarypreferred and secondarypreferred: ./auth.md#primarypreferred-and-secondarypreferred

`Nearest`_
----------

.. _nearest: ./auth.md#nearest

`Tag Set Lists`_
================

.. _tag set lists: ./auth.md#tag-set-lists

`Multi-threaded Server Selection Implementation`_
=================================================

.. _multi-threaded server selection implementation: ./auth.md#multi-threaded-server-selection-implementation

`Single-threaded Server Selection Implementation`_
==================================================

.. _single-threaded server selection implementation: ./auth.md#single-threaded-server-selection-implementation

`Server Selection Errors`_
==========================

.. _server selection errors: ./auth.md#server-selection-errors

`Cursors`_
==========

.. _cursors: ./auth.md#cursors

`Sharded Transactions`_
=======================

.. _sharded transactions: ./auth.md#sharded-transactions

`The 'text' Command And Mongos`_
================================

.. _the 'text' command and mongos: ./auth.md#the-text-command-and-mongos

`Test Plan`_
************

.. _test plan: ./auth.md#test-plan

`Design Rationale`_
*******************

.. _design rationale: ./auth.md#design-rationale

`Use Of Topology Types`_
========================

.. _use of topology types: ./auth.md#use-of-topology-types

`Consistency With Mongos`_
==========================

.. _consistency with mongos: ./auth.md#consistency-with-mongos

`New Localthresholdms Configuration Option Name`_
=================================================

.. _new localthresholdms configuration option name: ./auth.md#new-localthresholdms-configuration-option-name

`Random Selection Within The Latency Window (single-threaded)`_
===============================================================

.. _random selection within the latency window (single-threaded): ./auth.md#random-selection-within-the-latency-window-single-threaded

`Operationcount-based Selection Within The Latency Window (multi-threaded Or Async)`_
=====================================================================================

.. _operationcount-based selection within the latency window (multi-threaded or async): ./auth.md#operationcount-based-selection-within-the-latency-window-multi-threaded-or-async

`The Secondaryok Wire Protocol Flag`_
=====================================

.. _the secondaryok wire protocol flag: ./auth.md#the-secondaryok-wire-protocol-flag

`General Command Method Going To Primary`_
==========================================

.. _general command method going to primary: ./auth.md#general-command-method-going-to-primary

`Average Round Trip Time Calculation`_
======================================

.. _average round trip time calculation: ./auth.md#average-round-trip-time-calculation

`Verbose Errors`_
=================

.. _verbose errors: ./auth.md#verbose-errors

`"try Once" Mode`_
==================

.. _"try once" mode: ./auth.md#try-once-mode

`What Is The Purpose Of Socketcheckintervalms?`_
================================================

.. _what is the purpose of socketcheckintervalms?: ./auth.md#what-is-the-purpose-of-socketcheckintervalms

`Backwards Compatibility`_
**************************

.. _backwards compatibility: ./auth.md#backwards-compatibility

`Questions And Answers`_
************************

.. _questions and answers: ./auth.md#questions-and-answers

`What Happened To Pinning?`_
============================

.. _what happened to pinning?: ./auth.md#what-happened-to-pinning

`Why Change From Mongos High Availablity (ha) To Random Selection?`_
====================================================================

.. _why change from mongos high availablity (ha) to random selection?: ./auth.md#why-change-from-mongos-high-availablity-ha-to-random-selection

`What Happened To Auto-retry?`_
===============================

.. _what happened to auto-retry?: ./auth.md#what-happened-to-auto-retry

`Why Is Maxstalenessseconds Applied Before Tag_sets?`_
======================================================

.. _why is maxstalenessseconds applied before tag_sets?: ./auth.md#why-is-maxstalenessseconds-applied-before-tag-sets

`References`_
*************

.. _references: ./auth.md#references

`Changelog`_
************

.. _changelog: ./auth.md#changelog

