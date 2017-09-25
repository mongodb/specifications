.. role:: javascript(code)
  :language: javascript

=====================
Driver Authentication
=====================

:Spec: 100
:Title: Driver Authentication
:Author: Craig Wilson
:Advisors: Andy Schwerin, Bernie Hacket, Jeff Yemin, David Golden
:Status: Accepted
:Type: Standards
:Minimum Server Version: 1.8
:Last Modified: 2017-08-23

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
	* Always '$external' for GSSAPI, MONGODB-X509, and PLAIN.
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

This section augments the `Server Discovery and Monitoring Spec <../server-discovery-and-monitoring/server-discovery-and-monitoring.rst>`_.

A MongoClient instance MUST be considered a single logical connection to the server/deployment. Hence, all credentials given to an instance of a MongoClient should apply to every currently opened socket. Drivers SHOULD require all credentials to be specified upon construction of the MongoClient. This is defined as eager authentication and drivers MUST support this mode.


Connection Handshake
~~~~~~~~~~~~~~~~~~~~

Drivers MUST consider a server ``Unknown`` if authentication fails. Effectively, an authentication failure is equivalent to a network or socket error in that we have failed to establish a connection with the server. The steps to support this are below:

#. If credentials exist
	#. Upon opening a socket, drivers MUST issue `MongoDB Handshake <../mongodb-handshake/handshake.rst>`_ immediately. This allows a driver to determine whether the server is an Arbiter.
	#. A driver MUST perform authentication with all supplied credentials for all server types with the exception of RSArbiter.
	#. A single invalid credential is the same as all credentials being invalid.


Lazy Authentication
~~~~~~~~~~~~~~~~~~~

Some drivers need to support lazy authentication for backwards compatibility. A credential cache MUST be employed to handle authentication within a MongoClient. When a user has requested authentication against a particular database, those credentials MUST be remembered. When a new socket is created, all the existing authentications MUST be applied to the new socket. In addition, when an existing socket is checked out, any authentications that have taken place since its last use MUST also be applied. Should a user request authentication with different credentials against a database that already exists in the credential cache, an error MUST be raised.

.. code:: python

	db = client.getDB("foo")
 
	## this will send the authentication against the "foo" database
	db.auth(user: "user1", password: "password")

	## this should NOT raise an error because the credential is the same against the "foo" database
	db.auth(user: "user1", password: "password")

	## this should raise an error as the credential is different
	db.auth(user: "user2", password: "password")
	 
	## this should also raise an error even though the "db" instance we are working with is not
	## the "foo" database, "foo" is the database the authentication should be tested against.
	db = client.getDB("bar")
	db.auth(user: "user2", password: "password", source: "foo")

	## logout allows the user to log in to a database with a different credential
	db = db.client.getDB("foo");
	db.logout();
	db.auth(user: "user2", password: "password")

In addition, drivers supporting lazy authentication may need to support logout as well. In practice, it works exactly the opposite of authenticate. When logout is called, those credentials MUST be forgotten. When an existing socket is checked out, any forgotten credential must be de-authenticated on that socket.

If the initial authentication fails, an error SHOULD be raised and the credentials SHOULD NOT be added to the credential cache. However, when authentication fails using credentials from the credential cache, all open connections MUST be closed and the server type set to ``Unknown``.


--------------------------------
Supported Authentication Methods
--------------------------------

Defaults
--------

:since: 3.0

If the user did not provide a mechanism via the connection string or via code, SCRAM-SHA-1 MUST be used when talking to servers >= 3.0. Prior to server 3.0, MONGODB-CR MUST be used.

When a user has specified a mechanism, regardless of the server version, the driver MUST honor this and attempt to authenticate.

Determining Server Version
~~~~~~~~~~~~~~~~~~~~~~~~~~

Some drivers use the ``buildinfo`` command to determine server version. Occasionally, it might be enough to check the wire version. Checking the wire version is only possible when the server has bumped it in accordance with what needs to be checked.

For instance, checking the wire version to determine whether or not the server supports SCRAM-SHA-1 is only possible if the server bumps the wire version when they release server 3.0.


MongoDB Custom Mechanisms
-------------------------

MONGODB-CR
~~~~~~~~~~

:since: 1.4
:deprecated: 3.0

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
	MUST be specified.

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
	MUST be $external.

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
	MUST be "$external"

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
	MUST be $external.

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

`Page 8 of the RFC <http://tools.ietf.org/html/rfc5802#page-8>`_ identifies the "SaltedPassword" as ``:= Hi(Normalize(password), salt, i)``. The ``password`` variable MUST be the mongodb hashed variant. The mongo hashed variant is computed as :javascript:`hash = HEX( MD5( UTF8( username + ':mongo:' + plain_text_password )))`, where ``plain_text_password`` is actually plain text. For example, to compute the ClientKey according to the RFC:

.. code:: javascript

	// note that "salt" and "i" have been provided by the server
	function computeClientKey(username, plain_text_password) {
		mongo_hashed_password = HEX( MD5( UTF8( username + ':mongo:' + plain_text_password )));
		saltedPassword  = Hi(Normalize(mongo_hashed_password), salt, i);
		clientKey = HMAC(saltedPassword, "Client Key");
	}

In addition, SCRAM-SHA-1 requires that a client create a randomly generated nonce. It is imperative, for security sake, that this be as secure and truly random as possible. For instance, java provides both a Random class as well as a SecureRandom class. SecureRandom is cryptographically generated while Random is just a pseudo-random generator with predictable outcomes.


Conversation
````````````

As an example, given a username of "user" and a password of "pencil" and an r value of "fyko+d2lbbFgONRv9qkxdawL", the scram conversation would appear as follows:

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
	MUST be specified.

password
	MUST be specified. 

mechanism
	MUST be "SCRAM-SHA-1"

mechanism_properties
	MUST NOT be specified.


-------------------------
Connection String Options
-------------------------

``mongodb://[username[:password]@]host1[:port1][,[host2:[port2]],...[hostN:[portN]]][/database][?options]``


Auth Related Options
--------------------

authMechanism
	MONGODB-CR, MONGODB-X509, GSSAPI, PLAIN, SCRAM-SHA-1

	Sets the Mechanism property on the MongoCredential. The default is MONGODB-CR if <= 2.6, otherwise SCRAM-SHA-1.

authSource
	Sets the Source property on the MongoCredential. This overrides the database name on the connection string for where authentication occurs. The default is admin.

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

Tests have been defined in the associated files:

* `Connection String <tests/connection-string.json>`_.


Backwards Compatibility
=======================

There should be no backwards compatibility concerns. Drivers currently supporting late-bound authentication only should be able to migrate to eager authentication while still allowing lazy authentication.


Reference Implementation
========================

The .NET driver currently uses eager authentication and abides by this specification. The Java driver abides by this specification and uses a mix of eager and lazy authentication.

Q & A
=====

Q: According to `Connection Handshake`_, we are calling isMaster for every socket. Isn't this a lot?
	Drivers should be pooling connections and, as such, new sockets getting opened should be relatively infrequent. It's simply part of the protocol for setting up a socket to be used.

Q: Where is information related to user management?
	Not here currently. Should it be? This is about authentication, not user management. Perhaps a new spec is necessary.

Q: I've heard ``isMaster`` will require authentication in the future. Should we consider that here?
	Not right now. We don't know what the future looks like yet and, as such, any preparation would be a guess. This spec will be augmented when the server changes connection protocols.

Q: It's possible to continue using authenticated sockets even if new sockets fail authentication. Why can't we do that so that applications continue to work.
	Yes, that's technically true. The issue with doing that is for drivers using connection pooling. An application would function normally until an operation needed an additional connection(s) during a spike. Each new connection would fail to authenticate causing intermittent failures that would be very difficult to understand for a user.

Q: Should a driver support multiple credentials?
    The server supports multiple credentials. If a driver wants to support all of the server, then it needs to support multiple credentials. However, since multiple authentications are not supported against a single database, certain mechanisms are restricted to a single credential and some credentials cannot be used in conjunction (GSSAPI and X509 both use the $external database). 


Version History
===============

2017-08-23: Changed the list of server types requiring authentication.

2016-11-01: Made providing username for X509 authentication optional.

2016-08-17: Added FAQ regarding multiple credentials.

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
