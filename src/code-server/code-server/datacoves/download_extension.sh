#!/usr/bin/env bash

set -e


dl() {
    curl --fail -JLO --compressed "$1"
}

url="$1"

dl "$url" && exit 0

echo 'Download failed, retrying in 2 seconds...'
sleep 2
dl "$url" && exit 0

echo 'Download failed, retrying in 5 seconds...'
sleep 5
dl "$url" && exit 0

echo 'Download failed, retrying in 10 seconds...'
sleep 10
dl "$url" && exit 0

echo 'Download failed.'
exit 1
