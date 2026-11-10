#!/bin/bash
set -euo pipefail
cd /usr/share/opensearch
./plugins/opensearch-security/tools/install_demo_configuration.sh -y -i -s
# Retain only the generated admin identity; remove demo users with public passwords.
awk '/^[a-zA-Z_][^ ]*:/ {keep=($0 ~ /^(_meta|admin):/)} keep' \
  config/opensearch-security/internal_users.yml > config/opensearch-security/internal_users.local
mv config/opensearch-security/internal_users.local config/opensearch-security/internal_users.yml
for name in root-ca.pem esnode.pem esnode-key.pem kirk.pem kirk-key.pem; do
  cp "/local-tls/$name" "config/$name"
done
sed -i 's/transport.ssl.enforce_hostname_verification: false/transport.ssl.enforce_hostname_verification: true/; s/plugins.security.allow_unsafe_democertificates: true/plugins.security.allow_unsafe_democertificates: false/' config/opensearch.yml
chmod 700 config
chmod 600 config/*.pem
export DISABLE_INSTALL_DEMO_CONFIG=true
exec ./opensearch-docker-entrypoint.sh
