.. role:: javascript(code)
  :language: javascript

=====================
Driver Authentication
=====================

:Spec: 100
:Spec Version: 1.7
:Title: Driver Authentication
:Author: Craig Wilson, David Golden
:Advisors: Andy Schwerin, Bernie Hacket, Jeff Yemin, David Golden
:Status: Accepted
:Type: Standards
:Minimum Server Version: 2.6
:Last Modified: 2018-04-17

.. contents::

--------

Abstract
========

MongoDB supports various authentication strategies across various versions. When authentication is turned on in the database, a driver must authenticate before it is allowed to communicate with the server. This spec defines when and how a driver performs authentication with a MongoDB server.

----
META
----

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

----------
References
----------

`Server Discovery and Monitoring <https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/>`_

Specification
=============

-----------
Definitions
-----------

Credential
	The pieces of information used to establish the authenticity of a user. This is composed of an identity and some form of evidence such as a password or a certificate.

FQDN 
	Fully Qualified Domain Name

Mechanism
	A SASL implementation of a particular type of credential negotiation.

Source
	The authority used to establish credentials and/or privileges in reference to a mongodb server. In practice, it is the database to which sasl authentication commands are sent.

Realm
	The authority used to establish credentials and/or privileges in reference to GSSAPI.

SASL
	Simple Authentication and Security Layer - `RFC 4422 <http://www.ietf.org/rfc/rfc4422.txt>`_


---------------------
Client Implementation
---------------------


MongoCredential
---------------

Drivers SHOULD contain a type called `MongoCredential`. It SHOULD contain some or all of the following information.

username (string)
	* Applies to all mechanisms.
	* Optional for MONGODB-X509.
source (string)
	* Applies to all mechanisms.
	* Always '$external' for GSSAPI and MONGODB-X509.
	* This is the database to which the authenticate command will be sent.
	* This is the database to which sasl authentication commands will be sent.
password (string)
	* Does not apply to all mechanisms.
mechanism (string)
	* Indicates which mechanism to use with the credential.
mechanism_properties
	* Includes additional properties for the given mechanism.


Errors
~~~~~~

Drivers SHOULD raise an error as early as possible when detecting invalid values in a credential. For instance, if a ``mechanism_property`` is specified for `MONGODB-CR`_, the driver should raise an error indicating that the property does not apply.


Naming
~~~~~~

Naming of this information MUST be idiomatic to the driver's language/framework but still remain consistent. For instance, python would use "mechanism_properties" and .NET would use "MechanismProperties".

Naming of mechanism properties MUST be case-insensitive. For instance, SERVICE_NAME and service_name refer to the same property.


Authentication
--------------

A MongoClient instance MUST be considered a single logical connection to
the server/deployment.

Socket connections from a MongoClient to deployment members can be one
of two types:

* Monitoring-only socket: multi-threaded drivers maintain monitoring
  sockets separate from sockets in connection pools.

* General-use socket: for multi-threaded drivers, these are sockets in
  connection pools used for (non-monitoring) user operations; in
  single-threaded drivers, these are used for both monitoring and user
  operations.

Authentication (including mechanism negotiation) MUST NOT happen on
monitoring-only sockets.

If one or more credentials are provided to a MongoClient, then whenever
a general-use socket is opened, drivers MUST immediately conduct an
authentication handshake over that socket.

Drivers SHOULD require all credentials to be specified upon construction
of the MongoClient.  This is defined as eager authentication and drivers
MUST support this mode.

Authentication Handshake
~~~~~~~~~~~~~~~~~~~~~~~~

An authentication handshake consists of an initial ``isMaster`` command
possibly followed by one or more authentication conversations.

Drivers MUST follow the following steps for an authentication
handshake:

#. Upon opening a general-use socket to a server for a given
   MongoClient, drivers MUST issue a `MongoDB Handshake
   <../mongodb-handshake/handshake.rst>`_ immediately.  This allows a
   driver to determine the server type.  If the ``isMaster`` of the
   MongoDB Handshake fails with an error, drivers MUST treat this an
   an authentication error.

#  If the server is not of type Standalone, RSPrimary, RSSecondary or
   Mongos, no authentication is possible and the handshake is complete.

#. If credentials exist:

    #. A driver MUST authenticate with all credentials provided to the
           MongoClient.

    #. A single invalid credential is the same as all credentials being
           invalid.

If the authentication handshake fails for a socket, drivers MUST close all
other general-use sockets connected to the same server.

Mechanism Negotiation via Handshake
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:since: 4.0

If an application provides a username but does not provide an
authentication mechanism, drivers MUST negotiate a mechanism via an
``isMaster`` command requesting a user's supported SASL mechanisms::

    {isMaster: 1, saslSupportedMechs: "<dbname>.<username>"}

In this example ``<dbname>`` is the authentication database name (default
'admin') and ``<username>`` is the username provided in the auth credential.
The username MUST NOT be modified from the form provided by the user (i.e.  do
not normalize with SASLprep), as the server uses the raw form to look for
conflicts with legacy credentials.

If the ``isMaster`` command fails with error code 11 (UserNotFound), drivers
must consider authentication to have failed.  In such a case, drivers MUST
raise an error that is equivalent to what they would have raised if the
authentication mechanism were specified and the server responded the same way.

If the ``isMaster`` command succeeds and the response includes a
``saslSupportedMechs`` field, then drivers MUST use the contents of that field
to select a default mechanism as described later.  If the command succeeds and
the response does not include a ``saslSupportedMechs`` field, then drivers MUST
use the legacy default mechanism rules for servers older than 4.0.

Single-credential drivers
`````````````````````````

When the authentication mechanism is not specied, drivers that allow
only a single credential per client MUST perform mechanism negotiation
as part of the MongoDB Handshake portion of the authentication
handshake.  This lets authentication proceed without a separate
negotiation round-trip exchange with the server.

Multi-credential drivers
````````````````````````

The use of multiple credentials within a driver is discouraged, but some
legacy drivers still allow this.  Such drivers may not have user credentials
when connections are opened and thus will not be able to do negotiation.

Drivers with a list of credentials at the time a connection is opened MAY do
mechanism negotiation on the initial handshake, but only for the first
credential in the list of credentials.

When authenticating each credential, if the authentication mechanism is not
specified and has not been negotiated for that credential:

- If the connection handshake results indicate the server version is 4.0 or
  later, drivers MUST send a new ``isMaster`` negotiation command for the
  credential to determine the default authentication mechanism.

- Otherwise, when the server version is earlier than 4.0, the driver MUST
  select a default authentication mechanism for the credential following the
  instructions for when the ``saslSupportedMechs`` field is not present in
  an ``isMaster`` response.

Caching credentials in SCRAM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the implementation of SCRAM authentication mechanisms (e.g. SCRAM-SHA-1
and SCRAM-SHA-2), drivers MUST maintain a cache of computed SCRAM credentials.
The cache entries SHOULD be identified by some combination of the password, 
salt, iteration count, and a value that uniquely identifies the authentication
mechanism (e.g. "SHA1" or "SCRAM-SHA-2").

The cache entry value MUST be either the ``saltedPassword`` parameter or the
combination of the ``clientKey`` and ``serverKey`` parameters.

--------------------------------
Supported Authentication Methods
--------------------------------

Defaults
--------

:since: 3.0
:revised: 4.0

If the user did not provide a mechanism via the connection string or via code,
the following logic describes how to select a default.

If a ``saslSupportedMechs`` field was present in the ``isMaster`` results for
mechanism negotiation, then it MUST be inspected to select a default
mechanism::

    {
        "ismaster" : true,
        "saslSupportedMechs": ["SCRAM-SHA-1", "SCRAM-SHA-256"],
        ...
        "ok" : 1
    }

If SCRAM-SHA-256 is present in the list of mechanism, then it MUST be
used as the default; otherwise, SCRAM-SHA-1 MUST be used as the default,
regardless of whether SCRAM-SHA-1 is in the list.  Drivers MUST NOT
attempt to use any other mechanism (e.g. PLAIN) as the default.

If ``saslSupportedMechs`` is not present in the ``isMaster`` results for
mechanism negotiation, then SCRAM-SHA-1 MUST be used when talking to servers >=
3.0. Prior to server 3.0, MONGODB-CR MUST be used.

When a user has specified a mechanism, regardless of the server version, the
driver MUST honor this and attempt to authenticate.

Determining Server Version
~~~~~~~~~~~~~~~~~~~~~~~~~~

Drivers SHOULD use the server's wire version ranges to determine the server's
version.

MongoDB Custom Mechanisms
-------------------------

MONGODB-CR
~~~~~~~~~~

:since: 1.4
:deprecated: 3.0
:removed: 4.0

MongoDB Challenge Response is a nonce and MD5 based system. The driver sends a `getNonce` command, encodes and hashes the password using the returned nonce, and then sends an `authenticate` command.

Conversation
````````````

#. Send ``getNonce`` command
	* :javascript:`{ getNonce: 1 }`
	* Response: :javascript:`{ nonce: <nonce> }`
#. Compute key
	* :javascript:`passwordDigest = HEX( MD5( UTF8( username + ':mongo:' + password )))`
	* :javascript:`key = HEX( MD5( UTF8( nonce + username + passwordDigest )))`
#. Send ``authenticate`` command
	* :javascript:`{ authenticate: 1, nonce: nonce, user: username, key: key }`

As an example, given a username of "user" and a password of "pencil", the conversation would appear as follows:

| C: :javascript:`{getnonce : 1}`
| S: :javascript:`{nonce: "2375531c32080ae8", ok: 1}`
| C: :javascript:`{authenticate: 1, user: "user", nonce: "2375531c32080ae8", key: "21742f26431831d5cfca035a08c5bdf6"}`
| S: :javascript:`{ok: 1}`

`MongoCredential`_ Properties
`````````````````````````````

username
	MUST be specified.

source
	MUST be specified. Defaults to the database name if supplied on the connection string or ``admin``.

password
	MUST be specified.

mechanism
	MUST be "MONGODB-CR"

mechanism_properties
	MUST NOT be specified.


MONGODB-X509
~~~~~~~~~~~~

:since: 2.6
:changed: 3.4


MONGODB-X509 is the usage of X.509 certificates to validate a client where the
distinguished subject name of the client certificate acts as the username.

When connected to MongoDB 3.4:
  * You MUST NOT raise an error when the application only provides an X.509 certificate and no username.
  * If the application does not provide a username you MUST NOT send a username to the server.
  * If the application provides a username you MUST send that username to the server.
When connected to MongoDB 3.2 or earlier:
  * You MUST send a username to the server.
  * If no username is provided by the application, you MAY extract the username from the X.509 certificate instead of requiring the application to provide it.
  * If you choose not to automatically extract the username from the certificate you MUST error when no username is provided by the application.


Conversation
````````````

#. Send ``authenticate`` command (MongoDB 3.4+)
	* C: :javascript:`{"authenticate": 1, "mechanism": "MONGODB-X509"}`
	* S: :javascript:`{"dbname" : "$external", "user" : "C=IS,ST=Reykjavik,L=Reykjavik,O=MongoDB,OU=Drivers,CN=client", "ok" : 1}`

#. Send ``authenticate`` command with username:
	* ``username = openssl x509 -subject -nameopt RFC2253 -noout -inform PEM -in my-cert.pem``
	* C: :javascript:`{authenticate: 1, mechanism: "MONGODB-X509", user: "C=IS,ST=Reykjavik,L=Reykjavik,O=MongoDB,OU=Drivers,CN=client"}`
	* S: :javascript:`{"dbname" : "$external", "user" : "C=IS,ST=Reykjavik,L=Reykjavik,O=MongoDB,OU=Drivers,CN=client", "ok" : 1}`


`MongoCredential`_ Properties
`````````````````````````````

username
	SHOULD NOT be provided for MongoDB 3.4+
	MUST be specified for MongoDB prior to 3.4

source
	MUST be "$external". Defaults to ``$external``.

password
	MUST NOT be specified.

mechanism
	MUST be "MONGODB-X509"

mechanism_properties
	MUST NOT be specified.


TODO: Errors


SASL Mechanisms
---------------

:since: 2.4 enterprise

SASL mechanisms are all implemented using the same sasl commands and interpreted as defined by the `SASL specification RFC 4422 <http://tools.ietf.org/html/rfc4422>`_.

#. Send the `saslStart` command.
	* :javascript:`{ saslStart: 1, mechanism: <mechanism_name>, payload: BinData(...), autoAuthorize: 1 }`
	* Response: :javascript:`{ conversationId: <number>, code: <code>, done: <boolean>, payload: <payload> }`
		- conversationId: the conversation identifier. This will need to be remembered and used for the duration of the conversation.
		- code: A response code that will indicate failure. This field is not included when the command was successful.
		- done: a boolean value indicating whether or not the conversation has completed.
		- payload: a sequence of bytes or a base64 encoded string (depending on input) to pass into the SASL library to transition the state machine.
#. Continue with the `saslContinue` command while `done` is `false`.
	* :javascript:`{ saslContinue: 1, conversationId: conversationId, payload: BinData(...) }`
	* Response is the same as that of `saslStart`


Many languages will have the ability to utilize 3rd party libraries. The server uses `cyrus-sasl <http://www.cyrusimap.org/docs/cyrus-sasl/2.1.25/>`_ and it would make sense for drivers with a choice to also choose cyrus. However, it is important to ensure that when utilizing a 3rd party library it does implement the mechanism on all supported OS versions and that it interoperates with the server. For instance, the cyrus sasl library offered on RHEL 6 does not implement SCRAM-SHA-1. As such, if your driver supports RHEL 6, you'll need to implement SCRAM-SHA-1 from scratch.


GSSAPI
~~~~~~

:since: 
	2.4 enterprise

	2.6 enterprise on windows

GSSAPI is kerberos authentication as defined in `RFC 4752 <http://tools.ietf.org/html/rfc4752>`_. Microsoft has a proprietary implementation called SSPI which is compatible with both windows and linux clients.

`MongoCredential`_ properties:

username
	MUST be specified.

source
	MUST be "$external". Defaults to ``$external``.

password
	MAY be specified.

mechanism
	MUST be "GSSAPI"

mechanism_properties
	SERVICE_NAME
		Drivers MUST allow the user to specify a different service name. The default is "mongodb".

	CANONICALIZE_HOST_NAME
		Drivers MAY allow the user to request canonicalization of the hostname. This might be required when the hosts report different hostnames than what is used in the kerberos database. The default is "false".

	SERVICE_REALM
		Drivers MAY allow the user to specify a different realm for the service. This might be necessary to support cross-realm authentication where the user exists in one realm and the service in another.

Hostname Canonicalization
`````````````````````````

If CANONICALIZE_HOST_NAME is true, the client MUST canonicalize the name of each host it uses for authentication. There are two options. First, if the client's underlying GSSAPI library provides hostname canonicalization, the client MAY rely on it. For example, MIT Kerberos has `a configuration option for canonicalization <https://web.mit.edu/kerberos/krb5-1.13/doc/admin/princ_dns.html#service-principal-canonicalization>`_.

Second, the client MAY implement its own canonicalization. If so, the canonicalization algorithm MUST be::

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

  reversed = do a reverse DNS lookup for address
  if reversed:
    canonicalized = lowercase(reversed)
  else:
    canonicalized = lowercase(host)

For example, here is a Python implementation of this algorithm using ``getaddrinfo`` (for address and CNAME resolution) and ``getnameinfo`` (for reverse DNS).

.. code-block:: python

  from socket import *
  import sys


  def canonicalize(host):
      # Get a CNAME for host, if any.
      af, socktype, proto, canonname, sockaddr = getaddrinfo(
          host, None, 0, 0, IPPROTO_TCP, AI_CANONNAME)[0]

      print('address from getaddrinfo: [%s]' % (sockaddr[0],))
      print('canonical name from getaddrinfo: [%s]' % (canonname,))

      try:
          # NI_NAMEREQD requests an error if getnameinfo fails.
          name = getnameinfo(sockaddr, NI_NAMEREQD)
      except gaierror as exc:
          print('getname info failed: "%s"' % (exc,))
          return canonname.lower()

      return name[0].lower()


  canonicalized = canonicalize(sys.argv[1])
  print('canonicalized: [%s]' % (canonicalized,))

Beware of a bug in older glibc where ``getaddrinfo`` uses PTR records instead of CNAMEs if the address family hint is AF_INET6, and beware of a bug in older MIT Kerberos that causes it to always do reverse DNS lookup even if the ``rdns`` configuration option is set to ``false``.

PLAIN
~~~~~

:since: 2.6 enterprise

The PLAIN mechanism, as defined in `RFC 4616 <http://tools.ietf.org/html/rfc4616>`_, is used in MongoDB to perform LDAP authentication. It cannot be used to perform any other type of authentication. Since the credentials are stored outside of MongoDB, the `$external` database must be used for authentication.

Conversation
````````````

As an example, given a username of "user" and a password of "pencil", the conversation would appear as follows:

| C: :javascript:`{saslStart: 1, mechanism: "PLAIN", payload: BinData(0, "AHVzZXIAcGVuY2ls")}`
| S: :javascript:`{conversationId: 1, payload: BinData(0,""), done: true, ok: 1}`

If your sasl client is also sending the authzid, it would be "user" and the conversation would appear as follows:

| C: :javascript:`{saslStart: 1, mechanism: "PLAIN", payload: BinData(0, "dXNlcgB1c2VyAHBlbmNpbA==")}`
| S: :javascript:`{conversationId: 1, payload: BinData(0,""), done: true, ok: 1}`

MongoDB supports either of these forms.

`MongoCredential`_ Properties
`````````````````````````````

username
	MUST be specified.

source
	MUST be specified. Defaults to the database name if supplied on the connection string or ``$external``.

password
	MUST be specified.

mechanism
	MUST be "PLAIN"

mechanism_properties
	MUST NOT be specified.


SCRAM-SHA-1
~~~~~~~~~~~

:since: 3.0

SCRAM-SHA-1 is defined in `RFC 5802 <http://tools.ietf.org/html/rfc5802>`_.

`Page 11 of the RFC <http://tools.ietf.org/html/rfc5802#page-11>`_ specifies
that user names be prepared with SASLprep, but drivers MUST NOT do so.

`Page 8 of the RFC <http://tools.ietf.org/html/rfc5802#page-8>`_ identifies the
"SaltedPassword" as ``:= Hi(Normalize(password), salt, i)``. The ``password``
variable MUST be the mongodb hashed variant. The mongo hashed variant is
computed as :javascript:`hash = HEX( MD5( UTF8( username + ':mongo:' +
plain_text_password )))`, where ``plain_text_password`` is actually plain text.
The ``username`` and ``password`` MUST NOT be prepared with SASLprep before
hashing.

For example, to compute the ClientKey according to the RFC:

.. code:: javascript

	// note that "salt" and "i" have been provided by the server
	function computeClientKey(username, plain_text_password) {
		mongo_hashed_password = HEX( MD5( UTF8( username + ':mongo:' + plain_text_password )));
		saltedPassword  = Hi(Normalize(mongo_hashed_password), salt, i);
		clientKey = HMAC(saltedPassword, "Client Key");
	}

In addition, SCRAM-SHA-1 requires that a client create a randomly generated
nonce. It is imperative, for security sake, that this be as secure and truly
random as possible. For instance, Java provides both a Random class as well as
a SecureRandom class. SecureRandom is cryptographically generated while Random
is just a pseudo-random generator with predictable outcomes.

Additionally, drivers MUST enforce a minimum iteration count of 4096 and MUST
error if the authentication conversation specifies a lower count.  This
mitigates downgrade attacks by a man-in-the-middle attacker.

Drivers MUST NOT advertise support for channel binding, as the server does
not support it and legacy servers may fail authentication if drivers advertise
support. I.e. the client-first-message MUST start with ``n,``.

Conversation
````````````

As an example, given a username of "user" and a password of "pencil" and an r
value of "fyko+d2lbbFgONRv9qkxdawL", a SCRAM-SHA-1 conversation would appear as
follows:

| C: ``n,,n=user,r=fyko+d2lbbFgONRv9qkxdawL``
| S: ``r=fyko+d2lbbFgONRv9qkxdawLHo+Vgk7qvUOKUwuWLIWg4l/9SraGMHEE,s=rQ9ZY3MntBeuP3E1TDVC4w==,i=10000``
| C: ``c=biws,r=fyko+d2lbbFgONRv9qkxdawLHo+Vgk7qvUOKUwuWLIWg4l/9SraGMHEE,p=MC2T8BvbmWRckDw8oWl5IVghwCY=``
| S: ``v=UMWeI25JD1yNYZRMpZ4VHvhZ9e0=``

This same conversation over mongodb's sasl implementation would appear as follows:

| C: :javascript:`{saslStart: 1, mechanism: "SCRAM-SHA-1", payload: BinData(0, "biwsbj11c2VyLHI9ZnlrbytkMmxiYkZnT05Sdjlxa3hkYXdM")}`
| S: :javascript:`{conversationId : 1, payload: BinData(0,"cj1meWtvK2QybGJiRmdPTlJ2OXFreGRhd0xIbytWZ2s3cXZVT0tVd3VXTElXZzRsLzlTcmFHTUhFRSxzPXJROVpZM01udEJldVAzRTFURFZDNHc9PSxpPTEwMDAw"), done: false, ok: 1}`
| C: :javascript:`{saslContinue: 1, conversationId: 1, payload: BinData(0, "Yz1iaXdzLHI9ZnlrbytkMmxiYkZnT05Sdjlxa3hkYXdMSG8rVmdrN3F2VU9LVXd1V0xJV2c0bC85U3JhR01IRUUscD1NQzJUOEJ2Ym1XUmNrRHc4b1dsNUlWZ2h3Q1k9")}`
| S: :javascript:`{conversationId: 1, payload: BinData(0,"dj1VTVdlSTI1SkQxeU5ZWlJNcFo0Vkh2aFo5ZTA9"), done: false, ok: 1}`
| C: :javascript:`{saslContinue: 1, conversationId: 1, payload: BinData(0, "")}`
| S: :javascript:`{conversationId: 1, payload: BinData(0,""), done: true, ok: 1}`

.. note::

	There is an extra round trip due to an implementation decision on the server. This is accomplished by sending no bytes back to the server for what is effectively a no-op.

`MongoCredential`_ Properties
`````````````````````````````

username
	MUST be specified.

source
	MUST be specified. Defaults to the database name if supplied on the connection string or ``admin``.

password
	MUST be specified. 

mechanism
	MUST be "SCRAM-SHA-1"

mechanism_properties
	MUST NOT be specified.

SCRAM-SHA-256
~~~~~~~~~~~~~

:since: 4.0

SCRAM-SHA-256 extends `RFC 5802 <http://tools.ietf.org/html/rfc5802>`_ and
is formally defined in `RFC 7677 <https://tools.ietf.org/html/rfc7677>`_.

The MongoDB SCRAM-SHA-256 mechanism works similarly to the SCRAM-SHA-1
mechanism, with the following changes:

- The SCRAM algorithm MUST use SHA-256 as the hash function instead of SHA-1.
- User names MUST NOT be prepared with SASLprep.  This intentionally
  contravenes the "SHOULD" provision of RFC 5802.
- Passwords MUST be prepared with SASLprep, per RFC 5802.  Passwords are
  used directly for key derivation ; they MUST NOT be digested as they are in
  SCRAM-SHA-1.

Additionally, drivers MUST enforce a minimum iteration count of 4096 and MUST
error if the authentication conversation specifies a lower count.  This
mitigates downgrade attacks by a man-in-the-middle attacker.

Conversation
````````````

As an example, given a username of "user" and a password of "pencil" and an r
value of "rOprNGfwEbeRWgbNEkqO", a SCRAM-SHA-256 conversation would appear as
follows:

| C: ``n,,n=user,r=rOprNGfwEbeRWgbNEkqO``
| S: ``r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,s=W22ZaJ0SNY7soEsUEjb6gQ==,i=4096``
| C: ``c=biws,r=rOprNGfwEbeRWgbNEkqO%hvYDpWUa2RaTCAfuxFIlj)hNlF$k0,p=dHzbZapWIk4jUhN+Ute9ytag9zjfMHgsqmmiz7AndVQ=``
| S: ``v=6rriTRBi23WpRR/wtup+mMhUZUn/dB5nLTJRsjl95G4=``

`MongoCredential`_ Properties
`````````````````````````````

username
	MUST be specified.

source
	MUST be specified. Defaults to the database name if supplied on the connection string or ``admin``.

password
	MUST be specified.

mechanism
	MUST be "SCRAM-SHA-256"

mechanism_properties
	MUST NOT be specified.

Caching credentials
`````````````````````

Drivers MUST maintain a cache of computed SCRAM credentials, where each cache
entry's key is the tuple of ``(mongo_hashed_password, salt, i)``. Drivers SHOULD
also include the name of the authentication mechanism, i.e. "SCRAM-SHA-256", as
part of the key; this allows a single cache to be used for all current and 
future SCRAM authentication mechanisms that drivers may implement.

The cache entry value MUST be either the ``saltedPassword`` parameter, the
combination of the ``clientKey`` and ``serverKey`` parameters, or the ``storedKey``
result.

-------------------------
Connection String Options
-------------------------

``mongodb://[username[:password]@]host1[:port1][,[host2:[port2]],...[hostN:[portN]]][/database][?options]``


Auth Related Options
--------------------

authMechanism
	MONGODB-CR, MONGODB-X509, GSSAPI, PLAIN, SCRAM-SHA-1, SCRAM-SHA-256

	Sets the Mechanism property on the MongoCredential. When not set, the default will be one of SCRAM-SHA-256, SCRAM-SHA-1 or MONGODB-CR, following the auth spec default mechanism rules.

authSource
	Sets the Source property on the MongoCredential.

	For GSSAPI and MONGODB-X509 authMechanisms the authSource defaults to ``$external``.
	For PLAIN the authSource defaults to the database name if supplied on the connection string or ``$external``.
	For MONGODB-CR, SCRAM-SHA-1 and SCRAM-SHA-256 authMechanisms, the authSource defaults to the database name if supplied on the connection string or ``admin``.

authMechanismProperties=PROPERTY_NAME:PROPERTY_VALUE,PROPERTY_NAME2:PROPERTY_VALUE2
	A generic method to set mechanism properties in the connection string. 

	For example, to set REALM and CANONICALIZE_HOST_NAME, the option would be ``authMechanismProperties=CANONICALIZE_HOST_NAME:true,SERVICE_REALM:AWESOME``.

gssapiServiceName (deprecated)
	An alias for ``authMechanismProperties=SERVICE_NAME:mongodb``.


Implementation
--------------

#. Credentials MAY be specified in the connection string immediately after the scheme separator "//".
#. A realm MAY be passed as a part of the username in the url. It would be something like dev@MONGODB.COM, where dev is the username and MONGODB.COM is the realm. Per the RFC, the @ symbol should be url encoded using %40.
	* When GSSAPI is specified, this should be interpretted as the realm.
	* When non-GSSAPI is specified, this should be interpetted as part of the username.
#. It is permissible for only the username to appear in the connection string. This would be identified by having no colon follow the username before the '@' hostname separator.
#. The source is determined by the following:
	* if authSource is specified, it is used.
	* otherwise, if database is specified, it is used.
	* otherwise, the admin database is used.


Test Plan
=========

Connection string tests have been defined in the associated files:

* `Connection String <tests/connection-string.json>`_.

---------------------------------------
SCRAM-SHA-256 and mechanism negotiation
---------------------------------------

Testing SCRAM-SHA-256 requires server version 3.7.3 or later with
``featureCompatibilityVersion`` of "4.0" or later.

Drivers that allow specifying auth parameters in code as well as via
connection string should test both for the test cases described below.

Step 1
------

Create three test users, one with only SHA-1, one with only SHA-256 and one
with both.  For example::

    db.runCommand({createUser: 'sha1', pwd: 'sha1', roles: ['root'], mechanisms: ['SCRAM-SHA-1']})
    db.runCommand({createUser: 'sha256', pwd: 'sha256', roles: ['root'], mechanisms: ['SCRAM-SHA-256']})
    db.runCommand({createUser: 'both', pwd: 'both', roles: ['root'], mechanisms: ['SCRAM-SHA-1', 'SCRAM-SHA-256']})

Step 2
------

For each test user, verify that you can connect and run a command requiring
authentication for the following cases:

- Explicitly specifying each mechanism the user supports.
- Specifying no mechanism and relying on mechanism negotiation.

For the example users above, the ``dbstats`` command could be used as a test
command.

For a test user supporting both SCRAM-SHA-1 and SCRAM-SHA-256, drivers should
verify that negotation selects SCRAM-SHA-256.  This may require monkey
patching, manual log analysis, etc.

Step 3
------

For test users that support only one mechanism, verify that explictly specifying
the other mechanism fails.

For a non-existent username, verify that not specifying a mechanism when
connecting fails with the same error type that would occur with a correct
username but incorrect password or mechanism.  (Because negotiation with a
non-existent user name causes an isMaster error, we want to verify this is
seen by users as similar to other authentication errors, not as a network or
database command error.)


Step 4
------

To test SASLprep behavior, create two users:

#. username: "IX", password "IX"
#. username: "\u2168" (ROMAN NUMERAL NINE), password "\u2163" (ROMAN NUMERAL FOUR)

To create the users, use the exact bytes for username and password without
SASLprep or other normalization and specify SCRAM-SHA-256 credentials:

    db.runCommand({createUser: 'IX', pwd: 'IX', roles: ['root'], mechanisms: ['SCRAM-SHA-256']})
    db.runCommand({createUser: '\u2168', pwd: '\u2163', roles: ['root'], mechanisms: ['SCRAM-SHA-256']})

For each user, verify that the driver can authenticate with the password in
both SASLprep normalized and non-normalized forms:

- User "IX": use password forms "IX" and "I\u00ADX"
- User "\u2168": use password forms "IV" and "I\u00ADV"

As a URI, those have to be UTF-8 encoded and URL-escaped, e.g.:

- mongodb://IX:IX@mongodb.example.com/admin
- mongodb://IX:I%C2%ADX@mongodb.example.com/admin
- mongodb://%E2%85%A8:IV@mongodb.example.com/admin
- mongodb://%E2%85%A8:I%C2%ADV@mongodb.example.com/admin

-----------------------
Minimum iteration count
-----------------------

For SCRAM-SHA-1 and SCRAM-SHA-256, test that the minimum iteration count
is respected.  This may be done via unit testing of an underlying SCRAM
library.

Backwards Compatibility
=======================

Drivers may need to remove support for association of more than one credential with a MongoClient, including

	* Deprecation and removal of MongoClient constructors that take as an argument more than a single credential
	* Deprecation and removal of methods that allow lazy authentication (i.e post-MongoClient construction)

Reference Implementation
========================

The Java and .NET drivers currently uses eager authentication and abide by this specification.

Q & A
=====

Q: According to `Authentication Handshake`_, we are calling isMaster for every socket. Isn't this a lot?
	Drivers should be pooling connections and, as such, new sockets getting opened should be relatively infrequent. It's simply part of the protocol for setting up a socket to be used.

Q: Where is information related to user management?
	Not here currently. Should it be? This is about authentication, not user management. Perhaps a new spec is necessary.

Q: It's possible to continue using authenticated sockets even if new sockets fail authentication. Why can't we do that so that applications continue to work.
	Yes, that's technically true. The issue with doing that is for drivers using connection pooling. An application would function normally until an operation needed an additional connection(s) during a spike. Each new connection would fail to authenticate causing intermittent failures that would be very difficult to understand for a user.

Q: Should a driver support multiple credentials?
    No. 

    Historically, the MongoDB server and drivers have supported multiple credentials, one per authSource, on a single connection.  It was necessary because early versions of MongoDB allowed a user to be granted privileges 
    to access the database in which the user was defined (or all databases in the special case of the "admin" database).  But with the introduction of role-based access control in MongoDB 2.6, that restriction was 
    removed and it became possible to create applications that access multiple databases with a single authenticated user.

    Role-based access control also introduces the potential for accidental privilege escalation.  An application may, for example, authenticate user A from authSource X, and user B from authSource Y, thinking that 
    user A has privileges only on collections in X and user B has privileges only on collections in Y.  But with role-based access control that restriction no longer exists, and it's possible that user B has, for example,
    more privileges on collections in X than user A does.  Due to this risk it's generally safer to create a single user with only the privileges required for a given application, and authenticate only that one user
    in the application.

    In addition, since only a single credential is supported per authSource, certain mechanisms are restricted to a single credential and some credentials cannot be used in conjunction (GSSAPI and X509 both use the "$external" database). 

    Finally, MongoDB 3.6 introduces sessions, and allows at most a single authenticated user on any connection which makes use of one. Therefore any application that requires multiple authenticated users will not be able to make use of any feature that builds on sessions (e.g. retryable writes).  
    
    Drivers should therefore guide application creators in the right direction by supporting the association of at most one credential with a MongoClient instance. 

Q: Should a driver support lazy authentication?
    No, for the same reasons as given in the previous section, as lazy authentication is another mechanism for allowing multiple credentials to be associated with a single MongoClient instance.

Q: Why does SCRAM sometimes SASLprep and sometimes not?
    When MongoDB implemented SCRAM-SHA-1, it required drivers to *NOT* SASLprep
    usernames and passwords.  The primary reason for this was to allow a smooth
    upgrade path from MongoDB-CR using existing usernames and passwords.
    Also, because MongoDB's SCRAM-SHA-1 passwords are hex characters of a digest,
    SASLprep of passwords was irrelevant.

    With the introduction of SCRAM-SHA-256, MongoDB requires users to
    explicitly create new SCRAM-SHA-256 credentials distinct from those used
    for MONGODB-CR and SCRAM-SHA-1.  This means SCRAM-SHA-256 passwords are not
    digested and any Unicode character could now appear in a password.
    Therefore, the SCRAM-SHA-256 mechanism requires passwords to be normalized
    with SASLprep, in accordance with the SCRAM RFC.

    However, usernames must be unique, which creates a similar upgrade path
    problem.  SASLprep maps multiple byte representations to a single
    normalized one.  An existing database could have multiple existing users
    that map to the same SASLprep form, which makes it impossible to find the
    correct user document for SCRAM authentication given only a SASLprep
    username.  After considering various options to address or workaround this
    problem, MongoDB decided that the best user experience on upgrade and
    lowest technical risk of implementation is to require drivers to continue
    to not SASLprep usernames in SCRAM-SHA-256.

Version History
===============

Version 1.7 Changes
    * Clarify authSource defaults
    * Fix PLAIN authSource rule to allow user provided values

Version 1.6 Changes
    * Change SCRAM-SHA-256 rules such that usernames are *NOT* normalized;
      this follows a change in the server design and should be available in
      server 4.0-rc0.

Version 1.5 Changes
    * Clarify auth handshake and that it only applies to non-monitoring
      sockets.

Version 1.4.1 Changes
    * Describe CANONICALIZE_HOST_NAME algorithm.

Version 1.4 Changes
	* Added SCRAM-SHA-256 and mechanism negotiation as provided by server 4.0
	* Updated default mechanism determination
	* Clarified SCRAM-SHA-1 rules around SASLprep
	* Require SCRAM-SHA-1 and SCRAM-SHA-256 to enforce a minimum iteration count

Version 1.3 Changes
	* Updated minimum server version to 2.6
	* Updated the Q & A to recommend support for at most a single credential per MongoClient
	* Removed lazy authentication section
	* Changed the list of server types requiring authentication
	* Made providing username for X509 authentication optional

Version 1.2 Changes
	* Added SCRAM-SHA-1 sasl mechanism
	* Added `Connection Handshake`_
	* Changed connection string to support mechanism properties in generic form
	* Added example conversations for all mechanisms except GSSAPI
	* Miscellaneous wording changes for clarification

Version 1.1 Changes
	* Added MONGODB-X509
	* Added PLAIN sasl mechanism
	* Added support for GSSAPI mechanism property gssapiServiceName
