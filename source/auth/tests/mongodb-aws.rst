===========
MongoDB AWS
===========

There are 6 scenarios drivers MUST test:

#. ``Regular Credentials``: Auth via an ``ACCESS_KEY_ID`` and ``SECRET_ACCESS_KEY`` pair
#. ``EC2 Credentials``: Auth from an EC2 instance via temporary credentials assigned to the machine
#. ``ECS Credentials``: Auth from an ECS instance via temporary credentials assigned to the task
#. ``Assume Role``: Auth via temporary credentials obtained from an STS AssumeRole request
#. ``Assume Role with Web Identity``: Auth via temporary credentials obtained from an STS AssumeRoleWithWebIdentity request
#. ``AWS Lambda``: Auth via environment variables ``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``, and ``AWS_SESSION_TOKEN``.
#. Caching of AWS credentials fetched by the driver.

For brevity, this section gives the values ``<AccessKeyId>``, ``<SecretAccessKey>`` and ``<Token>`` in place of a valid access key ID, secret access key and session token (also known as a security token). Note that if these values are passed into the URI they MUST be URL encoded. Sample values are below.

.. code-block:: 

  AccessKeyId=AKIAI44QH8DHBEXAMPLE
  SecretAccessKey=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
  Token=AQoDYXdzEJr...<remainder of security token>

.. sectnum::

Regular credentials
======================

Drivers MUST be able to authenticate by providing a valid access key id and secret access key pair as the username and password, respectively, in the MongoDB URI. An example of a valid URI would be:

.. code-block:: 

  mongodb://<AccessKeyId>:<SecretAccessKey>@localhost/?authMechanism=MONGODB-AWS

EC2 Credentials
===============

Drivers MUST be able to authenticate from an EC2 instance via temporary credentials assigned to the machine. A sample URI on an EC2 machine would be:

.. code-block::
  
  mongodb://localhost/?authMechanism=MONGODB-AWS

.. note:: No username, password or session token is passed into the URI. Drivers MUST query the EC2 instance endpoint to obtain these credentials.

ECS instance
============

Drivers MUST be able to authenticate from an ECS container via temporary credentials. A sample URI in an ECS container would be:

.. code-block::

  mongodb://localhost/?authMechanism=MONGODB-AWS

.. note:: No username, password or session token is passed into the URI. Drivers MUST query the ECS container endpoint to obtain these credentials.

AssumeRole
==========

Drivers MUST be able to authenticate using temporary credentials returned from an assume role request. These temporary credentials consist of an access key ID, a secret access key, and a security token passed into the URI. A sample URI would be: 

.. code-block::

  mongodb://<AccessKeyId>:<SecretAccessKey>@localhost/?authMechanism=MONGODB-AWS&authMechanismProperties=AWS_SESSION_TOKEN:<Token>

Assume Role with Web Identity
=============================

Drivers MUST be able to authentiate using a valid OIDC token and associated
role ARN taken from environment variables, respectively:

.. code-block::
  AWS_WEB_IDENTITY_TOKEN_FILE
  AWS_ROLE_ARN
  AWS_ROLE_SESSION_NAME (optional)

A sample URI in for a web identity test would be:

.. code-block::

  mongodb://localhost/?authMechanism=MONGODB-AWS

Drivers MUST test with and without AWS_ROLE_SESSION_NAME set.

.. note:: No username, password or session token is passed into the URI.
Drivers MUST check the environment variables listed above and make an `AssumeRoleWithWebIdentity request <https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html>`_ to obtain
credentials.

AWS Lambda
==========

Drivers MUST be able to authenticate via an access key ID, secret access key and optional session token taken from the environment variables, respectively: 

.. code-block::

  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY 
  AWS_SESSION_TOKEN

Sample URIs both with and without optional session tokens set are shown below. Drivers MUST test both cases.

.. code-block:: bash

  # without a session token
  export AWS_ACCESS_KEY_ID="<AccessKeyId>"
  export AWS_SECRET_ACCESS_KEY="<SecretAccessKey>"

  URI="mongodb://localhost/?authMechanism=MONGODB-AWS"

.. code-block:: bash

  # with a session token
  export AWS_ACCESS_KEY_ID="<AccessKeyId>"
  export AWS_SECRET_ACCESS_KEY="<SecretAccessKey>"
  export AWS_SESSION_TOKEN="<Token>"

  URI="mongodb://localhost/?authMechanism=MONGODB-AWS"

.. note:: No username, password or session token is passed into the URI. Drivers MUST check the environment variables listed above for these values. If the session token is set Drivers MUST use it.


Cached Credentials
==================

Drivers MUST ensure that they are testing the ability to cache credentials.
Drivers will need to be able to query and override the cached credentials to
verify usage.  To determine whether to run the cache tests, the driver can
check for the absence of the AWS_ACCESS_KEY_ID and of credentials in the URI.

#. Clear the cache.
#. Create a new client.
#. Ensure that a ``find`` operation adds credentials to the cache..
#. Override the cached credentials with an "Expiration" that is within one
   minute of the current UTC time.
#. Create a new client.
#. Ensure that a ``find`` operation updates the credentials in the cache.
#. Poison the cache with garbage content.
#. Create a new client.
#. Ensure that a ``find`` operation results in an error.
#. Ensure that the cache has been cleared.
#. Ensure that a subsequent ``find`` operation succeeds.
#. Ensure that the cache has been set.
