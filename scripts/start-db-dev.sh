#!/bin/bash
export DYNAMODB_ACCESS_KEY_ID=DUMMYIDEXAMPLE
export DYNAMODB_SECRET_ACCESS_KEY=DUMMYEXAMPLEKEY
export DYNAMODB_DEFAULT_REGION=eu-west-2
export DYNAMODB_TABLE_NAME=cp-637250fa84046ef0
export API_KEY=fake

docker-compose -f docker-compose.yml up -d --build

aws dynamodb create-table --cli-input-json file://dynambodb_testing/create-table.json --endpoint-url http://localhost:8000 > /dev/null
