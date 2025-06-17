#!/bin/bash

pass=${1}
repo=${2}

if [[ $repo != *"/"* ]]; then
    repo="library/$repo"
fi

basic=$(printf "datacovesprivate:$pass" | base64)

tokenUri="https://auth.docker.io/token"
data=("service=registry.docker.io" "scope=repository:${repo}:pull")
if [[ $repo != *"datacovesprivate/"* ]]; then
     token="$(curl --silent --get --data-urlencode ${data[0]} --data-urlencode ${data[1]} $tokenUri | jq --raw-output '.token')"
else
     token="$(curl -H "Authorization: Basic $basic" --silent --get --data-urlencode ${data[0]} --data-urlencode ${data[1]} $tokenUri | jq --raw-output '.token')"
fi
listUri="https://registry-1.docker.io/v2/${repo}/tags/list"
authz="Authorization: Bearer $token"
result="$(curl --silent --get -H "Accept: application/json" -H "Authorization: Bearer $token" $listUri | jq --raw-output '.')"

echo $result