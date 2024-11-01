# MongoDB Handshake Tests

## Prose Tests

### Test 1: Test that environment metadata is properly captured

Drivers that capture values for `client.env` should test that a connection and hello command succeeds in the presence of
the following sets of environment variables:

1. Valid AWS

    | Environment Variable              | Value              |
    | --------------------------------- | ------------------ |
    | `AWS_EXECUTION_ENV`               | `AWS_Lambda_java8` |
    | `AWS_REGION`                      | `us-east-2`        |
    | `AWS_LAMBDA_FUNCTION_MEMORY_SIZE` | `1024`             |

2. Valid Azure

    | Environment Variable       | Value  |
    | -------------------------- | ------ |
    | `FUNCTIONS_WORKER_RUNTIME` | `node` |

3. Valid GCP

    | Environment Variable   | Value         |
    | ---------------------- | ------------- |
    | `K_SERVICE`            | `servicename` |
    | `FUNCTION_MEMORY_MB`   | `1024`        |
    | `FUNCTION_TIMEOUT_SEC` | `60`          |
    | `FUNCTION_REGION`      | `us-central1` |

4. Valid Vercel

    | Environment Variable | Value  |
    | -------------------- | ------ |
    | `VERCEL`             | `1`    |
    | `VERCEL_REGION`      | `cdg1` |

5. Invalid - multiple providers

    | Environment Variable       | Value              |
    | -------------------------- | ------------------ |
    | `AWS_EXECUTION_ENV`        | `AWS_Lambda_java8` |
    | `FUNCTIONS_WORKER_RUNTIME` | `node`             |

6. Invalid - long string

    | Environment Variable | Value                  |
    | -------------------- | ---------------------- |
    | `AWS_EXECUTION_ENV`  | `AWS_Lambda_java8`     |
    | `AWS_REGION`         | `a` repeated 512 times |

7. Invalid - wrong types

    | Environment Variable              | Value              |
    | --------------------------------- | ------------------ |
    | `AWS_EXECUTION_ENV`               | `AWS_Lambda_java8` |
    | `AWS_LAMBDA_FUNCTION_MEMORY_SIZE` | `big`              |

8. Invalid - `AWS_EXECUTION_ENV` does not start with `"AWS_Lambda_"`

    | Environment Variable | Value |
    | -------------------- | ----- |
    | `AWS_EXECUTION_ENV`  | `EC2` |

9. Valid container and FaaS provider. This test MUST verify that both the container metadata and the AWS Lambda metadata
    is present in `client.env`.

    | Environment Variable              | Value              |
    | --------------------------------- | ------------------ |
    | `AWS_EXECUTION_ENV`               | `AWS_Lambda_java8` |
    | `AWS_REGION`                      | `us-east-2`        |
    | `AWS_LAMBDA_FUNCTION_MEMORY_SIZE` | `1024`             |
    | `KUBERNETES_SERVICE_HOST`         | `1`                |

### Test 2: Test that the driver accepts an arbitrary auth mechanism

1. Mock the server response in a way that `saslSupportedMechs` array in the `hello` command response contains an
    arbitrary string.

2. Create and connect a `Connection` object that connects to the server that returns the mocked response.

3. Assert that no error is raised.
