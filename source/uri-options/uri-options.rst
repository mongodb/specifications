=========================
URI Options Specification
=========================

:Spec Title: URI Options Specification
:Spec Version: 1.6.1
:Author: Sam Rossi
:Spec Lead: Bernie Hackett
:Advisory Group: Scott L'Hommedieu
:Approver(s): Cailin Nelson, Jeff Yemin, Matt Broadstone, Dan Pasette, Prashant Mital, Spencer Jackson
:Informed: drivers@
:Status: Accepted (Could be Draft, Accepted, Rejected, Final, or Replaced)
:Type: Standards
:Last Modified: 2021-04-08


**Abstract**
------------

Historically, URI options have been defined in individual specs, and
drivers have defined any additional options independently of one another.
Because of the frustration due to there not being a single place where
all of the URI options are defined, this spec aims to do just that—namely,
provide a canonical list of URI options that each driver defines.

**THIS SPEC DOES NOT REQUIRE DRIVERS TO MAKE ANY BREAKING CHANGES.**

**META**
--------

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this
document are to be interpreted as described in
`RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

**Specification**
-----------------

Conflicting TLS options
~~~~~~~~~~~~~~~~~~~~~~~

Per the `Connection String spec <https://github.com/mongodb/specifications/blob/master/source/connection-string/connection-string-spec.rst#repeated-keys>`_,
the behavior of duplicates of most URI options is undefined. However, due
to the security implications of certain options, drivers MUST raise an
error to the user during parsing if any of the following circumstances
occur:

1. Both ``tlsInsecure`` and ``tlsAllowInvalidCertificates`` appear in the
   URI options.
2. Both ``tlsInsecure`` and ``tlsAllowInvalidHostnames`` appear in the
   URI options.
3. Both ``tlsInsecure`` and ``tlsDisableOCSPEndpointCheck`` appear in
   the URI options.
4. Both ``tlsInsecure`` and ``tlsDisableCertificateRevocationCheck``
   appear in the URI options.
5. Both ``tlsAllowInvalidCertificates`` and
   ``tlsDisableOCSPEndpointCheck`` appear in the URI options.
6. Both ``tlsAllowInvalidCertificates`` and
   ``tlsDisableCertificateRevocationCheck`` appear in the URI options.
7. Both ``tlsDisableOCSPEndpointCheck`` and
   ``tlsDisableCertificateRevocationCheck`` appear in the URI options.
8. All instances of ``tls`` and ``ssl`` in the URI options do not have the
   same value. If all instances of ``tls`` and ``ssl`` have the same
   value, an error MUST NOT be raised.

SRV URI with directConnection URI option
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The driver MUST report an error if the ``directConnection=true`` URI option
is specified with an SRV URI, because the URI may resolve to multiple
hosts. The driver MUST allow specifying ``directConnection=false`` URI
option with an SRV URI.

Multiple seeds with directConnection URI option
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The driver MUST report an error if the ``directConnection=true`` URI option
is specified with multiple seeds.

List of specified options
~~~~~~~~~~~~~~~~~~~~~~~~~

Each driver option below MUST be implemented in each driver unless marked
as optional. If an option is marked as optional, a driver MUST meet any
conditions specified for leaving it out if it is not included. If a driver
already provides the option under a different name, the driver MAY
implement the old and new names as aliases. All keys and values MUST be
encoded in UTF-8. All integer options are 32-bit unless specified otherwise.
Note that all requirements and recommendations described in the `Connection
String spec
<https://github.com/mongodb/specifications/blob/master/source/connection-string/connection-string-spec.rst>`_
pertaining to URI options apply here.


.. list-table::
   :header-rows: 1
   :widths: 1 1 1 1 1

   * - Name
     - Accepted Values
     - Default Value
     - Optional to implement?
     - Description

   * - appname
     - any string that meets the criteria listed in the `handshake spec
       <https://github.com/mongodb/specifications/blob/master/source/mongodb-handshake/handshake.rst#client-application-name>`_
     - no appname specified
     - no
     - Passed into the server in the client metadata as part of the
       connection handshake

   * - authMechanism
     - any string; valid values are defined in the `auth spec
       <https://github.com/mongodb/specifications/blob/master/source/auth/auth.rst#supported-authentication-methods>`_
     - None; default values for authentication exist for constructing authentication credentials per the
       `auth spec <https://github.com/mongodb/specifications/blob/master/source/auth/auth.rst#supported-authentication-methods>`_,
       but there is no default for the URI option itself.
     - no
     - The authentication mechanism method to use for connection to the
       server

   * - authMechanismProperties
     - comma separated key:value pairs, e.g. "opt1:val1,opt2:val2"
     - no properties specified
     - no
     - Additional options provided for authentication (e.g. to enable hostname canonicalization for GSSAPI)

   * - authSource
     - any string
     - None; default values for authentication exist for constructing authentication credentials per the
       `auth spec <https://github.com/mongodb/specifications/blob/master/source/auth/auth.rst#supported-authentication-methods>`_,
       but there is no default for the URI option itself.
     - no
     - The database that connections should authenticate against

   * - compressors
     - comma separated list of strings, e.g. "snappy,zlib"
     - defined in `compression spec <https://github.com/mongodb/specifications/blob/master/source/compression/OP_COMPRESSED.rst#compressors>`_
     - no
     - The list of allowed compression types for wire protocol messages
       sent or received from the server

   * - connectTimeoutMS
     - non-negative integer; 0 means "no timeout"
     - 10,000 ms (unless a driver already has a different default)
     - no
     - Amount of time to wait for a single TCP socket connection to the
       server to be established before erroring; note that this applies to
       SDAM hello and legacy hello operations (see handshake spec for details)

   * - directConnection
     - "true" or "false"
     - defined in `SDAM spec <https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#initial-topology-type>`_
     - no
     - Whether to connect to the deployment in Single topology.

   * - heartbeatFrequencyMS
     - integer greater than or equal to 500
     - defined in `SDAM spec <https://github.com/mongodb/specifications/blob/master/source/server-discovery-and-monitoring/server-discovery-and-monitoring.rst#heartbeatfrequencyms>`_
     - no
     - the interval between regular server monitoring checks

   * - journal
     - "true" or "false"
     - no "j" field specified
     - no
     - Default write concern "j" field for the client

   * - localThresholdMS
     - non-negative integer; 0 means 0 ms (i.e. the fastest eligible server
       must be selected)
     - defined in the `server selection spec <https://github.com/mongodb/specifications/blob/master/source/server-selection/server-selection.rst#localthresholdms>`_
     - no
     - The amount of time beyond the fastest round trip time that a given
       server’s round trip time can take and still be eligible for server selection

   * - maxIdleTimeMS
     - non-negative integer; 0 means no minimum
     - defined in the `Connection Pooling spec`_
     - required for drivers with connection pools
     - The amount of time a connection can be idle before it's closed

   * - maxPoolSize
     - non-negative integer; 0 means no maximum
     - defined in the `Connection Pooling spec`_
     - required for drivers with connection pools
     - The maximum number of clients or connections able to be created by a pool at a given time. This count includes connections which are currently checked out.

   * - maxStalenessSeconds
     - -1 (no max staleness check) or integer >= 90
     - defined in `max staleness spec <https://github.com/mongodb/specifications/blob/master/source/max-staleness/max-staleness.rst#api>`_
     - no
     - The maximum replication lag, in wall clock time, that a secondary can suffer and still be eligible for server selection

   * - minPoolSize
     - non-negative integer
     - defined in the `Connection Pooling spec`_
     - required for drivers with connection pools
     - The number of connections the driver should create and maintain in the pool even when no operations are occurring. This count includes connections which are currently checked out. 

   * - readConcernLevel
     - any string (`to allow for forwards compatibility with the server <https://github.com/mongodb/specifications/blob/master/source/read-write-concern/read-write-concern.rst#unknown-levels-and-additional-options-for-string-based-readconcerns>`_)
     - no read concern specified
     - no
     - Default read concern for the client

   * - readPreference
     - any string; currently supported values are defined in the `server selection spec <https://github.com/mongodb/specifications/blob/master/source/server-selection/server-selection.rst#mode>`_, but must be lowercase camelCase, e.g. "primaryPreferred"
     - defined in `server selection spec <https://github.com/mongodb/specifications/blob/master/source/server-selection/server-selection.rst#mode>`_
     - no
     - Default read preference for the client (excluding tags)

   * - readPreferenceTags
     - comma-separated key:value pairs (e.g. "dc:ny,rack:1" and "dc:ny)

       can be specified multiple times; each instance of this key is a
       separate tag set
     - no tags specified
     - no
     - Default read preference tags for the client; only valid if the read preference mode is not primary

       The order of the tag sets in the read preference is the same as the order they are specified in the URI

   * - replicaSet
     - any string
     - no replica set name provided
     - no
     - The name of the replica set to connect to

   * - retryReads
     - "true" or "false
     - defined in `retryable reads spec <https://github.com/mongodb/specifications/blob/master/source/retryable-reads/retryable-reads.rst#retryreads>`_
     - no
     - Enables retryable reads on server 3.6+

   * - retryWrites
     - "true" or "false
     - defined in `retryable writes spec <https://github.com/mongodb/specifications/blob/master/source/retryable-writes/retryable-writes.rst#retrywrites>`_
     - no
     - Enables retryable writes on server 3.6+

   * - serverSelectionTimeoutMS
     - positive integer; a driver may also accept 0 to be used for a special case, provided that it documents the meaning
     - defined in `server selection spec <https://github.com/mongodb/specifications/blob/master/source/server-selection/server-selection.rst#serverselectiontimeoutms>`_
     - no
     - A timeout in milliseconds to block for server selection before raising an error

   * - serverSelectionTryOnce
     - "true" or "false"
     - defined in `server selection spec <https://github.com/mongodb/specifications/blob/master/source/server-selection/server-selection.rst#serverselectiontryonce>`_
     - required for single-threaded drivers
     - Scan the topology only once after a server selection failure instead of repeatedly until the server selection times out

   * - socketTimeoutMS
     - non-negative integer; 0 means no timeout
     - no timeout
     - no
     - Amount of time spent attempting to send or receive on a socket before timing out; note that this only applies to application operations, not SDAM

   * - ssl
     - "true" or "false"
     - same as "tls"
     - no
     - alias of "tls"; required to ensure that Atlas connection strings continue to work

   * - tls
     - "true" or "false"
     - TLS required if "mongodb+srv" scheme; otherwise, drivers may may enable TLS by default if other "tls"-prefixed options are present


       Drivers MUST clearly document the conditions under which TLS is enabled implicitly
     - no
     - Whether or not to require TLS for connections to the server


   * - tlsAllowInvalidCertificates
     - "true" or "false"
     - error on invalid certificates
     - required if the driver’s language/runtime allows bypassing hostname verification
     - Specifies whether or not the driver should error when the server’s TLS certificate is invalid

   * - tlsAllowInvalidHostnames
     - "true" or "false"
     - error on invalid certificates
     - required if the driver’s language/runtime allows bypassing hostname verification
     - Specifies whether or not  the driver should error when there is a mismatch between the server’s hostname and the hostname specified by the TLS certificate

   * - tlsCAFile
     - any string
     - no certificate authorities specified
     - required if the driver's language/runtime allows non-global configuration
     - Path to file with either a single or bundle of certificate authorities to be considered trusted when making a TLS connection

   * - tlsCertificateKeyFile
     - any string
     - no client certificate specified
     - required if the driver's language/runtime allows non-global configuration
     - Path to the client certificate file or the client private key file; in the case that they both are needed, the files should be concatenated

   * - tlsCertificateKeyFilePassword
     - any string
     - no password specified
     - required if the driver's language/runtime allows non-global configuration
     - Password to decrypt the client private key to be used for TLS connections

   * - tlsDisableCertificateRevocationCheck
     - "true" or "false"
     - false i.e. driver will reach check a certificate's revocation status
     - Yes
     - Controls whether or not the driver will check a certificate's
       revocation status via CRLs or OCSP. See the `OCSP Support Spec
       <../ocsp-support/ocsp-support.rst#tlsDisableCertificateRevocationCheck>`__
       for additional information.

   * - tlsDisableOCSPEndpointCheck
     - "true" or "false"
     - false i.e. driver will reach out to OCSP endpoints `if needed
       <../ocsp-support/ocsp-support.rst#id1>`__.
     - Yes
     - Controls whether or not the driver will reach out to OCSP
       endpoints if needed. See the `OCSP Support Spec
       <../ocsp-support/ocsp-support.rst#tlsDisableOCSPEndpointCheck>`__
       for additional information.

   * - tlsInsecure
     - "true" or "false"
     - No TLS constraints are relaxed
     - no
     - Relax TLS constraints as much as possible (e.g. allowing invalid certificates or hostname mismatches); drivers must document the exact constraints which are relaxed by this option being true

   * - w
     - non-negative integer or string
     - no "w" value specified
     - no
     - Default write concern "w" field for the client

   * - waitQueueTimeoutMS
     - positive number
     - defined in the `Connection Pooling spec`_
     - required for drivers with connection pools, with exceptions described in the `Connection Pooling spec`_
     - Amount of time spent attempting to check out a connection from a server's
       connection pool before timing out

   * - wTimeoutMS
     - non-negative 64-bit integer; 0 means no timeout
     - no timeout
     - no
     - Default write concern "wtimeout" field for the client

   * - zlibCompressionLevel
     - integer between -1 and 9 (inclusive)
     - -1 (default compression level of the driver)
     - no
     - Specifies the level of compression when using zlib to compress wire
       protocol messages; -1 signifies the default level, 0 signifies no
       compression, 1 signifies the fastest speed, and 9 signifies the
       best compression

**Test Plan**
-------------

Tests are implemented and described in the `tests <tests>`_ directory

**Design Rationale**
---------------------

Why allow drivers to provide the canonical names as aliases to existing options?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First and foremost, this spec aims not to introduce any breaking changes
to drivers. Forcing a driver to change the name of an option that it
provides will break any applications that use the old option. Moreover, it
is already possible to provide duplicate options in the URI by specifying
the same option more than once; drivers can use the same semantics to
resolve the conflicts as they did before, whether it’s raising an error,
using the first option provided, using the last option provided, or simply
telling users that the behavior is not defined.

Why use "tls" as the prefix instead of "ssl" for related options?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Technically speaking, drivers already only support TLS, which supersedes
SSL. While SSL is commonly used in parlance to refer to TLS connections,
the fact remains that SSL is a weaker cryptographic protocol than TLS, and
we want to accurately reflect the strict requirements that drivers have in
ensuring the security of a TLS connection.

Why use the names "tlsAllowInvalidHostnames" and "tlsAllowInvalidCertificates"?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The "tls" prefix is used for the same reasons described above. The use of the
terms "AllowInvalidHostnames" and "AllowInvalidCertificates" is an intentional
choice in order to convey the inherent unsafety of these options, which should
only be used for testing purposes. Additionally, both the server and the shell
use "AllowInvalid" for their equivalent options.

Why provide multiple implementation options for the insecure TLS options (i.e. "tlsInsecure" vs. "tlsAllowInvalidHostnames"/"tlsAllowInvalidCertificates"?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some TLS libraries (e.g. Go’s standard library implementation) do not provide
the ability to distinguish between allow invalid certificates and hostnames,
meaning they either both are allowed, or neither are. However, when more
granular options are available, it’s better to expose these to the user to
allow them to relax security constraints as little as they need.


Why leave the decision up to drivers to enable TLS implicitly when TLS options are present?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It can be useful to turn on TLS implicitly when options such as "tlsCAFile" are
present and "tls" is not present. However, with options such as
"tlsAllowInvalidHostnames", some drivers may not have the ability to
distinguish between "false" being provided and the option not being specified.
To keep the implicit enabling of TLS consistent between such options, we defer
the decision to enable TLS based on the presence of "tls"-prefixed options
(besides "tls" itself) to drivers.

**Reference Implementations**
-----------------------------

Ruby and Python

**Security Implication**
------------------------

Each of the "insecure" TLS options (i.e. "tlsInsecure",
"tlsAllowInvalidHostnames", "tlsAllowInvalidCertificates",
"tlsDisableOCSPEndpointCheck", and
"tlsDisableCertificateRevocationCheck") default to the more secure
option when TLS is enabled. In order to be backwards compatible with
existing driver behavior, neither TLS nor authentication is enabled by
default.

**Future Work**
---------------

This specification is intended to represent the current state of drivers URI
options rather than be a static description of the options at the time it was
written. Whenever another specification is written or modified in a way that
changes the name or the semantics of a URI option or adds a new URI option,
this specification MUST be updated to reflect those changes.

Changes
-------

- 2021-04-08 Updated to refer to hello and legacy hello
- 2020-03-03 Add tlsDisableCertificateRevocationCheck option
- 2020-02-26 Add tlsDisableOCSPEndpointCheck option
- 2019-01-25 Updated to reflect new Connection Monitoring and Pooling Spec
- 2019-02-04 Specified errors for conflicting TLS-related URI options
- 2019-04-26 authSource and authMechanism have no default value
- 2019-09-08 Add retryReads option

.. _Connection Pooling spec: https://github.com/mongodb/specifications/blob/master/source/connection-monitoring-and-pooling/connection-monitoring-and-pooling.rst#connection-pool-options-1
