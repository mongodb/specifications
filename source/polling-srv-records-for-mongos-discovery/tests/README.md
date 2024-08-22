# SRV Polling Tests

## Introduction

This directory contains prose test descriptions that drivers can use to prove their conformance to the SRV polling
specification.

Without (automated) access to a DNS server configuration, it is nearly impossible to implement functional tests for a
correct implementation of this specification. However, it might be possible to mock changes to DNS SRV records such that
automated testing is doable. In any case, the following tests should be executed, either manually, or programmatically.

## Configuring the Test Environment

To test, start a sharded cluster with mongos servers on ports 27017, 27018, 27019, and 27020.

For each test, take as a starting point the test1, test3, and test22 SRV records from the
[test set-up](../../initial-dns-seedlist-discovery/tests/README.md) from the
[Initial DNS Seedlist Discovery](../../initial-dns-seedlist-discovery/initial-dns-seedlist-discovery.md) specification:

```
Record                                    TTL    Class   Address
localhost.test.test.build.10gen.cc.        86400  IN A    127.0.0.1

Record                                    TTL    Class   Port   Target
_mongodb._tcp.test1.test.build.10gen.cc.      86400  IN SRV  27017  localhost.test.build.10gen.cc.
_mongodb._tcp.test1.test.build.10gen.cc.      86400  IN SRV  27018  localhost.test.build.10gen.cc.
_mongodb._tcp.test3.test.build.10gen.cc.      86400  IN SRV  27017  localhost.test.build.10gen.cc.
_customname._tcp.test22.test.build.10gen.cc.  86400  IN SRV  27017  localhost.test.build.10gen.cc.
```

## Prose Tests

### Changing DNS records with test1.test.build.10gen.cc

The following tests MUST setup a MongoClient using the `test1.test.build.10gen.cc` SRV record. Each test MUST mock the
described DNS changes and then verify that the new list of hosts is present.

#### 1. Addition of a new DNS record

Add the following record:

```
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27019  localhost.test.build.10gen.cc.
```

#### 2. Removal of an existing DNS record

Remove the following record:

```
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27018  localhost.test.build.10gen.cc.
```

#### 3. Replacement of a DNS record

Replace the following record:

```
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27018  localhost.test.build.10gen.cc.
```

with:

```
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27019  localhost.test.build.10gen.cc.
```

#### 4. Replacement of both existing DNS records with *one* new record

Replace both records with:

```
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27019  localhost.test.build.10gen.cc.
```

#### 5. Replacement of both existing DNS records with *two* new records

Replace both records with:

```
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27019  localhost.test.build.10gen.cc.
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27020  localhost.test.build.10gen.cc.
```

### Error scenarios with test1.test.build.10gen.cc

The following tests MUST setup a MongoClient using the `test1.test.build.10gen.cc` SRV record. Each test MUST mock the
described error situation and assert that the internal list of discovered mongos servers has not changed.

#### 6. DNS record lookup timeout

Mock a DNS record lookup timeout error.

#### 7. DNS record lookup failure

Mock a DNS record lookup failure (i.e. domain no longer exists because it's no longer registered).

#### 8. Removal of all DNS SRV records

Mock a DNS record lookup that returns zero SRV records.

### Changing DNS records with test3.test.build.10gen.cc

The following tests MUST setup a MongoClient using the `test3.test.build.10gen.cc` SRV record. Each test MUST mock the
described situation and make the specified assertions.

#### 9. Test that SRV polling is not done for load balalanced clusters

Connect to `mongodb+srv://test3.test.build.10gen.cc/?loadBalanced=true`, mock the addition of the following DNS record:

```
_mongodb._tcp.test3.test.build.10gen.cc.  86400  IN SRV  27018  localhost.test.build.10gen.cc.
```

Wait until `2*rescanSRVIntervalMS` and assert that the final topology description only contains one server:
`localhost.test.build.10gen.cc.` at port `27017`.

### SRV polling with srvMaxHosts MongoClient option

The following tests MUST setup a MongoClient using the `srvMaxHosts` option and `test1.test.build.10gen.cc` SRV record.
Each test MUST mock the described DNS changes and then verify that the new list of hosts is present.

#### 10. All DNS records are selected (srvMaxHosts = 0)

Configure the MongoClient with `srvMaxHosts=0`.

Replace the following record:

```
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27018  localhost.test.build.10gen.cc.
```

with:

```
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27019  localhost.test.build.10gen.cc.
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27020  localhost.test.build.10gen.cc.
```

Wait until `2*rescanSRVIntervalMS` and assert that the final topology description contains the following hosts:

- localhost.test.build.10gen.cc:27017
- localhost.test.build.10gen.cc:27019
- localhost.test.build.10gen.cc:27020

#### 11. All DNS records are selected (srvMaxHosts >= records)

Configure the MongoClient with `srvMaxHosts=2`.

Replace both records with:

```
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27019  localhost.test.build.10gen.cc.
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27020  localhost.test.build.10gen.cc.
```

Wait until `2*rescanSRVIntervalMS` and assert that the final topology description contains the following hosts:

- localhost.test.build.10gen.cc:27019
- localhost.test.build.10gen.cc:27020

#### 12. New DNS records are randomly selected (srvMaxHosts > 0)

Configure the MongoClient with `srvMaxHosts=2`.

Replace the following record:

```
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27018  localhost.test.build.10gen.cc.
```

with:

```
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27019  localhost.test.build.10gen.cc.
_mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27020  localhost.test.build.10gen.cc.
```

Wait until `2*rescanSRVIntervalMS` and assert that the topology has two hosts present and that one of the hosts is
`localhost.test.build.10gen.cc:27017`. The second, new host will have been randomly selected and cannot be
deterministically asserted.

### SRV polling with srvServiceName MongoClient option

The following test MUST setup a MongoClient using the `srvServiceName` option and the `test22.test.build.10gen.cc` SRV
record. The test MUST mock the described DNS changes and then verify that the new list of hosts is present.

#### 13. DNS record with custom service name can be found

Configure the MongoClient with `srvServiceName=customname`.

Replace both records with:

```
_customname._tcp.test22.test.build.10gen.cc.  86400  IN SRV  27019  localhost.test.build.10gen.cc.
_customname._tcp.test22.test.build.10gen.cc.  86400  IN SRV  27020  localhost.test.build.10gen.cc.
```

Wait until `2*rescanSRVIntervalMS` and assert that the final topology description contains the following hosts:

- localhost.test.build.10gen.cc:27019
- localhost.test.build.10gen.cc:27020
