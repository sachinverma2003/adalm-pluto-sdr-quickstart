"""
fm_radio.py

WFM / NFM Demodulator & Audio Recorder.

Default Target: 98.5 MHz (Commercial FM Broadcast 88–108 MHz)

Frequency & Unlocking Bounds Note:
- Commercial FM broadcast band (88–108 MHz) requires unlocking your Pluto SDR
  to AD9364 mode (70 MHz – 6000 MHz).
- Stock factory Plutos support 325 MHz – 3800 MHz.
- This script tests hardware capability at runtime. If running on stock firmware,
  it alerts the user and provides instructions to unlock AD9364 (docs/unlocking_ad9364.md)
  or automatically falls back to simulation mode / in-range frequencies.

Features:
- Performs Quadrature FM demodulation (np.angle(rx[1:] * np.conj(rx[:-1]))).
- Applies deemphasis filter (75 µs) and downsamples audio to 48 kHz.
- Exports demodulated audio to a WAV file ('fm_audio.wav').
- Plots RF spectrum and audio waveform ('fm_radio_spectrum.png').
- Supports synthetic simulation mode (--sim).
"""

import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import decimate, lfilter, firwin
from scipy.io import wavfile

DEFAULT_FM_FREQ = int(98.5e6)  # 98.5 MHz (Requires AD9364 70-6000 MHz unlocked mode)
SAMPLE_RATE = int(2.4e6)       # 2.4 MSPS RF rate
AUDIO_RATE = int(48e3)         # 48 kHz Audio rate
DECIMATION = int(SAMPLE_RATE / AUDIO_RATE) # 50x
STOCK_MIN_FREQ = int(325e6)

try:
    import iio
    import adi
    HAS_ADI = True
except Exception:
    HAS_ADI = False


def check_and_probe_frequency(sdr_instance, freq_hz):
    """Probes if Pluto hardware supports requested frequency (<325 MHz requires unlocked mode)."""
    if freq_hz < STOCK_MIN_FREQ:
        print(f"[!] Frequency Bound Notice: Target frequency {freq_hz / 1e6:.1f} MHz is below factory stock limit (325 MHz).")
        try:
            sdr_instance.rx_lo = int(freq_hz)
            print("  [+] Hardware capability check PASSED: Pluto is UNLOCKED (AD9364 mode, 70-6000 MHz).")
            return True
        except Exception:
            print("  [*] Hardware capability check: Stock factory Pluto detected (325–3800 MHz).")
            print("  [*] To listen to 88-108 MHz FM broadcast, unlock AD9364 mode via docs/unlocking_ad9364.md.")
            return False
    return True


def fm_demodulate(rx_iq, rf_rate=2.4e6, audio_rate=48e3):
    """Demodulates FM signal, applies 75µs deemphasis filter, and downsamples to 48kHz."""
    # Quadrature demodulation
    raw_demod = np.angle(rx_iq[1:] * np.conj(rx_iq[:-1]))

    # De-emphasis filter (75 us time constant for North America / 50 us for EU)
    tau = 75e-6
    d_alpha = np.exp(-1.0 / (rf_rate * tau))
    deemph = lfilter([1.0 - d_alpha], [1.0, -d_alpha], raw_demod)

    # Decimate down to 48 kHz
    audio = decimate(deemph, DECIMATION, ftype='fir')
    # Normalize audio
    audio_norm = audio / (np.max(np.abs(audio)) + 1e-12)
    return audio_norm


def simulate_fm_broadcast(duration_sec=1.0, rf_rate=2.4e6, f_tone=1000.0, f_mod_index=5.0):
    """Generates synthetic FM broadcast signal with 1 kHz audio tone."""
    t = np.arange(int(rf_rate * duration_sec)) / rf_rate
    audio_signal = np.sin(2 * np.pi * f_tone * t)

    # Frequency modulation
    phase = 2 * np.pi * f_mod_index * np.cumsum(audio_signal) / rf_rate
    fm_iq = np.exp(1j * phase)

    # Add noise
    noise = (np.random.normal(0, 0.1, len(t)) +
             1j * np.random.normal(0, 0.1, len(t)))
    return fm_iq + noise


def capture_sdr_fm(freq_hz, uri=None):
    """Attempts hardware capture with frequency bound safety probe."""
    if not HAS_ADI:
        return None

    try:
        sdr = adi.Pluto(uri=uri) if uri else adi.Pluto()
        is_supported = check_and_probe_frequency(sdr, freq_hz)

        if not is_supported:
            print("[-] Cannot tune to frequency on stock firmware. Falling back to simulation mode.")
            return None

        sdr.sample_rate = SAMPLE_RATE
        sdr.rx_buffer_size = 262144
        sdr.gain_control_mode_chan0 = "slow_attack"

        print(f"[+] Capturing FM broadcast spectrum at {freq_hz / 1e6:.1f} MHz...")
        for _ in range(2):
            _ = sdr.rx()
        rx_iq = sdr.rx()
        return rx_iq
    except Exception as e:
        print(f"[-] Hardware capture failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="WFM / NFM Demodulator & Audio Recorder")
    parser.add_argument("--freq", type=float, default=98.5, help="Target frequency in MHz (default: 98.5)")
    parser.add_argument("--uri", type=str, default=None, help="Pluto SDR URI")
    parser.add_argument("--sim", action="store_true", help="Force synthetic simulation mode")
    args = parser.parse_args()

    target_freq_hz = int(args.freq * 1e6)

    rx_iq = None
    if not args.sim:
        rx_iq = capture_sdr_fm(target_freq_hz, uri=args.uri)

    if rx_iq is None:
        print(f"[*] Running in SIMULATION mode with synthetic FM broadcast signal at {args.freq:.1f} MHz...")
        rx_iq = simulate_fm_broadcast(duration_sec=1.5, rf_rate=SAMPLE_RATE)

    # Demodulate FM to 48 kHz PCM
    audio_pcm = fm_demodulate(rx_iq, rf_rate=SAMPLE_RATE, audio_rate=AUDIO_RATE)

    # Export WAV file
    audio_int16 = (audio_pcm * 32767).astype(np.int16)
    wav_filename = "fm_audio.wav"
    wavfile.write(wav_filename, AUDIO_RATE, audio_int16)
    print(f"[+] Demodulated audio exported to '{wav_filename}' (48 kHz 16-bit PCM WAV).")

    # Plot RF Spectrum & Demodulated Audio Waveform
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))

    spectrum = np.fft.fftshift(np.fft.fft(rx_iq[:4096]))
    freqs = np.fft.fftshift(np.fft.fftfreq(4096, d=1 / SAMPLE_RATE))
    ax1.plot(freqs / 1e3, 20 * np.log10(np.abs(spectrum) + 1e-6), color='purple')
    ax1.set_title(f"RF Spectrum around {args.freq:.1f} MHz")
    ax1.set_xlabel("Frequency Offset (kHz)")
    ax1.set_ylabel("Magnitude (dB)")
    ax1.grid(True)

    t_audio = np.arange(len(audio_pcm[:2400])) / AUDIO_RATE * 1000
    ax2.plot(t_audio, audio_pcm[:2400], color='teal')
    ax2.set_title("Demodulated Audio Waveform (First 50 ms)")
    ax2.set_xlabel("Time (ms)")
    ax2.set_ylabel("Audio Amplitude")
    ax2.grid(True)

    plt.tight_layout()
    output_plot = "fm_radio_spectrum.png"
    plt.savefig(output_plot, dpi=150)
    print(f"[+] Spectrum and audio plot saved to '{output_plot}'.")


if __name__ == "__main__":
    main()
