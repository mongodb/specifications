# Initial DNS Seedlist Discovery

- Status: Accepted
- Minimum Server Version: N/A

______________________________________________________________________

## Abstract

Presently, seeding a driver with an initial list of ReplicaSet or MongoS addresses is somewhat cumbersome, requiring a
comma-delimited list of host names to attempt connections to. A standardized answer to this problem exists in the form
of SRV records, which allow administrators to configure a single SRV record to return a list of host names. Supporting
this feature would assist our users by decreasing maintenance load, primarily by removing the need to maintain seed
lists at an application level.

This specification builds on the [Connection String](../connection-string/connection-string-spec.md) specification. It
adds a new protocol scheme and modifies how the
[Host Information](../connection-string/connection-string-spec.md#host-information) is interpreted.

## META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

### Connection String Format

The connection string parser in the driver is extended with a new protocol `mongodb+srv` as a logical pre-processing
step before it considers the connection string and SDAM specifications. In this protocol, the comma separated list of
host names is replaced with a single host name. The format is:

```text
mongodb+srv://{hostname}/{options} 
```

`{options}` refers to the optional elements from the [Connection String](../connection-string/connection-string-spec.md)
specification following the `Host Information`. This includes the `Auth database` and `Connection Options`.

For the purposes of this document, `{hostname}` will be divided using the following terminology. If an SRV `{hostname}`
has:

1. Three or more `.` separated parts, then the left-most part is the `{subdomain}` and the remaining portion is the
    `{domainname}`.

    - Examples:
        - `{hostname}` = `cluster_1.tests.mongodb.co.uk`

            - `{subdomain}` = `cluster_1`
            - `{domainname}` = `tests.mongodb.co.uk`

        - `{hostname}` = `hosts_34.example.com`

            - `{subdomain}` = `hosts_34`
            - `{domainname}` = `example.com`

2. One or two `.` separated part(s), then the `{hostname}` is equivalent to the `{domainname}`, and there is no
    subdomain.

    - Examples:
        - `{hostname}` = `{domainname}` = `localhost`
        - `{hostname}` = `{domainname}` = `mongodb.local`

Only `{domainname}` is used during SRV record verification and `{subdomain}` is ignored.

### MongoClient Configuration

#### srvMaxHosts

This option is used to limit the number of mongos connections that may be created for sharded topologies. This option
limits the number of SRV records used to populate the seedlist during initial discovery, as well as the number of
additional hosts that may be added during
[SRV polling](../polling-srv-records-for-mongos-discovery/polling-srv-records-for-mongos-discovery.md). This option
requires a non-negative integer and defaults to zero (i.e. no limit). This option MUST only be configurable at the level
of a `MongoClient`.

#### srvServiceName

This option specifies a valid SRV service name according to
[RFC 6335](https://datatracker.ietf.org/doc/html/rfc6335#section-5.1), with the exception that it may exceed 15
characters as long as the 63rd (62nd with prepended underscore) character DNS query limit is not surpassed. This option
requires a string value and defaults to "mongodb". This option MUST only be configurable at the level of a
`MongoClient`.

#### URI Validation

The driver MUST report an error if either the `srvServiceName` or `srvMaxHosts` URI options are specified with a non-SRV
URI (i.e. scheme other than `mongodb+srv`). The driver MUST allow specifying the `srvServiceName` and `srvMaxHosts` URI
options with an SRV URI (i.e. `mongodb+srv` scheme).

If `srvMaxHosts` is a positive integer, the driver MUST throw an error in the following cases:

- The connection string contains a `replicaSet` option.
- The connection string contains a `loadBalanced` option with a value of `true`.

When validating URI options, the driver MUST first do the SRV and TXT lookup and then perform the validation. For
drivers that do SRV lookup asynchronously this may result in a `MongoClient` being instantiated but erroring later
during operation execution.

### Seedlist Discovery

#### Validation Before Querying DNS

It is an error to specify a port in a connection string with the `mongodb+srv` protocol, and the driver MUST raise a
parse error and MUST NOT do DNS resolution or contact hosts.

It is an error to specify more than one host name in a connection string with the `mongodb+srv` protocol, and the driver
MUST raise a parse error and MUST NOT do DNS resolution or contact hosts.

If `mongodb+srv` is used, a driver MUST implicitly also enable TLS. Clients can turn this off by passing `tls=false` in
either the Connection String, or options passed in as parameters in code to the MongoClient constructor (or equivalent
API for each driver), but not through a TXT record (discussed in a later section).

#### Querying DNS

In this preprocessing step, the driver will query the DNS server for SRV records on the hostname, prefixed with the SRV
service name and protocol. The SRV service name is provided in the `srvServiceName` URI option and defaults to
`mongodb`. The protocol is always `tcp`. After prefixing, the URI should look like: `_{srvServiceName}._tcp.{hostname}`.
This DNS query is expected to respond with one or more SRV records.

The priority and weight fields in returned SRV records MUST be ignored.

If the DNS result returns no SRV records, or no records at all, or a DNS error happens, an error MUST be raised
indicating that the URI could not be used to find hostnames. The error SHALL include the reason why they could not be
found.

A driver MUST verify that the host names returned through SRV records share the original SRV's `{domainname}`. In
addition, SRV records with fewer than three `.` separated parts, the returned hostname MUST have at least one more
domain level than the SRV record hostname. Drivers MUST raise an error and MUST NOT initiate a connection to any
returned hostname which does not fulfill these requirements.

The driver MUST NOT attempt to connect to any hosts until the DNS query has returned its results.

If `srvMaxHosts` is zero or greater than or equal to the number of hosts in the DNS result, the driver MUST populate the
seedlist with all hosts.

If `srvMaxHosts` is greater than zero and less than the number of hosts in the DNS result, the driver MUST randomly
select that many hosts and use them to populate the seedlist. Drivers SHOULD use the
[Fisher-Yates shuffle](https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle#The_modern_algorithm) for
randomization.

### Default Connection String Options

As a second preprocessing step, a Client MUST also query the DNS server for TXT records on `{hostname}`. If available, a
TXT record provides default connection string options. The maximum length of a TXT record string is 255 characters, but
there can be multiple strings per TXT record. A Client MUST support multiple TXT record strings and concatenate them as
if they were one single string in the order they are defined in each TXT record. The order of multiple character strings
in each TXT record is guaranteed. A Client MUST NOT allow multiple TXT records for the same host name and MUST raise an
error when multiple TXT records are encountered.

Information returned within a TXT record is a simple URI string, just like the `{options}` in a connection string.

A Client MUST only support the `authSource`, `replicaSet`, and `loadBalanced` options through a TXT record, and MUST
raise an error if any other option is encountered. Although using `mongodb+srv://` implicitly enables TLS, a Client MUST
NOT allow the `ssl` option to be set through a TXT record option.

TXT records MAY be queried either before, in parallel, or after SRV records. Clients MUST query both the SRV and the TXT
records before attempting any connection to MongoDB.

A Client MUST use options specified in the Connection String, and options passed in as parameters in code to the
MongoClient constructor (or equivalent API for each driver), to override options provided through TXT records.

If any connection string option in a TXT record is incorrectly formatted, a Client MUST throw a parse exception.

This specification does not change the behaviour of handling unknown keys or incorrect values as is set out in the
[Connection String spec](../connection-string/connection-string-spec.md#defining-connection-options). Unknown keys or
incorrect values in default options specified through TXT records MUST be handled in the same way as unknown keys or
incorrect values directly specified through a Connection String. For example, if a driver that does not support the
`authSource` option finds `authSource=db` in a TXT record, it MUST handle the unknown option according to the rules in
the Connection String spec.

### CNAME not supported

The use of DNS CNAME records is not supported. Clients MUST NOT check for a CNAME record on `{hostname}`. A system's DNS
resolver could transparently handle CNAME, but because of how clients validate records returned from SRV queries, use of
CNAME could break validation. Seedlist discovery therefore does not recommend or support the use of CNAME records in
concert with SRV or TXT records.

## Example

If we provide the following URI:

```text
mongodb+srv://server.mongodb.com/
```

The driver needs to request the DNS server for the SRV record `_mongodb._tcp.server.mongodb.com`. This could return:

```dns
Record                            TTL   Class    Priority Weight Port  Target
_mongodb._tcp.server.mongodb.com. 86400 IN SRV   0        5      27317 mongodb1.mongodb.com.
_mongodb._tcp.server.mongodb.com. 86400 IN SRV   0        5      27017 mongodb2.mongodb.com.
```

The returned host names (`mongodb1.mongodb.com` and `mongodb2.mongodb.com`) must share the same domainname
(`mongodb.com`) as the provided host name (`server.mongodb.com`).

The driver also needs to request the DNS server for the TXT records on `server.mongodb.com`. This could return:

```dns
Record              TTL   Class    Text
server.mongodb.com. 86400 IN TXT   "replicaSet=replProduction&authSource=authDB"
```

From the DNS results, the driver now MUST treat the host information as if the following URI was used instead:

```text
mongodb://mongodb1.mongodb.com:27317,mongodb2.mongodb.com:27107/?ssl=true&replicaSet=replProduction&authSource=authDB
```

If we provide the following URI with the same DNS (SRV and TXT) records:

```text
mongodb+srv://server.mongodb.com/?authSource=otherDB
```

Then the default in the TXT record for `authSource` is not used as the value in the connection string overrides it. The
Client MUST treat the host information as if the following URI was used instead:

```text
mongodb://mongodb1.mongodb.com:27317,mongodb2.mongodb.com:27107/?ssl=true&replicaSet=replProduction&authSource=otherDB
```

## Test Plan

### Prose Tests

See README.md in the accompanying [test directory](tests/README.md).

### Spec Tests

See README.md in the accompanying [test directory](tests/README.md).

Additionally, see the `mongodb+srv` test `invalid-uris.yml` in the
[Connection String Spec tests](../connection-string/tests/README.md).

## Motivation

Several of our users have asked for this through tickets:

- <https://jira.mongodb.org/browse/DRIVERS-201>
- <https://jira.mongodb.org/browse/NODE-865>
- <https://jira.mongodb.org/browse/CSHARP-536>

## Design Rationale

The design specifically calls for a pre-processing stage of the processing of connection URLs to minimize the impact on
existing functionality.

## Justifications

### Why Are Multiple Key-Value Pairs Allowed in One TXT Record?

One could imagine an alternative design in which each TXT record would allow only one URI option. No `&` character would
be allowed as a delimiter within TXT records.

In this spec we allow multiple key-value pairs within one TXT record, delimited by `&`, because it will be common for
all options to fit in a single 255-character TXT record, and it is much more convenient to configure one record in this
case than to configure several.

Secondly, in some cases the order in which options occur is important. For example, readPreferenceTags can appear both
multiple times, and the order in which they appear is significant. Because DNS servers may return TXT records in any
order, it is only possible to guarantee the order in which readPreferenceTags keys appear by having them in the same TXT
record.

### Why Is There No Mention of UTF-8 Characters?

Although DNS TXT records allow any octet to exist in its value, many DNS providers do not allow non-ASCII characters to
be configured. As it is unlikely that any option names or values in the connection string have non-ASCII characters, we
left the behaviour of supporting UTF-8 characters as unspecified.

## Reference Implementation

None yet.

## Backwards Compatibility

There are no backwards compatibility concerns.

## Future Work

In the future we could consider using the priority and weight fields of the SRV records.

## ChangeLog

- 2025-04-22: Add test for SRV hostname validation when resolver and resolved hostnames are identical with three domain
    levels.

- 2024-09-24: Removed requirement for URI to have three '.' separated parts; these SRVs have stricter parent domain
    matching requirements for security. Create terminology section. Remove usage of term `{TLD}`. The `{hostname}` now
    refers to the entire hostname, not just the `{subdomain}`.

- 2024-03-06: Migrated from reStructuredText to Markdown.

- 2022-10-05: Revise spec front matter and reformat changelog.

- 2021-10-14: Add `srvMaxHosts` MongoClient option and restructure Seedlist Discovery section. Improve documentation for
    the `srvServiceName` MongoClient option and add a new URI Validation section.

- 2021-09-15: Clarify that service name only defaults to `mongodb`, and should be defined by the `srvServiceName` URI
    option.

- 2021-04-15: Adding in behaviour for load balancer mode.

- 2019-03-07: Clarify that CNAME is not supported

- 2018-02-08: Clarify that `{options}}` in the [Specification](#specification) section includes all the optional
    elements from the Connection String specification.

- 2017-11-21: Add clause that using `mongodb+srv://` implies enabling TLS. Add restriction that only `authSource` and
    `replicaSet` are allows in TXT records. Add restriction that only one TXT record is supported share the same parent
    domain name as the given host name.

- 2017-11-17: Add new rule that indicates that host names in returned SRV records MUST share the same parent domain name
    as the given host name. Remove language and tests for non-ASCII characters.

- 2017-11-07: Clarified that all parts of listable options such as readPreferenceTags are ignored if they are also
    present in options to the MongoClient constructor. Clarified which host names to use for SRV and TXT DNS queries.

- 2017-11-01: Clarified that individual TXT records can have multiple strings.

- 2017-10-31: Added a clause that specifying two host names with a `mongodb+srv://` URI is not allowed. Added a few more
    test cases.

- 2017-10-18: Removed prohibition of raising DNS related errors when parsing the URI.

- 2017-10-04: Removed from [Future Work](#future-work) the line about multiple MongoS discovery. The current
    specification already allows for it, as multiple host names which are all MongoS servers is already allowed under
    SDAM. And this specification does not modify SDAM. Added support for connection string options through TXT records.

- 2017-09-19: Clarify that host names in `mongodb+srv://` URLs work like normal host specifications.

- 2017-09-01: Updated test plan with YAML tests, and moved prose tests for URI parsing into invalid-uris.yml in the
    Connection String Spec tests.
