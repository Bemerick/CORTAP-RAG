#!/bin/bash
# Render Deployment Script for CORTAP RAG
# This script handles database migrations and deployment verification

set -e  # Exit on error

echo "🚀 Starting CORTAP RAG Deployment..."

# Check required environment variables
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY not set"
    exit 1
fi

echo "✅ Environment variables verified"

# Run database migrations
echo "📊 Running database migrations..."
cd /opt/render/project/src/backend || cd backend
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully"
else
    echo "❌ Database migrations failed"
    exit 1
fi

# Verify database connection
echo "🔍 Verifying database connection..."
python -c "
from database.connection import get_db
try:
    db = next(get_db())
    print('✅ Database connection verified')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

echo "✅ Deployment complete!"
echo "🎉 CORTAP RAG is ready to serve requests"
