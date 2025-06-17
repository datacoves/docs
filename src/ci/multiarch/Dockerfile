FROM docker:20

ARG BUILDX_URL=https://github.com/docker/buildx/releases/download/v0.10.4/buildx-v0.10.4.linux-amd64

# Enable experimental features in Docker client
RUN mkdir -p $HOME/.docker \
    && echo -e '{\n  "experimental": "enabled"\n}' | tee $HOME/.docker/config.json \
    && mkdir -p $HOME/.docker/cli-plugins/ \
    && wget -O $HOME/.docker/cli-plugins/docker-buildx $BUILDX_URL \
    && chmod a+x $HOME/.docker/cli-plugins/docker-buildx \
    && apk add --update py-pip python3 gcc curl git bash make go jq \
    && pip install uv

COPY requirements.txt .
RUN pip install -r requirements.txt
