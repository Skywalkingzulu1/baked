# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose the Flask default port
EXPOSE 5000

# Run the Flask application
CMD ["python", "app.py"]