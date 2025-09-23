FROM python:3.11-slim

# Install system deps and uv (fast Python package manager)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://astral.sh/uv/install.sh | sh

# Make uv available on PATH
ENV PATH="/root/.local/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy the requirements first for better layer caching
COPY requirements.txt ./requirements.txt

# Install Python dependencies using uv (cached, reproducible)
RUN uv pip install --system --no-cache -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Set environment variables for Python
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 8080

# Default command (can be overridden by docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
