#!/bin/bash
set -e

echo "⏳ Waiting for database..."
python -c "
import time, os
url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://')
import psycopg2
for i in range(30):
    try:
        psycopg2.connect(url)
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

echo "🌱 Running seed..."
python -m scripts.seed || echo "⚠️  Seed failed (non-blocking)"
echo "✅ Seed complete."
