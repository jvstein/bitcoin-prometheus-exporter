FROM python:3.8-alpine

LABEL org.opencontainers.image.title "bitcoin-prometheus-exporter"
LABEL org.opencontainers.image.description "Prometheus exporter for bitcoin nodes"

# Dependencies for python-bitcoinlib and sanity check.
RUN apk --no-cache add binutils openssl-dev && \
    python -c "import ctypes, ctypes.util; ctypes.cdll.LoadLibrary(ctypes.util.find_library('ssl') or 'libeay32')"

RUN pip install --no-cache-dir \
        prometheus_client \
        python-bitcoinlib \
        riprova

RUN mkdir -p /monitor
ADD ./bitcoind-monitor.py /monitor

CMD ["/monitor/bitcoind-monitor.py"]
