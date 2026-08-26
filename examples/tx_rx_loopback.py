"""
tx_rx_loopback.py

A slightly more useful starting point than hello_pluto.py: transmits a
tone and receives it back, then plots the spectrum. Good template for
your own TX/RX scripts.

Requires a loopback cable between TX and RX (or just observe noise if
you don't have one connected -- the script still runs).
"""

import numpy as np
import matplotlib.pyplot as plt
import adi

PLUTO_URI = "ip:192.168.2.1"
CENTER_FREQ = int(915e6)  # 915 MHz, adjust to your region/allowed band
SAMPLE_RATE = int(2e6)
TONE_FREQ = 100e3  # 100 kHz tone offset

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
tx_samples = tone * (2**14)  # scale for Pluto's expected int range

print("Transmitting tone, capturing RX...")
sdr.tx(tx_samples)

rx_samples = sdr.rx()

sdr.tx_destroy_buffer()

spectrum = np.fft.fftshift(np.fft.fft(rx_samples))
freqs = np.fft.fftshift(np.fft.fftfreq(len(rx_samples), d=1 / SAMPLE_RATE))

plt.figure()
plt.plot(freqs / 1e3, 20 * np.log10(np.abs(spectrum) + 1e-6))
plt.xlabel("Frequency offset (kHz)")
plt.ylabel("Magnitude (dB)")
plt.title(f"RX spectrum around {CENTER_FREQ / 1e6:.1f} MHz")
plt.grid(True)
plt.show()
