# ODM Performance Benchmarking

- Status: In progress
- Minimum Server Version: N/A

## Abstract

This document describes a standard benchmarking suite for MongoDB ODMs (Object Document Mappers). Much of the structure
is taken from the existing MongoDB driver benchmarking suite for consistency and readability.

## Overview

### Name and purpose

ODM performance will be measured by the MongoDB ODM Performance Benchmark. It will provide both "horizontal" insights
into how individual ODM performance evolves over time and two types of "vertical" insights: the relative performance of
different ODMs, and the relative performance of ODMs and their associated language drivers.

We expect substantial performance differences between ODMs based on both their language families (e.g. static vs.
dynamic or compiled vs. virtual-machine-based) as well as their inherent design (e.g. web frameworks such as Django vs.
application-agnostic such as Mongoose). However we still expect "vertical" comparison within families of ODMs to expose
outlier behavior that can be optimized away.

### Task Hierarchy

The benchmark suite consists of multiple groups of small, independent benchmarks. This allows us to better isolate areas
within ODMs that are faster or slower.

- Flat models -- reading and writing flat models of various sizes, to explore basic operation efficiency
- Nested models -- reading and writing nested models of various sizes, to explore basic operation efficiency for complex
    data
- Joins -- performing operations that involve joins (if supported), to explore $lookup efficiency

### Measurement

In addition to latency data, all benchmark tasks will be measured in terms of "megabytes/second" (MB/s) of documents
processed, with higher scores being better. (In this document, "megabyte" refers to the SI decimal unit, i.e. 1,000,000
bytes.) This makes cross-benchmark comparisons easier.

To avoid various types of measurement skew, tasks will be measured over numerous iterations. Each iteration will have a
number of operations performed per iteration that depends on the task being benchmarked. The final score for a task will
be the median score of the iterations. A range of percentiles will also be recorded for diagnostic analysis.

### Data sets

Data sets will vary by task. In some cases, they will be synthetically generated models inserted repeatedly to construct
an overall corpus of models. In other cases, data sets will be synthetic line-delimited JSON files or mock binary files
to be constructed by the ODM into the appropriate model.

### Versioning

The MongoDB ODM Performance Benchmark will have vX.Y versioning. Minor updates and clarifications will increment "Y" and
should have little impact on score comparison. Major changes, such as task modifications, MongoDB version tested
against, or hardware used, will increment "X" to indicate that older version scores are unlikely to be comparable.

## Benchmark execution phases and measurement

All benchmark tasks will be conducted via a number of iterations. Each iteration will be timed and will generally
include a large number of individual ODM operations.

The measurement is broken up this way to better isolate the benchmark from external volatility. If we consider the
problem of benchmarking an operation over many iterations, such as 100,000 model insertions, we want to avoid two
extreme forms of measurement:

- measuring a single insertion 100,000 times -- in this case, the timing code is likely to be a greater proportion of
    executed code, which could routinely evict the insertion code from CPU caches or mislead a JIT optimizer and throw
    off results
- measuring 100,000 insertions one time -- in this case, the longer the timer runs, the higher the likelihood that an
    external event occurs that affects the time of the run

Therefore, we choose a middle ground:

- measuring the same 1000 insertions over 100 iterations -- each timing run includes enough operations that insertion
    code dominates timing code; unusual system events are likely to affect only a fraction of the 100 timing
    measurements

With 100 timings of inserting the same 1000 models, we build up a statistical distribution of the operation timing,
allowing a more robust estimate of performance than a single measurement. (In practice, the number of iterations could
exceed 100, but 100 is a reasonable minimum goal.)

Because a timing distribution is bounded by zero on one side, taking the mean would allow large positive outlier
measurements to skew the result substantially. Therefore, for the benchmark score, we use the median timing measurement,
which is robust in the face of outliers.

Each benchmark is structured into discrete setup/execute/teardown phases. Phases are as follows, with specific details
given in a subsequent section:

- setup -- (ONCE PER TASK) something to do once before any benchmarking, e.g. construct a client object, load test data,
    insert data into a collection, etc.
- before operation -- (ONCE PER ITERATION) something to do before every task iteration, e.g. drop a collection, or
    reload test data (if the test run modifies it), etc.
- do operation -- (ONCE PER ITERATION) smallest amount of code necessary to execute the task; e.g. insert 1000 models
    one by one into the database, or retrieve 1000 models of test data from the database, etc.
- after operation -- (ONCE PER ITERATION) something to do after every task iteration (if necessary)
- teardown -- (ONCE PER TASK) something done once after all benchmarking is complete (if necessary); e.g. drop the test
    database

The wall-clock execution time of each "do operation" phase will be recorded. We use wall clock time to model user
experience and as a lowest-common denominator across ODMs. Iteration timing should be done with a high-resolution
monotonic timer (or best language approximation).

Unless otherwise specified, the number of iterations to measure per task is variable:

- iterations should loop for at least 1 minute cumulative execution time
- iterations should stop after 100 iterations or 5 minutes cumulative execution time, whichever is shorter

This balances measurement stability with a timing cap to ensure all tasks can complete in a reasonable time.

For each task, the 10th, 25th, 50th, 75th, 90th, 95th, 98th and 99th percentiles will be recorded using the following
algorithm:

- Given a 0-indexed array A of N iteration wall clock times
- Sort the array into ascending order (i.e. shortest time first)
- Let the index i for percentile p in the range [1,100] be defined as: `i = int(N * p / 100) - 1`

*N.B. This is the [Nearest Rank](https://en.wikipedia.org/wiki/Percentile#The_Nearest_Rank_method) algorithm, chosen for
its utter simplicity given that it needs to be implemented identically across a wide variety of ODMs and languages.*

The 50th percentile (i.e. the median) will be used for score composition. Other percentiles will be stored for
visualizations and analysis.

Each task will have defined for it an associated size in megabytes (MB). The benchmarking score for each task will be
the task size in MB divided by the median wall clock time.

## Benchmark task definitions

Datasets are available in the `odm-data` directory adjacent to this spec.

Note: The term "LDJSON" means "line-delimited JSON", which should be understood to mean a collection of UTF-8 encoded
JSON documents (without embedded CR or LF characters), separated by a single LF character. (Some Internet definition of
line-delimited JSON use CRLF delimiters, but this benchmark uses only LF.)

### Flat models

Datasets are in the `flat-models` tarball.

Flat model tests focus on flatly-structured model reads and writes across data sizes. They are designed to give insights
into the efficiency of the ODM's implementation of basic data operations.

The data will be stored as strict JSON with no extended types. These JSON representations must be converted into
equivalent models as part of the benchmark's setup.

Flat model benchmark tasks include:s

- Small model creation
- Small model update
- Small model find by filter
- Small model find foreign key by filter (if joins are supported)
- Large model creation
- Large model update

#### Small model creation

Summary: This benchmark tests ODM performance creating a single small model.

Dataset: The dataset (SMALL_DOC) is contained within `small-document.json` and consists of a sample document stored as
strict JSON with an encoded length of approximately X bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `small-document` source file (X bytes) times
10,000 operations, which equals X,XXX,XXX bytes or X MB.

| Phase       | Description                                                                            |
| ----------- | -------------------------------------------------------------------------------------- |
| Setup       | Load the SMALL_DOC dataset into memory as an ODM-appropriate model object.             |
| Before task | Drop the collection associated with the SMALL_DOC model.                               |
| Do task     | Save the model to the database in an ODM-appropriate manner. Repeat this 10,000 times. |
| After task  | n/a                                                                                    |
| Teardown    | n/a.                                                                                   |

#### Large model update

Summary: This benchmark tests ODM performance updating fields on a single small model.

Dataset: The dataset (SMALL_DOC) is contained within `small-document.json` and consists of a sample document stored as
strict JSON with an encoded length of approximately X bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `small-document` source file (X bytes) times
10,000 operations, which equals X,XXX,XXX bytes or X MB.

| Phase       | Description                                                                                                         |
| ----------- | ------------------------------------------------------------------------------------------------------------------- |
| Setup       | Load the SMALL_DOC dataset into memory as an ODM-appropriate model object. Save 10,000 instances into the database. |
| Before task | n/a.                                                                                                                |
| Do task     | Update the `FIELD_NAME` field for each instance of the model in an ODM-appropriate manner.                          |
| After task  | Drop the collection associated with the SMALL_DOC model.                                                            |
| Teardown    | n/a.                                                                                                                |

#### Small model find by filter

Summary: This benchmark tests ODM performance finding documents using a basic filter.

Dataset: The dataset (SMALL_DOC) is contained within `small-document.json` and consists of a sample document stored as
strict JSON with an encoded length of approximately X bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `small-document` source file (X bytes) times
10,000 operations, which equals X,XXX,XXX bytes or X MB.

| Phase | Description                                                                |
| ----- | -------------------------------------------------------------------------- |
| Setup | Load the SMALL_DOC dataset into memory as an ODM-appropriate model object. |

```
            Insert 10,000 instances into the database, saving the inserted _id field for each into a list.                                        |
```

| Before task | n/a. | | Do task | For each of the 10,000 \_id values, perform a filter operation to search for the
corresponding model document. | | After task | n/a. | | Teardown | Drop the collection associated with the SMALL_DOC
model. |

#### Small model find foreign key by filter

Summary: This benchmark tests ODM performance finding documents by foreign keys. This benchmark must only be run by ODMs
that support join ($lookup) operations.

Dataset: The dataset (SMALL_DOC_FK) is contained within `small-document-foreign-key.json` and consists of two sample
documents, both stored as strict JSON: the main document with an encoded length of approximately X bytes, and the
associated foreign key document with an encoded length of approximately Y bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `small-document-foreign-key.json` source file (X
\+ Y bytes) times 10,000 operations, which equals X,XXX,XXX bytes or X + Y MB.

| Phase | Description                                                                                                                                |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Setup | Load the SMALL_DOC_FK dataset into memory as two ODM-appropriate model objects: one for the main model, and one for the foreign key model. |

```
            Insert 10,000 instances of each into the database, saving the inserted _id field for each foreign key model into a list.              |
```

| Before task | n/a. | | Do task | For each of the 10,000 foreign key \_id values, perform a filter operation on the
main model. | | After task | n/a. | | Teardown | Drop the collection associated with the SMALL_DOC_FK model. |

#### Large model creation

Summary: This benchmark tests ODM performance creating a single large model.

Dataset: The dataset (LARGE_DOC) is contained within `large-document.json` and consists of a sample document stored as
strict JSON with an encoded length of approximately X bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `large-document` source file (X bytes) times
10,000 operations, which equals X,XXX,XXX bytes or X MB.

| Phase       | Description                                                                               |
| ----------- | ----------------------------------------------------------------------------------------- |
| Setup       | Load the LARGE_DOC dataset into memory as an ODM-appropriate model object.                |
| Before task | Drop the collection associated with the LARGE_DOC model.                                  |
| Do task     | Save the document to the database in an ODM-appropriate manner. Repeat this 10,000 times. |
| After task  | n/a                                                                                       |
| Teardown    | n/a.                                                                                      |

#### Large model update

Summary: This benchmark tests ODM performance updating fields on a single large model.

Dataset: The dataset (LARGE_DOC) is contained within `large-document.json` and consists of a sample document stored as
strict JSON with an encoded length of approximately X bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `large-document` source file (X bytes) times
10,000 operations, which equals X,XXX,XXX bytes or X MB.

| Phase       | Description                                                                                                         |
| ----------- | ------------------------------------------------------------------------------------------------------------------- |
| Setup       | Load the LARGE_DOC dataset into memory as an ODM-appropriate model object. Save 10,000 instances into the database. |
| Before task | n/a.                                                                                                                |
| Do task     | Update the `FIELD_NAME` field for each instance of the model in an ODM-appropriate manner.                          |
| After task  | Drop the collection associated with the LARGE_DOC model.                                                            |
| Teardown    | n/a.                                                                                                                |

### Nested models

Datasets are in the `nested-models` tarball.

Nested model tests focus performing reads and writes on models containing nested (embedded) documents. They are designed
to give insights into the efficiency of the ODM's implementation of a core advantage of the document model.

The data will be stored as strict JSON with no extended types. These JSON representations must be converted into
equivalent models as part of the benchmark's setup.

Nested model benchmark tasks include:s

- Small model creation
- Small model update
- Small model find nested field by filter
- Large model creation
- Large model update nested field

#### Small model insert

Summary: This benchmark tests ODM performance inserting a single small nested model.

Dataset: The dataset (SMALL_DOC_NESTED) is contained within `small-document-nested.json` and consists of a sample
document stored as strict JSON with an encoded length of approximately X bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `small-document-nested` source file (X bytes)
times 10,000 operations, which equals X,XXX,XXX bytes or X MB.

| Phase       | Description                                                                               |
| ----------- | ----------------------------------------------------------------------------------------- |
| Setup       | Load the SMALL_DOC_NESTED dataset into memory as an ODM-appropriate model object.         |
| Before task | Drop the collection associated with the SMALL_DOC_NESTED model.                           |
| Do task     | Save the document to the database in an ODM-appropriate manner. Repeat this 10,000 times. |
| After task  | n/a                                                                                       |
| Teardown    | n/a.                                                                                      |

#### Small model find nested field

Summary: This benchmark tests ODM performance finding documents by fields within nested documents.

Dataset: The dataset (SMALL_DOC_NESTED) is contained within `small-document-nested.json` and consists of a sample
document stored as strict JSON with an encoded length of approximately X bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `small-document-nested` source file (X bytes)
times 10,000 operations, which equals X,XXX,XXX bytes or X MB.

| Phase | Description                                                                       |
| ----- | --------------------------------------------------------------------------------- |
| Setup | Load the SMALL_DOC_NESTED dataset into memory as an ODM-appropriate model object. |

```
            Insert 10,000 instances into the database, saving the inserted _id field for each model into a list.                                  |
```

| Before task | n/a. | | Do task | For each of the 10,000 \_id values, perform a filter operation on the nested model's
field and the main model's \_id. | | After task | n/a. | | Teardown | Drop the collection associated with the
SMALL_DOC_NESTED model. |

#### Large model creation

Summary: This benchmark tests ODM performance creating a single large nested model.

Dataset: The dataset (LARGE_DOC_NESTED) is contained within `large-document-nested.json` and consists of a sample
document stored as strict JSON with an encoded length of approximately X bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `large-document-nested` source file (X bytes)
times 10,000 operations, which equals X,XXX,XXX bytes or X MB.

| Phase       | Description                                                                            |
| ----------- | -------------------------------------------------------------------------------------- |
| Setup       | Load the LARGE_DOC_NESTED dataset into memory as an ODM-appropriate model object.      |
| Before task | Drop the collection associated with the LARGE_DOC model.                               |
| Do task     | Save the model to the database in an ODM-appropriate manner. Repeat this 10,000 times. |
| After task  | n/a                                                                                    |
| Teardown    | n/a.                                                                                   |

#### Large model update

Summary: This benchmark tests ODM performance updating nested fields on a single large model.

Dataset: The dataset (LARGE_DOC_NESTED) is contained within `large-document-nested.json` and consists of a sample
document stored as strict JSON with an encoded length of approximately X bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `large-document-nested` source file (X bytes)
times 10,000 operations, which equals X,XXX,XXX bytes or X MB.

| Phase       | Description                                                                                                                |
| ----------- | -------------------------------------------------------------------------------------------------------------------------- |
| Setup       | Load the LARGE_DOC_NESTED dataset into memory as an ODM-appropriate model object. Save 10,000 instances into the database. |
| Before task | n/a.                                                                                                                       |
| Do task     | Update the `NESTED_FIELD_NAME` field for each instance of the model in an ODM-appropriate manner.                          |
| After task  | Drop the collection associated with the LARGE_DOC_NESTED model.                                                            |
| Teardown    | n/a.                                                                                                                       |

## Benchmark platform, configuration and environments

### Benchmark Client

Benchmarks should be run with the most recent stable version of the ODM and the newest version of the driver it
supports.

All operations must be run with write concern "w:1".

### Benchmark Server

TBD: spec Amazon instance size; describe configuration (e.g. no auth, journal, pre-alloc sizes?, WT with compression to
minimize disk I/O impact?); same AWS zone as client

## Changelog
