#!/bin/bash
export AWS_ACCESS_KEY_ID=DUMMYIDEXAMPLE
export AWS_SECRET_ACCESS_KEY=DUMMYEXAMPLEKEY
export AWS_DEFAULT_REGION=eu-west-2
export DYNAMODB_TABLE_NAME=cp-637250fa84046ef0
export API_KEY=fake

container_name=dynamodb-local

if [ "$(docker container inspect -f '{{.State.Running}}' $container_name 2>/dev/null)" = "true" ]; then
    docker stop $container_name
fi

docker pull amazon/$container_name
docker run --rm -d --name $container_name -p 8000:8000 amazon/$container_name &

aws dynamodb create-table --cli-input-json file://dynambodb_testing/create-table.json --endpoint-url http://localhost:8000
