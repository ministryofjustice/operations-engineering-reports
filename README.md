# MoJ Operations Engineering Reports

[![repo standards badge](https://img.shields.io/badge/dynamic/json?color=blue&style=for-the-badge&logo=github&label=MoJ%20Compliant&query=%24.data%5B%3F%28%40.name%20%3D%3D%20%22operations-engineering-reports%22%29%5D.status&url=https%3A%2F%2Foperations-engineering-reports.cloud-platform.service.justice.gov.uk%2Fgithub_repositories)](https://operations-engineering-reports.cloud-platform.service.justice.gov.uk/github_repositories#operations-engineering-reports "Link to report")

A web application to receive JSON data and publish reports.

This is the Python / Flask version.

The live site is published [here](https://operations-engineering-reports.cloud-platform.service.justice.gov.uk/).

## Reports

This is the current list of reports, with links to the source repositories:

- [GitHub Repository Standards](https://github.com/ministryofjustice/github-repository-standards)

## Updating

Changes merged to the `main` branch will be deployed via github actions.

See `.github/workflows/cd.yaml` for details.

## Development

There are multiple ways to run the Flask App with or without an AWS DynamoDB local instance running in a Docker container.

Once running the the App can be opened in a browser `http://127.0.0.1:4567` for the development server or `http://127.0.0.1` when running the production server locally.

To be able to use the login feature and see the private repository report requires creating a `.env` file at the root of the repository, obtaining two AUTH0 values from the AUTH0 [site](https://auth0.com/) and creating an encryption key using `dynambodb_testing/helper_code.py/example_encrypt_decrypt`.

The .env layout:

```
AUTH0_CLIENT_ID=
AUTH0_CLIENT_SECRET=
AUTH0_DOMAIN=operations-engineering.eu.auth0.com
APP_SECRET_KEY=appSecret123
ENCRYPTION_KEY=
```

Edit `~/.aws/config` and add `cli_pager=` to negate the need to press a button to continue the terminal when AWS commands are completed within the termial.

Run `make local` to run a local instance of the Flask App and a local AWS DynamoDB instance. This runs the App in the terminal and the AWS DynamoDB instance in a Docker container. This will run `scripts/start-local.sh`. When running the App using this command, you may need to press Q twice to continue the terminal when the AWS commands to create and add data to the database are executed. Use `crtl + c` to cancel the App and it will automatically remove the Docker container.

Run `make dev` to run a local instance of the Flask App and a local AWS DynamoDB instance. This runs the App and database in seperate containers using Docker compose.

Run `make prod` to run a local instance of the production Flask App and a local AWS DynamoDB instance. This runs the App and database in seperate containers using Docker compose. The gunicorn production server is used in this mode. Lint will be run against the python code before the Docker container is created.

Run `make stop` to stop both Docker commands above.

## Debugging

For debugging use the `.vscode/launch.json` and VS Code. Set a breakpoint in VS Code. Run the App in VS Code. VS Code will run the App internally and in the background start and end a Docker container for the local AWS DynamoDB instance.

## Manual Testing

See the files in the `dynambodb_testing` folder for the commands and code that can be used to create, setup, add data to the table, etc to the AWS DynamoDB local instance running within a Docker container.

## AWS Credentials

AWS env variables are set and used when creating, writing and reading from the AWS DynamoDB local instance. The env variables should be the same for each operation on the database wether via an AWS command or within code else they will fail. You will find the env variables are set in the VS Code debugger start files `launch.json` and `tasks.json`, in the `start.sh` script file and the Docker compose files `docker-compose.yml` and `docker-compose-prod.yml`. This generally involves setting and using the same env values `AWS_ACCESS_KEY_ID = DUMMYIDEXAMPLE`, `AWS_SECRET_ACCESS_KEY = DUMMYEXAMPLEKEY` and `AWS_DEFAULT_REGION = eu-west-2` when creating, writing and reading the database. For production the AWS keys are over written using the following env variables values `DYNAMODB_ACCESS_KEY_ID`, `DYNAMODB_SECRET_ACCESS_KEY`, and `DYNAMODB_REGION`.

## Troubleshooting

With the database use the AWS scan command to see if the database exists and has data. If it does not exist use the commands or code to create the database and add the data. The credentials used in the App and the database must match as explained in AWS Credentials section.

## Production

In production the `Dockerfile.prod` file is used to run a [Gunicorn](https://gunicorn.org/) server, which is a Python WSGI HTTP Server for UNIX.
