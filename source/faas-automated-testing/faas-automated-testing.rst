======================
FaaS Automated Testing
======================

:Status: 
:Minimum Server Version: 3.6

.. contents::

--------

Abstract
========

This specification is about the ability for drivers to automate tests for
"Functions as a Service" from continuous integration.

META
====

The keywords "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in `RFC 2119 <https://www.ietf.org/rfc/rfc2119.txt>`_.

Specification
=============

Terms
-----

FaaS
~~~~

"Function as a Service", such as AWS Lambda.

Implementing Automated FaaS Tests
---------------------------------

AWS Lambda
~~~~~~~~~~

This section describes the required setup of an AWS Lambda function and the
steps needed to automate the deployment and execution of the function in
Evergreen.

Local Execution
***************

Prerequisites
`````````````

For the initial local setup the following are required:

- The docker daemon running on the local machine.
- The [https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html](AWS SAM CLI)

The following environment variables MUST be present (See DRIVERS-2384 google doc for values):

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` - Set to us-east-1
- `MONGODB_URI` - The local MongoDB instance

Project Initialization
``````````````````````

Create the new project via SAM and follow the prompts:

.. code:: none

  sam init

For the template, select "AWS Quick Start Template".

.. code:: none

  Which template source would you like to use?
    1 - AWS Quick Start Templates
    2 - Custom Template Location
  Choice: 1

For the quick start template, select "Hello World Example".

.. code:: none

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

When prompted for language if the driver language is not Python, select "N".

.. code:: none

  Use the most popular runtime and package type? (Python and zip) [y/N]: n

Then select the runtime for your driver:

.. code:: none

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

Select Zip package type:

.. code:: none

  What package type would you like to use?
    1 - Zip
    2 - Image
  Package type: 1

Then follow the remaining prompts for the driver language to finish setup. Drivers MAY
choose to also enable X-Ray tracing and CloudWatch Application Insights during these
next steps.

Function Setup
``````````````

In the newly created project directory modify the template.yaml file:

Change default timeout to 30 seconds:

.. code:: yaml

  Globals:
    Function:
      Timeout: 30

Add a root parameter for for the MongoDB connection string:

.. code:: yaml

  Parameters:
    MongoDbUri:
      Type: String
      Description: The MongoDB connection string.

Replace all instances in the template yaml of `HelloWorld` with `MongoDB` and then
modify the root `Resources` config to add the MONGODB_URI env variable reference
and change the `CodeUri` to mongodb/ : Then rename the `hello-world` directory to `mongodb`.
Do not change the `Handler` and `Runtime` properties.

.. code:: yaml

  Resources:
    MongoDBFunction:
      Type: AWS::Serverless::Function
      Properties:
        CodeUri: mongodb/
        Environment:
          Variables:
            MONGODB_URI: !Ref MongoDbUri

Run the function locally from the same directory where the template.yaml resides:

.. code:: none

  sam build
  sam local invoke --parameter-overrides "MongoDbUri=${MONGODB_URI}"


Running in Continuous Integration
`````````````````````````````````

Running in CI requires Evergreen to be setup to assume the appropriate role in AWS
and then execute the script in drivers-evergreen-tools with the required environment
variables. An explanation of the required environment is as follows:

+-------------------------------+----------+--------------------------+
| Name                          | Description                         |
+===============================+=====================================+
| LAMBDA_AWS_ROLE_ARN           | The role ARN to assume              |
+-------------------------------+-------------------------------------+
| TEST_LAMBDA_DIRECTORY         | The lambda function directory       |
+-------------------------------+-------------------------------------+
| DRIVERS_TOOLS                 | Location of drivers-evergreen-tools |
+-------------------------------+-------------------------------------+
| DRIVERS_ATLAS_PUBLIC_API_KEY  | The Atlas public API key            |
+-------------------------------+-------------------------------------+
| DRIVERS_ATLAS_PRIVATE_API_KEY | The Atlas private API key           |
+-------------------------------+-------------------------------------+
| DRIVERS_ATLAS_LAMBDA_USER     | The Atlas cluster user name         |
+-------------------------------+-------------------------------------+
| DRIVERS_ATLAS_LAMBDA_PASSWORD | The Atlas cluster user password     |
+-------------------------------+-------------------------------------+
| DRIVERS_ATLAS_GROUP_ID        | The driver's Atlas group id         |
+-------------------------------+-------------------------------------+
| LAMBDA_STACK_NAME             | The driver's Lambda stack name      |
+-------------------------------+-------------------------------------+
| AWS_REGION                    | The function AWS region             |
+-------------------------------+-------------------------------------+
| AWS_ACCESS_KEY_ID             | Assume role atuomatically sets this |
+-------------------------------+-------------------------------------+
| AWS_SECRET_ACCESS_KEY         | Assume role automatically sets this |
+-------------------------------+-------------------------------------+
| AWS_SESSION_TOKEN             | Assume role automatically sets this |
+-------------------------------+-------------------------------------+


This is an example function in the Evergreen config that accomplishes this, using
subprocess.exec to execute a script that calls the drivers-evergreen-tools
function inside of it:

.. code:: yaml

  run deployed aws lambda tests:
  - command: ec2.assume_role
    params:
      role_arn: ${LAMBDA_AWS_ROLE_ARN}
  - command: subprocess.exec
    params:
      working_dir: src
      binary: bash
      args:
        - .evergreen/run-deployed-lambda-aws-tests.sh
      env:
        TEST_LAMBDA_DIRECTORY: ${PROJECT_DIRECTORY}/test/lambda
        DRIVERS_TOOLS: ${DRIVERS_TOOLS}
        DRIVERS_ATLAS_PUBLIC_API_KEY: ${DRIVERS_ATLAS_PUBLIC_API_KEY}
        DRIVERS_ATLAS_PRIVATE_API_KEY: ${DRIVERS_ATLAS_PRIVATE_API_KEY}
        DRIVERS_ATLAS_LAMBDA_USER: ${DRIVERS_ATLAS_LAMBDA_USER}
        DRIVERS_ATLAS_LAMBDA_PASSWORD: ${DRIVERS_ATLAS_LAMBDA_PASSWORD}
        DRIVERS_ATLAS_GROUP_ID: ${DRIVERS_ATLAS_GROUP_ID}
        LAMBDA_STACK_NAME: dbx-node-lambda
        AWS_REGION: us-east-1
        AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
        AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
        AWS_SESSION_TOKEN: ${AWS_SESSION_TOKEN}

The script itself:

.. code:: none

  #!/bin/bash
  set -o errexit  # Exit the script with error if any of the commands fail
  . ${DRIVERS_TOOLS}/.evergreen/run-deployed-lambda-aws-tests.sh

Description of the behaviour of run-deployed-lambda-aws-tests.sh:

- Creates a new Atlas cluster in a specific driver project
- Polls for the cluster SRV record when cluster creation is complete
- Builds the Lambda function locally
- Deploys the Lambda function to AWS.
- Queries for the Lambda function ARN.
- Invokes the Lambda function cold and frozen.
- Initiates a primary failover of the cluster in Atlas.
- Calls the frozen lambda function again.
- Deletes the Lambda function.
- Deletes the Atlas cluster.

