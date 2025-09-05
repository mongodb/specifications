# ODM Performance Benchmarking

- Status: In progress
- Minimum Server Version: N/A

## Abstract

This document describes a standard benchmarking suite for MongoDB ODMs (Object Document Mappers). Much of this
document's structure and content is taken from the existing MongoDB driver benchmarking suite for consistency.

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

The benchmark suite consists of two groups of small, independent benchmarks. This allows us to better isolate areas
within ODMs that are faster or slower.

- Flat models -- reading and writing flat models of various sizes, to explore basic operation efficiency
- Nested models -- reading and writing nested models of various sizes, to explore basic operation efficiency for complex
    data

The suite is intentionally kept small for several reasons. One, ODM feature sets vary significantly across libraries.
This limits the number of benchmarks that can be run across the entire collection of extant ODMs. Two, several popular
MongoDB ODMs are actively maintained by third-parties, such as Mongoose. By limiting the benchmarking suite to a minimal
set of representative tests that are easy to implement, we encourage adoption of the suite by these third-party
maintainers.

### Measurement

In addition to latency data, all benchmark tasks will be measured in terms of "megabytes/second" (MB/s) of documents
processed, with higher scores being better. (In this document, "megabyte" refers to the SI decimal unit, i.e. 1,000,000
bytes.) This makes cross-benchmark comparisons easier.

To avoid various types of measurement skew, tasks will be measured over several iterations. Each iteration will have a
number of operations performed per iteration that depends on the task being benchmarked. The final score for a task will
be the median score of the iterations. A range of percentiles will also be recorded for diagnostic analysis.

### Data sets

Data sets will vary by task. In most cases, data sets will be synthetic line-delimited JSON files to be constructed by
the ODM being benchmarked into the appropriate model. Some tasks will require additional modifications to these
constructed models, such as adding generated ObjectIds.

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

- measuring the same 10,000 insertions over 10 iterations -- each timing run includes enough operations that insertion
    code dominates timing code; unusual system events are likely to affect only a fraction of the 10 timing measurements

With 10 timings of inserting the same 10,000 models, we build up a statistical distribution of the operation timing,
allowing a more robust estimate of performance than a single measurement. (In practice, the number of iterations could
exceed 10, but 10 is a reasonable minimum goal.)

Because a timing distribution is bounded by zero on one side, taking the mean would allow large positive outlier
measurements to skew the result substantially. Therefore, for the benchmark score, we use the median timing measurement,
which is robust in the face of outliers.

Each benchmark is structured into discrete setup/execute/teardown phases. Phases are as follows, with specific details
given in a subsequent section:

- setup -- (ONCE PER TASK) something to do once before any benchmarking, e.g. construct a model object, load test data,
    insert data into a collection, etc.
- before operation -- (ONCE PER ITERATION) something to do before every task iteration, e.g. drop a collection, or
    reload test data (if the test run modifies it), etc.
- do operation -- (ONCE PER ITERATION) smallest amount of code necessary to execute the task; e.g. insert 10,000 models
    one by one into the database, or retrieve 10,000 models of test data from the database, etc.
- after operation -- (ONCE PER ITERATION) something to do after every task iteration (if necessary)
- teardown -- (ONCE PER TASK) something done once after all benchmarking is complete (if necessary); e.g. drop the test
    database

The wall-clock execution time of each "do operation" phase will be recorded. We use wall clock time to model user
experience and as a lowest-common denominator across ODMs. Iteration timing should be done with a high-resolution
monotonic timer (or best language approximation).

Unless otherwise specified, the number of iterations to measure per task is variable:

- iterations should loop for at least 30 seconds cumulative execution time
- once this 30 second minimum execution time is reached, iterations should stop after at least 10 iterations or 1 minute
    cumulative execution time, whichever is shorter

This balances measurement stability with a timing cap to ensure all tasks can complete in a reasonable time.

For each task, the 10th, 25th, 50th, 75th, 90th, 95th, 98th and 99th percentiles will be recorded using the following
algorithm:

- Given a 0-indexed array A of N iteration wall clock times
- Sort the array into ascending order (i.e. shortest time first)
- Let the index i for percentile p in the range [1,100] be defined as: `i = int(N * p / 100) - 1`

*N.B. This is the [Nearest Rank](https://en.wikipedia.org/wiki/Percentile#The_nearest-rank_method) algorithm, chosen for
its utter simplicity given that it needs to be implemented identically across a wide variety of ODMs and languages.*

The 50th percentile (i.e. the median) will be used for score composition. Other percentiles will be stored for
visualizations and analysis.

Each task will have defined for it an associated size in megabytes (MB). This size will be calculated using the task's
dataset size and the number of documents processed per iteration. The benchmarking score for each task will be the task
size in MB divided by the median wall clock time.

## Benchmark task definitions

Datasets are available in the `odm-data` directory adjacent to this spec.

Note: The term "LDJSON" means "line-delimited JSON", which should be understood to mean a collection of UTF-8 encoded
JSON documents (without embedded CR or LF characters), separated by a single LF character. (Some Internet definition of
line-delimited JSON use CRLF delimiters, but this benchmark uses only LF.)

### Flat models

Datasets are in the `flat_models` tarball.

Flat model tests focus on flatly-structured model reads and writes across data sizes. They are designed to give insights
into the efficiency of the ODM's implementation of basic data operations.

The data will be stored as strict JSON with no extended types. These JSON representations must be converted into
equivalent models as part of each benchmark task.

Flat model benchmark tasks include:

- Small model creation
- Small model update
- Small model find by filter
- Small model find foreign key by filter (if joins are supported)
- Large model creation
- Large model update

#### Small model creation

Summary: This benchmark tests ODM performance creating a single small model.

Dataset: The dataset (SMALL_DOC) is contained within `small_doc.json` and consists of a sample document stored as strict
JSON with an encoded length of approximately 250 bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `small_doc` source file (250 bytes) times 10,000
operations, which equals 2,250,000 bytes or 2.5 MB.

This benchmark uses a comparable dataset to the driver `small doc insertOne` benchmark, allowing for direct comparisons.

| Phase       | Description                                                                                                                |
| ----------- | -------------------------------------------------------------------------------------------------------------------------- |
| Setup       | Load the SMALL_DOC dataset into memory.                                                                                    |
| Before task | n/a.                                                                                                                       |
| Do task     | Create an ODM-appropriate model instance for the SMALL_DOC document and save it to the database. Repeat this 10,000 times. |
| After task  | Drop the collection associated with the SMALL_DOC model.                                                                   |
| Teardown    | n/a.                                                                                                                       |

#### Small model update

Summary: This benchmark tests ODM performance updating fields on a single small model.

Dataset: The dataset (SMALL_DOC) is contained within `small_doc.json` and consists of a sample document stored as strict
JSON with an encoded length of approximately 250 bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `updated_value` string file (13 bytes) times
10,000 operations, which equals 130,000 bytes or 130 KB.

| Phase       | Description                                                                                                         |
| ----------- | ------------------------------------------------------------------------------------------------------------------- |
| Setup       | Load the SMALL_DOC dataset into memory as an ODM-appropriate model object. Save 10,000 instances into the database. |
| Before task | n/a.                                                                                                                |
| Do task     | Update the `field1` field for each instance of the model to equal `updated_value` in an ODM-appropriate manner.     |
| After task  | n/a.                                                                                                                |
| Teardown    | Drop the collection associated with the SMALL_DOC model.                                                            |

#### Small model find by filter

Summary: This benchmark tests ODM performance finding documents using a basic filter.

Dataset: The dataset (SMALL_DOC) is contained within `small_doc.json` and consists of a sample document stored as strict
JSON with an encoded length of approximately 250 bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `small_doc` source file (250 bytes) times 10,000
operations, which equals 2,250,000 bytes or 2.5 MB.

| Phase       | Description                                                                                                                                                        |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Setup       | Load the SMALL_DOC dataset into memory as an ODM-appropriate model object. Insert 10,000 instances into the database, saving the `_id` field for each into a list. |
| Before task | n/a.                                                                                                                                                               |
| Do task     | For each of the 10,000 `_id` values, perform a filter operation to find the corresponding SMALL_DOC model.                                                         |
| After task  | n/a.                                                                                                                                                               |
| Teardown    | Drop the collection associated with the SMALL_DOC model.                                                                                                           |

#### Small model find foreign key by filter

Summary: This benchmark tests ODM performance finding documents by foreign keys. This benchmark must only be run by ODMs
that support join ($lookup) operations.

Dataset: The dataset (SMALL_DOC) is contained within `small_doc.json` and consists of a sample document stored as strict
JSON with an encoded length of approximately 250 bytes. An additional model (FOREIGN_KEY) representing the foreign key,
consisting of only a string field called `name`, must also be created.

Dataset size: For scoring purposes, the dataset size is the size of the `small_doc` source file (250 bytes) times 10,000
operations, which equals 2,250,000 bytes or 2.5 MB.

| Phase       | Description                                                                                                                                                                                                                                                                                        |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Setup       | Load the SMALL_DOC dataset into memory as an ODM-appropriate model object. For each SMALL_DOC model, create and assign a FOREIGN_KEY instance to the `field_fk` field. Insert 10,000 instances of both models into the database, saving the inserted `_id` field for each FOREIGN_KEY into a list. |
| Before task | n/a.                                                                                                                                                                                                                                                                                               |
| Do task     | For each of the 10,000 FOREIGN_KEY `_id` values, perform a filter operation in an ODM-appropriate manner to find the corresponding SMALL_DOC model.                                                                                                                                                |
| After task  | n/a.                                                                                                                                                                                                                                                                                               |
| Teardown    | Drop the collections associated with the SMALL_DOC and FOREIGN_KEY models.                                                                                                                                                                                                                         |

#### Large model creation

Summary: This benchmark tests ODM performance creating a single large model.

Dataset: The dataset (LARGE_DOC) is contained within `large_doc.json` and consists of a sample document stored as strict
JSON with an encoded length of approximately 8,000 bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `large_doc` source file (8,000 bytes) times
10,000 operations, which equals 80,000,000 bytes or 80 MB.

| Phase       | Description                                                                                                                |
| ----------- | -------------------------------------------------------------------------------------------------------------------------- |
| Setup       | Load the LARGE_DOC dataset into memory.                                                                                    |
| Before task | n/a.                                                                                                                       |
| Do task     | Create an ODM-appropriate model instance for the LARGE_DOC document and save it to the database. Repeat this 10,000 times. |
| After task  | Drop the collection associated with the LARGE_DOC model.                                                                   |
| Teardown    | n/a.                                                                                                                       |

#### Large model update

Summary: This benchmark tests ODM performance updating fields on a single large model.

Dataset: The dataset (LARGE_DOC) is contained within `large_doc.json` and consists of a sample document stored as strict
JSON with an encoded length of approximately 8,000 bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `updated_value` string file (13 bytes) times
10,000 operations, which equals 130,000 bytes or 130 KB.

| Phase       | Description                                                                                                         |
| ----------- | ------------------------------------------------------------------------------------------------------------------- |
| Setup       | Load the LARGE_DOC dataset into memory as an ODM-appropriate model object. Save 10,000 instances into the database. |
| Before task | n/a.                                                                                                                |
| Do task     | Update the `field1` field for each instance of the model to `updated_value` in an ODM-appropriate manner.           |
| After task  | Drop the collection associated with the LARGE_DOC model.                                                            |
| Teardown    | n/a.                                                                                                                |

### Nested models

Datasets are in the `nested_models` tarball.

Nested model tests focus performing reads and writes on models containing nested (embedded) documents. They are designed
to give insights into the efficiency of operations on the more complex data structures enabled by the document model.

The data will be stored as strict JSON with no extended types. These JSON representations must be converted into
equivalent ODM models as part of each benchmark task.

Nested model benchmark tasks include:s

- Large model creation
- Large model update nested field
- Large model find nested field by filter
- Large model find nested array field by filter

#### Large model creation

Summary: This benchmark tests ODM performance creating a single large nested model.

Dataset: The dataset (LARGE_DOC_NESTED) is contained within `large_doc_nested.json` and consists of a sample document
stored as strict JSON with an encoded length of approximately 8,000 bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `large_doc_nested` source file (8,000 bytes)
times 10,000 operations, which equals 80,000,000 bytes or 80 MB.

| Phase       | Description                                                                                                                       |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Setup       | Load the LARGE_DOC_NESTED dataset into memory.                                                                                    |
| Before task | n/a.                                                                                                                              |
| Do task     | Create an ODM-appropriate model instance for the LARGE_DOC_NESTED document and save it to the database. Repeat this 10,000 times. |
| After task  | Drop the collection associated with the LARGE_DOC_NESTED model.                                                                   |
| Teardown    | n/a.                                                                                                                              |

#### Large model update nested

Summary: This benchmark tests ODM performance updating nested fields on a single large model.

Dataset: The dataset (LARGE_DOC_NESTED) is contained within `large_doc_nested.json` and consists of a sample document
stored as strict JSON with an encoded length of approximately 8,000 bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `updated_value` string file (13 bytes) times
10,000 operations, which equals 130,000 bytes or 130 KB.

| Phase       | Description                                                                                                                               |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Setup       | Load the LARGE_DOC_NESTED dataset into memory as an ODM-appropriate model object. Save 10,000 instances into the database.                |
| Before task | n/a.                                                                                                                                      |
| Do task     | Update the value of the `embedded_str_doc_1.field1` field to `updated_value` in an ODM-appropriate manner for each instance of the model. |
| After task  | Drop the collection associated with the LARGE_DOC_NESTED model.                                                                           |
| Teardown    | n/a.                                                                                                                                      |

#### Large nested model find nested by filter

Summary: This benchmark tests ODM performance finding nested documents using a basic filter.

Dataset: The dataset (LARGE_DOC_NESTED) is contained within `large_doc_nested.json` and consists of a sample document
stored as strict JSON with an encoded length of approximately 8,000 bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `large_doc_nested` source file (8,000 bytes)
times 10,000 operations, which equals 80,000,000 bytes or 80 MB.

| Phase       | Description                                                                                                                                                                                                                            |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Setup       | Load the LARGE_DOC_NESTED dataset into memory as an ODM-appropriate model object. Insert 10,000 instances into the database, saving the value of the `unique_id` field for each model's `embedded_str_doc_1` nested model into a list. |
| Before task | n/a.                                                                                                                                                                                                                                   |
| Do task     | For each of the 10,000 `embedded_str_doc_1.unique_id` values, perform a filter operation to search for the parent LARGE_DOC_NESTED model.                                                                                              |
| After task  | n/a.                                                                                                                                                                                                                                   |
| Teardown    | Drop the collection associated with the LARGE_DOC_NESTED model.                                                                                                                                                                        |

#### Large nested model find nested array by filter

Summary: This benchmark tests ODM performance finding nested document arrays using a basic filter.

Dataset: The dataset (LARGE_DOC_NESTED) is contained within `large_doc_nested.json` and consists of a sample document
stored as strict JSON with an encoded length of approximately 8,000 bytes.

Dataset size: For scoring purposes, the dataset size is the size of the `large_doc_nested` source file (8,000 bytes)
times 10,000 operations, which equals 80,000,000 bytes or 80 MB.

| Phase       | Description                                                                                                                                                                                                                                                  |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Setup       | Load the LARGE_DOC_NESTED dataset into memory as an ODM-appropriate model object. Insert 10,000 instances into the database, saving the value of the `unique_id` field for the first item in each model's `embedded_str_doc_array` nested model into a list. |
| Before task | n/a.                                                                                                                                                                                                                                                         |
| Do task     | For each of the 10,000 `unique_id` values, perform a filter operation to search for the parent LARGE_DOC_NESTED model.                                                                                                                                       |
| After task  | n/a.                                                                                                                                                                                                                                                         |
| Teardown    | Drop the collection associated with the LARGE_DOC_NESTED model.                                                                                                                                                                                              |

## Benchmark platform, configuration and environments

### Benchmark Client

The benchmarks should be run with the most recent stable version of the ODM and the newest version of the driver it
supports.

### Benchmark Server

The MongoDB ODM Performance Benchmark must be run against a MongoDB replica set of size 1 running the latest stable
database version without authentication or SSL enabled.

### Benchmark placement and scheduling

The MongoDB ODM Performance Benchmark should be placed within the ODM's test directory as an independent test suite. Due
to the relatively long runtime of the benchmarks, including them as part of an automated suite that runs against every
PR is not recommended. Instead, scheduling benchmark runs on a regular cadence is the recommended method of automating
this suite of tests.

## ODM-specific benchmarking

As discussed earlier in this document, ODM feature sets vary significantly across libraries. Many ODMs have features
unique to them or their niche in the wider ecosystem, which makes specifying concrete benchmark test cases for every
possible API unfeasible. Instead, ODM authors should determine what mainline use cases of their library are not covered
by the benchmarks specified above and expand this testing suite with additional benchmarks to cover those areas.

## Changelog
