
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

.. _server selection: ./server-selection.md#server-selection

`Abstract`_
***********

.. _abstract: ./server-selection.md#abstract

`Meta`_
*******

.. _meta: ./server-selection.md#meta

`Motivation For Change`_
************************

.. _motivation for change: ./server-selection.md#motivation-for-change

`Specification`_
****************

.. _specification: ./server-selection.md#specification

`Scope And General Requirements`_
=================================

.. _scope and general requirements: ./server-selection.md#scope-and-general-requirements

`Terms`_
========

.. _terms: ./server-selection.md#terms

`Assumptions`_
==============

.. _assumptions: ./server-selection.md#assumptions

`Mongoclient Configuration`_
============================

.. _mongoclient configuration: ./server-selection.md#mongoclient-configuration

`Localthresholdms`_
-------------------

.. _localthresholdms: ./server-selection.md#localthresholdms

`Serverselectiontimeoutms`_
---------------------------

.. _serverselectiontimeoutms: ./server-selection.md#serverselectiontimeoutms

`Serverselectiontryonce`_
-------------------------

.. _serverselectiontryonce: ./server-selection.md#serverselectiontryonce

`Socketcheckintervalms`_
------------------------

.. _socketcheckintervalms: ./server-selection.md#socketcheckintervalms

`Smallestmaxstalenessseconds`_
------------------------------

.. _smallestmaxstalenessseconds: ./server-selection.md#smallestmaxstalenessseconds

`Serverselector`_
-----------------

.. _serverselector: ./server-selection.md#serverselector

`Read Preference`_
==================

.. _read preference: ./server-selection.md#read-preference

`Components Of A Read Preference`_
----------------------------------

.. _components of a read preference: ./server-selection.md#components-of-a-read-preference

`Mode`_
^^^^^^^

.. _mode: ./server-selection.md#mode

`Maxstalenessseconds`_
^^^^^^^^^^^^^^^^^^^^^^

.. _maxstalenessseconds: ./server-selection.md#maxstalenessseconds

`Tag_sets`_
^^^^^^^^^^^

.. _tag_sets: ./server-selection.md#tag-sets

`Hedge`_
^^^^^^^^

.. _hedge: ./server-selection.md#hedge

`Read Preference Configuration`_
--------------------------------

.. _read preference configuration: ./server-selection.md#read-preference-configuration

`Passing Read Preference To Mongos And Load Balancers`_
-------------------------------------------------------

.. _passing read preference to mongos and load balancers: ./server-selection.md#passing-read-preference-to-mongos-and-load-balancers

`For Op_msg:`_
^^^^^^^^^^^^^^

.. _for op_msg: ./server-selection.md#for-op-msg

`For Op_query:`_
^^^^^^^^^^^^^^^^

.. _for op_query: ./server-selection.md#for-op-query

`Document Structure`_
^^^^^^^^^^^^^^^^^^^^^

.. _document structure: ./server-selection.md#document-structure

`Use Of Read Preferences With Commands`_
----------------------------------------

.. _use of read preferences with commands: ./server-selection.md#use-of-read-preferences-with-commands

`Rules For Server Selection`_
=============================

.. _rules for server selection: ./server-selection.md#rules-for-server-selection

`Timeouts`_
-----------

.. _timeouts: ./server-selection.md#timeouts

`Multi-threaded Or Asynchronous Server Selection`_
--------------------------------------------------

.. _multi-threaded or asynchronous server selection: ./server-selection.md#multi-threaded-or-asynchronous-server-selection

`Operationcount`_
^^^^^^^^^^^^^^^^^

.. _operationcount: ./server-selection.md#operationcount

`Server Selection Algorithm`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _server selection algorithm: ./server-selection.md#server-selection-algorithm

`Single-threaded Server Selection`_
-----------------------------------

.. _single-threaded server selection: ./server-selection.md#single-threaded-server-selection

`Topology Type: Unknown`_
-------------------------

.. _topology type unknown: ./server-selection.md#topology-type-unknown

`Topology Type: Single`_
------------------------

.. _topology type single: ./server-selection.md#topology-type-single

`Topology Type: Loadbalanced`_
------------------------------

.. _topology type loadbalanced: ./server-selection.md#topology-type-loadbalanced

`Topology Types: Replicasetwithprimary Or Replicasetnoprimary`_
---------------------------------------------------------------

.. _topology types: replicasetwithprimary or replicasetnoprimary: ./server-selection.md#topology-types-replicasetwithprimary-or-replicasetnoprimary

`Read Operations`_
^^^^^^^^^^^^^^^^^^

.. _read operations: ./server-selection.md#read-operations

`Write Operations`_
^^^^^^^^^^^^^^^^^^^

.. _write operations: ./server-selection.md#write-operations

`Topology Type: Sharded`_
-------------------------

.. _topology type: sharded: ./server-selection.md#topology-type-sharded

`Round Trip Times And The Latency Window`_
==========================================

.. _round trip times and the latency window: ./server-selection.md#round-trip-times-and-the-latency-window

`Calculation Of Average Round Trip Times`_
------------------------------------------

.. _calculation of average round trip times: ./server-selection.md#calculation-of-average-round-trip-times

`Filtering Suitable Servers Based On The Latency Window`_
---------------------------------------------------------

.. _filtering suitable servers based on the latency window: ./server-selection.md#filtering-suitable-servers-based-on-the-latency-window

`Checking An Idle Socket After Socketcheckintervalms`_
======================================================

.. _checking an idle socket after socketcheckintervalms: ./server-selection.md#checking-an-idle-socket-after-socketcheckintervalms

`Requests And Pinning Deprecated`_
==================================

.. _requests and pinning deprecated: ./server-selection.md#requests-and-pinning-deprecated

`Logging`_
==========

.. _logging: ./server-selection.md#logging

`Common Fields`_
----------------

.. _common fields: ./server-selection.md#common-fields

`"server Selection Started" Message`_
-------------------------------------

.. _"server selection started" message: ./server-selection.md#server-selection-started-message

`"server Selection Succeeded" Message`_
---------------------------------------

.. _"server selection succeeded" message: ./server-selection.md#server-selection-succeeded-message

`"server Selection Failed" Message`_
------------------------------------

.. _"server selection failed" message: ./server-selection.md#server-selection-failed-message

`"waiting For Suitable Server To Become Available" Message`_
------------------------------------------------------------

.. _"waiting for suitable server to become available" message: ./server-selection.md#waiting-for-suitable-server-to-become-available-message

`Implementation Notes`_
***********************

.. _implementation notes: ./server-selection.md#implementation-notes

`Modes`_
========

.. _modes: ./server-selection.md#modes

`Primarypreferred And Secondarypreferred`_
------------------------------------------

.. _primarypreferred and secondarypreferred: ./server-selection.md#primarypreferred-and-secondarypreferred

`Nearest`_
----------

.. _nearest: ./server-selection.md#nearest

`Tag Set Lists`_
================

.. _tag set lists: ./server-selection.md#tag-set-lists

`Multi-threaded Server Selection Implementation`_
=================================================

.. _multi-threaded server selection implementation: ./server-selection.md#multi-threaded-server-selection-implementation

`Single-threaded Server Selection Implementation`_
==================================================

.. _single-threaded server selection implementation: ./server-selection.md#single-threaded-server-selection-implementation

`Server Selection Errors`_
==========================

.. _server selection errors: ./server-selection.md#server-selection-errors

`Cursors`_
==========

.. _cursors: ./server-selection.md#cursors

`Sharded Transactions`_
=======================

.. _sharded transactions: ./server-selection.md#sharded-transactions

`The 'text' Command And Mongos`_
================================

.. _the 'text' command and mongos: ./server-selection.md#the-text-command-and-mongos

`Test Plan`_
************

.. _test plan: ./server-selection.md#test-plan

`Design Rationale`_
*******************

.. _design rationale: ./server-selection.md#design-rationale

`Use Of Topology Types`_
========================

.. _use of topology types: ./server-selection.md#use-of-topology-types

`Consistency With Mongos`_
==========================

.. _consistency with mongos: ./server-selection.md#consistency-with-mongos

`New Localthresholdms Configuration Option Name`_
=================================================

.. _new localthresholdms configuration option name: ./server-selection.md#new-localthresholdms-configuration-option-name

`Random Selection Within The Latency Window (single-threaded)`_
===============================================================

.. _random selection within the latency window (single-threaded): ./server-selection.md#random-selection-within-the-latency-window-single-threaded

`Operationcount-based Selection Within The Latency Window (multi-threaded Or Async)`_
=====================================================================================

.. _operationcount-based selection within the latency window (multi-threaded or async): ./server-selection.md#operationcount-based-selection-within-the-latency-window-multi-threaded-or-async

`The Secondaryok Wire Protocol Flag`_
=====================================

.. _the secondaryok wire protocol flag: ./server-selection.md#the-secondaryok-wire-protocol-flag

`General Command Method Going To Primary`_
==========================================

.. _general command method going to primary: ./server-selection.md#general-command-method-going-to-primary

`Average Round Trip Time Calculation`_
======================================

.. _average round trip time calculation: ./server-selection.md#average-round-trip-time-calculation

`Verbose Errors`_
=================

.. _verbose errors: ./server-selection.md#verbose-errors

`"try Once" Mode`_
==================

.. _"try once" mode: ./server-selection.md#try-once-mode

`What Is The Purpose Of Socketcheckintervalms?`_
================================================

.. _what is the purpose of socketcheckintervalms?: ./server-selection.md#what-is-the-purpose-of-socketcheckintervalms

`Backwards Compatibility`_
**************************

.. _backwards compatibility: ./server-selection.md#backwards-compatibility

`Questions And Answers`_
************************

.. _questions and answers: ./server-selection.md#questions-and-answers

`What Happened To Pinning?`_
============================

.. _what happened to pinning?: ./server-selection.md#what-happened-to-pinning

`Why Change From Mongos High Availablity (ha) To Random Selection?`_
====================================================================

.. _why change from mongos high availablity (ha) to random selection?: ./server-selection.md#why-change-from-mongos-high-availablity-ha-to-random-selection

`What Happened To Auto-retry?`_
===============================

.. _what happened to auto-retry?: ./server-selection.md#what-happened-to-auto-retry

`Why Is Maxstalenessseconds Applied Before Tag_sets?`_
======================================================

.. _why is maxstalenessseconds applied before tag_sets?: ./server-selection.md#why-is-maxstalenessseconds-applied-before-tag-sets

`References`_
*************

.. _references: ./server-selection.md#references

`Changelog`_
************

.. _changelog: ./server-selection.md#changelog
