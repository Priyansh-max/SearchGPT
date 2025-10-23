#!/bin/bash
set -e

echo "Starting entrypoint script..."

# Verify Playwright is installed and working
echo "Checking Playwright installation:"
if python -c "import playwright; print('✅ Playwright installed successfully')" 2>/dev/null; then
    echo "✅ Playwright Python package is available"
else
    echo "❌ Playwright Python package not found"
    exit 1
fi

# Check if Playwright browsers are installed
echo "Checking Playwright browsers:"
if python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); browser.close(); p.stop(); print('✅ Playwright Chromium browser working')" 2>/dev/null; then
    echo "✅ Playwright Chromium browser is available and working"
else
    echo "❌ Playwright Chromium browser not working properly"
    echo "Attempting to install Playwright browsers..."
    playwright install chromium
    playwright install-deps chromium
fi

# Make sure debug directory exists
mkdir -p /app/debug
chmod 777 /app/debug

# Print environment variables
echo "Environment:"
echo "PYTHONUNBUFFERED=$PYTHONUNBUFFERED"
echo "PLAYWRIGHT_BROWSERS_PATH=$PLAYWRIGHT_BROWSERS_PATH"
echo "SERPAPI_KEY=${SERPAPI_KEY:0:10}..." # Only show first 10 chars for security

# Test SerpAPI configuration
echo "Testing SerpAPI configuration..."
if [ -z "$SERPAPI_KEY" ]; then
    echo "⚠️ SERPAPI_KEY not set - search functionality will not work"
else
    echo "✅ SERPAPI_KEY is configured"
fi

echo "Starting application..."
exec gunicorn app:app --bind 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker --timeout 300 --workers 1 