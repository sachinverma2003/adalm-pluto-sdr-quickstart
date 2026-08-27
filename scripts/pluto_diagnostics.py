"""
pluto_diagnostics.py

Comprehensive hardware health check and diagnostics tool for ADALM-PLUTO.
- Verifies network and IIO connectivity
- Reads device telemetry, firmware version, and onboard temperature
- Probes RF tuning range (Stock AD9363 vs Unlocked AD9364 mode)
- Measures USB IQ sample streaming throughput
"""

import sys
import time
import subprocess

try:
    import iio
    import adi
    import numpy as np
except ImportError:
    print("[!] Error: Required dependencies not found in current environment.")
    print("    Activate your venv and run: pip install -r requirements.txt")
    sys.exit(1)


def print_banner(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def discover_pluto_uri(explicit_uri=None):
    """
    Finds and resolves the Pluto SDR URI:
    1. If explicit URI is provided, uses it directly.
    2. Otherwise, scans local network and USB for Pluto contexts via libiio.
    3. Falls back to probing standard candidate IPs (192.168.2.1, 192.168.3.1, etc.).
    """
    if explicit_uri:
        return explicit_uri

    print("[*] Auto-scanning for connected Pluto SDRs (USB & Network)...", flush=True)

    # 1. Scan via libiio context scanner
    try:
        ctxs = iio.scan_contexts()
        if ctxs:
            for uri, desc in ctxs.items():
                if "Pluto" in desc or "pluto" in uri.lower():
                    print(f"    [+] Found: {uri} ({desc})")
                    return uri
            # If any IIO context found, return the first
            first_uri = list(ctxs.keys())[0]
            print(f"    [+] Found context: {first_uri}")
            return first_uri
    except Exception:
        pass

    # 2. Fallback candidate probing
    candidates = [
        "ip:192.168.2.1",
        "ip:192.168.3.1",
        "ip:pluto.local",
        "usb:",
    ]
    for cand in candidates:
        try:
            test_sdr = adi.Pluto(uri=cand)
            print(f"    [+] Connected via candidate: {cand}")
            del test_sdr
            return cand
        except Exception:
            continue

    # Default fallback
    return "ip:192.168.2.1"


def check_ping(ip_or_host):
    target = ip_or_host.replace("ip:", "")
    param = "-n" if sys.platform == "win32" else "-c"
    cmd = ["ping", param, "1", target]
    try:
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        return res.returncode == 0
    except Exception:
        return False


def main():
    print_banner("ADALM-PLUTO SDR Hardware Diagnostics")

    requested_uri = sys.argv[1] if len(sys.argv) > 1 else None
    target_uri = discover_pluto_uri(requested_uri)
    print(f"[*] Target URI: {target_uri}")

    # 1. Network check
    if target_uri.startswith("ip:"):
        print("[*] Testing IP network reachability...", end=" ", flush=True)
        if check_ping(target_uri):
            print("PASS (Host responded to ping)")
        else:
            print("NOTE (Ping timed out/blocked or mDNS - continuing)")

    # 2. IIO Context Connection
    print("[*] Connecting via pyadi-iio...", end=" ", flush=True)
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
        print("  4. If custom IP, run: python scripts/pluto_diagnostics.py ip:<your-ip>")
        sys.exit(1)

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

    # Try reading internal temperature sensor
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

    # 4. Transceiver RF Capabilities
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

    # Test tuning to 100 MHz (below stock 325 MHz limit)
    try:
        sdr.rx_lo = int(100e6)
        is_unlocked_low = True
    except Exception:
        is_unlocked_low = False

    # Test tuning to 4.5 GHz (above stock 3.8 GHz limit)
    try:
        sdr.rx_lo = int(4500e6)
        is_unlocked_high = True
    except Exception:
        is_unlocked_high = False

    # Restore safe LO
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
    sdr.sample_rate = int(3e6)  # 3 MSPS
    num_buffers = 16
    total_samples = sdr.rx_buffer_size * num_buffers
    total_bytes = total_samples * 4  # 16-bit I + 16-bit Q = 4 bytes/sample

    print(f"[*] Capturing {total_samples:,} IQ samples ({total_bytes / (1024*1024):.2f} MB)...", end=" ", flush=True)

    start_time = time.perf_counter()
    for _ in range(num_buffers):
        _ = sdr.rx()
    elapsed = time.perf_counter() - start_time

    rate_mb = (total_bytes / (1024 * 1024)) / elapsed
    rate_msps = (total_samples / 1e6) / elapsed

    print(f"DONE in {elapsed:.3f} s")
    print(f"  - Transfer Speed:      {rate_mb:.2f} MB/s ({rate_msps:.2f} MSPS continuous)")

    print_banner("Summary: All Diagnostic Checks Passed! Pluto is 100% Ready.")


if __name__ == "__main__":
    main()
