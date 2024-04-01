
.. note::
  This specification has been converted to Markdown and renamed to
  `client-side-encryption.md <client-side-encryption.md>`_.  

  Use the link above to access the latest version of the specification as the
  current reStructuredText file will no longer be updated.

  Use the links below to access equivalent section names in the Markdown version of
  the specification.

#########################
`Client Side Encryption`_
#########################

.. _client side encryption: ./client-side-encryption.md#client-side-encryption

`Abstract`_
***********

.. _abstract: ./client-side-encryption.md#abstract

`Meta`_
*******

.. _meta: ./client-side-encryption.md#meta

`Terms`_
********

.. _terms: ./client-side-encryption.md#terms

`Introduction`_
***************

.. _introduction: ./client-side-encryption.md#introduction

`Mongodb Key Vault Collection`_
===============================

.. _mongodb key vault collection: ./client-side-encryption.md#mongodb-key-vault-collection

`Kms Provider`_
===============

.. _kms provider: ./client-side-encryption.md#kms-provider

`Mongocryptd`_
==============

.. _mongocryptd: ./client-side-encryption.md#mongocryptd

`Crypt_shared`_
===============

.. _crypt_shared: ./client-side-encryption.md#crypt-shared

`Libmongocrypt`_
================

.. _libmongocrypt: ./client-side-encryption.md#libmongocrypt

`User Facing Api`_
******************

.. _user facing api: ./client-side-encryption.md#user-facing-api

`Mongoclient Changes`_
======================

.. _mongoclient changes: ./client-side-encryption.md#mongoclient-changes

`Keyvaultnamespace`_
--------------------

.. _keyvaultnamespace: ./client-side-encryption.md#keyvaultnamespace

`Keyvaultclient`_
-----------------

.. _keyvaultclient: ./client-side-encryption.md#keyvaultclient

`Keyvaultclient, Metadataclient, And The Internal Mongoclient`_
---------------------------------------------------------------

.. _keyvaultclient, metadataclient, and the internal mongoclient: ./client-side-encryption.md#keyvaultclient-metadataclient-and-the-internal-mongoclient

`Automatic Credentials`_
^^^^^^^^^^^^^^^^^^^^^^^^

.. _automatic credentials: ./client-side-encryption.md#automatic-credentials

`Obtaining Gcp Credentials`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _obtaining gcp credentials: ./client-side-encryption.md#obtaining-gcp-credentials

`Obtaining An Access Token For Azure Key Vault`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _obtaining an access token for azure key vault: ./client-side-encryption.md#obtaining-an-access-token-for-azure-key-vault

`Kms Provider Tls Options`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _kms provider tls options: ./client-side-encryption.md#kms-provider-tls-options

`Schemamap`_
------------

.. _schemamap: ./client-side-encryption.md#schemamap

`Bypassautoencryption`_
-----------------------

.. _bypassautoencryption: ./client-side-encryption.md#bypassautoencryption

`Extraoptions`_
---------------

.. _extraoptions: ./client-side-encryption.md#extraoptions

`Extraoptions.cryptsharedlibpath`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _extraoptions.cryptsharedlibpath: ./client-side-encryption.md#extraoptions-cryptsharedlibpath

`Extraoptions.cryptsharedlibrequired`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _extraoptions.cryptsharedlibrequired: ./client-side-encryption.md#extraoptions-cryptsharedlibrequired

`Encryptedfieldsmap`_
---------------------

.. _encryptedfieldsmap: ./client-side-encryption.md#encryptedfieldsmap

`Bypassqueryanalysis`_
----------------------

.. _bypassqueryanalysis: ./client-side-encryption.md#bypassqueryanalysis

`Queryable Encryption Create And Drop Collection Helpers`_
==========================================================

.. _queryable encryption create and drop collection helpers: ./client-side-encryption.md#queryable-encryption-create-and-drop-collection-helpers

`Collection Encryptedfields Lookup (getencryptedfields)`_
---------------------------------------------------------

.. _collection encryptedfields lookup (getencryptedfields): ./client-side-encryption.md#collection-encryptedfields-lookup-getencryptedfields

`Create Collection Helper`_
---------------------------

.. _create collection helper: ./client-side-encryption.md#create-collection-helper

`Create Encrypted Collection Helper`_
-------------------------------------

.. _create encrypted collection helper: ./client-side-encryption.md#create-encrypted-collection-helper

`Drop Collection Helper`_
-------------------------

.. _drop collection helper: ./client-side-encryption.md#drop-collection-helper

`Datakeyopts`_
==============

.. _datakeyopts: ./client-side-encryption.md#datakeyopts

`Masterkey`_
------------

.. _masterkey: ./client-side-encryption.md#masterkey

`Keyaltnames`_
--------------

.. _keyaltnames: ./client-side-encryption.md#keyaltnames

`Keymaterial`_
--------------

.. _keymaterial: ./client-side-encryption.md#keymaterial

`Rewrapmanydatakey`_
====================

.. _rewrapmanydatakey: ./client-side-encryption.md#rewrapmanydatakey

`Rewrapmanydatakeyopts`_
========================

.. _rewrapmanydatakeyopts: ./client-side-encryption.md#rewrapmanydatakeyopts

`Rewrapmanydatakeyresult`_
==========================

.. _rewrapmanydatakeyresult: ./client-side-encryption.md#rewrapmanydatakeyresult

`Encryptopts`_
==============

.. _encryptopts: ./client-side-encryption.md#encryptopts

`Keyid`_
--------

.. _keyid: ./client-side-encryption.md#keyid

`Keyaltname`_
-------------

.. _keyaltname: ./client-side-encryption.md#keyaltname

`Algorithm`_
------------

.. _algorithm: ./client-side-encryption.md#algorithm

`Contentionfactor`_
-------------------

.. _contentionfactor: ./client-side-encryption.md#contentionfactor

`Querytype`_
------------

.. _querytype: ./client-side-encryption.md#querytype

`Rangeopts`_
------------

.. _rangeopts: ./client-side-encryption.md#rangeopts

`User Facing Api: When Auto Encryption Fails`_
**********************************************

.. _user facing api when auto encryption fails: ./client-side-encryption.md#user-facing-api-when-auto-encryption-fails

`User Facing Api: View Limitations`_
************************************

.. _user facing api: view limitations: ./client-side-encryption.md#user-facing-api-view-limitations

`Implementation`_
*****************

.. _implementation: ./client-side-encryption.md#implementation

`Integrating With Libmongocrypt`_
*********************************

.. _integrating with libmongocrypt: ./client-side-encryption.md#integrating-with-libmongocrypt

`Enabling Command Marking With The Crypt_shared Library`_
*********************************************************

.. _enabling command marking with the crypt_shared library: ./client-side-encryption.md#enabling-command-marking-with-the-crypt-shared-library

`Setting Search Paths`_
=======================

.. _setting search paths: ./client-side-encryption.md#setting-search-paths

`Overriding The Crypt_shared Library Path`_
===========================================

.. _overriding the crypt_shared library path: ./client-side-encryption.md#overriding-the-crypt-shared-library-path

`Path Resolution Behavior`_
===========================

.. _path resolution behavior: ./client-side-encryption.md#path-resolution-behavior

`Search Paths For Testing`_
---------------------------

.. _search paths for testing: ./client-side-encryption.md#search-paths-for-testing

`Detecting Crypt_shared Availability`_
======================================

.. _detecting crypt_shared availability: ./client-side-encryption.md#detecting-crypt-shared-availability

`"disabling" Crypt_shared`_
===========================

.. _"disabling" crypt_shared: ./client-side-encryption.md#disabling-crypt-shared-1

`Loading Crypt_shared Multiple Times`_
======================================

.. _loading crypt_shared multiple times: ./client-side-encryption.md#loading-crypt-shared-multiple-times

`Managing Mongocryptd`_
***********************

.. _managing mongocryptd: ./client-side-encryption.md#managing-mongocryptd

`Spawning Mongocryptd`_
=======================

.. _spawning mongocryptd: ./client-side-encryption.md#spawning-mongocryptd

`Connecting To Mongocryptd`_
============================

.. _connecting to mongocryptd: ./client-side-encryption.md#connecting-to-mongocryptd

`Key Vault Collection`_
***********************

.. _key vault collection: ./client-side-encryption.md#key-vault-collection

`Auto Encrypt And Decrypt`_
***************************

.. _auto encrypt and decrypt: ./client-side-encryption.md#auto-encrypt-and-decrypt

`Interaction With Command Monitoring`_
**************************************

.. _interaction with command monitoring: ./client-side-encryption.md#interaction-with-command-monitoring

`Size Limits For Write Commands`_
*********************************

.. _size limits for write commands: ./client-side-encryption.md#size-limits-for-write-commands

`Appendix`_
***********

.. _appendix: ./client-side-encryption.md#appendix

`Appendix Terms`_
=================

.. _appendix terms: ./client-side-encryption.md#appendix-terms

`Key Vault Collection Schema For Data Keys`_
============================================

.. _key vault collection schema for data keys: ./client-side-encryption.md#key-vault-collection-schema-for-data-keys

`Masterkey Contents`_
---------------------

.. _masterkey contents: ./client-side-encryption.md#masterkey-contents

`Example Data Key Document`_
----------------------------

.. _example data key document: ./client-side-encryption.md#example-data-key-document

`Type 0: Intent-to-encrypt Marking`_
------------------------------------

.. _type 0: intent-to-encrypt marking: ./client-side-encryption.md#type-0-intent-to-encrypt-marking

`Types 1 And 2: Ciphertext`_
----------------------------

.. _types 1 and 2: ciphertext: ./client-side-encryption.md#types-1-and-2-ciphertext

`Jsonschema "encrypt"`_
=======================

.. _jsonschema "encrypt": ./client-side-encryption.md#jsonschema-encrypt

`Libmongocrypt: Prohibitions And Warnings`_
===========================================

.. _libmongocrypt: prohibitions and warnings: ./client-side-encryption.md#libmongocrypt-prohibitions-and-warnings

`Libmongocrypt: Collection Info Caching`_
=========================================

.. _libmongocrypt: collection info caching: ./client-side-encryption.md#libmongocrypt-collection-info-caching

`Libmongocrypt: Data Key Caching`_
==================================

.. _libmongocrypt: data key caching: ./client-side-encryption.md#libmongocrypt-data-key-caching

`Libmongocrypt: Crypto Implementation`_
=======================================

.. _libmongocrypt: crypto implementation: ./client-side-encryption.md#libmongocrypt-crypto-implementation

`Libmongocrypt: Auto Encryption Allow-list`_
============================================

.. _libmongocrypt: auto encryption allow-list: ./client-side-encryption.md#libmongocrypt-auto-encryption-allow-list

`Test Plan`_
************

.. _test plan: ./client-side-encryption.md#test-plan

`Rationale`_
************

.. _rationale: ./client-side-encryption.md#rationale

`Design Principles`_
====================

.. _design principles: ./client-side-encryption.md#design-principles

`1. Make Encryption Easy To Enable`_
====================================

.. _1. make encryption easy to enable: ./client-side-encryption.md#make-encryption-easy-to-enable

`2. Minimize Risk Of Exposing Sensitive Data`_
==============================================

.. _2. minimize risk of exposing sensitive data: ./client-side-encryption.md#minimize-risk-of-exposing-sensitive-data

`3. Minimize Api`_
==================

.. _3. minimize api: ./client-side-encryption.md#minimize-api

`How Did We Arrive At This Api?`_
=================================

.. _how did we arrive at this api?: ./client-side-encryption.md#how-did-we-arrive-at-this-api

`Why Is Client Side Encryption Configured On A Mongoclient?`_
-------------------------------------------------------------

.. _why is client side encryption configured on a mongoclient?: ./client-side-encryption.md#why-is-client-side-encryption-configured-on-a-mongoclient

`Why Not Make Auto Encryption "opt-in"?`_
-----------------------------------------

.. _why not make auto encryption "opt-in"?: ./client-side-encryption.md#why-not-make-auto-encryption-opt-in

`Why Are Auto Encrypted Collections Configured At Level Of Mongoclient?`_
-------------------------------------------------------------------------

.. _why are auto encrypted collections configured at level of mongoclient?: ./client-side-encryption.md#why-are-auto-encrypted-collections-configured-at-level-of-mongoclient

`Why Do We Have A Separate Top Level Type For Clientencryption?`_
-----------------------------------------------------------------

.. _why do we have a separate top level type for clientencryption?: ./client-side-encryption.md#why-do-we-have-a-separate-top-level-type-for-clientencryption

`Why Not Pass The Clientencryption Into Db.getcollection() To Enable Auto Encryption?`_
---------------------------------------------------------------------------------------

.. _why not pass the clientencryption into db.getcollection() to enable auto encryption?: ./client-side-encryption.md#why-not-pass-the-clientencryption-into-db-getcollection-to-enable-auto-encryption

`Why Do We Need To Pass A Client To Create A Clientencryption?`_
----------------------------------------------------------------

.. _why do we need to pass a client to create a clientencryption?: ./client-side-encryption.md#why-do-we-need-to-pass-a-client-to-create-a-clientencryption

`Why Are Extraoptions And Kmsproviders Maps?`_
----------------------------------------------

.. _why are extraoptions and kmsproviders maps?: ./client-side-encryption.md#why-are-extraoptions-and-kmsproviders-maps

`Why Is There A Bypassautoencryption?`_
---------------------------------------

.. _why is there a bypassautoencryption?: ./client-side-encryption.md#why-is-there-a-bypassautoencryption

`Why Not Require Compatibility Between Mongocryptd And The Server?`_
====================================================================

.. _why not require compatibility between mongocryptd and the server?: ./client-side-encryption.md#why-not-require-compatibility-between-mongocryptd-and-the-server

`Why Cache Keys?`_
==================

.. _why cache keys?: ./client-side-encryption.md#why-cache-keys

`Why Require Including A C Library?`_
=====================================

.. _why require including a c library?: ./client-side-encryption.md#why-require-including-a-c-library

`Why Warn If A Local Schema Does Not Have Encrypted Fields?`_
=============================================================

.. _why warn if a local schema does not have encrypted fields?: ./client-side-encryption.md#why-warn-if-a-local-schema-does-not-have-encrypted-fields

`Why Limit To One Top-level $jsonschema?`_
==========================================

.. _why limit to one top-level $jsonschema?: ./client-side-encryption.md#why-limit-to-one-top-level-jsonschema

`Why Not Allow Schemas To Be Configured At Runtime?`_
=====================================================

.. _why not allow schemas to be configured at runtime?: ./client-side-encryption.md#why-not-allow-schemas-to-be-configured-at-runtime

`Why Not Support Other Aws Auth Mechanisms?`_
=============================================

.. _why not support other aws auth mechanisms?: ./client-side-encryption.md#why-not-support-other-aws-auth-mechanisms

`Why Not Pass A Uri For External Key Vault Collections Instead Of A Mongoclient?`_
==================================================================================

.. _why not pass a uri for external key vault collections instead of a mongoclient?: ./client-side-encryption.md#why-not-pass-a-uri-for-external-key-vault-collections-instead-of-a-mongoclient

`What Happened To Multiple Key Vault Collections?`_
===================================================

.. _what happened to multiple key vault collections?: ./client-side-encryption.md#what-happened-to-multiple-key-vault-collections

`Why Auto Encrypt A Command Instead Of A Wire Protocol Message?`_
=================================================================

.. _why auto encrypt a command instead of a wire protocol message?: ./client-side-encryption.md#why-auto-encrypt-a-command-instead-of-a-wire-protocol-message

`Why Is A Failure To Decrypt Always An Error?`_
===============================================

.. _why is a failure to decrypt always an error?: ./client-side-encryption.md#why-is-a-failure-to-decrypt-always-an-error

`Why Are There No Apm Events For Mongocryptd?`_
===============================================

.. _why are there no apm events for mongocryptd?: ./client-side-encryption.md#why-are-there-no-apm-events-for-mongocryptd

`Why Aren't We Creating A Unique Index In The Key Vault Collection?`_
=====================================================================

.. _why aren't we creating a unique index in the key vault collection?: ./client-side-encryption.md#why-aren-t-we-creating-a-unique-index-in-the-key-vault-collection

`Why Do Operations On Views Fail?`_
===================================

.. _why do operations on views fail?: ./client-side-encryption.md#why-do-operations-on-views-fail

`Why Is A 4.2 Server Required?`_
================================

.. _why is a 4.2 server required?: ./client-side-encryption.md#why-is-a-4-2-server-required

`Why Are Serverselectiontryonce And Cooldownms Disabled For Single-threaded Drivers Connecting To Mongocryptd?`_
================================================================================================================

.. _why are serverselectiontryonce and cooldownms disabled for single-threaded drivers connecting to mongocryptd?: ./client-side-encryption.md#why-are-serverselectiontryonce-and-cooldownms-disabled-for-single-threaded-drivers-connecting-to-mongocryptd

`What's The Deal With Metadataclient, Keyvaultclient, And The Internal Client?`_
================================================================================

.. _what's the deal with metadataclient, keyvaultclient, and the internal client?: ./client-side-encryption.md#what-s-the-deal-with-metadataclient-keyvaultclient-and-the-internal-client

`Why Not Reuse The Parent Mongoclient When Maxpoolsize Is Limited?`_
--------------------------------------------------------------------

.. _why not reuse the parent mongoclient when maxpoolsize is limited?: ./client-side-encryption.md#why-not-reuse-the-parent-mongoclient-when-maxpoolsize-is-limited

`Why Is Keyvaultclient An Exposed Option, But Metadataclient Private?`_
-----------------------------------------------------------------------

.. _why is keyvaultclient an exposed option, but metadataclient private?: ./client-side-encryption.md#why-is-keyvaultclient-an-exposed-option-but-metadataclient-private

`Why Is The Metadataclient Not Needed If Bypassautoencryption=true`_
--------------------------------------------------------------------

.. _why is the metadataclient not needed if bypassautoencryption=true: ./client-side-encryption.md#why-is-the-metadataclient-not-needed-if-bypassautoencryption-true

`Why Are Commands Sent To Mongocryptd On Collections Without Encrypted Fields?`_
================================================================================

.. _why are commands sent to mongocryptd on collections without encrypted fields?: ./client-side-encryption.md#why-are-commands-sent-to-mongocryptd-on-collections-without-encrypted-fields

`Why Do Kms Providers Require Tls Options?`_
============================================

.. _why do kms providers require tls options?: ./client-side-encryption.md#why-do-kms-providers-require-tls-options

`Why Is It An Error To Have An Fle 1 And Queryable Encryption Field In The Same Collection?`_
=============================================================================================

.. _why is it an error to have an fle 1 and queryable encryption field in the same collection?: ./client-side-encryption.md#why-is-it-an-error-to-have-an-fle-1-and-queryable-encryption-field-in-the-same-collection

`Is It An Error To Set Schemamap And Encryptedfieldsmap?`_
==========================================================

.. _is it an error to set schemamap and encryptedfieldsmap?: ./client-side-encryption.md#is-it-an-error-to-set-schemamap-and-encryptedfieldsmap

`Why Is Bypassqueryanalysis Needed?`_
=====================================

.. _why is bypassqueryanalysis needed?: ./client-side-encryption.md#why-is-bypassqueryanalysis-needed

`Why Does Rewrapmanydatakey Return Rewrapmanydatakeyresult Instead Of Bulkwriteresult?`_
========================================================================================

.. _why does rewrapmanydatakey return rewrapmanydatakeyresult instead of bulkwriteresult?: ./client-side-encryption.md#why-does-rewrapmanydatakey-return-rewrapmanydatakeyresult-instead-of-bulkwriteresult

`Why Does Clientencryption Have Key Management Functions When Drivers Can Use Existing Crud Operations Instead?`_
=================================================================================================================

.. _why does clientencryption have key management functions when drivers can use existing crud operations instead?: ./client-side-encryption.md#why-does-clientencryption-have-key-management-functions-when-drivers-can-use-existing-crud-operations-instead

`Why Are The Querytype And Algorithm Options A String?`_
========================================================

.. _why are the querytype and algorithm options a string?: ./client-side-encryption.md#why-are-the-querytype-and-algorithm-options-a-string

`Why Is There An Encryptexpression Helper?`_
============================================

.. _why is there an encryptexpression helper?: ./client-side-encryption.md#why-is-there-an-encryptexpression-helper

`Why Do On-demand Kms Credentials Not Support Named Kms Providers?`_
====================================================================

.. _why do on-demand kms credentials not support named kms providers?: ./client-side-encryption.md#why-do-on-demand-kms-credentials-not-support-named-kms-providers

`Future Work`_
**************

.. _future work: ./client-side-encryption.md#future-work

`Make Libmonogocrypt Cache Window Configurable`_
================================================

.. _make libmonogocrypt cache window configurable: ./client-side-encryption.md#make-libmonogocrypt-cache-window-configurable

`Apm Events For Encryption Or Key Service Interaction`_
=======================================================

.. _apm events for encryption or key service interaction: ./client-side-encryption.md#apm-events-for-encryption-or-key-service-interaction

`Remove Mongocryptd`_
=====================

.. _remove mongocryptd: ./client-side-encryption.md#remove-mongocryptd

`Support External Key Vault Collection Discovery`_
==================================================

.. _support external key vault collection discovery: ./client-side-encryption.md#support-external-key-vault-collection-discovery

`Batch Listcollections Requests On Expired Schema Cache Entries`_
=================================================================

.. _batch listcollections requests on expired schema cache entries: ./client-side-encryption.md#batch-listcollections-requests-on-expired-schema-cache-entries

`Add A Maximum Size For The Jsonschema/key Cache.`_
===================================================

.. _add a maximum size for the jsonschema/key cache.: ./client-side-encryption.md#add-a-maximum-size-for-the-jsonschema-key-cache

`Recalculate Message Size Bounds Dynamically`_
==============================================

.. _recalculate message size bounds dynamically: ./client-side-encryption.md#recalculate-message-size-bounds-dynamically

`Support Sessions In Key Management Functions`_
===============================================

.. _support sessions in key management functions: ./client-side-encryption.md#support-sessions-in-key-management-functions

`Changelog`_
************

.. _changelog: ./client-side-encryption.md#changelog
