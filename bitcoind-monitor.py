#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import time
import os
import signal
import sys
import socket

from datetime import datetime
from functools import lru_cache
from typing import Any
from typing import Dict
from typing import List
from typing import Union
from urllib.parse import quote

import riprova

from bitcoin.rpc import InWarmupError, Proxy
from prometheus_client import start_http_server, Gauge, Counter


logger = logging.getLogger("bitcoin-exporter")


# Create Prometheus metrics to track bitcoind stats.
BITCOIN_BLOCKS = Gauge("bitcoin_blocks", "Block height")
BITCOIN_DIFFICULTY = Gauge("bitcoin_difficulty", "Difficulty")
BITCOIN_PEERS = Gauge("bitcoin_peers", "Number of peers")
BITCOIN_HASHPS_NEG1 = Gauge(
    "bitcoin_hashps_neg1", "Estimated network hash rate per second since the last difficulty change"
)
BITCOIN_HASHPS_1 = Gauge(
    "bitcoin_hashps_1", "Estimated network hash rate per second for the last block"
)
BITCOIN_HASHPS = Gauge(
    "bitcoin_hashps", "Estimated network hash rate per second for the last 120 blocks"
)

BITCOIN_ESTIMATED_SMART_FEE_GAUGES: Dict[int, Gauge] = {}

BITCOIN_WARNINGS = Counter("bitcoin_warnings", "Number of network or blockchain warnings detected")
BITCOIN_UPTIME = Gauge("bitcoin_uptime", "Number of seconds the Bitcoin daemon has been running")

BITCOIN_MEMINFO_USED = Gauge("bitcoin_meminfo_used", "Number of bytes used")
BITCOIN_MEMINFO_FREE = Gauge("bitcoin_meminfo_free", "Number of bytes available")
BITCOIN_MEMINFO_TOTAL = Gauge("bitcoin_meminfo_total", "Number of bytes managed")
BITCOIN_MEMINFO_LOCKED = Gauge("bitcoin_meminfo_locked", "Number of bytes locked")
BITCOIN_MEMINFO_CHUNKS_USED = Gauge("bitcoin_meminfo_chunks_used", "Number of allocated chunks")
BITCOIN_MEMINFO_CHUNKS_FREE = Gauge("bitcoin_meminfo_chunks_free", "Number of unused chunks")

BITCOIN_MEMPOOL_BYTES = Gauge("bitcoin_mempool_bytes", "Size of mempool in bytes")
BITCOIN_MEMPOOL_SIZE = Gauge(
    "bitcoin_mempool_size", "Number of unconfirmed transactions in mempool"
)
BITCOIN_MEMPOOL_USAGE = Gauge("bitcoin_mempool_usage", "Total memory usage for the mempool")

BITCOIN_LATEST_BLOCK_HEIGHT = Gauge(
    "bitcoin_latest_block_height", "Height or index of latest block"
)
BITCOIN_LATEST_BLOCK_WEIGHT = Gauge(
    "bitcoin_latest_block_weight", "Weight of latest block according to BIP 141"
)
BITCOIN_LATEST_BLOCK_SIZE = Gauge("bitcoin_latest_block_size", "Size of latest block in bytes")
BITCOIN_LATEST_BLOCK_TXS = Gauge(
    "bitcoin_latest_block_txs", "Number of transactions in latest block"
)

BITCOIN_NUM_CHAINTIPS = Gauge("bitcoin_num_chaintips", "Number of known blockchain branches")

BITCOIN_TOTAL_BYTES_RECV = Gauge("bitcoin_total_bytes_recv", "Total bytes received")
BITCOIN_TOTAL_BYTES_SENT = Gauge("bitcoin_total_bytes_sent", "Total bytes sent")

BITCOIN_LATEST_BLOCK_INPUTS = Gauge(
    "bitcoin_latest_block_inputs", "Number of inputs in transactions of latest block"
)
BITCOIN_LATEST_BLOCK_OUTPUTS = Gauge(
    "bitcoin_latest_block_outputs", "Number of outputs in transactions of latest block"
)
BITCOIN_LATEST_BLOCK_VALUE = Gauge(
    "bitcoin_latest_block_value", "Bitcoin value of all transactions in the latest block"
)

BITCOIN_BAN_CREATED = Gauge(
    "bitcoin_ban_created", "Time the ban was created", labelnames=["address", "reason"]
)
BITCOIN_BANNED_UNTIL = Gauge(
    "bitcoin_banned_until", "Time the ban expires", labelnames=["address", "reason"]
)

BITCOIN_SERVER_VERSION = Gauge("bitcoin_server_version", "The server version")
BITCOIN_PROTOCOL_VERSION = Gauge("bitcoin_protocol_version", "The protocol version of the server")

BITCOIN_SIZE_ON_DISK = Gauge("bitcoin_size_on_disk", "Estimated size of the block and undo files")

BITCOIN_VERIFICATION_PROGRESS = Gauge(
    "bitcoin_verification_progress", "Estimate of verification progress [0..1]"
)

EXPORTER_ERRORS = Counter(
    "bitcoin_exporter_errors", "Number of errors encountered by the exporter", labelnames=["type"]
)
PROCESS_TIME = Counter(
    "bitcoin_exporter_process_time", "Time spent processing metrics from bitcoin node"
)


BITCOIN_RPC_SCHEME = os.environ.get("BITCOIN_RPC_SCHEME", "http")
BITCOIN_RPC_HOST = os.environ.get("BITCOIN_RPC_HOST", "localhost")
BITCOIN_RPC_PORT = os.environ.get("BITCOIN_RPC_PORT", "8332")
BITCOIN_RPC_USER = os.environ.get("BITCOIN_RPC_USER")
BITCOIN_RPC_PASSWORD = os.environ.get("BITCOIN_RPC_PASSWORD")
SMART_FEES = [int(f) for f in os.environ.get("SMARTFEE_BLOCKS", "2,3,5,20").split(",")]
REFRESH_SECONDS = float(os.environ.get("REFRESH_SECONDS", "300"))
METRICS_PORT = int(os.environ.get("METRICS_PORT", "8334"))
RETRIES = int(os.environ.get("RETRIES", 5))
TIMEOUT = int(os.environ.get("TIMEOUT", 30))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")


RETRY_EXCEPTIONS = (
    InWarmupError,
    ConnectionError,
    socket.timeout
)

RpcResult = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


def on_retry(err: Exception, next_try: float) -> None:
    err_type = type(err)
    exception_name = err_type.__module__ + "." + err_type.__name__
    EXPORTER_ERRORS.labels(**{"type": exception_name}).inc()
    logger.error("Retry after exception %s: %s", exception_name, err)


def error_evaluator(e: Exception) -> bool:
    return isinstance(e, RETRY_EXCEPTIONS)

class MonitorProxy(Proxy):
        def __init__(self):
            if BITCOIN_RPC_PASSWORD:
                host = BITCOIN_RPC_HOST
                if BITCOIN_RPC_USER and BITCOIN_RPC_PASSWORD:
                    host = "%s:%s@%s" % (quote(BITCOIN_RPC_USER), quote(BITCOIN_RPC_PASSWORD), host,)
                if BITCOIN_RPC_PORT:
                    host = "%s:%s" % (host, BITCOIN_RPC_PORT)
                service_url = "%s://%s" % (BITCOIN_RPC_SCHEME, host)
                super(MonitorProxy, self).__init__(service_url=service_url, timeout=TIMEOUT)
            else:
                logger.info("Using config file")
                super(MonitorProxy, self).__init__(timeout=TIMEOUT)


@lru_cache(maxsize=1)
def rpc_client_factory():
    return lambda: MonitorProxy()

def rpc_client():
    return rpc_client_factory()()


@riprova.retry(
    timeout=TIMEOUT,
    backoff=riprova.ExponentialBackOff(),
    on_retry=on_retry,
    error_evaluator=error_evaluator,
)
def bitcoinrpc(*args) -> RpcResult:
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("RPC call: " + " ".join(str(a) for a in args))

    result = rpc_client().call(*args)

    logger.debug("Result:   %s", result)
    return result


def get_block(block_hash: str):
    try:
        block = bitcoinrpc("getblock", block_hash, 2)
    except Exception:
        logger.exception("Failed to retrieve block " + block_hash + " from bitcoind.")
        return None
    return block


def smartfee_gauge(num_blocks: int) -> Gauge:
    gauge = BITCOIN_ESTIMATED_SMART_FEE_GAUGES.get(num_blocks)
    if gauge is None:
        gauge = Gauge(
            "bitcoin_est_smart_fee_%d" % num_blocks,
            "Estimated smart fee per kilobyte for confirmation in %d blocks" % num_blocks,
        )
        BITCOIN_ESTIMATED_SMART_FEE_GAUGES[num_blocks] = gauge
    return gauge


def do_smartfee(num_blocks: int) -> None:
    smartfee = bitcoinrpc("estimatesmartfee", num_blocks).get("feerate")
    if smartfee is not None:
        gauge = smartfee_gauge(num_blocks)
        gauge.set(smartfee)


def refresh_metrics() -> None:
    uptime = int(bitcoinrpc("uptime"))
    meminfo = bitcoinrpc("getmemoryinfo", "stats")["locked"]
    blockchaininfo = bitcoinrpc("getblockchaininfo")
    networkinfo = bitcoinrpc("getnetworkinfo")
    chaintips = len(bitcoinrpc("getchaintips"))
    mempool = bitcoinrpc("getmempoolinfo")
    nettotals = bitcoinrpc("getnettotals")
    latest_block = get_block(str(blockchaininfo["bestblockhash"]))
    hashps_120 = float(bitcoinrpc("getnetworkhashps", 120))  # 120 is the default
    hashps_neg1 = float(bitcoinrpc("getnetworkhashps", -1))
    hashps_1 = float(bitcoinrpc("getnetworkhashps", 1))

    banned = bitcoinrpc("listbanned")

    BITCOIN_UPTIME.set(uptime)
    BITCOIN_BLOCKS.set(blockchaininfo["blocks"])
    BITCOIN_PEERS.set(networkinfo["connections"])
    BITCOIN_DIFFICULTY.set(blockchaininfo["difficulty"])
    BITCOIN_HASHPS.set(hashps_120)
    BITCOIN_HASHPS_NEG1.set(hashps_neg1)
    BITCOIN_HASHPS_1.set(hashps_1)
    BITCOIN_SERVER_VERSION.set(networkinfo["version"])
    BITCOIN_PROTOCOL_VERSION.set(networkinfo["protocolversion"])
    BITCOIN_SIZE_ON_DISK.set(blockchaininfo["size_on_disk"])
    BITCOIN_VERIFICATION_PROGRESS.set(blockchaininfo["verificationprogress"])

    for smartfee in SMART_FEES:
        do_smartfee(smartfee)

    for ban in banned:
        BITCOIN_BAN_CREATED.labels(address=ban["address"], reason=ban["ban_reason"]).set(
            ban["ban_created"]
        )
        BITCOIN_BANNED_UNTIL.labels(address=ban["address"], reason=ban["ban_reason"]).set(
            ban["banned_until"]
        )

    if networkinfo["warnings"]:
        BITCOIN_WARNINGS.inc()

    BITCOIN_NUM_CHAINTIPS.set(chaintips)

    BITCOIN_MEMINFO_USED.set(meminfo["used"])
    BITCOIN_MEMINFO_FREE.set(meminfo["free"])
    BITCOIN_MEMINFO_TOTAL.set(meminfo["total"])
    BITCOIN_MEMINFO_LOCKED.set(meminfo["locked"])
    BITCOIN_MEMINFO_CHUNKS_USED.set(meminfo["chunks_used"])
    BITCOIN_MEMINFO_CHUNKS_FREE.set(meminfo["chunks_free"])

    BITCOIN_MEMPOOL_BYTES.set(mempool["bytes"])
    BITCOIN_MEMPOOL_SIZE.set(mempool["size"])
    BITCOIN_MEMPOOL_USAGE.set(mempool["usage"])

    BITCOIN_TOTAL_BYTES_RECV.set(nettotals["totalbytesrecv"])
    BITCOIN_TOTAL_BYTES_SENT.set(nettotals["totalbytessent"])

    if latest_block is not None:
        BITCOIN_LATEST_BLOCK_SIZE.set(latest_block["size"])
        BITCOIN_LATEST_BLOCK_TXS.set(latest_block["nTx"])
        BITCOIN_LATEST_BLOCK_HEIGHT.set(latest_block["height"])
        BITCOIN_LATEST_BLOCK_WEIGHT.set(latest_block["weight"])
        inputs, outputs = 0, 0
        value = 0
        for tx in latest_block["tx"]:
            i = len(tx["vin"])
            inputs += i
            o = len(tx["vout"])
            outputs += o
            value += sum(o["value"] for o in tx["vout"])

        BITCOIN_LATEST_BLOCK_INPUTS.set(inputs)
        BITCOIN_LATEST_BLOCK_OUTPUTS.set(outputs)
        BITCOIN_LATEST_BLOCK_VALUE.set(value)


def sigterm_handler(signal, frame) -> None:
    logger.critical("Received SIGTERM. Exiting.")
    sys.exit(0)


def exception_count(e: Exception) -> None:
    err_type = type(e)
    exception_name = err_type.__module__ + "." + err_type.__name__
    EXPORTER_ERRORS.labels(**{"type": exception_name}).inc()


def main():
    # Set up logging to look similar to bitcoin logs (UTC).
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ"
    )
    logging.Formatter.converter = time.gmtime
    logger.setLevel(LOG_LEVEL)

    # Handle SIGTERM gracefully.
    signal.signal(signal.SIGTERM, sigterm_handler)

    # Start up the server to expose the metrics.
    start_http_server(METRICS_PORT)
    while True:
        process_start = datetime.now()

        # Allow riprova.MaxRetriesExceeded and unknown exceptions to crash the process.
        try:
            refresh_metrics()
        except riprova.exceptions.RetryError as e:
            logger.error("Refresh failed during retry. Cause: " + str(e))
            exception_count(e)
        except json.decoder.JSONDecodeError as e:
            logger.error("RPC call did not return JSON. Bad credentials? " + str(e))
            sys.exit(1)

        duration = datetime.now() - process_start
        PROCESS_TIME.inc(duration.total_seconds())
        logger.info("Refresh took %s seconds, sleeping for %s seconds", duration, REFRESH_SECONDS)

        time.sleep(REFRESH_SECONDS)


if __name__ == "__main__":
    main()
