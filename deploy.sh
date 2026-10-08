#!/usr/bin/env sh

set -eu

usage() {
  printf 'Usage: %s <app> [--force]\n' "$0" >&2
  printf 'Apps:' >&2
  for manifest in apps/*/awtrix.toml; do
    [ -f "$manifest" ] || continue
    project_dir=${manifest%/awtrix.toml}
    printf ' %s' "${project_dir##*/}" >&2
  done
  printf '\n\nBy default, deployment is create-only. Pass --force to replace an installed app.\n' >&2
}

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  usage
  exit 2
fi

APP=$1
shift

case "$APP" in
  ''|*[!a-z0-9_-]*)
    printf 'Invalid app name: %s\n' "$APP" >&2
    usage
    exit 2
    ;;
esac

FORCE=no
if [ "$#" -eq 1 ]; then
  if [ "$1" != '--force' ]; then
    printf 'Unknown option: %s\n' "$1" >&2
    usage
    exit 2
  fi
  FORCE=yes
fi

PROJECT="apps/$APP"
MANIFEST="$PROJECT/awtrix.toml"
SOURCE="$PROJECT/src/$APP.ax"

if [ ! -f "$MANIFEST" ] || [ ! -f "$SOURCE" ]; then
  printf 'AWTRIX project not found for app: %s\n' "$APP" >&2
  usage
  exit 2
fi

APP_NAME=$(awk '$1 == "#" && $2 == "@name" { print $3; exit }' "$SOURCE")
if [ -z "$APP_NAME" ]; then
  printf 'Missing # @name in %s\n' "$SOURCE" >&2
  exit 2
fi

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

: "${AWTRIX_IP:?AWTRIX_IP non défini (ajoutez-le dans .env ou exportez-le)}"

if [ -n "${AWTRIX_AUTH:-}" ] &&
   { [ -z "${AWTRIX_USERNAME:-}" ] || [ -z "${AWTRIX_PASSWORD:-}" ]; }; then
  case "$AWTRIX_AUTH" in
    *:*)
      AWTRIX_USERNAME=${AWTRIX_AUTH%%:*}
      AWTRIX_PASSWORD=${AWTRIX_AUTH#*:}
      ;;
    *)
      printf 'AWTRIX_AUTH must use the user:password format.\n' >&2
      exit 2
      ;;
  esac
fi
export AWTRIX_USERNAME AWTRIX_PASSWORD

case "$AWTRIX_IP" in
  http://*|https://*) AWTRIX_TARGET=$AWTRIX_IP ;;
  *) AWTRIX_TARGET="http://$AWTRIX_IP" ;;
esac

if ! command -v awtrix-cli >/dev/null 2>&1; then
  printf 'awtrix-cli is required; install it before deploying.\n' >&2
  exit 127
fi

printf 'Deploying %s from %s to %s with awtrix-cli.\n' "$APP_NAME" "$SOURCE" "$AWTRIX_TARGET"

if [ "$FORCE" = yes ]; then
  printf 'Unconditional replacement enabled; concurrent remote edits will not be protected.\n' >&2
  exec awtrix-cli --target "$AWTRIX_TARGET" --json script deploy "$APP_NAME" \
    --file "$SOURCE" --minify --force --verify-secs 10
fi

exec awtrix-cli --target "$AWTRIX_TARGET" --json script deploy "$APP_NAME" \
  --file "$SOURCE" --minify --create --verify-secs 10
