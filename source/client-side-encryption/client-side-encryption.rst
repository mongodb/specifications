
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

.. _client side encryption: ./auth.md#client-side-encryption

`Abstract`_
***********

.. _abstract: ./auth.md#abstract

`Meta`_
*******

.. _meta: ./auth.md#meta

`Terms`_
********

.. _terms: ./auth.md#terms

`Introduction`_
***************

.. _introduction: ./auth.md#introduction

`Mongodb Key Vault Collection`_
===============================

.. _mongodb key vault collection: ./auth.md#mongodb-key-vault-collection

`Kms Provider`_
===============

.. _kms provider: ./auth.md#kms-provider

`Mongocryptd`_
==============

.. _mongocryptd: ./auth.md#mongocryptd

`Crypt_shared`_
===============

.. _crypt_shared: ./auth.md#crypt-shared

`Libmongocrypt`_
================

.. _libmongocrypt: ./auth.md#libmongocrypt

`User Facing Api`_
******************

.. _user facing api: ./auth.md#user-facing-api

`Mongoclient Changes`_
======================

.. _mongoclient changes: ./auth.md#mongoclient-changes

`Keyvaultnamespace`_
--------------------

.. _keyvaultnamespace: ./auth.md#keyvaultnamespace

`Keyvaultclient`_
-----------------

.. _keyvaultclient: ./auth.md#keyvaultclient

`Keyvaultclient, Metadataclient, And The Internal Mongoclient`_
---------------------------------------------------------------

.. _keyvaultclient, metadataclient, and the internal mongoclient: ./auth.md#keyvaultclient-metadataclient-and-the-internal-mongoclient

`Automatic Credentials`_
^^^^^^^^^^^^^^^^^^^^^^^^

.. _automatic credentials: ./auth.md#automatic-credentials

`Obtaining Gcp Credentials`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _obtaining gcp credentials: ./auth.md#obtaining-gcp-credentials

`Obtaining An Access Token For Azure Key Vault`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _obtaining an access token for azure key vault: ./auth.md#obtaining-an-access-token-for-azure-key-vault

`Kms Provider Tls Options`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _kms provider tls options: ./auth.md#kms-provider-tls-options

`Schemamap`_
------------

.. _schemamap: ./auth.md#schemamap

`Bypassautoencryption`_
-----------------------

.. _bypassautoencryption: ./auth.md#bypassautoencryption

`Extraoptions`_
---------------

.. _extraoptions: ./auth.md#extraoptions

`Extraoptions.cryptsharedlibpath`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _extraoptions.cryptsharedlibpath: ./auth.md#extraoptions-cryptsharedlibpath

`Extraoptions.cryptsharedlibrequired`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _extraoptions.cryptsharedlibrequired: ./auth.md#extraoptions-cryptsharedlibrequired

`Encryptedfieldsmap`_
---------------------

.. _encryptedfieldsmap: ./auth.md#encryptedfieldsmap

`Bypassqueryanalysis`_
----------------------

.. _bypassqueryanalysis: ./auth.md#bypassqueryanalysis

`Queryable Encryption Create And Drop Collection Helpers`_
==========================================================

.. _queryable encryption create and drop collection helpers: ./auth.md#queryable-encryption-create-and-drop-collection-helpers

`Collection Encryptedfields Lookup (getencryptedfields)`_
---------------------------------------------------------

.. _collection encryptedfields lookup (getencryptedfields): ./auth.md#collection-encryptedfields-lookup-getencryptedfields

`Create Collection Helper`_
---------------------------

.. _create collection helper: ./auth.md#create-collection-helper

`Create Encrypted Collection Helper`_
-------------------------------------

.. _create encrypted collection helper: ./auth.md#create-encrypted-collection-helper

`Drop Collection Helper`_
-------------------------

.. _drop collection helper: ./auth.md#drop-collection-helper

`Datakeyopts`_
==============

.. _datakeyopts: ./auth.md#datakeyopts

`Masterkey`_
------------

.. _masterkey: ./auth.md#masterkey

`Keyaltnames`_
--------------

.. _keyaltnames: ./auth.md#keyaltnames

`Keymaterial`_
--------------

.. _keymaterial: ./auth.md#keymaterial

`Rewrapmanydatakey`_
====================

.. _rewrapmanydatakey: ./auth.md#rewrapmanydatakey

`Rewrapmanydatakeyopts`_
========================

.. _rewrapmanydatakeyopts: ./auth.md#rewrapmanydatakeyopts

`Rewrapmanydatakeyresult`_
==========================

.. _rewrapmanydatakeyresult: ./auth.md#rewrapmanydatakeyresult

`Encryptopts`_
==============

.. _encryptopts: ./auth.md#encryptopts

`Keyid`_
--------

.. _keyid: ./auth.md#keyid

`Keyaltname`_
-------------

.. _keyaltname: ./auth.md#keyaltname

`Algorithm`_
------------

.. _algorithm: ./auth.md#algorithm

`Contentionfactor`_
-------------------

.. _contentionfactor: ./auth.md#contentionfactor

`Querytype`_
------------

.. _querytype: ./auth.md#querytype

`Rangeopts`_
------------

.. _rangeopts: ./auth.md#rangeopts

`User Facing Api: When Auto Encryption Fails`_
**********************************************

.. _user facing api: when auto encryption fails: ./auth.md#user-facing-api-when-auto-encryption-fails

`User Facing Api: View Limitations`_
************************************

.. _user facing api: view limitations: ./auth.md#user-facing-api-view-limitations

`Implementation`_
*****************

.. _implementation: ./auth.md#implementation

`Integrating With Libmongocrypt`_
*********************************

.. _integrating with libmongocrypt: ./auth.md#integrating-with-libmongocrypt

`Enabling Command Marking With The Crypt_shared Library`_
*********************************************************

.. _enabling command marking with the crypt_shared library: ./auth.md#enabling-command-marking-with-the-crypt-shared-library

`Setting Search Paths`_
=======================

.. _setting search paths: ./auth.md#setting-search-paths

`Overriding The Crypt_shared Library Path`_
===========================================

.. _overriding the crypt_shared library path: ./auth.md#overriding-the-crypt-shared-library-path

`Path Resolution Behavior`_
===========================

.. _path resolution behavior: ./auth.md#path-resolution-behavior

`Search Paths For Testing`_
---------------------------

.. _search paths for testing: ./auth.md#search-paths-for-testing

`Detecting Crypt_shared Availability`_
======================================

.. _detecting crypt_shared availability: ./auth.md#detecting-crypt-shared-availability

`"disabling" Crypt_shared`_
===========================

.. _"disabling" crypt_shared: ./auth.md#disabling-crypt-shared-1

`Loading Crypt_shared Multiple Times`_
======================================

.. _loading crypt_shared multiple times: ./auth.md#loading-crypt-shared-multiple-times

`Managing Mongocryptd`_
***********************

.. _managing mongocryptd: ./auth.md#managing-mongocryptd

`Spawning Mongocryptd`_
=======================

.. _spawning mongocryptd: ./auth.md#spawning-mongocryptd

`Connecting To Mongocryptd`_
============================

.. _connecting to mongocryptd: ./auth.md#connecting-to-mongocryptd

`Key Vault Collection`_
***********************

.. _key vault collection: ./auth.md#key-vault-collection

`Auto Encrypt And Decrypt`_
***************************

.. _auto encrypt and decrypt: ./auth.md#auto-encrypt-and-decrypt

`Interaction With Command Monitoring`_
**************************************

.. _interaction with command monitoring: ./auth.md#interaction-with-command-monitoring

`Size Limits For Write Commands`_
*********************************

.. _size limits for write commands: ./auth.md#size-limits-for-write-commands

`Appendix`_
***********

.. _appendix: ./auth.md#appendix

`Appendix Terms`_
=================

.. _appendix terms: ./auth.md#appendix-terms

`Key Vault Collection Schema For Data Keys`_
============================================

.. _key vault collection schema for data keys: ./auth.md#key-vault-collection-schema-for-data-keys

`Masterkey Contents`_
---------------------

.. _masterkey contents: ./auth.md#masterkey-contents

`Example Data Key Document`_
----------------------------

.. _example data key document: ./auth.md#example-data-key-document

`Type 0: Intent-to-encrypt Marking`_
------------------------------------

.. _type 0: intent-to-encrypt marking: ./auth.md#type-0-intent-to-encrypt-marking

`Types 1 And 2: Ciphertext`_
----------------------------

.. _types 1 and 2: ciphertext: ./auth.md#types-1-and-2-ciphertext

`Jsonschema "encrypt"`_
=======================

.. _jsonschema "encrypt": ./auth.md#jsonschema-encrypt

`Libmongocrypt: Prohibitions And Warnings`_
===========================================

.. _libmongocrypt: prohibitions and warnings: ./auth.md#libmongocrypt-prohibitions-and-warnings

`Libmongocrypt: Collection Info Caching`_
=========================================

.. _libmongocrypt: collection info caching: ./auth.md#libmongocrypt-collection-info-caching

`Libmongocrypt: Data Key Caching`_
==================================

.. _libmongocrypt: data key caching: ./auth.md#libmongocrypt-data-key-caching

`Libmongocrypt: Crypto Implementation`_
=======================================

.. _libmongocrypt: crypto implementation: ./auth.md#libmongocrypt-crypto-implementation

`Libmongocrypt: Auto Encryption Allow-list`_
============================================

.. _libmongocrypt: auto encryption allow-list: ./auth.md#libmongocrypt-auto-encryption-allow-list

`Test Plan`_
************

.. _test plan: ./auth.md#test-plan

`Rationale`_
************

.. _rationale: ./auth.md#rationale

`Design Principles`_
====================

.. _design principles: ./auth.md#design-principles

`1. Make Encryption Easy To Enable`_
====================================

.. _1. make encryption easy to enable: ./auth.md#make-encryption-easy-to-enable

`2. Minimize Risk Of Exposing Sensitive Data`_
==============================================

.. _2. minimize risk of exposing sensitive data: ./auth.md#minimize-risk-of-exposing-sensitive-data

`3. Minimize Api`_
==================

.. _3. minimize api: ./auth.md#minimize-api

`How Did We Arrive At This Api?`_
=================================

.. _how did we arrive at this api?: ./auth.md#how-did-we-arrive-at-this-api

`Why Is Client Side Encryption Configured On A Mongoclient?`_
-------------------------------------------------------------

.. _why is client side encryption configured on a mongoclient?: ./auth.md#why-is-client-side-encryption-configured-on-a-mongoclient

`Why Not Make Auto Encryption "opt-in"?`_
-----------------------------------------

.. _why not make auto encryption "opt-in"?: ./auth.md#why-not-make-auto-encryption-opt-in

`Why Are Auto Encrypted Collections Configured At Level Of Mongoclient?`_
-------------------------------------------------------------------------

.. _why are auto encrypted collections configured at level of mongoclient?: ./auth.md#why-are-auto-encrypted-collections-configured-at-level-of-mongoclient

`Why Do We Have A Separate Top Level Type For Clientencryption?`_
-----------------------------------------------------------------

.. _why do we have a separate top level type for clientencryption?: ./auth.md#why-do-we-have-a-separate-top-level-type-for-clientencryption

`Why Not Pass The Clientencryption Into Db.getcollection() To Enable Auto Encryption?`_
---------------------------------------------------------------------------------------

.. _why not pass the clientencryption into db.getcollection() to enable auto encryption?: ./auth.md#why-not-pass-the-clientencryption-into-db-getcollection-to-enable-auto-encryption

`Why Do We Need To Pass A Client To Create A Clientencryption?`_
----------------------------------------------------------------

.. _why do we need to pass a client to create a clientencryption?: ./auth.md#why-do-we-need-to-pass-a-client-to-create-a-clientencryption

`Why Are Extraoptions And Kmsproviders Maps?`_
----------------------------------------------

.. _why are extraoptions and kmsproviders maps?: ./auth.md#why-are-extraoptions-and-kmsproviders-maps

`Why Is There A Bypassautoencryption?`_
---------------------------------------

.. _why is there a bypassautoencryption?: ./auth.md#why-is-there-a-bypassautoencryption

`Why Not Require Compatibility Between Mongocryptd And The Server?`_
====================================================================

.. _why not require compatibility between mongocryptd and the server?: ./auth.md#why-not-require-compatibility-between-mongocryptd-and-the-server

`Why Cache Keys?`_
==================

.. _why cache keys?: ./auth.md#why-cache-keys

`Why Require Including A C Library?`_
=====================================

.. _why require including a c library?: ./auth.md#why-require-including-a-c-library

`Why Warn If A Local Schema Does Not Have Encrypted Fields?`_
=============================================================

.. _why warn if a local schema does not have encrypted fields?: ./auth.md#why-warn-if-a-local-schema-does-not-have-encrypted-fields

`Why Limit To One Top-level $jsonschema?`_
==========================================

.. _why limit to one top-level $jsonschema?: ./auth.md#why-limit-to-one-top-level-jsonschema

`Why Not Allow Schemas To Be Configured At Runtime?`_
=====================================================

.. _why not allow schemas to be configured at runtime?: ./auth.md#why-not-allow-schemas-to-be-configured-at-runtime

`Why Not Support Other Aws Auth Mechanisms?`_
=============================================

.. _why not support other aws auth mechanisms?: ./auth.md#why-not-support-other-aws-auth-mechanisms

`Why Not Pass A Uri For External Key Vault Collections Instead Of A Mongoclient?`_
==================================================================================

.. _why not pass a uri for external key vault collections instead of a mongoclient?: ./auth.md#why-not-pass-a-uri-for-external-key-vault-collections-instead-of-a-mongoclient

`What Happened To Multiple Key Vault Collections?`_
===================================================

.. _what happened to multiple key vault collections?: ./auth.md#what-happened-to-multiple-key-vault-collections

`Why Auto Encrypt A Command Instead Of A Wire Protocol Message?`_
=================================================================

.. _why auto encrypt a command instead of a wire protocol message?: ./auth.md#why-auto-encrypt-a-command-instead-of-a-wire-protocol-message

`Why Is A Failure To Decrypt Always An Error?`_
===============================================

.. _why is a failure to decrypt always an error?: ./auth.md#why-is-a-failure-to-decrypt-always-an-error

`Why Are There No Apm Events For Mongocryptd?`_
===============================================

.. _why are there no apm events for mongocryptd?: ./auth.md#why-are-there-no-apm-events-for-mongocryptd

`Why Aren't We Creating A Unique Index In The Key Vault Collection?`_
=====================================================================

.. _why aren't we creating a unique index in the key vault collection?: ./auth.md#why-aren-t-we-creating-a-unique-index-in-the-key-vault-collection

`Why Do Operations On Views Fail?`_
===================================

.. _why do operations on views fail?: ./auth.md#why-do-operations-on-views-fail

`Why Is A 4.2 Server Required?`_
================================

.. _why is a 4.2 server required?: ./auth.md#why-is-a-4-2-server-required

`Why Are Serverselectiontryonce And Cooldownms Disabled For Single-threaded Drivers Connecting To Mongocryptd?`_
================================================================================================================

.. _why are serverselectiontryonce and cooldownms disabled for single-threaded drivers connecting to mongocryptd?: ./auth.md#why-are-serverselectiontryonce-and-cooldownms-disabled-for-single-threaded-drivers-connecting-to-mongocryptd

`What's The Deal With Metadataclient, Keyvaultclient, And The Internal Client?`_
================================================================================

.. _what's the deal with metadataclient, keyvaultclient, and the internal client?: ./auth.md#what-s-the-deal-with-metadataclient-keyvaultclient-and-the-internal-client

`Why Not Reuse The Parent Mongoclient When Maxpoolsize Is Limited?`_
--------------------------------------------------------------------

.. _why not reuse the parent mongoclient when maxpoolsize is limited?: ./auth.md#why-not-reuse-the-parent-mongoclient-when-maxpoolsize-is-limited

`Why Is Keyvaultclient An Exposed Option, But Metadataclient Private?`_
-----------------------------------------------------------------------

.. _why is keyvaultclient an exposed option, but metadataclient private?: ./auth.md#why-is-keyvaultclient-an-exposed-option-but-metadataclient-private

`Why Is The Metadataclient Not Needed If Bypassautoencryption=true`_
--------------------------------------------------------------------

.. _why is the metadataclient not needed if bypassautoencryption=true: ./auth.md#why-is-the-metadataclient-not-needed-if-bypassautoencryption-true

`Why Are Commands Sent To Mongocryptd On Collections Without Encrypted Fields?`_
================================================================================

.. _why are commands sent to mongocryptd on collections without encrypted fields?: ./auth.md#why-are-commands-sent-to-mongocryptd-on-collections-without-encrypted-fields

`Why Do Kms Providers Require Tls Options?`_
============================================

.. _why do kms providers require tls options?: ./auth.md#why-do-kms-providers-require-tls-options

`Why Is It An Error To Have An Fle 1 And Queryable Encryption Field In The Same Collection?`_
=============================================================================================

.. _why is it an error to have an fle 1 and queryable encryption field in the same collection?: ./auth.md#why-is-it-an-error-to-have-an-fle-1-and-queryable-encryption-field-in-the-same-collection

`Is It An Error To Set Schemamap And Encryptedfieldsmap?`_
==========================================================

.. _is it an error to set schemamap and encryptedfieldsmap?: ./auth.md#is-it-an-error-to-set-schemamap-and-encryptedfieldsmap

`Why Is Bypassqueryanalysis Needed?`_
=====================================

.. _why is bypassqueryanalysis needed?: ./auth.md#why-is-bypassqueryanalysis-needed

`Why Does Rewrapmanydatakey Return Rewrapmanydatakeyresult Instead Of Bulkwriteresult?`_
========================================================================================

.. _why does rewrapmanydatakey return rewrapmanydatakeyresult instead of bulkwriteresult?: ./auth.md#why-does-rewrapmanydatakey-return-rewrapmanydatakeyresult-instead-of-bulkwriteresult

`Why Does Clientencryption Have Key Management Functions When Drivers Can Use Existing Crud Operations Instead?`_
=================================================================================================================

.. _why does clientencryption have key management functions when drivers can use existing crud operations instead?: ./auth.md#why-does-clientencryption-have-key-management-functions-when-drivers-can-use-existing-crud-operations-instead

`Why Are The Querytype And Algorithm Options A String?`_
========================================================

.. _why are the querytype and algorithm options a string?: ./auth.md#why-are-the-querytype-and-algorithm-options-a-string

`Why Is There An Encryptexpression Helper?`_
============================================

.. _why is there an encryptexpression helper?: ./auth.md#why-is-there-an-encryptexpression-helper

`Why Do On-demand Kms Credentials Not Support Named Kms Providers?`_
====================================================================

.. _why do on-demand kms credentials not support named kms providers?: ./auth.md#why-do-on-demand-kms-credentials-not-support-named-kms-providers

`Future Work`_
**************

.. _future work: ./auth.md#future-work

`Make Libmonogocrypt Cache Window Configurable`_
================================================

.. _make libmonogocrypt cache window configurable: ./auth.md#make-libmonogocrypt-cache-window-configurable

`Apm Events For Encryption Or Key Service Interaction`_
=======================================================

.. _apm events for encryption or key service interaction: ./auth.md#apm-events-for-encryption-or-key-service-interaction

`Remove Mongocryptd`_
=====================

.. _remove mongocryptd: ./auth.md#remove-mongocryptd

`Support External Key Vault Collection Discovery`_
==================================================

.. _support external key vault collection discovery: ./auth.md#support-external-key-vault-collection-discovery

`Batch Listcollections Requests On Expired Schema Cache Entries`_
=================================================================

.. _batch listcollections requests on expired schema cache entries: ./auth.md#batch-listcollections-requests-on-expired-schema-cache-entries

`Add A Maximum Size For The Jsonschema/key Cache.`_
===================================================

.. _add a maximum size for the jsonschema/key cache.: ./auth.md#add-a-maximum-size-for-the-jsonschema-key-cache

`Recalculate Message Size Bounds Dynamically`_
==============================================

.. _recalculate message size bounds dynamically: ./auth.md#recalculate-message-size-bounds-dynamically

`Support Sessions In Key Management Functions`_
===============================================

.. _support sessions in key management functions: ./auth.md#support-sessions-in-key-management-functions

`Changelog`_
************

.. _changelog: ./auth.md#changelog

