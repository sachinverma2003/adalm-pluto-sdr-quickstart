"""
hello_pluto.py

Confirms your ADALM-PLUTO is reachable and prints basic info about it.
Run this after setup to sanity-check your environment before writing
your own scripts.
"""

import sys

try:
    import adi
except ImportError:
    print("pyadi-iio is not installed. Activate your venv and run:")
    print("  pip install pyadi-iio")
    sys.exit(1)

PLUTO_URI = "ip:192.168.2.1"  # default Pluto IP over USB


def main():
    print(f"Connecting to Pluto at {PLUTO_URI} ...")
    try:
        sdr = adi.Pluto(uri=PLUTO_URI)
    except Exception as e:
        print(f"Failed to connect: {e}")
        print("Checklist:")
        print("  - Is the Pluto plugged in and its LED on?")
        print("  - Did the driver/network setup step complete?")
        print("  - Try: ping 192.168.2.1")
        sys.exit(1)

    print("Connected! Basic device info:")
    print(f"  RX LO frequency:  {sdr.rx_lo / 1e6:.3f} MHz")
    print(f"  TX LO frequency:  {sdr.tx_lo / 1e6:.3f} MHz")
    print(f"  RX sample rate:   {sdr.sample_rate / 1e6:.3f} MSPS")
    print(f"  RX buffer size:   {sdr.rx_buffer_size}")

    print("\nCapturing a small block of samples...")
    sdr.rx_lo = int(100e6)  # 100 MHz, just to have a defined LO
    sdr.rx_buffer_size = 1024
    samples = sdr.rx()
    print(f"  Got {len(samples)} IQ samples. First 5: {samples[:5]}")

    print("\nAll good — your Pluto is set up correctly.")


if __name__ == "__main__":
    main()
