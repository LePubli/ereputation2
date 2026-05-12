#!/bin/bash
set -e

echo "⏳ Waiting for database..."
python -c "
import time, psycopg2, os
for i in range(30):
    try:
        psycopg2.connect(os.environ['DATABASE_URL'])
        print('✅ Database ready')
        break
    except Exception as e:
        print(f'Retry {i+1}/30: {e}')
        time.sleep(2)
else:
    print('❌ Database not ready after 60s')
    exit(1)
"

echo "🚀 Running Alembic migrations..."
alembic upgrade head

echo "✅ Migrations complete."
