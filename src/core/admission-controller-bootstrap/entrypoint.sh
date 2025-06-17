#!/usr/bin/env sh
set -e
action=$1
shift

ADMISSION_SERVICE_WITH_NAMESPACE="${ADMISSION_SERVICE}.${ADMISSION_NAMESPACE}"
ADMISSION_SERVICE_FULL="${ADMISSION_SERVICE}.${ADMISSION_NAMESPACE}.svc"

generate_ssl() {
  if [ -z "${ADMISSION_SERVICE}" ] || [ -z "${ADMISSION_NAMESPACE}" ]; then
    echo 'You need to define ADMISSION_SECRET and ADMISSION_NAMESPACE environment variables'
    exit 1
  else
    echo "Generating cert"
    mkdir -p /tmp/cert
    cd /tmp/cert && \
    openssl req -new -x509 -sha256 -newkey rsa:2048 -keyout webhook.key -out webhook.crt -days 1024 -nodes -addext "subjectAltName=DNS.1:${ADMISSION_SERVICE}, DNS.2:${ADMISSION_SERVICE_WITH_NAMESPACE}, DNS.3:${ADMISSION_SERVICE_FULL}" -subj "/C=US/ST=St/L=l/O=Datacoves/CN=datacoves.com"
    cp /tmp/cert/webhook.key /home/user/webhook.key
    cp /tmp/cert/webhook.crt /home/user/webhook.crt
    rm -rf /tmp/cert
  fi
}

generate_secret() {
  if [ -z "${ADMISSION_SECRET}" ] || [ -z "${ADMISSION_NAMESPACE}" ]; then
    echo 'You need to define ADMISSION_SECRET and ADMISSION_NAMESPACE environment variables'
    exit 1
  else
    if ! kubectl get secret "${ADMISSION_SECRET}" --namespace="${ADMISSION_NAMESPACE}";
    then
        echo "Generating secret template"
        kubectl create secret generic "${ADMISSION_SECRET}" \
          --from-file=webhook.crt=/home/user/webhook.crt \
          --from-file=webhook.key=/home/user/webhook.key \
          --namespace="${ADMISSION_NAMESPACE}" --dry-run=client -o yaml > /home/user/secret.yaml
        echo "Deleting old secrets"
        kubectl delete secret "${ADMISSION_SECRET}" --ignore-not-found=true --namespace="${ADMISSION_NAMESPACE}" --grace-period=10
        echo "Creating new secret in cluster"
        kubectl create -f /home/user/secret.yaml
    else
        echo "Secret already exists"
    fi
  fi
}

bootstrap() {
  generate_ssl
  generate_secret
}

case ${action} in
bootstrap)
  bootstrap
  exit 0
  ;;
*)
  echo "Unknown action: \"${action}\"."
  help
  ;;
esac

exec "${action}" "$@"
