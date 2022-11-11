=======
Logging
=======

:Title: Logging
:Status: Accepted
:Minimum Server Version: N/A

.. contents::

--------

Abstract
========
This specification defines requirements for drivers' logging configuration and behavior. 


META
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”,
“SHOULD”, “SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this
document are to be interpreted as described in `RFC 2119
<https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

-----
Terms
-----
Structured logging
    Structured logging refers to producing log messages in a structured format, i.e. a series of
    key-value pairs, which can be converted to external formats such as JSON.

Unstructured logging
    Unstructured logging refers to producing string log messages which embed all attached
    information within that string.

---------------------------
Implementation requirements
---------------------------
Drivers SHOULD implement support for logging in a manner that is idiomatic for their language and
ecosystem.


Minimizing Required Code Changes
--------------------------------
If possible, drivers SHOULD support the following configuration requirements in a manner that does
not require any changes to an application's source code, and in the case of compiled languages,
does not require recompilation.
However, if that is impossible to do without conflicting with idiomatic logging patterns for the
language ecosystem, it is acceptable for a driver to require minimal changes to enable logging,
such as recompiling with a feature flag specified, or passing a logging configuration to a 
``MongoClient`` constructor. In that case, drivers SHOULD strive to minimize the amount of code
change needed.

Drivers SHOULD take advantage of built-in support for logging configuration within logging
frameworks or their language ecosystem if available. If unavailable, drivers MUST support
configuration via the listed fallback implementation methods.

In addition to supporting configuration without code changes/recompilation, drivers MAY
additionally provide support for enabling and configuring logging via their API in a
manner that does require code changes, and MAY support additional configuration options beyond
those defined in this specification.

For languages/ecosystems where libraries depend on only a logging interface (for example, the Java
driver and `SLF4J <https://www.slf4j.org/>`_) and application developers must choose a log handler,
the requirements MAY be considered satisfied if there is a log handler available in the ecosystem
which users can select that satisfies the requirements. Similarly, the requirements MAY be
considered satisfied if the driver provides an integration with a logging framework which satisfies
the requirements.

Per-Component Configuration of Log Levels
-----------------------------------------
Drivers MUST support enabling logging and specifying the minimum severity level for emitted messages
on a per-component level, for each component defined below in the `Components`_ section.
  
  **Fallback implementation method**: Support configuration via environment variables 
  corresponding to each component, as defined in `Components`_, as well as via the
  environment variable ``MONGODB_LOG_ALL``.

  Each of these variables may be set to any of the values defined below in `Log Severity Levels`_
  to indicate the minimum severity level at which messages should be emitted for the
  corresponding component, or in the case of ``MONGODB_LOG_ALL``, all components. Setting a value
  for ``MONGODB_LOG_ALL`` is equivalent to setting that value for all of the per-component
  variables.

  If ``MONGODB_LOG_ALL`` is specified in addition to one or more component variables, the
  component variable(s) MUST take precedence.

  The default is to not log anything. 

  If a variable is set to an invalid value, it MUST be treated as if it were not specified at all.

Configurable Log Destination
----------------------------
Drivers MUST support configuring where log messages should be output, including the options: stdout,
stderr, output file (path MUST be configurable).

    **Fallback implementation method**: If the environment variable ``MONGODB_LOG_PATH`` is provided:
     - If the value is "stdout" (case-insensitive), log to stdout.
     - If the value is "stderr" (case-insensitive), log to stderr.
     - Else, log to a file at the specified path. If the file already exists, it MUST be appended to.

    If the variable is not provided, the driver MUST log to stderr.

Configurable Max Document Length
--------------------------------
Drivers MUST support configuring the maximum logged length for extended JSON documents in log messages.
The unit here is flexible and can be bytes, Unicode code points, code units, or graphemes, depending on
what a driver is able to accomplish with its language's string APIs. The default max length is 1000 of
whichever unit is selected.
If the chosen unit is anything other than a Unicode code point, the driver MUST ensure that it
gracefully handles cases where the truncation length falls mid code point, by either rounding the length
up or down to the closest code point boundary or using the Unicode replacement character, to avoid
producing invalid Unicode data.
Drivers MUST implement truncation naively by simply truncating the output at the required length; i.e.
do not attempt to implement truncation such that the output is still valid JSON.
Truncated extended JSON MUST have a trailing ellipsis ``...`` appended to indicate to the user that
truncation occurred. The ellipsis MUST NOT count toward the the max length.

    **Fallback Implementation method**: Environment variable ``MONGOB_LOG_MAX_DOCUMENT_LENGTH``.
    When unspecified, any extended JSON representation of a document which is longer than the
    default max length MUST be truncated to that length. 
    When set to an integer value, any extended JSON document longer than that value MUST be
    truncated to that length.
    If the variable is set to an invalid value, it MUST be treated as if it were not specified at
    all.

Components
----------
Drivers MUST support configuring minimum log severity levels on a per-component level. The below
components currently exist and correspond to the listed specifications. This list is expected to
grow over time as logging is added to more specifications.

Drivers SHOULD specify the component names in whatever the idiomatic way is for their language.
For example, the Java command component could be named ``org.mongodb.driver.protocol.command``.

Drivers MAY define additional language-specific components in addition to these for any
driver-specific messages they produce.

.. list-table::
   :header-rows: 1
   :widths: 1 1 1

   * - Component Name
     - Specification(s)
     - Environment Variable

   * - command
     - `Command Monitoring <../command-monitoring/command-monitoring.rst>`__
     - ``MONGODB_LOG_COMMAND``

   * - topology
     - `Server Discovery and Monitoring
       <../server-discovery-and-monitoring/server-discovery-and-monitoring.rst>`__
     - ``MONGODB_LOG_TOPOLOGY``

   * - serverSelection
     - `Server Selection <../server-selection/server-selection.rst>`__
     - ``MONGODB_LOG_SERVER_SELECTION``

   * - connection
     - `Connection Monitoring and Pooling
       <../connection-monitoring-and-pooling/connection-monitoring-and-pooling.rst>`__
     - ``MONGODB_LOG_CONNECTION``


Log Severity Levels
-------------------

Driver specifications defining log messages MUST use log levels from the following list, inspired
by the Syslog Protocol as described in `RFC 5424 <https://www.rfc-editor.org/rfc/rfc5424/>`_:

.. list-table::
   :header-rows: 1

   * - Code
     - Level Name
     - Meaning
     - Environment Variable value (case-insensitive)

   * - \-
     - Off
     - Nothing is logged.
     - ``off``

   * - 0
     - Emergency
     - \-
     - ``emergency``

   * - 1
     - Alert
     - \-
     - ``alert``

   * - 2
     - Critical
     - \-
     - ``critical``

   * - 3
     - Error
     - Any error that we are unable to report to the user via driver API.
     - ``error``

   * - 4
     - Warning
     - Indicates a situation where undesirable application behavior may occur.
       Example: The driver ignores an unrecognized option in a connection string.
     - ``warn``

   * - 5
     - Notice
     - Indicates an event that is unusual but not problematic. Example: a
       change stream is automatically resumed.
     - ``notice``

   * - 6
     - Informational
     - High-level information about normal driver behavior. Example:
       ``MongoClient`` creation or close.
     - ``info``

   * - 7
     - Debug
     - Detailed information that may be helpful when debugging an application.
       Example: A command starting.
     - ``debug``

   * - 8
     - Trace
     - Very fine-grained details related to logic flow. Example: entering and
       exiting function bodies.
     - ``trace``

Note that the Emergency, Alert, and Critical levels have been intentionally left undefined. At the
time of writing this specification, we do not expect any driver specifications to need to log at
these levels, but we have included them in the list of permitted levels for consistency with Syslog.

The levels above are defined in order from most to least severe. Not all logging frameworks will
necessarily support all of these levels. If an equivalent level is not available, drivers MUST emit
messages for that level at the closest, less severe level if one is available, or the closest more
severe level otherwise.

For example:

- If an Informational level is not available and Debug is, messages defined as Informational in a
  specification MUST be emitted at Debug level.
- If a Trace level is not available, Trace messages MUST be omitted at Debug level.

Structured versus Unstructured Logging
--------------------------------------
If structured logging is available in and idiomatic for the driver's language/ecosystem, the driver
SHOULD produce structured log messages. Note that some ecosystems with structured logging support
may also have support available to convert structured output to traditional unstructured messages
for users who want it (for example, the
`log feature <https://docs.rs/tracing/latest/tracing/#emitting-log-records>`_ in Rust's
`tracing <https://docs.rs/tracing/latest/tracing/>`_ crate). If such support is available, drivers
SHOULD utilize it to support both types of logging.

Note that drivers implementing unstructured logging MUST still support some internal way to intercept
the data contained in messages in a structured form, as this is required to implement the unified tests
for logging conformance.. See the `unified test format specification 
<../unified-test-format/unified-test-format.rst#expectedLogMessage>`_ for details.

Representing Documents in Log Messages
--------------------------------------
BSON documents MUST be represented in relaxed extended JSON when they appear in log messages to
improve readability.

Representing Errors in Log Messages
-----------------------------------
Drivers MAY represent errors in log messages in whatever format is idiomatic for their language and
existing error types. For example, if a driver's error classes have existing ``toString()``
implementations, those MAY be used. Alternatively, if a driver emits structured log messages, a
structured format containing error data could be used. Any information which a driver reports via
its error classes MUST be included in the log representations. 
Note that if the driver includes full server responses in its errors these MUST be truncated in
accordance with the max document length option.

Omitting Null Values from Log Messages
--------------------------------------
Some log messages will include fields that are only present under particular circumstances, for example
on certain server versions. When such a field is not present:

- If the driver does structured logging, the field MUST be omitted from the message altogether, i.e. the field 
  MUST not be present with an explicit null value.
- If the driver does unstructured logging, the corresponding segment of the message string MUST be omitted
  altogether.

Performance Considerations
--------------------------
The computation required to generate certain log messages can be significant, e.g. if extended
JSON serialization is required. If possible, drivers SHOULD check whether a log message would
actually be emitted and consumed based on the users' configuration before doing such computation.
For example, this can be checked in Rust via `log::log_enabled 
<https://docs.rs/log/latest/log/macro.log_enabled.html>`_. 

Drivers SHOULD optimize extended JSON generation to avoid generating JSON strings longer than will
be emitted, such that the complexity is O(N) where N = ``<max document length>``, rather than
N = ``<actual document length>``.

Standard Naming in Structured Log Messages
------------------------------------------
Driver specifications typically allow for language-appropriate naming variations, e.g. using
snakecase or camelcase to name a property. However, for log messages, drivers doing structured
logging MUST use the exact names and casing specified for the names of fields included in messages.
This will be easier for our support team since the names will be consistent across languages, and
will simplify writing language-agnostic tooling to search through and parse structured logs.

Including Timestamps in Log Messages
------------------------------------
Drivers MAY add timestamps to their log messages if one will not be added automatically by the logging framework(s) they use.

Test Plan
=========
Tests for logging behavior are defined in each corresponding specification. The  `unified test
runner specification <../unified-test-format/unified-test-format.rst>`_
has support for specifying logging expectations in tests.

Motivation for Change
=====================
A common complaint from our support team is that they don't know how to easily get debugging
information from drivers. Some drivers provide debug logging, but others do not. For drivers that
do provide it, the log messages produced and the mechanisms for enabling debug logging are
inconsistent.

Although users can implement their own debug logging support via existing driver events (SDAM,
APM, etc), this requires code changes. It is often difficult to quickly implement and deploy such
changes in production at the time they are needed, and to remove the changes afterward.
Additionally, there are useful scenarios to log that do not correspond to existing events.
Standardizing on debug log messages that drivers produce and how to enable/configure logging will
provide TSEs, CEs, and MongoDB users an easier way to get debugging information out of our drivers,
facilitate support of drivers for our internal teams, and improve our documentation around
troubleshooting.

Design Rationale
================

-----------------------------
Truncation of large documents
-----------------------------

1. Why have an option? 
    We considered a number of approaches for dealing with documents of potentially very large size
    in log messages, e.g. command documents, including 1) always logging the full document, 2) only
    logging documents with the potential to be large when the user opts in, and 3) truncating large
    documents by default, but allowing the user to adjust the maximum length logged. We chose the
    third option as we felt it struck the best balance between concerns around readability and
    usability of log messages. In the case where data is sufficiently small, the default behavior
    will show the user the full data. In the case where data is large, the user will receive a
    readable message with truncated data, but have the option to see more or all of the data.

2. Why are the units for max document length flexible? 
    String APIs vary across languages, and not all drivers will be able to easily and efficiently
    truncate strings in the same exact manner. The important thing is that the option exists and
    that its default value is reasonable, and for all possible unit choices (byte, code point, 
    code unit, or grapheme) we felt 1000 was a reasonable default. See
    `here <https://exploringjs.com/impatient-js/ch_unicode.html>`_ for a helpful primer on related
    Unicode concepts.

3. Why do we implement naive truncation rather than truncating the JSON so it is still valid?
    Designing and implementing a truncation algorithm for JSON that outputs valid JSON, but fits
    in as much of the original JSON as possible, would be non-trivial. The server team wrote an
    entire separate truncation design document when they implemented this for their log messages.
    This is more of a necessity for the server where the entire log message is JSON, but we don't
    know if parsing the documents included in log messages is something that users will actually
    need to do. Furthermore, any users who want parseable documents have an escape hatch to do so:
    they can set the max document length to a very large value. If we hear of use cases in the future
    for parsing the documents in log messages, we could make an additive change to this specification
    to permit a smarter truncation algorithm.

--------------------------------------
Structured versus Unstructured Logging
--------------------------------------
The MongoDB server produces structured logs as of 4.4, so it seems natural that MongoDB drivers
might too. However, structured logging is not idiomatic or common in some language ecosystems,
so we have chosen not to require it.

--------------------------------------
Omitting Null Values from Log Messages
--------------------------------------
We considered alternatives such as allowing, or requiring, drivers to explicitly include null values
in log messages. While this might make it easier to identify cases where a value is unexpectedly null,
we decided against it because there are a number of values that will often be null, or even always
be null for certain applications (e.g. ``serviceId`` when not connected to a load-balanced topology)
and their inclusion may confuse users and lead them to think the null value is meaningful.
Additionally, always including null values would increase the size of log messages. The omission of
null values is left to the drivers' discretion for any driver-specific logs not covered by common
specification components. 

Backwards Compatibility
=======================
This specification takes the stance that the contents of log messages (both structured and
unstructured) are *not* covered by semantic versioning, but that logging components *are*, since
changing the name of a component or removing a component altogether has the potential to break user
logging configuration and cause users to silently miss log messages.

As a result, any drivers that already support logging should be free to update the messages they
log to match those defined in various specifications. However, drivers should take care to avoid
removing or renaming existing logging components except in major version releases.

Since this specification defines no particular API, drivers are free to keep any existing
programmatic APIs they have for configuring logging. If such APIs are incompatible with the logging
specification requirements (for example, the driver defines its own set of log levels in a public
type, which do not match the spec-defined levels), changes to match the specification should be
staged in via semantic versioning.

Reference Implementation
========================
Links to be added once Rust and C# implementations have been merged.

Security Implication
====================
Drivers must take care to avoid exposing sensitive information (e.g. authentication credentials) in
log messages. It will be up to each individual specification that defines log messages to define
which information should be redacted and add tests confirming its redaction.

Future work
===========

-------------------------
Additional Log Components
-------------------------
Additional log components may be added as logging is added to more specifications.

-----------------------------------------------------
Preventing Recursion When Using MongoDB as a Log Sink
-----------------------------------------------------
If a user chooses to store log messages produced by a driver in MongoDB, it may be possible for
them to end up recursing infinitely if each write to store a log message generates additional
log messages. This has historically not been an issue in drivers that already produce log messages,
or with the command monitoring API, but if users start to run into this issue, we could try to
address it at the specification level by e.g. requiring drivers to support disabling logging on
individual clients or for particular namespaces.


Changelog
=========

:2022-10-26: Allow drivers to add timestamps to log messages.
:2022-11-10: Clarify driver-specific null omission.
