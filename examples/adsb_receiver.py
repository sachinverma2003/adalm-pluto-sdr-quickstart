"""
adsb_receiver.py

ADS-B (Automatic Dependent Surveillance-Broadcast) 1090 MHz Aircraft Receiver.

Frequency: 1090 MHz (1.09 GHz)
Range check: Operating at 1090 MHz is strictly within factory stock PlutoSDR range (325 MHz - 3800 MHz).

Features:
- Captures 1090 MHz Mode-S PPM (Pulse Position Modulation) aircraft signals.
- Detects ADS-B preamble sync pulses.
- Decodes ICAO 24-bit aircraft hex addresses from Mode-S Extended Squitter frames.
- Supports synthetic simulation mode if physical SDR hardware is not attached or if --sim is passed.
"""

import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt

# Default ADS-B RF parameter constants
ADSB_FREQ = int(1090e6)      # 1090 MHz (Stock range: 325 MHz - 3800 MHz)
SAMPLE_RATE = int(2e6)       # 2 MSPS (1 sample = 0.5 µs)
STOCK_MIN_FREQ = int(325e6)  # 325 MHz
STOCK_MAX_FREQ = int(3800e6) # 3.8 GHz

try:
    import iio
    import adi
    HAS_ADI = True
except Exception:
    HAS_ADI = False


def check_frequency_range(freq_hz):
    """Ensures 1090 MHz is within valid hardware bounds."""
    if not (STOCK_MIN_FREQ <= freq_hz <= STOCK_MAX_FREQ):
        print(f"[!] Warning: {freq_hz / 1e6:.1f} MHz is outside stock Pluto range (325–3800 MHz).")
        return False
    print(f"[+] Frequency check: {freq_hz / 1e6:.1f} MHz is within stock AD9363 range (325–3800 MHz).")
    return True


def generate_synthetic_adsb_signal(sample_rate=2e6, num_samples=10000):
    """Generates synthetic ADS-B Mode-S signal (PPM preamble + random frame data)."""
    t = np.arange(num_samples) / sample_rate
    iq = (np.random.normal(0, 0.05, num_samples) +
          1j * np.random.normal(0, 0.05, num_samples))

    # 2 MSPS = 0.5 us per sample
    # ADS-B preamble pulses at 0.0us, 1.0us, 3.5us, 4.5us -> sample indices 0, 2, 7, 9
    preamble_indices = [0, 2, 7, 9]
    start_idx = 1000

    # Insert strong preamble
    for idx in preamble_indices:
        iq[start_idx + idx] += 1.0 + 0j

    # Insert synthetic PPM data bits (112 bits, each bit = 2 samples)
    # Bit 1 = High-Low [1, 0], Bit 0 = Low-High [0, 1]
    np.random.seed(42)
    bits = np.random.randint(0, 2, 112)
    # Force DF=17 (Extended Squitter 10001 in binary)
    bits[0:5] = [1, 0, 0, 0, 1]

    data_start = start_idx + 16
    for i, b in enumerate(bits):
        pos = data_start + i * 2
        if pos + 1 < num_samples:
            if b == 1:
                iq[pos] += 0.8 + 0j
                iq[pos + 1] += 0.1 + 0j
            else:
                iq[pos] += 0.1 + 0j
                iq[pos + 1] += 0.8 + 0j

    return iq, start_idx, bits


def detect_preambles(magnitude, sample_rate=2e6):
    """
    Correlates signal magnitude against ADS-B Mode-S 8µs preamble pattern.
    At 2 MSPS (0.5 µs / sample):
    Pulse times: 0.0, 1.0, 3.5, 4.5 µs -> indices [0, 2, 7, 9]
    """
    # 8 µs preamble = 16 samples at 2 MSPS
    preamble_pattern = np.array([1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0], dtype=float)

    correlations = np.correlate(magnitude, preamble_pattern, mode='valid')
    threshold = np.max(correlations) * 0.6 if len(correlations) > 0 else 1.0

    detected_indices = np.where(correlations > threshold)[0]
    return detected_indices, correlations


def decode_mode_s_frame(magnitude, start_idx):
    """Decodes 112-bit Mode-S PPM frame starting after preamble (16 samples at 2 MSPS)."""
    data_start = start_idx + 16
    bits = []
    for i in range(112):
        pos = data_start + i * 2
        if pos + 1 >= len(magnitude):
            break
        # Compare high vs low pulse half
        bit = 1 if magnitude[pos] > magnitude[pos + 1] else 0
        bits.append(bit)

    if len(bits) < 112:
        return None

    # Convert bits to hex
    bit_str = "".join(str(b) for b in bits)
    df = int(bit_str[:5], 2)
    icao = hex(int(bit_str[8:32], 2))[2:].zfill(6).upper()
    return {"df": df, "icao": icao, "raw_bits": bit_str}


def capture_sdr_samples(uri=None):
    """Connects to Pluto SDR and captures 1090 MHz IQ samples."""
    if not HAS_ADI:
        print("[!] pyadi-iio is not available.")
        return None

    try:
        if uri:
            sdr = adi.Pluto(uri=uri)
        else:
            sdr = adi.Pluto()

        check_frequency_range(ADSB_FREQ)
        sdr.sample_rate = SAMPLE_RATE
        sdr.rx_lo = ADSB_FREQ
        sdr.gain_control_mode_chan0 = "fast_attack"
        sdr.rx_buffer_size = 32768

        print(f"[+] Connected to Pluto at {ADSB_FREQ / 1e6:.1f} MHz. Capturing ADS-B frame buffer...")
        # Flush initial buffers
        for _ in range(2):
            _ = sdr.rx()
        rx_iq = sdr.rx()
        return rx_iq
    except Exception as e:
        print(f"[-] Could not connect to Pluto SDR hardware: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="ADS-B 1090 MHz Aircraft Receiver & Pulse Decoder")
    parser.add_argument("--uri", type=str, default=None, help="Pluto SDR URI (e.g. ip:192.168.2.1)")
    parser.add_argument("--sim", action="store_true", help="Force synthetic simulation mode without SDR hardware")
    args = parser.parse_args()

    check_frequency_range(ADSB_FREQ)

    rx_iq = None
    if not args.sim:
        rx_iq = capture_sdr_samples(args.uri)

    if rx_iq is None:
        print("[*] Running in SIMULATION mode with synthetic ADS-B 1090 MHz signals...")
        rx_iq, synth_start, synth_bits = generate_synthetic_adsb_signal(SAMPLE_RATE)

    mag = np.abs(rx_iq)
    mag_norm = mag / (np.max(mag) + 1e-12)

    detected_indices, correlations = detect_preambles(mag_norm, SAMPLE_RATE)

    print(f"[+] Detected {len(detected_indices)} candidate Mode-S preambles.")

    if len(detected_indices) > 0:
        first_idx = detected_indices[0]
        decoded = decode_mode_s_frame(mag_norm, first_idx)
        if decoded:
            print(f"[+] Decoded Mode-S Extended Squitter Frame:")
            print(f"    - Downlink Format (DF): {decoded['df']} (DF=17 is Extended Squitter)")
            print(f"    - Aircraft ICAO Hex:    0x{decoded['icao']}")

    # Save visualization plot
    plt.figure(figsize=(10, 5))
    plot_len = min(2000, len(mag_norm))
    plt.plot(mag_norm[:plot_len], label="Normalized Magnitude")
    plt.title("ADS-B 1090 MHz Mode-S Pulse Capture")
    plt.xlabel("Sample Index (0.5 µs / sample @ 2 MSPS)")
    plt.ylabel("Normalized Amplitude")
    plt.grid(True)
    plt.legend()

    output_plot = "adsb_pulse.png"
    plt.savefig(output_plot, dpi=150)
    print(f"[+] Plot saved to '{output_plot}'.")


if __name__ == "__main__":
    main()
