===================================
$out Aggregation Pipeline Operator
===================================

:Title: $out Aggregation Pipeline Operator
:Author: Emily Stolfo
:Status: Draft
:Type: Standards
:Last Modified: January 12, 2015

.. contents::

--------------------

Server Specification
--------------------

The aggregation framework is used to process data and return computed results. Up until release 2.6, the result from an aggregation was a single document. That single document had a 'result' field with an array containing the aggregation results. It was therefore subject to the BSON Document size limit, which is 16 megabytes at the time of release 2.6.

The **$out** pipeline option is new in 2.6 and allows you to specify the name of a collection to which the result of the aggregation should be written. With the **$out** option, there is no 16mb limit on the result set.
A new collection will be created if the one specified in **$out** does not already exist in the current database. Note that if the collection already exists, it will be dropped before written to.

The **$out** option is sometimes referred to as "unsharded **$out**" because it only allows results to be piped to a non-sharded collection. On the other hand, the collection on which the aggregation is performed can be sharded.

References:

* SERVER ticket: https://jira.mongodb.org/browse/SERVER-3253
* DRIVERS ticket: https://jira.mongodb.org/browse/DRIVERS-111

Server Return Value
''''''''''''''''''''
If the aggregation with **$out** specified completes successfully, the result will be a document in the following format::

    {
      "result" : [ ],
      "ok" : 1
    }

Fields
~~~~~~

**result**
  This field will be an empty array.

**ok**
  1 indicates successful aggregation, 0 indicates failure.
  
Notes and Restrictions
''''''''''''''''''''''

**1. The $out collection cannot be sharded**

The collection to which the aggregation is piped cannot be sharded. An error will be returned if an aggregation is attempted with **$out** specified as a sharded collection, or if that collection becomes sharded while the aggregation is running. The error is the following::


    aggregate failed: {
        "errmsg" : "exception: namespace 'records.users' is sharded so it can't be used for $out'",
        "code" : 17017,
        "ok" : 0
    }

**2. The $out option must be the last pipeline operator**

An ordered list is presumably already used to specify the pipeline passed to the aggregation. The **$out** option must be last in the list, otherwise, an error will be returned::


    aggregate failed: {
        "code" : 16991,
        "ok" : 0,
        "errmsg" : "exception: $out can only be the final stage in the pipeline"
    }

**3. Both the cursor option and $out option are specified**

If both a cursor and **$out** are requested, the results will be written to the collection specified but no cursor will be created (cursor id == 0)::

    {
      "cursor" : {
                   "id" : NumberLong(0),
                   "ns" : "records.users",
                   "firstBatch" : [ ]
            },
      "ok" : 1
    }


Driver API
----------

The **$out** option is provided just as any other pipeline operator is::

    pipeline = [{ $project: { uid: 1, email: 1 } }, { $out: "users" }]
    collection.aggregate(pipeline)


Driver return value
'''''''''''''''''''

The driver will return the raw document received from the server::

    {
      "result" : [ ],
      "ok" : 1
    }


The user can decide whether to instantiate a collection using the name specified in the **$out** operator.

Read preferences
''''''''''''''''

The only replica set member that can be used with **$out** is the primary because the operation writes to a collection. If a read preference other than primary is specified, the driver MUST route the aggregation to the primary and SHOULD log a warning that it has done so.

See DRIVERS ticket: https://jira.mongodb.org/browse/DRIVERS-84

If **$out** is not specified, the read preference will be respected.

Recall what your driver does with Map-Reduce if out is specified and it's not 'inline' while thinking about how to handle this scenario.

Reason for warning: Rerouting the aggregation with **$out** to the primary could present a problem such that the collection is written and then queried by the user with read preference non-primary before replication has completed. The user risks querying the collection before it is fully replicated.
