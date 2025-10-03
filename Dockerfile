# Use Ubuntu as base image
FROM ubuntu:22.04

# Install NGINX
RUN apt-get update && apt-get install -y nginx && apt-get clean

# Copy your HTML file into NGINX's default directory
COPY index.html /var/www/html/index.html

# Expose port 80 (HTTP)
EXPOSE 80

# Start NGINX in the foreground
CMD ["nginx", "-g", "daemon off;"]
