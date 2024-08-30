# MongoDB AWS

Drivers MUST test the following scenarios:

1. `Regular Credentials`: Auth via an `ACCESS_KEY_ID` and `SECRET_ACCESS_KEY` pair
2. `EC2 Credentials`: Auth from an EC2 instance via temporary credentials assigned to the machine
3. `ECS Credentials`: Auth from an ECS instance via temporary credentials assigned to the task
4. `Assume Role`: Auth via temporary credentials obtained from an STS AssumeRole request
5. `Assume Role with Web Identity`: Auth via temporary credentials obtained from an STS AssumeRoleWithWebIdentity
   request
6. `AWS Lambda`: Auth via environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN`.
7. Caching of AWS credentials fetched by the driver.

For brevity, this section gives the values `<AccessKeyId>`, `<SecretAccessKey>` and `<Token>` in place of a valid access
key ID, secret access key and session token (also known as a security token). Note that if these values are passed into
the URI they MUST be URL encoded. Sample values are below.

```
AccessKeyId=AKIAI44QH8DHBEXAMPLE
SecretAccessKey=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Token=AQoDYXdzEJr...<remainder of security token>
```

## Regular credentials

Drivers MUST be able to authenticate by providing a valid access key id and secret access key pair as the username and
password, respectively, in the MongoDB URI. An example of a valid URI would be:

```
mongodb://<AccessKeyId>:<SecretAccessKey>@localhost/?authMechanism=MONGODB-AWS
```

## EC2 Credentials

Drivers MUST be able to authenticate from an EC2 instance via temporary credentials assigned to the machine. A sample
URI on an EC2 machine would be:

```
mongodb://localhost/?authMechanism=MONGODB-AWS
```

> [!NOTE]
> No username, password or session token is passed into the URI. Drivers MUST query the EC2 instance endpoint to obtain
> these credentials.

## ECS instance

Drivers MUST be able to authenticate from an ECS container via temporary credentials. A sample URI in an ECS container
would be:

```
mongodb://localhost/?authMechanism=MONGODB-AWS
```

> [!NOTE]
> No username, password or session token is passed into the URI. Drivers MUST query the ECS container endpoint to obtain
> these credentials.

## AssumeRole

Drivers MUST be able to authenticate using temporary credentials returned from an assume role request. These temporary
credentials consist of an access key ID, a secret access key, and a security token passed into the URI. A sample URI
would be:

```
mongodb://<AccessKeyId>:<SecretAccessKey>@localhost/?authMechanism=MONGODB-AWS&authMechanismProperties=AWS_SESSION_TOKEN:<Token>
```

## Assume Role with Web Identity

Drivers MUST be able to authentiate using a valid OIDC token and associated role ARN taken from environment variables,
respectively:

```
AWS_WEB_IDENTITY_TOKEN_FILE
AWS_ROLE_ARN
AWS_ROLE_SESSION_NAME (optional)
```

A sample URI in for a web identity test would be:

```
mongodb://localhost/?authMechanism=MONGODB-AWS
```

Drivers MUST test with and without AWS_ROLE_SESSION_NAME set.

> [!NOTE]
> No username, password or session token is passed into the URI.

Drivers MUST check the environment variables listed above and make an
[AssumeRoleWithWebIdentity request](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html)
to obtain credentials.

## AWS Lambda

Drivers MUST be able to authenticate via an access key ID, secret access key and optional session token taken from the
environment variables, respectively:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY 
AWS_SESSION_TOKEN
```

Sample URIs both with and without optional session tokens set are shown below. Drivers MUST test both cases.

```bash
# without a session token
export AWS_ACCESS_KEY_ID="<AccessKeyId>"
export AWS_SECRET_ACCESS_KEY="<SecretAccessKey>"

URI="mongodb://localhost/?authMechanism=MONGODB-AWS"
```

```bash
# with a session token
export AWS_ACCESS_KEY_ID="<AccessKeyId>"
export AWS_SECRET_ACCESS_KEY="<SecretAccessKey>"
export AWS_SESSION_TOKEN="<Token>"

URI="mongodb://localhost/?authMechanism=MONGODB-AWS"
```

> [!NOTE]
> No username, password or session token is passed into the URI. Drivers MUST check the environment variables listed
> above for these values. If the session token is set Drivers MUST use it.

## Cached Credentials

Drivers MUST ensure that they are testing the ability to cache credentials. Drivers will need to be able to query and
override the cached credentials to verify usage. To determine whether to run the cache tests, the driver can check for
the absence of the AWS_ACCESS_KEY_ID environment variable and of credentials in the URI.

01. Clear the cache.
02. Create a new client.
03. Ensure that a `find` operation adds credentials to the cache.
04. Override the cached credentials with an "Expiration" that is within one minute of the current UTC time.
05. Create a new client.
06. Ensure that a `find` operation updates the credentials in the cache.
07. Poison the cache with an invalid access key id.
08. Create a new client.
09. Ensure that a `find` operation results in an error.
10. Ensure that the cache has been cleared.
11. Ensure that a subsequent `find` operation succeeds.
12. Ensure that the cache has been set.

If the drivers's language supports dynamically setting environment variables, add the following tests. Note that if
integration tests are run in parallel for the driver, then these tests must be run as unit tests interacting with the
auth provider directly instead of using a client.

01. Clear the cache.
02. Create a new client.
03. Ensure that a `find` operation adds credentials to the cache.
04. Set the AWS environment variables based on the cached credentials.
05. Clear the cache.
06. Create a new client.
07. Ensure that a `find` operation succeeds and does not add credentials to the cache.
08. Set the AWS environment variables to invalid values.
09. Create a new client.
10. Ensure that a `find` operation results in an error.
11. Clear the AWS environment variables.
12. Clear the cache.
13. Create a new client.
14. Ensure that a `find` operation adds credentials to the cache.
15. Set the AWS environment variables to invalid values.
16. Create a new client.
17. Ensure that a `find` operation succeeds.
18. Clear the AWS environment variables.
