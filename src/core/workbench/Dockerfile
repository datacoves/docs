FROM node:18.12.1-alpine AS local
LABEL com.datacoves.from=nginx:1.12-alpine
LABEL com.datacoves.version.core-workbench='0.4.0'
LABEL com.datacoves.version.core-workbench.node='16.8.0-alpine'
LABEL com.datacoves.version.core-workbench.nginx='1.12-alpine'

RUN apk add --no-cache vim

WORKDIR /usr/src
COPY app/package.json .
COPY app/yarn.lock .

RUN yarn install    # backup of node_modules for later reuse

ENV PATH=/usr/src/app/node_modules/.bin:$PATH

WORKDIR /usr/src/app

CMD sh -c "cp -rf ../node_modules . && tail -f /dev/null"

# build deps
FROM local AS build-deps

COPY app /usr/src/app

WORKDIR /usr/src/app

RUN mv ../node_modules . && yarn build

# Nginx
FROM nginx:1.12-alpine AS production

COPY --from=build-deps /usr/src/app/build /usr/share/nginx/workbench

COPY default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

