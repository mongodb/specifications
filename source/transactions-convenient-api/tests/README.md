# Convenient API for Transactions Tests

______________________________________________________________________

## Introduction

The YAML and JSON files in this directory are platform-independent tests meant to exercise a driver's implementation of
the Convenient API for Transactions spec. These tests utilize the
[Unified Test Format](../../unified-test-format/unified-test-format.md).

Several prose tests, which are not easily expressed in YAML, are also presented in this file. Those tests will need to
be manually implemented by each driver.

## Prose Tests

### Callback Raises a Custom Error

Write a callback that raises a custom exception or error that does not include either UnknownTransactionCommitResult or
TransientTransactionError error labels. Execute this callback using `withTransaction` and assert that the callback's
error bypasses any retry logic within `withTransaction` and is propagated to the caller of `withTransaction`.

### Callback Returns a Value

Write a callback that returns a custom value (e.g. boolean, string, object). Execute this callback using
`withTransaction` and assert that the callback's return value is propagated to the caller of `withTransaction`.

### Retry Timeout is Enforced

Drivers should test that `withTransaction` enforces a non-configurable timeout before retrying both commits and entire
transactions. Specifically, three cases should be checked:

- If the callback raises an error with the TransientTransactionError label and the retry timeout has been exceeded,
    `withTransaction` should propagate the error to its caller.
- If committing raises an error with the UnknownTransactionCommitResult label, and the retry timeout has been exceeded,
    `withTransaction` should propagate the error to its caller.
- If committing raises an error with the TransientTransactionError label and the retry timeout has been exceeded,
    `withTransaction` should propagate the error to its caller. This case may occur if the commit was internally retried
    against a new primary after a failover and the second primary returned a NoSuchTransaction error response.

If possible, drivers should implement these tests without requiring the test runner to block for the full duration of
the retry timeout. This might be done by internally modifying the timeout value used by `withTransaction` with some
private API or using a mock timer.

### Retry Backoff is Enforced

Drivers should test that retries within `withTransaction` do not occur immediately. First, run transactions without
backoff. To do so, configure the random number generator used for jitter to always return `0` -- this effectively
disables backoff. Then, configure a fail point that forces 30 retries like so:

```json
{
    "configureFailPoint": "failCommand",
    "mode": {
        "times": 13
    },
    "data": {
        "failCommands": ["commitTransaction"],
        "errorCode": 251,  // NoSuchTransaction
    },
}
```

Let the callback for the transaction be a simple `insertOne` command. Let `no_backoff_time` be the time it took for the
command to succeed.

Next, we will run the transactions again with backoff. Configure the random number generator used for jitter to always
return `1`. Set the fail point to force 13 retries using the same command as before. Using the same callback as before,
check that the total time for the withTransaction command is within +/-1 second of `no_backoff_time` plus 2.2 seconds.
Note that 2.2 seconds is the sum of backoff 13 consecutive backoff values and the 1-second window is just to account for
potential networking differences between the two runs.

## Changelog

- 2025-10-17: Added Backoff test.
- 2024-09-06: Migrated from reStructuredText to Markdown.
- 2024-02-08: Converted legacy tests to unified format.
- 2021-04-29: Remove text about write concern timeouts from prose test.
