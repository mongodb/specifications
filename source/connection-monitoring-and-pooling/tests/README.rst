.. role:: javascript(code)
  :language: javascript

========================================
Connection Monitoring and Pooling (CMaP)
========================================

.. contents::

--------

Introduction
============

The YAML and JSON files in this directory are platform-independent tests that
drivers can use to prove their conformance to the Connection Monitoring and Pooling (CPAM) Spec.

Several prose tests, which are not easily expressed in YAML, are also presented
in this file. Those tests will need to be manually implemented by each driver.

Common Test Format
================

Each YAML file has the following keys:

- ``version``: A version number indicating the expected format of the spec tests (current version = 1)
- ``style``: A string indicating what style of tests this file contains. Currently ``unit`` is the only valid value
- ``tests``: An array of tests that are to be run independently of each other

Unit Test Format:
=================

All Unit Tests have some of the following fields:

- ``description``: A text description of what the test is meant to assert
- ``operations``: A list of operations to perform. Each operation has some of the following fields:

  - ``command``: A string describing which command to issue.
  - ``args``: An array of arguments to pass to the command
  - ``thread``: The name of the thread in which to run this command. If not specified, runs in the default thread
  - ``object``: For some command, specifies the object on which to run the command
  - ``returnTo``: For some commands, specifies what to name the return value of the command

- ``error``: Indicates that the main thread is expected to error during this test. Subfields (like ``message``) indicate what error is expected
- ``events``: An array of all connection monitoring events expected to occur while running ``operations``
- ``ignore``: An array of event names to ignore

Valid Unit Test Operations are the following:

- ``start(name)``: Starts a new thread named ``name``
- ``wait(x)``: Sleep the current thread for x milliseconds
- ``waitFor(name, suppressError?)``: wait for thread ``name`` to finish executing. If ``suppressError`` is true, ignore any errors coming from that thread, otherwise propagate the errors to the main thread.
- ``returnTo = createPool(options)``: creates and returns a new Connection Pool with the specified options. ``enableConnectionMonitoring`` MUST be set to true, and any connection events MUST be captured
- ``returnTo = object.acquire()``: call ``acquire`` on Pool ``object``, returning the acquired connection
- ``object.release(connection, force?)``: call ``release`` on Pool ``object``, passing in connection and optional force flag
- ``object.clear()``: call ``clear`` on Pool ``object``
- ``object.close()``: call ``close`` on Pool ``object``

Spec Test Context References
============================

If an any point a value in a test is of the form ``{ $$ref: string[] }``, that value is considered a Context Reference. Context References are resolved by replacing the value with the current value of ``context[...$$ref]``

The definition of RESOLVE in the Spec Test Runner is as follows:

- RESOLVE takes two value, ``context`` and ``unresolved``
- Notation is ``RESOLVE(context, unresolved)``

Pseudocode implementation of ``RESOLVE(context, unresolved)``:

::

  if unresolved is a JSON array:
    resolved = []
    for every idk/value in unresolved:
      resolved[idx] = RESOLVE(context, value)
    return resolved
  else if unresolved is a JSON object:
    if unresolved["$$ref""] is an array:
      resolved = context
      for every value in unresolved:
        resolved = resolved[value]
      return resolved
    else:
      resolved = {}
      for every key/value in unresolved:
        resolved[key] = RESOLVE(context, value)
      return resolved
  else:
    return unresolved


Examples: if ``context = { foo: 'bar', fizz: 12, buzz: { spam: 'eggs' } }``

- ``RESOLVE(context, { $$ref: [ "foo" ] })`` equals ``"bar"``
- ``RESOLVE(context, { $$ref: [ "buzz", "spam" ] })`` equals ``"eggs"``
- ``RESOLVE(context, { foo: { $$ref : ["fizz"] } })`` equals ``{ foo: 12 }``

Spec Test Match Function
========================

The definition of MATCH or MATCHES in the Spec Test Runner is as follows:

- MATCH takes two values, ``expected`` and ``actual``
- Notation is "Assert [actual] MATCHES [expected]
- Assertion passes if ``expected`` is a subset of ``actual``, with the values ``42`` and ``"42"`` acting as placeholders for "any value"

Pseudocode implementation of ``actual`` MATCHES ``expected``:

::
  
  If expected is "42" or 42:
    Assert that actual exists (is not null or undefined)
  Else:
    Assert that actual is of the same JSON type as expected
    If expected is a JSON array:
      For every idx/value in expected:
        Assert that actual[idx] MATCHES value
    Else if expected is a JSON object:
      For every key/value in expected
        Assert that actual[key] MATCHES value
    Else:
      Assert that expected equals actual

Unit Test Runner:
=================

For the unit tests, the behavior of a Connection is irrelevant beyond the need to asserting ``connection.id`` and ``connection.generation``. Drivers MAY use a mock connection class for testing the pool behavior in unit tests

For each YAML file with ``style: unit``, for each element in ``tests``:

- Initialize an empty dictionary ``context``
- Execute each ``operation`` in ``operations``

  - If a ``thread`` is specified, execute in that corresponding thread. Otherwise, execute in the main thread.
  - If an ``object`` is specified, execute the operation against ``context[object]``
  - If a ``returnTo`` is specified, set ``context[returnTo]`` to the return value of the operation
  - If ``args`` are specified:

    - For every ``idx``/``arg`` in ``args``:
    
      - ``args[i] = RESOLVE(context, arg)``

    - Pass ``args`` into the operation

- Wait for the main thread to finish executing all of its operations
- If ``error`` is presented

  - Assert that an actual error ``actualError`` was thrown by the main thread
  - Assert that ``actualError`` MATCHES ``RESOLVE(context, error)``

- Else: 

  - Assert that no errors were thrown by the main thread

- ``expectedEvents = []``
- for every ``idx/value`` in ``events``: 

  - ``expectedEvents[idx] = RESOLVE(context, value)``

- calculate ``actualEvents`` as every Connection Event emitted whose ``type`` is not in ``ignore``
- if ``expectedEvents`` is not empty, then for every (``expectedEvent``, ``i``) in ``expectedEvents``

  - Assert that ``actualEvents[i]`` exists
  - Assert that ``actualEvents[i]`` MATCHES ``expectedEvent``
