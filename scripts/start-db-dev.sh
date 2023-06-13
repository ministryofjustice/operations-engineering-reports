#!/bin/bash
export AWS_ACCESS_KEY_ID=DUMMYIDEXAMPLE
export AWS_SECRET_ACCESS_KEY=DUMMYEXAMPLEKEY
export AWS_DEFAULT_REGION=eu-west-2
export DYNAMODB_TABLE_NAME=cp-637250fa84046ef0
export API_KEY=fake

docker-compose -f docker-compose.yml up -d --build

aws dynamodb create-table --cli-input-json file://dynambodb_testing/create-table.json --endpoint-url http://localhost:8000 > /dev/null
aws dynamodb batch-write-item --request-items file://dynambodb_testing/add-public-data.json --endpoint-url http://localhost:8000 > /dev/null
aws dynamodb batch-write-item --request-items file://dynambodb_testing/add-private-data.json --endpoint-url http://localhost:8000 > /dev/null
