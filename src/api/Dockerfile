# Use a base image with Python 3.11
FROM python:3.11-slim

# Install build dependencies that are commonly needed for Python packages with C extensions.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Update pip to the latest version
RUN pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy your requirements file into the container
COPY requirements.txt .

# Install the Python dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Set environment variables for Python
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 8080

# The command to run your application using uvicorn
# Assumes your FastAPI app instance is named 'app' in 'app/main.py'
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

