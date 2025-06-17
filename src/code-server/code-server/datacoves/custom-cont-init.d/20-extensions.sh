#!/bin/bash

set -e

echo "[datacoves setup] Installing extensions..."

rm -rf /config/extensions-prep
rm -rf /config/extensions

echo "Debug: Creating /config/extensions-prep"
mkdir -p /config/extensions-prep
mkdir -p /config/extensions

cd /opt/datacoves/profile/extensions

for filename in *.vsix; do
    echo "   - processing $filename..."

    rm -rf /tmp/extension
    unzip "$filename" extension/* -d /tmp

    rm -rf /config/extensions-prep/"${filename/.vsix/}"

    echo "Debug: Moving /tmp/extension to /config/extensions-prep/${filename/.vsix/}"
    mv /tmp/extension /config/extensions-prep/"${filename/.vsix/}"
done

chown -R abc:abc /config/extensions-prep
chown -R abc:abc /config/extensions
