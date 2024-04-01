
.. note::
  This specification has been converted to Markdown and renamed to
  `change-streams.md <change-streams.md>`_.  

  Use the link above to access the latest version of the specification as the
  current reStructuredText file will no longer be updated.

  Use the links below to access equivalent section names in the Markdown version of
  the specification.

#################
`Change Streams`_
#################

.. _change streams: ./auth.md#change-streams

`Abstract`_
***********

.. _abstract: ./auth.md#abstract

`Specification`_
****************

.. _specification: ./auth.md#specification

`Definitions`_
==============

.. _definitions: ./auth.md#definitions

`Meta`_
-------

.. _meta: ./auth.md#meta

`Terms`_
--------

.. _terms: ./auth.md#terms

`Resumable Error`_
^^^^^^^^^^^^^^^^^^

.. _resumable error: ./auth.md#resumable-error

`Guidance`_
===========

.. _guidance: ./auth.md#guidance

`Server Specification`_
=======================

.. _server specification: ./auth.md#server-specification

`Response Format`_
------------------

.. _response format: ./auth.md#response-format

`Driver Api`_
=============

.. _driver api: ./auth.md#driver-api

`Helper Method`_
----------------

.. _helper method: ./auth.md#helper-method

`Collection.watch Helper`_
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _collection.watch helper: ./auth.md#collection-watch-helper

`Database.watch Helper`_
^^^^^^^^^^^^^^^^^^^^^^^^

.. _database.watch helper: ./auth.md#database-watch-helper

`Mongoclient.watch Helper`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _mongoclient.watch helper: ./auth.md#mongoclient-watch-helper

`Changestream`_
---------------

.. _changestream: ./auth.md#changestream

`Single Server Topologies`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _single server topologies: ./auth.md#single-server-topologies

`Startatoperationtime`_
^^^^^^^^^^^^^^^^^^^^^^^

.. _startatoperationtime: ./auth.md#startatoperationtime

`Resumeafter`_
^^^^^^^^^^^^^^

.. _resumeafter: ./auth.md#resumeafter

`Resume Process`_
^^^^^^^^^^^^^^^^^

.. _resume process: ./auth.md#resume-process

`Exposing All Resume Tokens`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _exposing all resume tokens: ./auth.md#exposing-all-resume-tokens

`Timeouts`_
^^^^^^^^^^^

.. _timeouts: ./auth.md#timeouts

`Notes And Restrictions`_
^^^^^^^^^^^^^^^^^^^^^^^^^

.. _notes and restrictions: ./auth.md#notes-and-restrictions

`Rationale`_
************

.. _rationale: ./auth.md#rationale

`Why Helper Methods?`_
======================

.. _why helper methods?: ./auth.md#why-helper-methods

`Why Are Changestreams Required To Retry Once On A Resumable Error?`_
=====================================================================

.. _why are changestreams required to retry once on a resumable error?: ./auth.md#why-are-changestreams-required-to-retry-once-on-a-resumable-error

`Why Do We Allow Access To The Resume Token To Users`_
======================================================

.. _why do we allow access to the resume token to users: ./auth.md#why-do-we-allow-access-to-the-resume-token-to-users

`Why Is There No Example Of The Desired User Experience?`_
==========================================================

.. _why is there no example of the desired user experience?: ./auth.md#why-is-there-no-example-of-the-desired-user-experience

`Why Is An Allow List Of Error Codes Preferable To A Deny List?`_
=================================================================

.. _why is an allow list of error codes preferable to a deny list?: ./auth.md#why-is-an-allow-list-of-error-codes-preferable-to-a-deny-list

`Why Is Cursornotfound Special-cased When Determining Resumability?`_
=====================================================================

.. _why is cursornotfound special-cased when determining resumability?: ./auth.md#why-is-cursornotfound-special-cased-when-determining-resumability

`Why Do We Need To Send A Default Startatoperationtime When Resuming A Changestream?`_
======================================================================================

.. _why do we need to send a default startatoperationtime when resuming a changestream?: ./auth.md#why-do-we-need-to-send-a-default-startatoperationtime-when-resuming-a-changestream

`Why Do We Need To Expose The Postbatchresumetoken?`_
=====================================================

.. _why do we need to expose the postbatchresumetoken?: ./auth.md#why-do-we-need-to-expose-the-postbatchresumetoken

`Test Plan`_
************

.. _test plan: ./auth.md#test-plan

`Backwards Compatibility`_
**************************

.. _backwards compatibility: ./auth.md#backwards-compatibility

`Reference Implementations`_
****************************

.. _reference implementations: ./auth.md#reference-implementations

`Changelog`_
************

.. _changelog: ./auth.md#changelog

