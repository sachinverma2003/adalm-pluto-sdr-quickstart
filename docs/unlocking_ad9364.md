# Unlocking AD9364 Mode & 70 MHz – 6 GHz Range on ADALM-PLUTO

The ADALM-PLUTO is physically equipped with an Analog Devices RF transceiver that is silicon-identical to the high-end **AD9364**. By default, factory firmware limits the device tree to **AD9363** specifications.

Analog Devices officially supports software-switching the device compatibility mode via U-Boot environment variables.

---

## ⚡ What Gets Unlocked?

| Specification | Stock Factory Mode (AD9363) | Unlocked Mode (AD9364) |
| :--- | :--- | :--- |
| **Frequency Range** | **325 MHz to 3800 MHz** (3.8 GHz) | **70 MHz to 6000 MHz** (6.0 GHz) |
| **RF Bandwidth** | Up to **20 MHz** | Up to **56 MHz** |
| **Bands Unlocked** | UHF, 433 MHz, 915 MHz, 2.4 GHz | FM Broadcast (88–108 MHz), VHF Airband, ADS-B (1090 MHz), 5 GHz WiFi, 5.8 GHz ISM |
| **CPU Processing** | Single ARM Core (default) | **Dual ARM Cortex-A9 Cores** |

---

## 🚀 How to Unlock (Step-by-Step)

The quickest method is connecting to the Pluto's built-in Linux system via **SSH**.

### Step 1: Open SSH to Pluto
1. Plug your Pluto into your PC (middle port labeled `USB`).
2. Open PowerShell or a terminal and run:
   ```bash
   ssh root@192.168.2.1
   ```
3. When prompted for password, enter:
   ```text
   analog
   ```

---

### Step 2: Set the U-Boot Variables
At the `#` prompt, copy and paste the following commands:

```bash
# Enable AD9364 RF Transceiver Mode (70 MHz - 6 GHz, 56 MHz BW)
fw_setenv attr_name compatible
fw_setenv attr_val "ad9364"

# (Optional but Recommended) Enable the 2nd ARM CPU Core
fw_setenv maxcpus

# Reboot the Pluto to apply changes
reboot
```

The Pluto will reboot automatically (LED will flash and turn solid within ~15 seconds).

---

## 🔍 How to Verify the Unlock

Once the Pluto boots back up, verify the expansion using the included diagnostics tool:

1. Double-click `run_diagnostics.bat` (or run in terminal):
   ```bash
   python scripts/pluto_diagnostics.py
   ```
2. Look at section `3. Hardware Unlocking & Frequency Coverage Probe`:
   ```text
   [+] Status: UNLOCKED (AD9364 Mode)
   [+] Frequency Range:  70 MHz to 6000 MHz (6.0 GHz)
   [+] Max RF Bandwidth: Up to 56 MHz
   ```

---

## 🔄 How to Revert Back to Factory Stock Mode

If you ever want to restore factory default settings:

1. SSH back into Pluto: `ssh root@192.168.2.1` (password: `analog`)
2. Clear the override variables:
   ```bash
   fw_setenv attr_name
   fw_setenv attr_val
   reboot
   ```

---

> Reference: [Analog Devices Wiki - PlutoSDR Customizing](https://wiki.analog.com/university/tools/pluto/users/customizing#updating_to_the_ad9364)
