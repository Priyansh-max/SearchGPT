#!/bin/bash
set -e

echo "Starting entrypoint script..."

# Verify Chrome is installed and working
echo "Checking Chrome installation:"
if [ -f "$CHROME_BIN" ]; then
    echo "✅ Chrome binary found at: $CHROME_BIN"
    CHROME_VERSION=$("$CHROME_BIN" --version)
    echo "🌐 $CHROME_VERSION"
else
    echo "❌ Chrome binary not found at: $CHROME_BIN"
    echo "Searching for Chrome in common locations..."
    which google-chrome
    which google-chrome-stable
fi

# Verify ChromeDriver is installed and working
echo "Checking ChromeDriver installation:"
if [ -f "$CHROMEDRIVER_PATH" ]; then
    echo "✅ ChromeDriver binary found at: $CHROMEDRIVER_PATH"
    CHROMEDRIVER_VERSION=$("$CHROMEDRIVER_PATH" --version)
    echo "🔧 $CHROMEDRIVER_VERSION"
else
    echo "❌ ChromeDriver binary not found at: $CHROMEDRIVER_PATH"
    echo "Searching for ChromeDriver in PATH..."
    which chromedriver
fi

# Make sure debug directory exists
mkdir -p /app/debug
chmod 777 /app/debug

# Start the X Virtual Frame Buffer
echo "Starting Xvfb on display :99..."
Xvfb :99 -screen 0 1280x1024x24 -ac &
XVFB_PID=$!

# Wait for Xvfb to be ready
sleep 2
echo "Xvfb started with PID: $XVFB_PID"

# Test that Xvfb is working
if xdpyinfo -display :99 >/dev/null 2>&1; then
    echo "✅ Xvfb is running correctly"
else
    echo "⚠️ Xvfb might not be running correctly, but we'll continue anyway"
fi

# Print environment variables
echo "Environment:"
echo "DISPLAY=$DISPLAY"
echo "PYTHONUNBUFFERED=$PYTHONUNBUFFERED"
echo "SELENIUM_HEADLESS=${SELENIUM_HEADLESS:-true}"
echo "SELENIUM_TIMEOUT=${SELENIUM_TIMEOUT:-30}"

echo "Starting application..."
exec gunicorn app:app --bind 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker --timeout 300 --workers 1 