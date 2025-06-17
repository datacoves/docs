FROM alpine:3.17

LABEL com.datacoves.from=alpine:3.17
LABEL com.datacoves.library.admission-controller-bootstrap.kubectl=1.25.1

ARG APP_USER=container_user
ARG KUBECTL_VERSION=v1.25.1

RUN adduser -h /home/user -s /bin/sh -D -u 1000 ${APP_USER} ${APP_USER} \
    && apk --no-cache update \
    && apk --no-cache add openssl curl

# Installing kubectl
RUN curl -L "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    -o /usr/local/bin/kubectl && \
    chmod +x /usr/local/bin/kubectl

COPY --chown=${APP_USER}:${APP_USER} ./entrypoint.sh /
USER $APP_USER
WORKDIR /home/user
VOLUME ["/home/user"]
ENTRYPOINT ["/entrypoint.sh"]

CMD ["bootstrap"]
