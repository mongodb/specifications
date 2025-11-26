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

A token-bucket based system introduced in MongoDB 8.2 to admit, reject or queue connection requests. It aims to prevent
connection spikes from overloading the system.

#### Ingress Request Rate Limiter

A token bucket based system introduced in MongoDB 8.2 to admit an operation or reject it with a System Overload Error at
the front door of a mongod/s. It aims to prevent operations spikes from overloading the system.

#### MongoTune

Mongotune is a policy engine outside the server (mongod or mongos) which monitors a set of metrics (MongoDB or system
host) to dynamically configure MongoDB settings. MongoTune is deployed to Atlas clusters and will dynamically configure
the connection and request rate limiters to prevent and mitigate overloading the system.

#### RetryableError label

An error is considered retryable if it includes the "RetryableError" label. This error label indicates that an operation
is safely retryable regardless of the type of operation, its metadata, or any of its arguments.

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

### Requirements for Client Backpressure

#### Overload retry policy

This specification expands the driver's retry ability to all commands, including those not currently considered
retryable such as updateMany, create collection, getMore, and generic runCommand. The new command execution method obeys
the following rules:

1. If the command succeeds on the first attempt, drivers MUST deposit `RETRY_TOKEN_RETURN_RATE` tokens.
    - The value is 0.1 and non-configurable.
2. If the command succeeds on a retry attempt, drivers MUST deposit `RETRY_TOKEN_RETURN_RATE`+1 tokens.
3. If a retry attempt fails with an error that does not include `SystemOverloadedError` label, drivers MUST deposit 1
    token.
4. A retry attempt will only be permitted if the error includes the `RetryableError` label, we have not reached
    `MAX_ATTEMPTS`, the CSOT deadline has not expired, and a token can be acquired from the token bucket.
    - The value of `MAX_ATTEMPTS` is 5 and non-configurable.
    - This intentionally changes the behavior of CSOT which otherwise would retry an unlimited number of times within the
        timeout to avoid retry storms.
5. If the previous error includes the `SystemOverloadedError` label, the client MUST apply exponential backoff according
    to according to the following formula: `delayMS = j * min(maxBackoff, baseBackoff * 2^i)`
    - `i` is the retry attempt (starting with 0 for the first retry).
    - `j` is a random jitter value between 0 and 1.
    - `baseBackoff` is constant 100ms.
    - `maxBackoff` is 10000ms.
    - This results in delays of 100ms, 200ms, 400ms, 800ms, and 1600ms before accounting for jitter.
6. If the previous error contained the `SystemOverloadedError` error label, the node will be added to the set of
    deprioritized servers.

#### Pseudocode

The following pseudocode describes the overload retry policy:

```python
BASE_BACKOFF = 0.1
MAX_BACKOFF = 10
RETRY_TOKEN_RETURN_RATE = 0.1

def execute_command_retryable(command, ...):
    deprioritized_servers = []
    attempt = 0
    while True:
        try:
            server = select_server(deprioritized_servers)
            connection = server.getConnection()
            res = execute_command(connection, command)
            # Return tokens to the bucket on success.
            tokens = RETRY_TOKEN_RETURN_RATE
            if attempt > 0:
                tokens += 1
            token_bucket.deposit(tokens)
            return res
        except PyMongoError as exc:
            backoff = 0
            attempt += 1

            if attempt > MAX_ATTEMPTS:
                raise

            # Raise if the error is non retryable.
            is_retryable = exc.has_error_label("RetryableError") or is_retryable_write_error() or is_retryable_read_error()
            if not is_retryable:
                raise error
            if exc.has_error_label("SystemOverloadedError"):
                jitter = random.random() # Random float between [0.0, 1.0).
                backoff = jitter * min(BASE_BACKOFF * (2 ** attempt), MAX_BACKOFF)
		   
            # If the delay exceeds the deadline, bail early before consuming a token.
            if _csot.get_timeout():
                if time.monotonic() + backoff > _csot.get_deadline():
                    raise

            if not token_bucket.consume(1):
                raise

            if backoff:
                time.sleep(backoff)
            deprioritized_servers.append(server)
            continue
```

Some drivers might not have retryability implementations that allow easy separation of the existing retryable
reads/writes mechanisms from the exponential backoff and jitter retry algorithm. An example pseudocode is defined below
that demonstrates a combined retryable reads/writes implementation with the corresponding backpressure changes (adapted
from the Node driver's implementation):

```typescript
async function tryOperation<T extends AbstractOperation, TResult = ResultTypeFromOperation<T>>(
  operation: T,
  { topology, timeoutContext, session, readPreference }: RetryOptions
): Promise<TResult> {
  const serverSelector = getServerSelectorForReadPreference(operation, readPreference);

  let server = await topology.selectServer(selector, {
    session,
  });

  const hasReadAspect = operation.hasAspect(Aspect.READ_OPERATION);
  const hasWriteAspect = operation.hasAspect(Aspect.WRITE_OPERATION);
  const inTransaction = session?.inTransaction() ?? false;

  const willRetryRead = topology.s.options.retryReads && !inTransaction && operation.canRetryRead;

  const willRetryWrite =
    topology.s.options.retryWrites &&
    !inTransaction &&
    supportsRetryableWrites(server) &&
    operation.canRetryWrite;

  const willRetry =
    operation.hasAspect(Aspect.RETRYABLE) &&
    session != null &&
    ((hasReadAspect && willRetryRead) || (hasWriteAspect && willRetryWrite));

  if (hasWriteAspect && willRetryWrite && session != null) {
    operation.options.willRetryWrite = true;
    session.incrementTransactionNumber();
  }

  // The maximum number of retry attempts using regular retryable reads/writes logic (not including
  // SystemOverLoad error retries).
  const maxNonOverloadRetryAttempts = willRetry 
    ? timeoutMS != null 
        ? Infinity 
        : 2 
    : 1;

  let previousOperationError: MongoError | undefined;
  let previousServer: ServerDescription | undefined;

  let nonOverloadRetryAttempt = 0;
  let systemOverloadRetryAttempt = 0;

  const maxSystemOverloadRetryAttempts = 5;
  const backoffDelayProvider = exponentialBackoffDelayProvider(
    10_000, // MAX_BACKOFF
    100, // base backoff
    2 // backoff rate
  );

  while (true) {
    if (previousOperationError) {
      if (previousOperationError.hasErrorLabel("SystemOverloadError")) {
        systemOverloadRetryAttempt += 1;

        if (
          // if the SystemOverloadError is not retryable, throw.
          !previousOperationError.hasErrorLabel("RetryableError") ||
          !(
            // if retryable writes or reads are not configured, throw.
            (
              (hasReadAspect && topology.s.options.retryReads) ||
              (hasWriteAspect && topology.s.options.retryWrites)
            )
          )
        ) {
          throw previousOperationError;
        }

        // if we have exhausted overload retry attempts, throw.
        if (systemOverloadRetryAttempt > maxSystemOverloadRetryAttempts) {
          throw previousOperationError;
        }

        const { value: delayMS } = backoffDelayProvider.next();

        // if the delay would exhaust the CSOT timeout, short-circuit.
        if (timeoutContext.csotEnabled() && delayMS > timeoutContext.remainingTimeMS) {
          throw previousError;
        }

        await setTimeout(delayMS);

        // attempt to consume a retry token, throw if we don't have budget.
        if (!topology.tokenBucket.consume(RETRY_COST)) {
          throw previousOperationError;
        }

        server = await topology.selectServer(selector, { session });
      } else {
        nonOverloadRetryAttempt++;
        // we have no more retry attempts, throw.
        if (nonOverloadRetryAttempt > maxNonOverloadRetryAttempts) {
          throw previousOperationError;
        }

        // Handle MMAPv1 not supporting retryable writes.
        if (hasWriteAspect && previousOperationError.code === MMAPv1_RETRY_WRITES_ERROR_CODE) {
          throw new MongoServerError({
            message: MMAPv1_RETRY_WRITES_ERROR_MESSAGE,
            errmsg: MMAPv1_RETRY_WRITES_ERROR_MESSAGE,
            originalError: previousOperationError
          });
        }

        // handle non-retryable errors
        if (
          (hasWriteAspect && !isRetryableWriteError(previousOperationError)) ||
          (hasReadAspect && !isRetryableReadError(previousOperationError))
        ) {
          throw previousOperationError;
        }

        server = await topology.selectServer(selector, { session });

        // handle rare downgrade scenarios where some nodes don't support 
        // retryable writes but others do.
        if (hasWriteAspect && !supportsRetryableWrites(server)) {
          throw new MongoUnexpectedServerResponseError(
            'Selected server does not support retryable writes'
          );
        }
      }
    }

    try {
      try {
        const result = await server.command(operation, timeoutContext);
        const isRetry = nonOverloadRetryAttempt > 0 || systemOverloadRetryAttempt > 0;
        topology.tokenBucket.deposit(
          isRetry
            ? // on successful retry, deposit the retry cost + the refresh rate.
              TOKEN_REFRESH_RATE + RETRY_COST
            : // otherwise, just deposit the refresh rate.
              TOKEN_REFRESH_RATE
        );
        return operation.handleOk(result);
      } catch (error) {
        return operation.handleError(error);
      }
    } catch (operationError) {
      if (!operationError.hasErrorLabel("SystemOverloadError")) {
        // if an operation fails with an error that does not contain the SystemOverloadError, deposit 1 token.
        topology.tokenBucket.deposit(RETRY_COST);
      }

      if (
        previousOperationError != null &&
        operationError.hasErrorLabel("NoWritesPerformed")
      ) {
        throw previousOperationError;
      }
      previousServer = server.description;
      previousOperationError = operationError;
    }
  }
}
```

### Token Bucket

The overload retry policy introduces a per-client token bucket to limit retry attempts. Although the server rejects
excess operations as quickly as possible, doing so costs CPU and creates extra contention on the connection pool which
can eventually negatively affect goodput. To reduce this risk, the token bucket will limit retry attempts during a
prolonged overload.

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

##### Implementation notes

On some platforms sleep() can have a very low precision, meaning an attempt to sleep for 50ms may actually sleep for a
much larger time frame. Drivers are not required to work around this limitation.

### Logging Retry Attempts

[As with retryable writes](../retryable-writes/retryable-writes.md#logging-retry-attempts), drivers MAY choose to log
retry attempts for load shed operations. This specification does not define a format for such log messages.

### Command Monitoring

[As with retryable writes](../retryable-writes/retryable-writes.md#command-monitoring), in accordance with the
[Command Logging and Monitoring](../command-logging-and-monitoring/command-logging-and-monitoring.md) specification,
drivers MUST guarantee that each `CommandStartedEvent` has either a correlating `CommandSucceededEvent` or
`CommandFailedEvent` and that every "command started" log message has either a correlating "command succeeded" log
message or "command failed" log message. If the first attempt of a retryable operation encounters a retryable error,
drivers MUST fire a `CommandFailedEvent` and emit a "command failed" log message for the retryable error and fire a
separate `CommandStartedEvent` and emit a separate "command started" log message when executing the subsequent retry
attempt. Note that the second `CommandStartedEvent` and "command started" log message may have a different
`connectionId`, since a server is reselected for a retry attempt.

### Documentation

1. Drivers MUST document that all operations support retries on server overload.
2. Driver release notes MUST make it clear to users that they may need to adjust custom retry logic to prevent an
    application from inadvertently retrying for too long (see [Backwards Compatibility](#backwards-compatibility) for
    details).

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

## Q&A

TODO

## Changelog

- 2025-XX-XX: Initial version.
