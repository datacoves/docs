FROM nginx:latest

# This lives exclusively on our VM and if you have access to this file in this
# repo, then you already have access to the documentation, so I don't see a
# point to hiding the password.
#
# We will bake a self-signed cert into here and rely on CloudFlare to
# translate it into a 'real' cert.
RUN apt-get update && apt-get install -y apache2-utils && \
    htpasswd -c -b /etc/nginx/htpasswd hey d@t@c0v3D3V3L0P3R && \
    openssl req -x509 -nodes -newkey rsa:4096 \
            -keyout "/etc/nginx/privkey.pem" \
            -out "/etc/nginx/fullchain.pem" \
            -days 3650 \
            -subj "/C=US/ST=NA/L=Datacoves/O=Datacoves/OU=Org/CN=devdocs.datacoves.com"


# Also build our 

COPY docs_output /usr/share/nginx/html
COPY default.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
