#!/usr/bin/env bash
# PlutoSDR quickstart setup for macOS.
# - Installs libiio via Homebrew
# - Creates a Python venv with pyadi-iio and runs a hello-world test
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v brew >/dev/null 2>&1; then
    echo "Homebrew not found. Install it first: https://brew.sh"
    exit 1
fi

echo "==> Installing libiio via Homebrew"
brew install libiio

echo "==> Creating Python virtual environment"
python3 -m venv "$REPO_ROOT/.venv"
source "$REPO_ROOT/.venv/bin/activate"
pip install --upgrade pip
pip install pyadi-iio numpy matplotlib

cat <<'EOF'

==> Plug in your PlutoSDR now if you haven't already.
    macOS should show a new network interface for it automatically.
    If it doesn't appear within ~20s, go to:
    System Settings -> Network -> and check for a "RNDIS/Ethernet Gadget"
    or similar new interface, and make sure it's set to "Using DHCP".
EOF
read -rp "Press Enter once the network interface is up... "

echo "==> Running hello_pluto.py"
python3 "$REPO_ROOT/examples/hello_pluto.py" || {
    echo "Could not reach Pluto at ip:192.168.2.1 yet. Re-run after checking the network interface:"
    echo "  source .venv/bin/activate && python3 examples/hello_pluto.py"
}

echo ""
echo "==> Done. In VS Code: open this folder, run 'Python: Select Interpreter',"
echo "    choose: $REPO_ROOT/.venv/bin/python"
