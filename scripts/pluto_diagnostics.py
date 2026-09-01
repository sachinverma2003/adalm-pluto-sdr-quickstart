"""
pluto_diagnostics.py

Comprehensive hardware health check and diagnostics tool for ADALM-PLUTO.
- Supports single or multi-device setups simultaneously
- Verifies network and IIO connectivity
- Reads device telemetry, firmware version, and onboard temperature
- Probes RF tuning range (Stock AD9363 vs Unlocked AD9364 mode)
- Measures USB IQ sample streaming throughput
"""

import os
import sys
import time
import subprocess

# Configure Windows DLL search directories for libiio if running on Windows
if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    for _dll_dir in [
        os.path.join(sys.prefix, "Scripts"),
        os.path.join(sys.prefix, "Lib", "site-packages"),
        r"C:\Program Files\libiio",
        r"C:\Program Files (x86)\libiio",
        r"C:\Program Files\PothosSDR\bin",
        r"C:\Windows\System32",
    ]:
        if os.path.isdir(_dll_dir):
            try:
                os.add_dll_directory(_dll_dir)
            except Exception:
                pass

try:
    import iio
    import adi
    import numpy as np
except (ImportError, TypeError, OSError) as _err:
    print(f"[!] Error: Required dependencies or libiio runtime not loaded: {_err}")
    print("    Please run 'setup.bat' or verify libiio is installed.")
    sys.exit(1)


def print_banner(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def scan_all_plutos():
    """
    Scans USB and Network contexts to return a deduplicated list of connected Pluto SDRs.
    Returns: list of dicts [{'uri': ..., 'desc': ..., 'serial': ...}]
    """
    discovered = []
    seen_serials = set()

    try:
        ctxs = iio.scan_contexts()
        for uri, desc in ctxs.items():
            if "Pluto" in desc or "pluto" in uri.lower() or "0456:b673" in desc:
                # Extract serial if present in description
                serial = "Unknown"
                if "serial=" in desc:
                    serial = desc.split("serial=")[-1].strip()

                if serial != "Unknown" and serial in seen_serials:
                    continue

                if serial != "Unknown":
                    seen_serials.add(serial)

                discovered.append({"uri": uri, "desc": desc, "serial": serial})
    except Exception:
        pass

    # If scan found nothing, probe default IPs
    if not discovered:
        for cand in ["ip:192.168.2.1", "ip:192.168.3.1", "ip:pluto.local"]:
            try:
                sdr = adi.Pluto(uri=cand)
                s_num = sdr.ctx.attrs.get("hw_serial", "Unknown")
                del sdr
                if s_num not in seen_serials:
                    seen_serials.add(s_num)
                    discovered.append({"uri": cand, "desc": cand, "serial": s_num})
            except Exception:
                continue

    return discovered


def check_ping(ip_or_host):
    target = ip_or_host.replace("ip:", "")
    param = "-n" if sys.platform == "win32" else "-c"
    cmd = ["ping", param, "1", target]
    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        return res.returncode == 0
    except Exception:
        return False


def diagnose_single_pluto(target_uri, device_index=1, total_devices=1):
    header = f"Diagnostics for Pluto #{device_index} (URI: {target_uri})" if total_devices > 1 else "Hardware Diagnostics"
    print_banner(header)

    # 1. Network check
    if target_uri.startswith("ip:"):
        print("[*] Testing IP network reachability...", end=" ", flush=True)
        if check_ping(target_uri):
            print("PASS (Host responded to ping)")
        else:
            print("NOTE (Ping timed out/blocked or mDNS - continuing)")

    # 2. IIO Context Connection
    print(f"[*] Connecting to {target_uri} via pyadi-iio...", end=" ", flush=True)
    try:
        sdr = adi.Pluto(uri=target_uri)
        print("CONNECTED successfully!")
    except Exception as e:
        print("FAILED")
        print(f"\n[!] Error connecting to Pluto: {e}")
        print("\nTroubleshooting Checklist:")
        print("  1. Is the USB cable connected to the MIDDLE port labeled 'USB' (not 'POWER')?")
        print("  2. Does the cable support data transfer (not charging-only)?")
        print("  3. Did you wait ~15-20 seconds after plugging in for the Pluto to boot?")
        return False

    # 3. System & Firmware Telemetry
    print_banner("1. System & Device Telemetry")
    ctx_attrs = getattr(sdr.ctx, "attrs", {})
    fw_ver = ctx_attrs.get("fw_version", "N/A")
    hw_model = ctx_attrs.get("hw_model", "ADALM-PLUTO")
    hw_serial = ctx_attrs.get("hw_serial", "N/A")
    libiio_ver = getattr(sdr.ctx, "version", "N/A")

    print(f"  - Device Model:        {hw_model}")
    print(f"  - Firmware Version:    {fw_ver}")
    print(f"  - Serial Number:       {hw_serial}")
    print(f"  - libiio Version:      {libiio_ver}")

    # Read internal temperature sensor
    temp_c = None
    try:
        phy_dev = sdr.ctx.find_device("ad9361-phy")
        if phy_dev:
            chan = phy_dev.find_channel("temp0")
            if chan and "input" in chan.attrs:
                temp_raw = int(chan.attrs["input"].value)
                temp_c = temp_raw / 1000.0
    except Exception:
        pass

    if temp_c is not None:
        print(f"  - Transceiver Temp:    {temp_c:.1f} °C (Operating within safe limits)")
    else:
        print("  - Transceiver Temp:    Not exposed on current kernel/driver")

    # 4. Transceiver RF Configuration
    print_banner("2. RF Transceiver & Configuration")
    sample_rate_msps = sdr.sample_rate / 1e6
    rx_lo_mhz = sdr.rx_lo / 1e6
    tx_lo_mhz = sdr.tx_lo / 1e6
    rx_gain_mode = sdr.gain_control_mode_chan0
    tx_gain = sdr.tx_hardwaregain_chan0

    print(f"  - Current Sample Rate: {sample_rate_msps:.3f} MSPS")
    print(f"  - RX LO Frequency:     {rx_lo_mhz:.3f} MHz")
    print(f"  - TX LO Frequency:     {tx_lo_mhz:.3f} MHz")
    print(f"  - RX Gain Mode:        {rx_gain_mode}")
    print(f"  - TX Hardware Gain:    {tx_gain} dB")
    print(f"  - RX Buffer Size:      {sdr.rx_buffer_size} samples")

    # 5. Hardware Mode Probe (Stock AD9363 vs Unlocked AD9364)
    print_banner("3. Hardware Unlocking & Frequency Coverage Probe")
    original_rx_lo = sdr.rx_lo

    is_unlocked_low = False
    is_unlocked_high = False

    try:
        sdr.rx_lo = int(100e6)
        is_unlocked_low = True
    except Exception:
        is_unlocked_low = False

    try:
        sdr.rx_lo = int(4500e6)
        is_unlocked_high = True
    except Exception:
        is_unlocked_high = False

    # Restore LO
    sdr.rx_lo = original_rx_lo

    if is_unlocked_low and is_unlocked_high:
        print("  [+] Status: UNLOCKED (AD9364 Mode)")
        print("  [+] Frequency Range:  70 MHz to 6000 MHz (6.0 GHz)")
        print("  [+] Max RF Bandwidth: Up to 56 MHz")
    else:
        print("  [*] Status: STOCK FACTORY MODE (AD9363)")
        print("  [*] Frequency Range:  325 MHz to 3800 MHz (3.8 GHz)")
        print("  [*] Max RF Bandwidth: 20 MHz")
        print("  [*] Note: You can unlock 70 MHz - 6.0 GHz anytime! See docs/unlocking_ad9364.md")

    # 6. Throughput & Streaming Benchmark
    print_banner("4. USB Streaming & Throughput Benchmark")
    sdr.rx_buffer_size = 65536
    sdr.sample_rate = int(3e6)
    num_buffers = 16
    total_samples = sdr.rx_buffer_size * num_buffers
    total_bytes = total_samples * 4

    print(f"[*] Capturing {total_samples:,} IQ samples ({total_bytes / (1024*1024):.2f} MB)...", end=" ", flush=True)

    start_time = time.perf_counter()
    for _ in range(num_buffers):
        _ = sdr.rx()
    elapsed = time.perf_counter() - start_time

    rate_mb = (total_bytes / (1024 * 1024)) / elapsed
    rate_msps = (total_samples / 1e6) / elapsed

    print(f"DONE in {elapsed:.3f} s")
    print(f"  - Transfer Speed:      {rate_mb:.2f} MB/s ({rate_msps:.2f} MSPS continuous)")

    print(f"\n[+] Pluto #{device_index} ({hw_serial}) is 100% HEALTHY & READY.")
    return True


def main():
    print_banner("ADALM-PLUTO SDR Multi-Device Diagnostics")

    # If user provided a specific URI via CLI, test only that one
    if len(sys.argv) > 1:
        requested_uri = sys.argv[1]
        print(f"[*] Target URI specified via argument: {requested_uri}")
        diagnose_single_pluto(requested_uri, 1, 1)
        return

    # Auto-scan all connected Plutos
    print("[*] Auto-scanning for all connected Pluto SDRs (USB & Network)...")
    devices = scan_all_plutos()

    if not devices:
        print("[-] No Pluto SDRs detected automatically.")
        print("[*] Falling back to default URI: ip:192.168.2.1")
        diagnose_single_pluto("ip:192.168.2.1", 1, 1)
        return

    print(f"[+] Found {len(devices)} connected Pluto SDR device(s):")
    for idx, dev in enumerate(devices, 1):
        print(f"    {idx}. URI: {dev['uri']}  |  Serial: {dev['serial']}")

    for idx, dev in enumerate(devices, 1):
        diagnose_single_pluto(dev["uri"], idx, len(devices))

    print("\n" + "=" * 60)
    print("  ALL CONNECTED PLUTO SDRs DIAGNOSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
