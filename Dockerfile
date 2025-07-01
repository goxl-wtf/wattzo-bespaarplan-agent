# Use official Python image as base
FROM python:3.10-slim

# Install system dependencies needed for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all project files
COPY . .

# Install uv package manager
RUN pip install uv

# Install Python dependencies using uv with pyproject.toml
RUN uv pip install --system -e .

# Create necessary directories
RUN mkdir -p logs

# Expose the port (Render will provide PORT env var)
EXPOSE 8000

# Command to start the application
CMD ["python", "run_api.py"]