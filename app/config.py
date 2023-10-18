import os
from types import SimpleNamespace

config = SimpleNamespace(
    database=SimpleNamespace(
        endpoint=os.environ.get('DATABASE_ENDPOINT') or 'dynamodb-local',
        name=os.environ.get('DATABASE_NAME') or 'dynamo'
    )
)
