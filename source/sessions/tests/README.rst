====================
Driver Session Tests
====================

.. contents::

----

Introduction
============

The YAML and JSON files in this directory are platform-independent tests that
drivers can use to prove their conformance to the Driver Sessions Spec. They are
designed with the intention of sharing most test-runner code with the
Transactions spec tests.

Several prose tests, which are not easily expressed in YAML, are also presented
in the Driver Sessions Spec. Those tests will need to be manually implemented
by each driver.

Test Format
===========

The same as the `Transactions Spec Test format
<../../transactions/tests/README.rst#test-format>`_.

Special Test Operations
```````````````````````

Certain operations that appear in the "operations" array do not correspond to
API methods but instead represent special test operations. Such operations are
defined on the "testRunner" object and are documented in the
`Transactions Spec Test
<../../transactions/tests/README.rst#special-test-operations>`_.
Additional, session test specific operations are documented here:

assertServerSessionPoolSize
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The "assertServerSessionPoolSize" operation instructs the test runner to
assert that the test's MongoClient has a ServerSession pool containing the
given number of ServerSessions::

      - name: assertServerSessionPoolSize
        object: testRunner
        arguments:
          size: 0

assertSessionDirty
~~~~~~~~~~~~~~~~~~

The "assertSessionDirty" operation instructs the test runner to assert that
the given session is marked dirty::

      - name: assertSessionDirty
        object: testRunner
        arguments:
          session: session0

assertSessionNotDirty
~~~~~~~~~~~~~~~~~~~~~

The "assertSessionNotDirty" operation instructs the test runner to assert that
the given session is *not* marked dirty::

      - name: assertSessionNotDirty
        object: testRunner
        arguments:
          session: session0

Changelog
=========

:2019-05-07: Initial version.
