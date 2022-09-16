# AWS DynamoDB for Development and Testing

This is an example of setting up and interacting with a AWS DynamoDB local instance for development and testing purposes. This can be done stand alone or with the App.

## Prerequisite

If you have AWS cli tool already installed and completed the configure stage then skip the below steps.

```
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /
aws --version
aws configure
```

Alternatively use a profile:

```
aws configure --profile user1
```

then use the profile on the end of each command:

```
aws s3 ls --profile produser
```

Use random values for configure:

```
AWS Access Key ID [None]: ASIIAMFAKENOPZLX6J5L
AWS Secret Access Key [None]: w0pE4j5k4FlUrkIIAMFAKEdiLMKLGZlxyctrGpTam
Default region name [None]: eu-west-2
Default output format [None]: json
```

## Create local DynamoDB Table for Development

The following commands are to be used against a Docker container running an AWS DynamoDB local instance.

```
aws dynamodb create-table --cli-input-json file://dynambodb_testing/create-table.json --endpoint-url http://localhost:8000

aws dynamodb list-tables --endpoint-url http://localhost:8000

aws dynamodb batch-write-item --request-items file://dynambodb_testing/add-public-data.json --endpoint-url http://localhost:8000

aws dynamodb batch-write-item --request-items file://dynambodb_testing/add-private-data.json --endpoint-url http://localhost:8000

aws dynamodb scan --table-name cp-637250fa84046ef0 --endpoint-url http://localhost:8000

aws dynamodb get-item --consistent-read --table-name cp-637250fa84046ef0 --key '{ "filename": {"S": "data/public_github_repositories"}}' --endpoint-url http://localhost:8000

aws dynamodb update-item --table-name cp-637250fa84046ef0 --key '{ "filename": {"S": "data/public_github_repositories"}}' --update-expression "SET stored_at = :newval" --expression-attribute-values '{":newval":{"S": "2022-08-30 10:21:25"}}' --return-values ALL_NEW --endpoint-url http://localhost:8000
```

Omit ` --endpoint-url http://localhost:8000` to interact with a live AWS DynamoDB database.

## Other Useful Commands

```
aws dynamodb help
aws dynamodb COMMAND --endpoint-url http://localhost:8000
aws dynamodb delete-item --table-name cp-637250fa84046ef0 --key '{ "filename": {"S": "data/public_github_repositories"}}' --endpoint-url http://localhost:8000
aws dynamodb delete-table --table-name cp-637250fa84046ef0 --endpoint-url http://localhost:8000
aws dynamodb describe-table --table-name cp-637250fa84046ef0 --endpoint-url http://localhost:8000
```

See the [AWS CLI](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/dynamodb/index.html) for other commands.

## The Python files

The python script `helper_code.py` is used to send encrypted data to the App which can be added to a running AWS DynamoDB local instance. This requires the App and database to be up and running using one of the make commands.

The python file `dynamodb.py` has code that can interact with a running AWS DynamoDB local instance directly. The database in a container can be created and setup using the debugger via `launch.json` within the VS Code debugger.

## AWS Credentials commands

Sometimes it will be necessary to set the AWS credentials when interacting with the database, below is an example of how to set the credentials and interact with the database using those credentials. If the credentials used to create and setup the database are different to those used later on to interact with the database it will result in failures as the credentials will not be recognized by the database.

The following commands apply the AWS credentials to a terminal window only:

```
export AWS_DEFAULT_REGION=eu-west-2 && export AWS_ACCESS_KEY_ID=ASIIAMFAKENOPZLX6J5L && export AWS_SECRET_ACCESS_KEY=w0pE4j5k4FlUrkIIAMFAKEdiLMKLGZlxyctrGpTam

unset AWS_DEFAULT_REGION && unset AWS_ACCESS_KEY_ID && AWS_SECRET_ACCESS_KEY
```
