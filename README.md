# PlutoSDR Quickstart (Windows-first)

Plug in your ADALM-PLUTO, double-click **`setup.bat`**, and start
writing/running Python (`pyadi-iio`) against it in VS Code. No manual driver
hunting, no reading through confusing wiki pages.

> Based on the official Analog Devices quick start: https://wiki.analog.com/university/tools/pluto/users/quick_start

---

## ⚡ 1-Click Windows Quick Start

1. Clone or download this repo onto your Windows PC.
2. **Double-click `setup.bat`** (or right-click → *Run as administrator*).
3. That's it! The script will automatically:
   - Request Administrator approval (UAC) to install USB drivers.
   - Silently download and install the official signed ADI USB/RNDIS drivers.
   - Install Python 3.12 via winget if not already present.
   - Create the Python virtual environment (`.venv`) and install all required libraries (`pyadi-iio`, `numpy`, `matplotlib`).
   - Prompt you to plug in the Pluto and run `examples/hello_pluto.py` to confirm everything works.

> **Manual PowerShell Alternative**: If you prefer running PowerShell manually:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> .\scripts\windows_setup.ps1
> ```

---

## ⚠️ Important Physical Hardware Note

The ADALM-PLUTO has **two Micro-USB ports**:
1. **Middle port labeled `USB`**: This carries **both data and power**. Always connect your PC to this port.
2. **Outer port labeled `POWER`**: This is for auxiliary power only (no data communication with the PC).

> Always ensure you use a **data-capable USB cable** connected to the **middle `USB` port**.

---

## 🩺 Hardware Diagnostics & Telemetry

Check your Pluto's health, signal throughput, and frequency unlocking status at any time:

- **Double-click `run_diagnostics.bat`** (or run `python scripts/pluto_diagnostics.py`).
- It tests:
  - Device telemetry & firmware version
  - Onboard transceiver temperature (°C)
  - **Stock AD9363 vs Unlocked AD9364 detection**
  - Live USB streaming benchmark (MB/s throughput)

---

## 🔓 Unlocking 70 MHz – 6.0 GHz (AD9364 Mode)

Factory-stock Plutos support **325 MHz to 3800 MHz**. You can safely unlock the full **70 MHz to 6000 MHz (6.0 GHz)** range and dual-core CPU via a simple 2-command U-Boot setting.

👉 **Read the full step-by-step guide: [docs/unlocking_ad9364.md](docs/unlocking_ad9364.md)**

---

## 💻 Using it in VS Code

1. Open this folder in VS Code (`code .` from the repo folder, or File > Open Folder).
2. `Ctrl+Shift+P` → **Python: Select Interpreter** → choose `.venv` (`.venv\Scripts\python.exe`).
3. Open `examples/hello_pluto.py` and hit Run (▶) — you should see the Pluto's hardware info and sample capture printed in the terminal.
4. Start writing your own scripts. The pattern is always:
   ```python
   import adi
   sdr = adi.Pluto(uri="ip:192.168.2.1")
   ```

---

## 📁 Example Scripts Included

- `examples/hello_pluto.py` — connects and prints basic device info (LO frequency, sample rates, buffer) and captures test IQ samples.
- `examples/tx_rx_loopback.py` — generates and transmits a 100 kHz tone at 915 MHz, captures the RX buffer, and saves + displays the FFT frequency spectrum (`rx_loopback_spectrum.png`).

> **Tip**: All example scripts accept a custom URI as an optional command-line argument:
> ```bash
> python examples/hello_pluto.py ip:192.168.2.1
> # or over direct USB context:
> python examples/hello_pluto.py usb:1.2.5
> ```

---

## 🔧 Troubleshooting (Windows)

- **Script won't run / "running scripts is disabled"**:
  If using PowerShell directly, ensure you run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`. If using `setup.bat`, this is handled automatically.
- **Driver install seems to do nothing / device not detected**:
  1. Confirm your cable is plugged into the **middle `USB` port**, not the `POWER` port.
  2. Verify that your USB cable supports data transfer (some cheap cables are charging-only).
  3. Look in **Device Manager** under **Network adapters** for `Remote NDIS Compatible Device` or `ADALM-PLUTO`.
- **`hello_pluto.py` times out on `192.168.2.1`**:
  The Pluto takes about 15-20 seconds to boot up after being plugged in. Try pinging it in PowerShell:
  ```powershell
  ping 192.168.2.1
  ```
- **Frequency Range Note**:
  A stock ADALM-PLUTO (AD9363) supports **325 MHz to 3800 MHz** (3.8 GHz). If you try to tune outside this band (e.g., 100 MHz or 5.8 GHz) on stock firmware, you will encounter an `Invalid argument` error. Unlock to AD9364 using [docs/unlocking_ad9364.md](docs/unlocking_ad9364.md).
- **IP conflict** (if your local LAN / home router uses `192.168.2.x`):
  Pluto's static IP can be changed in its internal `config.txt` mass storage drive or via SSH — see the [ADI Pluto Documentation](https://wiki.analog.com/university/tools/pluto/users/customizing).

---

## 🍎 Also Supported: macOS & Linux

```bash
# macOS (requires Homebrew)
bash scripts/macos_setup.sh

# Linux (Debian / Ubuntu / Fedora / Arch)
bash scripts/linux_setup.sh
```

- **Linux**: Installs `libiio` and automatically configures udev rules (`/etc/udev/rules.d/53-adi-plutosdr-usb.rules`) for non-root USB access.
- **macOS**: Installs `libiio` via Homebrew and configures the virtual environment.

---

## 🐳 Optional: Docker (Linux hosts only)

> **Note**: For Windows users, the native `setup.bat` is recommended. Docker Desktop on Windows/WSL2 cannot bridge USB/RNDIS network interfaces directly without extra tools like `usbipd-win`. On Linux hosts, Docker `--network host` works out of the box:

```bash
docker build -t pluto-sdr -f docker/Dockerfile .
docker run --rm -it --network host pluto-sdr
```

VS Code Dev Container configuration is also provided in `.devcontainer/devcontainer.json`.

---

## 📂 Repository Structure

```
├── setup.bat             # 1-Click setup launcher for Windows (auto UAC elevation)
├── run_diagnostics.bat   # Double-click diagnostics launcher
├── docs/
│   └── unlocking_ad9364.md # Step-by-step guide to unlock 70 MHz - 6 GHz & dual core
├── examples/
│   ├── hello_pluto.py    # Basic connectivity and device inspection test
│   └── tx_rx_loopback.py # Loopback tone transmission & FFT spectrum plot
├── scripts/
│   ├── pluto_diagnostics.py # Hardware health check, probe & benchmark
│   ├── windows_setup.ps1 # Windows driver & venv setup script
│   ├── linux_setup.sh    # Linux packages, udev rules & venv setup
│   └── macos_setup.sh    # macOS Homebrew & venv setup
├── requirements.txt      # Python dependencies (pyadi-iio, numpy, matplotlib)
└── README.md
```
