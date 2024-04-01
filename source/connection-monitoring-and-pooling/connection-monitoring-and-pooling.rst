
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

.. _connection monitoring and pooling: ./connection-monitoring-and-pooling.md#connection-monitoring-and-pooling

`Abstract`_
***********

.. _abstract: ./connection-monitoring-and-pooling.md#abstract

`Meta`_
*******

.. _meta: ./connection-monitoring-and-pooling.md#meta

`Definitions`_
**************

.. _definitions: ./connection-monitoring-and-pooling.md#definitions

`Endpoint`_
===========

.. _endpoint: ./connection-monitoring-and-pooling.md#endpoint

`Thread`_
=========

.. _thread: ./connection-monitoring-and-pooling.md#thread

`Behavioral Description`_
*************************

.. _behavioral description: ./connection-monitoring-and-pooling.md#behavioral-description

`Which Drivers This Applies To`_
================================

.. _which drivers this applies to: ./connection-monitoring-and-pooling.md#which-drivers-this-applies-to

`Detailed Design`_
******************

.. _detailed design: ./connection-monitoring-and-pooling.md#detailed-design

`Deprecated Options`_
---------------------

.. _deprecated options: ./connection-monitoring-and-pooling.md#deprecated-options

`Connection Pool Members`_
==========================

.. _connection pool members: ./connection-monitoring-and-pooling.md#connection-pool-members

`Waitqueue`_
------------

.. _waitqueue: ./connection-monitoring-and-pooling.md#waitqueue

`Connection Pool`_
------------------

.. _connection pool: ./connection-monitoring-and-pooling.md#connection-pool

`Creating A Connection Pool`_
-----------------------------

.. _creating a connection pool: ./connection-monitoring-and-pooling.md#creating-a-connection-pool

`Closing A Connection Pool`_
----------------------------

.. _closing a connection pool: ./connection-monitoring-and-pooling.md#closing-a-connection-pool

`Marking A Connection Pool As Ready`_
-------------------------------------

.. _marking a connection pool as ready: ./connection-monitoring-and-pooling.md#marking-a-connection-pool-as-ready

`Creating A Connection (internal Implementation)`_
--------------------------------------------------

.. _creating a connection (internal implementation): ./connection-monitoring-and-pooling.md#creating-a-connection-internal-implementation

`Establishing A Connection (internal Implementation)`_
------------------------------------------------------

.. _establishing a connection (internal implementation): ./connection-monitoring-and-pooling.md#establishing-a-connection-internal-implementation

`Closing A Connection (internal Implementation)`_
-------------------------------------------------

.. _closing a connection (internal implementation): ./connection-monitoring-and-pooling.md#closing-a-connection-internal-implementation

`Marking A Connection As Available (internal Implementation)`_
--------------------------------------------------------------

.. _marking a connection as available (internal implementation): ./connection-monitoring-and-pooling.md#marking-a-connection-as-available-internal-implementation

`Populating The Pool With A Connection (internal Implementation)`_
------------------------------------------------------------------

.. _populating the pool with a connection (internal implementation): ./connection-monitoring-and-pooling.md#populating-the-pool-with-a-connection-internal-implementation

`Checking In A Connection`_
---------------------------

.. _checking in a connection: ./connection-monitoring-and-pooling.md#checking-in-a-connection

`Clearing A Connection Pool`_
-----------------------------

.. _clearing a connection pool: ./connection-monitoring-and-pooling.md#clearing-a-connection-pool

`Clearing A Non-load Balanced Pool`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _clearing a non-load balanced pool: ./connection-monitoring-and-pooling.md#clearing-a-non-load-balanced-pool

`Clearing A Load Balanced Pool`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _clearing a load balanced pool: ./connection-monitoring-and-pooling.md#clearing-a-load-balanced-pool

`Load Balancer Mode`_
---------------------

.. _load balancer mode: ./connection-monitoring-and-pooling.md#load-balancer-mode

`Forking`_
----------

.. _forking: ./connection-monitoring-and-pooling.md#forking

`Optional Behaviors`_
---------------------

.. _optional behaviors: ./connection-monitoring-and-pooling.md#optional-behaviors

`Background Thread`_
^^^^^^^^^^^^^^^^^^^^

.. _background thread: ./connection-monitoring-and-pooling.md#background-thread

`Withconnection`_
^^^^^^^^^^^^^^^^^

.. _withconnection: ./connection-monitoring-and-pooling.md#withconnection

`Connection Pool Logging`_
==========================

.. _connection pool logging: ./connection-monitoring-and-pooling.md#connection-pool-logging

`Common Fields`_
----------------

.. _common fields: ./connection-monitoring-and-pooling.md#common-fields

`Pool Created Message`_
-----------------------

.. _pool created message: ./connection-monitoring-and-pooling.md#pool-created-message

`Pool Ready Message`_
---------------------

.. _pool ready message: ./connection-monitoring-and-pooling.md#pool-ready-message

`Pool Cleared Message`_
-----------------------

.. _pool cleared message: ./connection-monitoring-and-pooling.md#pool-cleared-message

`Pool Closed Message`_
----------------------

.. _pool closed message: ./connection-monitoring-and-pooling.md#pool-closed-message

`Connection Created Message`_
-----------------------------

.. _connection created message: ./connection-monitoring-and-pooling.md#connection-created-message

`Connection Ready Message`_
---------------------------

.. _connection ready message: ./connection-monitoring-and-pooling.md#connection-ready-message

`Connection Closed Message`_
----------------------------

.. _connection closed message: ./connection-monitoring-and-pooling.md#connection-closed-message

`Connection Checkout Started Message`_
--------------------------------------

.. _connection checkout started message: ./connection-monitoring-and-pooling.md#connection-checkout-started-message

`Connection Checkout Failed Message`_
-------------------------------------

.. _connection checkout failed message: ./connection-monitoring-and-pooling.md#connection-checkout-failed-message

`Connection Checked Out`_
-------------------------

.. _connection checked out: ./connection-monitoring-and-pooling.md#connection-checked-out

`Connection Checked In`_
------------------------

.. _connection checked in: ./connection-monitoring-and-pooling.md#connection-checked-in

`Connection Pool Errors`_
=========================

.. _connection pool errors: ./connection-monitoring-and-pooling.md#connection-pool-errors

`Test Plan`_
************

.. _test plan: ./connection-monitoring-and-pooling.md#test-plan

`Design Rationale`_
*******************

.. _design rationale: ./connection-monitoring-and-pooling.md#design-rationale

`Why Do We Set Minpoolsize Across All Members Of A Replicaset, When Most Traffic Will Be Against A Primary?`_
=============================================================================================================

.. _why do we set minpoolsize across all members of a replicaset, when most traffic will be against a primary?: ./connection-monitoring-and-pooling.md#why-do-we-set-minpoolsize-across-all-members-of-a-replicaset-when-most-traffic-will-be-against-a-primary

`Why Do We Have Separate Connectioncreated And Connectionready Events, But Only One Connectionclosed Event?`_
=============================================================================================================

.. _why do we have separate connectioncreated and connectionready events, but only one connectionclosed event?: ./connection-monitoring-and-pooling.md#why-do-we-have-separate-connectioncreated-and-connectionready-events-but-only-one-connectionclosed-event

`Why Are Waitqueuesize And Waitqueuemultiple Deprecated?`_
==========================================================

.. _why are waitqueuesize and waitqueuemultiple deprecated?: ./connection-monitoring-and-pooling.md#why-are-waitqueuesize-and-waitqueuemultiple-deprecated

`Why Is Waitqueuetimeoutms Optional For Some Drivers?`_
=======================================================

.. _why is waitqueuetimeoutms optional for some drivers?: ./connection-monitoring-and-pooling.md#why-is-waitqueuetimeoutms-optional-for-some-drivers

`Why Must Populating The Pool Require The Use Of A Background Thread Or Async I/o?`_
====================================================================================

.. _why must populating the pool require the use of a background thread or async i/o?: ./connection-monitoring-and-pooling.md#why-must-populating-the-pool-require-the-use-of-a-background-thread-or-async-i-o

`Why Should Closing A Connection Be Non-blocking?`_
===================================================

.. _why should closing a connection be non-blocking?: ./connection-monitoring-and-pooling.md#why-should-closing-a-connection-be-non-blocking

`Why Can The Pool Be Paused?`_
==============================

.. _why can the pool be paused?: ./connection-monitoring-and-pooling.md#why-can-the-pool-be-paused

`Why Not Emit Poolcleared Events And Log Messages When Clearing A Paused Pool?`_
================================================================================

.. _why not emit poolcleared events and log messages when clearing a paused pool?: ./connection-monitoring-and-pooling.md#why-not-emit-poolcleared-events-and-log-messages-when-clearing-a-paused-pool

`Why Does The Pool Need To Support Interrupting In Use Connections As Part Of Its Clear Logic?`_
================================================================================================

.. _why does the pool need to support interrupting in use connections as part of its clear logic?: ./connection-monitoring-and-pooling.md#why-does-the-pool-need-to-support-interrupting-in-use-connections-as-part-of-its-clear-logic

`Why Don't We Configure Tcp_user_timeout?`_
===========================================

.. _why don't we configure tcp_user_timeout?: ./connection-monitoring-and-pooling.md#why-don-t-we-configure-tcp-user-timeout

`Backwards Compatibility`_
**************************

.. _backwards compatibility: ./connection-monitoring-and-pooling.md#backwards-compatibility

`Reference Implementations`_
****************************

.. _reference implementations: ./connection-monitoring-and-pooling.md#reference-implementations

`Future Development`_
*********************

.. _future development: ./connection-monitoring-and-pooling.md#future-development

`Sdam`_
=======

.. _sdam: ./connection-monitoring-and-pooling.md#sdam

`Advanced Pooling Behaviors`_
=============================

.. _advanced pooling behaviors: ./connection-monitoring-and-pooling.md#advanced-pooling-behaviors

`Add Support For Op_msg Exhaustallowed`_
========================================

.. _add support for op_msg exhaustallowed: ./connection-monitoring-and-pooling.md#add-support-for-op-msg-exhaustallowed

`Changelog`_
************

.. _changelog: ./connection-monitoring-and-pooling.md#changelog
