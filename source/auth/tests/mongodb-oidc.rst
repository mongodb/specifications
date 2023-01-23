============
MongoDB OIDC
============

Drivers MUST test the following scenarios:

#. ``Authorization Code Flow``
#. ``AWS Device Flow``
#. ``Multiple Principals``
#. ``Caching``


.. sectnum::

Authorization Code Flow
=======================

Drivers MUST be able to authenticate using OIDC callback(s) when there
is one principal configured.

An example of a valid URI would be:

.. code-block::

  mongodb://localhost/?authMechanism=MONGODB-OIDC

The following URI would also be valid, if it matches the single principal name:

.. code-block::

  mongodb://localhost/?authMechanism=MONGODB-OIDC&authMechanismProperties=PRINCIPAL_NAME:<PRINCIPAL>


AWS Device Flow
===============

Drivers MUST be able to authenticate using the "aws" device workflow on an EC2 instance when there is one principal configured.

.. code-block::

  mongodb://localhost/?authMechanism=MONGODB-OIDC&authMechanismProperties=DEVICE_NAME=aws

The following URI would also be valid, if it matches the single principal name:

.. code-block::

  mongodb://localhost/?authMechanism=MONGODB-OIDC&authMechanismProperties=PRINCIPAL_NAME:<PRINCIPAL>,DEVICE_NAME:aws


Multiple Principals
===================

Drivers MUST be able to authenticate using either authentication or device
type if there are multiple principals configured on the server.

.. code-block::

  mongodb://localhost/?authMechanism=MONGODB-OIDC&authMechanismProperties=PRINCIPAL_NAME:<PRINCIPAL1>

  mongodb://localhost/?authMechanism=MONGODB-OIDC&authMechanismProperties=PRINCIPAL_NAME"<PRINCIPAL2>,DEVICE_NAME:aws

Drivers MUST ensure that the following URIs fail:

.. code-block::

  mongodb://localhost/?authMechanism=MONGODB-OIDC

  mongodb://localhost/?authMechanism=MONGODB-OIDC&authMechanismProperties=DEVICE_NAME:aws

Note: Even thogh only one of the the principals is using the device workflow,
if the user does not provide a principal name then they cannot be
distinguished, which is why the second URL should fail.


Cached Credentials
==================

Drivers MUST ensure that they are testing the ability to cache credentials.
Drivers will need to be able to query and override the cached credentials to
verify usage.  This test must be performed with the authorization code
workflow with and without a provided refresh callback.

#. Clear the cache.
#. Create a new client with a request callback and a refresh callback.  Both callbacks will read the contents of the ``AWS_WEB_IDENTITY_TOKEN_FILE`` location to obtain a valid access token.
#. Give a callback response with a valid accessToken and an expiresInSeconds
that is within one minute.
#. Ensure that a ``find`` operation adds credentials to the cache.
#. Create a new client with the same request callback and a refresh callback.
#. Ensure that a ``find`` operation results in a call to the refresh callback.

#. Clear the cache.
#. Create a new client with a request callback callback.
#. Give a callback response with a valid accessToken and an expiresInSeconds
that is within one minute.
#. Ensure that a ``find`` operation adds credentials to the cache.
#. Create a new client with the same request callback.
#. Ensure that a ``find`` operation results in a call to the request callback.

#. Poison the cache with an invalid access_token.
#. Create a new client with a request callback and a refresh callback.
#. Ensure that a ``find`` operation results in an error.
#. Ensure that the cache has been cleared.
#. Ensure that a subsequent ``find`` operation results in a call to the refresh callback.
#. Ensure that the cache has been set.
