FROM python:3.10-slim

# Update and install necessary dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    jq \
    curl

# Set up Chrome installation
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Download ChromeDriver using a script that finds the matching version
RUN echo '#!/bin/bash \n\
CHROME_VERSION=$(google-chrome --version | awk "{ print \$3 }" | cut -d. -f1,2,3) \n\
echo "Chrome version: $CHROME_VERSION" \n\
CHROME_MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1) \n\
echo "Looking for ChromeDriver version for Chrome $CHROME_MAJOR_VERSION" \n\
\n\
# First try to find the latest ChromeDriver for this major version \n\
LATEST_DRIVER_URL="https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_$CHROME_MAJOR_VERSION" \n\
CHROMEDRIVER_VERSION=$(curl -s $LATEST_DRIVER_URL) \n\
if [ -z "$CHROMEDRIVER_VERSION" ]; then \n\
  echo "Could not find latest ChromeDriver for Chrome $CHROME_MAJOR_VERSION" \n\
  # Try the last known version format for Chrome 135 \n\
  CHROMEDRIVER_VERSION="$CHROME_MAJOR_VERSION.0.7049.114" \n\
fi \n\
\n\
echo "Using ChromeDriver version: $CHROMEDRIVER_VERSION" \n\
\n\
# Try different download URLs \n\
DOWNLOAD_URLS=( \n\
  "https://storage.googleapis.com/chrome-for-testing-public/$CHROMEDRIVER_VERSION/linux64/chromedriver-linux64.zip" \n\
  "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$CHROMEDRIVER_VERSION/linux64/chromedriver-linux64.zip" \n\
  "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \n\
) \n\
\n\
SUCCESS=false \n\
for URL in "${DOWNLOAD_URLS[@]}"; do \n\
  echo "Trying to download ChromeDriver from: $URL" \n\
  if curl -s -f -L -o chromedriver.zip "$URL"; then \n\
    echo "Successfully downloaded ChromeDriver from $URL" \n\
    SUCCESS=true \n\
    break \n\
  fi \n\
done \n\
\n\
if [ "$SUCCESS" = false ]; then \n\
  echo "All download attempts failed, falling back to a known working version" \n\
  curl -s -f -L -o chromedriver.zip "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/114.0.5735.90/linux64/chromedriver-linux64.zip" \n\
fi \n\
\n\
# Extract and install ChromeDriver \n\
unzip -q chromedriver.zip \n\
if [ -d "chromedriver-linux64" ]; then \n\
  mv chromedriver-linux64/chromedriver /usr/local/bin/ \n\
else \n\
  mv chromedriver /usr/local/bin/ \n\
fi \n\
chmod +x /usr/local/bin/chromedriver \n\
rm -rf chromedriver*.zip chromedriver-linux64 \n\
\n\
echo "ChromeDriver installed at: /usr/local/bin/chromedriver" \n\
/usr/local/bin/chromedriver --version \n\
' > /tmp/install_chromedriver.sh \
    && chmod +x /tmp/install_chromedriver.sh \
    && /tmp/install_chromedriver.sh \
    && rm /tmp/install_chromedriver.sh

# Set environment variables for Selenium
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

WORKDIR /app

# Copy requirements first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"

# Copy application code
COPY . .

# Create debug directory
RUN mkdir -p debug && chmod 777 debug

# Expose port
EXPOSE 8000

# Run script to start virtual display and then run app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]