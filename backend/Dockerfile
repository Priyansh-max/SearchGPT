FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    chromium \
    chromium-driver

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver


WORKDIR /app

# Copy requirements first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN python -m playwright install --with-deps chromium

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"

# Copy application code
COPY . .

# Create debug directory
RUN mkdir -p debug && chmod 777 debug

# Expose port
EXPOSE 8000

# Run the application with Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker", "--timeout", "300", "--workers", "1"]