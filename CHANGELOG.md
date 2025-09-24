# Changelog
Changes to the project.

## [Unreleased]

## [0.9.0] - 2025-09-24

### Changed
- Exporter now exits cleanly on SIGTERM. SIGINT now exits with a non-zero code. ([#38][pr-38])
- Username and password are now properly handled when they contain URL reserved characters. ([#40][issue-40])

[pr-38]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/38
[issue-40]: https://github.com/jvstein/bitcoin-prometheus-exporter/issues/40


## [0.8.0] - 2025-06-25

BREAKING CHANGE: The `bitcoin_ban_created` and `bitcoin_banned_until` metrics are now disabled by default. Re-enable,
if desired, using `BAN_ADDRESS_METRICS=true`.

### Changed
- Update docker base image to be fully qualifed for better podman support ([#25][pr-25])
- Add metric for minimum fee ([#31][pr-31])
- Upgrade to Python 3.13
- Remove support for s390x docker image
- Disable per-address metrics for banned peers. Add `bitcoin_banned_peers` metric for summary information. ([#13][issue-13])
- Remove unused `RETRIES` variable ([#36][issue-36])

[pr-25]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/25
[pr-31]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/31
[issue-13]: https://github.com/jvstein/bitcoin-prometheus-exporter/issues/13
[issue-36]: https://github.com/jvstein/bitcoin-prometheus-exporter/issues/36


## [0.7.0] - 2022-01-14

**BREAKING CHANGE: Default port number has changed to 9332! Use `METRICS_PORT=8334` to use old port.**

### Added
- Add `bitcoin_rpc_active` stat for number of active RPC calls.
  - [Source](https://github.com/EchterAgo/bitcoin-prometheus-exporter/commit/cc2a804e214556414c7184830166242c34d42457)
- Add `bitcoin_txcount` stat for total number of transactions since the genesis block.
  - [Source 1](https://github.com/EchterAgo/bitcoin-prometheus-exporter/commit/b368138574641e4e26a8a2dfc8be6eede82f4a73)
  - [Source 2](https://github.com/EchterAgo/bitcoin-prometheus-exporter/commit/a9a6b250f463906c1b1f9446d9a689c78c4add6d)
- Support for Bitcoin Cash nodes ([#22][pr-22]).

[pr-22]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/22

### Changed
- Default port changed from `8334` to `9332` to avoid conflicts with Bitcoin Tor port.
- Update metrics on HTTP request, instead of timer ([#12][issue-12]).
  - [Source 1](https://github.com/EchterAgo/bitcoin-prometheus-exporter/commit/c8382240b7a931503dfdd4c8cf89a8415326caf6)
  - [Source 2](https://github.com/EchterAgo/bitcoin-prometheus-exporter/commit/89212072386307fcb6a9f062ee7f958a266b1075)
- Improve performance of block statistics.
  - [Source](https://github.com/EchterAgo/bitcoin-prometheus-exporter/commit/9c018bf081bfdc604af03d8dedd125197401b2de)
- The number of blocks for the `bitcoin_hashps` metrics is now configurable via `HASHPS_BLOCKS` ([#22][pr-22]).

[issue-12]: https://github.com/jvstein/bitcoin-prometheus-exporter/issues/12


## [0.6.0] - 2021-06-05

### Added
- Support changing bind address with `METRICS_ADDR` environment variable ([#11][pr-11]).
- Add `requirements.txt` file.
- Set default `bad_reason` to "manually added" to support Bitcoin Core 0.20.1 ([#16][pr-16]).
- Remove premature URL encoding of bitcoind rpc credentials ([#18][pr-18]).
- New metrics for Bitcoin Core 0.21.0.
- Support for ARM docker image builds via `buildx`.

[pr-11]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/11
[pr-16]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/16
[pr-18]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/18

### Fixed
- Fix port number in README ([#17][pr-17]).

[pr-17]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/17

## Changed
- Modify type annotations to run on python 3.5.


## [0.5.0] - 2020-02-10

### Fixed
- Avoid crash on `socket.timeout` errors. Retry the request in that case.

### Changed
- Switch to python 3.8 and alpine for base image.
- Update docker container to use `nobody` instead of default `root` account.
- Update shebang to use PATH ([#6][pr-6]).
- Support loading bitcoin config from `BITCOIN_CONF_PATH` environment variable ([#7][pr-7]).
- Reuse the `Proxy` RPC client to avoid repeatedly looking for config file.
- Config file examples in the docker-compose file.
- Retry on `ConnectionError`, not just `ConnectionRefusedError` ([#9][pr-9]).
- Pass `TIMEOUT` environment value to bitcoin client as well as retry library.
- Rely on python-bitcoinlib to handle bitcoin config location detection ([#10][pr-10]).

[pr-6]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/6
[pr-7]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/7
[pr-9]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/9
[pr-10]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/10


## [0.4.0] - 2020-01-05

### Added
- New counter metric `bitcoin_exporter_process_time_total` for time spent refreshing the metrics.
- New `bitcoin_verification_progress` metric to track chain verification progress ([#5][pr-5]).
- Use `logging` for output messages and improve level of output for errors ([#4][issue-4]).
- Add docker-compose config with basic setup for testing regressions.

[pr-5]: https://github.com/jvstein/bitcoin-prometheus-exporter/pull/5
[issue-4]: https://github.com/jvstein/bitcoin-prometheus-exporter/issues/4

### Changed
- Retry failed RPC calls with exponential timeout using riprova and keep track of retry exceptions using new
  `bitcoin_exporter_errors` metric.
- Improved error message when credentials are incorrect.
- Make smartfee metrics configurable using `SMARTFEE_BLOCKS` environment variable.
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

[Unreleased]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jvstein/bitcoin-prometheus-exporter/compare/5abac0a8c58a9c0a79c6493b3273e04fda7b050f...v0.1.0
