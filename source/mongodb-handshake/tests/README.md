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

## Client Metadata Update Prose Tests

Drivers that do not emit events for commands issued as part of the handshake with the server will need to create a
test-only backdoor mechanism to intercept the handshake `hello` command for verification purposes.

Client metadata specified as part of a "Create a `MongoClient` instance" step MUST use an API which appends the
specified metadata _during_ `MongoClient` initialization.

Client metadata specified as part of an "Append the `DriverInfoOptions`" step MUST use an API which appends the
specified metadata _after_ `MongoClient` initialization.

### Test 1: Test that the driver updates metadata

Drivers should verify that metadata provided after `MongoClient` initialization is appended, not replaced, and is
visible in the `hello` command of new connections.

There are multiple test cases parameterized with `DriverInfoOptions` to be appended after `MongoClient` initialization.
Before each test case, perform the setup.

#### Setup

1. Create a `MongoClient` instance with the following:

    - `maxIdleTimeMS` set to `1ms`

    - Client metadata appended with the following `DriverInfoOptions`:

        | Field    | Value            |
        | -------- | ---------------- |
        | name     | library          |
        | version  | 1.2              |
        | platform | Library Platform |

2. Send a `ping` command to the server and verify that the command succeeds.

3. Save intercepted `client` document as `initialClientMetadata`.

4. Wait 5ms for the connection to become idle.

#### Parameterized test cases

| Case | Name      | Version | Platform           |
| ---- | --------- | ------- | ------------------ |
| 1    | framework | 2.0     | Framework Platform |
| 2    | framework | 2.0     | null               |
| 3    | framework | null    | Framework Platform |
| 4    | framework | null    | null               |

#### Running a test case

1. Append the `DriverInfoOptions` from the selected test case to the `MongoClient` metadata.

2. Send a `ping` command to the server and verify:

    - The command succeeds.

    - The framework metadata is appended to the existing `DriverInfoOptions` in the `client.driver` fields of the `hello`
        command, with values separated by a pipe `|`.

        - `client.driver.name` is `library|<name>`, where `<name>` is the empty string if the test case's name is null. The
            delimiter is appended unconditionally so name and version stay aligned by index.
        - `client.driver.version` is `1.2|<version>`, where `<version>` is the empty string if the test case's version is
            null.
        - `client.platform`:
            - If test case's platform is non-null: `Library Platform|<platform>`
            - Otherwise, the field remains unchanged: `Library Platform`

    - All other subfields in the `client` document remain unchanged from `initialClientMetadata`.

### Test 2: Multiple Successive Metadata Updates

Drivers should verify that after `MongoClient` initialization, metadata can be updated multiple times, not replaced, and
is visible in the `hello` command of new connections.

There are multiple test cases parameterized with `DriverInfoOptions` to be appended after a previous metadata update.
Before each test case, perform the setup.

#### Setup

1. Create a `MongoClient` instance with:

    - `maxIdleTimeMS` set to `1ms`

2. Append the following `DriverInfoOptions` to the `MongoClient` metadata:

    | Field    | Value            |
    | -------- | ---------------- |
    | name     | library          |
    | version  | 1.2              |
    | platform | Library Platform |

3. Send a `ping` command to the server and verify that the command succeeds.

4. Save intercepted `client` document as `clientMetadata`.

5. Wait 5ms for the connection to become idle.

##### Parameterized test cases

| Case | Name      | Version | Platform           |
| ---- | --------- | ------- | ------------------ |
| 1    | framework | 2.0     | Framework Platform |
| 2    | framework | 2.0     | null               |
| 3    | framework | null    | Framework Platform |
| 4    | framework | null    | null               |

##### Running a test case

1. Append the `DriverInfoOptions` from the selected test case to the `MongoClient` metadata.

2. Send a `ping` command to the server and verify:

    - The command succeeds.

    - The framework metadata is appended to the existing `DriverInfoOptions` in the `client.driver` fields of the `hello`
        command, with values separated by a pipe `|`.

        - `client.driver.name` is `library|<name>`, where `<name>` is the empty string if the test case's name is null. The
            delimiter is appended unconditionally so name and version stay aligned by index.
        - `client.driver.version` is `1.2|<version>`, where `<version>` is the empty string if the test case's version is
            null.
        - `client.platform`:
            - If test case's platform is non-null: `Library Platform|<platform>`
            - Otherwise, the field remains unchanged: `Library Platform`

    - All other subfields in the `client` document remain unchanged from `clientMetadata`.

### Test 3: Multiple Successive Metadata Updates with Duplicate Data

There are multiple test cases parameterized with `DriverInfoOptions` to be appended after a previous metadata update.
Before each test case, perform the setup.

#### Setup

1. Create a `MongoClient` instance with:

    - `maxIdleTimeMS` set to `1ms`

2. Append the following `DriverInfoOptions` to the `MongoClient` metadata:

    | Field    | Value            |
    | -------- | ---------------- |
    | name     | library          |
    | version  | 1.2              |
    | platform | Library Platform |

3. Send a `ping` command to the server and verify that the command succeeds.

4. Save intercepted `client` document as `updatedClientMetadata`.

5. Wait 5ms for the connection to become idle.

##### Parameterized test cases

| Case | Name      | Version | Platform           |
| ---- | --------- | ------- | ------------------ |
| 1    | library   | 1.2     | Library Platform   |
| 2    | framework | 1.2     | Library Platform   |
| 3    | library   | 2.0     | Library Platform   |
| 4    | library   | 1.2     | Framework Platform |
| 5    | framework | 2.0     | Library Platform   |
| 6    | framework | 1.2     | Framework Platform |
| 7    | library   | 2.0     | Framework Platform |

##### Running a test case

1. Append the `DriverInfoOptions` from the selected test case to the `MongoClient` metadata.

2. Send a `ping` command to the server and verify:

    - The command succeeds.

    - The framework metadata is appended to the existing `DriverInfoOptions` in the `client.driver` fields of the `hello`
        command, with values separated by a pipe `|`. To simplify assertions in these tests, strip out the default driver
        info that is automatically added by the driver (ex: `metadata.name.split('|').slice(1).join('|')`).

        - If the test case's DriverInfo is identical to the driver info from setup step 2 (test case 1):
            - Assert `metadata.driver.name` is equal to `library`
            - Assert `metadata.driver.version` is equal to `1.2`
            - Assert `metadata.platform` is equal to `LibraryPlatform`
        - Otherwise:
            - Assert `metadata.driver.name` is equal to `library|<name>`
            - Assert `metadata.driver.version` is equal to `1.2|<version>`
            - Assert `metadata.platform` is equal to `LibraryPlatform|<platform>`

    - All other subfields in the `client` document remain unchanged from `updatedClientMetadata`.

### Test 4: Multiple Metadata Updates with Duplicate Data

1. Create a `MongoClient` instance with:

    - `maxIdleTimeMS` set to `1ms`

2. Append the following `DriverInfoOptions` to the `MongoClient` metadata:

    | Field    | Value            |
    | -------- | ---------------- |
    | name     | library          |
    | version  | 1.2              |
    | platform | Library Platform |

3. Send a `ping` command to the server and verify that the command succeeds.

4. Wait 5ms for the connection to become idle.

5. Append the following `DriverInfoOptions` to the `MongoClient` metadata:

    | Field    | Value              |
    | -------- | ------------------ |
    | name     | framework          |
    | version  | 2.0                |
    | platform | Framework Platform |

6. Send a `ping` command to the server and verify that the command succeeds.

7. Save intercepted `client` document as `clientMetadata`.

8. Wait 5ms for the connection to become idle.

9. Append the following `DriverInfoOptions` to the `MongoClient` metadata:

    | Field    | Value            |
    | -------- | ---------------- |
    | name     | library          |
    | version  | 1.2              |
    | platform | Library Platform |

10. Send a `ping` command to the server and verify that the command succeeds.

11. Save intercepted `client` document as `updatedClientMetadata`.

12. Assert that `clientMetadata` is identical to `updatedClientMetadata`.

### Test 5: Metadata is not appended if identical to initial metadata

1. Create a `MongoClient` instance with:

    - `maxIdleTimeMS` set to `1ms`

    - Client metadata appended with the following `DriverInfoOptions`:

        | Field    | Value            |
        | -------- | ---------------- |
        | name     | library          |
        | version  | 1.2              |
        | platform | Library Platform |

2. Send a `ping` command to the server and verify that the command succeeds.

3. Save intercepted `client` document as `clientMetadata`.

4. Wait 5ms for the connection to become idle.

5. Append the following `DriverInfoOptions` to the `MongoClient` metadata:

    | Field    | Value            |
    | -------- | ---------------- |
    | name     | library          |
    | version  | 1.2              |
    | platform | Library Platform |

6. Send a `ping` command to the server and verify that the command succeeds.

7. Save intercepted `client` document as `updatedClientMetadata`.

8. Assert that `clientMetadata` is identical to `updatedClientMetadata`.

### Test 6: Metadata is not appended if identical to initial metadata (separated by non-identical metadata)

1. Create a `MongoClient` instance with:

    - `maxIdleTimeMS` set to `1ms`

    - Client metadata appended with the following `DriverInfoOptions`:

        | Field    | Value            |
        | -------- | ---------------- |
        | name     | library          |
        | version  | 1.2              |
        | platform | Library Platform |

2. Send a `ping` command to the server and verify that the command succeeds.

3. Wait 5ms for the connection to become idle.

4. Append the following `DriverInfoOptions` to the `MongoClient` metadata:

    | Field    | Value            |
    | -------- | ---------------- |
    | name     | framework        |
    | version  | 1.2              |
    | platform | Library Platform |

5. Send a `ping` command to the server and verify that the command succeeds.

6. Save intercepted `client` document as `clientMetadata`.

7. Wait 5ms for the connection to become idle.

8. Append the following `DriverInfoOptions` to the `MongoClient` metadata:

    | Field    | Value            |
    | -------- | ---------------- |
    | name     | library          |
    | version  | 1.2              |
    | platform | Library Platform |

9. Send a `ping` command to the server and verify that the command succeeds.

10. Save intercepted `client` document as `updatedClientMetadata`.

11. Assert that `clientMetadata` is identical to `updatedClientMetadata`.

### Test 7: Empty strings are considered unset when appending duplicate metadata

Drivers should verify that after `MongoClient` initialization, metadata can be updated multiple times, not replaced, and
is visible in the `hello` command of new connections.

There are multiple test cases parameterized with `DriverInfoOptions` to be appended after a previous metadata update.
Before each test case, perform the setup.

##### Parameterized test cases

> [!NOTE]
> Drivers whose API allows `client.driver.name` to be unset MAY implement Case 1.

###### Appended metadata

| Case  | Name     | Version | Platform             |
| ----- | -------- | ------- | -------------------- |
| ~~1~~ | ~~null~~ | ~~1.2~~ | ~~Library Platform~~ |
| 2     | library  | null    | Library Platform     |
| 3     | library  | 1.2     | null                 |

###### Duplicate Metadata

| Case  | Name    | Version | Platform             |
| ----- | ------- | ------- | -------------------- |
| ~~1~~ | ~~""~~  | ~~1.2~~ | ~~Library Platform~~ |
| 2     | library | ""      | Library Platform     |
| 3     | library | 1.2     | ""                   |

##### Running a test case

1. Create a `MongoClient` instance with:

    - `maxIdleTimeMS` set to `1ms`

2. Append the `DriverInfoOptions` from the selected test case from the appended metadata section.

3. Send a `ping` command to the server and verify that the command succeeds.

4. Save intercepted `client` document as `clientMetadata`.

5. Wait 5ms for the connection to become idle.

6. Append the `DriverInfoOptions` from the selected test case from the duplicate metadata section.

7. Send a `ping` command to the server and verify the command succeeds.

8. Store the response as `updatedClientMetadata`.

9. Assert that `clientMetadata` is identical to `updatedClientMetadata`.

### Test 8: Empty strings are considered unset when appending metadata identical to initial metadata

Drivers should verify that after `MongoClient` initialization, metadata can be updated multiple times, not replaced, and
is visible in the `hello` command of new connections.

There are multiple test cases parameterized with `DriverInfoOptions` to be appended after a previous metadata update.
Before each test case, perform the setup.

##### Parameterized test cases

###### Initial metadata

| Case  | Name     | Version | Platform             |
| ----- | -------- | ------- | -------------------- |
| ~~1~~ | ~~null~~ | ~~1.2~~ | ~~Library Platform~~ |
| 2     | library  | null    | Library Platform     |
| 3     | library  | 1.2     | null                 |

###### Appended Metadata

| Case  | Name     | Version | Platform             |
| ----- | -------- | ------- | -------------------- |
| ~~1~~ | ~~null~~ | ~~1.2~~ | ~~Library Platform~~ |
| 2     | library  | ""      | Library Platform     |
| 3     | library  | 1.2     | ""                   |

##### Running a test case

1. Create a `MongoClient` instance with:

    - `maxIdleTimeMS` set to `1ms`
    - Client metadata appended with the `DriverInfoOptions` from the selected test case from the initial metadata
        section.

2. Send a `ping` command to the server and verify that the command succeeds.

3. Save intercepted `client` document as `initialClientMetadata`.

4. Wait 5ms for the connection to become idle.

5. Append the `DriverInfoOptions` from the selected test case from the appended metadata section.

6. Send a `ping` command to the server and verify the command succeeds.

7. Store the response as `updatedClientMetadata`.

8. Assert that `initialClientMetadata` is identical to `updatedClientMetadata`.

### Test 9: Handshake documents include `backpressure: "2"`

These tests require a mechanism for observing handshake documents sent to the server.

1. Create a `MongoClient` that is configured to record all handshake documents sent to the server as a part of
    connection establishment.

2. Send a `ping` command to the server and verify that the command succeeds. This ensure that a connection is
    established on all topologies.

3. Assert that for every handshake document intercepted:

    1. The document has a field `backpressure` whose value is `"2"`.

### Test 10: Entries in `driver.name` and `driver.version` correspond by index

Drivers should verify that each appended `DriverInfoOptions` contributes exactly one entry to `client.driver.name` and
one to `client.driver.version`, so that the two fields can be split on the delimiter to recover which version belongs to
which library.

The driver's own name and version always occupy the first entry of each field, so every expected value below is written
relative to them. `<driver-name>` and `<driver-version>` stand for the values the driver reports for itself.

These tests require a mechanism for observing handshake documents sent to the server.

#### Setup

Repeat for each parameterized test case:

1. Create a `MongoClient` instance with a `maxIdleTimeMS` set to `1ms`

2. Send a `ping` command to the server and verify that the command succeeds.

3. Wait 5ms for the connection to become idle.

#### Parameterized test cases

Each case appends the listed `DriverInfoOptions` in order. `null` means the field is not set. `platform` is set only in
Case 10, which exercises duplicate detection across every field; `platform` is not itself index-aligned and is otherwise
covered by Tests 1 through 3.

| Case | Description                                 | Appended options                      | Expected `driver.name`         | Expected `driver.version`            |
| ---- | ------------------------------------------- | ------------------------------------- | ------------------------------ | ------------------------------------ |
| 1    | Gap in middle (name)                        | (null, null), (F2, null)              | `<driver-name>\|\|F2`          | `<driver-version>\|\|`               |
| 2    | Gap in middle (version)                     | (F1, null), (F2, 2.0)                 | `<driver-name>\|F1\|F2`        | `<driver-version>\|\|2.0`            |
| 3    | Trailing delimiter retained                 | (F1, null)                            | `<driver-name>\|F1`            | `<driver-version>\|`                 |
| 4    | Equal versions do not collapse              | (F1, `<driver-version>`)              | `<driver-name>\|F1`            | `<driver-version>\|<driver-version>` |
| 5    | Equal names do not collapse                 | (`<driver-name>`, 1.0)                | `<driver-name>\|<driver-name>` | `<driver-version>\|1.0`              |
| 6    | Duplicates deduplicate                      | (F1, 1.0), (F1, 1.0)                  | `<driver-name>\|F1`            | `<driver-version>\|1.0`              |
| 7    | All versions absent                         | (F1, null), (F2, null)                | `<driver-name>\|F1\|F2`        | `<driver-version>\|\|`               |
| 8    | All names absent                            | (null, 1.0), (null, 2.0)              | `<driver-name>\|\|`            | `<driver-version>\|1.0\|2.0`         |
| 9    | Non-adjacent duplicate                      | (F1, 1.0), (F2, 2.0), (F1, 1.0)       | `<driver-name>\|F1\|F2`        | `<driver-version>\|1.0\|2.0`         |
| 10   | Platform-only difference is not a duplicate | (F1, 1.0, P1), (F1, 1.0, P2)          | `<driver-name>\|F1\|F1`        | `<driver-version>\|1.0\|1.0`         |
| 11   | Wrapper matching the driver's own identity  | (`<driver-name>`, `<driver-version>`) | `<driver-name>\|<driver-name>` | `<driver-version>\|<driver-version>` |
| 12   | Duplicates with an unset field deduplicate  | (F1, null), (F1, null)                | `<driver-name>\|F1`            | `<driver-version>\|`                 |

> [!NOTE]
> Cases 1 and 8 only apply to drivers whose API allows `driver.name` to be unset. Drivers that require a name MAY skip
> them.

### Test 11: Appending metadata containing the delimiter raises an error

Drivers should verify that appending a `DriverInfoOptions` whose fields contain the `|` delimiter raises an error, and
that the metadata accumulated before the failed append is left unchanged.

These tests require a mechanism for observing handshake documents sent to the server.

##### Parameterized test cases

| Case | Field containing the delimiter | Name          | Version | Platform              |
| ---- | ------------------------------ | ------------- | ------- | --------------------- |
| 1    | `name`                         | `frame\|work` | 2.0     | Framework Platform    |
| 2    | `version`                      | framework     | `2\|0`  | Framework Platform    |
| 3    | `platform`                     | framework     | 2.0     | `Framework\|Platform` |

##### Running a test case

1. Create a `MongoClient` instance with:

    - `maxIdleTimeMS` set to `1ms`

    - Client metadata initialized with the following `DriverInfoOptions`:

        - name: `library`
        - version: `1.2`
        - platform: `Library Platform`

2. Send a `ping` command to the server and verify that the command succeeds.

3. Wait 5ms for the connection to become idle.

4. Append the `DriverInfoOptions` from the selected test case and assert that an error is raised.

5. Wait 5ms for the connection to become idle so that the next operation establishes a new connection and handshakes
    again.

6. Assert that the intercepted `client` document is unchanged by the failed append, that is:

    - `client.driver.name` is `<driver-name>|library`
    - `client.driver.version` is `<driver-version>|1.2`
    - `client.platform` is `<driver-platform>|Library Platform`
