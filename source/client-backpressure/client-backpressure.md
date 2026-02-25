# Client Backpressure

- Status: Accepted
- Minimum Server Version: N/A

______________________________________________________________________

## Abstract

This specification adds the ability for drivers to automatically retry requests that fail due to server overload errors
while applying backpressure to avoid further overloading the server.

The retry behaviors defined in this specification are separate from and complementary to the retry behaviors defined in
the [Retryable Reads](../retryable-reads/retryable-reads.md) and
[Retryable Writes](../retryable-writes/retryable-writes.md) specifications. This specification expands retry support to
all commands when specific server overload conditions are encountered, regardless of whether the command would normally
be retryable under those specifications.

## META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

### Terms

#### Ingress Connection Rate Limiter

A token bucket based system introduced in MongoDB 8.2 to admit, reject or queue connection requests. It aims to prevent
connection spikes from overloading the system.

#### Ingress Request Rate Limiter

A token bucket based system introduced in MongoDB 8.2 to admit a command or reject it with an overload error at the
front door of a mongod/s. It aims to prevent command spikes from overloading the system.

The ingress request rate limiter only applies to commands sent on authenticated connections.

#### MongoTune

Mongotune is a policy engine outside the server (mongod or mongos) which monitors a set of metrics (MongoDB or system
host) to dynamically configure MongoDB settings. MongoTune is deployed to Atlas clusters and will dynamically configure
the connection and request rate limiters to prevent and mitigate overloading the system.

#### RetryableError label

This error label indicates that a command is safely retryable regardless of the command type (read or write), its
metadata, or any of its arguments.

#### SystemOverloadedError label

An error is considered to be an overload error if it contains the `SystemOverloadedError` label. This error label
indicates that the server is overloaded. If this error label is present, drivers will backoff before attempting a retry.

#### Retryable Overload Error

An error which indicates that it is an overload error (contains the `SystemOverloadedError` label) and contains the
`RetryableError` label.

For example, when a request exceeds the ingress request rate limit, the following error may be returned:

```js
{
  'ok': 0.0,
  'errmsg': "Rate limiter 'ingressRequestRateLimiter' rate exceeded",
  'code': 462,
  'codeName': 'IngressRequestRateLimitExceeded',
  'errorLabels': ['SystemOverloadedError', 'RetryableError'],
}
```

Note that an error is not guaranteed to contain both the `SystemOverloadedError` and the `RetryableError` labels just
because it contains one of them.

#### Goodput

The throughput of positive, useful output. In the context of drivers, this refers to the number of non-error results
that the driver processes per unit of time.

See [goodput](https://en.wikipedia.org/wiki/Goodput).

### Requirements for Client Backpressure

#### Driver mechanisms subject to the retry policy

Commands sent by the driver to the server are subject to the retry policy defined in this specification unless the
command is included in the exceptions below.

Driver commands not subject to the overload retry policy:

- [Monitoring commands](../server-discovery-and-monitoring/server-monitoring.md#monitoring) and
    [round-trip time pingers](../server-discovery-and-monitoring/server-monitoring.md#measuring-rtt) (see
    [Why not apply the overload retry policy to monitoring and RTT connections?](./client-backpressure.md#why-not-apply-the-overload-retry-policy-to-monitoring-and-rtt-connections)).
- Commands executed during
    [connection establishment](../connection-monitoring-and-pooling/connection-monitoring-and-pooling.md#establishing-a-connection-internal-implementation)
    and [reauthentication](../auth/auth.md) (see
    [Why not apply the overload policy to authentication commands or reauthentication commands?](./client-backpressure.md#why-not-apply-the-overload-policy-to-authentication-commands-or-reauthentication-commands)).

Note: Drivers communicate with [mongocryptd](../client-side-encryption/client-side-encryption.md#mongocryptd) using the
driver's `runCommand()` API. Consequently, drivers will implicitly apply the retry policy to communication with
mongocryptd, although in practice the retry policy would never be used because mongocryptd connections are not
authenticated.

#### Overload retry policy

This specification expands the driver's retry ability to all commands if the error indicates that it is a retryable
overload error, including those not eligible for retry under the
[read](../retryable-reads/retryable-reads.md)/[write](../retryable-writes/retryable-writes.md) retry policies such as
updateMany, create collection, getMore, and generic runCommand. The new command execution method obeys the following
rules:

1. `attempt` is the execution attempt number (starting with 0). Note that `attempt` includes retries for errors that are
    not overload errors (this might include attempts under other retry policies, see
    [Interactions with Other Retry Policies](./client-backpressure.md#interaction-with-other-retry-policies)).
2. A retry attempt will only be permitted if:
    1. The error is a retryable overload error.
    2. We have not reached `MAX_RETRIES`.
        - The value of `MAX_RETRIES` is 5 and non-configurable.
        - This intentionally changes the behavior of CSOT which otherwise would retry an unlimited number of times within
            the timeout to avoid retry storms.
    3. (CSOT-only): There is still time for a retry attempt according to the
        [Client Side Operations Timeout](../client-side-operations-timeout/client-side-operations-timeout.md)
        specification.
    4. The command is a write and [retryWrites](../retryable-writes/retryable-writes.md#retrywrites) is enabled or the
        command is a read and [retryReads](../retryable-reads/retryable-reads.md#retryreads) is enabled.
        - To retry `runCommand`, both [retryWrites](../retryable-writes/retryable-writes.md#retrywrites) and
            [retryReads](../retryable-reads/retryable-reads.md#retryreads) MUST be enabled. See
            [Why must both `retryWrites` and `retryReads` be enabled to retry runCommand?](client-backpressure.md#why-must-both-retrywrites-and-retryreads-be-enabled-to-retry-runcommand)
3. If the request is eligible for retry (as outlined in step 2 above and step 4 in the
    [adaptive retry requirements](client-backpressure.md#adaptive-retry-policy) below), the client MUST apply
    exponential backoff according to the following formula:
    `backoff = jitter * min(MAX_BACKOFF, BASE_BACKOFF * 2^(attempt - 1))`
    - `jitter` is a random jitter value between 0 and 1.
    - `BASE_BACKOFF` is constant 100ms.
    - `MAX_BACKOFF` is 10000ms.
    - This results in delays of 100ms, 200ms, 400ms, 800ms, and 1600ms before accounting for jitter.
4. If the request is eligible for retry (as outlined in step 2 above and step 4 in the
    [adaptive retry requirements](client-backpressure.md#adaptive-retry-policy) below), the client MUST add the
    previously used server's address to the list of deprioritized server addresses for
    [server selection](../server-selection/server-selection.md).
5. If the request is eligible for retry (as outlined in step 2 above and step 4 in the
    [adaptive retry requirements](client-backpressure.md#adaptive-retry-policy) below) and is a retryable write:
    1. If the command is a part of a transaction, the instructions for command modification on retry for commands in
        transactions MUST be followed, as outlined in the
        [transactions](../transactions/transactions.md#interaction-with-retryable-writes) specification.
    2. If the command is a not a part of a transaction, the instructions for command modification on retry for retryable
        writes MUST be followed, as outlined in the [retryable writes](../retryable-writes/retryable-writes.md)
        specification.
6. If the request is not eligible for any retries, then the client MUST propagate errors following the behaviors
    described in the [retryable reads](../retryable-reads/retryable-reads.md),
    [retryable writes](../retryable-writes/retryable-writes.md) and the [transactions](../transactions/transactions.md)
    specifications.
    - For the purposes of error propagation, `runCommand` is considered a write.

##### Adaptive retry policy

If adaptive retries are enabled, the following rules MUST also be obeyed:

1. If the command succeeds on the first attempt, drivers MUST deposit `RETRY_TOKEN_RETURN_RATE` tokens.
    - The value is 0.1 and non-configurable.
2. If the command succeeds on a retry attempt, drivers MUST deposit `RETRY_TOKEN_RETURN_RATE`+1 tokens.
3. If a retry attempt fails with an error that is not an overload error, drivers MUST deposit 1 token.
    - An error that does not contain the `SystemOverloadedError` error label indicates that the server is healthy enough
        to handle requests. For the purposes of retry budget tracking, this counts as a success.
4. A retry attempt will only be permitted if a token can be consumed from the token bucket.
5. A retry attempt consumes 1 token from the token bucket.

#### Interaction with Other Retry Policies

The retry policy in this specification is separate from the other retry policies defined in the
[retryable reads](../retryable-reads/retryable-reads.md) and [retryable writes](../retryable-writes/retryable-writes.md)
specifications. Drivers MUST ensure:

- Only overload errors consume tokens from the token bucket before retrying.
- When a failed attempt is retried, backoff MUST be applied if and only if the error is an overload error.
- If an overload error is encountered:
    - Regardless of whether CSOT is enabled or not, the maximum number of retries for any retry policy becomes
        `MAX_RETRIES`.
    - If CSOT is enabled and a command has been retried at least `MAX_RETRIES` times, it MUST NOT be retried further.

#### Pseudocode

The following pseudocode demonstrates the unified retry policy, combining the overload retry policy defined in this
specification with the retry policies from [Retryable Reads](../retryable-reads/retryable-reads.md) and
[Retryable Writes](../retryable-writes/retryable-writes.md). For brevity, some interactions with other specs are not
included, such as error handling with `NoWritesPerformed` labels.

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
    allowed_retries = if is_csot then math.inf else 1

    while True:
        try:
            server = select_server(deprioritized_servers)
            connection = server.getConnection()
            res = execute_command(connection, command)
            if adaptive_retry:
                # Deposit tokens into the bucket on success.
                tokens = RETRY_TOKEN_RETURN_RATE
                if attempt > 0:
                    tokens += 1
                token_bucket.deposit(tokens)
            return res
        except PyMongoError as exc:
            is_retryable = (is_retryable_write(command, exc) 
                or is_retryable_read(command, exc) 
                or (exc.contains_error_label("RetryableError") and exc.contains_error_label("SystemOverloadedError")))
            is_overload = exc.contains_error_label("SystemOverloadedError")

            # if a retry fails with an error which is not an overload error, deposit 1 token
            if adaptive_retry and attempt > 0 and not is_overload:
                token_bucket.deposit(1)

            # Raise if the error is non-retryable.
            if not is_retryable:
                raise

            attempt += 1
            if is_overload:
                allowed_retries = MAX_RETRIES

            if attempt > allowed_retries:
                raise

            deprioritized_servers.append(server.address)

            if is_overload:
                jitter = random.random() # Random float between [0.0, 1.0).
                backoff = jitter * min(MAX_BACKOFF, BASE_BACKOFF * 2 ** (attempt - 1))
          
                # If the delay exceeds the deadline, bail early.
                if _csot.get_timeout():
                    if time.monotonic() + backoff > _csot.get_deadline():
                        raise

                if adaptive_retry and not token_bucket.consume(1):
                    raise

                time.sleep(backoff)
```

### Token Bucket

The overload retry policy introduces an opt-in per-client [token bucket](https://en.wikipedia.org/wiki/Token_bucket) to
limit overload error retry attempts. Although the server rejects excess commands as quickly as possible, doing so costs
CPU and creates extra contention on the connection pool which can eventually negatively affect goodput. To reduce this
risk, the token bucket will limit retry attempts during a prolonged overload.

The token bucket MUST be disabled by default and can be enabled through the `adaptiveRetries=True` connection and client
options.

The token bucket starts at its maximum capacity of 1000 for consistency with the server.

Each MongoClient instance MUST have its own token bucket. When adaptive retries are enabled, the token bucket MUST be
created when the MongoClient is initialized and exist for the lifetime of the MongoClient. Drivers MUST ensure the token
bucket implementation is thread-safe as it may be accessed concurrently by multiple operations.

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

Drivers conforming to this spec MUST add `"backpressure": True` to the
[connection handshake](../mongodb-handshake/handshake.rst). This flag allows the server to identify clients which do and
do not support backpressure. Currently, this flag is unused but in the future the server may offer different rate
limiting behavior for clients that do not support backpressure.

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
message or "command failed" log message. If an attempt of a retryable command encounters a retryable error, drivers MUST
fire a `CommandFailedEvent` and emit a "command failed" log message for the retryable error and fire a separate
`CommandStartedEvent` and emit a separate "command started" log message when executing the subsequent retry attempt.
Note that for retries, `CommandStartedEvent`s and "command started" log message may have different `connectionId`s,
since a server is reselected for a retry attempt.

### Documentation

1. Drivers MUST document that all commands support retries on server overload.
2. Driver release notes MUST make it clear to users that they may need to adjust custom retry logic to prevent an
    application from inadvertently retrying for too long (see [Backwards Compatibility](#backwards-compatibility) for
    details).

### Backwards Compatibility

The server's rate limiting can introduce higher error rates than previously would have been exposed to users under
periods of extreme server overload. The increased error rate is a tradeoff: given the choice between an overloaded
server (potential crash), or at minimum dramatically slower query execution time and a stable but lowered throughput
with higher error rate as the server load sheds, we have chosen the latter.

The changes in this specification help smooth out the impact of the server's rate limiting on users by reducing the
number of errors users see during spikes or burst workloads and help prevent retry storms by spacing out retries.
However, older drivers do not have this benefit. Drivers MUST document that:

- Users SHOULD upgrade to driver versions that officially support backpressure to avoid any impacts of server changes.
- Users who do not upgrade might need to update application error handling to handle higher rates of overload errors.

## Test Plan

See the [README](./tests/README.md) for tests.

## Motivation for Change

New load shedding mechanisms are being introduced to the server that improve its ability to remain available under
extreme load, however clients do not know how to handle the errors returned when one of its requests has been rejected.
As a result, such overload errors would currently either be propagated back to applications, increasing
externally-visible command failure rates, or be retried immediately, increasing the load on already overburdened
servers. To minimize these effects, this specification enables clients to retry requests that have been load shed in a
way that does not overburden already overloaded servers. This retry policy allows for more aggressive and effective load
shedding policies to be deployed in the future. This will also help unify the currently-divergent retry policy between
drivers and the server (mongos).

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

### Why override existing maximum number of retry attempt defaults for retryable reads and writes if an overload error is received?

Load-shedded errors indicate that the request was rejected by the server to minimize load, not that the command failed
for logical reasons. So, when determining the number of retries an operation should attempt:

- Any load-shedded errors should be retried to give them a real attempt at success
- If the command ultimately would have failed if it had not been load shed by the server, returning an actionable error
    message is preferable to a generic overload error.

The maximum retry attempt logic in this specification balances retry policies described in the
[retryable reads](../retryable-reads/retryable-reads.md) and [retryable writes](../retryable-writes/retryable-writes.md)
specifications with load-shedding behavior:

- Relying on either 1 or infinite retries (depending on whether CSOT enabled or not) preserves retry behaviors defined
    in the [retryable reads](../retryable-reads/retryable-reads.md),
    [retryable writes](../retryable-writes/retryable-writes.md) and
    [CSOT](../client-side-operations-timeout/client-side-operations-timeout.md) specifications when no overload errors are
    encountered.
- Adjusting the maximum number of retry attempts to 5 if an overload error is returned from the server gives requests
    more opportunities to succeed and helps reduce application errors.
- An alternative approach would be to retry once if we don't receive an overload error, in which case we'd retry 5
    times. The approach chosen allows for additional retries in scenarios where a non-overload error fails on a retry
    with an overload error.

### Why not apply the overload retry policy to monitoring and RTT connections?

The ingress request rate limiter only applies to authenticated connections. Neither the
[monitoring connection](../server-discovery-and-monitoring/server-monitoring.md#monitoring) nor the
[RTT pinger](../server-discovery-and-monitoring/server-monitoring.md#measuring-rtt) use authentication, and consequently
will not encounter ingress operation rate limiter errors.

It is conceivable that a driver attempting to establish a monitoring connection or RTT connection could encounter the
ingress connection rate limiter. However, in these scenarios, the driver already behaves in an appropriate manner.

If an error is encountered, both the RTT connections and monitoring connections already retry.

- The RTT pinger retries indefinitely until the monitor is reset.
- Monitoring failures will mark the server unknown, which will reset the monitor, triggering another monitoring request.

Under most circumstances, both monitoring and RTT connections wait at least `minHeartbeatFrequencyMS` between `hello`
commands, ensuring delays between retries. The notable exception is monitoring connections retrying network errors
without waiting for `minHeartbeatFrequencyMS`, which is acceptable since re-establishing monitoring is the driver's top
priority when a monitoring connection disconnects.

### Why not apply the overload policy to authentication commands or reauthentication commands?

The ingress request rate limiter only applies to authenticated connections. The server does not consider a connection to
be authenticated until after the authentication workflow has completed and during reauthentication a connection is not
considered authenticated by the server. So, authentication and reauthentication commands will not hit the ingress
operation rate limiter.

### Why must both `retryWrites` and `retryReads` be enabled to retry runCommand?

[`runCommand`](../run-command/run-command.md) is not retryable under the
[retryable reads](../retryable-reads/retryable-reads.md) and [retryable writes](../retryable-writes/retryable-writes.md)
specifications and consequently it was not historically classified as a read or write command.

The most flexible approach would be to inspect the user's command and determine if it is a read or a write. However,
this is problematic for two reasons:

- The runCommand specification specifically forbids drivers from inspecting the user's command.
- `runCommand` is commonly used to execute commands of which the driver has no knowledge and therefore cannot determine
    whether it is a read or write.

Another option is to always consider `runCommand` retryable under the overload retry policy, regardless of the setting
of [`retryReads`](../retryable-reads/retryable-reads.md#retryreads) and
[`retryWrites`](../retryable-writes/retryable-writes.md#retrywrites). However, this behavior goes against a user's
expectations: if a user disables both options, they would expect no commands to be retried.

Retrying `runCommand` only when both `retryReads` and `retryWrites` are enabled is a safe default that does not have the
pitfalls of either approach outlined by above:

- This approach does not require drivers to inspect a user's command document.
- This approach will not retry commands if a user has disabled both `retryReads` and `retryWrites`.

Additionally, both `retryReads` and `retryWrites` are enabled by default, so for most users `runCommand` will be
retried. This approach also prevents accidentally retrying a read command when only `retryWrites` is enabled, or
retrying a write command when only `retryReads` is enabled.

## Changelog

- 2026-02-20: Disable token buckets by default.

- 2026-01-09: Initial version.
