============
MongoDB OIDC
============

Local Testing
=============

To test locally, use the `oidc_get_tokens.sh`_ script from
drivers-evergreen-tools_ to download a set of OIDC tokens, including
`test_user1` and `test_user1_expires`. You first have to install the AWS CLI and
login using the SSO flow.

For example, if the selected AWS profile ID is "drivers-test", run:

.. code:: shell

  aws configure sso
  AWS_PROFILE="drivers-test" ./oidc_get_tokens.sh
  AWS_WEB_IDENTITY_TOKEN_FILE="/tmp/tokens/test_user1" /my/test/command

.. _oidc_get_tokens.sh: https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/auth_oidc/oidc_get_tokens.sh
.. _drivers-evergreen-tools: https://github.com/mongodb-labs/drivers-evergreen-tools/

----------

Prose Tests
===========

Drivers MUST implement all prose tests in this section.

(1) OIDC Callback Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**1.1 Callback is called during authentication**

- Create a ``MongoClient`` configured with an OIDC callback that implements the
  AWS provider logic.
- Perform a ``find`` operation that succeeds.
- Verify that the callback was called 1 time.
- Close the client.

**1.2 Callback is called during reauthentication**

- Create a ``MongoClient`` configured with an OIDC callback that implements the
  AWS provider logic.
- Set a fail point for ``find`` commands of the form:

.. code:: javascript

    {
      configureFailPoint: "failCommand",
      mode: {
        times: 1
      },
      data: {
        failCommands: [
          "find"
        ],
        errorCode: 391
      }
    }

- Perform a ``find`` operation that succeeds.
- Verify that the callback was called 2 times (once during the connection
  handshake, and again during reauthentication).
- Close the client.

(2) OIDC Callback Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**2.1 Valid Callback Inputs**

- Create a ``MongoClient`` with an OIDC callback that validates its inputs and
  returns a valid access token.
- Perform a ``find`` operation that succeeds.
- Verify that the OIDC callback was called with the appropriate inputs,
  including the timeout parameter if possible. Ensure that there are no
  unexpected fields.
- Close the client.

**2.2 OIDC Callback Returns Null**

- Create a ``MongoClient`` with an OIDC callback that returns ``null``.
- Perform a ``find`` operation that fails.
- Close the client.

**2.3 OIDC Callback Returns Missing Data**

- Create a ``MongoClient`` with an OIDC callback that returns data not
  conforming to the ``OIDCCredential`` with missing fields.
- Perform a ``find`` operation that fails.
- Close the client.

**2.4 OIDC Callback Returns Invalid Data**

- Create a ``MongoClient`` with an OIDC callback that returns data not
  conforming to the ``OIDCCredential`` with extra fields.
- Perform a ``find`` operation that fails.
- Close the client.

(3) Authentication Failure
~~~~~~~~~~~~~~~~~~~~~~~~~~

**3.1 Authentication failure with cached tokens fetch a new token and retry**

- Create a ``MongoClient`` configured with ``retryReads=false`` and an OIDC
  callback that implements the AWS provider logic.
- Poison the cache with an invalid access token.
- Perform a ``find`` operation that succeeds.
- Verify that the callback was called 1 time.
- Close the client.

**3.2 Authentication failures without cached tokens return an error**

- Create a ``MongoClient`` configured with ``retryReads=false`` and an OIDC
  callback that always returns invalid access tokens.
- Perform a ``find`` operation that fails.
- Verify that the callback was called 1 time.
- Close the client.

(3) Reauthentication
~~~~~~~~~~~~~~~~~~~~

TODO:
- Custom callback and provider_name returns error
- Reauthentication succeeds on multiple connections


----------

Human Authentication Flow Prose Tests
=====================================

Drivers that support the `Human Authentication Flow
<../auth/auth.rst#human-authentication-flow>`_ MUST implement all prose tests in
this section.

Drivers MUST be able to authenticate against a server configured with either one
or two configured identity providers.

Note that typically the preconfigured Atlas Dev clusters are used for testing,
in Evergreen and localy. The URIs can be fetched from the ``drivers/oidc``
Secrets vault, see `vault instructions`_. Use ``OIDC_ATLAS_URI_SINGLE`` for
``MONGODB_URI_SINGLE`` and ``OIDC_ATLAS_URI_MULTI`` for
``OIDC_ATLAS_URI_MULTI``.

If using local servers is preferred, using the `Local Testing`_ method, use
``mongodb://localhost/?authMechanism=MONGODB-OIDC`` for ``MONGODB_URI_SINGLE``
and
``mongodb://localhost:27018/?authMechanism=MONGODB-OIDC&directConnection=true&readPreference=secondaryPreferred``
for ``MONGODB_URI_MULTI`` because the other server is a secondary on a replica
set, on port ``27018``.

The default OIDC client used in the tests will be configured with
``MONGODB_URI_SINGLE`` and a valid human callback handler that returns the
``test_user1`` local token in ``OIDC_TOKEN_DIR`` as the "access_token", and a
dummy "refresh_token".

.. _Local Testing: https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/auth_oidc/README.md#local-testing
.. _vault instructions: https://wiki.corp.mongodb.com/display/DRIVERS/Using+AWS+Secrets+Manager+to+Store+Testing+Secrets

(1) Human Callback Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers MUST be able to authenticate using OIDC callback(s) when there
is one principal configured.

**1.1 Single Principal Implicit Username**

- Create default OIDC client with `authMechanism=MONGODB-OIDC`.
- Perform a ``find`` operation that succeeds.
- Close the client.

**1.2 Single Principal Explicit Username**

- Create a client with ``MONGODB_URI_SINGLE``, a username of ``test_user1``,
  `authMechanism=MONGODB-OIDC`, and the OIDC human callback.
- Perform a ``find`` operation that succeeds.
- Close the client.

**1.3 Multiple Principal User 1**

- Create a client with ``MONGODB_URI_MULTI``, a username of ``test_user1``,
  `authMechanism=MONGODB-OIDC`, and the OIDC human callback.
- Perform a ``find`` operation that succeeds.
- Close the client.

**1.4 Multiple Principal User 2**

- Create a human callback that reads in the generated ``test_user2`` token file.
- Create a client with ``MONGODB_URI_MULTI``, a username of ``test_user2``,
  `authMechanism=MONGODB-OIDC`, and the OIDC human callback.
- Perform a ``find`` operation that succeeds.
- Close the client.

**1.5 Multiple Principal No User**

- Create a client with ``MONGODB_URI_MULTI``, no username,
  `authMechanism=MONGODB-OIDC`, and the OIDC human callback.
- Assert that a ``find`` operation fails.
- Close the client.

**1.6 Allowed Hosts Blocked**

- Create a default OIDC client, with an ``ALLOWED_HOSTS`` that is an empty list.
- Assert that a ``find`` operation fails with a client-side error.
- Close the client.
- Create a client that uses the URL
  ``mongodb://localhost/?authMechanism=MONGODB-OIDC&ignored=example.com``, a
  human callback, and an ``ALLOWED_HOSTS`` that contains ``["example.com"]``.
- Assert that a ``find`` operation fails with a client-side error.
- Close the client.

(2) Human Callback Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**2.1 Valid Callback Inputs**

- Create a ``MongoClient`` with a human callback that validates its inputs and
  returns a valid access token.
- Perform a ``find`` operation that succeeds. Verify that the human
  callback was called with the appropriate inputs, including the timeout
  parameter if possible. Ensure that there are no unexpected fields.
- Close the client.

**2.3 Human Callback Returns Missing Data**

- Create a ``MongoClient`` with a human callback that returns data not conforming to
  the ``OIDCCredential`` with missing fields.
- Perform a ``find`` operation that fails.
- Close the client.

**2.4 OIDC Callback Returns Invalid Data**

- Create a ``MongoClient`` with a human callback that returns data not
  conforming to the ``OIDCCredential`` with extra fields.
- Perform a ``find`` operation that fails.
- Close the client.

(3) Speculative Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
We can only test the successful case, by verifying that ``saslStart``
is not called.

- Create a ``MongoClient`` with a human callback that returns a valid token.
- Set a fail point for ``saslStart`` commands of the form:

.. code:: javascript

    {
      configureFailPoint: "failCommand",
      mode: "alwaysOn",
      data: {
        failCommands: [
          "saslStart"
        ],
        errorCode: 20
      }
    }

.. note::

  The driver MUST either use a unique ``appName`` or explicitly
  remove the ``failCommand`` after the test to prevent leakage.

- Perform a ``find`` operation that succeeds.
- Close the client.

(4) Reauthentication
~~~~~~~~~~~~~~~~~~~~

The driver MUST test reauthentication with MONGODB-OIDC for a read
operation.

**4.1 Succeeds**

- Create a default OIDC client and add an event listener.  The following
  assumes that the driver does not emit ``saslStart`` or ``saslContinue``
  events.  If the driver does emit those events, ignore/filter them for the
  purposes of this test.
- Perform a ``find`` operation that succeeds.
- Assert that the human callback has been called once.
- Clear the listener state if possible.
- Force a reauthenication using a ``failCommand`` of the form:

.. code:: javascript

    {
      configureFailPoint: "failCommand",
      mode: {
        times: 1
      },
      data: {
        failCommands: [
          "find"
        ],
        errorCode: 391
      }
    }

.. note::

  the driver MUST either use a unique ``appName`` or explicitly
  remove the ``failCommand`` after the test to prevent leakage.

- Perform another find operation that succeeds.
- Assert that the human callback has been called twice.
- Assert that the ordering of list started events is [``find``],
  , ``find``.  Note that if the listener stat could not be cleared then there
  will and be extra ``find`` command.
- Assert that the list of command succeeded events is [``find``].
- Assert that a ``find`` operation failed once during the command execution.
- Close the client.

**4.2 Succeeds no refresh**

- Create a default OIDC client with a human callback that does not return
  a refresh token.
- Perform a ``find`` operation that succeeds.
- Assert that the human callback has been called once.
- Force a reauthenication using a ``failCommand`` of the form:

.. code:: javascript

    {
      configureFailPoint: "failCommand",
      mode: {
        times: 1
      },
      data: {
        failCommands: [
          "find"
        ],
        errorCode: 391
      }
    }

- Perform a ``find`` operation that succeeds.
- Assert that the human callback has been called twice.
- Close the client.

**4.3 Succeeds after refresh fails**

- Create a default OIDC client.
- Perform a ``find`` operation that succeeds.
- Assert that the human callback has been called once.
- Force a reauthenication using a ``failCommand`` of the form:

.. code:: javascript

    {
      configureFailPoint: "failCommand",
      mode: {
        times: 2
      },
      data: {
        failCommands: [
          "find", "saslContinue"
        ],
        errorCode: 391
      }
    }

- Perform a ``find`` operation that succeeds.
- Assert that the human callback has been called three times.
- Close the client.

**4.4 Fails**

- Create a default OIDC client.
- Perform a find operation that succeeds (to force a speculative auth).
- Assert that the human callback has been called once.
- Force a reauthenication using a failCommand of the form:

.. code:: javascript

  {
    "configureFailPoint": "failCommand",
    "mode": {
      "times": 2
    },
    "data": {
      "failCommands": [
        "find", "saslStart"
      ],
      "errorCode": 391
    }
  }

- Perform a find operation that fails.
- Assert that the human callback has been called twice.
- Close the client.

**4.5 Separate Connections Avoid Extra Callback Calls**

The following test assumes that the driver will be able to share a cache between
two MongoClient objects, or ensure that the same MongoClient is used with two
different connections.  Otherwise, the test would have a race condition.
If neither is possible, the test may be skipped.

- Create a human callback that returns valid, and ensure that we can record the
  number of times the callback is called.
- Create two clients using the callbacks, or a single client and two connection
  objects.
- Peform a find operation on each client/connection that succeeds.
- If using a single client, share the underlying cache between clients.
- Ensure that the human callback has been called twice.
- Force a reauthenication on the first client/connection using a ``failCommand``
  of the form:

.. code:: javascript

    {
      configureFailPoint: "failCommand",
      mode: {
        times: 1
      },
      data: {
        failCommands: [
          "find"
        ],
        errorCode: 391
      }
    }

- Perform a ``find`` operation that succeds.
- Ensure that the human callback has been called three times.
- Repeat the ``failCommand`` and ``find`` operation on the second
  client/connection.
- Ensure that the human callback has been called three times.
- Close all clients/connections.
