#!/bin/bash
python3 -m venv venv
source venv/bin/activate
venv/bin/pip3 install -r requirements.txt
export FLASK_CONFIGURATION=development
export FLASK_DEBUG=true
export AWS_ACCESS_KEY_ID=DUMMYIDEXAMPLE
export AWS_SECRET_ACCESS_KEY=DUMMYEXAMPLEKEY
export AWS_DEFAULT_REGION=eu-west-2
export DYNAMODB_TABLE_NAME=cp-637250fa84046ef0
docker stop dynamodb-local
docker pull amazon/dynamodb-local
docker run --rm -d --name dynamodb-local -p 8000:8000 amazon/dynamodb-local &
sleep 5
aws dynamodb create-table --cli-input-json file://dynambodb_testing/create-table.json --endpoint-url http://localhost:8000
aws dynamodb batch-write-item --request-items file://dynambodb_testing/add-public-data.json --endpoint-url http://localhost:8000
aws dynamodb batch-write-item --request-items file://dynambodb_testing/add-private-data.json --endpoint-url http://localhost:8000
python3 operations_engineering_reports.py

trap '' EXIT
docker stop dynamodb-local
unset FLASK_CONFIGURATION
unset FLASK_DEBUG
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_DEFAULT_REGION
unset DYNAMODB_TABLE_NAME
echo ' --- Exit --- '
