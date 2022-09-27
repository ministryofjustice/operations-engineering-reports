#!/bin/bash

container_name=dynamodb-local

echo ' Stopping Container '

docker stop $container_name

unset FLASK_CONFIGURATION
unset FLASK_DEBUG
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_DEFAULT_REGION
unset DYNAMODB_TABLE_NAME
unset API_KEY

echo ' --- Exit --- '
