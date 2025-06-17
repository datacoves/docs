# Use the official Elixir image as a base
# Find eligible builder and runner images on Docker Hub. We use Ubuntu/Debian
# instead of Alpine to avoid DNS resolution issues in production.
#
# https://hub.docker.com/r/hexpm/elixir/tags?page=1&name=ubuntu
# https://hub.docker.com/_/ubuntu?tab=tags
#
# This file is based on these images:
#
#   - https://hub.docker.com/r/hexpm/-elixir/tags - for the build image
#   - https://hub.docker.com/_/debian?tab=tags&page=1&name=bullseye-20240130-slim - for the release image
#   - https://pkgs.org/ - resource for finding needed packages
#   - Ex: hexpm/elixir:1.15.0-erlang-26.0.1-debian-bullseye-20240130-slim
#
ARG ELIXIR_VERSION=1.18.2
ARG OTP_VERSION=27.2.2
ARG DEBIAN_VERSION=bullseye-20250203-slim

ARG BUILDER_IMAGE="hexpm/elixir:${ELIXIR_VERSION}-erlang-${OTP_VERSION}-debian-${DEBIAN_VERSION}"

FROM ${BUILDER_IMAGE} AS builder

# Without this, you can't build the image on macOS
# See: https://elixirforum.com/t/arm64-dockerfile-failing/57317/12
ENV ERL_FLAGS="+JPperf true"

# install build dependencies
RUN apt-get update -y && apt-get install -y build-essential git \
    && apt-get clean && rm -f /var/lib/apt/lists/*_*

# install hex + rebar
RUN mix local.hex --force && \
    mix local.rebar --force

# Create and set the working directory
WORKDIR "/app"

# Set the build environment for fetching the dependencies
ENV MIX_ENV="prod"

# Copy over your mix.exs and mix.lock files to install dependencies
COPY mix.exs mix.lock ./
RUN mix deps.get --only $MIX_ENV
RUN mkdir config

# copy compile-time config files before we compile dependencies
# to ensure any relevant config change will trigger the dependencies
# to be re-compiled.
COPY config/config.exs config/${MIX_ENV}.exs config/
RUN mix deps.compile

COPY priv priv

COPY lib lib

COPY assets assets

# compile assets
RUN mix assets.deploy

# Compile the release
RUN mix compile

# Changes to config/runtime.exs don't require recompiling the code
COPY config/runtime.exs config/

# Copy over the rest of your app's code
COPY . .

# Make the run script executable
RUN chmod +x run.sh

# Run the Phoenix server
ENTRYPOINT ["./run.sh"]
