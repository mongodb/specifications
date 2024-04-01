
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

.. _driver transactions specification: ./transactions.md#driver-transactions-specification

`Abstract`_
***********

.. _abstract: ./transactions.md#abstract

`Meta`_
*******

.. _meta: ./transactions.md#meta

`Specification`_
****************

.. _specification: ./transactions.md#specification

`Terms`_
========

.. _terms: ./transactions.md#terms

`Resource Management Block`_
----------------------------

.. _resource management block: ./transactions.md#resource-management-block

`Read Operation`_
-----------------

.. _read operation: ./transactions.md#read-operation

`Write Operation`_
------------------

.. _write operation: ./transactions.md#write-operation

`Retryable Error`_
------------------

.. _retryable error: ./transactions.md#retryable-error

`Command Error`_
----------------

.. _command error: ./transactions.md#command-error

`Network Error`_
----------------

.. _network error: ./transactions.md#network-error

`Error Label`_
--------------

.. _error label: ./transactions.md#error-label

`Transient Transaction Error`_
------------------------------

.. _transient transaction error: ./transactions.md#transient-transaction-error

`Naming Variations`_
====================

.. _naming variations: ./transactions.md#naming-variations

`Transaction Api`_
==================

.. _transaction api: ./transactions.md#transaction-api

`Transactionoptions`_
=====================

.. _transactionoptions: ./transactions.md#transactionoptions

`Readconcern`_
--------------

.. _readconcern: ./transactions.md#readconcern

`Writeconcern`_
---------------

.. _writeconcern: ./transactions.md#writeconcern

`Readpreference`_
-----------------

.. _readpreference: ./transactions.md#readpreference

`Maxcommittimems`_
------------------

.. _maxcommittimems: ./transactions.md#maxcommittimems

`Sessionoptions Changes`_
=========================

.. _sessionoptions changes: ./transactions.md#sessionoptions-changes

`Defaulttransactionoptions`_
----------------------------

.. _defaulttransactionoptions: ./transactions.md#defaulttransactionoptions

`Clientsession Changes`_
========================

.. _clientsession changes: ./transactions.md#clientsession-changes

`Starttransaction`_
-------------------

.. _starttransaction: ./transactions.md#starttransaction

`Endsession Changes`_
---------------------

.. _endsession changes: ./transactions.md#endsession-changes

`Error Reporting Changes`_
==========================

.. _error reporting changes: ./transactions.md#error-reporting-changes

`Transactions Wire Protocol`_
*****************************

.. _transactions wire protocol: ./transactions.md#transactions-wire-protocol

`Constructing Commands Within A Transaction`_
=============================================

.. _constructing commands within a transaction: ./transactions.md#constructing-commands-within-a-transaction

`Behavior Of The Starttransaction Field`_
-----------------------------------------

.. _behavior of the starttransaction field: ./transactions.md#behavior-of-the-starttransaction-field

`Behavior Of The Autocommit Field`_
-----------------------------------

.. _behavior of the autocommit field: ./transactions.md#behavior-of-the-autocommit-field

`Behavior Of The Readconcern Field`_
------------------------------------

.. _behavior of the readconcern field: ./transactions.md#behavior-of-the-readconcern-field

`Behavior Of The Writeconcern Field`_
-------------------------------------

.. _behavior of the writeconcern field: ./transactions.md#behavior-of-the-writeconcern-field

`Behavior Of The Recoverytoken Field`_
--------------------------------------

.. _behavior of the recoverytoken field: ./transactions.md#behavior-of-the-recoverytoken-field

`Constructing The First Command Within A Transaction`_
------------------------------------------------------

.. _constructing the first command within a transaction: ./transactions.md#constructing-the-first-command-within-a-transaction

`Constructing Any Other Command Within A Transaction`_
------------------------------------------------------

.. _constructing any other command within a transaction: ./transactions.md#constructing-any-other-command-within-a-transaction

`Generic Runcommand Helper Within A Transaction`_
-------------------------------------------------

.. _generic runcommand helper within a transaction: ./transactions.md#generic-runcommand-helper-within-a-transaction

`Interaction With Causal Consistency`_
======================================

.. _interaction with causal consistency: ./transactions.md#interaction-with-causal-consistency

`Interaction With Retryable Writes`_
====================================

.. _interaction with retryable writes: ./transactions.md#interaction-with-retryable-writes

`Server Commands`_
==================

.. _server commands: ./transactions.md#server-commands

`Sharded Transactions`_
***********************

.. _sharded transactions: ./transactions.md#sharded-transactions

`Mongos Pinning`_
=================

.. _mongos pinning: ./transactions.md#mongos-pinning

`When To Unpin`_
----------------

.. _when to unpin: ./transactions.md#when-to-unpin

`Pinning In Load Balancer Mode`_
--------------------------------

.. _pinning in load balancer mode: ./transactions.md#pinning-in-load-balancer-mode

`Recoverytoken Field`_
======================

.. _recoverytoken field: ./transactions.md#recoverytoken-field

`Error Reporting And Retrying Transactions`_
********************************************

.. _error reporting and retrying transactions: ./transactions.md#error-reporting-and-retrying-transactions

`Error Labels`_
===============

.. _error labels: ./transactions.md#error-labels

`Transienttransactionerror`_
============================

.. _transienttransactionerror: ./transactions.md#transienttransactionerror

`Retrying Transactions That Fail With Transienttransactionerror`_
-----------------------------------------------------------------

.. _retrying transactions that fail with transienttransactionerror: ./transactions.md#retrying-transactions-that-fail-with-transienttransactionerror

`Unknowntransactioncommitresult`_
=================================

.. _unknowntransactioncommitresult: ./transactions.md#unknowntransactioncommitresult

`Retrying Committransaction`_
-----------------------------

.. _retrying committransaction: ./transactions.md#retrying-committransaction

`Handling Command Errors`_
**************************

.. _handling command errors: ./transactions.md#handling-command-errors

`Test Plan`_
************

.. _test plan: ./transactions.md#test-plan

`Design Rationale`_
*******************

.. _design rationale: ./transactions.md#design-rationale

`Drivers Ignore All Aborttransaction Errors`_
=============================================

.. _drivers ignore all aborttransaction errors: ./transactions.md#drivers-ignore-all-aborttransaction-errors

`Drivers Add The "transienttransactionerror" Label To Network Errors`_
======================================================================

.. _drivers add the "transienttransactionerror" label to network errors: ./transactions.md#drivers-add-the-transienttransactionerror-label-to-network-errors

`Transactions In Gridfs`_
=========================

.. _transactions in gridfs: ./transactions.md#transactions-in-gridfs

`Causal Consistency With Runcommand Helper`_
============================================

.. _causal consistency with runcommand helper: ./transactions.md#causal-consistency-with-runcommand-helper

`Calling Committransaction With The Generic Runcommand Helper Is Undefined Behavior`_
=====================================================================================

.. _calling committransaction with the generic runcommand helper is undefined behavior: ./transactions.md#calling-committransaction-with-the-generic-runcommand-helper-is-undefined-behavior

`Dependencies`_
***************

.. _dependencies: ./transactions.md#dependencies

`Backwards Compatibility`_
**************************

.. _backwards compatibility: ./transactions.md#backwards-compatibility

`Reference Implementation`_
***************************

.. _reference implementation: ./transactions.md#reference-implementation

`Future Work`_
**************

.. _future work: ./transactions.md#future-work

`Justifications`_
*****************

.. _justifications: ./transactions.md#justifications

`Why Is There No Transaction Object?`_
======================================

.. _why is there no transaction object?: ./transactions.md#why-is-there-no-transaction-object

`Why Is Readpreference Part Of Transactionoptions?`_
====================================================

.. _why is readpreference part of transactionoptions?: ./transactions.md#why-is-readpreference-part-of-transactionoptions

`Users Cannot Pass Readconcern Or Writeconcern To Operations In Transactions`_
==============================================================================

.. _users cannot pass readconcern or writeconcern to operations in transactions: ./transactions.md#users-cannot-pass-readconcern-or-writeconcern-to-operations-in-transactions

`Aggregate With Write Stage Is A Read Operation`_
=================================================

.. _aggregate with write stage is a read operation: ./transactions.md#aggregate-with-write-stage-is-a-read-operation

`A Server Selection Error Is Labeled Unknowntransactioncommitresult`_
=====================================================================

.. _a server selection error is labeled unknowntransactioncommitresult: ./transactions.md#a-server-selection-error-is-labeled-unknowntransactioncommitresult

`Faq`_
******

.. _faq: ./transactions.md#faq

`What Commands Can Be Run In A Transaction?`_
=============================================

.. _what commands can be run in a transaction?: ./transactions.md#what-commands-can-be-run-in-a-transaction

`Why Don’t Drivers Automatically Retry Commit After A Write Concern Timeout Error?`_
====================================================================================

.. _why don’t drivers automatically retry commit after a write concern timeout error?: ./transactions.md#why-dont-drivers-automatically-retry-commit-after-a-write-concern-timeout-error

`What Happens When A Command Object Passed To Runcommand Already Contains A Transaction Field (eg. Lsid, Txnnumber, Etc...)?`_
==============================================================================================================================

.. _what happens when a command object passed to runcommand already contains a transaction field (eg. lsid, txnnumber, etc...)?: ./transactions.md#what-happens-when-a-command-object-passed-to-runcommand-already-contains-a-transaction-field-eg-lsid-txnnumber-etc

`Majority Write Concern Is Used When Retrying Committransaction`_
=================================================================

.. _majority write concern is used when retrying committransaction: ./transactions.md#majority-write-concern-is-used-when-retrying-committransaction

`Changelog`_
************

.. _changelog: ./transactions.md#changelog
