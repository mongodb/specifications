=======
Logging
=======

:Spec Title: Logging
:Spec Version: 1.0.0
:Author: Kaitlin Mahar
:Spec Lead: Jeff Yemin
:Advisors: Andreas Braun, James Kovacs, Rachelle Palmer, Isabella Siu
:Status: Draft
:Type: Standards
:Minimum Server Version: N/A
:Last Modified: 2020-10-14

.. contents::

--------

Abstract
========

This specification defines requirements for drivers' logging architecture and
behavior.

META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`__.

Specification
=============

Terms
-----

Structured/Unstructured Logging
  *Structured* logging refers to producing log messages in a structured format,
  i.e. a series of key-value pairs, which can be converted to external
  representations such as JSON. *Unstructured* logging refers to producing
  string log messages.

Implementation Requirements
---------------------------
Drivers SHOULD implement support for logging in a manner that is idiomatic for
their language and ecosystem. 

At minimum, drivers MUST provide support for all of the following requirements,
and MUST support them in a manner that **does not require any changes to an
application's source code**, and in the case of compiled languages, **does not
require recompilation**. Drivers SHOULD take advantage of built-in support for
such dynamic configuration within logging frameworks or their language ecosystem
if available. If not available, drivers MUST support dynamic configuration via
the fallback implementation methods defined below.

For languages/ecosystems where libraries depend on only a logging interface (for
example, the Java driver and `SLF4J <ttp://www.slf4j.org/>`__ and application
developers must choose a log handler, the requirements MAY be considered
satisfied if there is a log handler available in the ecosystem which satisfies
the requirements in the required manner (i.e. without code changes or
recompilation).

.. list-table::
   :header-rows: 1
   :widths: 1 1

   * - Requirement
     - Fallback Implementation Method

   * - Support for enabling logging and specifying the minimum severity level
       for emitted messages for each `component <Components_>`_.
     - Support configuration by specifying environment variables corresponding
       to each `component <Components_>`_, as well as by specifying the
       environment variable ``MONGODB_LOG_ALL``.

       Each of these variables may be set to any of the
       `severity levels <Severity Levels_>`_ to indicate the minimum severity
       level at which messages should be emitted for the corresponding component
       (or in the case of ``MONGODB_LOG_ALL``, all components).

       Providing a value for ``MONGODB_LOG_ALL`` is equivalent to providing
       that value for all of the per-component variables.

       If ``MONGODB_LOG_ALL`` is specified in addition to one or more
       component variables, the component variable's value MUST be used to
       determine the minimum level for that component.

       E.g. if the user sets 
       ``MONGODB_LOG_ALL=debug MONGODB_LOG_COMMAND=info``, the command
       component is set to ``info`` level and all other components are set to
       ``debug`` level.

       These variables may also be set to "off" (case-insensitive) to indicate
       that nothing should be logged.

       The default is to not log anything.

       If a variable is set to an invalid value, it MUST be treated as if it
       were not specified at all.

   * - Support for configuring where log messages should be output, including stderr,
       stdout, and an output file with a configurable path.
     - Support configuration via the environment variable ``MONGODB_LOG_PATH``.
       
       If the value is "stdout" or "stderr" (case-insensitive), log to the
       corresponding output stream.
       
       Else, log to a file at the specified path. If the file already exists,
       it MUST be appended to.

       If the variable is not provided, log to stderr.

   * - Support for configuring the maximum length for extended JSON documents
       in log messages, with a default max length of 1000 characters.
     - Support configuration via the environment variable
       ``MONGODB_LOG_MAX_DOCUMENT_LENGTH``.
      
       When unspecified, any document longer than 1000 characters MUST be
       truncated to 1000 characters.

       When set to an integer value, any document longer than that value MUST
       be truncated to that number of characters.

       When set to the string "unlimited", documents MUST be included in full.

       If the variable is set to an invalid value, it MUST be treated as if it
       were not specified at all.

Drivers MAY additionally provide support for enabling and configuring logging
via API in a manner that does require code changes, and MAY support additional
configuration options if it is idiomatic to do so.

Components
----------
As noted above, drivers must support configuring logging verbosity on a
per-component level. The below components currently exist and correspond to the
listed specifications; this list is expected to grow over time.

.. list-table::
   :header-rows: 1
   :widths: 1 1 1

   * - Component Name
     - Specification(s)
     - Environment Variable

   * - Command
     - `Command Monitoring <../command-monitoring/command-monitoring.rst>`__
     - ``MONGODB_LOG_COMMAND``

   * - SDAM
     - `Server Discovery and Monitoring
       <../server-discovery-and-monitoring/server-discovery-and-monitoring.rst>`__
     - ``MONGODB_LOG_SDAM``

   * - Server Selection
     - `Server Selection <../server-selection/server-selection.rst>`__
     - ``MONGODB_LOG_SERVER_SELECTION``

   * - Connection
     - `Connection Monitoring and Pooling
       <../connection-monitoring-and-pooling/connection-monitoring-and-pooling.rst>`__
     - ``MONGODB_LOG_CONNECTION``

Severity Levels
---------------
Driver specifications defining log messages may use any of the following levels,
inspired by the Syslog Protocol as described in `RFC 5424
<https://tools.ietf.org/html/rfc5424>`__:

.. list-table::
   :header-rows: 1
   :widths: 1 1 1 1

   * - Code
     - Level Name
     - Meaning
     - Environment Variable value (case-insensitive)

   * - 0
     - Emergency
     - N/A
     - emergency

   * - 1
     - Alert
     - N/A
     - alert

   * - 2
     - Critical
     - N/A
     - critical

   * - 3
     - Error
     - Any error that we are unable to report to the user via API.
     - error

   * - 4
     - Warning
     - Indicates a situation where undesirable application behavior may occur.
       Example: The driver ignores an unrecognized option in a URI.
     - warn

   * - 5
     - Notice
     - Indicates an event that is unusual but not problematic. Example: a
       change stream is automatically resumed.
     - notice

   * - 6
     - Informational
     - High-level information about normal driver behavior. Example:
       ```MongoClient`` creation or close.
     - info

   * - 7
     - Debug
     - Detailed information that may be helpful when debugging the application.
       Example: A command starting.
     - debug

   * - 8
     - Trace
     - Very fine-grained details related to logic flow. Example: entering and
       exiting function bodies.
     - trace

Note that the Emergency, Alert, and Critical levels have been intentionally left
undefined. At the time of writing this specification, we do not expect any
driver specifications to need to log at these levels, but we have included them
in the list of permitted levels for consistency with Syslog and so that they
may be used in the future if needed.

Not all logging frameworks will necessarily support all of these levels. If an
equivalent level is not available, drivers SHOULD emit messages for that level
at the closest less severe level if one is available, or the closest more
severe level otherwise. For example, if an Informational level is not available
and Debug is, Informational messages should be emitted at Debug level. If a
Trace level is not available, Debug should be used.

Structured Logging
------------------
If structured logging is idiomatic for the driver's language/ecosystem, the
driver SHOULD produce structured log messages. Otherwise, the driver SHOULD
produce unstructured log messages. All structured log messages MUST use the
exact key names used in specifications.

Test Plan
---------
Tests for logging behavior are defined in each corresponding specification.

Motivation for Change
---------------------
A common complaint from our support team is that they don't know how to easily
get debugging information from drivers. Some drivers provide debug logging, but
others do not. For drivers that do provide it, the log messages produced and
the mechanisms for enabling debug logging are inconsistent.

Although users can implement their own debug logging support via existing driver
events (SDAM, APM, etc), this requires code changes. It is often difficult to
quickly implement and deploy such changes in production at the time they are
needed, and to remove the changes afterward. Additionally, there are useful
scenarios to log that do not correspond to existing events.

Standardizing on debug log messages that drivers produce and how to
enable/configure logging will provide TSEs, CEs, and MongoDB users an easier
way to get debugging information out of our drivers, facilitating support of
drivers for our internal teams, and improve our documentation around
troubleshooting.

Design Rationale
----------------

**Truncation of large documents**: We considered a number of approaches for
dealing with documents of potentially very large size in log messages, e.g.
command documents, including 1) always logging the full document, 2) only
logging documents of potentially very large size when the user opts in, and
3) truncating large documents by default, but allowing the user to opt-in to
logging more of the data. We chose the third option as we felt it struck the best
balance between concerns around readability and usability of log messages. In
the case where data is sufficiently small, the default behavior will show the
user the full data. In the case where data is large, the user will receive a 
readable message with truncated data, but have the option to see the full data.

Reference Implementation
------------------------
TODO: add links here.
Reference implementations are available in Go, C, and Swift.

Future Work
-----------
Following the completion of this specification, a number of other driver
specifications will be updated to include relevant log messages.

Q&A
---
**Q**: The server produces structured log messages as of 4.4. Why doesn't this
specification require structured logging to match the server?

**A**: The logging mechanisms of choice for some language ecosystems don't
support it, so we can't require it.

Change Log
==========
2020-10-14: 
- Shorten environment variable names by prefixing with ``MONGODB_LOG`` rather than ``MONGODB_LOGGING``.
- Remove "off" from table of log levels; describe its behavior in section on environment variables instead.
