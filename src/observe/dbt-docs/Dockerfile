FROM nginx:1.12-alpine
LABEL com.datacoves.from=nginx:1.12-alpine
LABEL com.datacoves.version.observe.nginx=1.12-alpine

COPY default.conf /

COPY docs_missing.html /usr/share/nginx/html/

EXPOSE 80

CMD ["/bin/sh", "-c", "envsubst '$DBT_DOCS_GIT_PATH' < /default.conf > /etc/nginx/conf.d/default.conf ; nginx -g 'daemon off;'"]
