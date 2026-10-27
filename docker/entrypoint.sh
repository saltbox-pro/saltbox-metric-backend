#! /bin/bash

set -e

warn() {
  1>&2 echo "$@"
}

err() {
  warn "$@" && exit 1
}

REDIS_PASSWORD="$(cat /run/secrets/redis_salt_password)"
KEYCLOAK_CLIENT_SECRET="$(cat "$KEYCLOAK_CLIENT_SECRET_FILE")"

export REDIS_PASSWORD KEYCLOAK_CLIENT_SECRET

if [ "$DEV_MODE" = 1 ]; then
  uv --no-progress pip install --system --editable .[reload]
  uv --no-progress pip install --system --editable "${SALTBOX_SDK_SRC_PATH}"
fi

cmd_uvicorn() {
  cmd=(uvicorn saltbox_metric.main:app --host=0.0.0.0 --port=8000)
  cmd+=(--timeout-graceful-shutdown="${TIMEOUT_GRACEFUL_SHUTDOWN}")
  if [ "$DEV_MODE" = 1 ]; then
    cmd+=(--reload)
  fi
}

cmd_shell() {
  cmd=("${@:2}")
}

wrong_cmd() {
  warn "Unknown command \"${*}\""
  err "Try \"shell ${*}\" for arbitrary command"
}

case $1 in
  uvicorn) cmd_uvicorn ;;
  shell) cmd_shell "$@" ;;
  *) wrong_cmd "$@" ;;
esac

echo "$ ${cmd[*]}"
exec "${cmd[@]}"
