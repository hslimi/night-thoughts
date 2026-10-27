#!/bin/bash
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo after reviewing queued/running application work." >&2
  exit 1
fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_USER="${SUDO_USER:-$(id -un)}"
HOME_DIR="$(dscl . -read "/Users/${SERVICE_USER}" NFSHomeDirectory | awk '{print $2}')"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/var/deploy-backups/$STAMP"
mkdir -p "$BACKUP"
chmod 700 "$BACKUP"
for label in com.nightthoughts.imaging.api com.nightthoughts.imaging.worker; do
  plist="/Library/LaunchDaemons/${label}.plist"
  if [ -f "$plist" ]; then
    cp -p "$plist" "$BACKUP/${label}.plist"
  fi
  plutil -lint "$ROOT/deploy/${label}.plist"
done
for label in com.nightthoughts.imaging.api com.nightthoughts.imaging.worker; do
  configured="$BACKUP/${label}.configured.plist"
  sed -e "s|__PROJECT_ROOT__|${ROOT}|g" -e "s|__SERVICE_USER__|${SERVICE_USER}|g" -e "s|__HOME__|${HOME_DIR}|g" "$ROOT/deploy/${label}.plist" > "$configured"
  plutil -lint "$configured"
  launchctl bootout "system/${label}" 2>/dev/null || true
  install -m 644 "$configured" "/Library/LaunchDaemons/${label}.plist"
  launchctl bootstrap system "/Library/LaunchDaemons/${label}.plist"
done
printf 'Application service configuration backup: %s\n' "$BACKUP"
