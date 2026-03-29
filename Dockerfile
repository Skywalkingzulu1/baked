# ---------- Builder Stage ----------
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies (if any) and pip packages
# Using --no-cache-dir to keep image small
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . ./

# ---------- Runtime Stage ----------
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_RUN_HOST=0.0.0.0 \
    PORT=5000

# Set working directory
WORKDIR /app

# Copy only the installed packages and application code from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app

# Expose the port the Flask app runs on
EXPOSE 5000

# Use gunicorn as the production server
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]