#!/usr/bin/env sh

# Usage: ./deploy.sh <script-name>
# Exemple: ./deploy.sh anothertime
# Déploie <script-name>.ax vers l'appareil AWTRIX (nom d'app = PascalCase du script)

set -eu

if [ $# -eq 0 ]; then
  echo "Usage: $0 <script-name>"
  echo ""
  echo "Scripts disponibles :"
  for f in *.ax; do
    [ -f "$f" ] && echo "  ${f%.ax}"
  done
  exit 1
fi

SCRIPT="$1"
SCRIPT_FILE="${SCRIPT}.ax"

if [ ! -f "$SCRIPT_FILE" ]; then
  echo "❌ Script introuvable: $SCRIPT_FILE"
  echo ""
  echo "Scripts disponibles :"
  for f in *.ax; do
    [ -f "$f" ] && echo "  ${f%.ax}"
  done
  exit 1
fi

# Charger .env s'il existe
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

: "${AWTRIX_IP:?AWTRIX_IP non défini (ajoutez-le dans .env ou exportez-le)}"

# Nom de l'app = PascalCase du script (anothertime -> Anothertime)
APP_NAME=$(echo "$SCRIPT" | sed 's/\b\(.\)/\u\1/g')

MIN_FILE="${SCRIPT}.min.ax"

echo "🔨 Minification de $SCRIPT_FILE..."
./minify-berry/minify-berry.ts --classes --variables "$SCRIPT_FILE" > "$MIN_FILE"

echo "🚀 Déploiement vers $AWTRIX_IP (app: $APP_NAME)..."
CURL_ARGS="-H Content-Type:text/plain -X PUT --data-binary @$MIN_FILE"

if [ -n "${AWTRIX_AUTH:-}" ]; then
  CURL_ARGS="-u $AWTRIX_AUTH $CURL_ARGS"
fi

# shellcheck disable=SC2086
curl -sS $CURL_ARGS "http://$AWTRIX_IP/api/v1/apps/script/$APP_NAME" | jq .

echo "✅ Déployé. Vérifiez avec : curl -s \"http://$AWTRIX_IP/api/v1/apps/active\" -X PUT -H 'Content-Type: application/json' -d '{\"name\":\"$APP_NAME\",\"fast\":true}'"