# SOCKS5 Support Tests

______________________________________________________________________

## Introduction

This document describes how drivers should test support for SOCKS5 proxies.

## Testing Requirements

For a single server version (at least 5.0), drivers MUST add two Evergreen tasks: one with a replica set with TLS
enabled, and one with TLS disabled. The servers of the replica set may listen on any free ports.

Each task MUST also start up two SOCKS5 proxies: one requiring authentication, and one that does not require
authentication.

### SOCKS5 Proxy Configuration

Drivers MUST use the `socks5srv.py` script in `drivers-evergreen-tools` to run the SOCKS5 proxy servers for Evergreen
tasks. This script MUST be run after the backing replica set has already been started, and MUST be started with
`` --map "localhost:12345 to <host>"` where `host` is the host:port identifier of an arbitrary member of the replica set. The SOCKS5 proxy server requiring authentication MUST be started with ``
--port 1080 --auth username:p4ssw0rd`, the one not requiring authentication with `--port 1081 \`\`.

## Prose Tests

Drivers MUST test the following connection strings:

| Connection String                                                                                                                      | Expected Result |
| -------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| `mongodb://<mappedhost>/?proxyHost=localhost&proxyPort=1080&directConnection=true`                                                     | (fails)         |
| `mongodb://<mappedhost>/?proxyHost=localhost&proxyPort=1081&directConnection=true`                                                     | (succeeds)      |
| `mongodb://<replicaset>/?proxyHost=localhost&proxyPort=1080`                                                                           | (fails)         |
| `mongodb://<replicaset>/?proxyHost=localhost&proxyPort=1081`                                                                           | (succeeds)      |
| `mongodb://<mappedhost>/?proxyHost=localhost&proxyPort=1080&proxyUsername=nonexistentuser&proxyPassword=badauth&directConnection=true` | (fails)         |
| `mongodb://<mappedhost>/?proxyHost=localhost&proxyPort=1081&proxyUsername=nonexistentuser&proxyPassword=badauth&directConnection=true` | (succeeds)      |
| `mongodb://<replicaset>/?proxyHost=localhost&proxyPort=1081&proxyUsername=nonexistentuser&proxyPassword=badauth`                       | (succeeds)      |
| `mongodb://<mappedhost>/?proxyHost=localhost&proxyPort=1080&proxyUsername=username&proxyPassword=p4ssw0rd&directConnection=true`       | (succeeds)      |
| `mongodb://<mappedhost>/?proxyHost=localhost&proxyPort=1081&directConnection=true`                                                     | (succeeds)      |
| `mongodb://<replicaset>/?proxyHost=localhost&proxyPort=1080&proxyUsername=username&proxyPassword=p4ssw0rd`                             | (succeeds)      |
| `mongodb://<replicaset>/?proxyHost=localhost&proxyPort=1081`                                                                           | (succeeds)      |

where `<replicaset>` stands for all hosts in the tests replica set and `mappedhost` stands for `localhost:12345`. For
the Evergreen task in which TLS is enabled, the required `tls` and - Code:`tlsCAFile` connection string options are
appended to all connection strings listed above.

Drivers MUST create a `MongoClient` for each of these connection strings, and attempt to run a `hello` command using
each client. The operation must succeed for table entries marked (succeeds) and fail for table entries marked (fails).
The connection strings MUST all be accepted as valid connection strings.

Drivers MUST run variants of these tests in which the proxy options are substituted for `MongoClient` options.

Drivers MUST verify for at least one of the connection strings marked (succeeds) that command monitoring events do not
reference the SOCKS5 proxy host where the MongoDB service server/port are referenced.
