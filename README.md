# Bitcoin Core Prometheus Exporter

A [Prometheus] exporter for [Bitcoin Core] nodes written in python and packaged for running as a container.

A rudimentary Grafana [dashboard] is available in the [`dashboard/bitcoin-grafana.json`](dashboard/bitcoin-grafana.json)
file.

The main script is a modified version of [`bitcoin-monitor.py`][source-gist], updated to remove the need for the
`bitcoin-cli` binary, packaged into a [Docker image][docker-image], and expanded to export additional metrics.

[Bitcoin Core]: https://github.com/bitcoin/bitcoin
[Prometheus]: https://github.com/prometheus/prometheus
[docker-image]: https://hub.docker.com/r/jvstein/bitcoin-prometheus-exporter

[source-gist]: https://gist.github.com/ageis/a0623ae6ec9cfc72e5cb6bde5754ab1f
[python-bitcoinlib]: https://github.com/petertodd/python-bitcoinlib
[dashboard]: https://grafana.com/grafana/dashboards/11274

# Run the container
```
docker run \
    --name=bitcoin-exporter \
    -p 9332:9332 \
    -e BITCOIN_RPC_HOST=bitcoin-node \
    -e BITCOIN_RPC_USER=alice \
    -e BITCOIN_RPC_PASSWORD=DONT_USE_THIS_YOU_WILL_GET_ROBBED_8ak1gI25KFTvjovL3gAM967mies3E= \
    jvstein/bitcoin-prometheus-exporter:v0.7.0
```

## Basic Testing
There's a [`docker-compose.yml`](docker-compose.yml) file in the repository that references a test bitcoin node. To
test changes to the exporter in docker, run the following commands.

```
docker-compose down
docker-compose build
docker-compose up
```

If you see a lot of `ConnectionRefusedError` errors, run `chmod og+r test-bitcoin.conf`.

# [Change Log](CHANGELOG.md)
See the [`CHANGELOG.md`](CHANGELOG.md) file for changes.

# Other Exporters
 - [Rust port](https://github.com/eburghar/bitcoin-exporter)
