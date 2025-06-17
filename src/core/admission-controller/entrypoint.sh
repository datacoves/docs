#!/usr/bin/env sh
set -e
action=$1
shift

help () {
  echo "
  Container Available Commands
    help                     : show this help
    server                   : run uviconrn server
  "
}

case ${action} in
help)
  help
  exit 0
  ;;
server)
  exec "uvicorn" "api:app" "--host" "${HOST:-0.0.0.0}" "--port" "${PORT:-8000}" "--ssl-keyfile=${SSL_KEYFILE}" "--ssl-certfile=${SSL_CERTFILE}"
  ;;
*)
  echo "Unknown action: \"${action}\"."
  help
  ;;
esac

exec "${action}" "$@"
