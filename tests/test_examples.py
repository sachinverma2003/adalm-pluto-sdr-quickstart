"""
test_examples.py

Automated unit tests for PlutoSDR Quickstart example scripts and frequency bounds checks.
Ensures all example scripts run cleanly in simulation mode without physical SDR hardware attached.
"""

import sys
import subprocess
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def run_script(script_rel_path, extra_args=None):
    """Runs a python script in repo root and asserts exit code 0."""
    script_path = REPO_ROOT / script_rel_path
    cmd = [sys.executable, str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    res = subprocess.run(cmd, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert res.returncode == 0, f"Script {script_rel_path} failed:\nSTDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}"
    return res.stdout


def test_adsb_receiver_sim():
    stdout = run_script("examples/adsb_receiver.py", ["--sim"])
    assert "SIMULATION mode" in stdout
    assert "adsb_pulse.png" in stdout


def test_digital_modem_sim_qpsk():
    stdout = run_script("examples/digital_modem.py", ["--sim", "--mode", "qpsk"])
    assert "QPSK" in stdout
    assert "digital_constellation.png" in stdout


def test_digital_modem_sim_bpsk():
    stdout = run_script("examples/digital_modem.py", ["--sim", "--mode", "bpsk"])
    assert "BPSK" in stdout
    assert "digital_constellation.png" in stdout


def test_rf_power_sweeper_sim():
    stdout = run_script("examples/rf_power_sweeper.py", ["--sim", "--start", "800", "--stop", "900", "--step", "20"])
    assert "SIMULATION mode" in stdout
    assert "rf_power_sweep.png" in stdout


def test_fm_radio_sim():
    stdout = run_script("examples/fm_radio.py", ["--sim", "--freq", "98.5"])
    assert "SIMULATION mode" in stdout
    assert "fm_audio.wav" in stdout
    assert "fm_radio_spectrum.png" in stdout


def test_frequency_bounds_checks():
    from examples.adsb_receiver import check_frequency_range
    assert check_frequency_range(1090e6) is True  # 1090 MHz within stock range
    assert check_frequency_range(100e6) is False  # 100 MHz outside stock range
