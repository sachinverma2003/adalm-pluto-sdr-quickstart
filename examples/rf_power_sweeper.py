"""
rf_power_sweeper.py

Wideband RF Power Sweeper & Band RSSI Scanner.

Default Range: 800 MHz to 1000 MHz
Range check: Default range is strictly within factory stock PlutoSDR range (325 MHz - 3800 MHz).
             Validates user inputs and warns if <325 MHz or >3800 MHz requires unlocked AD9364 mode.

Features:
- Sweeps across a specified RF frequency range in user-configured step sizes.
- Measures average received power (dB) / RSSI across the spectrum band.
- Automatically identifies peak active transmissions and frequencies.
- Saves a wideband spectrum power plot ('rf_power_sweep.png').
- Supports synthetic simulation mode (--sim).
"""

import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt

STOCK_MIN_FREQ = int(325e6)  # 325 MHz
STOCK_MAX_FREQ = int(3800e6) # 3.8 GHz

try:
    import iio
    import adi
    HAS_ADI = True
except Exception:
    HAS_ADI = False


def validate_frequency_range(start_freq_hz, stop_freq_hz):
    """Validates requested sweep frequency bounds against stock hardware limits."""
    print(f"[+] Requested sweep band: {start_freq_hz / 1e6:.1f} MHz to {stop_freq_hz / 1e6:.1f} MHz")
    if start_freq_hz < STOCK_MIN_FREQ or stop_freq_hz > STOCK_MAX_FREQ:
        print(f"[!] Note: Target band extends outside stock factory range ({STOCK_MIN_FREQ / 1e6:.0f}–{STOCK_MAX_FREQ / 1e6:.0f} MHz).")
        print("    If tuning fails, ensure your Pluto is unlocked to AD9364 mode (70–6000 MHz). See docs/unlocking_ad9364.md.")
        return False
    print(f"[+] Frequency check: Sweep band is within stock AD9363 range ({STOCK_MIN_FREQ / 1e6:.0f}–{STOCK_MAX_FREQ / 1e6:.0f} MHz).")
    return True


def sweep_hardware(start_freq_hz, stop_freq_hz, step_freq_hz, uri=None):
    """Sweeps Pluto SDR tuner across frequency steps and measures received signal power."""
    freq_steps = np.arange(start_freq_hz, stop_freq_hz + step_freq_hz, step_freq_hz)
    powers_db = []

    try:
        sdr = adi.Pluto(uri=uri) if uri else adi.Pluto()
        sdr.sample_rate = int(2e6)
        sdr.rx_buffer_size = 4096
        sdr.gain_control_mode_chan0 = "manual"
        sdr.rx_hardwaregain_chan0 = 30  # Fixed gain for consistent RSSI sweep

        for freq in freq_steps:
            sdr.rx_lo = int(freq)
            _ = sdr.rx() # Flush buffer
            samples = sdr.rx()
            power_linear = np.mean(np.abs(samples)**2)
            power_db = 10 * np.log10(power_linear + 1e-12)
            powers_db.append(power_db)

        return freq_steps, np.array(powers_db)
    except Exception as e:
        print(f"[-] Hardware sweep failed: {e}")
        return None, None


def simulate_sweep(start_freq_hz, stop_freq_hz, step_freq_hz):
    """Simulates wideband spectrum scan with synthetic RF emitters."""
    freq_steps = np.arange(start_freq_hz, stop_freq_hz + step_freq_hz, step_freq_hz)

    # Base noise floor around -60 dB
    np.random.seed(42)
    powers_db = -60 + np.random.normal(0, 1.5, len(freq_steps))

    # Add synthetic peaks (e.g. active transmissions at 850 MHz and 915 MHz)
    for idx, f in enumerate(freq_steps):
        if abs(f - 850e6) < 15e6:
            powers_db[idx] += 25 * np.exp(-((f - 850e6) / 5e6)**2)
        if abs(f - 915e6) < 15e6:
            powers_db[idx] += 30 * np.exp(-((f - 915e6) / 5e6)**2)

    return freq_steps, powers_db


def main():
    parser = argparse.ArgumentParser(description="Wideband RF Spectrum Power Sweeper")
    parser.add_argument("--start", type=float, default=800, help="Start frequency in MHz (default: 800)")
    parser.add_argument("--stop", type=float, default=1000, help="Stop frequency in MHz (default: 1000)")
    parser.add_argument("--step", type=float, default=10, help="Step frequency in MHz (default: 10)")
    parser.add_argument("--uri", type=str, default=None, help="Pluto SDR URI")
    parser.add_argument("--sim", action="store_true", help="Force synthetic simulation mode")
    args = parser.parse_args()

    start_hz = int(args.start * 1e6)
    stop_hz = int(args.stop * 1e6)
    step_hz = int(args.step * 1e6)

    validate_frequency_range(start_hz, stop_hz)

    freqs, powers = None, None
    if not args.sim and HAS_ADI:
        freqs, powers = sweep_hardware(start_hz, stop_hz, step_hz, uri=args.uri)

    if freqs is None:
        print("[*] Running in SIMULATION mode with synthetic spectrum signals...")
        freqs, powers = simulate_sweep(start_hz, stop_hz, step_hz)

    # Find peak signal
    max_idx = np.argmax(powers)
    peak_freq = freqs[max_idx] / 1e6
    peak_power = powers[max_idx]

    print(f"[+] Sweep Complete:")
    print(f"    - Scanned Range:    {args.start:.1f} MHz to {args.stop:.1f} MHz")
    print(f"    - Peak Transmission: {peak_power:.1f} dB at {peak_freq:.2f} MHz")

    # Plot results
    plt.figure(figsize=(10, 5))
    plt.plot(freqs / 1e6, powers, color='green', marker='o', linestyle='-', linewidth=1.5, label='RSSI Power (dB)')
    plt.plot(peak_freq, peak_power, 'r*', markersize=12, label=f'Peak Peak ({peak_freq:.1f} MHz)')
    plt.title(f"Wideband Spectrum Power Sweep ({args.start:.0f} MHz - {args.stop:.0f} MHz)")
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Relative Received Power (dB)")
    plt.grid(True)
    plt.legend()

    output_plot = "rf_power_sweep.png"
    plt.savefig(output_plot, dpi=150)
    print(f"[+] Wideband power sweep chart saved to '{output_plot}'.")


if __name__ == "__main__":
    main()
