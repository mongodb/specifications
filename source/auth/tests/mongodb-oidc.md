# MongoDB OIDC

## Local Testing

To test locally, use the
[oidc_get_tokens.sh](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/auth_oidc/oidc_get_tokens.sh)
script from [drivers-evergreen-tools](https://github.com/mongodb-labs/drivers-evergreen-tools/) to download a set of
OIDC tokens, including `test_user1` and `test_user1_expires`. You first have to install the AWS CLI and login using the
SSO flow.

For example, if the selected AWS profile ID is "drivers-test", run:

```shell
aws configure sso
export OIDC_TOKEN_DIR=/tmp/tokens
AWS_PROFILE="drivers-test" oidc_get_tokens.sh
AWS_WEB_IDENTITY_TOKEN_FILE="$OIDC_TOKEN_DIR/test_user1" /my/test/command
```

______________________________________________________________________

## Prose Tests

Drivers MUST implement all prose tests in this section. Unless otherwise noted, all `MongoClient` instances MUST be
configured with `retryReads=false`.

> [!NOTE]
> For test cases that create fail points, drivers MUST either use a unique `appName` or explicitly remove the fail point
> after the test to prevent interaction between test cases.

Note that typically the preconfigured Atlas Dev clusters are used for testing, in Evergreen and locally. The URIs can be
fetched from the `drivers/oidc` Secrets vault, see
[vault instructions](https://wiki.corp.mongodb.com/display/DRIVERS/Using+AWS+Secrets+Manager+to+Store+Testing+Secrets).
Use `OIDC_ATLAS_URI_SINGLE` for the `MONGODB_URI`. If using local servers is preferred, using the
[Local Testing](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/auth_oidc/README.md#local-testing)
method, use `mongodb://localhost/?authMechanism=MONGODB-OIDC` for `MONGODB_URI`.

### (1) OIDC Callback Authentication

**1.1 Callback is called during authentication**

- Create a `MongoClient` configured with an OIDC callback that implements the AWS provider logic.
- Perform a `find` operation that succeeds.
- Assert that the callback was called 1 time.
- Close the client.

**1.2 Callback is called once for multiple connections**

- Create a `MongoClient` configured with an OIDC callback that implements the AWS provider logic.
- Start 10 threads and run 100 `find` operations in each thread that all succeed.
- Assert that the callback was called 1 time.
- Close the client.

### (2) OIDC Callback Validation

**2.1 Valid Callback Inputs**

- Create a `MongoClient` configured with an OIDC callback that validates its inputs and returns a valid access token.
- Perform a `find` operation that succeeds.
- Assert that the OIDC callback was called with the appropriate inputs, including the timeout parameter if possible.
- Close the client.

**2.2 OIDC Callback Returns Null**

- Create a `MongoClient` configured with an OIDC callback that returns `null`.
- Perform a `find` operation that fails.
- Close the client.

**2.3 OIDC Callback Returns Missing Data**

- Create a `MongoClient` configured with an OIDC callback that returns data not conforming to the `OIDCCredential` with
  missing fields.
- Perform a `find` operation that fails.
- Close the client.

**2.4 Invalid Client Configuration with Callback**

- Create a `MongoClient` configured with an OIDC callback and auth mechanism property `PROVIDER_NAME:aws`.
- Assert it returns a client configuration error.

### (3) Authentication Failure

**3.1 Authentication failure with cached tokens fetch a new token and retry auth**

- Create a `MongoClient` configured with an OIDC callback that implements the AWS provider logic.
- Poison the *Client Cache* with an invalid access token.
- Perform a `find` operation that succeeds.
- Assert that the callback was called 1 time.
- Close the client.

**3.2 Authentication failures without cached tokens return an error**

- Create a `MongoClient` configured with an OIDC callback that always returns invalid access tokens.
- Perform a `find` operation that fails.
- Assert that the callback was called 1 time.
- Close the client.

### (4) Reauthentication

- Create a `MongoClient` configured with an OIDC callback that implements the AWS provider logic.
- Set a fail point for `find` commands of the form:

```javascript
{
  configureFailPoint: "failCommand",
  mode: {
    times: 1
  },
  data: {
    failCommands: [
      "find"
    ],
    errorCode: 391 // ReauthenticationRequired
  }
}
```

- Perform a `find` operation that succeeds.
- Assert that the callback was called 2 times (once during the connection handshake, and again during reauthentication).
- Close the client.

______________________________________________________________________

## Human Authentication Flow Prose Tests

Drivers that support the [Human Authentication Flow](../auth.md#human-authentication-flow) MUST implement all prose
tests in this section. Unless otherwise noted, all `MongoClient` instances MUST be configured with `retryReads=false`.

> [!NOTE]
> For test cases that create fail points, drivers MUST either use a unique `appName` or explicitly remove the fail point
> after the test to prevent interaction between test cases.

Drivers MUST be able to authenticate against a server configured with either one or two configured identity providers.

Note that typically the preconfigured Atlas Dev clusters are used for testing, in Evergreen and locally. The URIs can be
fetched from the `drivers/oidc` Secrets vault, see
[vault instructions](https://wiki.corp.mongodb.com/display/DRIVERS/Using+AWS+Secrets+Manager+to+Store+Testing+Secrets).
Use `OIDC_ATLAS_URI_SINGLE` for `MONGODB_URI_SINGLE` and `OIDC_ATLAS_URI_MULTI` for `MONGODB_URI_MULTI`. Currently the
`OIDC_ATLAS_URI_MULTI` cluster does not work correctly with fail points, so all prose tests that use fail points SHOULD
use `OIDC_ATLAS_URI_SINGLE`.

If using local servers is preferred, using the
[Local Testing](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/auth_oidc/README.md#local-testing)
method, use `mongodb://localhost/?authMechanism=MONGODB-OIDC` for `MONGODB_URI_SINGLE` and
`mongodb://localhost:27018/?authMechanism=MONGODB-OIDC&directConnection=true&readPreference=secondaryPreferred` for
`MONGODB_URI_MULTI` because the other server is a secondary on a replica set, on port `27018`.

The default OIDC client used in the tests is configured with `MONGODB_URI_SINGLE` and a valid human callback handler
that returns the `test_user1` local token in `OIDC_TOKEN_DIR` as the "access_token", and a dummy "refresh_token".

### (1) OIDC Human Callback Authentication

Drivers MUST be able to authenticate using OIDC callback(s) when there is one principal configured.

**1.1 Single Principal Implicit Username**

- Create default OIDC client with `authMechanism=MONGODB-OIDC`.
- Perform a `find` operation that succeeds.
- Close the client.

**1.2 Single Principal Explicit Username**

- Create a client with `MONGODB_URI_SINGLE`, a username of `test_user1`, `authMechanism=MONGODB-OIDC`, and the OIDC
  human callback.
- Perform a `find` operation that succeeds.
- Close the client.

**1.3 Multiple Principal User 1**

- Create a client with `MONGODB_URI_MULTI`, a username of `test_user1`, `authMechanism=MONGODB-OIDC`, and the OIDC human
  callback.
- Perform a `find` operation that succeeds.
- Close the client.

**1.4 Multiple Principal User 2**

- Create a human callback that reads in the generated `test_user2` token file.
- Create a client with `MONGODB_URI_MULTI`, a username of `test_user2`, `authMechanism=MONGODB-OIDC`, and the OIDC human
  callback.
- Perform a `find` operation that succeeds.
- Close the client.

**1.5 Multiple Principal No User**

- Create a client with `MONGODB_URI_MULTI`, no username, `authMechanism=MONGODB-OIDC`, and the OIDC human callback.
- Assert that a `find` operation fails.
- Close the client.

**1.6 Allowed Hosts Blocked**

- Create a default OIDC client, with an `ALLOWED_HOSTS` that is an empty list.
- Assert that a `find` operation fails with a client-side error.
- Close the client.
- Create a client that uses the URL `mongodb://localhost/?authMechanism=MONGODB-OIDC&ignored=example.com`, a human
  callback, and an `ALLOWED_HOSTS` that contains `["example.com"]`.
- Assert that a `find` operation fails with a client-side error.
- Close the client.

### (2) OIDC Human Callback Validation

**2.1 Valid Callback Inputs**

- Create a `MongoClient` with a human callback that validates its inputs and returns a valid access token.
- Perform a `find` operation that succeeds. Verify that the human callback was called with the appropriate inputs,
  including the timeout parameter if possible.
- Close the client.

**2.3 Human Callback Returns Missing Data**

- Create a `MongoClient` with a human callback that returns data not conforming to the `OIDCCredential` with missing
  fields.
- Perform a `find` operation that fails.
- Close the client.

### (3) Speculative Authentication

**3.1 Uses speculative authentication if there is a cached token**

- Create a `MongoClient` with a human callback that returns a valid token.
- Set a fail point for `find` commands of the form:

```javascript
{
  configureFailPoint: "failCommand",
  mode: {
    times: 1
  },
  data: {
    failCommands: [
      "find"
    ],
    closeConnection: true
  }
}
```

- Perform a `find` operation that fails.
- Set a fail point for `saslStart` commands of the form:

```javascript
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
```

- Perform a `find` operation that succeeds.
- Close the client.

**3.2 Does not use speculative authentication if there is no cached token**

- Create a `MongoClient` with a human callback that returns a valid token.
- Set a fail point for `saslStart` commands of the form:

```javascript
{
  configureFailPoint: "failCommand",
  mode: "alwaysOn",
  data: {
    failCommands: [
      "saslStart"
    ],
    errorCode: 20 // IllegalOperation
  }
}
```

- Perform a `find` operation that fails.
- Close the client.

### (4) Reauthentication

**4.1 Succeeds**

- Create a default OIDC client and add an event listener. The following assumes that the driver does not emit
  `saslStart` or `saslContinue` events. If the driver does emit those events, ignore/filter them for the purposes of
  this test.
- Perform a `find` operation that succeeds.
- Assert that the human callback has been called once.
- Clear the listener state if possible.
- Force a reauthenication using a fail point of the form:

```javascript
{
  configureFailPoint: "failCommand",
  mode: {
    times: 1
  },
  data: {
    failCommands: [
      "find"
    ],
    errorCode: 391 // ReauthenticationRequired
  }
}
```

- Perform another find operation that succeeds.
- Assert that the human callback has been called twice.
- Assert that the ordering of list started events is \[`find`\], , `find`. Note that if the listener stat could not be
  cleared then there will and be extra `find` command.
- Assert that the list of command succeeded events is \[`find`\].
- Assert that a `find` operation failed once during the command execution.
- Close the client.

**4.2 Succeeds no refresh**

- Create a default OIDC client with a human callback that does not return a refresh token.
- Perform a `find` operation that succeeds.
- Assert that the human callback has been called once.
- Force a reauthenication using a fail point of the form:

```javascript
{
  configureFailPoint: "failCommand",
  mode: {
    times: 1
  },
  data: {
    failCommands: [
      "find"
    ],
    errorCode: 391 // ReauthenticationRequired
  }
}
```

- Perform a `find` operation that succeeds.
- Assert that the human callback has been called twice.
- Close the client.

**4.3 Succeeds after refresh fails**

- Create a default OIDC client.
- Perform a `find` operation that succeeds.
- Assert that the human callback has been called once.
- Force a reauthenication using a fail point of the form:

```javascript
{
  configureFailPoint: "failCommand",
  mode: {
    times: 2
  },
  data: {
    failCommands: [
      "find", "saslStart"
    ],
    errorCode: 391 // ReauthenticationRequired
  }
}
```

- Perform a `find` operation that succeeds.
- Assert that the human callback has been called 3 times.
- Close the client.

**4.4 Fails**

- Create a default OIDC client.
- Perform a find operation that succeeds (to force a speculative auth).
- Assert that the human callback has been called once.
- Force a reauthenication using a failCommand of the form:

```javascript
{
  configureFailPoint: "failCommand",
  mode: {
    times: 3
  },
  data: {
    failCommands: [
      "find", "saslStart"
    ],
    errorCode: 391 // ReauthenticationRequired
  }
}
```

- Perform a find operation that fails.
- Assert that the human callback has been called twice.
- Close the client.
