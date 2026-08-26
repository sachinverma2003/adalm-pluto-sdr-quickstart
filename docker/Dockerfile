FROM python:3.12-slim

# libiio + libad9361 runtime deps for pyadi-iio
RUN apt-get update && apt-get install -y --no-install-recommends \
        libiio-utils \
        libiio0 \
        libusb-1.0-0 \
        iproute2 \
        iputils-ping \
        git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pyadi-iio numpy matplotlib

WORKDIR /work
COPY examples /work/examples

# Container must be run with --network host so it can reach the
# Pluto's default IP (192.168.2.1) exposed on the Linux host's USB
# network interface. See README.md for usage.
CMD ["python3", "examples/hello_pluto.py"]
