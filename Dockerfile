FROM python:3.7-slim-stretch AS builder

LABEL org.opencontainers.image.title "bitcoin-prometheus-exporter"
LABEL org.opencontainers.image.description "Prometheus exporter for bitcoin nodes"

RUN pip install --no-cache-dir \
        prometheus_client \
        python-bitcoinlib \
        riprova

RUN mkdir -p /monitor
ADD ./bitcoind-monitor.py /monitor

CMD ["/monitor/bitcoind-monitor.py"]
