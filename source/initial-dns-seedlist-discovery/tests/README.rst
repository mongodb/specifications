====================================
Initial DNS Seedlist Discovery tests
====================================

This directory contains platform-independent tests that drivers can use
to prove their conformance to the Initial DNS Seedlist Discovery spec.

Test Setup
----------

Start a three-node replica set on localhost, on ports 27017, 27018, and 27019,
with replica set name "repl0".

There are two methods to provide the SRV records required for testing: either
mock them with the resolv_wrapper library and test only on Linux, or configure
the SRV records with a real name server.

If you choose the first method, build the `CWRAP resolv_wrapper library
<https://cwrap.org/resolv_wrapper.html>`_ and initialize its hosts file, for
example with this shell script:

.. code-block:: sh

  if [ ! -f resolv_wrapper_build/src/libresolv_wrapper.so ]; then
    curl -LO https://ftp.samba.org/pub/cwrap/resolv_wrapper-1.1.5.tar.gz
    tar xvf resolv_wrapper-1.1.5.tar.gz
    mkdir resolv_wrapper_build
    cd resolv_wrapper_build
    cmake ../resolv_wrapper-1.1.5
    make
    cd ..
  fi

  cat << EOF > hosts.txt
  SRV _mongodb._tcp.test1.test.build.10gen.cc localhost 27017
  SRV _mongodb._tcp.test1.test.build.10gen.cc localhost 27018
  SRV _mongodb._tcp.test2.test.build.10gen.cc localhost 27018
  SRV _mongodb._tcp.test2.test.build.10gen.cc localhost 27019
  SRV _mongodb._tcp.test3.test.build.10gen.cc localhost 27017
  EOF

  export LD_PRELOAD=`pwd`/resolv_wrapper_build/src/libresolv_wrapper.so
  export RESOLV_WRAPPER_HOSTS=hosts.txt

You can debug the library by exporting ``RESOLV_WRAPPER_DEBUGLEVEL=3``.

If you choose instead to configure a real name server with SRV records, adapt
the records shown above to your domain name, and update the "uri" field in the
YAML or JSON files in this directory with the actual domain.

Test Format and Use
-------------------

These YAML and JSON files contain the following fields:

- ``uri``: a mongodb+srv connection string
- ``seeds``: the expected set of initial seeds discovered from the SRV record
- ``hosts``: the discovered topology's list of hosts once SDAM completes a scan

For each file, create MongoClient initialized with the mongodb+srv connection
string. You SHOULD verify the client's initial seed list matches the list of
seeds. You MUST verify the set of ServerDescriptions in the client's
TopologyDescription eventually matches the list of hosts.
