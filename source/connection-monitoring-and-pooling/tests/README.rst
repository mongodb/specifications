.. role:: javascript(code)
  :language: javascript

========================================
Connection Monitoring and Pooling (CMAP)
========================================

.. contents::

--------

Introduction
============
Drivers MUST implement all of the following types of CMAP tests:

* Pool unit and integration tests as described in `cmap-format/README.rst <./cmap-format/README.rst>`__
* Integration tests written in the `Unified Test Format <../../unified-test-format/unified-test-format.rst>`_ located in the `/unified <./unified>`_ directory
* Pool prose tests as described below in `Prose Tests`_

Prose Tests
===========

The following tests have not yet been automated, but MUST still be tested:

#. All ConnectionPoolOptions MUST be specified at the MongoClient level
#. All ConnectionPoolOptions MUST be the same for all pools created by a MongoClient
#. A user MUST be able to specify all ConnectionPoolOptions via a URI string
#. A user MUST be able to subscribe to Connection Monitoring Events in a manner idiomatic to their language and driver

