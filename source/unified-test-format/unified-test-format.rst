
.. note::
  This specification has been converted to Markdown and renamed to
  `unified-test-format.md <unified-test-format.md>`_.  

  Use the link above to access the latest version of the specification as the
  current reStructuredText file will no longer be updated.

  Use the links below to access equivalent section names in the Markdown version of
  the specification.

######################
`Unified Test Format`_
######################

.. _unified test format: ./unified-test-format.md#unified-test-format

`Abstract`_
***********

.. _abstract: ./unified-test-format.md#abstract

`Meta`_
*******

.. _meta: ./unified-test-format.md#meta

`Goals`_
********

.. _goals: ./unified-test-format.md#goals

`Specification`_
****************

.. _specification: ./unified-test-format.md#specification

`Terms`_
========

.. _terms: ./unified-test-format.md#terms

`Server Compatibility`_
=======================

.. _server compatibility: ./unified-test-format.md#server-compatibility

`Schema Version`_
=================

.. _schema version: ./unified-test-format.md#schema-version

`Json Schema Validation`_
-------------------------

.. _json schema validation: ./unified-test-format.md#json-schema-validation

`Test Runner Support`_
----------------------

.. _test runner support: ./unified-test-format.md#test-runner-support

`Impact Of Spec Changes On Schema Version`_
-------------------------------------------

.. _impact of spec changes on schema version: ./unified-test-format.md#impact-of-spec-changes-on-schema-version

`Entity Map`_
=============

.. _entity map: ./unified-test-format.md#entity-map

`Supported Entity Types`_
-------------------------

.. _supported entity types: ./unified-test-format.md#supported-entity-types

`Test Format`_
==============

.. _test format: ./unified-test-format.md#test-format

`Top-level Fields`_
-------------------

.. _top-level fields: ./unified-test-format.md#top-level-fields

`Runonrequirement`_
-------------------

.. _runonrequirement: ./unified-test-format.md#runonrequirement

`Entity`_
---------

.. _entity: ./unified-test-format.md#entity

`Storeeventsasentity`_
----------------------

.. _storeeventsasentity: ./unified-test-format.md#storeeventsasentity

`Serverapi`_
------------

.. _serverapi: ./unified-test-format.md#serverapi

`Collectiondata`_
-----------------

.. _collectiondata: ./unified-test-format.md#collectiondata

`Test`_
-------

.. _test: ./unified-test-format.md#test

`Operation`_
------------

.. _operation: ./unified-test-format.md#operation

`Expectederror`_
----------------

.. _expectederror: ./unified-test-format.md#expectederror

`Expectedeventsforclient`_
--------------------------

.. _expectedeventsforclient: ./unified-test-format.md#expectedeventsforclient

`Expectedevent`_
----------------

.. _expectedevent: ./unified-test-format.md#expectedevent

`Expectedcommandevent`_
^^^^^^^^^^^^^^^^^^^^^^^

.. _expectedcommandevent: ./unified-test-format.md#expectedcommandevent

`Expectedcmapevent`_
^^^^^^^^^^^^^^^^^^^^

.. _expectedcmapevent: ./unified-test-format.md#expectedcmapevent

`Expectedsdamevent`_
^^^^^^^^^^^^^^^^^^^^

.. _expectedsdamevent: ./unified-test-format.md#expectedsdamevent

`Hasserviceid`_
^^^^^^^^^^^^^^^

.. _hasserviceid: ./unified-test-format.md#hasserviceid

`Hasserverconnectionid`_
^^^^^^^^^^^^^^^^^^^^^^^^

.. _hasserverconnectionid: ./unified-test-format.md#hasserverconnectionid

`Expectedlogmessagesforclient`_
-------------------------------

.. _expectedlogmessagesforclient: ./unified-test-format.md#expectedlogmessagesforclient

`Expectedlogmessage`_
---------------------

.. _expectedlogmessage: ./unified-test-format.md#expectedlogmessage

`Collectionordatabaseoptions`_
------------------------------

.. _collectionordatabaseoptions: ./unified-test-format.md#collectionordatabaseoptions

`Common Options`_
=================

.. _common options: ./unified-test-format.md#common-options

`Version String`_
=================

.. _version string: ./unified-test-format.md#version-string

`Entity Test Operations`_
=========================

.. _entity test operations: ./unified-test-format.md#entity-test-operations

`Expressing Required And Optional Parameters`_
----------------------------------------------

.. _expressing required and optional parameters: ./unified-test-format.md#expressing-required-and-optional-parameters

`Special Handling For Arguments`_
---------------------------------

.. _special handling for arguments: ./unified-test-format.md#special-handling-for-arguments

`Converting Returned Model Objects To Documents`_
-------------------------------------------------

.. _converting returned model objects to documents: ./unified-test-format.md#converting-returned-model-objects-to-documents

`Iterating Returned Iterables`_
-------------------------------

.. _iterating returned iterables: ./unified-test-format.md#iterating-returned-iterables

`Client Operations`_
====================

.. _client operations: ./unified-test-format.md#client-operations

`Clientencryption Operations`_
==============================

.. _clientencryption operations: ./unified-test-format.md#clientencryption-operations

`Database Operations`_
======================

.. _database operations: ./unified-test-format.md#database-operations

`Listcollections`_
------------------

.. _listcollections: ./unified-test-format.md#listcollections

`Runcommand`_
-------------

.. _runcommand: ./unified-test-format.md#runcommand

`Runcursorcommand`_
-------------------

.. _runcursorcommand: ./unified-test-format.md#runcursorcommand

`Createcommandcursor`_
----------------------

.. _createcommandcursor: ./unified-test-format.md#createcommandcursor

`Collection Operations`_
========================

.. _collection operations: ./unified-test-format.md#collection-operations

`Bulkwrite`_
------------

.. _bulkwrite: ./unified-test-format.md#bulkwrite

`Createfindcursor`_
-------------------

.. _createfindcursor: ./unified-test-format.md#createfindcursor

`Createsearchindex`_
--------------------

.. _createsearchindex: ./unified-test-format.md#createsearchindex

`Createsearchindexes`_
----------------------

.. _createsearchindexes: ./unified-test-format.md#createsearchindexes

`Dropsearchindex`_
------------------

.. _dropsearchindex: ./unified-test-format.md#dropsearchindex

`Find`_
-------

.. _find: ./unified-test-format.md#find

`Findoneandreplace And Findoneandupdate`_
-----------------------------------------

.. _findoneandreplace and findoneandupdate: ./unified-test-format.md#findoneandreplace-and-findoneandupdate

`Insertmany`_
-------------

.. _insertmany: ./unified-test-format.md#insertmany

`Insertone`_
------------

.. _insertone: ./unified-test-format.md#insertone

`Listsearchindexes`_
--------------------

.. _listsearchindexes: ./unified-test-format.md#listsearchindexes

`Updatesearchindex`_
--------------------

.. _updatesearchindex: ./unified-test-format.md#updatesearchindex

`Session Operations`_
=====================

.. _session operations: ./unified-test-format.md#session-operations

`Withtransaction`_
------------------

.. _withtransaction: ./unified-test-format.md#withtransaction

`Bucket Operations`_
====================

.. _bucket operations: ./unified-test-format.md#bucket-operations

`Download And Downloadbyname`_
------------------------------

.. _download and downloadbyname: ./unified-test-format.md#download-and-downloadbyname

`Downloadtostream And Downloadtostreambyname`_
----------------------------------------------

.. _downloadtostream and downloadtostreambyname: ./unified-test-format.md#downloadtostream-and-downloadtostreambyname

`Opendownloadstream And Opendownloadstreambyname`_
--------------------------------------------------

.. _opendownloadstream and opendownloadstreambyname: ./unified-test-format.md#opendownloadstream-and-opendownloadstreambyname

`Openuploadstream And Openuploadstreamwithid`_
----------------------------------------------

.. _openuploadstream and openuploadstreamwithid: ./unified-test-format.md#openuploadstream-and-openuploadstreamwithid

`Upload And Uploadwithid`_
--------------------------

.. _upload and uploadwithid: ./unified-test-format.md#upload-and-uploadwithid

`Uploadfromstream And Uploadfromstreamwithid`_
----------------------------------------------

.. _uploadfromstream and uploadfromstreamwithid: ./unified-test-format.md#uploadfromstream-and-uploadfromstreamwithid

`Cursor Operations`_
====================

.. _cursor operations: ./unified-test-format.md#cursor-operations

`Iterateuntildocumentorerror`_
------------------------------

.. _iterateuntildocumentorerror: ./unified-test-format.md#iterateuntildocumentorerror

`Iterateonce`_
--------------

.. _iterateonce: ./unified-test-format.md#iterateonce

`Special Test Operations`_
==========================

.. _special test operations: ./unified-test-format.md#special-test-operations

`Failpoint`_
------------

.. _failpoint: ./unified-test-format.md#failpoint

`Targetedfailpoint`_
--------------------

.. _targetedfailpoint: ./unified-test-format.md#targetedfailpoint

`Assertsessiontransactionstate`_
--------------------------------

.. _assertsessiontransactionstate: ./unified-test-format.md#assertsessiontransactionstate

`Assertsessionpinned`_
----------------------

.. _assertsessionpinned: ./unified-test-format.md#assertsessionpinned

`Assertsessionunpinned`_
------------------------

.. _assertsessionunpinned: ./unified-test-format.md#assertsessionunpinned

`Assertdifferentlsidonlasttwocommands`_
---------------------------------------

.. _assertdifferentlsidonlasttwocommands: ./unified-test-format.md#assertdifferentlsidonlasttwocommands

`Assertsamelsidonlasttwocommands`_
----------------------------------

.. _assertsamelsidonlasttwocommands: ./unified-test-format.md#assertsamelsidonlasttwocommands

`Assertsessiondirty`_
---------------------

.. _assertsessiondirty: ./unified-test-format.md#assertsessiondirty

`Assertsessionnotdirty`_
------------------------

.. _assertsessionnotdirty: ./unified-test-format.md#assertsessionnotdirty

`Assertcollectionexists`_
-------------------------

.. _assertcollectionexists: ./unified-test-format.md#assertcollectionexists

`Assertcollectionnotexists`_
----------------------------

.. _assertcollectionnotexists: ./unified-test-format.md#assertcollectionnotexists

`Assertindexexists`_
--------------------

.. _assertindexexists: ./unified-test-format.md#assertindexexists

`Assertindexnotexists`_
-----------------------

.. _assertindexnotexists: ./unified-test-format.md#assertindexnotexists

`Loop`_
-------

.. _loop: ./unified-test-format.md#loop

`Assertnumberconnectionscheckedout`_
------------------------------------

.. _assertnumberconnectionscheckedout: ./unified-test-format.md#assertnumberconnectionscheckedout

`Runonthread`_
--------------

.. _runonthread: ./unified-test-format.md#runonthread

`Waitforthread`_
----------------

.. _waitforthread: ./unified-test-format.md#waitforthread

`Waitforevent`_
---------------

.. _waitforevent: ./unified-test-format.md#waitforevent

`Asserteventcount`_
-------------------

.. _asserteventcount: ./unified-test-format.md#asserteventcount

`Recordtopologydescription`_
----------------------------

.. _recordtopologydescription: ./unified-test-format.md#recordtopologydescription

`Asserttopologytype`_
---------------------

.. _asserttopologytype: ./unified-test-format.md#asserttopologytype

`Waitforprimarychange`_
-----------------------

.. _waitforprimarychange: ./unified-test-format.md#waitforprimarychange

`Wait`_
-------

.. _wait: ./unified-test-format.md#wait

`Special Placeholder Value`_
============================

.. _special placeholder value: ./unified-test-format.md#special-placeholder-value

`$$placeholder`_
----------------

.. _$$placeholder: ./unified-test-format.md#placeholder

`Evaluating Matches`_
=====================

.. _evaluating matches: ./unified-test-format.md#evaluating-matches

`Flexible Numeric Comparisons`_
-------------------------------

.. _flexible numeric comparisons: ./unified-test-format.md#flexible-numeric-comparisons

`Allowing Extra Fields In Root-level Documents`_
------------------------------------------------

.. _allowing extra fields in root-level documents: ./unified-test-format.md#allowing-extra-fields-in-root-level-documents

`Document Key Order Variation`_
-------------------------------

.. _document key order variation: ./unified-test-format.md#document-key-order-variation

`Arrays Must Contain The Same Number Of Elements`_
--------------------------------------------------

.. _arrays must contain the same number of elements: ./unified-test-format.md#arrays-must-contain-the-same-number-of-elements

`Special Operators For Matching Assertions`_
--------------------------------------------

.. _special operators for matching assertions: ./unified-test-format.md#special-operators-for-matching-assertions

`$$exists`_
^^^^^^^^^^^

.. _$$exists: ./unified-test-format.md#exists

`$$type`_
^^^^^^^^^

.. _$$type: ./unified-test-format.md#type

`$$matchesentity`_
^^^^^^^^^^^^^^^^^^

.. _$$matchesentity: ./unified-test-format.md#matchesentity

`$$matcheshexbytes`_
^^^^^^^^^^^^^^^^^^^^

.. _$$matcheshexbytes: ./unified-test-format.md#matcheshexbytes

`$$unsetormatches`_
^^^^^^^^^^^^^^^^^^^

.. _$$unsetormatches: ./unified-test-format.md#unsetormatches

`$$sessionlsid`_
^^^^^^^^^^^^^^^^

.. _$$sessionlsid: ./unified-test-format.md#sessionlsid

`$$lte`_
^^^^^^^^

.. _$$lte: ./unified-test-format.md#lte

`$$matchasdocument`_
^^^^^^^^^^^^^^^^^^^^

.. _$$matchasdocument: ./unified-test-format.md#matchasdocument

`$$matchasroot`_
^^^^^^^^^^^^^^^^

.. _$$matchasroot: ./unified-test-format.md#matchasroot

`Test Runner Implementation`_
=============================

.. _test runner implementation: ./unified-test-format.md#test-runner-implementation

`Initializing The Test Runner`_
-------------------------------

.. _initializing the test runner: ./unified-test-format.md#initializing-the-test-runner

`Executing A Test File`_
------------------------

.. _executing a test file: ./unified-test-format.md#executing-a-test-file

`Executing A Test`_
-------------------

.. _executing a test: ./unified-test-format.md#executing-a-test

`Executing An Operation`_
-------------------------

.. _executing an operation: ./unified-test-format.md#executing-an-operation

`Special Procedures`_
---------------------

.. _special procedures: ./unified-test-format.md#special-procedures

`Terminating Open Transactions`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _terminating open transactions: ./unified-test-format.md#terminating-open-transactions

`Staledbversion Errors On Sharded Clusters`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _staledbversion errors on sharded clusters: ./unified-test-format.md#staledbversion-errors-on-sharded-clusters

`Server Fail Points`_
=====================

.. _server fail points: ./unified-test-format.md#server-fail-points

`Configuring Fail Points`_
--------------------------

.. _configuring fail points: ./unified-test-format.md#configuring-fail-points

`Disabling Fail Points`_
------------------------

.. _disabling fail points: ./unified-test-format.md#disabling-fail-points

`Fail Points Commonly Used In Tests`_
-------------------------------------

.. _fail points commonly used in tests: ./unified-test-format.md#fail-points-commonly-used-in-tests

`Failcommand`_
^^^^^^^^^^^^^^

.. _failcommand: ./unified-test-format.md#failcommand

`Determining If A Sharded Cluster Uses Replica Sets`_
=====================================================

.. _determining if a sharded cluster uses replica sets: ./unified-test-format.md#determining-if-a-sharded-cluster-uses-replica-sets

`Design Rationale`_
*******************

.. _design rationale: ./unified-test-format.md#design-rationale

`Why Can't Observesensitivecommands Be True When Authentication Is Enabled?`_
=============================================================================

.. _why can't observesensitivecommands be true when authentication is enabled?: ./unified-test-format.md#why-can-t-observesensitivecommands-be-true-when-authentication-is-enabled

`Breaking Changes`_
*******************

.. _breaking changes: ./unified-test-format.md#breaking-changes

`Future Work`_
**************

.. _future work: ./unified-test-format.md#future-work

`Assert Expected Log Messages`_
===============================

.. _assert expected log messages: ./unified-test-format.md#assert-expected-log-messages

`Target Failpoint By Read Preference`_
======================================

.. _target failpoint by read preference: ./unified-test-format.md#target-failpoint-by-read-preference

`Io Operations For Gridfs Streams`_
===================================

.. _io operations for gridfs streams: ./unified-test-format.md#io-operations-for-gridfs-streams

`Support Client-side Encryption Integration Tests`_
===================================================

.. _support client-side encryption integration tests: ./unified-test-format.md#support-client-side-encryption-integration-tests

`Incorporate Referenced Entity Operations Into The Schema Version`_
===================================================================

.. _incorporate referenced entity operations into the schema version: ./unified-test-format.md#incorporate-referenced-entity-operations-into-the-schema-version

`Changelog`_
************

.. _changelog: ./unified-test-format.md#changelog
