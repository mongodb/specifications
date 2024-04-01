
.. note::
  This specification has been converted to Markdown and renamed to
  `transactions.md <transactions.md>`_.  

  Use the link above to access the latest version of the specification as the
  current reStructuredText file will no longer be updated.

  Use the links below to access equivalent section names in the Markdown version of
  the specification.

####################################
`Driver Transactions Specification`_
####################################

.. _driver transactions specification: ./auth.md#driver-transactions-specification

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

`Resource Management Block`_
----------------------------

.. _resource management block: ./auth.md#resource-management-block

`Read Operation`_
-----------------

.. _read operation: ./auth.md#read-operation

`Write Operation`_
------------------

.. _write operation: ./auth.md#write-operation

`Retryable Error`_
------------------

.. _retryable error: ./auth.md#retryable-error

`Command Error`_
----------------

.. _command error: ./auth.md#command-error

`Network Error`_
----------------

.. _network error: ./auth.md#network-error

`Error Label`_
--------------

.. _error label: ./auth.md#error-label

`Transient Transaction Error`_
------------------------------

.. _transient transaction error: ./auth.md#transient-transaction-error

`Naming Variations`_
====================

.. _naming variations: ./auth.md#naming-variations

`Transaction Api`_
==================

.. _transaction api: ./auth.md#transaction-api

`Transactionoptions`_
=====================

.. _transactionoptions: ./auth.md#transactionoptions

`Readconcern`_
--------------

.. _readconcern: ./auth.md#readconcern

`Writeconcern`_
---------------

.. _writeconcern: ./auth.md#writeconcern

`Readpreference`_
-----------------

.. _readpreference: ./auth.md#readpreference

`Maxcommittimems`_
------------------

.. _maxcommittimems: ./auth.md#maxcommittimems

`Sessionoptions Changes`_
=========================

.. _sessionoptions changes: ./auth.md#sessionoptions-changes

`Defaulttransactionoptions`_
----------------------------

.. _defaulttransactionoptions: ./auth.md#defaulttransactionoptions

`Clientsession Changes`_
========================

.. _clientsession changes: ./auth.md#clientsession-changes

`Starttransaction`_
-------------------

.. _starttransaction: ./auth.md#starttransaction

`Endsession Changes`_
---------------------

.. _endsession changes: ./auth.md#endsession-changes

`Error Reporting Changes`_
==========================

.. _error reporting changes: ./auth.md#error-reporting-changes

`Transactions Wire Protocol`_
*****************************

.. _transactions wire protocol: ./auth.md#transactions-wire-protocol

`Constructing Commands Within A Transaction`_
=============================================

.. _constructing commands within a transaction: ./auth.md#constructing-commands-within-a-transaction

`Behavior Of The Starttransaction Field`_
-----------------------------------------

.. _behavior of the starttransaction field: ./auth.md#behavior-of-the-starttransaction-field

`Behavior Of The Autocommit Field`_
-----------------------------------

.. _behavior of the autocommit field: ./auth.md#behavior-of-the-autocommit-field

`Behavior Of The Readconcern Field`_
------------------------------------

.. _behavior of the readconcern field: ./auth.md#behavior-of-the-readconcern-field

`Behavior Of The Writeconcern Field`_
-------------------------------------

.. _behavior of the writeconcern field: ./auth.md#behavior-of-the-writeconcern-field

`Behavior Of The Recoverytoken Field`_
--------------------------------------

.. _behavior of the recoverytoken field: ./auth.md#behavior-of-the-recoverytoken-field

`Constructing The First Command Within A Transaction`_
------------------------------------------------------

.. _constructing the first command within a transaction: ./auth.md#constructing-the-first-command-within-a-transaction

`Constructing Any Other Command Within A Transaction`_
------------------------------------------------------

.. _constructing any other command within a transaction: ./auth.md#constructing-any-other-command-within-a-transaction

`Generic Runcommand Helper Within A Transaction`_
-------------------------------------------------

.. _generic runcommand helper within a transaction: ./auth.md#generic-runcommand-helper-within-a-transaction

`Interaction With Causal Consistency`_
======================================

.. _interaction with causal consistency: ./auth.md#interaction-with-causal-consistency

`Interaction With Retryable Writes`_
====================================

.. _interaction with retryable writes: ./auth.md#interaction-with-retryable-writes

`Server Commands`_
==================

.. _server commands: ./auth.md#server-commands

`Sharded Transactions`_
***********************

.. _sharded transactions: ./auth.md#sharded-transactions

`Mongos Pinning`_
=================

.. _mongos pinning: ./auth.md#mongos-pinning

`When To Unpin`_
----------------

.. _when to unpin: ./auth.md#when-to-unpin

`Pinning In Load Balancer Mode`_
--------------------------------

.. _pinning in load balancer mode: ./auth.md#pinning-in-load-balancer-mode

`Recoverytoken Field`_
======================

.. _recoverytoken field: ./auth.md#recoverytoken-field

`Error Reporting And Retrying Transactions`_
********************************************

.. _error reporting and retrying transactions: ./auth.md#error-reporting-and-retrying-transactions

`Error Labels`_
===============

.. _error labels: ./auth.md#error-labels

`Transienttransactionerror`_
============================

.. _transienttransactionerror: ./auth.md#transienttransactionerror

`Retrying Transactions That Fail With Transienttransactionerror`_
-----------------------------------------------------------------

.. _retrying transactions that fail with transienttransactionerror: ./auth.md#retrying-transactions-that-fail-with-transienttransactionerror

`Unknowntransactioncommitresult`_
=================================

.. _unknowntransactioncommitresult: ./auth.md#unknowntransactioncommitresult

`Retrying Committransaction`_
-----------------------------

.. _retrying committransaction: ./auth.md#retrying-committransaction

`Handling Command Errors`_
**************************

.. _handling command errors: ./auth.md#handling-command-errors

`Test Plan`_
************

.. _test plan: ./auth.md#test-plan

`Design Rationale`_
*******************

.. _design rationale: ./auth.md#design-rationale

`Drivers Ignore All Aborttransaction Errors`_
=============================================

.. _drivers ignore all aborttransaction errors: ./auth.md#drivers-ignore-all-aborttransaction-errors

`Drivers Add The "transienttransactionerror" Label To Network Errors`_
======================================================================

.. _drivers add the "transienttransactionerror" label to network errors: ./auth.md#drivers-add-the-transienttransactionerror-label-to-network-errors

`Transactions In Gridfs`_
=========================

.. _transactions in gridfs: ./auth.md#transactions-in-gridfs

`Causal Consistency With Runcommand Helper`_
============================================

.. _causal consistency with runcommand helper: ./auth.md#causal-consistency-with-runcommand-helper

`Calling Committransaction With The Generic Runcommand Helper Is Undefined Behavior`_
=====================================================================================

.. _calling committransaction with the generic runcommand helper is undefined behavior: ./auth.md#calling-committransaction-with-the-generic-runcommand-helper-is-undefined-behavior

`Dependencies`_
***************

.. _dependencies: ./auth.md#dependencies

`Backwards Compatibility`_
**************************

.. _backwards compatibility: ./auth.md#backwards-compatibility

`Reference Implementation`_
***************************

.. _reference implementation: ./auth.md#reference-implementation

`Future Work`_
**************

.. _future work: ./auth.md#future-work

`Justifications`_
*****************

.. _justifications: ./auth.md#justifications

`Why Is There No Transaction Object?`_
======================================

.. _why is there no transaction object?: ./auth.md#why-is-there-no-transaction-object

`Why Is Readpreference Part Of Transactionoptions?`_
====================================================

.. _why is readpreference part of transactionoptions?: ./auth.md#why-is-readpreference-part-of-transactionoptions

`Users Cannot Pass Readconcern Or Writeconcern To Operations In Transactions`_
==============================================================================

.. _users cannot pass readconcern or writeconcern to operations in transactions: ./auth.md#users-cannot-pass-readconcern-or-writeconcern-to-operations-in-transactions

`Aggregate With Write Stage Is A Read Operation`_
=================================================

.. _aggregate with write stage is a read operation: ./auth.md#aggregate-with-write-stage-is-a-read-operation

`A Server Selection Error Is Labeled Unknowntransactioncommitresult`_
=====================================================================

.. _a server selection error is labeled unknowntransactioncommitresult: ./auth.md#a-server-selection-error-is-labeled-unknowntransactioncommitresult

`Faq`_
******

.. _faq: ./auth.md#faq

`What Commands Can Be Run In A Transaction?`_
=============================================

.. _what commands can be run in a transaction?: ./auth.md#what-commands-can-be-run-in-a-transaction

`Why Don’t Drivers Automatically Retry Commit After A Write Concern Timeout Error?`_
====================================================================================

.. _why don’t drivers automatically retry commit after a write concern timeout error?: ./auth.md#why-dont-drivers-automatically-retry-commit-after-a-write-concern-timeout-error

`What Happens When A Command Object Passed To Runcommand Already Contains A Transaction Field (eg. Lsid, Txnnumber, Etc...)?`_
==============================================================================================================================

.. _what happens when a command object passed to runcommand already contains a transaction field (eg. lsid, txnnumber, etc...)?: ./auth.md#what-happens-when-a-command-object-passed-to-runcommand-already-contains-a-transaction-field-eg-lsid-txnnumber-etc

`Majority Write Concern Is Used When Retrying Committransaction`_
=================================================================

.. _majority write concern is used when retrying committransaction: ./auth.md#majority-write-concern-is-used-when-retrying-committransaction

`Changelog`_
************

.. _changelog: ./auth.md#changelog

