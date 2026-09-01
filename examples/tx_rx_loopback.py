"""
tx_rx_loopback.py

A slightly more useful starting point than hello_pluto.py: transmits a
tone and receives it back, then plots the spectrum. Good template for
your own TX/RX scripts.

Requires a loopback cable between TX and RX (or just observe noise if
you don't have one connected -- the script still runs).
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

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
    try:
        ctxs = iio.scan_contexts()
        for uri, desc in ctxs.items():
            if "Pluto" in desc or "pluto" in uri.lower():
                return uri
        if ctxs:
            return list(ctxs.keys())[0]
    except Exception:
        pass
    for cand in ["ip:192.168.2.1", "ip:192.168.3.1", "ip:pluto.local"]:
        try:
            test_sdr = adi.Pluto(uri=cand)
            del test_sdr
            return cand
        except Exception:
            continue
    return "ip:192.168.2.1"


PLUTO_URI = find_pluto_uri()
CENTER_FREQ = int(915e6)  # 915 MHz (ISM band, valid on stock 325-3800 MHz Pluto)
SAMPLE_RATE = int(2e6)
TONE_FREQ = 100e3  # 100 kHz tone offset

print(f"Connecting to Pluto at {PLUTO_URI}...")
sdr = adi.Pluto(uri=PLUTO_URI)
sdr.sample_rate = SAMPLE_RATE
sdr.tx_lo = CENTER_FREQ
sdr.rx_lo = CENTER_FREQ
sdr.tx_cyclic_buffer = True
sdr.rx_buffer_size = 4096
sdr.tx_hardwaregain_chan0 = -10  # dBm-ish, keep modest for bench testing
sdr.gain_control_mode_chan0 = "slow_attack"

# Build a simple complex tone
N = 4096
t = np.arange(N) / SAMPLE_RATE
tone = 0.5 * np.exp(2j * np.pi * TONE_FREQ * t)
tx_samples = tone * (2**14)  # scale for Pluto's expected 14-bit range

print("Transmitting tone, capturing RX...")
sdr.tx(tx_samples)

# Flush stale initial buffers before capturing
for _ in range(3):
    _ = sdr.rx()

rx_samples = sdr.rx()

# Clean up TX buffer
sdr.tx_destroy_buffer()

spectrum = np.fft.fftshift(np.fft.fft(rx_samples))
freqs = np.fft.fftshift(np.fft.fftfreq(len(rx_samples), d=1 / SAMPLE_RATE))

plt.figure(figsize=(9, 5))
plt.plot(freqs / 1e3, 20 * np.log10(np.abs(spectrum) + 1e-6))
plt.xlabel("Frequency offset (kHz)")
plt.ylabel("Magnitude (dB)")
plt.title(f"RX Spectrum around {CENTER_FREQ / 1e6:.1f} MHz (Tone at +{TONE_FREQ / 1e3:.0f} kHz)")
plt.grid(True)

output_plot = "rx_loopback_spectrum.png"
plt.savefig(output_plot, dpi=150)
print(f"Spectrum plot saved to '{output_plot}'.")

try:
    plt.show()
except Exception:
    pass
