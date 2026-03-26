# -------------------------------------------------
# Multi-stage Dockerfile for serving a static site
# -------------------------------------------------

# ---------- Builder Stage ----------
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install Python dependencies (if any are needed at runtime)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy static site files
COPY index.html .

# ---------- Runtime Stage ----------
FROM nginx:stable-alpine

# Remove default Nginx static files
RUN rm -rf /usr/share/nginx/html/*

# Copy the built static files from the builder stage
COPY --from=builder /app/index.html /usr/share/nginx/html/

# Add custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]