#!/usr/bin/env bash
# Build script for Render deployment

set -e

# Install system dependencies for Chrome/Selenium
apt-get update
apt-get install -y wget gnupg2 unzip

# Install Chromium
apt-get install -y chromium-browser chromium-driver

# Log installed versions
chromium-browser --version
chromedriver --version

# Install Python requirements
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"

# Create debug directory
mkdir -p debug
chmod 777 debug 