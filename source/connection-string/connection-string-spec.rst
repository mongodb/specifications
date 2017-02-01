.. role:: javascript(code)
  :language: javascript

======================
Connection String Spec
======================

:Spec: 104
:Title: Connection String Spec
:Authors: Ross Lawley
:Advisors: \A. Jesse Jiryu Davis, Jeremy Mikola, Anna Herlihy
:Status: Approved
:Type: Standards
:Last Modified: Jan. 09, 2017
:Version: 1.1

.. contents::

--------

Abstract
========

The purpose of the Connection String is to provide a machine readable way of configuring a MongoClient, allowing users to configure and change the connection to their MongoDB system without requiring any application code changes.

This specification defines how the connection string is constructed and parsed. The aim is not to list all of connection string options and their semantics. Rather it defines the syntax of the connection string, including rules for parsing, naming conventions for options, and standard data types.

It should be noted that while the connection string specification is inspired by the URI specification as described in `RFC 3986 <http://tools.ietf.org/html/rfc3986>`_  and uses similar terminology, it does not conform to that specification.

-----------
Definitions
-----------

META
----

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

--------------
General Syntax
--------------

In general we follow URI style conventions, however unlike a URI the
connection string supports multiple hosts.

.. code:: prettyprint

  mongodb://username:password@example.com:27017,example2.com:27017,...,example.comN:27017/database?key=value&keyN=valueN
  \_____/   \_______________/ \_________/ \__/  \_______________________________________/ \______/ \_/ \___/
    |             |             |           |                    |                          |       |    |
  Scheme          |            Host        Port        Alternative host identifiers         |      Key Value
               Userinfo       \_____________/                                               |      \_______/
                                     |                                              Auth database      |
                                Host Identifier                                                    Key Value Pair
                               \_______________________________________________________/          \___________________/
                                                        |                                                   |
                                                   Host Information                                  Connection Options


------
Scheme
------
The scheme mongodb represents that this is a connection string for a MongoClient.

-------------------
Userinfo (optional)
-------------------
The user information if present, is followed by a commercial at-sign ("@") that delimits it from the host.

A password may be supplied as part of the user information and is anything after the first colon (":") up until the end of the user information.

If the username, or password section contains a percent sign ("%"), an at-sign ("@") or a colon (":") it MUST be URL encoded.

If the user information contains a percent sign ("%"), an at-sign ("@") or more than one colon (":") then an exception MUST be thrown informing the user that the username and password must be URL encoded.

----------------
Host Information
----------------
Unlike a standard URI, the connection string allows for identifying multiple hosts. The host information section of the connection string is delimited by the trailing slash ("/") or end of string.

The host information must contain at least one host identifier but may contain more (see the alternative hosts / ports in the general syntax diagram above). Multiple host identifiers are delimited by a comma (",").

Host Identifier
---------------
A host identifier consists of a host and an optional port.

Host
~~~~
Identifies a server address to connect to. It can identify either a hostname, IP address, IP Literal, or UNIX domain socket. For definitions of hostname, IP address and IP Literal formats see `RFC 3986 <http://tools.ietf.org/html/rfc3986#section-3.2.2>`_ .

UNIX domain sockets MUST end in ".sock" and MUST be URL encoded, for example::

    mongodb://user:pass@%2Ftmp%2Fmongodb-27017.sock/authDB?replicaSet=rs

The host information cannot contain an unescaped slash ("/"), if it does then an exception MUST be thrown informing users that paths must be URL encoded. For example::

  Unsupported host '/tmp/mongodb-27017.sock', UNIX socket domain paths must be URL encoded.

Support for UNIX domain sockets and IP Literals is OPTIONAL.

Unsupported host types MUST throw an exception informing the user they are not supported.

This specification does not define how host types should be differentiated (e.g. determining if a parsed host string is a socket path or hostname). It is merely concerned with extracting the host identifiers from the URI.

Port (optional)
~~~~~~~~~~~~~~~
The port is an integer between 1 and 65535 (inclusive) that identifies the port to connect to. See `RFC 3986 <http://tools.ietf.org/html/rfc3986#section-3.2.3>`_ .

------------------------
Auth Database (optional)
------------------------
The database to authenticate against. If provided it is everything after the Host Information (ending with "/") and up to the first question mark ("?") or end of string. The auth database MUST be URL decoded by the parser.

-----------------------------
Connection Options (optional)
-----------------------------

Any extra options to configure the MongoClient connection can be specified in the connection options part of the connection string. If provided, it is everything after the Host Information, optional auth database, and first question mark ("?") to the end of the
string.  Connection Options consist of an ordered list of Key Value Pairs that are delimited by an ampersand ("&"). A delimiter of a semi colon (";") MAY also be supported for connection options for legacy reasons.

Key Value Pair
--------------
A key value pair represents the option key and its associated value. The key is everything up to the first equals sign ("=") and the value is everything afterwards. Key values contain the following information:

- Key:
   The connection option's key string.  Keys should be normalised and
   character case should be ignored.
- Value: (optional)
   The value if provided otherwise it defaults to an empty string.

---------------------------
Defining connection options
---------------------------
Connection option key values MUST be defined in the relevant specification that describes the usage of the key and value.  The value data type MUST also be defined there. The value's default value SHOULD also be defined if it is relevant.

Keys
----
Keys are strings and the character case must be normalized by lower casing the uppercase ASCII characters A through Z; other characters are left as-is.

When defining and documenting keys, specifications should follow the camelCase naming convention with the first letter in lowercase, snake\_case MUST not be used. Keys that aren't supported by a driver MUST be ignored.

A WARN level logging message MUST be issued. For example::

  Unsupported option 'connectMS' on URI 'mongodb://localhost?connectMS=1'. Keys should be descriptive and follow existing conventions:


Time based keys
~~~~~~~~~~~~~~~
If a key represents a unit of time it MUST end with that unit of time.

Key authors SHOULD follow the existing convention of defaulting to using milliseconds as the unit of time (e.g. `connectionTimeoutMS`).

Values
------
The values in connection options MUST be URL decoded by the parser. The values can represent the following data types:

- Strings:
    The value
- Integer:
    The value parsed as a integer
- Boolean:
    "true" and "false" strings MUST be supported.

  - For legacy reasons it is RECOMMENDED that alternative values for true and false be supported:

    - true: "1", "yes", "y" and "t"
    - false: "0", "-1", "no", "n" and "f".

  Alternative values are deprecated and MUST be removed from documentation and examples.

  If any of these alternative values are used, drivers MUST log a deprecation notice or issue a logging message at the WARNING level (as appropriate for your language). For example::

    Deprecated boolean value for "journal" : "1", please update to "journal=true"

- Lists:
    Repeated keys represent a list in the Connection String consisting of the corresponding values in the same order as they appear in the Connection String. For example::

      ?readPreferenceTags=dc:ny,rack:1&readPreferenceTags=dc:ny&readPreferenceTags=
- Key value pairs:
    A value that represents one or more key and value pairs. Multiple key value pairs are delimited by a comma (","). The key is everything up to the first colon sign (":") and the value is everything afterwards. If any keys or values containing a comma (",") or a colon (":") they must be URL encoded. For example::

      ?readPreferenceTags=dc:ny,rack:1

Any invalid Values for a given key MUST be ignored and MUST log a WARN level message. For example::

  Unsupported value for "fsync" : "ifPossible"

-------------
Repeated Keys
-------------
If a key is repeated and the corresponding data type is not a List then the precedence of which key value pair will be used is undefined.

Where possible, a warning SHOULD be raised to inform the user that multiple options were found for the same value.

--------------------------
Deprecated Key Value Pairs
--------------------------
If a key name was deprecated due to renaming it MUST still be supported. Users aren't expected to be vigilant on changes to key names.

If the renamed key is also defined in the connection string the deprecated key MUST NOT be applied and a WARN level message MUST be logged. For example::

    Deprecated key "wtimeout" present and ignored as found replacement "wtimeoutms" value.

Deprecated keys MUST log a WARN level message informing the user that the option is deprecated and supply the alternative key name. For example::

    Deprecated key "wtimeout" has been replaced with "wtimeoutms"

--------------
Legacy support
--------------

Semi colon (";") query parameter delimiters and alternative string representations of Boolean values MAY be supported only for legacy reasons.

As these options are not standard they might not be supported across all drivers. As such, these alternatives MUST NOT be used as general examples or documentation.

------------------------------------
Language specific connection options
------------------------------------

Connection strings are a mechanism to configure a MongoClient outside the user's application. As each driver may have language specific configuration options, those options SHOULD also be supported via the connection string.   Where suitable, specifications MUST be updated to reflect new options.

Keys MUST follow existing connection option naming conventions as defined above. Values MUST also follow the existing, specific data types.

Any options that are not supported MUST raise a WARN log level as described in the keys section.

-----------------------------
Connection options precedence
-----------------------------

As the connection string is designed as a mechanism outside of an application to define and change MongoClient configuration, it is RECOMMENDED that the connection string and its defined options take precedence over any MongoClient Options defined in the application, which take precedence over default values.

---------
Test Plan
---------

See the `README <tests/README.rst>`_ for tests.

---------------------
Motivation for Change
---------------------
The motivation for this specification is to publish how connection strings are formed and how they should be parsed.  This is important because although the connection string follows the terminology of a standard URI format (as described in `RFC 3986 <http://tools.ietf.org/html/rfc3986>`_) it is not a standard URI and cannot be parsed by standard URI parsers.

The specification also formalizes the standard practice for the definition of new connection options and where the responsibility for their definition should be.

----------------
Design Rationale
----------------
The rationale for the Connection String is to provide a consistent, driver independent way to define the connection to a MongoDB system outside of the application.  The connection string is an existing standard and is already widely used.

-----------------------
Backwards Compatibility
-----------------------
Connection Strings are already generally supported across languages and driver implementations.  As the responsibility for the definitions of connections options relies on the specifications defining them, there should be no backwards compatibility breaks caused by this specification with regards to options.

Connection options precedence may cause some backwards incompatibilities as existing driver behaviour differs here. As such,  it is currently only a recommendation.

------------------------
Reference Implementation
------------------------
The Java driver implements a ``ConnectionString`` class for the parsing of the connection string; however, it does not support UNIX domain sockets. The Python driver's ``uri_parser`` module implements connection string parsing for both hosts and UNIX domain sockets.

The following example parses a connection string into its components and can be used as a guide.

Given the string ``mongodb://foo:bar%3A@mongodb.example.com,%2Ftmp%2Fmongodb-27018.sock/admin?w=1``:

1. Validate and remove the scheme prefix ``mongodb://``, leaving: ``foo:bar%3A@mongodb.example.com,%2Ftmp%2Fmongodb-27018.sock/admin?w=1``

2. Split the string by the last, unescaped ``/`` (if any), yielding:

   1. User information and host identifers: ``foo:bar%3A@mongodb.example.com,%2Ftmp%2Fmongodb-27018.sock``.

   2. Auth database and connection options: ``admin?w=1``.

3. Split the user information and host identifiers string by the last, unescaped ``@``, yielding:

   1. User information: ``foo:bar%3A``.

   2. Host identifiers: ``mongodb.example.com,%2Ftmp%2Fmongodb-27018.sock``.

4. Validate, split (if applicable), and URL decode the user information. In this example, the username and password would be ``foo`` and ``bar:``, respectively.

5. Validate, split, and URL decode the host identifiers. In this example, the hosts would be ``["mongodb.example.com", "/tmp/mongodb-27018.sock"]``.

6. Split the auth database and connection options string by the first, unescaped ``?``, yielding:

   1. Auth database: ``admin``.

   2. Connection options: ``w=1``.

7. URL decode the auth database. In this example, the auth database is ``admin``.

8. Validate, split, and URL decode the connection options. In this example, the connection options are ``{w: 1}``.

---
Q&A
---

Q: What about existing Connection Options that aren't currently defined in a specification?
  Ideally all MongoClient options would already belong in their relevant specifications.  As we iterate and produce more specifications these options should be covered.

Q: Why is it recommended that Connection Options take precedence over application set options?
  This is only a recommendation but the reasoning is application code is much harder to change across deployments. By making the Connection String take precedence from outside the application it would be easier for the application to be portable across environments.  The order of precedence of MongoClient hosts and options is recommended to be from low to high:

  1. Default values
  2. MongoClient hosts and options
  3. Connection String hosts and options

Q: Why WARN level warning on unknown options rather than throwing an exception?
 It is responsible to inform users of possible misconfigurations and both methods achieve that.  However, there are conflicting requirements of a  Connection String.  One goal is that any given driver should be configurable by a connection string but different drivers and languages have different feature sets.  Another goal is that Connection Strings should be portable and as such some options supported by language X might not be relevant to language Y. Any given driver does not know is an option is specific to a different driver or is misspelled or just not supported.  So the only way to stay portable and support configuration of all options is to not throw an exception but rather log a warning.

Q: How long should deprecation options be supported?
 This is not declared in this specification. It's not deemed responsible to give a single timeline for how long deprecated options should be supported. As such any specifications that deprecate options that do have the context of the decision should provide the timeline.

Q: Why can I not use a standard URI parser?
  The connection string format does not follow the standard URI format (as described in `RFC 3986 <http://tools.ietf.org/html/rfc3986>`_) we differ in two key areas:

  1. Hosts
      The connection string allows for multiple hosts for high availability reasons but standard URI's only ever define a single host.

  2. Query Parameters / Connection Options
      The connection string provides a concreted definition on how the Connection Options are parsed, including definitions of different data types.  The `RFC 3986 <http://tools.ietf.org/html/rfc3986>`_ only defines that they are `key=value` pairs and gives no instruction on parsing. In fact different languages handle the parsing of query parameters in different ways and as such there is no such thing as a standard URI parser.

Q: Can the connection string contain non-ASCII characters?
  The connection string can contain non-ASCII characters.  The connection string is text, which can be encoded in any way appropriate for the application (e.g. the C Driver requires you to pass it a UTF-8 encoded connection string).

Q: Why does reference implementation check for a ``.sock`` suffix when parsing a socket path and possible auth database?
  To simplify parsing of a socket path followed by an auth database, we rely on MongoDB's `naming restrictions <http://docs.mongodb.org/manual/reference/limits/#naming-restrictions>`_), which do not allow database names to contain a dot character, and the fact that socket paths must end with ``.sock``. This allows us to differentiate the last part of a socket path from a database name. While we could immediately rule out an auth database on the basis of the dot alone, this specification is primarily concerned with breaking down the components of a URI (e.g. hosts, auth database, options) in a deterministic manner, rather than applying strict validation to those parts (e.g. host types, database names, allowed values for an option). Additionally, some drivers might allow a namespace (e.g. ``"db.collection"``) for the auth database part, so we do not want to be more strict than is necessary for parsing.

Q: Why throw an exception if the userinfo contains a percent sign ("%"), at-sign ("@"), or more than one colon (":")?
  This is done to help users format the connection string correctly. Although at-signs ("@") or colons (":") in the username must be URL encoded, users may not be aware of that requirement. Take the following example::

    mongodb://anne:bob:pass@localhost:27017

  Is the username ``anne`` and the password ``bob:pass`` or is the username ``anne:bob`` and the password ``pass``? Accepting this as the userinfo could cause authentication to fail, causing confusion for the user as to why. Allowing unescaped at-sign and percent symbols would invite further ambiguity. By throwing an exception users are made aware and then update the connection string so to be explicit about what forms the username and password.

Q: Why must UNIX domain sockets be URL encoded?
  This has been done to reduce ambiguity between the socket name and the database name. Take the following example::

    mongodb:///tmp/mongodb.sock/mongodb.sock

  Is the host ``/tmp/mongodb.sock`` and the auth database ``mongodb.sock`` or does the connection string just contain the host ``/tmp/mongodb.sock/mongodb.sock`` and no auth database?  By enforcing URL encoding on UNIX domain sockets it makes users be explicit about the host and the auth database. By requiring an exception to be thrown when the host contains a slash ("/") users can be informed on how to migrate their connection strings.

Q: Why must the auth database be URL decoded by the parser?
  On Linux systems database names can contain a question mark ("?"), in these rare cases the auth database must be URL encoded.  This disambiguates between the auth database and the connection options. Take the following example::

    mongodb://localhost/admin%3F?w=1

  In this case the auth database would be ``admin?`` and the connection options  ``w=1``.

-------
Changes
-------

- 2017-01-09: In Userinfo section, clarify that percent signs must be encoded.
- 2016-07-22: In Port section, clarify that zero is not an acceptable port.
