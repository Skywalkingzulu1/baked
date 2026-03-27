FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the static HTML file
COPY index.html ./

# Expose the default port for a simple HTTP server
EXPOSE 8000

# Use Python's built-in HTTP server to serve the static site
CMD ["python", "-m", "http.server", "8000"]
