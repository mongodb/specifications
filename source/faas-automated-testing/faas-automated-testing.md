# FaaS Automated Testing

- Status:
- Minimum Server Version: 3.6

______________________________________________________________________

## Abstract

This specification is about the ability for drivers to automate tests for "Functions as a Service" from continuous
integration.

## META

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## Specification

### Terms

#### FaaS

"Function as a Service", such as AWS Lambda.

### Implementing Automated FaaS Tests

#### AWS Lambda

This section describes the required setup of an AWS Lambda function and the steps needed to automate the deployment and
execution of the function in Evergreen.

##### Local Execution

###### Prerequisites

For the initial local setup the following are required:

- The docker daemon running on the local machine.
- The [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

AWS access MUST be configured, either through `$HOME/.aws/credentials` or with the following environment variables:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` - Set to us-east-1
- `MONGODB_URI` - The local MongoDB instance

###### Project Initialization

Create the new project via SAM and follow the prompts:

```bash
sam init
```

For the template, select "AWS Quick Start Template".

```bash
Which template source would you like to use?
  1 - AWS Quick Start Templates
  2 - Custom Template Location
Choice: 1
```

For the quick start template, select "Hello World Example".

```bash
Choose an AWS Quick Start application template
  1 - Hello World Example
  2 - Multi-step workflow
  3 - Serverless API
  4 - Scheduled task
  5 - Standalone function
  6 - Data processing
  7 - Infrastructure event management
  8 - Hello World Example With Powertools
  9 - Serverless Connector Hello World Example
  10 - Multi-step workflow with Connectors
  11 - Lambda EFS example
  12 - DynamoDB Example
  13 - Machine Learning
Template: 1
```

When prompted for language if the driver language is not Python, select "N".

```text
Use the most popular runtime and package type? (Python and zip) [y/N]: n
```

Then select the runtime for your driver:

```bash
Which runtime would you like to use?
  1 - aot.dotnet7 (provided.al2)
  2 - dotnet6
  3 - dotnet5.0
  4 - dotnetcore3.1
  5 - go1.x
  6 - go (provided.al2)
  7 - graalvm.java11 (provided.al2)
  8 - graalvm.java17 (provided.al2)
  9 - java11
  10 - java8.al2
  11 - java8
  12 - nodejs18.x
  13 - nodejs16.x
  14 - nodejs14.x
  15 - nodejs12.x
  16 - python3.9
  17 - python3.8
  18 - python3.7
  19 - ruby2.7
  20 - rust (provided.al2)
Runtime: 12
```

Select Zip package type:

```bash
What package type would you like to use?
  1 - Zip
  2 - Image
Package type: 1
```

Then follow the remaining prompts for the driver language to finish setup. Drivers MAY choose to also enable X-Ray
tracing and CloudWatch Application Insights during these next steps.

*NOTE* - If the driver wants to skip prompts in the setup it can provide defaults to the sam init command. Example:

```bash
sam init --name my-hello-world-app \
    --app-template "hello-world" \
    --runtime go1.x \
    --package-type Zip
```

###### Function Setup

In the newly created project directory modify the template.yaml file:

Change default timeout to 30 seconds:

```yaml
Globals:
  Function:
    Timeout: 30
```

Add a root parameter for the MongoDB connection string:

```yaml
Parameters:
  MongoDbUri:
    Type: String
    Description: The MongoDB connection string.
```

Replace all instances in the template.yaml of `HelloWorld` with `MongoDB` and then modify the root `Resources` config to
add the MONGODB_URI env variable reference and change the `CodeUri` to mongodb/ : Then rename the `hello-world`
directory to `mongodb`. Do not change the `Handler` and `Runtime` properties.

```yaml
Resources:
  MongoDBFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: mongodb/
      Environment:
        Variables:
          MONGODB_URI: !Ref MongoDbUri
```

If the generated template contains Resources.Events.CatchAll.Properties.Path then change it to /mongodb and if it also
contains Resources.Handler modify that to mongodb as well.

```yaml
Resources:
  Events:
    CatchAll:
      Properties:
        Path: /mongodb
  Handler: mongodb
```

If possible, install the current driver under test into the lambda environment, to avoid having to release the driver in
order to test features or catch regressions. See docs on
<https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-zip.html> for how to create a .zip file deployment
with dependencies.

Start the local MongoDB instance. If using Docker Desktop on MacOS, set
`MONGODB_URI=mongodb://host.docker.internal:27017` in order for the function to be able to access the host port.

Run the function locally from the same directory where the template.yaml resides:

```bash
sam build
sam local invoke --parameter-overrides "MongoDbUri=${MONGODB_URI}"
```

*NOTE* "127.0.0.1" in the MONGODB_URI MUST be replaced with "host.docker.internal" to test a local MongoDB deployment.
If "host.docker.internal" does not work (can occur on M1 machines), drivers MAY choose to use a
[bridged docker container](https://docs.docker.com/network/bridge/) to test locally.

###### Implementing the Function

Drivers MUST setup the function as would be done in their appropriate language. In the function implementation the
driver MUST:

- Create a MongoClient that points to MONGODB_URI.
- Add listeners for the following monitoring events: ServerHeartbeatStarted, ServerHeartbeatFailed, CommandSucceeded,
    CommandFailed, ConnectionCreated, ConnectionClosed.
- Drivers MUST perform a single insert and then a single delete of the inserted document to force write operations on
    the primary node.
- Drivers MUST record the durations and counts of the heartbeats, the durations of the commands, as well as keep track
    of the number of open connections, and report this information in the function response as JSON.
- Drivers MUST assert no ServerHeartbeat events contain the `awaited=True` flag to confirm that the streaming protocol
    is disabled ([DRIVERS-2578](https://jira.mongodb.org/browse/DRIVERS-2578)).

###### Running in Continuous Integration

Running in CI requires Evergreen to be setup to assume the appropriate role in AWS and then execute the script in
drivers-evergreen-tools with the required environment variables. An explanation of the required environment is as
follows:

| Name                          | Description                         |
| ----------------------------- | ----------------------------------- |
| LAMBDA_AWS_ROLE_ARN           | The role ARN to assume              |
| TEST_LAMBDA_DIRECTORY         | The lambda function directory       |
| DRIVERS_TOOLS                 | Location of drivers-evergreen-tools |
| DRIVERS_ATLAS_PUBLIC_API_KEY  | The Atlas public API key            |
| DRIVERS_ATLAS_PRIVATE_API_KEY | The Atlas private API key           |
| DRIVERS_ATLAS_LAMBDA_USER     | The Atlas cluster user name         |
| DRIVERS_ATLAS_LAMBDA_PASSWORD | The Atlas cluster user password     |
| DRIVERS_ATLAS_GROUP_ID        | The driver's Atlas group id         |
| LAMBDA_STACK_NAME             | The driver's Lambda stack name      |
| AWS_REGION                    | The function AWS region             |
| AWS_ACCESS_KEY_ID             | Assume role automatically sets this |
| AWS_SECRET_ACCESS_KEY         | Assume role automatically sets this |
| AWS_SESSION_TOKEN             | Assume role automatically sets this |

The value for `LAMBDA_AWS_ROLE_ARN` must be stored in Evergreen project settings. The value can be found in the
`drivers/atlas-qa` vault.

The values for `DRIVERS_ATLAS_PUBLIC_API_KEY`, `DRIVERS_ATLAS_PRIVATE_API_KEY`, `DRIVERS_ATLAS_LAMBDA_USER`,
`DRIVERS_ATLAS_LAMBDA_PASSWORD` and `DRIVERS_ATLAS_GROUP_ID` can be obtained programmatically from the
`drivers/atlas-qa` vault.

See
[Secrets Handling README](https://github.com/mongodb-labs/drivers-evergreen-tools/blob/master/.evergreen/secrets_handling/README.md)
for details on how to access the secrets.

Supported Evergreen variants that have the AWS SAM CLI installed:

- ubuntu2204
- ubuntu1804
- ubuntu1804-workstation
- ubuntu2204-arm64
- ubuntu2004-arm64
- ubuntu1804-arm64
- rhel90
- rhel80
- rhel84
- rhel90-selinux
- rhel80-selinux
- rhel90-arm64
- rhel82-arm64

This is an example task group in the Evergreen config that accomplishes this, using subprocess.exec to execute scripts
that call the drivers-evergreen-tools functions inside of it for setup, teardown, and execution:

```yaml
tasks:
  - name: "test-aws-lambda-deployed"
    commands:
      - func: "install dependencies"
      - command: ec2.assume_role
        params:
          role_arn: ${LAMBDA_AWS_ROLE_ARN}
          duration_seconds: 3600
      - command: subprocess.exec
        params:
          working_dir: src
          binary: bash
          add_expansions_to_env: true
          args:
            - ${DRIVERS_TOOLS}/.evergreen/aws_lambda/run-deployed-lambda-aws-tests.sh
          env:
            TEST_LAMBDA_DIRECTORY: ${PROJECT_DIRECTORY}/test/lambda
            AWS_REGION: us-east-1
task_groups:
  - name: test_aws_lambda_task_group
    setup_group:
      - func: fetch source
      - command: subprocess.exec
        params:
          working_dir: src
          binary: bash
          add_expansions_to_env: true
          args:
            - ${DRIVERS_TOOLS}/.evergreen/atlas/setup-atlas-cluster.sh
      - command: expansions.update
        params:
          file: src/atlas-expansion.yml
    teardown_group:
      - command: subprocess.exec
        params:
          working_dir: src
          binary: bash
          add_expansions_to_env: true
          args:
            - ${DRIVERS_TOOLS}/.evergreen/atlas/teardown-atlas-cluster.sh
    setup_group_can_fail_task: true
    setup_group_timeout_secs: 1800
    tasks:
      - test-aws-lambda-deployed
```

Drivers MUST run the function on a single variant in Evergreen, in order to not potentially hit the Atlas API rate
limit. The variant itself MUST have the SAM CLI installed.

Description of the behaviour of run-deployed-lambda-aws-tests.sh:

- Builds the Lambda function locally
- Deploys the Lambda function to AWS.
- Queries for the Lambda function ARN.
- Invokes the Lambda function cold and frozen.
- Initiates a primary failover of the cluster in Atlas.
- Calls the frozen lambda function again.
- Deletes the Lambda function.

## Changelog

- 2025-08-07: Added instructions for accessing secrets from the vault.
- 2024-02-27: Migrated from reStructuredText to Markdown.
- 2023-08-21: Drivers MUST assert that the streaming protocol is disabled in the Lambda function.
- 2023-08-17: Fixed URI typo, added host note, increase assume role duration.
- 2023-06-22: Updated evergreen configuration to use task groups.
- 2023-04-14: Added list of supported variants, added additional template config.
