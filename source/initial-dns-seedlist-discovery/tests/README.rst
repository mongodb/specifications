====================================
Initial DNS Seedlist Discovery tests
====================================

This directory contains platform-independent tests that drivers can use
to prove their conformance to the Initial DNS Seedlist Discovery spec.

Test Setup
----------

Start a three-node replica set on localhost, on ports 27017, 27018, and 27019,
with replica set name "repl0".

To run the tests that accompany this spec, you need to configure the SRV and
TXT records with a real name server. The following records are required for
these tests::

  Record                                    TTL    Class   Port   Target
  _mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27017  localhost.build.10gen.cc.
  _mongodb._tcp.test1.test.build.10gen.cc.  86400  IN SRV  27018  localhost.build.10gen.cc.
  _mongodb._tcp.test2.test.build.10gen.cc.  86400  IN SRV  27018  localhost.build.10gen.cc.
  _mongodb._tcp.test2.test.build.10gen.cc.  86400  IN SRV  27019  localhost.build.10gen.cc.
  _mongodb._tcp.test3.test.build.10gen.cc.  86400  IN SRV  27017  localhost.build.10gen.cc.
  _mongodb._tcp.test5.test.build.10gen.cc.  86400  IN SRV  27017  localhost.build.10gen.cc.
  _mongodb._tcp.test6.test.build.10gen.cc.  86400  IN SRV  27017  localhost.build.10gen.cc.
  _mongodb._tcp.test7.test.build.10gen.cc.  86400  IN SRV  27017  localhost.build.10gen.cc.
  _mongodb._tcp.test8.test.build.10gen.cc.  86400  IN SRV  27017  localhost.build.10gen.cc.
  _mongodb._tcp.test10.test.build.10gen.cc. 86400  IN SRV  27017  localhost.build.10gen.cc.
  _mongodb._tcp.test11.test.build.10gen.cc. 86400  IN SRV  27017  localhost.build.10gen.cc.

  Record                                    TTL    Class   Text
  test5.test.build.10gen.cc.                86400  IN TXT  "connectTimeoutMS=300000&socketTimeoutMS=300000"
  test6.test.build.10gen.cc.                86400  IN TXT  "connectTimeoutMS=200000"
  test6.test.build.10gen.cc.                86400  IN TXT  "socketTimeoutMS=200000"
  test7.test.build.10gen.cc.                86400  IN TXT  "readPreference=secondaryPreferred&readPreferenceTags=item:glass"
  test8.test.build.10gen.cc.                86400  IN TXT  "readPreference"
  test10.test.build.10gen.cc.               86400  IN TXT  "socketTimeoutMS=thisShouldBeAnInt"
  test11.test.build.10gen.cc.               86400  IN TXT  "connectTime" "outMS=150000" "&socketT" "imeoutMS" "=" "250000"

Note that ``test4`` is omitted deliberately to test what happens with no SRV
record. ``test9`` is missing because it was deleted during the development of
the tests.

In our tests we have used "localhost.build.10gen.cc" as the domain, and then
configured "localhost.build.10gen.cc" to resolve to 127.0.0.1.

You need to adapt the records shown above to replace ``build.10gen.cc`` with
your own domain name, and update the "uri" field in the YAML or JSON files in
this directory with the actual domain.

Test Format and Use
-------------------

These YAML and JSON files contain the following fields:

- ``uri``: a mongodb+srv connection string
- ``seeds``: the expected set of initial seeds discovered from the SRV record
- ``hosts``: the discovered topology's list of hosts once SDAM completes a scan
- ``options``: the parsed connection string options as discovered from URI and
  TXT records
- ``error``: indicates that the parsing of the URI, or the resolving or
  contents of the SRV or TXT records included errors.
- ``comment``: a comment to indicate why a test would fail.

For each file, create MongoClient initialized with the mongodb+srv connection
string. You SHOULD verify that the client's initial seed list matches the list of
seeds. You MUST verify that the set of ServerDescriptions in the client's
TopologyDescription eventually matches the list of hosts. You MUST verify that
the set of Connection String Options matches the client's parsed set. You MUST
verify that an error has been thrown if ``error`` is present.
