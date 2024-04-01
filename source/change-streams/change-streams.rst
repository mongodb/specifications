
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

.. _change streams: ./change-streams.md#change-streams

`Abstract`_
***********

.. _abstract: ./change-streams.md#abstract

`Specification`_
****************

.. _specification: ./change-streams.md#specification

`Definitions`_
==============

.. _definitions: ./change-streams.md#definitions

`Meta`_
-------

.. _meta: ./change-streams.md#meta

`Terms`_
--------

.. _terms: ./change-streams.md#terms

`Resumable Error`_
^^^^^^^^^^^^^^^^^^

.. _resumable error: ./change-streams.md#resumable-error

`Guidance`_
===========

.. _guidance: ./change-streams.md#guidance

`Server Specification`_
=======================

.. _server specification: ./change-streams.md#server-specification

`Response Format`_
------------------

.. _response format: ./change-streams.md#response-format

`Driver Api`_
=============

.. _driver api: ./change-streams.md#driver-api

`Helper Method`_
----------------

.. _helper method: ./change-streams.md#helper-method

`Collection.watch Helper`_
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _collection.watch helper: ./change-streams.md#collection-watch-helper

`Database.watch Helper`_
^^^^^^^^^^^^^^^^^^^^^^^^

.. _database.watch helper: ./change-streams.md#database-watch-helper

`Mongoclient.watch Helper`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _mongoclient.watch helper: ./change-streams.md#mongoclient-watch-helper

`Changestream`_
---------------

.. _changestream: ./change-streams.md#changestream

`Single Server Topologies`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _single server topologies: ./change-streams.md#single-server-topologies

`Startatoperationtime`_
^^^^^^^^^^^^^^^^^^^^^^^

.. _startatoperationtime: ./change-streams.md#startatoperationtime

`Resumeafter`_
^^^^^^^^^^^^^^

.. _resumeafter: ./change-streams.md#resumeafter

`Resume Process`_
^^^^^^^^^^^^^^^^^

.. _resume process: ./change-streams.md#resume-process

`Exposing All Resume Tokens`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _exposing all resume tokens: ./change-streams.md#exposing-all-resume-tokens

`Timeouts`_
^^^^^^^^^^^

.. _timeouts: ./change-streams.md#timeouts

`Notes And Restrictions`_
^^^^^^^^^^^^^^^^^^^^^^^^^

.. _notes and restrictions: ./change-streams.md#notes-and-restrictions

`Rationale`_
************

.. _rationale: ./change-streams.md#rationale

`Why Helper Methods?`_
======================

.. _why helper methods?: ./change-streams.md#why-helper-methods

`Why Are Changestreams Required To Retry Once On A Resumable Error?`_
=====================================================================

.. _why are changestreams required to retry once on a resumable error?: ./change-streams.md#why-are-changestreams-required-to-retry-once-on-a-resumable-error

`Why Do We Allow Access To The Resume Token To Users`_
======================================================

.. _why do we allow access to the resume token to users: ./change-streams.md#why-do-we-allow-access-to-the-resume-token-to-users

`Why Is There No Example Of The Desired User Experience?`_
==========================================================

.. _why is there no example of the desired user experience?: ./change-streams.md#why-is-there-no-example-of-the-desired-user-experience

`Why Is An Allow List Of Error Codes Preferable To A Deny List?`_
=================================================================

.. _why is an allow list of error codes preferable to a deny list?: ./change-streams.md#why-is-an-allow-list-of-error-codes-preferable-to-a-deny-list

`Why Is Cursornotfound Special-cased When Determining Resumability?`_
=====================================================================

.. _why is cursornotfound special-cased when determining resumability?: ./change-streams.md#why-is-cursornotfound-special-cased-when-determining-resumability

`Why Do We Need To Send A Default Startatoperationtime When Resuming A Changestream?`_
======================================================================================

.. _why do we need to send a default startatoperationtime when resuming a changestream?: ./change-streams.md#why-do-we-need-to-send-a-default-startatoperationtime-when-resuming-a-changestream

`Why Do We Need To Expose The Postbatchresumetoken?`_
=====================================================

.. _why do we need to expose the postbatchresumetoken?: ./change-streams.md#why-do-we-need-to-expose-the-postbatchresumetoken

`Test Plan`_
************

.. _test plan: ./change-streams.md#test-plan

`Backwards Compatibility`_
**************************

.. _backwards compatibility: ./change-streams.md#backwards-compatibility

`Reference Implementations`_
****************************

.. _reference implementations: ./change-streams.md#reference-implementations

`Changelog`_
************

.. _changelog: ./change-streams.md#changelog
