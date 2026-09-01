"""
hello_pluto.py

Confirms your ADALM-PLUTO is reachable and prints basic info about it.
Run this after setup to sanity-check your environment before writing
your own scripts.
"""

import os
import sys

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
except (ImportError, TypeError, OSError) as _err:
    print(f"Error loading pyadi-iio / libiio: {_err}")
    print("Please run 'setup.bat' or activate your venv and verify libiio is installed.")
    sys.exit(1)


def find_pluto_uri():
    """Returns explicit CLI argument or auto-discovers connected Pluto."""
    if len(sys.argv) > 1:
        return sys.argv[1]

    # Try libiio scan
    try:
        ctxs = iio.scan_contexts()
        for uri, desc in ctxs.items():
            if "Pluto" in desc or "pluto" in uri.lower():
                return uri
        if ctxs:
            return list(ctxs.keys())[0]
    except Exception:
        pass

    # Try candidate IPs
    for cand in ["ip:192.168.2.1", "ip:192.168.3.1", "ip:pluto.local"]:
        try:
            test_sdr = adi.Pluto(uri=cand)
            del test_sdr
            return cand
        except Exception:
            continue

    return "ip:192.168.2.1"


def main():
    pluto_uri = find_pluto_uri()
    print(f"Connecting to Pluto at {pluto_uri} ...")
    try:
        sdr = adi.Pluto(uri=pluto_uri)
    except Exception as e:
        print(f"Failed to connect: {e}")
        print("Checklist:")
        print("  - Is the Pluto plugged into the middle 'USB' port (not 'POWER') and its LED on?")
        print("  - Did the driver/network setup step complete?")
        print("  - Try: ping 192.168.2.1 (or custom IP: python examples/hello_pluto.py ip:192.168.3.1)")
        sys.exit(1)

    print("Connected! Basic device info:")
    print(f"  RX LO frequency:  {sdr.rx_lo / 1e6:.3f} MHz")
    print(f"  TX LO frequency:  {sdr.tx_lo / 1e6:.3f} MHz")
    print(f"  RX sample rate:   {sdr.sample_rate / 1e6:.3f} MSPS")
    print(f"  RX buffer size:   {sdr.rx_buffer_size}")

    print("\nCapturing a small block of samples...")
    # 915 MHz is within the stock AD9363 range (325 MHz - 3800 MHz)
    sdr.rx_lo = int(915e6)
    sdr.rx_buffer_size = 1024
    samples = sdr.rx()
    print(f"  Got {len(samples)} IQ samples. First 5: {samples[:5]}")

    print("\nAll good — your Pluto is set up correctly.")


if __name__ == "__main__":
    main()
