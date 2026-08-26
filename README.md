# PlutoSDR Quickstart (Windows-first)

Plug in your ADALM-PLUTO, run **one PowerShell script**, and start
writing/running Python (`pyadi-iio`) against it in VS Code. No manual driver
hunting, no reading the ADI wiki.

> Based on the official quick start: https://wiki.analog.com/university/tools/pluto/users/quick_start

## How it works (no Docker, just a script)

This is **not** a Docker setup by default — it's plain and simple:

1. You clone/download this repo onto your Windows machine.
2. You run `scripts\windows_setup.ps1`.
3. That script installs the official ADI USB driver, sets up a local Python
   virtual environment (`.venv`) with `pyadi-iio` pre-installed, and confirms
   your Pluto is talking to it.
4. You open the folder in VS Code, pick `.venv` as the interpreter, and start
   writing scripts.

That's the whole thing. Docker is available as an optional advanced path
further down, but you don't need it and can ignore that section entirely.

## Windows quick start

1. Clone this repo (or download it as a zip and extract it).
2. Open **PowerShell as Administrator**.
3. `cd` into the repo folder, then run:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\scripts\windows_setup.ps1
   ```
4. When prompted, plug in the Pluto (or make sure it's already plugged in),
   wait for it to show up in **Device Manager**, then press Enter.
5. The script runs a test script (`examples/hello_pluto.py`) automatically to
   confirm the connection works.

### What the driver step actually does

Pluto shows up over USB as a network device (an RNDIS/Ethernet adapter at IP
`192.168.2.1`). Windows doesn't recognize this out of the box, so the script
downloads and silently installs ADI's official signed driver package from
their GitHub releases (`analogdevicesinc/plutosdr-m2k-drivers-win`). Once
installed, Windows treats the Pluto like a small network device permanently —
you won't need to reinstall the driver again, even after replugging it.

### Using it in VS Code

1. Open this folder in VS Code (`code .` from the repo folder, or File > Open Folder).
2. `Ctrl+Shift+P` → **Python: Select Interpreter** → choose the one inside
   `.venv` (e.g. `.venv\Scripts\python.exe`).
3. Open `examples/hello_pluto.py` and hit Run (▶) — you should see the
   Pluto's hardware info printed in the terminal.
4. Start writing your own scripts. The pattern is always:
   ```python
   import adi
   sdr = adi.Pluto(uri="ip:192.168.2.1")
   ```

### Example scripts included

- `examples/hello_pluto.py` — connects and prints basic device info + a
  sample capture. Good first sanity check.
- `examples/tx_rx_loopback.py` — transmits a tone, receives it back, plots
  the spectrum. A more realistic starting template.

## Troubleshooting (Windows)

- **Script won't run / "running scripts is disabled"**: that's why step 3
  above includes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
  — it only applies to that one PowerShell session, nothing permanent.
- **Driver install seems to do nothing**: check Device Manager after
  plugging in the Pluto — look under "Network adapters" and "Ports (COM &
  LPT)". If nothing new appears, unplug/replug, or re-run the script as
  Administrator.
- **`hello_pluto.py` can't connect / times out on `192.168.2.1`**: give it
  10-15 seconds after plugging in, then try `ping 192.168.2.1` in a normal
  terminal. If that fails, the driver/network side didn't come up — re-run
  the setup script.
- **IP conflict** (you're already on a `192.168.2.x` network, e.g. some home
  routers): Pluto's IP can be changed — see the
  [ADI driver troubleshooting page](https://wiki.analog.com/university/tools/pluto/drivers/windows).

## Also supported: macOS / Linux

Same idea, different script:

```bash
# macOS
bash scripts/macos_setup.sh

# Linux
bash scripts/linux_setup.sh
```

Linux doesn't need a special driver at all (Pluto just enumerates as a
network device); macOS needs a one-time libiio install via Homebrew.

---

## Optional / advanced: Docker (Linux hosts only)

**You can ignore this section completely for the Windows workflow above.**
It's here only for people who prefer an isolated container over a local
Python install, and it only works reliably on **Linux** hosts — not Windows,
because Docker Desktop's WSL2 backend can't see the Pluto's USB/network
interface without extra manual `usbipd-win` setup. On Linux, `--network host`
makes it trivial, which is why this path is Linux-only.

```bash
docker build -t pluto-sdr -f docker/Dockerfile .
docker run --rm -it --network host pluto-sdr
```

There's also a `.devcontainer/` config so VS Code's Dev Containers extension
can open the repo inside that image, again on Linux/WSL2 hosts only.

## Repo layout

```
scripts/            OS setup scripts (windows_setup.ps1 is the main one)
examples/           Starter Python scripts using pyadi-iio
docker/             Optional container path (Linux only, not required)
.devcontainer/      Optional VS Code Dev Container config (Linux only)
```
