# MongoDB OIDC

## Local Testing

See the detailed instructions in
[drivers-evergreen-tools](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/auth_oidc/README.md)
for how to set up your environment for OIDC testing.

______________________________________________________________________

## Unified Spec Tests

Drivers MUST run the unified spec tests in all supported OIDC environments.

______________________________________________________________________

## Prose Tests

Drivers MUST implement all prose tests in this section. Unless otherwise noted, all `MongoClient` instances MUST be
configured with `retryReads=false`.

Drivers MUST run the prose tests in all supported OIDC environments.

> [!NOTE]
> For test cases that create fail points, drivers MUST either use a unique `appName` or explicitly remove the fail point
> callback to prevent interaction between test cases.

After setting up your OIDC
[environment](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/auth_oidc/README.md),
source the `secrets-export.sh` file and use the associated env variables in your tests.

The default client should set the appropriate `ENVIRONMENT` auth mechanism property and include a callback that gets the
appropriate token for the given environment.

### Callback Authentication

**1.1 Callback is called during authentication**

- Create an OIDC configured client.
- Perform a `find` operation that succeeds.
- Assert that the callback was called 1 time.
- Close the client.

**1.2 Callback is called once for multiple connections**

- Create an OIDC configured client.
- Start 10 threads and run 100 `find` operations in each thread that all succeed.
- Assert that the callback was called 1 time.
- Close the client.

### (2) OIDC Callback Validation

**2.1 Valid Callback Inputs**

- Create an OIDC configured client with an OIDC callback that validates its inputs and returns a valid access token.
- Perform a `find` operation that succeeds.
- Assert that the OIDC callback was called with the appropriate inputs, including the timeout parameter if possible.
- Close the client.

**2.2 OIDC Callback Returns Null**

- Create an OIDC configured client with an OIDC callback that returns `null`.
- Perform a `find` operation that fails.
- Close the client.

**2.3 OIDC Callback Returns Missing Data**

- Create an OIDC configured client with an OIDC callback that returns data not conforming to the `OIDCCredential` with
  missing fields.
- Perform a `find` operation that fails.
- Close the client.

**2.4 Invalid Client Configuration with Callback**

- Create a `MongoClient` configured with an OIDC callback and auth mechanism property `ENVIRONMENT:test`.
- Assert it returns a client configuration error.

### (3) Authentication Failure

**3.1 Authentication failure with cached tokens fetch a new token and retry auth**

- Create an OIDC configured client.
- Poison the *Client Cache* with an invalid access token.
- Perform a `find` operation that succeeds.
- Assert that the callback was called 1 time.
- Close the client.

**3.2 Authentication failures without cached tokens return an error**

- Create an OIDC configured client with an OIDC callback that always returns invalid access tokens.
- Perform a `find` operation that fails.
- Assert that the callback was called 1 time.
- Close the client.

### (4) Reauthentication

- Create an OIDC configured client.
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

## (5) Azure Tests

Drivers MUST only run the Azure tests when testing on an Azure VM. See instructions in
[Drivers Evergreen Tools](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/auth_oidc/azure/README.md)
for test setup.

# 5.1 Azure With No Username

- Create a `MongoClient` configured with `ENVIRONMENT:azure` and a valid `TOKEN_RESOURCE` and no username.
- Perform a `find` operation that succeeds.
- Close the client.

# 5.2 Azure with Bad Usernam

- Create a `MongoClient` configured with `ENVIRONMENT:azure` and a valid `TOKEN_RESOURCE` and a username of `"bad"`.
- Perform a `find` operation that fails.
- Close the client.

______________________________________________________________________

## Human Authentication Flow Prose Tests

Drivers that support the [Human Authentication Flow](../auth.md#human-authentication-flow) MUST implement all prose
tests in this section. Unless otherwise noted, all `MongoClient` instances MUST be configured with `retryReads=false`.

The human workflow tests MUST only be run when in `ENVIRONMENT:test`.

> [!NOTE]
> For test cases that create fail points, drivers MUST either use a unique `appName` or explicitly remove the fail point
> after the test to prevent interaction between test cases.

Drivers MUST be able to authenticate against a server configured with either one or two configured identity providers.

Unless otherwise specified, use `MONGODB_URI_SINGLE` and the `test_user1` token in the `OIDC_TOKEN_DIR` as the
"access_token", and a dummy "refresh_token" for all tests.

When using an explicit username for the client, we use the token name and the domain name given by `OIDC_DOMAIN`, e.g.
`test_user1@${OIDC_DOMAIN}`.

### (1) OIDC Human Callback Authentication

Drivers MUST be able to authenticate using OIDC callback(s) when there is one principal configured.

**1.1 Single Principal Implicit Username**

- Create default client
- Perform a `find` operation that succeeds.
- Close the client.

**1.2 Single Principal Explicit Username**

- Create a client with `MONGODB_URI_SINGLE` and a username of `test_user1@${OIDC_DOMAIN}`.
- Perform a `find` operation that succeeds.
- Close the client.

**1.3 Multiple Principal User 1**

- Create a client with `MONGODB_URI_MULTI` and username of `test_user1@${OIDC_DOMAIN}`.
- Perform a `find` operation that succeeds.
- Close the client.

**1.4 Multiple Principal User 2**

- Create a client with `MONGODB_URI_MULTI` and username of `test_user2@${OIDC_DOMAIN}`. that reads the `test_user2`
  token file.
- Perform a `find` operation that succeeds.
- Close the client.

**1.5 Multiple Principal No User**

- Create a client with `MONGODB_URI_MULTI` and no username.
- Assert that a `find` operation fails.
- Close the client.

**1.6 Allowed Hosts Blocked**

- Create a client with an `ALLOWED_HOSTS` that is an empty list.
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
