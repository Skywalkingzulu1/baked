# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system build dependencies (gcc for any compiled packages)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Flask and Gunicorn are installed (they may not be in requirements.txt)
RUN pip install --no-cache-dir Flask gunicorn

# Copy the rest of the application code
COPY . .

# Expose the Flask default port
EXPOSE 5000

# Use Gunicorn to serve the Flask app in production
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
