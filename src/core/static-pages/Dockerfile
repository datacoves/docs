FROM nginx:1.12-alpine
LABEL com.datacoves.from=nginx:1.12-alpine
LABEL com.datacoves.version.observe.nginx=1.12-alpine

COPY default.conf /etc/nginx/conf.d/default.conf

WORKDIR /usr/share/nginx/html/
COPY src .
COPY templates /tmp/templates

EXPOSE 80

CMD ["/bin/sh", "-c", "envsubst < /tmp/templates/index.template.html > /usr/share/nginx/html/index.html; nginx -g 'daemon off;'"]
