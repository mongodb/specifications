# Authentication

- Status: Accepted
- Minimum Server Version: 2.6

______________________________________________________________________

## Abstract

MongoDB supports various authentication strategies across various versions. When authentication is turned on in the
database, a driver must authenticate before it is allowed to communicate with the server. This spec defines when and how
a driver performs authentication with a MongoDB server.

### META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

### References

[Server Discovery and Monitoring](../server-discovery-and-monitoring/server-discovery-and-monitoring.md)

## Specification

### Definitions

- Credential

  The pieces of information used to establish the authenticity of a user. This is composed of an identity and some form
  of evidence such as a password or a certificate.

- FQDN

  Fully Qualified Domain Name

- Mechanism

  A SASL implementation of a particular type of credential negotiation.

- Source

  The authority used to establish credentials and/or privileges in reference to a mongodb server. In practice, it is the
  database to which sasl authentication commands are sent.

- Realm

  The authority used to establish credentials and/or privileges in reference to GSSAPI.

- SASL

  Simple Authentication and Security Layer - [RFC 4422](http://www.ietf.org/rfc/rfc4422.txt)

### Client Implementation

#### MongoCredential

Drivers SHOULD contain a type called `MongoCredential`. It SHOULD contain some or all of the following information.

- username (string)

  - Applies to all mechanisms.
  - Optional for MONGODB-X509, MONGODB-AWS, and MONGODB-OIDC.

- source (string)

  - Applies to all mechanisms.
  - Always '$external' for GSSAPI and MONGODB-X509.
  - This is the database to which the authenticate command will be sent.
  - This is the database to which sasl authentication commands will be sent.

- password (string)

  - Does not apply to all mechanisms.

- mechanism (string)

  - Indicates which mechanism to use with the credential.

- mechanism_properties

  - Includes additional properties for the given mechanism.

Each mechanism requires certain properties to be present in a MongoCredential for authentication to occur. See the
individual mechanism definitions in the "MongoCredential Properties" section. All requirements listed for a mechanism
must be met for authentication to occur.

#### Credential delimiter in URI implies authentication

The presence of a credential delimiter (i.e. @) in the URI connection string is evidence that the user has unambiguously
specified user information and MUST be interpreted as a user configuring authentication credentials (even if the
username and/or password are empty strings).

##### Authentication source and URI database do not imply authentication

The presence of a database name in the URI connection string MUST NOT be interpreted as a user configuring
authentication credentials. The URI database name is only used as a default source for some mechanisms when
authentication has been configured and a source is required but has not been specified. See individual mechanism
definitions for details.

Similarly, the presence of the `authSource` option in the URI connection string without other credential data such as
Userinfo or authentication parameters in connection options MUST NOT be interpreted as a request for authentication.

#### Errors

Drivers SHOULD raise an error as early as possible when detecting invalid values in a credential. For instance, if a
`mechanism_property` is specified for [MONGODB-CR](#mongodb-cr), the driver should raise an error indicating that the
property does not apply.

Drivers MUST raise an error if any required information for a mechanism is missing. For instance, if a `username` is not
specified for SCRAM-SHA-256, the driver must raise an error indicating the the property is missing.

#### Naming

Naming of this information MUST be idiomatic to the driver's language/framework but still remain consistent. For
instance, python would use "mechanism_properties" and .NET would use "MechanismProperties".

Naming of mechanism properties MUST be case-insensitive. For instance, SERVICE_NAME and service_name refer to the same
property.

### Authentication

A MongoClient instance MUST be considered a single logical connection to the server/deployment.

Socket connections from a MongoClient to deployment members can be one of two types:

- Monitoring-only socket: multi-threaded drivers maintain monitoring sockets separate from sockets in connection pools.
- General-use socket: for multi-threaded drivers, these are sockets in connection pools used for (non-monitoring) user
  operations; in single-threaded drivers, these are used for both monitoring and user operations.

Authentication (including mechanism negotiation) MUST NOT happen on monitoring-only sockets.

If one or more credentials are provided to a MongoClient, then whenever a general-use socket is opened, drivers MUST
immediately conduct an authentication handshake over that socket.

Drivers SHOULD require all credentials to be specified upon construction of the MongoClient. This is defined as eager
authentication and drivers MUST support this mode.

#### Authentication Handshake

An authentication handshake consists of an initial `hello` or legacy hello command possibly followed by one or more
authentication conversations.

Drivers MUST follow the following steps for an authentication handshake:

1. Upon opening a general-use socket to a server for a given MongoClient, drivers MUST issue a
   [MongoDB Handshake](../mongodb-handshake/handshake.md) immediately. This allows a driver to determine the server
   type. If the `hello` or legacy hello of the MongoDB Handshake fails with an error, drivers MUST treat this as an
   authentication error.
2. If the server is of type RSArbiter, no authentication is possible and the handshake is complete.
3. Inspect the value of `maxWireVersion`. If the value is greater than or equal to `6`, then the driver MUST use
   `OP_MSG` for authentication. Otherwise, it MUST use `OP_QUERY`.
4. If credentials exist: 3.1. A driver MUST authenticate with all credentials provided to the MongoClient. 3.2. A single
   invalid credential is the same as all credentials being invalid.

If the authentication handshake fails for a socket, drivers MUST mark the server Unknown and clear the server's
connection pool. (See [Q & A](#q-and-a) below and SDAM's
[Why mark a server Unknown after an auth error](../server-discovery-and-monitoring/server-discovery-and-monitoring.md#why-mark-a-server-unknown-after-an-auth-error)
for rationale.)

All blocking operations executed as part of the authentication handshake MUST apply timeouts per the
[Client Side Operations Timeout](../client-side-operations-timeout/client-side-operations-timeout.md) specification.

#### Mechanism Negotiation via Handshake

- Since: 4.0

If an application provides a username but does not provide an authentication mechanism, drivers MUST negotiate a
mechanism via a `hello` or legacy hello command requesting a user's supported SASL mechanisms:

```javascript
{hello: 1, saslSupportedMechs: "<dbname>.<username>"}
```

In this example `<dbname>` is the authentication database name that either SCRAM-SHA-1 or SCRAM-SHA-256 would use (they
are the same; either from the connection string or else defaulting to 'admin') and `<username>` is the username provided
in the auth credential. The username MUST NOT be modified from the form provided by the user (i.e. do not normalize with
SASLprep), as the server uses the raw form to look for conflicts with legacy credentials.

If the handshake response includes a `saslSupportedMechs` field, then drivers MUST use the contents of that field to
select a default mechanism as described later. If the command succeeds and the response does not include a
`saslSupportedMechs` field, then drivers MUST use the legacy default mechanism rules for servers older than 4.0.

Drivers MUST NOT validate the contents of the `saslSupportedMechs` attribute of the initial handshake reply. Drivers
MUST NOT raise an error if the `saslSupportedMechs` attribute of the reply includes an unknown mechanism.

### Single-credential drivers

When the authentication mechanism is not specified, drivers that allow only a single credential per client MUST perform
mechanism negotiation as part of the MongoDB Handshake portion of the authentication handshake. This lets authentication
proceed without a separate negotiation round-trip exchange with the server.

### Multi-credential drivers

The use of multiple credentials within a driver is discouraged, but some legacy drivers still allow this. Such drivers
may not have user credentials when connections are opened and thus will not be able to do negotiation.

Drivers with a list of credentials at the time a connection is opened MAY do mechanism negotiation on the initial
handshake, but only for the first credential in the list of credentials.

When authenticating each credential, if the authentication mechanism is not specified and has not been negotiated for
that credential:

- If the connection handshake results indicate the server version is 4.0 or later, drivers MUST send a new `hello` or
  legacy hello negotiation command for the credential to determine the default authentication mechanism.
- Otherwise, when the server version is earlier than 4.0, the driver MUST select a default authentication mechanism for
  the credential following the instructions for when the `saslSupportedMechs` field is not present in a legacy hello
  response.

### Caching credentials in SCRAM

In the implementation of SCRAM authentication mechanisms (e.g. SCRAM-SHA-1 and SCRAM-SHA-256), drivers MUST maintain a
cache of computed SCRAM credentials. The cache entries SHOULD be identified by the password, salt, iteration count, and
a value that uniquely identifies the authentication mechanism (e.g. "SHA1" or "SCRAM-SHA-256").

The cache entry value MUST be either the `saltedPassword` parameter or the combination of the `clientKey` and
`serverKey` parameters.

### Reauthentication

On any operation that requires authentication, the server may raise the error `ReauthenticationRequired` (391),
typically if the user's credential has expired. Drivers MUST immediately attempt a reauthentication on the connection
using suitable credentials, as specified by the particular authentication mechanism when this error is raised, and then
re-attempt the operation. This attempt MUST be irrespective of whether the operation is considered retryable. Drivers
MUST NOT resend a `hello` message during reauthentication, instead using SASL messages directly. Any errors that could
not be recovered from during reauthentication, or that were encountered during the subsequent re-attempt of the
operation MUST be raised to the user.

Currently the only authentication mechanism on the server that supports reauthentication is MONGODB-OIDC. See the
[MONGODB-OIDC](#mongodb-oidc) section on reauthentication for more details. Note that in order to implement the unified
spec tests for reauthentication, it may be necessary to add reauthentication support for whichever auth mechanism is
used when running the authentication spec tests.

### Default Authentication Methods

- Since: 3.0
- Revised: 4.0

If the user did not provide a mechanism via the connection string or via code, the following logic describes how to
select a default.

If a `saslSupportedMechs` field was present in the handshake response for mechanism negotiation, then it MUST be
inspected to select a default mechanism:

```javascript
{
    "hello" : true,
    "saslSupportedMechs": ["SCRAM-SHA-1", "SCRAM-SHA-256"],
    ...
    "ok" : 1
}
```

If SCRAM-SHA-256 is present in the list of mechanism, then it MUST be used as the default; otherwise, SCRAM-SHA-1 MUST
be used as the default, regardless of whether SCRAM-SHA-1 is in the list. Drivers MUST NOT attempt to use any other
mechanism (e.g. PLAIN) as the default.

If `saslSupportedMechs` is not present in the handshake response for mechanism negotiation, then SCRAM-SHA-1 MUST be
used when talking to servers >= 3.0. Prior to server 3.0, MONGODB-CR MUST be used.

When a user has specified a mechanism, regardless of the server version, the driver MUST honor this.

#### Determining Server Version

Drivers SHOULD use the server's wire version ranges to determine the server's version.

### MONGODB-CR

- Since: 1.4
- Deprecated: 3.0
- Removed: 4.0

MongoDB Challenge Response is a nonce and MD5 based system. The driver sends a `getnonce` command, encodes and hashes
the password using the returned nonce, and then sends an `authenticate` command.

#### Conversation

1. Send `getnonce` command

```javascript
CMD = { getnonce: 1 }
RESP = { nonce: <nonce> }
```

2. Compute key

```javascript
passwordDigest = HEX( MD5( UTF8( username + ':mongo:' + password )))
key = HEX( MD5( UTF8( nonce + username + passwordDigest )))
```

3. Send `authenticate` command

```javascript
CMD = { authenticate: 1, nonce: nonce, user: username, key: key }
```

As an example, given a username of "user" and a password of "pencil", the conversation would appear as follows:

```javascript
CMD = {getnonce : 1}
RESP = {nonce: "2375531c32080ae8", ok: 1}
CMD = {authenticate: 1, user: "user", nonce: "2375531c32080ae8", key: "21742f26431831d5cfca035a08c5bdf6"}
RESP = {ok: 1}
```

#### [MongoCredential](#mongocredential) Properties

- username

  MUST be specified and non-zero length.

- source

  MUST be specified. Defaults to the database name if supplied on the connection string or `admin`.

- password

  MUST be specified.

- mechanism

  MUST be "MONGODB-CR"

- mechanism_properties

  MUST NOT be specified.

### MONGODB-X509

- Since: 2.6
- Changed: 3.4

MONGODB-X509 is the usage of X.509 certificates to validate a client where the distinguished subject name of the client
certificate acts as the username.

When connected to MongoDB 3.4:

- You MUST NOT raise an error when the application only provides an X.509 certificate and no username.
- If the application does not provide a username you MUST NOT send a username to the server.
- If the application provides a username you MUST send that username to the server.

When connected to MongoDB 3.2 or earlier:

- You MUST send a username to the server.
- If no username is provided by the application, you MAY extract the username from the X.509 certificate instead of
  requiring the application to provide it.
- If you choose not to automatically extract the username from the certificate you MUST error when no username is
  provided by the application.

#### Conversation

1. Send `authenticate` command (MongoDB 3.4+)

```javascript
CMD = {"authenticate": 1, "mechanism": "MONGODB-X509"}
RESP = {"dbname" : "$external", "user" : "C=IS,ST=Reykjavik,L=Reykjavik,O=MongoDB,OU=Drivers,CN=client", "ok" : 1}
```

2. Send `authenticate` command with username:

```bash
username = $(openssl x509 -subject -nameopt RFC2253 -noout -inform PEM -in my-cert.pem)
```

```javascript
CMD = {authenticate: 1, mechanism: "MONGODB-X509", user: "C=IS,ST=Reykjavik,L=Reykjavik,O=MongoDB,OU=Drivers,CN=client"}
RESP = {"dbname" : "$external", "user" : "C=IS,ST=Reykjavik,L=Reykjavik,O=MongoDB,OU=Drivers,CN=client", "ok" : 1}
```

#### [MongoCredential](#mongocredential) Properties

- username

  SHOULD NOT be provided for MongoDB 3.4+ MUST be specified and non-zero length for MongoDB prior to 3.4

- source

  MUST be "$external". Defaults to `$external`.

- password

  MUST NOT be specified.

- mechanism

  MUST be "MONGODB-X509"

- mechanism_properties

  MUST NOT be specified.

TODO: Errors

### SASL Mechanisms

- Since: 2.4 Enterprise

SASL mechanisms are all implemented using the same sasl commands and interpreted as defined by the
[SASL specification RFC 4422](http://tools.ietf.org/html/rfc4422).

1. Send the `saslStart` command.

```javascript
CMD = { saslStart: 1, mechanism: <mechanism_name>, payload: BinData(...), autoAuthorize: 1 }
RESP = { conversationId: <number>, code: <code>, done: <boolean>, payload: <payload> }
```

- conversationId: the conversation identifier. This will need to be remembered and used for the duration of the
  conversation.
- code: A response code that will indicate failure. This field is not included when the command was successful.
- done: a boolean value indicating whether or not the conversation has completed.
- payload: a sequence of bytes or a base64 encoded string (depending on input) to pass into the SASL library to
  transition the state machine.

2. Continue with the `saslContinue` command while `done` is `false`.

```javascript
CMD = { saslContinue: 1, conversationId: conversationId, payload: BinData(...) }
RESP = { conversationId: <number>, code: <code>, done: <boolean>, payload: <payload> }
```

Many languages will have the ability to utilize 3rd party libraries. The server uses
[cyrus-sasl](https://www.cyrusimap.org/sasl/) and it would make sense for drivers with a choice to also choose cyrus.
However, it is important to ensure that when utilizing a 3rd party library it does implement the mechanism on all
supported OS versions and that it interoperates with the server. For instance, the cyrus sasl library offered on RHEL 6
does not implement SCRAM-SHA-1. As such, if your driver supports RHEL 6, you'll need to implement SCRAM-SHA-1 from
scratch.

### GSSAPI

- Since:

  2.4 Enterprise

  2.6 Enterprise on Windows

GSSAPI is kerberos authentication as defined in [RFC 4752](http://tools.ietf.org/html/rfc4752). Microsoft has a
proprietary implementation called SSPI which is compatible with both Windows and Linux clients.

[MongoCredential](#mongocredential) properties:

- username

  MUST be specified and non-zero length.

- source

  MUST be "$external". Defaults to `$external`.

- password

  MAY be specified. If omitted, drivers MUST NOT pass the username without password to SSPI on Windows and instead use
  the default credentials.

- mechanism

  MUST be "GSSAPI"

- mechanism_properties

  - SERVICE_NAME

    Drivers MUST allow the user to specify a different service name. The default is "mongodb".

  - CANONICALIZE_HOST_NAME

    Drivers MAY allow the user to request canonicalization of the hostname. This might be required when the hosts report
    different hostnames than what is used in the kerberos database. The value is a string of either "none", "forward",
    or "forwardAndReverse". "none" is the default and performs no canonicalization. "forward" performs a forward DNS
    lookup to canonicalize the hostname. "forwardAndReverse" performs a forward DNS lookup and then a reverse lookup on
    that value to canonicalize the hostname. The driver MUST fallback to the provided host if any lookup errors or
    returns no results. Drivers MAY decide to also keep the legacy boolean values where `true` equals the
    "forwardAndReverse" behaviour and `false` equals "none".

  - SERVICE_REALM

    Drivers MAY allow the user to specify a different realm for the service. This might be necessary to support
    cross-realm authentication where the user exists in one realm and the service in another.

  - SERVICE_HOST

    Drivers MAY allow the user to specify a different host for the service. This is stored in the service principal name
    instead of the standard host name. This is generally used for cases where the initial role is being created from
    localhost but the actual service host would differ.

#### Hostname Canonicalization

Valid values for CANONICALIZE_HOST_NAME are `true`, `false`, "none", "forward", "forwardAndReverse". If a value is
provided that does not match one of these the driver MUST raise an error.

If CANONICALIZE_HOST_NAME is `false`, "none", or not provided, the driver MUST NOT canonicalize the host name.

If CANONICALIZE_HOST_NAME is `true`, "forward", or "forwardAndReverse", the client MUST canonicalize the name of each
host it uses for authentication. There are two options. First, if the client's underlying GSSAPI library provides
hostname canonicalization, the client MAY rely on it. For example, MIT Kerberos has
[a configuration option for canonicalization](https://web.mit.edu/kerberos/krb5-1.13/doc/admin/princ_dns.html#service-principal-canonicalization).

Second, the client MAY implement its own canonicalization. If so, the canonicalization algorithm MUST be:

```python
addresses = fetch addresses for host
if no addresses:
  throw error

address = first result in addresses

while true:
  cnames = fetch CNAME records for host
  if no cnames:
    break

  # Unspecified which CNAME is used if > 1.
  host = one of the records in cnames

if forwardAndReverse or true:
  reversed = do a reverse DNS lookup for address
  canonicalized = lowercase(reversed)
else:
  canonicalized = lowercase(host)
```

For example, here is a Python implementation of this algorithm using `getaddrinfo` (for address and CNAME resolution)
and `getnameinfo` (for reverse DNS).

```python
from socket import *
import sys


def canonicalize(host, mode):
    # Get a CNAME for host, if any.
    af, socktype, proto, canonname, sockaddr = getaddrinfo(
        host, None, 0, 0, IPPROTO_TCP, AI_CANONNAME)[0]

    print('address from getaddrinfo: [%s]' % (sockaddr[0],))
    print('canonical name from getaddrinfo: [%s]' % (canonname,))

    if (mode == true or mode == 'forwardAndReverse'):
        try:
            # NI_NAMEREQD requests an error if getnameinfo fails.
            name = getnameinfo(sockaddr, NI_NAMEREQD)
        except gaierror as exc:
            print('getname info failed: "%s"' % (exc,))
            return canonname.lower()
        return name[0].lower()
    else:
        return canonname.lower()


canonicalized = canonicalize(sys.argv[1])
print('canonicalized: [%s]' % (canonicalized,))
```

Beware of a bug in older glibc where `getaddrinfo` uses PTR records instead of CNAMEs if the address family hint is
AF_INET6, and beware of a bug in older MIT Kerberos that causes it to always do reverse DNS lookup even if the `rdns`
configuration option is set to `false`.

### PLAIN

- Since: 2.6 Enterprise

The PLAIN mechanism, as defined in [RFC 4616](http://tools.ietf.org/html/rfc4616), is used in MongoDB to perform LDAP
authentication. It cannot be used to perform any other type of authentication. Since the credentials are stored outside
of MongoDB, the `$external` database must be used for authentication.

#### Conversation

As an example, given a username of "user" and a password of "pencil", the conversation would appear as follows:

```javascript
CMD = {saslStart: 1, mechanism: "PLAIN", payload: BinData(0, "AHVzZXIAcGVuY2ls")}
RESP = {conversationId: 1, payload: BinData(0,""), done: true, ok: 1}
```

If your sasl client is also sending the authzid, it would be "user" and the conversation would appear as follows:

```javascript
CMD = {saslStart: 1, mechanism: "PLAIN", payload: BinData(0, "dXNlcgB1c2VyAHBlbmNpbA==")}
RESP = {conversationId: 1, payload: BinData(0,""), done: true, ok: 1}
```

MongoDB supports either of these forms.

#### [MongoCredential](#mongocredential) Properties

- username

  MUST be specified and non-zero length.

- source

  MUST be specified. Defaults to the database name if supplied on the connection string or `$external`.

- password

  MUST be specified.

- mechanism

  MUST be "PLAIN"

- mechanism_properties

  MUST NOT be specified.

### SCRAM-SHA-1

- Since: 3.0

SCRAM-SHA-1 is defined in [RFC 5802](http://tools.ietf.org/html/rfc5802).

[Page 11 of the RFC](http://tools.ietf.org/html/rfc5802#page-11) specifies that user names be prepared with SASLprep,
but drivers MUST NOT do so.

[Page 8 of the RFC](http://tools.ietf.org/html/rfc5802#page-8) identifies the "SaltedPassword" as
`:= Hi(Normalize(password), salt, i)`. The `password` variable MUST be the mongodb hashed variant. The mongo hashed
variant is computed as `hash = HEX( MD5( UTF8( username + ':mongo:' + plain_text_password )))`, where
`plain_text_password` is actually plain text. The `username` and `password` MUST NOT be prepared with SASLprep before
hashing.

For example, to compute the ClientKey according to the RFC:

```javascript
// note that "salt" and "i" have been provided by the server
function computeClientKey(username, plain_text_password) {
    mongo_hashed_password = HEX( MD5( UTF8( username + ':mongo:' + plain_text_password )));
    saltedPassword  = Hi(Normalize(mongo_hashed_password), salt, i);
    clientKey = HMAC(saltedPassword, "Client Key");
}
```

In addition, SCRAM-SHA-1 requires that a client create a randomly generated nonce. It is imperative, for security sake,
that this be as secure and truly random as possible. For instance, Java provides both a Random class as well as a
SecureRandom class. SecureRandom is cryptographically generated while Random is just a pseudo-random generator with
predictable outcomes.

Additionally, drivers MUST enforce a minimum iteration count of 4096 and MUST error if the authentication conversation
specifies a lower count. This mitigates downgrade attacks by a man-in-the-middle attacker.

Drivers MUST NOT advertise support for channel binding, as the server does not support it and legacy servers may fail
authentication if drivers advertise support. I.e. the client-first-message MUST start with `n,`.

Drivers MUST add a top-level `options` field to the saslStart command, whose value is a document containing a field
named `skipEmptyExchange` whose value is true. Older servers will ignore the `options` field and continue with the
longer conversation as shown in the "Backwards Compatibility" section. Newer servers will set the `done` field to `true`
when it responds to the client at the end of the second round trip, showing proof that it knows the password. This will
shorten the conversation by one round trip.

#### Conversation

As an example, given a username of "user" and a password of "pencil" and an r value of "fyko+d2lbbFgONRv9qkxdawL", a
SCRAM-SHA-1 conversation would appear as follows:

```javascript
CMD = "n,,n=user,r=fyko+d2lbbFgONRv9qkxdawL"
RESP = "r=fyko+d2lbbFgONRv9qkxdawLHo+Vgk7qvUOKUwuWLIWg4l/9SraGMHEE,s=rQ9ZY3MntBeuP3E1TDVC4w==,i=10000"
CMD = "c=biws,r=fyko+d2lbbFgONRv9qkxdawLHo+Vgk7qvUOKUwuWLIWg4l/9SraGMHEE,p=MC2T8BvbmWRckDw8oWl5IVghwCY="
RESP = "v=UMWeI25JD1yNYZRMpZ4VHvhZ9e0="
```

This same conversation over MongoDB's SASL implementation would appear as follows:

```javascript
CMD = {saslStart: 1, mechanism: "SCRAM-SHA-1", payload: BinData(0, "biwsbj11c2VyLHI9ZnlrbytkMmxiYkZnT05Sdjlxa3hkYXdM"), options: { skipEmptyExchange: true }}
RESP = {conversationId : 1, payload: BinData(0,"cj1meWtvK2QybGJiRmdPTlJ2OXFreGRhd0xIbytWZ2s3cXZVT0tVd3VXTElXZzRsLzlTcmFHTUhFRSxzPXJROVpZM01udEJldVAzRTFURFZDNHc9PSxpPTEwMDAw"), done: false, ok: 1}
CMD = {saslContinue: 1, conversationId: 1, payload: BinData(0, "Yz1iaXdzLHI9ZnlrbytkMmxiYkZnT05Sdjlxa3hkYXdMSG8rVmdrN3F2VU9LVXd1V0xJV2c0bC85U3JhR01IRUUscD1NQzJUOEJ2Ym1XUmNrRHc4b1dsNUlWZ2h3Q1k9")}
RESP = {conversationId: 1, payload: BinData(0,"dj1VTVdlSTI1SkQxeU5ZWlJNcFo0Vkh2aFo5ZTA9"), done: true, ok: 1}
```

#### [MongoCredential](#mongocredential) Properties

- username

  MUST be specified and non-zero length.

- source

  MUST be specified. Defaults to the database name if supplied on the connection string or `admin`.

- password

  MUST be specified.

- mechanism

  MUST be "SCRAM-SHA-1"

- mechanism_properties

  MUST NOT be specified.

### SCRAM-SHA-256

- Since: 4.0

SCRAM-SHA-256 extends [RFC 5802](http://tools.ietf.org/html/rfc5802) and is formally defined in
[RFC 7677](https://tools.ietf.org/html/rfc7677).

The MongoDB SCRAM-SHA-256 mechanism works similarly to the SCRAM-SHA-1 mechanism, with the following changes:

- The SCRAM algorithm MUST use SHA-256 as the hash function instead of SHA-1.
- User names MUST NOT be prepared with SASLprep. This intentionally contravenes the "SHOULD" provision of RFC 5802.
- Passwords MUST be prepared with SASLprep, per RFC 5802. Passwords are used directly for key derivation ; they MUST NOT
  be digested as they are in SCRAM-SHA-1.

Additionally, drivers MUST enforce a minimum iteration count of 4096 and MUST error if the authentication conversation
specifies a lower count. This mitigates downgrade attacks by a man-in-the-middle attacker.

Drivers MUST add a top-level `options` field to the saslStart command, whose value is a document containing a field
named `skipEmptyExchange` whose value is true. Older servers will ignore the `options` field and continue with the
longer conversation as shown in the "Backwards Compatibility" section. Newer servers will set the `done` field to `true`
when it responds to the client at the end of the second round trip, showing proof that it knows the password. This will
shorten the conversation by one round trip.

#### Conversation

As an example, given a username of "user" and a password of "pencil" and an r value of "rOprNGfwEbeRWgbNEkqO", a
SCRAM-SHA-256 conversation would appear as follows:

```javascript
CMD = "n,,n=user,r=rOprNGfwEbeRWgbNEkqO"
RESP = "r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,s=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096"
CMD = "c=biws,r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,p=dHzbZapWIk4jUhN+Ute9ytag9zjfMHgsqmmiz7AndVQ="
RESP = "v=6rriTRBi23WpRR/wtup+mMhUZUn/dB5nLTJRsjl95G4="
```

This same conversation over MongoDB's SASL implementation would appear as follows:

```javascript
CMD = {saslStart: 1, mechanism:"SCRAM-SHA-256", options: {skipEmptyExchange: true}, payload: BinData(0, "biwsbj11c2VyLHI9ck9wck5HZndFYmVSV2diTkVrcU8=")}
RESP = {conversationId: 1, payload: BinData(0, "cj1yT3ByTkdmd0ViZVJXZ2JORWtxTyVodllEcFdVYTJSYVRDQWZ1eEZJbGopaE5sRiRrMCxzPVcyMlphSjBTTlk3c29Fc1VFamI2Z1E9PSxpPTQwOTY="), done: false, ok: 1}
CMD = {saslContinue: 1, conversationId: 1, payload: BinData(0, "Yz1iaXdzLHI9ck9wck5HZndFYmVSV2diTkVrcU8laHZZRHBXVWEyUmFUQ0FmdXhGSWxqKWhObEYkazAscD1kSHpiWmFwV0lrNGpVaE4rVXRlOXl0YWc5empmTUhnc3FtbWl6N0FuZFZRPQ==")}
RESP = {conversationId: 1, payload: BinData(0, "dj02cnJpVFJCaTIzV3BSUi93dHVwK21NaFVaVW4vZEI1bkxUSlJzamw5NUc0PQ=="), done: true, ok: 1}
```

#### [MongoCredential](#mongocredential) Properties

- username

  MUST be specified and non-zero length.

- source

  MUST be specified. Defaults to the database name if supplied on the connection string or `admin`.

- password

  MUST be specified.

- mechanism

  MUST be "SCRAM-SHA-256"

- mechanism_properties

  MUST NOT be specified.

### MONGODB-AWS

- Since: 4.4

MONGODB-AWS authenticates using AWS IAM credentials (an access key ID and a secret access key),
[temporary AWS IAM credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html) obtained from
an [AWS Security Token Service (STS)](https://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html)
[Assume Role](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html) request, an OpenID Connect ID
token that supports
[AssumeRoleWithWebIdentity](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html), or
temporary AWS IAM credentials assigned to an
[EC2 instance](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2.html) or ECS task.
Temporary credentials, in addition to an access key ID and a secret access key, includes a security (or session) token.

MONGODB-AWS requires that a client create a randomly generated nonce. It is imperative, for security sake, that this be
as secure and truly random as possible. Additionally, the secret access key and only the secret access key is sensitive.
Drivers MUST take proper precautions to ensure we do not leak this info.

All messages between MongoDB clients and servers are sent as BSON V1.1 Objects in the payload field of saslStart and
saslContinue. All fields in these messages have a "short name" which is used in the serialized BSON representation and a
human-readable "friendly name" which is used in this specification. They are as follows:

| Name | Friendly Name        | Type              | Description                                                                                                                                 |
| ---- | -------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| r    | client nonce         | BinData Subtype 0 | 32 byte cryptographically secure random number                                                                                              |
| p    | gs2-cb-flag          | int32             | The integer representation of the ASCII character 'n' or 'y', i.e., `110` or `121`                                                          |
| s    | server nonce         | BinData Subtype 0 | 64 bytes total, 32 bytes from the client first message and a 32 byte cryptographically secure random number generated by the server         |
| h    | sts host             | string            | FQDN of the STS service                                                                                                                     |
| a    | authorization header | string            | Authorization header for [AWS Signature Version 4](https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html?shortFooter=true) |
| d    | X-AMZ-Date           | string            | Current date in UTC. See [AWS Signature Version 4](https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html?shortFooter=true) |
| t    | X-AMZ-Security-Token | string            | Optional AWS security token                                                                                                                 |

Drivers MUST NOT advertise support for channel binding, as the server does not support it and legacy servers may fail
authentication if drivers advertise support. The client-first-message MUST set the gs2-cb-flag to the integer
representation of the ASCII character `n`, i.e., `110`.

#### Conversation

The first message sent by drivers MUST contain a `client nonce` and `gs2-cb-flag`. In response, the server will send a
`server nonce` and `sts host`. Drivers MUST validate that the server nonce is exactly 64 bytes and the first 32 bytes
are the same as the client nonce. Drivers MUST also validate that the length of the host is greater than 0 and less than
or equal to 255 bytes per [RFC 1035](https://tools.ietf.org/html/rfc1035). Drivers MUST reject FQDN names with empty
labels (e.g., "abc..def"), names that start with a period (e.g., ".abc.def") and names that end with a period (e.g.,
"abc.def."). Drivers MUST respond to the server's message with an `authorization header` and a `date`.

As an example, given a client nonce value of "dzw1U2IwSEtgaWI0IUxZMVJqc2xuQzNCcUxBc05wZjI=", a MONGODB-AWS conversation
decoded from BSON to JSON would appear as follows:

Client First

```javascript
{
     "r" : new BinData(0, "dzw1U2IwSEtgaWI0IUxZMVJqc2xuQzNCcUxBc05wZjI="),
     "p" : 110
}
```

Server First

```javascript
{
    "s" : new BinData(0, "dzw1U2IwSEtgaWI0IUxZMVJqc2xuQzNCcUxBc05wZjIGS0J9EgLwzEZ9dIzr/hnnK2mgd4D7F52t8g9yTC5cIA=="),
    "h" : "sts.amazonaws.com"
}
```

Client Second

```javascript
{
    "a" : "AWS4-HMAC-SHA256 Credential=AKIAICGVLKOKZVY3X3DA/20191107/us-east-1/sts/aws4_request, SignedHeaders=content-length;content-type;host;x-amz-date;x-mongodb-gs2-cb-flag;x-mongodb-server-nonce, Signature=ab62ce1c75f19c4c8b918b2ed63b46512765ed9b8bb5d79b374ae83eeac11f55",
    "d" : "20191107T002607Z"
    "t" : "<security_token>"
}
```

Note that `X-AMZ-Security-Token` is required when using temporary credentials. When using regular credentials, it MUST
be omitted. Each message above will be encoded as BSON V1.1 objects and sent to the peer as the value of `payload`.
Therefore, the SASL conversation would appear as:

Client First

```javascript
{
    "saslStart" : 1,
    "mechanism" : "MONGODB-AWS"
    "payload" : new BinData(0, "NAAAAAVyACAAAAAAWj0lSjp8M0BMKGU+QVAzRSpWfk0hJigqO1V+b0FaVz4QcABuAAAAAA==")
}
```

Server First

```javascript
{
    "conversationId" : 1,
    "done" : false,
    "payload" : new BinData(0, "ZgAAAAVzAEAAAAAAWj0lSjp8M0BMKGU+QVAzRSpWfk0hJigqO1V+b0FaVz5Rj7x9UOBHJLvPgvgPS9sSzZUWgAPTy8HBbI1cG1WJ9gJoABIAAABzdHMuYW1hem9uYXdzLmNvbQAA"),
    "ok" : 1.0
}
```

Client Second:

```javascript
{
    "saslContinue" : 1,
    "conversationId" : 1,
    "payload" : new BinData(0, "LQEAAAJhAAkBAABBV1M0LUhNQUMtU0hBMjU2IENyZWRlbnRpYWw9QUtJQUlDR1ZMS09LWlZZM1gzREEvMjAxOTExMTIvdXMtZWFzdC0xL3N0cy9hd3M0X3JlcXVlc3QsIFNpZ25lZEhlYWRlcnM9Y29udGVudC1sZW5ndGg7Y29udGVudC10eXBlO2hvc3Q7eC1hbXotZGF0ZTt4LW1vbmdvZGItZ3MyLWNiLWZsYWc7eC1tb25nb2RiLXNlcnZlci1ub25jZSwgU2lnbmF0dXJlPThhMTI0NGZjODYyZTI5YjZiZjc0OTFmMmYwNDE5NDY2ZGNjOTFmZWU1MTJhYTViM2ZmZjQ1NDY3NDEwMjJiMmUAAmQAEQAAADIwMTkxMTEyVDIxMDEyMloAAA==")
}
```

In response to the Server First message, drivers MUST send an `authorization header`. Drivers MUST follow the
[Signature Version 4 Signing Process](https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html) to
calculate the signature for the `authorization header`. The required and optional headers and their associated values
drivers MUST use for the canonical request (see
[Summary of Signing Steps](https://docs.aws.amazon.com/general/latest/gr/sigv4-create-canonical-request.html)) are
specified in the table below. The following pseudocode shows the construction of the Authorization header.

```javascript
Authorization: algorithm Credential=access key ID/credential scope, SignedHeaders=SignedHeaders, Signature=signature
```

The following example shows a finished Authorization header.

```javascript
Authorization: AWS4-HMAC-SHA256 Credential=AKIDEXAMPLE/20150830/us-east-1/iam/aws4_request, SignedHeaders=content-type;host;x-amz-date, Signature=5d672d79c15b13162d9279b0855cfba6789a8edb4c82c400e06b5924a6f2b5d7
```

The following diagram is a summary of the steps drivers MUST follow to calculate the signature.

![image](includes/calculating_a_signature.png)

| Name                      | Value                                                                                                                         |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| HTTP Request Method       | POST                                                                                                                          |
| URI                       | /                                                                                                                             |
| Content-Type\*            | application/x-www-form-urlencoded                                                                                             |
| Content-Length\*          | 43                                                                                                                            |
| Host\*                    | Host field from Server First Message                                                                                          |
| Region                    | Derived from Host - see [Region Calculation](#region-calculation) below                                                       |
| X-Amz-Date\*              | See [Amazon Documentation](https://docs.aws.amazon.com/general/latest/gr/sigv4_elements.html)                                 |
| X-Amz-Security-Token\*    | Optional, see [Amazon Documentation](https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html?shortFooter=true) |
| X-MongoDB-Server-Nonce\*  | Base64 string of server nonce                                                                                                 |
| X-MongoDB-GS2-CB-Flag\*   | ASCII lower-case character 'n' or 'y' or 'p'                                                                                  |
| X-MongoDB-Optional-Data\* | Optional data, base64 encoded representation of the optional object provided by the client                                    |
| Body                      | Action=GetCallerIdentity&Version=2011-06-15                                                                                   |

> [!NOTE]
> `*`, Denotes a header that MUST be included in SignedHeaders, if present.

#### Region Calculation

To get the region from the host, the driver MUST follow the algorithm expressed in pseudocode below. :

```
if the host is invalid according to the rules described earlier
    the region is undefined and the driver must raise an error.
else if the host is "aws.amazonaws.com"
    the region is "us-east-1"
else if the host contains the character '.' (a period)
        split the host by its periods. The region is the second label.
else // the valid host string contains no periods and is not "aws.amazonaws.com"
    the region is "us-east-1"
```

Examples are provided below.

| Host                           | Region    | Notes                                            |
| ------------------------------ | --------- | ------------------------------------------------ |
| sts.amazonaws.com              | us-east-1 | the host is "sts.amazonaws.com"; use `us-east-1` |
| sts.us-west-2.amazonaws.com    | us-west-2 | use the second label                             |
| sts.us-west-2.amazonaws.com.ch | us-west-2 | use the second label                             |
| example.com                    | com       | use the second label                             |
| localhost                      | us-east-1 | no "`.`" character; use the default region       |
| sts..com                       | <Error>   | second label is empty                            |
| .amazonaws.com                 | <Error>   | starts with a period                             |
| sts.amazonaws.                 | <Error>   | ends with a period                               |
| ""                             | <Error>   | empty string                                     |
| "string longer than 255"       | <Error>   | string longer than 255 bytes                     |

#### [MongoCredential](#mongocredential) Properties

- username

  MAY be specified. The non-sensitive AWS access key.

- source

  MUST be "$external". Defaults to `$external`.

- password

  MAY be specified. The sensitive AWS secret key.

- mechanism

  MUST be "MONGODB-AWS"

- mechanism_properties

  - AWS_SESSION_TOKEN

    Drivers MUST allow the user to specify an AWS session token for authentication with temporary credentials.

#### Obtaining Credentials

Drivers will need AWS IAM credentials (an access key, a secret access key and optionally a session token) to complete
the steps in the
[Signature Version 4 Signing Process](https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html?shortFooter=true).
If a username and password are provided drivers MUST use these for the AWS IAM access key and AWS IAM secret key,
respectively. If, additionally, a session token is provided Drivers MUST use it as well. If a username is provided
without a password (or vice-versa) or if *only* a session token is provided Drivers MUST raise an error. In other words,
regardless of how Drivers obtain credentials the only valid combination of credentials is an access key ID and a secret
access key or an access key ID, a secret access key and a session token.

AWS recommends using an SDK to "take care of some of the heavy lifting necessary in successfully making API calls,
including authentication, retry behavior, and more".

A recommended pattern for drivers with existing custom implementation is to not further enhance existing
implementations, and take an optional dependency on the AWS SDK. If the SDK is available, use it, otherwise fallback to
the existing implementation.

One thing to be mindful of when adopting an AWS SDK is that they typically will check for credentials in a shared AWS
credentials file when one is present, which may be confusing for users relying on the previous authentication handling
behavior. It would be helpful to include a note like the following:

"Because we are now using the AWS SDK to handle credentials, if you have a shared AWS credentials or config file, then
those credentials will be used by default if AWS auth environment variables are not set. To override this behavior, set
`AWS_SHARED_CREDENTIALS_FILE=""` in your shell or set the equivalent environment variable value in your script or
application. Alternatively, you can create an AWS profile specifically for your MongoDB credentials and set the
`AWS_PROFILE` environment variable to that profile name."

The order in which Drivers MUST search for credentials is:

1. The URI
2. Environment variables
3. Using `AssumeRoleWithWebIdentity` if `AWS_WEB_IDENTITY_TOKEN_FILE` and `AWS_ROLE_ARN` are set.
4. The ECS endpoint if `AWS_CONTAINER_CREDENTIALS_RELATIVE_URI` is set. Otherwise, the EC2 endpoint.

> [!NOTE]
> See *Should drivers support accessing Amazon EC2 instance metadata in Amazon ECS* in [Q & A](#q-and-a)
>
> Drivers are not expected to handle
> [AssumeRole](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html) requests directly. See
> description of `AssumeRole` below, which is distinct from `AssumeRoleWithWebIdentity` requests that are meant to be
> handled directly by the driver.

##### URI

An example URI for authentication with MONGODB-AWS using AWS IAM credentials passed through the URI is as follows:

```javascript
"mongodb://<access_key>:<secret_key>@mongodb.example.com/?authMechanism=MONGODB-AWS"
```

Users MAY have obtained temporary credentials through an
[AssumeRole](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html) request. If so, then in addition
to a username and password, users MAY also provide an `AWS_SESSION_TOKEN` as a `mechanism_property`.

```javascript
"mongodb://<access_key>:<secret_key>@mongodb.example.com/?authMechanism=MONGODB-AWS&authMechanismProperties=AWS_SESSION_TOKEN:<security_token>"
```

##### Environment variables

AWS Lambda runtimes set several
[environment variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html#configuration-envvars-runtime)
during initialization. To support AWS Lambda runtimes Drivers MUST check a subset of these variables, i.e.,
`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN`, for the access key ID, secret access key and
session token, respectively if AWS credentials are not explicitly provided in the URI. The `AWS_SESSION_TOKEN` may or
may not be set. However, if `AWS_SESSION_TOKEN` is set Drivers MUST use its value as the session token. Drivers
implemented in programming languages that support altering environment variables MUST always read environment variables
dynamically during authorization, to handle the case where another part the application has refreshed the credentials.

However, if environment variables are not present during initial authorization, credentials may be fetched from another
source and cached. Even if the environment variables are present in subsequent authorization attempts, the driver MUST
use the cached credentials, or refresh them if applicable. This behavior is consistent with how the AWS SDKs behave.

##### AssumeRoleWithWebIdentity

AWS EKS clusters can be configured to automatically provide a valid OpenID Connect ID token and associated role ARN.
These can be exchanged for temporary credentials using an
[AssumeRoleWithWebIdentity request](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html).

If the `AWS_WEB_IDENTITY_TOKEN_FILE` and `AWS_ROLE_ARN` environment variables are set, drivers MUST make an
`AssumeRoleWithWebIdentity` request to obtain temporary credentials. AWS recommends using an AWS Software Development
Kit (SDK) to make STS requests.

The `WebIdentityToken` value is obtained by reading the contents of the file given by `AWS_WEB_IDENTITY_TOKEN_FILE`. The
`RoleArn` value is obtained from `AWS_ROLE_ARN`. If `AWS_ROLE_SESSION_NAME` is set, it MUST be used for the
`RoleSessionName` parameter, otherwise a suitable random name can be chosen. No other request parameters need to be set
if using an SDK.

If not using an AWS SDK, the request must be made manually. If making a manual request, the `Version` should be
specified as well. An example manual POST request looks like the following:

```html
https://sts.amazonaws.com/
?Action=AssumeRoleWithWebIdentity
&RoleSessionName=app1
&RoleArn=<role_arn>
&WebIdentityToken=<token_file_contents>
&Version=2011-06-15
```

with the header:

```html
Accept: application/json
```

The JSON response from the STS endpoint will contain credentials in this format:

```javascript
{
    "Credentials": {
        "AccessKeyId": <access_key>,
        "Expiration": <date>,
        "RoleArn": <assumed_role_arn>,
        "SecretAccessKey": <secret_access_key>,
        "SessionToken": <session_token>
    }
}
```

Note that the token is called `SessionToken` and not `Token` as it would be with other credential responses.

##### ECS endpoint

If a username and password are not provided and the aforementioned environment variables are not set, drivers MUST query
a link-local AWS address for temporary credentials. If temporary credentials cannot be obtained then drivers MUST fail
authentication and raise an error. Drivers SHOULD enforce a 10 second read timeout while waiting for incoming content
from both the ECS and EC2 endpoints. If the environment variable `AWS_CONTAINER_CREDENTIALS_RELATIVE_URI` is set then
drivers MUST assume that it was set by an AWS ECS agent and use the URI
`http://169.254.170.2/$AWS_CONTAINER_CREDENTIALS_RELATIVE_URI` to obtain temporary credentials. Querying the URI will
return the JSON response:

```javascript
{
 "AccessKeyId": <access_key>,
 "Expiration": <date>,
 "RoleArn": <task_role_arn>,
 "SecretAccessKey": <secret_access_key>,
 "Token": <security_token>
}
```

##### EC2 endpoint

If the environment variable `AWS_CONTAINER_CREDENTIALS_RELATIVE_URI` is unset, drivers MUST use the EC2 endpoint,

```html
http://169.254.169.254/latest/meta-data/iam/security-credentials/<role-name>
```

with the required header,

```html
X-aws-ec2-metadata-token: <secret-token>
```

to access the EC2 instance's metadata. Drivers MUST obtain the role name from querying the URI

```html
http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

The role name request also requires the header `X-aws-ec2-metadata-token`. Drivers MUST use v2 of the EC2 Instance
Metadata Service
([IMDSv2](https://aws.amazon.com/blogs/security/defense-in-depth-open-firewalls-reverse-proxies-ssrf-vulnerabilities-ec2-instance-metadata-service/))
to access the secret token. In other words, Drivers MUST

- Start a session with a simple HTTP PUT request to IMDSv2.

  - The URL is `http://169.254.169.254/latest/api/token`.
  - The required header is `X-aws-ec2-metadata-token-ttl-seconds`. Its value is the number of seconds the secret token
    should remain valid with a max of six hours (`21600` seconds).

- Capture the secret token IMDSv2 returned as a response to the PUT request. This token is the value for the header
  `X-aws-ec2-metadata-token`.

The curl recipe below demonstrates the above. It retrieves a secret token that's valid for 30 seconds. It then uses that
token to access the EC2 instance's credentials:

```bash
$ TOKEN=`curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 30"`
$ ROLE_NAME=`curl http://169.254.169.254/latest/meta-data/iam/security-credentials/ -H "X-aws-ec2-metadata-token: $TOKEN"`
$ curl http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE_NAME -H "X-aws-ec2-metadata-token: $TOKEN"
```

Drivers can test this process using the mock EC2 server in
[mongo-enterprise-modules](https://github.com/10gen/mongo-enterprise-modules/blob/master/jstests/external_auth/lib/ec2_metadata_http_server.py).
The script must be run with `python3`:

```bash
python3 ec2_metadata_http_server.py
```

To re-direct queries from the EC2 endpoint to the mock server, replace the link-local address (`http://169.254.169.254`)
with the IP and port of the mock server (by default, `http://localhost:8000`). For example, the curl script above
becomes:

```bash
$ TOKEN=`curl -X PUT "http://localhost:8000/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 30"`
$ ROLE_NAME=`curl http://localhost:8000/latest/meta-data/iam/security-credentials/ -H "X-aws-ec2-metadata-token: $TOKEN"`
$ curl http://localhost:8000/latest/meta-data/iam/security-credentials/$ROLE_NAME -H "X-aws-ec2-metadata-token: $TOKEN"
```

The JSON response from both the actual and mock EC2 endpoint will be in this format:

```javascript
{
        "Code": "Success",
        "LastUpdated" : <date>,
        "Type": "AWS-HMAC",
    "AccessKeyId" : <access_key>,
        "SecretAccessKey": <secret_access_key>,
        "Token" : <security_token>,
        "Expiration": <date>
}
```

From the JSON response drivers MUST obtain the `access_key`, `secret_key` and `security_token` which will be used during
the
[Signature Version 4 Signing Process](https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html?shortFooter=true).

##### Caching Credentials

Credentials fetched by the driver using AWS endpoints MUST be cached and reused to avoid hitting AWS rate limitations.
AWS recommends using a suitable Software Development Kit (SDK) for your language. If that SDK supports credential fetch
and automatic refresh/caching, then that mechanism can be used in lieu of manual caching.

If using manual caching, the "Expiration" field MUST be stored and used to determine when to clear the cache.
Credentials are considered valid if they are more than five minutes away from expiring; to the reduce the chance of
expiration before they are validated by the server. Credentials that are retrieved from environment variables MUST NOT
be cached.

If there are no current valid cached credentials, the driver MUST initiate a credential request. To avoid adding a
bottleneck that would override the `maxConnecting` setting, the driver MUST not place a lock on making a request. The
cache MUST be written atomically.

If AWS authentication fails for any reason, the cache MUST be cleared.

> [!NOTE]
> Five minutes was chosen based on the AWS documentation for
> [IAM roles for EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html) : "We make new
> credentials available at least five minutes before the expiration of the old credentials". The intent is to have some
> buffer between when the driver fetches the credentials and when the server verifies them.

### MONGODB-OIDC

- Since: 7.0 Enterprise

MONGODB-OIDC authenticates using an [OpenID Connect (OIDC)](https://openid.net/specs/openid-connect-core-1_0.html)
access token.

There are two OIDC authentication flows that drivers can support: machine-to-machine ("machine") and human-in-the-loop
("human"). Drivers MUST support the machine authentication flow. Drivers MAY support the human authentication flow.

The MONGODB-OIDC specification refers to the following OIDC concepts:

- **Identity Provider (IdP)**: A service that manages user accounts and authenticates users or applications, such as
  Okta or OneLogin. In the [Human Authentication Flow](#human-authentication-flow), the
  [OIDC Human Callback](#oidc-human-callback) interacts directly the IdP. In the
  [Machine Authentication Flow](#machine-authentication-flow), only the MongoDB server interacts directly the IdP.
- **Access token**: Used to authenticate requests to protected resources. OIDC access tokens are signed JWT strings.
- **Refresh token**: Some OIDC providers may return a refresh token in addition to an access token. A refresh token can
  be used to retrieve new access tokens without requiring a human to re-authorize the application. Refresh tokens are
  typically only supported by the [Human Authentication Flow](#human-authentication-flow).

#### Machine Authentication Flow

The machine authentication flow is intended to be used in cases where human interaction is not necessary or practical,
such as to authenticate database access for a web service. Some OIDC documentation refers to the machine authentication
flow as "workload authentication".

Drivers MUST implement all behaviors described in the MONGODB-OIDC specification, unless the section or block
specifically says that it only applies to the [Human Authentication Flow](#human-authentication-flow).

#### Human Authentication Flow

The human authentication flow is intended to be used for applications that involve direct human interaction, such as
database tools or CLIs. Some OIDC documentation refers to the human authentication flow as "workforce authentication".

Drivers that support the [Human Authentication Flow](#human-authentication-flow) MUST implement all behaviors described
in the MONGODB-OIDC specification, including sections or blocks that specifically say that it only applies the
[Human Authentication Flow](#human-authentication-flow).

#### [MongoCredential](#mongocredential) Properties

- username

  MAY be specified. Its meaning varies depending on the OIDC provider integration used.

- source

  MUST be "$external". Defaults to `$external`.

- password

  MUST NOT be specified.

- mechanism

  MUST be "MONGODB-OIDC"

- mechanism_properties

  - ENVIRONMENT

    Drivers MUST allow the user to specify the name of a built-in OIDC application environment integration to use to
    obtain credentials. If provided, the value MUST be one of `["test", "azure", "gcp"]`. If both `ENVIRONMENT` and an
    [OIDC Callback](#oidc-callback) or [OIDC Human Callback](#oidc-human-callback) are provided for the same
    `MongoClient`, the driver MUST raise an error.

  - TOKEN_RESOURCE

    The URI of the target resource. If `TOKEN_RESOURCE` is provided and `ENVIRONMENT` is not one of `["azure", "gcp"]`
    or `TOKEN_RESOURCE` is not provided and `ENVIRONMENT` is one of `["azure", "gcp"]`, the driver MUST raise an error.
    Note: because the `TOKEN_RESOURCE` is often itself a URL, drivers MUST document that a `TOKEN_RESOURCE` with a comma
    `,` must be given as a `MongoClient` configuration and not as part of the connection string, and that the
    `TOKEN_RESOURCE` value can contain a colon `:` character.

  - OIDC_CALLBACK

    An [OIDC Callback](#oidc-callback) that returns OIDC credentials. Drivers MAY allow the user to specify an
    [OIDC Callback](#oidc-callback) using a `MongoClient` configuration instead of a mechanism property, depending on
    what is idiomatic for the driver. Drivers MUST NOT support both the `OIDC_CALLBACK` mechanism property and a
    `MongoClient` configuration.

  - OIDC_HUMAN_CALLBACK

    An [OIDC Human Callback](#oidc-human-callback) that returns OIDC credentials. Drivers MAY allow the user to specify
    a [OIDC Human Callback](#oidc-human-callback) using a `MongoClient` configuration instead of a mechanism property,
    depending on what is idiomatic for the driver. Drivers MUST NOT support both the `OIDC_HUMAN_CALLBACK` mechanism
    property and a `MongoClient` configuration. Drivers MUST return an error if both an [OIDC Callback](#oidc-callback)
    and `OIDC Human Callback` are provided for the same `MongoClient`. This property is only required for drivers that
    support the [Human Authentication Flow](#human-authentication-flow).

  - ALLOWED_HOSTS

    The list of allowed hostnames or ip-addresses (ignoring ports) for MongoDB connections. The hostnames may include a
    leading "\*." wildcard, which allows for matching (potentially nested) subdomains. `ALLOWED_HOSTS` is a security
    feature and MUST default to
    `["*.mongodb.net", "*.mongodb-qa.net", "*.mongodb-dev.net", "*.mongodbgov.net", "localhost", "127.0.0.1", "::1"]`.
    When MONGODB-OIDC authentication using a [OIDC Human Callback](#oidc-human-callback) is attempted against a hostname
    that does not match any of list of allowed hosts, the driver MUST raise a client-side error without invoking any
    user-provided callbacks. This value MUST NOT be allowed in the URI connection string. The hostname check MUST be
    performed after SRV record resolution, if applicable. This property is only required for drivers that support the
    [Human Authentication Flow](#human-authentication-flow).

<span id="built-in-provider-integrations"/>

#### Built-in OIDC Environment Integrations

Drivers MUST support all of the following built-in OIDC application environment integrations.

**Test**

The test integration is enabled by setting auth mechanism property `ENVIRONMENT:test`. It is meant for driver testing
purposes, and is not meant to be documented as a user-facing feature.

If enabled, drivers MUST generate a token using a script in the `auth_oidc`
[folder](https://github.com/mongodb-labs/drivers-evergreen-tools/tree/master/.evergreen/auth_oidc#readme) in Drivers
Evergreen Tools. The driver MUST then set the `OIDC_TOKEN_FILE` environment variable to the path to that file. At
runtime, the driver MUST use the `OIDC_TOKEN_FILE` environment variable and read the OIDC access token from that path.
The driver MUST use the contents of that file as value in the `jwt` field of the `saslStart` payload.

Drivers MAY implement the "test" integration so that it conforms to the function signature of the
[OIDC Callback](#oidc-callback) to prevent having to re-implement the "test" integration logic in the OIDC prose tests.

**Azure**

The Azure provider integration is enabled by setting auth mechanism property `ENVIRONMENT:azure`.

If enabled, drivers MUST use an internal machine callback that calls the
[Azure Instance Metadata Service](https://learn.microsoft.com/en-us/azure/virtual-machines/instance-metadata-service)
and parse the JSON response body, as follows:

Make an HTTP GET request to

```
http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=<resource>&client_id=<client_id>
```

with headers

```
Accept: application/json
Metadata: true
```

where `<resource>` is the url-encoded value of the `TOKEN_RESOURCE` mechanism property and `<client_id>` is the
`username` from the connection string. If a `username` is not provided, the `client_id` query parameter should be
omitted. The timeout should equal the `callbackTimeoutMS` parameter given to the callback.

```bash
curl -X GET \
  -H "Accept: application/json" \
  -H "Metadata: true" \
  --max-time $CALLBACK_TIMEOUT_MS \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=$ENCODED_TOKEN_RESOURCE"
```

The JSON response will be in this format:

```json
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "",
  "expires_in": "3599",
  "expires_on": "1506484173",
  "not_before": "1506480273",
  "resource": "https://management.azure.com/",
  "token_type": "Bearer"
}
```

The driver MUST use the returned `"access_token"` value as the access token in a `JwtStepRequest`. If the response does
not return a status code of 200, the driver MUST raise an error including the HTTP response body.

For more details, see
[How to use managed identities for Azure resources on an Azure VM to acquire an access token](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/how-to-use-vm-token).

The callback itself MUST not perform any caching, and the driver MUST cache its tokens in the same way as if a custom
callback had been provided by the user.

For details on test environment setup, see the README in
[Drivers-Evergreen-Tools](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/auth_oidc/azure/README.md).

**GCP**

The GCP provider integration is enabled by setting auth mechanism property `ENVIRONMENT:gcp`.

If enabled, drivers MUST use an internal machine callback that calls the
[Google Cloud VM metadata](https://cloud.google.com/compute/docs/metadata/overview) endpoint and parse the JSON response
body, as follows:

Make an HTTP GET request to

```
http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience=<resource>
```

with headers

```
Metadata-Flavor: Google
```

where `<resource>` is the url-encoded value of the `TOKEN_RESOURCE` mechanism property. The timeout should equal the
`callbackTimeoutMS` parameter given to the callback.

```bash
curl -X GET \
  -H "Metadata-Flavor: Google" \
  --max-time $CALLBACK_TIMEOUT_MS \
  "http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience=$ENCODED_TOKEN_RESOURCE"
```

The response body will be the access token itself.

The driver MUST use the returned value as the access token in a `JwtStepRequest`. If the response does not return a
status code of 200, the driver MUST raise an error including the HTTP response body.

For more details, see [View and query VM metadata](https://cloud.google.com/compute/docs/metadata/querying-metadata).

The callback itself MUST not perform any caching, and the driver MUST cache its tokens in the same way as if a custom
callback had been provided by the user.

For details on test environment setup, see the README in
[Drivers-Evergreen-Tools](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/auth_oidc/gcp/README.md).

#### OIDC Callback

Drivers MUST allow users to provide a callback that returns an OIDC access token. The purpose of the callback is to
allow users to integrate with OIDC providers not supported by the
[Built-in Provider Integrations](#built-in-provider-integrations). Callbacks can be synchronous or asynchronous,
depending on the driver and/or language. Asynchronous callbacks should be preferred when other operations in the driver
use asynchronous functions.

Drivers MUST provide a way for the callback to be either automatically canceled, or to cancel itself. This can be as a
timeout argument to the callback, a cancellation context passed to the callback, or some other language-appropriate
mechanism. The timeout value MUST be `min(remaining connectTimeoutMS, remaining timeoutMS)` as described in the Server
Selection section of the CSOT spec. If CSOT is not applied, then the driver MUST use 1 minute as the timeout.

The driver MUST pass the following information to the callback:

- `timeout`: A timeout, in milliseconds, a deadline, or a `timeoutContext`.

- `username`: The username given as part of the connection string or `MongoClient` parameter.

- `version`: The callback API version number. The version number is used to communicate callback API changes that are
  not breaking but that users may want to know about and review their implementation. Drivers MUST pass `1` for the
  initial callback API version number and increment the version number anytime the API changes. Note that this may
  eventually lead to some drivers having different callback version numbers.

  For example, users may add the following check in their callback:

  ```typescript
  if(params.version > 1) {
      throw new Error("OIDC callback API has changed!");
  }
  ```

The callback MUST be able to return the following information:

- `accessToken`: An OIDC access token string. The driver MUST NOT attempt to validate `accessToken` directly.
- `expiresIn`: An optional expiry duration for the access token. Drivers with optional parameters MAY interpret a
  missing value as infinite. Drivers MUST error if a negative value is returned. Drivers SHOULD use the most idiomatic
  type for representing a duration in the driver's language. Note that the access token expiry value is currently not
  used in [Credential Caching](#credential-caching), but is intended to support future caching optimizations.

The signature and naming of the callback API is up to the driver's discretion. Drivers MUST ensure that additional
optional input parameters and return values can be added to the callback signature in the future without breaking
backward compatibility.

An example callback API might look like:

```typescript
interface OIDCCallbackParams {
    callbackTimeoutMS: int;
    username: str;
    version: int;
}

interface OIDCCredential {
    accessToken: string;
    expiresInSeconds: Optional<int>;
}

function oidcCallback(params: OIDCCallbackParams): OIDCCredential
```

##### OIDC Human Callback

The human callback is an OIDC callback that includes additional information that is required when using the
[Human Authentication Flow](#human-authentication-flow). Drivers that support the
[Human Authentication Flow](#human-authentication-flow) MUST implement the human callback.

In addition to the information described in the [OIDC Callback](#oidc-callback) section, drivers MUST be able to pass
the following information to the callback:

- `idpInfo`: Information used to authenticate with the IdP.
  - `issuer`: A URL which describes the Authentication Server. This identifier should be the iss of provided access
    tokens, and be viable for RFC8414 metadata discovery and RFC9207 identification.
  - `clientId`: A unique client ID for this OIDC client.
  - `requestScopes`: A list of additional scopes to request from IdP.
- `refreshToken`: The refresh token, if applicable, to be used by the callback to request a new token from the issuer.

In addition to the information described in the [OIDC Callback](#oidc-callback) section, the callback MUST be able to
return the following information:

- `refreshToken`: An optional refresh token that can be used to fetch new access tokens.

The signature and naming of the callback API is up to the driver's discretion. Drivers MAY use a single callback API for
both callback types or separate callback APIs for each callback type. Drivers MUST ensure that additional optional input
parameters and return values can be added to the callback signature in the future without breaking backward
compatibility.

An example human callback API might look like:

```typescript
interface IdpInfo {
  issuer: string;
  clientId: Optional<string>;
  requestScopes: Optional<Array<string>>;
}

interface OIDCCallbackParams {
    username: str;
    callbackTimeoutMS: int;
    version: int;
    idpInfo: Optional<IdpInfo>;
    refreshToken: Optional<any>;
}

interface OIDCCredential {
    accessToken: string;
    expiresInSeconds: Optional<int>;
    refreshToken: Optional<any>;
}

function oidcCallback(params: OIDCCallbackParams): OIDCCredential
```

When a human callback is provided, drivers MUST use the following behaviors when calling the callback:

- The driver MUST pass the `IdpInfo` and the refresh token (if available) to the callback.
  - If there is no cached `IdpInfo`, drivers MUST start a [Two-Step](#two-step) conversation before calling the human
    callback. See the Conversation and [Credential Caching](#credential-caching) sections for more details.
- The timeout duration MUST be 5 minutes. This is to account for the human interaction required to complete the
  callback. In this case, the callback is not subject to CSOT.

#### Conversation

OIDC supports two conversation styles: one-step and two-step. The server detects whether the driver is using a one-step
or two-step conversation based on the structure of the `saslStart` payload.

##### One-Step

A one-step conversation is used for OIDC providers that allow direct access to an access token. For example, an OIDC
provider configured for machine-to-machine authentication may provide an access token via a local file pre-loaded on an
application host.

Drivers MUST use a one-step conversation when using a cached access token, one of the
[Built-in Provider Integrations](#built-in-provider-integrations), or an [OIDC Callback](#oidc-callback) (not an
[OIDC Human Callback](#oidc-human-callback)).

The one-step conversation starts with a `saslStart` containing a `JwtStepRequest` payload. The value of `jwt` is the
OIDC access token string.

```typescript
interface JwtStepRequest:
    // Compact serialized JWT with signature.
    jwt: string;
}
```

An example OIDC one-step SASL conversation with access token string "abcd1234" looks like:

```javascript
// Client:
{
  saslStart: 1,
  mechanism: "MONGODB-OIDC",
  db: "$external"
  // payload is a BSON generic binary field containing a JwtStepRequest BSON
  // document: {"jwt": "abcd1234"}
  payload: BinData(0, "FwAAAAJqd3QACQAAAGFiY2QxMjM0AAA=")
}

// Server:
{
  conversationId : 1,
  payload: BinData(0, ""),
  done: true,
  ok: 1
}
```

##### Two-Step

A two-step conversation is used for OIDC providers that require an extra authorization step before issuing a credential.
For example, an OIDC provider configured for end-user authentication may require redirecting the user to a webpage so
they can authorize the request.

Drivers that support the [Human Authentication Flow](#human-authentication-flow) MUST implement the two-step
conversation. Drivers MUST use a two-step conversation when using a [OIDC Human Callback](#oidc-human-callback) and when
there is no cached access token.

The two-step conversation starts with a `saslStart` containing a `PrincipalStepRequest` payload. The value of `n` is the
`username` from the connection string. If a `username` is not provided, field `n` should be omitted.

```typescript
interface PrincipalStepRequest {
  // Name of the OIDC user principal.
  n: Optional<string>;
}
```

The server uses `n` (if provided) to select an appropriate IdP. Note that the principal name is optional as it may be
provided by the IdP in environments where only one IdP is used.

The server responds to the `PrincipalStepRequest` with `IdpInfo` for the selected IdP:

```typescript
interface IdpInfo {
  // A URL which describes the Authentication Server. This identifier should
  // be the iss of provided access tokens, and be viable for RFC8414 metadata
  // discovery and RFC9207 identification.
  issuer: string;

  // A unique client ID for this OIDC client.
  clientId: string;

  // A list of additional scopes to request from IdP.
  requestScopes: Optional<Array<string>>;
}
```

The driver passes the IdP information to the [OIDC Human Callback](#oidc-human-callback), which should return an OIDC
credential containing an access token and, optionally, a refresh token.

The driver then sends a `saslContinue` with a `JwtStepRequest` payload to complete authentication. The value of `jwt` is
the OIDC access token string.

```typescript
interface JwtStepRequest:
    // Compact serialized JWT with signature.
    jwt: string;
}
```

An example OIDC two-step SASL conversation with username "myidp" and access token string "abcd1234" looks like:

```javascript
// Client:
{
  saslStart: 1,
  mechanism: "MONGODB-OIDC",
  db: "$external",
  // payload is a BSON generic binary field containing a PrincipalStepRequest
  // BSON document: {"n": "myidp"}
  payload: BinData(0, "EgAAAAJuAAYAAABteWlkcAAA")
}

// Server:
{
  conversationId : 1,
  // payload is a BSON generic binary field containing an IdpInfo BSON document:
  // {"issuer": "https://issuer", "clientId": "abcd", "requestScopes": ["a","b"]}
  payload: BinData(0, "WQAAAAJpc3N1ZXIADwAAAGh0dHBzOi8vaXNzdWVyAAJjbGllbnRJZAAFAAAAYWJjZAAEcmVxdWVzdFNjb3BlcwAXAAAAAjAAAgAAAGEAAjEAAgAAAGIAAAA="),
  done: false,
  ok: 1
}

// Client:
{
  saslContinue: 1,
  conversationId: 1,
  // payload is a BSON generic binary field containing a JwtStepRequest BSON
  // document: {"jwt": "abcd1234"}
  payload: BinData(0, "FwAAAAJqd3QACQAAAGFiY2QxMjM0AAA=")
}

// Server:
{
  conversationId: 1,
  payload: BinData(0, ""),
  done: true,
  ok: 1
}
```

#### Credential Caching

Some OIDC providers may impose rate limits, incur per-request costs, or be slow to return. To minimize those issues,
drivers MUST cache and reuse access tokens returned by OIDC providers.

Drivers MUST cache the most recent access token per `MongoClient` (henceforth referred to as the *Client Cache*).
Drivers MAY store the *Client Cache* on the `MongoClient` object or any object that guarantees exactly 1 cached access
token per `MongoClient`. Additionally, drivers MUST cache the access token used to authenticate a connection on the
connection object (henceforth referred to as the *Connection Cache*).

Drivers MUST ensure that only one call to the configured provider or OIDC callback can happen at a time. To avoid adding
a bottleneck that would override the `maxConnecting` setting, the driver MUST NOT hold an exclusive lock while running
`saslStart` or `saslContinue`.

Example code for credential caching using the read-through cache pattern:

```python
def get_access_token():
  # Lock the OIDC authenticator so that only one caller can modify the cache
  # and call the configured OIDC provider at a time.
  client.oidc_cache.lock()

  # Check if we can use the access token from the Client Cache or if we need
  # to fetch and cache a new access token from the OIDC provider.
  access_token = client.oidc_cache.access_token
  is_cache = True
  if access_token is None
    credential = oidc_provider()
    is_cache = False
    client.oidc_cache.access_token = credential.access_token

  client.oidc_cache.unlock()

  return access_token, is_cache
```

Drivers MUST have a way to invalidate a specific access token from the *Client Cache*. Invalidation MUST only clear the
cached access token if it is the same as the invalid access token and MUST be an atomic operation (e.g. using a mutex or
a compare-and-swap operation).

Example code for invalidation:

```python
def invalidate(access_token):
  client.oidc_cache.lock()

  if client.oidc_cache.access_token == access_token:
    client.oidc_cache.access_token = None

  client.oidc_cache.unlock()
```

Drivers that support the [Human Authentication Flow](#human-authentication-flow) MUST also cache the `IdPInfo` and
refresh token in the *Client Cache* when a [OIDC Human Callback](#oidc-human-callback) is configured.

**Authentication**

Use the following algorithm to authenticate a new connection:

- Check if the the *Client Cache* has an access token.
  - If it does, cache the access token in the *Connection Cache* and perform a `One-Step` SASL conversation using the
    access token in the *Client Cache*. If the server returns a Authentication error (18), invalidate that access token.
    Raise any other errors to the user. On success, exit the algorithm.
- Call the configured built-in provider integration or the OIDC callback to retrieve a new access token. Wait until it
  has been at least 100ms since the last callback invocation, to avoid overloading the callback.
- Cache the new access token in the *Client Cache* and *Connection Cache*.
- Perform a `One-Step` SASL conversation using the new access token. Raise any errors to the user.

Example code to authenticate a connection using the `get_access_token` and `invalidate` functions described above:

```python
def auth(connection):
  access_token, is_cache = get_access_token()

  # If there is a cached access token, try to authenticate with it. If
  # authentication fails with an Authentication error (18), 
  # invalidate the access token, fetch a new access token, and try
  # to authenticate again.
  # If the server fails for any other reason, do not clear the cache.
  if is_cache:
    try:
      connection.oidc_cache.access_token = access_token
      sasl_start(connection, payload={"jwt": access_token})
      return
    except ServerError as e:
      if e.code == 18:
        invalidate(access_token)
        access_token, _ = get_access_token()

  connection.oidc_cache.access_token = access_token
  sasl_start(connection, payload={"jwt": access_token})
```

For drivers that support the [Human Authentication Flow](#human-authentication-flow), use the following algorithm to
authenticate a new connection when a [OIDC Human Callback](#oidc-human-callback) is configured:

- Check if the *Client Cache* has an access token.
  - If it does, cache the access token in the *Connection Cache* and perform a [One-Step](#one-step) SASL conversation
    using the access token. If the server returns an Authentication error (18), invalidate the access token token from
    the *Client Cache*, clear the *Connection Cache*, and restart the authentication flow. Raise any other errors to the
    user. On success, exit the algorithm.
- Check if the *Client Cache* has a refresh token.
  - If it does, call the [OIDC Human Callback](#oidc-human-callback) with the cached refresh token and `IdpInfo` to get
    a new access token. Cache the new access token in the *Client Cache* and *Connection Cache*. Perform a
    [One-Step](#one-step) SASL conversation using the new access token. If the the server returns an Authentication
    error (18), clear the refresh token, invalidate the access token from the *Client Cache*, clear the *Connection
    Cache*, and restart the authentication flow. Raise any other errors to the user. On success, exit the algorithm.
- Start a new [Two-Step](#two-step) SASL conversation.
- Run a `PrincipalStepRequest` to get the `IdpInfo`.
- Call the [OIDC Human Callback](#oidc-human-callback) with the new `IdpInfo` to get a new access token and optional
  refresh token. Drivers MUST NOT pass a cached refresh token to the callback when performing a new
  [Two-Step](#two-step) conversation.
- Cache the new `IdpInfo` and refresh token in the *Client Cache* and the new access token in the *Client Cache* and
  *Connection Cache*.
- Attempt to authenticate using a `JwtStepRequest` with the new access token. Raise any errors to the user.

#### Speculative Authentication

Drivers MUST implement speculative authentication for MONGODB-OIDC during the `hello` handshake. Drivers MUST NOT
attempt speculative authentication if the *Client Cache* does not have a cached access token. Drivers MUST NOT
invalidate tokens from the *Client Cache* if speculative authentication does not succeed.

Use the following algorithm to perform speculative authentication:

- Check if the *Client Cache* has an access token.
  - If it does, cache the access token in the *Connection Cache* and send a `JwtStepRequest` with the cached access
    token in the speculative authentication SASL payload. If the response is missing a speculative authentication
    document or the speculative authentication document indicates authentication was not successful, clear the the
    *Connection Cache* and proceed to the next step.
- Authenticate with the standard authentication handshake.

Example code for speculative authentication using the `auth` function described above:

```python
def speculative_auth(connection):
  access_token = client.oidc_cache.access_token
  if access_token != None:
    connection.oidc_cache.access_token = access_token
    res = hello(connection, payload={"jwt": access_token})
    if res.speculative_authenticate.done:
      return

  connection.oidc_cache.access_token = None
  auth(connection)
```

#### Reauthentication

If any operation fails with `ReauthenticationRequired` (error code 391) and MONGODB-OIDC is in use, the driver MUST
reauthenticate the connection. Drivers MUST NOT resend a `hello` message during reauthentication, instead using SASL
messages directly. Drivers MUST NOT try to use Speculative Authentication during reauthentication. See the main
[reauthentication](#reauthentication) section for more information.

To reauthenticate a connection, invalidate the access token stored on the connection (i.e. the *Connection Cache*) from
the *Client Cache*, fetch a new access token, and re-run the SASL conversation.

Example code for reauthentication using the `auth` function described above:

```python
def reauth(connection):
  invalidate(connection.oidc_cache.access_token)
  connection.oidc_cache.access_token = None
  auth(connection)
```

### Connection String Options

`mongodb://[username[:password]@]host1[:port1][,[host2:[port2]],...[hostN:[portN]]][/database][?options]`

<span id="supported-authentication-methods"></span>

#### Auth Related Options

- authMechanism

  MONGODB-CR, MONGODB-X509, GSSAPI, PLAIN, SCRAM-SHA-1, SCRAM-SHA-256, MONGODB-AWS

  Sets the Mechanism property on the MongoCredential. When not set, the default will be one of SCRAM-SHA-256,
  SCRAM-SHA-1 or MONGODB-CR, following the auth spec default mechanism rules.

- authSource

  Sets the Source property on the MongoCredential.

For GSSAPI, MONGODB-X509 and MONGODB-AWS authMechanisms the authSource defaults to `$external`. For PLAIN the authSource
defaults to the database name if supplied on the connection string or `$external`. For MONGODB-CR, SCRAM-SHA-1 and
SCRAM-SHA-256 authMechanisms, the authSource defaults to the database name if supplied on the connection string or
`admin`.

- authMechanismProperties=PROPERTY_NAME:PROPERTY_VALUE,PROPERTY_NAME2:PROPERTY_VALUE2

  A generic method to set mechanism properties in the connection string.

For example, to set REALM and CANONICALIZE_HOST_NAME, the option would be
`authMechanismProperties=CANONICALIZE_HOST_NAME:forward,SERVICE_REALM:AWESOME`.

- gssapiServiceName (deprecated)

  An alias for `authMechanismProperties=SERVICE_NAME:mongodb`.

#### Errors

Drivers MUST raise an error if the `authSource` option is specified in the connection string with an empty value, e.g.
`mongodb://localhost/admin?authSource=`.

#### Implementation

1. Credentials MAY be specified in the connection string immediately after the scheme separator "//".

2. A realm MAY be passed as a part of the username in the url. It would be something like <dev@MONGODB.COM>, where dev
   is the username and MONGODB.COM is the realm. Per the RFC, the @ symbol should be url encoded using %40.

   - When GSSAPI is specified, this should be interpreted as the realm.
   - When non-GSSAPI is specified, this should be interpreted as part of the username.

3. It is permissible for only the username to appear in the connection string. This would be identified by having no
   colon follow the username before the '@' hostname separator.

4. The source is determined by the following:

   - if authSource is specified, it is used.
   - otherwise, if database is specified, it is used.
   - otherwise, the admin database is used.

## Test Plan

Connection string tests have been defined in the associated files:

- [Connection String](./tests/legacy/connection-string.json).

### SCRAM-SHA-256 and mechanism negotiation

Testing SCRAM-SHA-256 requires server version 3.7.3 or later with `featureCompatibilityVersion` of "4.0" or later.

Drivers that allow specifying auth parameters in code as well as via connection string should test both for the test
cases described below.

#### Step 1

Create three test users, one with only SHA-1, one with only SHA-256 and one with both. For example:

```javascript
db.runCommand({createUser: 'sha1', pwd: 'sha1', roles: ['root'], mechanisms: ['SCRAM-SHA-1']})
db.runCommand({createUser: 'sha256', pwd: 'sha256', roles: ['root'], mechanisms: ['SCRAM-SHA-256']})
db.runCommand({createUser: 'both', pwd: 'both', roles: ['root'], mechanisms: ['SCRAM-SHA-1', 'SCRAM-SHA-256']})
```

#### Step 2

For each test user, verify that you can connect and run a command requiring authentication for the following cases:

- Explicitly specifying each mechanism the user supports.
- Specifying no mechanism and relying on mechanism negotiation.

For the example users above, the `dbstats` command could be used as a test command.

For a test user supporting both SCRAM-SHA-1 and SCRAM-SHA-256, drivers should verify that negotiation selects
SCRAM-SHA-256. This may require monkey patching, manual log analysis, etc.

#### Step 3

For test users that support only one mechanism, verify that explicitly specifying the other mechanism fails.

For a non-existent username, verify that not specifying a mechanism when connecting fails with the same error type that
would occur with a correct username but incorrect password or mechanism. (Because negotiation with a non-existent user
name at one point during server development caused a handshake error, we want to verify this is seen by users as similar
to other authentication errors, not as a network or database command error on the `hello` or legacy hello commands
themselves.)

#### Step 4

To test SASLprep behavior, create two users:

1. username: "IX", password "IX"
2. username: "\\u2168" (ROMAN NUMERAL NINE), password "\\u2163" (ROMAN NUMERAL FOUR)

To create the users, use the exact bytes for username and password without SASLprep or other normalization and specify
SCRAM-SHA-256 credentials:

```javascript
db.runCommand({createUser: 'IX', pwd: 'IX', roles: ['root'], mechanisms: ['SCRAM-SHA-256']})
db.runCommand({createUser: '\\u2168', pwd: '\\u2163', roles: ['root'], mechanisms: ['SCRAM-SHA-256']})
```

For each user, verify that the driver can authenticate with the password in both SASLprep normalized and non-normalized
forms:

- User "IX": use password forms "IX" and "I\\u00ADX"
- User "\\u2168": use password forms "IV" and "I\\u00ADV"

As a URI, those have to be UTF-8 encoded and URL-escaped, e.g.:

- <mongodb://IX:IX@mongodb.example.com/admin>
- <mongodb://IX:I%C2%ADX@mongodb.example.com/admin>
- <mongodb://%E2%85%A8:IV@mongodb.example.com/admin>
- <mongodb://%E2%85%A8:I%C2%ADV@mongodb.example.com/admin>

### Speculative Authentication

See the speculative authentication section in the [MongoDB Handshake spec](../mongodb-handshake/handshake.md).

### Minimum iteration count

For SCRAM-SHA-1 and SCRAM-SHA-256, test that the minimum iteration count is respected. This may be done via unit testing
of an underlying SCRAM library.

## Backwards Compatibility

Drivers may need to remove support for association of more than one credential with a MongoClient, including

- Deprecation and removal of MongoClient constructors that take as an argument more than a single credential
- Deprecation and removal of methods that allow lazy authentication (i.e post-MongoClient construction)

Drivers need to support both the shorter and longer SCRAM-SHA-1 and SCRAM-SHA-256 conversations over MongoDB's SASL
implementation. Earlier versions of the server required an extra round trip due to an implementation decision. This was
accomplished by sending no bytes back to the server, as seen in the following conversation (extra round trip
emphasized):

```javascript
CMD = {saslStart: 1, mechanism: "SCRAM-SHA-1", payload: BinData(0, "biwsbj11c2VyLHI9ZnlrbytkMmxiYkZnT05Sdjlxa3hkYXdM"), options: {skipEmptyExchange: true}}
RESP = {conversationId : 1, payload: BinData(0,"cj1meWtvK2QybGJiRmdPTlJ2OXFreGRhd0xIbytWZ2s3cXZVT0tVd3VXTElXZzRsLzlTcmFHTUhFRSxzPXJROVpZM01udEJldVAzRTFURFZDNHc9PSxpPTEwMDAw"), done: false, ok: 1}
CMD = {saslContinue: 1, conversationId: 1, payload: BinData(0, "Yz1iaXdzLHI9ZnlrbytkMmxiYkZnT05Sdjlxa3hkYXdMSG8rVmdrN3F2VU9LVXd1V0xJV2c0bC85U3JhR01IRUUscD1NQzJUOEJ2Ym1XUmNrRHc4b1dsNUlWZ2h3Q1k9")}
RESP = {conversationId: 1, payload: BinData(0,"dj1VTVdlSTI1SkQxeU5ZWlJNcFo0Vkh2aFo5ZTA9"), done: false, ok: 1}
# Extra round trip
CMD = {saslContinue: 1, conversationId: 1, payload: BinData(0, "")}  
RESP = {conversationId: 1, payload: BinData(0,""), done: true, ok: 1}
```

The extra round trip will be removed in server version 4.4 when `options: { skipEmptyExchange: true }` is specified
during `saslStart`.

## Reference Implementation

The Java and .NET drivers currently uses eager authentication and abide by this specification.

<span id="q-and-a"></span>

## Q & A

Q: According to [Authentication Handshake](#authentication-handshake), we are calling `hello` or legacy hello for every
socket. Isn't this a lot?

Drivers should be pooling connections and, as such, new sockets getting opened should be relatively infrequent. It's
simply part of the protocol for setting up a socket to be used.

Q: Where is information related to user management?

Not here currently. Should it be? This is about authentication, not user management. Perhaps a new spec is necessary.

Q: It's possible to continue using authenticated sockets even if new sockets fail authentication. Why can't we do that
so that applications continue to work.

Yes, that's technically true. The issue with doing that is for drivers using connection pooling. An application would
function normally until an operation needed an additional connection(s) during a spike. Each new connection would fail
to authenticate causing intermittent failures that would be very difficult to understand for a user.

Q: Should a driver support multiple credentials?

No.

Historically, the MongoDB server and drivers have supported multiple credentials, one per authSource, on a single
connection. It was necessary because early versions of MongoDB allowed a user to be granted privileges to access the
database in which the user was defined (or all databases in the special case of the "admin" database). But with the
introduction of role-based access control in MongoDB 2.6, that restriction was removed and it became possible to create
applications that access multiple databases with a single authenticated user.

Role-based access control also introduces the potential for accidental privilege escalation. An application may, for
example, authenticate user A from authSource X, and user B from authSource Y, thinking that user A has privileges only
on collections in X and user B has privileges only on collections in Y. But with role-based access control that
restriction no longer exists, and it's possible that user B has, for example, more privileges on collections in X than
user A does. Due to this risk it's generally safer to create a single user with only the privileges required for a given
application, and authenticate only that one user in the application.

In addition, since only a single credential is supported per authSource, certain mechanisms are restricted to a single
credential and some credentials cannot be used in conjunction (GSSAPI and X509 both use the "$external" database).

Finally, MongoDB 3.6 introduces sessions, and allows at most a single authenticated user on any connection which makes
use of one. Therefore any application that requires multiple authenticated users will not be able to make use of any
feature that builds on sessions (e.g. retryable writes).

Drivers should therefore guide application creators in the right direction by supporting the association of at most one
credential with a MongoClient instance.

Q: Should a driver support lazy authentication?

No, for the same reasons as given in the previous section, as lazy authentication is another mechanism for allowing
multiple credentials to be associated with a single MongoClient instance.

Q: Why does SCRAM sometimes SASLprep and sometimes not?

When MongoDB implemented SCRAM-SHA-1, it required drivers to *NOT* SASLprep usernames and passwords. The primary reason
for this was to allow a smooth upgrade path from MongoDB-CR using existing usernames and passwords. Also, because
MongoDB's SCRAM-SHA-1 passwords are hex characters of a digest, SASLprep of passwords was irrelevant.

With the introduction of SCRAM-SHA-256, MongoDB requires users to explicitly create new SCRAM-SHA-256 credentials
distinct from those used for MONGODB-CR and SCRAM-SHA-1. This means SCRAM-SHA-256 passwords are not digested and any
Unicode character could now appear in a password. Therefore, the SCRAM-SHA-256 mechanism requires passwords to be
normalized with SASLprep, in accordance with the SCRAM RFC.

However, usernames must be unique, which creates a similar upgrade path problem. SASLprep maps multiple byte
representations to a single normalized one. An existing database could have multiple existing users that map to the same
SASLprep form, which makes it impossible to find the correct user document for SCRAM authentication given only a
SASLprep username. After considering various options to address or workaround this problem, MongoDB decided that the
best user experience on upgrade and lowest technical risk of implementation is to require drivers to continue to not
SASLprep usernames in SCRAM-SHA-256.

Q: Should drivers support accessing Amazon EC2 instance metadata in Amazon ECS?

No. While it's possible to allow access to EC2 instance metadata in ECS, for security reasons, Amazon states it's best
practice to avoid this. (See
[accessing EC2 metadata in ECS](https://aws.amazon.com/premiumsupport/knowledge-center/ecs-container-ec2-metadata/) and
[IAM Roles for Tasks](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html))

## Changelog

- 2024-08-19: Clarify Reauthentication and Speculative Authentication combination behavior.

- 2024-05-29: Disallow comma character when `TOKEN_RESOURCE` is given in a connection string.

- 2024-05-03: Clarify timeout behavior for OIDC machine callback. Add `serverless:forbid` to OIDC unified tests. Add an
  additional prose test for the behavior of `ALLOWED_HOSTS`.

- 2024-04-24: Clarify that TOKEN_RESOURCE for MONGODB-OIDC must be url-encoded.

- 2024-04-22: Fix API description for GCP built-in OIDC provider.

- 2024-04-22: Updated OIDC authentication flow and prose tests.

- 2024-04-22: Clarify that driver should not validate `saslSupportedMechs` content.

- 2024-04-03: Added GCP built-in OIDC provider integration.

- 2024-03-29: Updated OIDC test setup and descriptions.

- 2024-03-21: Added Azure built-in OIDC provider integration.

- 2024-03-09: Rename OIDC integration name and values.

- 2024-01-31: Migrated from reStructuredText to Markdown.

- 2024-01-17: Added MONGODB-OIDC machine auth flow spec and combine with human auth flow specs.

- 2023-04-28: Added MONGODB-OIDC auth mechanism

- 2022-11-02: Require environment variables to be read dynamically.

- 2022-10-28: Recommend the use of AWS SDKs where available.

- 2022-10-07: Require caching of AWS credentials fetched by the driver.

- 2022-10-05: Remove spec front matter and convert version history to changelog.

- 2022-09-07: Add support for AWS AssumeRoleWithWebIdentity.

- 2022-01-20: Require that timeouts be applied per the client-side operations timeout spec.

- 2022-01-14: Clarify that `OP_MSG` must be used for authentication when it is supported.

- 2021-04-23: Updated to use hello and legacy hello.

- 2021-03-04: Note that errors encountered during auth are handled by SDAM.

- 2020-03-06: Add reference to the speculative authentication section of the handshake spec.

- 2020-02-15: Rename MONGODB-IAM to MONGODB-AWS

- 2020-02-04: Support shorter SCRAM conversation starting in version 4.4 of the server.

- 2020-01-31: Clarify that drivers must raise an error when a connection string has an empty value for authSource.

- 2020-01-23: Clarify when authentication will occur.

- 2020-01-22: Clarify that authSource in URI is not treated as a user configuring auth credentials.

- 2019-12-05: Added MONGODB-IAM auth mechanism

- 2019-07-13: Clarify database to use for auth mechanism negotiation.

- 2019-04-26: Test format changed to improve specificity of behavior assertions.

  - Clarify that database name in URI is not treated as a user configuring auth credentials.

- 2018-08-08: Unknown users don't cause handshake errors. This was changed before server 4.0 GA in SERVER-34421, so the
  auth spec no longer refers to such a possibility.

- 2018-04-17: Clarify authSource defaults

  - Fix PLAIN authSource rule to allow user provided values
  - Change SCRAM-SHA-256 rules such that usernames are *NOT* normalized; this follows a change in the server design and
    should be available in server 4.0-rc0.

- 2018-03-29: Clarify auth handshake and that it only applies to non-monitoring sockets.

- 2018-03-15: Describe CANONICALIZE_HOST_NAME algorithm.

- 2018-03-02: Added SCRAM-SHA-256 and mechanism negotiation as provided by server 4.0

  - Updated default mechanism determination
  - Clarified SCRAM-SHA-1 rules around SASLprep
  - Require SCRAM-SHA-1 and SCRAM-SHA-256 to enforce a minimum iteration count

- 2017-11-10: Updated minimum server version to 2.6

  - Updated the Q & A to recommend support for at most a single credential per MongoClient
  - Removed lazy authentication section
  - Changed the list of server types requiring authentication
  - Made providing username for X509 authentication optional

- 2015-02-04: Added SCRAM-SHA-1 sasl mechanism

  - Added connection handshake
  - Changed connection string to support mechanism properties in generic form
  - Added example conversations for all mechanisms except GSSAPI
  - Miscellaneous wording changes for clarification
  - Added MONGODB-X509
  - Added PLAIN sasl mechanism
  - Added support for GSSAPI mechanism property gssapiServiceName

______________________________________________________________________
