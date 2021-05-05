=========================
Versioned API For Drivers
=========================

:Spec Title: Versioned API For Drivers
:Spec Version: 1.2.0
:Author: Andreas Braun
:Advisors: Jeff Yemin, A. Jesse Jiryu Davis, Patrick Freed, Oleg Pudeyev
:Status: Accepted
:Type: Standards
:Minimum Server Version: N/A
:Last Modified: 2021-05-05

.. contents::

--------

Abstract
========

As MongoDB moves toward more frequent releases (a.k.a. continuous delivery), we
want to enable users to take advantage of our rapidly released features, without
exposing applications to incompatible server changes due to automatic server
upgrades. A versioned API will help accomplish that goal.


META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`__.

This document tends to use "SHOULD" more frequently than other specifications,
but mainly in the context of providing guidance on writing test files. This is
discussed in more detail in `Design Rationale`_.


Specification
=============

Background
----------

When applications interact with MongoDB, both the driver and the server
participate in executing operations. Therefore, when determining application
compatibility with MongoDB, both the driver and the server behavior must be
taken into account.

An application can specify the server API version when creating MongoClient.
When this is done:

- The client sends the specified API version to the server, causing the server
  to behave in a manner compatible with that API version.
- The driver will behave in a manner compatible with a server configured with
  that API version, regardless of the server's actual release version.

Presently there is no specification for how a driver must behave when a
particular server API version is requested, or what driver operations are
subject to API compatibility guarantees. Such requirements may be stipulated in
subsequent specifications.

This specification requires MongoClient to validate that it supports the
specified server API version, if any, but does not define what such support
means.


``MongoClient`` changes
-----------------------

``MongoClient`` instances accept a new ``serverApi`` option to allow the user to
declare an API version:

.. code:: typescript

   class MongoClient {
       MongoClient(... serverApi: ServerApi);
   }

   enum ServerApiVersion {
       v1 = "1",
   }

   class ServerApi {
       version: string|ServerApiVersion;
       strict: Optional<Boolean>; // Default false
       deprecationErrors: Optional<Boolean>; // Default false
   }

Drivers SHOULD group the ``serverApi`` option with other similar client options
like ``autoEncryptionOpts``. Drivers MUST NOT allow specification of any
versioned API options via the connection string. See the
`design rationale <_rationale_no_uri_options>`_ for more details.


ServerApiVersion enumeration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This specification and subsequent specifications will define the known API
versions. Drivers SHOULD define an enumeration containing the known API
versions, using the version identifiers given. Drivers MAY deviate from the
version identifiers used in this and subsequent specifications if doing so is
necessary given the driver's programming language's constraints. Drivers MUST
ensure that adding new API versions to this enumeration does not result in
backward compatibility breaks in non-major releases. This can be the case in
languages that allow exhaustive ``switch`` statements (e.g. Swift).

Drivers for languages that don't have enums (e.g. PHP) MUST expose the version
as a string, but SHOULD offer constants to allow for IDE features such as code
completion. In these cases, the driver MUST validate (e.g. when the application
provides a version string to the ``ServerApi`` class) that the version string is
valid and trigger a client-side error if an unknown API version was used.


ServerApi class
~~~~~~~~~~~~~~~

The ``ServerApi`` class stores an API version, along with flags that decide
whether or not unknown or deprecated commands in the specified API version
trigger a server-side error. A ``version`` MUST be specified when declaring an
API version, while the ``strict`` and ``deprecationErrors`` options are both
optional. The ``ServerApi`` class is considered immutable; changes to the
declared API version MUST be prohibited.


Declared Version Inheritance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers MUST ensure that users cannot override the API version declared in the
``MongoClient`` instance. This includes the ``MongoDatabase`` and
``MongoCollection`` classes, as well as any operations in these classes. See the
rationale for more details.


Sending Declared API Version to the Server
------------------------------------------

The declared API version MUST be sent to the server as part of every command
request, with the exception of the cases listed below. Drivers MUST NOT use a
server's reported ``maxWireVersion`` to decide whether it supports the versioned
API. The server will reply with an error if the declared API version is not
supported, or if the command does not support API versioning options. If the
user does not declare an API version, the driver MUST NOT send any API
versioning options to the server.

This requirement applies to all command requests, regardless of whether they are
sent using ``OP_MSG`` or ``OP_QUERY`` (e.g. during the initial handshake). For
all other opcodes, including pre-command usage of ``OP_QUERY``, drivers MUST NOT
attempt to send API version parameters to the server.


Command Syntax
~~~~~~~~~~~~~~

The options from the declared API version are mapped to the following command
options:

===================== ========================
**ServerApi field**   **Command option**
``version``           ``apiVersion``
``strict``            ``apiStrict``
``deprecationErrors`` ``apiDeprecationErrors``
===================== ========================

If an API version was declared, drivers MUST add the ``apiVersion`` option to
every command that is sent to a server. Drivers MUST add the ``apiStrict`` and
``apiDeprecationErrors`` options if they were specified by the user, even when
the specified value is equal to the server default. Drivers MUST NOT add any
API versioning options if the user did not specify them.
This includes the ``getMore`` command as well as all commands that are part of a
transaction. A previous version of this specification excluded those commands,
but that has since changed in the server.


Handshake behavior
~~~~~~~~~~~~~~~~~~

If an API version was declared, drivers MUST NOT use the legacy hello command
during the initial handshake or afterwards. Instead, drivers MUST use the
``hello`` command exclusively. If the server does not support ``hello``, the
server description MUST reflect this with an ``Unknown`` server type.


Cursors
~~~~~~~

For ``getMore``, drivers MUST submit API parameters. If the values given do not
match the API parameters given in the cursor-initiating command, the server will
reply with an error.


Transactions
~~~~~~~~~~~~

When running commands as part of a transaction, drivers MUST send API parameters
with all commands that are part of a transaction. If the API parameters for a
command in a transaction do not match those of the transaction-starting command,
the server will reply with an error.


Generic command helper
~~~~~~~~~~~~~~~~~~~~~~

Drivers that offer a generic command helper (e.g. ``command()`` or
``runCommand()``) MUST NOT inspect the command document to detect API versioning
options. As with all other commands, drivers MUST inherit the API version from
the client. Specifying API versioning options in the command document and
declaring an API version on the client is not supported. Drivers MUST document
that the behaviour of the command helper is undefined in this case.


Design Rationale
================

.. _rationale_no_uri_options:

No URI Options
--------------

Since changing the API version can cause the application to behave differently,
drivers MUST NOT allow users to change the declared API version without
deploying code changes. This ensures that users don't copy a connection string
with a declared API version that may be different from what their application
expects. A URI option can be added later if we realise our users need it, while
the opposite is not easily accomplished.


Don't Allow Overriding the Declared API Version
-----------------------------------------------

While users are used to overriding options like read preference, read concern,
and write concern in ``MongoDatabase`` and ``MongoCollection`` objects, or on an
operation level, we explicitly decided against this for the declared API
version. With a single API version available to start, we can't anticipate what
use cases users may have to override the API version. Not including this feature
at the beginning allows us to gather feedback on use cases and add the features
users are looking for. On the other hand, adding the ability to override the
declared API version can't be undone until a future major release, which is
almost impossible to accomplish across all drivers.


Generic Command Helper Behaviour
--------------------------------

The runCommand helper is a way for the user to run a native command with the
driver doing little to no inspection in the command. This allows users to run
arbitrary commands that may not have helpers in the driver, or to pass options
that are not supported by the driver version they are currently using. Commands
run using this helper do not inherit any ``readConcern`` or ``writeConcern``
options that may have been set on the ``MongoClient`` or ``MongoDatabase``
objects.

However, the declared API version is a different case. We are introducing this
feature to give users a certain peace of mind when upgrading driver or server
versions, by ensuring that their code will continue to show the same behaviour
they've gotten used to. This includes all commands run using the generic command
helper. Thus, the helper will inherit the API version declared on the client.


Hardcode supported versions in drivers
--------------------------------------

Since a new API version might require driver changes (e.g. to account for
removed commands), we don't yet know what changes drivers must make for a future
version. Until we do, we must prevent users from choosing any unknown API
version.


Backward Compatibility
======================

Driver changes are fully backward compatible. Not declaring an API version when
creating a client may cause an error if the server was started with the
``requireApiVersion`` option enabled, but this is outside of driver control.


Future Work
===========

Overriding the Declared API Version
-----------------------------------

In the future, we may want to allow users to override the declared API version
on a ``MongoDatabase``, ``MongoCollection``, or individual operation level.
However, this is not necessary until there is a different API version and we
have data on why and how users would want to override the declared API version.


Versioned CRUD API
------------------

Drivers may also want to provide versioned ``MongoClient``, ``MongoDatabase``,
and ``MongoCollection`` classes to only include features that are part of the
versioned API. This is not covered in this specification.


Change Log
==========

* 2021-05-05: Require sending versioned API parameters with ``getMore`` and
  transaction-continuing commands.
* 2021-04-20: Require using ``hello`` when using the versioned API.
* 2021-04-10: Replaced usages of ``acceptAPIVersion2`` with ``acceptApiVersion2``.
