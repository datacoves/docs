# Debugging images outside Datacoves.

Sometimes we need to review images that are running in Datacoves in a simpler way to debug processes, review the versions of libraries, versions of pipelines, etc.

1. Create `compose.yaml` or `docker-compose.yaml` file

```sh
version: '3'

services:
  snowflake:
    image: "taqy-docker.artifactrepo.jnj.com/datacoves/ci-basic-dbt-snowflake:3.1"
    command: bash -c "sleep infinity"
```

2. Run commands

```sh
docker compose run --rm snowflake bash -c "pip show dbt-core dbt-snowflake"
```

3. Get a terminal

```sh
docker compose up -d
docker ps
docker exec -ti <container-id> /bin/bash
```
