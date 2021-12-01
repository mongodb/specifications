==============
SOCKS5 Support
==============

:Spec Title: SOCKS5 Support
:Spec Version: 1.0.0
:Author: Anna Henningsen
:Advisors: TODO
:Status: Draft
:Type: Standards
:Minimum Server Version: N/A
:Last Modified: 2021-11-19

.. contents::

--------

Abstract
========

SOCKS5 is a standardized protocol for connecting to network services through
a separate proxy server. It can be used for connecting to hosts that would
otherwise be unreachable from the local network by connecting to a proxy
server, which receives the intended target host’s address from the client
and then connects to that address.

This specification defines driver behaviour when connecting to MongoDB services
through a SOCKS5 proxy.

META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`__.

Specification
=============


Terms
-----

SOCKS5
^^^^^^

The SOCKS protocol, version 5, as defined in `RFC1928 <https://datatracker.ietf.org/doc/html/rfc1928>`__,
restricted to either no authentication or username/password authentication
as defined in `RFC1929 <https://datatracker.ietf.org/doc/html/rfc1929>`__.


MongoClient Configuration
-------------------------

proxyHost
^^^^^^^^^

To specify to the driver to connect using a SOCKS5 proxy, a connection string
option of :code:`proxyHost=host` MUST be added to the connection string
or passed through an equivalent :code:`MongoClient` option.
This option specifies a domain name or IPv4 or IPv6 address on which
a SOCKS5 proxy is listening.
This option MUST only be configurable at the level of a :code:`MongoClient`.

proxyPort
^^^^^^^^^

To specify to the driver to connect using a SOCKS5 proxy listening
on a non-default port, a connection string option of :code:`proxyPort=port`
MUST be added to the connection string or passed through an
equivalent :code:`MongoClient` option.
This option specifies a TCP port number. The default for this option
MUST be :code:`1080`.
This option MUST only be configurable at the level of a :code:`MongoClient`.
Drivers MUST error if this option was specified and :code:`proxyHost`
was not specified.

proxyUsername
^^^^^^^^^^^^^

To specify to the driver to connect using a SOCKS5 proxy requiring
username/password authentication, a connection string option of
:code:`proxyUsername=username` MUST be added to the connection string
or passed through an equivalent :code:`MongoClient` option.
This option specifies a string of non-zero length. Drivers MUST ignore
this option if it specifies a zero-length string. Drivers MUST error
if this option was specified and :code:`proxyHost` was not specified
or :code:`proxyPassword` was not specified.

proxyPassword
^^^^^^^^^^^^^

To specify to the driver to connect using a SOCKS5 proxy requiring
username/password authentication, a connection string option of
:code:`proxyPassword=password` MUST be added to the connection string
or passed through an equivalent :code:`MongoClient` option.
This option specifies a string of non-zero length. Drivers MUST ignore
this option if it specifies a zero-length string. Drivers MUST error
if this option was specified and :code:`proxyHost` was not specified
or :code:`proxyUsername` was not specified.

Connection Pooling
------------------------

Connection Establishment
^^^^^^^^^^^^^^^^^^^^^^^^

When establishing a new outgoing TCP connection, drivers MUST perform
the following steps if :code:`proxyHost`
was specified:

#. Connect to the SOCKS5 proxy host, using :code:`proxyHost` and :code:`proxyPort` as specified.

#. Perform a SOCKS5 handshake as specified in RFC1928.

    If :code:`proxyUsername` and :code:`proxyPassword` were passed,
    drivers MUST indicate in the handshake that both "no authentication"
    and "username/password authentication" are supported. Otherwise,
    drivers MUST indicate support for "no authentication" only.

    Drivers MUST NOT attempt to perform DNS A or AAAA record resolution
    of the destination hostname and instead pass the hostname to the
    proxy as-is.

#. Continue with connection establishment as if the connection was one
   to the destination host.

Drivers MUST use the SOCKS5 proxy for connections to MongoDB services
and `client-side field-level encryption KMS servers <https://github.com/mongodb/specifications/blob/master/source/client-side-encryption/client-side-encryption.rst#kms-provider>`__.

Drivers MUST NOT use the SOCKS5 proxy for connections to
:code:`mongocryptd` processes spawned for automatic client-side field-level encryption.

Drivers MUST treat a connection failure when connecting to the SOCKS5
proxy or a SOCKS5 handshake or authentication failure the same as a
network error (e.g. `ECONNREFUSED`).

Events
------

SOCKS5 proxies are fully transparent to connection monitoring events.
In particular, in :code:`CommandStartedEvent`, :code:`CommandSucceededEvent`, and
:code:`CommandFailedEvent`, the driver SHOULD NOT reference the SOCKS5
proxy as part of the :code:`connectionId` field or other fields.

Q&A
---

Why not include DNS requests in the set of proxied network communication?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

While SOCKS5 as a protocol does support UDP forwarding, using this feature has a number
of downsides. Notably, only a subset of SOCKS5 client libraries and SOCKS5 server
implementations support UDP forwarding (e.g. the OpenSSH client’s dynamic
forwarding feature does not). This would also considerably increase implementation
complexity in drivers that do not use DNS libraries in which the driver is
in control of how the UDP packets are sent and received.

Why not support other proxy protocols, such as Socks4/Socks4a, HTTP Connect proxies, etc.?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

SOCKS5 is a powerful, standardized and widely used proxy protocol. It is likely that
almost all users which require tunneling/proxying of some sort will be able to use it,
and those who require another protocol or a more advanced setup like proxy chaining,
can work around that by using a local SOCKS5 intermediate proxy.

Why are the connection string parameters generic, with no explicit mention of SOCKS5?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the case that future changes will enable drivers using other proxy protocols,
keeping the option names generic allows their re-use.
In that case, another option would specify the protocol and SOCKS5 would be the
implied default. However, since there is no reason to believe that such additions
will be made in the forseeable future, no option for specifying the proxy protocol
is introduced here.

Why is support for authentication methods limited to no authentication and username/password authentication?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This matches the set of authentication methods most commonly implemented by SOCKS5
client libraries and thus reduces implementation complexity for drivers.
This advantage is sufficient to ignore the possible advantages that would
come with enabling other authentication methods.

Design Rationales
-----------------

Alternative Designs
-------------------

Change Log
==========
