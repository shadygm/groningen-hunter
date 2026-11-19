#!/bin/bash
# Install groningen-hunter to /opt/groningen-hunter and set it up as a
# systemd service (alternative to the Docker container).
#
# Usage:
#   sudo ./setup-systemd.sh              Install/upgrade and enable the service
#   sudo ./setup-systemd.sh --uninstall  Stop and remove the service (/opt/groningen-hunter is kept)
set -euo pipefail

SERVICE_NAME="groningen-hunter"
UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
INSTALL_DIR="/opt/${SERVICE_NAME}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="${REPO_DIR}/${SERVICE_NAME}.service.in"

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root: sudo ./setup-systemd.sh" >&2
    exit 1
fi

if [ "${1:-}" = "--uninstall" ]; then
    echo "==> Removing ${SERVICE_NAME} service"
    systemctl disable --now "$SERVICE_NAME" 2>/dev/null || true
    rm -f "$UNIT_PATH"
    systemctl daemon-reload
    echo "Service removed. $INSTALL_DIR (including your configuration and history) was kept."
    exit 0
fi

# Run the service as the user who invoked sudo (falls back to root)
RUN_USER="${SUDO_USER:-root}"
if [ "$RUN_USER" = "root" ]; then
    echo "Warning: could not detect the invoking user, the service will run as root." >&2
fi

echo "==> Installing system packages"
apt-get update
apt-get install -y python3 python3-venv

# Package names differ between Debian and Ubuntu
if ! apt-get install -y chromium chromium-driver; then
    apt-get install -y chromium-browser chromium-chromedriver
fi

# The bot expects Chromium at /usr/bin/chromium and the driver at
# /usr/bin/chromedriver (see src/hunters/hunter.py). Link them if the
# distribution installed them elsewhere.
link_if_missing() {
    local expected="$1"; shift
    [ -e "$expected" ] && return 0
    local candidate
    for candidate in "$@"; do
        if [ -x "$candidate" ]; then
            ln -sf "$candidate" "$expected"
            echo "Linked $expected -> $candidate"
            return 0
        fi
    done
    echo "Error: no binary found for $expected (tried: $*)" >&2
    return 1
}
link_if_missing /usr/bin/chromium /usr/bin/chromium-browser /snap/bin/chromium
link_if_missing /usr/bin/chromedriver /usr/lib/chromium-browser/chromedriver /snap/bin/chromium.chromedriver

echo "==> Installing to $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
# Copy the code, preserving src/.env and history.txt from a previous install
cp -r "$REPO_DIR/src/." "$INSTALL_DIR/src.new"
if [ -s "$INSTALL_DIR/src/.env" ]; then
    cp "$INSTALL_DIR/src/.env" "$INSTALL_DIR/src.new/.env"
fi
rm -rf "$INSTALL_DIR/src"
mv "$INSTALL_DIR/src.new" "$INSTALL_DIR/src"
cp "$REPO_DIR/requirements.txt" "$INSTALL_DIR/"
touch "$INSTALL_DIR/src/.env" "$INSTALL_DIR/history.txt"

echo "==> Creating Python virtual environment"
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

chown -R "$RUN_USER:$RUN_USER" "$INSTALL_DIR"

echo "==> Installing systemd service"
sed "s|__USER__|$RUN_USER|g" "$TEMPLATE" > "$UNIT_PATH"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

if grep -q '^BOT_TOKEN=' "$INSTALL_DIR/src/.env"; then
    echo "==> Starting service"
    systemctl restart "$SERVICE_NAME"
    echo
    echo "Done! The bot is running."
else
    echo
    echo "Done! Before starting the bot, set your Telegram bot token:"
    echo "    ./hunter.sh --set-bot-token \"YOUR-TELEGRAM-BOT-TOKEN\""
    echo "    sudo ./setup-systemd.sh   # re-run to copy the token and start"
fi
