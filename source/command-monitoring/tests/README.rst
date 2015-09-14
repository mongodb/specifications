.. role:: javascript(code)
  :language: javascript

==================
Command Monitoring
==================

.. contents::

--------

Testing
=======

Tests are provided in YML and JSON format to assert proper upconversion of commands.

Expectations
------------

Fake Placeholder Values
```````````````````````

When an attribute in an expectation contains the value {{"42"}}, {{42}} or {{""}}, this is a fake
placeholder value indicating that a special case MUST be tested that could not be
expressed in a YAML or JSON test. These cases are as follows:

Cursor Matching
^^^^^^^^^^^^^^^

When encountering a {{cursor}} or {{getMore}} value of {{"42"}} in a test, the driver MUST assert
that the values are equal to each other and greater than zero.

Errors
^^^^^^

For write errors, {{code}} values of {{42}} MUST assert that the value is present and
greater than zero. {{errmsg}} values of {{""}} MUST assert that the value is not empty
(a string of length greater than 1).

OK Values
^^^^^^^^^

The server is inconsistent on whether the ok values returned are integers or doubles so
for simplicity the tests specify all expected values as doubles. Server 'ok' values of
integers MUST be converted to doubles for comparison with the expected values.

Additional Values
`````````````````

The expected events provide the minimum data that is required and can be tested. It is
possible for more values to be present in the events, such as extra data provided when
using sharded clusters or ``nModified`` field in updates. The driver MUST assert the
expected data is present and also MUST allow for additional data to be present as well.
