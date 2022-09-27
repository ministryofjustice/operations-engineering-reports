#!/bin/bash

/bin/bash scripts/start-db-dev.sh

export AWS_ACCESS_KEY_ID=DUMMYIDEXAMPLE
export AWS_SECRET_ACCESS_KEY=DUMMYEXAMPLEKEY
export AWS_DEFAULT_REGION=eu-west-2
export DYNAMODB_TABLE_NAME=cp-637250fa84046ef0
export API_KEY=default123
export FLASK_CONFIGURATION=development
export FLASK_DEBUG=true

python3 -m venv venv
source venv/bin/activate
venv/bin/pip3 install -r requirements.txt
python3 operations_engineering_reports.py

trap '' EXIT
/bin/bash scripts/stop-db.sh
