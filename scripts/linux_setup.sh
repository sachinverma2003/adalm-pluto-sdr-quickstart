#!/usr/bin/env bash
# PlutoSDR quickstart setup for Linux.
# - Installs libiio + build deps
# - Adds a udev rule so non-root users can access the device
# - Creates a Python venv with pyadi-iio and runs a hello-world test
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Detecting package manager"
if command -v apt-get >/dev/null 2>&1; then
    PM="apt"
elif command -v dnf >/dev/null 2>&1; then
    PM="dnf"
elif command -v pacman >/dev/null 2>&1; then
    PM="pacman"
else
    echo "Unsupported distro. Please install libiio and python3-venv manually." >&2
    exit 1
fi

echo "==> Installing libiio and Python venv support ($PM)"
case "$PM" in
    apt)
        sudo apt-get update
        sudo apt-get install -y libiio-utils libiio-dev python3-venv python3-pip udev
        ;;
    dnf)
        sudo dnf install -y libiio libiio-devel python3-venv python3-pip
        ;;
    pacman)
        sudo pacman -Sy --noconfirm libiio python-pip
        ;;
esac

echo "==> Installing udev rule for PlutoSDR (no-sudo USB access)"
UDEV_RULE='SUBSYSTEM=="usb", ATTR{idVendor}=="0456", ATTR{idProduct}=="b673", MODE="0666", GROUP="plugdev"'
echo "$UDEV_RULE" | sudo tee /etc/udev/rules.d/53-adi-plutosdr-usb.rules >/dev/null
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "==> Creating Python virtual environment"
python3 -m venv "$REPO_ROOT/.venv"
source "$REPO_ROOT/.venv/bin/activate"
pip install --upgrade pip
pip install pyadi-iio numpy matplotlib

echo "==> Plug in your PlutoSDR now if you haven't already."
read -rp "Press Enter once it's plugged in and its LED is steady... "

echo "==> Running hello_pluto.py"
python3 "$REPO_ROOT/examples/hello_pluto.py" || {
    echo "Could not reach Pluto at ip:192.168.2.1 yet. Wait a few seconds and re-run:"
    echo "  source .venv/bin/activate && python3 examples/hello_pluto.py"
}

echo ""
echo "==> Done. In VS Code: open this folder, run 'Python: Select Interpreter',"
echo "    choose: $REPO_ROOT/.venv/bin/python"
