# Use Python 3.10 on Debian 11 (Bullseye) to match the MS repo
FROM python:3.10-slim-bullseye

# 1) Install system dependencies needed to add Microsoft repo
RUN apt-get update && apt-get install -y curl gnupg2 apt-transport-https

# 2) Import Microsoft’s GPG key & add the msodbcsql17 repo for Debian 11
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# 3) Now install msodbcsql17 (ODBC Driver 17 for SQL Server) + unixodbc-dev
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev && \
    rm -rf /var/lib/apt/lists/*

# Set a working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code to /app
COPY . .

# Expose the port that gunicorn will listen on
EXPOSE 5000

# Run Gunicorn on container startup
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
