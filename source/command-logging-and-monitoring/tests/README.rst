.. role:: javascript(code)
  :language: javascript

==============================
Command Logging and Monitoring
==============================

.. contents::

--------

Testing
=======

Automated Tests
^^^^^^^^^^^^^^^
There are tests in the `Unified Test Format <../../unified-test-format/unified-test-format.rst>`__ for both logging and
monitoring in `/logging/unified </logging/unified>`_ and `/monitoring/unified </monitoring/unified>`_, respectively.


Prose Tests
~~~~~~~~~~~
Drivers MUST implement the following logging prose tests. These tests require the ability to capture log message data in a
structured form as described in the 
`Unified Test Format specification <../../unified-test-format/unified-test-format.rst#expectedLogMessage>`__.

*Test 1: Default truncation limit*

1. Configure logging with a minimum severity level of "debug" for the "command" component. Do not explicitly configure the max document length.
2. Construct an array ``docs`` containing the document ``{"x" : "y"}`` repeated 100 times.
3. Insert ``docs`` to a collection via ``insertMany``.
4. Inspect the resulting "command started" log message and assert that the "command" value is a string of length 1000.
5. Inspect the resulting "command succeeded" log message and assert that the "reply" value is a string of length <= 1000.
6. Run ``find()`` on the collection where the document was inserted.
7. Inspect the resulting "command succeeded" log message and assert that the reply is a string of length 1000.

*Test 2: Explicitly configured truncation limit*

1. Configure logging with a minimum severity level of "debug" for the "command" component. Set the max document length to 5 of (your driver's unit of choice for truncation).
2. Run the command ``{"hello": true}```.
3. Inspect the resulting "command started" log message and assert that the "command" value is a string of length 5.
4. Inspect the resulting "command succeeded" log message and assert that the "reply" value is a string of length 5.
5. If the driver attaches raw server responses to failures and can access these via log messages to assert on, run the command 
   ``{"notARealCommand": true}``. Inspect the resulting "command failed" log message and confirm that the server error is
   a string of length 5.

*Test 3: Truncation with multi-byte codepoints*

A specific test case is not provided here due to the allowed variations in truncation logic as well as varying extended JSON whitespace usage.
Drivers MUST write language-specific tests that confirm truncation of commands, replies, and (if applicable) server responses included in error
messages work as expected when the data being truncated includes multi-byte Unicode codepoints.
If the driver uses bytes as the unit for max document length, there also MUST be tests confirming that cases where the max byte length falls in
the middle of a multi-byte codepoint are handled gracefully.
