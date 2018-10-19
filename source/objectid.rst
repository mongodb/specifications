.. role:: javascript(code)
  :language: javascript

===============
ObjectID format
===============

:Spec-ticket: WRITING-2823
:Title: ObjectID
:Authors: Derick Rethans
:Status: Draft
:Type: Standards
:Last Modified: 2018-10-11
:Version: 0.3
:Spec Lead: n/a
:Advisory Group: n/a
:Approver(s): Andy Schwerin, Bernie Hackett, Eliot Horowitz, Jeff Yemin, Jeremy Mikola, Matt Broadstone


.. contents::

--------

Abstract
========

This specification documents the format and data contents of ObjectID BSON
values that the drivers and the server generate when no field values have been
specified (e.g. creating an ObjectID BSON value when no _id field is present
in a document). It is primarily aimed to provide an alternative to the
historical use of the MD5 hashing algorithm for the machine information field
of the ObjectID, which is problematic when providing a FIPS compliant
implementation. It also documents existing best practices for the timestamp
and counter fields.

META
====

The keywords “MUST”, “MUST NOT”, “REQUIRED”, “SHALL”, “SHALL NOT”, “SHOULD”,
“SHOULD NOT”, “RECOMMENDED”, “MAY”, and “OPTIONAL” in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

The ObjectID_ BSON type is a 12-byte value consisting of three different
portions (fields):

- a 4-byte value representing the seconds since the Unix epoch in the highest
  order bytes,
- a 5-byte random number unique to a machine and process,
- a 3-byte counter, starting with a random value.

::

      4 byte timestamp    5 byte process unique   3 byte counter
    |<----------------->|<---------------------->|<------------>|
    [----|----|----|----|----|----|----|----|----|----|----|----]
    0                   4                   8                   12

.. _ObjectID: https://docs.mongodb.com/manual/reference/method/ObjectId/

Timestamp Field
---------------

This 4-byte big endian field represents the seconds since the Unix epoch (Jan
1st, 1970, midnight UTC). It is an ever increasing value that will have a
range until about Jan 7th, 2106.

Drivers MUST create ObjectIDs with this value representing the number of
seconds since the Unix epoch.

Drivers MUST interpret this value as an **unsigned 32-bit integer** when
conversions to language specific date/time values are created, and when
converting this to a timestamp.

Drivers SHOULD have an accessor method on an ObjectID class for obtaining the
timestamp value.

Random Value
------------

A 5-byte field consisting of a random value generated once per process.

Drivers MUST NOT have an accessor method on an ObjectID class for obtaining
this value.

Counter
-------

A 3-byte big endian counter.

This counter MUST be initialised to a random value when the driver is first
activated. After initialisation, the counter MUST be increased by 1 for every
ObjectID creation.

When the counter overflows (i.e., hits 16777215+1), the counter MUST be reset
to 0.

Drivers MUST NOT have an accessor method on an ObjectID class for obtaining
this value.

Test Plan
=========

Drivers MUST:

- Ensure that the Timestamp field is represented as an unsigned 32-bit
  representing the number of seconds since the Epoch for the Timestamp values:

  - ``0x00000000``: To match ``"Jan 1st, 1970 00:00:00 UTC"``
  - ``0x7FFFFFFF``: To match ``"Jan 19th, 2038 03:14:07 UTC"``
  - ``0x80000000``: To match ``"Jan 19th, 2038 03:14:08 UTC"``
  - ``0xFFFFFFFF``: To match ``"Feb 7th, 2106 06:28:15 UTC"``

- Ensure that the Counter field successfully overflows its sequence from
  ``0xFFFFFF`` to ``0x000000``.

Motivation for Change
=====================

Besides the specific exclusion of MD5 as an allowed hashing algorithm, the
information in this specification is meant to align the ObjectID generation
algorithm of both drivers and the server.

Design Rationale
================

**Timestamp:** The timestamp is a 32-bit **unsigned** integer, as it allows us
to extend the furthest date that the timestamp can represent from the year 2038
to 2106. There is no reason why MongoDB would generate a timestamp to mean a
date before 1970, as MongoDB did not exist back then.

**Random Value:** Originally, this field consisted of the Machine ID and
Process ID fields. There were numerous divergences between drivers due to
implementation choices, and the Machine ID field traditionally used the MD5
hashing algorithm which can't be used on FIPS compliant machines. In order to
allow for a similar behaviour among all drivers **and** the MongoDB Server,
these two fields have been collated together into a single 5-byte random value,
unique to a machine and process.

**Counter:** The counter makes it possible to have multiple ObjectIDs per
second, per server, and per process. As the counter can overflow, there is a
possibility of having duplicate ObjectIDs if you create more than 16 million
ObjectIDs per second in the same process on a single machine.

**Endianness:** The *Timestamp* and *Counter* are big endian because we can
then use ``memcmp`` to order ObjectIDs, and we want to ensure an increasing order.


Backwards Compatibility
=======================

This specification requires that the existing *Machine ID* and *Process ID*
fields are merged into a single 5-byte value. This will change the behaviour of
ObjectID generation, as well as the behaviour of drivers that currently have
getters and setters for the original *Machine ID* and *Process ID* fields.

Reference Implementation
========================

Currently there is no full reference implementation yet.

Changelog
=========

2018-10-11 — Version 0.3
	Clarify that the *Timestamp* and *Counter* fields are big endian, and add
	the reason why.

2018-07-02 — Version 0.2
	Replaced Machine ID and Process ID fields with a single 5-byte unique value

2018-05-22 — Version 0.1
	Initial Release
