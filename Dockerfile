# Use a slim Python base image
FROM python:3.10-slim

# Install system dependencies needed by pyodbc
RUN apt-get update && apt-get install -y unixodbc-dev && rm -rf /var/lib/apt/lists/*

# Create a working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into /app
COPY . .

# Expose the port that gunicorn will listen on
EXPOSE 5000

# The command to start gunicorn on the container
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
