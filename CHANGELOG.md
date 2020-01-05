# Changelog
Changes to the project.

## [Unreleased]

## [0.4.0] - 2020-01-05

### Added
- New counter metric `bitcoin_exporter_process_time_total` for time spent refreshing the metrics.
- New `bitcoin_verification_progress` metric to track chain verification progress ([#5][pr-5]).
- Use `logging` for output messages and improve level of output for errors ([#4][issue-4]).
- Add docker-compose config with basic setup for testing regressions.

[pr-5]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/5
[issue-4]: https://github.com/jvstein/bitcoin-prometheus-exporter/issues/4

### Changed
- Update script shebang to use PATH ([#6][pr-6])
- Prefer the `$HOME/.bitcoin/bitcoin.conf` file over `BITCOIN_RPC_HOST`, `BITCOIN_RPC_USER`, ... if it exists ([#7][pr-7]).
- Add pre-commit hooks for catching style and code issues.
- Added type annotations and no longer attempting to support less than Python 3.7.

[pr-6]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/6
[pr-7]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/7

### Fixed
- Avoid crashing on node restart by ignoring `bitcoin.rpc.InWarmupError` exception.
- Prevent KeyError when smartfee values are not calculable ([#2][issue-2]).
- Fix duplicate sleep call introduced in 5d83f9e ([#3][issue-3]).

[issue-2]: https://github.com/jvstein/bitcoin-prometheus-exporter/issues/2
[issue-3]: https://github.com/jvstein/bitcoin-prometheus-exporter/issues/3

### Changed
- Retry failed RPC calls with exponential timeout using riprova and keep track of retry exceptions using new
  `bitcoin_exporter_errors` metric.
- Improved error message when credentials are incorrect.
- Make smartfee metrics configurable using `SMARTFEE_BLOCKS` environment variable.

## [0.3.0] - 2019-11-25

### Added
- Include explicit 3-clause BSD LICENSE.
- New `bitcoin_latest_block_weight` and `bitcoin_latest_block_height` metrics using value from [getblock].
- Include my rudimentary dashboard.

### Changed
- Update `bitcoin_latest_block_txs` to use the `nTx` value returned by [getblock] instead of `len(tx)`. No observed change in value.

### Removed
- Dead code cleanup (`find_bitcoin_cli` and `BITCOIN_CLI_PATH`).

[getblock]: https://bitcoincore.org/en/doc/0.18.0/rpc/blockchain/getblock/

## [0.2.0] - 2019-10-20

### Added
- New metrics from [getmemoryinfo] with the `bitcoin_meminfo_` prefix.
- `bitcoin_size_on_disk` metric with data from [getblockchaininfo].

[getmemoryinfo]: https://bitcoincore.org/en/doc/0.18.0/rpc/control/getmemoryinfo/
[getblockchaininfo]: https://bitcoincore.org/en/doc/0.18.0/rpc/blockchain/getblockchaininfo/

### Changed
- Move changelog to separate file.
- Make binding port configurable using `METRICS_PORT` environment variable.

### Fixed
- Fix example commands in README.
- Handle SIGTERM gracefully to avoid later SIGKILL.


## [0.1.0] - 2019-07-27

Initial release of project. Changes are relative to the [`bitcoin-monitor.md`][source-gist] gist, which was commited
as-is in the first commit.

[source-gist]: https://gist.github.com/ageis/a0623ae6ec9cfc72e5cb6bde5754ab1f

### Added
- Packaged for docker and modified to pull settings from environment variables.
- `bitcoin_hashps_1` and `bitcoin_hashps_neg1` for estimated hash rates associated with only the last block and for all blocks with the same difficulty.
- `bitcoin_est_smart_fee_*` metrics for estimated fee per kilobyte for confirmation within a number of blocks.
- `bitcoin_latest_block_value` for the transaction value of the last block.
- `bitcoin_server_version` and `bitcoin_protocol_version` to track upgrades of the bitcoin server.
- `bitcoin_mempool_usage` metric.
- `bitcoin_ban_created` and `bitcoin_banned_until` to track peer bans.

### Changed
- Use RPC calls using [python-bitcoinlib] instead of relying on the `bitcoin-cli` binary.
- Remove need for `txindex=` to be set on the bitcoin server. Transactions are now pulled using the `getblock` call by setting `verbosity=2`.

[python-bitcoinlib]: https://github.com/petertodd/python-bitcoinlib

[Unreleased]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/5abac0a8c58a9c0a79c6493b3273e04fda7b050f...v0.1.0
