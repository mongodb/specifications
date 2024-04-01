
.. note::
  This specification has been converted to Markdown and renamed to
  `connection-monitoring-and-pooling.md <connection-monitoring-and-pooling.md>`_.  

  Use the link above to access the latest version of the specification as the
  current reStructuredText file will no longer be updated.

  Use the links below to access equivalent section names in the Markdown version of
  the specification.

####################################
`Connection Monitoring And Pooling`_
####################################

.. _connection monitoring and pooling: ./auth.md#connection-monitoring-and-pooling

`Abstract`_
***********

.. _abstract: ./auth.md#abstract

`Meta`_
*******

.. _meta: ./auth.md#meta

`Definitions`_
**************

.. _definitions: ./auth.md#definitions

`Endpoint`_
===========

.. _endpoint: ./auth.md#endpoint

`Thread`_
=========

.. _thread: ./auth.md#thread

`Behavioral Description`_
*************************

.. _behavioral description: ./auth.md#behavioral-description

`Which Drivers This Applies To`_
================================

.. _which drivers this applies to: ./auth.md#which-drivers-this-applies-to

`Detailed Design`_
******************

.. _detailed design: ./auth.md#detailed-design

`Deprecated Options`_
---------------------

.. _deprecated options: ./auth.md#deprecated-options

`Connection Pool Members`_
==========================

.. _connection pool members: ./auth.md#connection-pool-members

`Waitqueue`_
------------

.. _waitqueue: ./auth.md#waitqueue

`Connection Pool`_
------------------

.. _connection pool: ./auth.md#connection-pool

`Creating A Connection Pool`_
-----------------------------

.. _creating a connection pool: ./auth.md#creating-a-connection-pool

`Closing A Connection Pool`_
----------------------------

.. _closing a connection pool: ./auth.md#closing-a-connection-pool

`Marking A Connection Pool As Ready`_
-------------------------------------

.. _marking a connection pool as ready: ./auth.md#marking-a-connection-pool-as-ready

`Creating A Connection (internal Implementation)`_
--------------------------------------------------

.. _creating a connection (internal implementation): ./auth.md#creating-a-connection-internal-implementation

`Establishing A Connection (internal Implementation)`_
------------------------------------------------------

.. _establishing a connection (internal implementation): ./auth.md#establishing-a-connection-internal-implementation

`Closing A Connection (internal Implementation)`_
-------------------------------------------------

.. _closing a connection (internal implementation): ./auth.md#closing-a-connection-internal-implementation

`Marking A Connection As Available (internal Implementation)`_
--------------------------------------------------------------

.. _marking a connection as available (internal implementation): ./auth.md#marking-a-connection-as-available-internal-implementation

`Populating The Pool With A Connection (internal Implementation)`_
------------------------------------------------------------------

.. _populating the pool with a connection (internal implementation): ./auth.md#populating-the-pool-with-a-connection-internal-implementation

`Checking In A Connection`_
---------------------------

.. _checking in a connection: ./auth.md#checking-in-a-connection

`Clearing A Connection Pool`_
-----------------------------

.. _clearing a connection pool: ./auth.md#clearing-a-connection-pool

`Clearing A Non-load Balanced Pool`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _clearing a non-load balanced pool: ./auth.md#clearing-a-non-load-balanced-pool

`Clearing A Load Balanced Pool`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _clearing a load balanced pool: ./auth.md#clearing-a-load-balanced-pool

`Load Balancer Mode`_
---------------------

.. _load balancer mode: ./auth.md#load-balancer-mode

`Forking`_
----------

.. _forking: ./auth.md#forking

`Optional Behaviors`_
---------------------

.. _optional behaviors: ./auth.md#optional-behaviors

`Background Thread`_
^^^^^^^^^^^^^^^^^^^^

.. _background thread: ./auth.md#background-thread

`Withconnection`_
^^^^^^^^^^^^^^^^^

.. _withconnection: ./auth.md#withconnection

`Connection Pool Logging`_
==========================

.. _connection pool logging: ./auth.md#connection-pool-logging

`Common Fields`_
----------------

.. _common fields: ./auth.md#common-fields

`Pool Created Message`_
-----------------------

.. _pool created message: ./auth.md#pool-created-message

`Pool Ready Message`_
---------------------

.. _pool ready message: ./auth.md#pool-ready-message

`Pool Cleared Message`_
-----------------------

.. _pool cleared message: ./auth.md#pool-cleared-message

`Pool Closed Message`_
----------------------

.. _pool closed message: ./auth.md#pool-closed-message

`Connection Created Message`_
-----------------------------

.. _connection created message: ./auth.md#connection-created-message

`Connection Ready Message`_
---------------------------

.. _connection ready message: ./auth.md#connection-ready-message

`Connection Closed Message`_
----------------------------

.. _connection closed message: ./auth.md#connection-closed-message

`Connection Checkout Started Message`_
--------------------------------------

.. _connection checkout started message: ./auth.md#connection-checkout-started-message

`Connection Checkout Failed Message`_
-------------------------------------

.. _connection checkout failed message: ./auth.md#connection-checkout-failed-message

`Connection Checked Out`_
-------------------------

.. _connection checked out: ./auth.md#connection-checked-out

`Connection Checked In`_
------------------------

.. _connection checked in: ./auth.md#connection-checked-in

`Connection Pool Errors`_
=========================

.. _connection pool errors: ./auth.md#connection-pool-errors

`Test Plan`_
************

.. _test plan: ./auth.md#test-plan

`Design Rationale`_
*******************

.. _design rationale: ./auth.md#design-rationale

`Why Do We Set Minpoolsize Across All Members Of A Replicaset, When Most Traffic Will Be Against A Primary?`_
=============================================================================================================

.. _why do we set minpoolsize across all members of a replicaset, when most traffic will be against a primary?: ./auth.md#why-do-we-set-minpoolsize-across-all-members-of-a-replicaset-when-most-traffic-will-be-against-a-primary

`Why Do We Have Separate Connectioncreated And Connectionready Events, But Only One Connectionclosed Event?`_
=============================================================================================================

.. _why do we have separate connectioncreated and connectionready events, but only one connectionclosed event?: ./auth.md#why-do-we-have-separate-connectioncreated-and-connectionready-events-but-only-one-connectionclosed-event

`Why Are Waitqueuesize And Waitqueuemultiple Deprecated?`_
==========================================================

.. _why are waitqueuesize and waitqueuemultiple deprecated?: ./auth.md#why-are-waitqueuesize-and-waitqueuemultiple-deprecated

`Why Is Waitqueuetimeoutms Optional For Some Drivers?`_
=======================================================

.. _why is waitqueuetimeoutms optional for some drivers?: ./auth.md#why-is-waitqueuetimeoutms-optional-for-some-drivers

`Why Must Populating The Pool Require The Use Of A Background Thread Or Async I/o?`_
====================================================================================

.. _why must populating the pool require the use of a background thread or async i/o?: ./auth.md#why-must-populating-the-pool-require-the-use-of-a-background-thread-or-async-i-o

`Why Should Closing A Connection Be Non-blocking?`_
===================================================

.. _why should closing a connection be non-blocking?: ./auth.md#why-should-closing-a-connection-be-non-blocking

`Why Can The Pool Be Paused?`_
==============================

.. _why can the pool be paused?: ./auth.md#why-can-the-pool-be-paused

`Why Not Emit Poolcleared Events And Log Messages When Clearing A Paused Pool?`_
================================================================================

.. _why not emit poolcleared events and log messages when clearing a paused pool?: ./auth.md#why-not-emit-poolcleared-events-and-log-messages-when-clearing-a-paused-pool

`Why Does The Pool Need To Support Interrupting In Use Connections As Part Of Its Clear Logic?`_
================================================================================================

.. _why does the pool need to support interrupting in use connections as part of its clear logic?: ./auth.md#why-does-the-pool-need-to-support-interrupting-in-use-connections-as-part-of-its-clear-logic

`Why Don't We Configure Tcp_user_timeout?`_
===========================================

.. _why don't we configure tcp_user_timeout?: ./auth.md#why-don-t-we-configure-tcp-user-timeout

`Backwards Compatibility`_
**************************

.. _backwards compatibility: ./auth.md#backwards-compatibility

`Reference Implementations`_
****************************

.. _reference implementations: ./auth.md#reference-implementations

`Future Development`_
*********************

.. _future development: ./auth.md#future-development

`Sdam`_
=======

.. _sdam: ./auth.md#sdam

`Advanced Pooling Behaviors`_
=============================

.. _advanced pooling behaviors: ./auth.md#advanced-pooling-behaviors

`Add Support For Op_msg Exhaustallowed`_
========================================

.. _add support for op_msg exhaustallowed: ./auth.md#add-support-for-op-msg-exhaustallowed

`Changelog`_
************

.. _changelog: ./auth.md#changelog

