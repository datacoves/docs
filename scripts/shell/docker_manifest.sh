#!/bin/bash

pass=${1}
repo=${2}
tag=${3}

if [[ $repo != *"/"* ]]; then
    repo="library/$repo"
fi

basic=$(printf "datacovesprivate:$pass" | base64)
if [[ $repo != *"datacovesprivate/"* ]]; then
     token=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${repo}:pull" \
          | jq -r '.token')
else
     token=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${repo}:pull" \
          -H "Authorization: Basic $basic" | jq -r '.token')
    
fi

digest=$(curl -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
     -H "Authorization: Bearer $token" -s "https://registry-1.docker.io/v2/${repo}/manifests/${tag}" | jq -r .config.digest)
curl -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
     -H "Authorization: Bearer $token" \
     -s -L "https://registry-1.docker.io/v2/${repo}/blobs/${digest}" | jq .config