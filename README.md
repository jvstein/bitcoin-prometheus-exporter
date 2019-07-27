# Bitcoin Node Exporter

This is a docker image that runs a modified version of [`bitcoin-monitor.md`][source-gist]. The script has been modified
to use the [python-bitcoinlib] library to directly call the RPC server, removing the need for the `bitcoin-cli` binary
in the image.

[source-gist]: https://gist.github.com/ageis/a0623ae6ec9cfc72e5cb6bde5754ab1f
[python-bitcoinlib]: https://github.com/petertodd/python-bitcoinlib

# Run the container
```
docker run \
    --name=bitcoin-exporter \
    -e BITCOIN_RPC_USER=alice \
    -e BITCOIN_RPC_PASSWORD=DONT_USE_THIS_YOU_WILL_GET_ROBBED_8ak1gI25KFTvjovL3gAM967mies3E= \
    jvstein/bitcoin-prometheus-exporter:latest
```


# Change Log

- Remove need for `txindex=` to be set on the bitcoin server. Transactions are now pulled using the `getblock` call by
  setting `verbosity=2`.
- Add additional `bitcoin_hashps_1` and `bitcoin_hashps_neg1` for estimated hash rates associated with only the last
  block and for all blocks with the same difficulty.
- Add `bitcoin_est_smart_fee_*` metrics for estimated fee per kilobyte for confirmation within a number of blocks.
- Add `bitcoin_latest_block_value` for the transaction value of the last block.
- Add `bitcoin_server_version` and `bitcoin_protocol_version` to track upgrades of the bitcoin server.
- Add `bitcoin_mempool_usage` metric.
- Add `bitcoin_ban_created` and `bitcoin_banned_until` to track peer bans.
