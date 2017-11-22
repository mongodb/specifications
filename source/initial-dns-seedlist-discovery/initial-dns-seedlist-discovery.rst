.. role:: javascript(code)
  :language: javascript

==============================
Initial DNS Seedlist Discovery
==============================

:Spec-ticket: SPEC-878, SPEC-937
:Title: Initial DNS Seedlist Discovery
:Authors: Derick Rethans
:Status: Draft
:Type: Standards
:Last Modified: 2017-11-21
:Version: 1.3.0
:Spec Lead: Matt Broadstone
:Advisory Group: \A. Jesse Jiryu Davis
:Approver(s): Bernie Hackett, David Golden, Jeff Yemin, Matt Broadstone, A. Jesse Jiryu Davis


.. contents::

--------

Abstract
========

Presently, seeding a driver with an initial list of ReplicaSet or MongoS
addresses is somewhat cumbersome, requiring a comma-delimited list of host
names to attempt connections to.  A standardized answer to this problem exists
in the form of SRV records, which allow administrators to configure a single
domain to return a list of host names. Supporting this feature would assist
our users by decreasing maintenance load, primarily by removing the need to
maintain seed lists at an application level.

This specification builds on the `Connection String`_ specification. It adds a
new protocol scheme and modifies how the `Host Information`_ is interpreted.

.. _`Connection String`: ../connection-string/connection-string-spec.rst
.. _`Host Information`: ../connection-string/connection-string-spec.rst#host-information

META
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

The connection string parser in the driver is extended with a new protocol
``mongodb+srv`` as a logical pre-processing step before it considers the
connection string and SDAM specifications. In this protocol, the comma
separated list of host names is replaced with a single host name. The
format is::

    mongodb+srv://{hostname}.{domainname}/{options}

Seedlist Discovery
------------------

In this preprocessing step, the driver will query the DNS server for SRV
records on ``{hostname}.{domainname}``, prefixed with ``_mongodb._tcp.``:
``_mongodb._tcp.{hostname}.{domainname}``. This DNS query is expected to
respond with one or more SRV records. From the DNS result, the driver now MUST
behave the same as if an ``mongodb://`` URI was provided with all the host
names and port numbers that were returned as part of the DNS SRV query result.

The priority and weight fields in returned SRV records MUST be ignored.

If ``mongodb+srv`` is used, a driver MUST implicitly also enable TLS. Clients
can turn this off by passing ``ssl=false`` in either the Connection String,
or options passed in as parameters in code to the MongoClient constructor (or
equivalent API for each driver), but not through a TXT record (discussed in
the next section).

A driver MUST verify that in addition to the ``{hostname}``, the
``{domainname}`` consists of at least two parts: the domain name, and a TLD.
Drivers MUST raise an error and MUST NOT contact the DNS server to obtain SRV
(or TXT records) if the full URI does not consists of at least three parts.

A driver MUST verify that the host names returned through SRV records have the
same parent ``{domainname}``. Drivers MUST raise an error and MUST NOT
initiate a connection to any returned host name which does not share the same
``{domainname}``.

It is an error to specify a port in a connection string with the
``mongodb+srv`` protocol, and the driver MUST raise a parse error and MUST NOT
do DNS resolution or contact hosts.

It is an error to specify more than one host name in a connection string with
the ``mongodb+srv`` protocol, and the driver MUST raise a parse error and MUST
NOT do DNS resolution or contact hosts.

The driver MUST NOT attempt to connect to any hosts until the DNS query has
returned its results.

If the DNS result returns no SRV records, or no records at all, or a DNS error
happens, an error MUST be raised indicating that the URI could not be used to
find hostnames. The error SHALL include the reason why they could not be
found.

Default Connection String Options
---------------------------------

As a second preprocessing step, a Client MUST also query the DNS server for
TXT records on ``{hostname}.{domainname}``. If available, a TXT record
provides default connection string options. The maximum length of a TXT record
string is 255
characters, but there can be multiple strings per TXT record. A Client MUST
support multiple TXT record strings and concatenate them as if they were one
single string in the order they are defined in each TXT record. The order of
multiple character strings in each TXT record is guaranteed.
A Client MUST NOT allow multiple TXT records for the same host name and MUST
raise an error when multiple TXT records are encountered.

Information returned within a TXT record is a simple URI string, just like
the ``{options}`` in a connection string.

A Client MUST only support the ``authSource`` and ``replicaSet`` options
through a TXT record, and MUST raise an error if any other option is
encountered. Although using ``mongodb+srv://`` implicitly enables TLS, a
Client MUST NOT allow the ``ssl`` option to be set through a TXT record
option.

TXT records MAY be queried either before, in parallel, or after SRV records.
Clients MUST query both the SRV and the TXT records before attempting any
connection to MongoDB.

A Client MUST use options specified in the Connection String, and options
passed in as parameters in code to the MongoClient constructor (or equivalent
API for each driver), to override options provided through TXT records.

.. _`Connection String spec`: ../connection-string/connection-string-spec.rst#defining-connection-options

If any connection string option in a TXT record is incorrectly formatted, a
Client MUST throw a parse exception.

This specification does not change the behaviour of handling unknown keys or
incorrect values as is set out in the `Connection String spec`_. Unknown keys
or incorrect values in default options specified through TXT records MUST be
handled in the same way as unknown keys or incorrect values directly specified
through a Connection String. For example, if a driver that does not support
the ``authSource`` option finds ``authSource=db`` in a TXT record, it MUST handle
the unknown option according to the rules in the Connection String spec.

Example
=======

If we provide the following URI::

    mongodb+srv://server.mongodb.com/

The driver needs to request the DNS server for the SRV record
``_mongodb._tcp.server.mongodb.com``. This could return::

    Record                            TTL   Class    Priority Weight Port  Target
    _mongodb._tcp.server.mongodb.com. 86400 IN SRV   0        5      27317 mongodb1.mongodb.com.
    _mongodb._tcp.server.mongodb.com. 86400 IN SRV   0        5      27017 mongodb2.mongodb.com.

The returned host names (``mongodb1.mongodb.com`` and
``mongodb2.mongodb.com``) must share the same parent domain name
(``mongodb.com``) as the provided host name (``server.mongodb.com``).

The driver also needs to request the DNS server for the TXT records on
``server.mongodb.com``. This could return::

    Record              TTL   Class    Text
    server.mongodb.com. 86400 IN TXT   "replicaSet=replProduction&authSource=authDB"

From the DNS results, the driver now MUST treat the host information as if the
following URI was used instead::

    mongodb://mongodb1.mongodb.com:27317,mongodb2.mongodb.com:27107/?ssl=true&replicaSet=replProduction&authSource=authDB

If we provide the following URI with the same DNS (SRV and TXT) records::

    mongodb+srv://server.mongodb.com/?authSource=otherDB

Then the default in the TXT record for ``authSource`` is not used as
the value in the connection string overrides it. The Client MUST treat the host
information as if the following URI was used instead::

    mongodb://mongodb1.mongodb.com:27317,mongodb2.mongodb.com:27107/?ssl=true&replicaSet=replProduction&authSource=otherDB

Test Plan
=========

See README.rst in the accompanying `test directory`_.

.. _`test directory`: tests

Additionally, see the ``mongodb+srv`` test ``invalid-uris.yml`` in the `Connection
String Spec tests`_.

.. _`Connection String Spec tests`: ../connection-string/tests

Motivation
==========

Several of our users have asked for this through tickets:

* `<https://jira.mongodb.org/browse/DRIVERS-201>`_
* `<https://jira.mongodb.org/browse/NODE-865>`_
* `<https://jira.mongodb.org/browse/CSHARP-536>`_

Design Rationale
================

The design specifically calls for a pre-processing stage of the processing of
connection URLs to minimize the impact on existing functionality.

Justifications
==============

Why Are Multiple Key-Value Pairs Allowed in One TXT Record?
-----------------------------------------------------------

One could imagine an alternative design in which each TXT record would allow
only one URI option. No ``&`` character would be allowed as a delimiter within
TXT records.

In this spec we allow multiple key-value pairs within one TXT record,
delimited by ``&``, because it will be common for all options to fit in a
single 255-character TXT record, and it is much more convenient to configure
one record in this case than to configure several.

Secondly, in some cases the order in which options occur is important. For
example, readPreferenceTags can appear both multiple times, and the order in
which they appear is significant. Because DNS servers may return TXT records
in any order, it is only possible to guarantee the order in which
readPreferenceTags keys appear by having them in the same TXT record.

Why Is There No Mention of UTF-8 Characters?
--------------------------------------------

Although DNS TXT records allow any octet to exist in its value, many DNS
providers do not allow non-ASCII characters to be configured. As it is
unlikely that any option names or values in the connection string have
non-ASCII characters, we left the behaviour of supporting UTF-8 characters as
unspecified.

Reference Implementation
========================

None yet.

Backwards Compatibility
=======================

There are no backwards compatibility concerns.

Future Work
===========

In the future we could consider using the priority and weight fields of the
SRV records.

ChangeLog
=========

2017-11-21 — 1.3.0
    Add clause that using ``mongodb+srv://`` implies enabling TLS. Add
    restriction that only ``authSource`` and ``replicaSet`` are allows in TXT
    records. Add restriction that only one TXT record is supported share
    the same parent domain name as the given host name.

2017-11-17 — 1.2.0
    Add new rule that indicates that host names in returned SRV records MUST
    share the same parent domain name as the given host name.

2017-11-17 — 1.1.6
    Remove language and tests for non-ASCII characters.

2017-11-07 — 1.1.5
    Clarified that all parts of listable options such as readPreferenceTags
    are ignored if they are also present in options to the MongoClient
    constructor.

    Clarified which host names to use for SRV and TXT DNS queries.

2017-11-01 — 1.1.4
    Clarified that individual TXT records can have multiple strings.

2017-10-31 — 1.1.3
    Added a clause that specifying two host names with a `mongodb+srv://`` URI
    is not allowed. Added a few more test cases.

2017-10-18 — 1.1.2
    Removed prohibition of raising DNS related errors when parsing the URI.

2017-10-04 — 1.1.1
    Removed from `Future Work`_ the line about multiple MongoS discovery. The
    current specification already allows for it, as multiple host names which
    are all MongoS servers is already allowed under SDAM. And this
    specification does not modify SDAM.

2017-10-04 — 1.1
    Added support for connection string options through TXT records.

2017-09-19
    Clarify that host names in `mongodb+srv://` URLs work like normal host
    specifications.

2017-09-01
    Updated test plan with YAML tests, and moved prose tests for URI parsing
    into invalid-uris.yml in the Connection String Spec tests.
