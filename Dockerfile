FROM nginx:alpine

# Copy all static site files (HTML, data files, images, etc.) into Nginx's default serving directory
COPY . /usr/share/nginx/html

# Expose the default HTTP port
EXPOSE 80

# The default command for the nginx:alpine image already starts Nginx in the foreground, so no additional CMD is required.
