# ------------------------------------------------------------
# Multi‑stage Dockerfile for building and serving the static site
# ------------------------------------------------------------

# ---------- Builder Stage ----------
# Using a lightweight Alpine image as the build environment.
# For a pure static site there is no compilation step,
# but this stage allows future extensions (e.g., npm build).
FROM alpine:3.20 AS builder

# Set working directory
WORKDIR /src

# Copy the entire project (HTML, assets, etc.) into the builder.
COPY . .

# If a build step is required (e.g., npm run build), it would be added here.
# For now we simply retain the source files as‑is.


# ---------- Production Stage ----------
# Use the official lightweight Nginx image to serve the site.
FROM nginx:alpine

# Copy the built static files from the builder stage into Nginx's
# default document root.
COPY --from=builder /src /usr/share/nginx/html

# Copy the custom Nginx configuration that adds caching headers
# and enables HTTPS support.
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP and HTTPS ports.
EXPOSE 80 443

# Run Nginx in the foreground.
CMD ["nginx", "-g", "daemon off;"]