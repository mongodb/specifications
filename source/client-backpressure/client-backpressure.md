# Client Backpressure

- Status: Accepted
- Minimum Server Version: N/A

______________________________________________________________________

## Abstract

This specification adds the ability for drivers to automatically retry requests that fail due to server overload errors
while applying backpressure to avoid further overloading the server.

## META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

### Terms

#### Ingress Connection Rate Limiter

A token bucket based system introduced in MongoDB 8.2 to admit, reject or queue connection requests. It aims to prevent
connection spikes from overloading the system.

#### Ingress Request Rate Limiter

A token bucket based system introduced in MongoDB 8.2 to admit a command or reject it with a System Overload Error at
the front door of a mongod/s. It aims to prevent command spikes from overloading the system.

#### MongoTune

Mongotune is a policy engine outside the server (mongod or mongos) which monitors a set of metrics (MongoDB or system
host) to dynamically configure MongoDB settings. MongoTune is deployed to Atlas clusters and will dynamically configure
the connection and request rate limiters to prevent and mitigate overloading the system.

#### RetryableError label

This error label indicates that an command is safely retryable regardless of the command type (read or write), its
metadata, or any of its arguments.

#### SystemOverloadedError label

An error is considered overloaded if it includes the "SystemOverloadError" label. This error label indicates that the
server is overloaded. If this error label is present, drivers will backoff before attempting a retry.

#### Overload Errors

An overload error is any command or network error that occurs due to a server overload. For example, when a request
exceeds the ingress request rate limit:

```js
{
  'ok': 0.0,
  'errmsg': "Rate limiter 'ingressRequestRateLimiter' rate exceeded",
  'code': 462,
  'codeName': 'IngressRequestRateLimitExceeded',
  'errorLabels': ['SystemOverloadedError', 'RetryableError'],
}
```

When a new connection attempt exceeds the ingress connection rate limit, the server closes the TCP connection before TLS
handshake is complete. Drivers will observe this as a network error (e.g. "connection reset by peer" or "connection
closed").

When a new connection attempt is queued by the server for so long that the driver-side timeout expires, drivers will
observe this as a network timeout error.

Note that there is no guarantee that all SystemOverloaded errors are retryable or that all RetryableErrors also have the
SystemOverloaded error label.

#### Goodput

The throughput of positive, useful output. In the context of drivers, this refers to the number of non-error results
that the driver processes per unit of time.

See [goodput](https://en.wikipedia.org/wiki/Goodput).

### Requirements for Client Backpressure

#### Overload retry policy

This specification expands the driver's retry ability to all commands if the error indicates that it is both an overload
error and that it is retryable, including those not currently considered retryable such as updateMany, create
collection, getMore, and generic runCommand. The new command execution method obeys the following rules:

1. If the command succeeds on the first attempt, drivers MUST deposit `RETRY_TOKEN_RETURN_RATE` tokens.
    - The value is 0.1 and non-configurable.
2. If the command succeeds on a retry attempt, drivers MUST deposit `RETRY_TOKEN_RETURN_RATE`+1 tokens.
3. If a retry attempt fails with an error that does not include `SystemOverloadedError` label, drivers MUST deposit 1
    token.
    - A non-SystemOverloaded error indicates that the server is healthy enough to handle requests. For the purposes of
        retry budget tracking, this counts as a success.
4. A retry attempt will only be permitted if:
    1. The error has both the `SystemOverloadedError` and the `RetryableError` label.
    2. We have not reached `MAX_RETRIES`.
        - The value of `MAX_RETRIES` is 5 and non-configurable.
        - This intentionally changes the behavior of CSOT which otherwise would retry an unlimited number of times within
            the timeout to avoid retry storms.
    3. (CSOT-only): `timeoutMS` has not expired.
    4. A token can be acquired from the token bucket.
5. A retry attempt consumes 1 token from the token bucket.
6. If the request is eligible for retry (as outlined in step 4), the client MUST apply exponential backoff according to
    the following formula: `delayMS = j * min(maxBackoff, baseBackoff * 2^(i - 1))`
    - `i` is the retry attempt number (starting with 1 for the first retry). Note that `i` includes retries for
        non-overloaded errors.
    - `j` is a random jitter value between 0 and 1.
    - `baseBackoff` is constant 100ms.
    - `maxBackoff` is 10000ms.
    - This results in delays of 100ms, 200ms, 400ms, 800ms, and 1600ms before accounting for jitter.
7. If the request is eligible for retry (as outlined in step 4), the client MUST add the previously used server's
    address to the list of deprioritized server addresses for server selection.

#### Interaction with Existing Retry Behavior

The retry policy in this specification is separate from the existing retryability policies defined in the
[retryable reads](../retryable-reads/retryable-reads.md) and [retryable writes](../retryable-writes/retryable-writes.md)
specifications. Drivers MUST ensure:

- Only errors with the `SystemOverloadedError` consume tokens from the token bucket before retrying.
- Only errors with the `SystemOverloadedError` label apply backoff.
- All retryable errors apply backoff if they also contain a `SystemOverloadedError` label. This includes:
    - Errors defined as retryable in the [retryable reads specification](../retryable-reads/retryable-reads.md).
    - Errors defined as retryable in the [retryable writes specification](../retryable-writes/retryable-writes.md).
    - Errors with the `RetryableError` label.
- Any command is retried at most MAX_ATTEMPTS (default=5) times, if any attempt has failed with a
    `SystemOverloadedError`, regardless of which retry policy the current or future retry attempts are caused by.

#### Pseudocode

The following pseudocode demonstrates the unified retry behavior, combining the overload retry policy defined in this
specification with the existing retry behaviors from [Retryable Reads](../retryable-reads/retryable-reads.md) and
[Retryable Writes](../retryable-writes/retryable-writes.md). For brevity, some error handling details such as the
handling of "NoWritesPerformed" are omitted.

```python
# Note: the values below have been scaled down by a factor of 1000 because
# Python's sleep API takes a duration in seconds, not milliseconds.
BASE_BACKOFF = 0.1 # 100ms
MAX_BACKOFF = 10   # 10000ms

RETRY_TOKEN_RETURN_RATE = 0.1
MAX_RETRIES = 5

def execute_command_retryable(command, ...):
    deprioritized_servers = []
    attempt = 0
    attempts = if is_csot then math.inf else 1

    while True:
        try:
            server = select_server(deprioritized_servers)
            connection = server.getConnection()
            res = execute_command(connection, command)
            # Deposit tokens into the bucket on success.
            tokens = RETRY_TOKEN_RETURN_RATE
            if attempt > 0:
                tokens += 1
            token_bucket.deposit(tokens)
            return res
        except PyMongoError as exc:
            is_retryable = is_retryable_write() or is_retryable_read() or (exc.has_error_label("RetryableError") and exc.has_error_label("SystemOverloadedError"))
            is_overload = exc.has_error_label("SystemOverloadedError")

            # if a retry fails with a non-System overloaded error, deposit 1 token
            if attempt > 0 and not is_overload:
                token_bucket.deposit(1)

            # Raise if the error is non-retryable.
            if not is_retryable:
                raise

            attempt += 1
            if is_overload:
                attempts = MAX_RETRIES

            if attempt > attempts:
                raise

            deprioritized_servers.append(server.address)

            if is_overload:
                jitter = random.random() # Random float between [0.0, 1.0).
                backoff = jitter * min(BASE_BACKOFF * (2 ** attempt - 1), MAX_BACKOFF)
          
                # If the delay exceeds the deadline, bail early.
                if _csot.get_timeout():
                    if time.monotonic() + backoff > _csot.get_deadline():
                        raise

                if not token_bucket.consume(1):
                    raise

                time.sleep(backoff)
```

### Token Bucket

The overload retry policy introduces a per-client token bucket to limit SystemOverloaded retry attempts. Although the
server rejects excess commands as quickly as possible, doing so costs CPU and creates extra contention on the connection
pool which can eventually negatively affect goodput. To reduce this risk, the token bucket will limit retry attempts
during a prolonged overload.

The token bucket capacity is set to 1000 for consistency with the server.

#### Pseudocode

The token bucket is implemented via a thread safe counter. For languages without atomics, this can be implemented via a
lock, for example:

```python
DEFAULT_RETRY_TOKEN_CAPACITY = 1000
class TokenBucket:
    """A token bucket implementation for rate limiting."""
    def __init__(
        self,
        capacity: float = DEFAULT_RETRY_TOKEN_CAPACITY,
    ):
        self.lock = Lock()
        self.capacity = capacity
        self.tokens = capacity

    def consume(self, n: float) -> bool:
        """Consume n tokens from the bucket if available."""
        with self.lock:
            if self.tokens >= n:
                self.tokens -= n
                return True
            return False

   def deposit(self, n: float) -> None:
        """Deposit n tokens back into the bucket."""
        with self.lock:
            self.tokens = min(self.capacity, self.tokens + n)
```

#### Handshake changes

Drivers conforming to this spec MUST add `“backpressure”: True` to the connection handshake. This flag allows the server
to identify clients which do and do not support backpressure. Currently, this flag is unused but in the future the
server may offer different rate limiting behavior for clients that do not support backpressure.

#### Implementation notes

On some platforms sleep() can have a very low precision, meaning an attempt to sleep for 50ms may actually sleep for a
much larger time frame. Drivers are not required to work around this limitation.

### Logging Retry Attempts

[As with retryable writes](../retryable-writes/retryable-writes.md#logging-retry-attempts), drivers MAY choose to log
retry attempts for load shed commands. This specification does not define a format for such log messages.

### Command Monitoring

[As with retryable writes](../retryable-writes/retryable-writes.md#command-monitoring), in accordance with the
[Command Logging and Monitoring](../command-logging-and-monitoring/command-logging-and-monitoring.md) specification,
drivers MUST guarantee that each `CommandStartedEvent` has either a correlating `CommandSucceededEvent` or
`CommandFailedEvent` and that every "command started" log message has either a correlating "command succeeded" log
message or "command failed" log message. If the first attempt of a retryable command encounters a retryable error,
drivers MUST fire a `CommandFailedEvent` and emit a "command failed" log message for the retryable error and fire a
separate `CommandStartedEvent` and emit a separate "command started" log message when executing the subsequent retry
attempt. Note that the second `CommandStartedEvent` and "command started" log message may have a different
`connectionId`, since a server is reselected for a retry attempt.

### Documentation

1. Drivers MUST document that all commands support retries on server overload.
2. Driver release notes MUST make it clear to users that they may need to adjust custom retry logic to prevent an
    application from inadvertently retrying for too long (see [Backwards Compatibility](#backwards-compatibility) for
    details).

### Backwards Compatibility

The server's rate limiting can introduce higher error rates than previously would have been exposed to users under
periods of extreme server overload. The increased error rates is a tradeoff: given the choice between an overloaded
server (potential crash), or at minimum dramatically slower query execution time and a stable but lowered throughput
with higher error rate as the server load sheds, we have chosen the latter.

The changes in this specification help smooth out the impact of the server's rate limiting on users by reducing the
number of errors users see during spikes or burst workloads and help prevent retry storms by spacing out retries.
However, older drivers do not have this benefit. Drivers MUST document that:

- Users SHOULD upgrade to driver versions that officially support backpressure to avoid any impacts of server changes.
- Users who do not upgrade might need to update application error handling to handle higher error rates of
    SystemOverloadedErrors.

## Test Plan

See the [README](./tests/README.md) for tests.

## Motivation for Change

New load shedding mechanisms are being introduced to the server that improve its ability to remain available under
extreme load, however clients do not know how to handle the errors returned when one of its requests has been rejected.
As a result, such overload errors would currently either be propagated back to applications, increasing
externally-visible command failure rates, or be retried immediately, increasing the load on already overburdened
servers. To minimize these effects, this specification enables clients to retry requests that have been load shed in a
way that does not overburden already overloaded servers. This retry behavior allows for more aggressive and effective
load shedding policies to be deployed in the future. This will also help unify the currently-divergent retry behavior
between drivers and the server (mongos).

## Reference Implementation

The Node and Python drivers will provide the reference implementations. See
[NODE-7142](https://jira.mongodb.org/browse/NODE-7142) and [PYTHON-5528](https://jira.mongodb.org/browse/PYTHON-5528).

## Future work

1. [DRIVERS-3333](https://jira.mongodb.org/browse/DRIVERS-3333) Add a backoff state into the connection pool.
2. [DRIVERS-3241](https://jira.mongodb.org/browse/DRIVERS-3241) Add diagnostic metadata to retried commands.
3. [DRIVERS-3352](https://jira.mongodb.org/browse/DRIVERS-3352) Add support for RetryableError labels to retryable reads
    and writes.

## Q&A

### Why are drivers not required to work around timing limitations in their language's sleep() APIs?

The client backpressure retry loop is primarily concerned with spreading out retries to avoid retry storms. The exact
sleep duration is not critical to the intended behavior, so long as we sleep at least as long as we say we will.

### Why override existing maximum number of retry attempt defaults for retryable reads and writes if a `SystemOverloadedError` is received?

Load-shedded errors indicate that the request was rejected by the server to minimize load, not that the command failed
for logical reasons. So, when determining the number of retries an operation should attempt:

- Any load-shedded errors should be retried to give them a real attempt at success
- If the command ultimately would have failed if it had not been load shed by the server, returning an actionable error
    message is preferable to a generic SystemOverloadedError.

The maximum retry attempt logic in this specification balances legacy retryability behavior with load-shedding behavior:

- Relying on either 1 or infinite timeouts (depending on CSOT) preserves existing retry behavior.
- Adjusting the maximum number of retry attempts to 5 if a `SystemOverloadedError` error is returned from the server
    gives requests more opportunities to succeed and helps reduce application errors.
- An alternative approach would be to retry once if we don't receive a SystemOverloadedError, in which case we'd retry 5
    times. The approach chosen allows for additional retries in scenarios where a non-`SystemOverloadedError` fails on a
    retry with a `SystemOverloadedError`.

## Changelog

- 2025-XX-XX: Initial version.
