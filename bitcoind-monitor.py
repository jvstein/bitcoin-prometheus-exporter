#!/usr/local/bin/python
# -*- coding: utf-8 -*-

import json
import time
import os
import signal
import subprocess
import sys

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

from bitcoin.rpc import Proxy
from prometheus_client import start_http_server, Gauge, Counter


# Create Prometheus metrics to track bitcoind stats.
BITCOIN_BLOCKS = Gauge('bitcoin_blocks', 'Block height')
BITCOIN_DIFFICULTY = Gauge('bitcoin_difficulty', 'Difficulty')
BITCOIN_PEERS = Gauge('bitcoin_peers', 'Number of peers')
BITCOIN_HASHPS_NEG1 = Gauge('bitcoin_hashps_neg1', 'Estimated network hash rate per second since the last difficulty change')
BITCOIN_HASHPS_1 = Gauge('bitcoin_hashps_1', 'Estimated network hash rate per second for the last block')
BITCOIN_HASHPS = Gauge('bitcoin_hashps', 'Estimated network hash rate per second for the last 120 blocks')

BITCOIN_ESTIMATED_SMART_FEE_2 = Gauge('bitcoin_est_smart_fee_2', 'Estimated smart fee per kilobyte for confirmation in 2 blocks')
BITCOIN_ESTIMATED_SMART_FEE_3 = Gauge('bitcoin_est_smart_fee_3', 'Estimated smart fee per kilobyte for confirmation in 3 blocks')
BITCOIN_ESTIMATED_SMART_FEE_5 = Gauge('bitcoin_est_smart_fee_5', 'Estimated smart fee per kilobyte for confirmation in 5 blocks')
BITCOIN_ESTIMATED_SMART_FEE_20 = Gauge('bitcoin_est_smart_fee_20', 'Estimated smart fee per kilobyte for confirmation in 20 blocks')

BITCOIN_WARNINGS = Counter('bitcoin_warnings', 'Number of network or blockchain warnings detected')
BITCOIN_UPTIME = Gauge('bitcoin_uptime', 'Number of seconds the Bitcoin daemon has been running')

BITCOIN_MEMINFO_USED = Gauge('bitcoin_meminfo_used', 'Number of bytes used')
BITCOIN_MEMINFO_FREE = Gauge('bitcoin_meminfo_free', 'Number of bytes available')
BITCOIN_MEMINFO_TOTAL = Gauge('bitcoin_meminfo_total', 'Number of bytes managed')
BITCOIN_MEMINFO_LOCKED = Gauge('bitcoin_meminfo_locked', 'Number of bytes locked')
BITCOIN_MEMINFO_CHUNKS_USED = Gauge('bitcoin_meminfo_chunks_used', 'Number of allocated chunks')
BITCOIN_MEMINFO_CHUNKS_FREE = Gauge('bitcoin_meminfo_chunks_free', 'Number of unused chunks')

BITCOIN_MEMPOOL_BYTES = Gauge('bitcoin_mempool_bytes', 'Size of mempool in bytes')
BITCOIN_MEMPOOL_SIZE = Gauge('bitcoin_mempool_size', 'Number of unconfirmed transactions in mempool')
BITCOIN_MEMPOOL_USAGE = Gauge('bitcoin_mempool_usage', 'Total memory usage for the mempool')

BITCOIN_LATEST_BLOCK_SIZE = Gauge('bitcoin_latest_block_size', 'Size of latest block in bytes')
BITCOIN_LATEST_BLOCK_TXS = Gauge('bitcoin_latest_block_txs', 'Number of transactions in latest block')

BITCOIN_NUM_CHAINTIPS = Gauge('bitcoin_num_chaintips', 'Number of known blockchain branches')

BITCOIN_TOTAL_BYTES_RECV = Gauge('bitcoin_total_bytes_recv', 'Total bytes received')
BITCOIN_TOTAL_BYTES_SENT = Gauge('bitcoin_total_bytes_sent', 'Total bytes sent')

BITCOIN_LATEST_BLOCK_INPUTS = Gauge('bitcoin_latest_block_inputs', 'Number of inputs in transactions of latest block')
BITCOIN_LATEST_BLOCK_OUTPUTS = Gauge('bitcoin_latest_block_outputs', 'Number of outputs in transactions of latest block')
BITCOIN_LATEST_BLOCK_VALUE = Gauge('bitcoin_latest_block_value', 'Bitcoin value of all transactions in the latest block')

BITCOIN_BAN_CREATED = Gauge('bitcoin_ban_created', 'Time the ban was created', labelnames=['address', 'reason'])
BITCOIN_BANNED_UNTIL = Gauge('bitcoin_banned_until', 'Time the ban expires', labelnames=['address', 'reason'])

BITCOIN_SERVER_VERSION = Gauge('bitcoin_server_version', 'The server version')
BITCOIN_PROTOCOL_VERSION = Gauge('bitcoin_protocol_version', 'The protocol version of the server')

BITCOIN_SIZE_ON_DISK = Gauge('bitcoin_size_on_disk', 'Estimated size of the block and undo files')


BITCOIN_RPC_SCHEME = os.environ.get('BITCOIN_RPC_SCHEME', 'http')
BITCOIN_RPC_HOST = os.environ.get('BITCOIN_RPC_HOST', 'localhost')
BITCOIN_RPC_PORT = os.environ.get('BITCOIN_RPC_PORT', '8332')
BITCOIN_RPC_USER = os.environ.get('BITCOIN_RPC_USER')
BITCOIN_RPC_PASSWORD = os.environ.get('BITCOIN_RPC_PASSWORD')
REFRESH_SECONDS = float(os.environ.get('REFRESH_SECONDS', '300'))
METRICS_PORT = int(os.environ.get('METRICS_PORT', '8334'))


def find_bitcoin_cli():
    if sys.version_info[0] < 3:
        from whichcraft import which
    if sys.version_info[0] >= 3:
        from shutil import which
    return which('bitcoin-cli')

BITCOIN_CLI_PATH = str(find_bitcoin_cli())


def bitcoinrpc(*args):
    host = BITCOIN_RPC_HOST
    if BITCOIN_RPC_USER and BITCOIN_RPC_PASSWORD:
        host = "%s:%s@%s" % (
            quote(BITCOIN_RPC_USER),
            quote(BITCOIN_RPC_PASSWORD),
            host,
        )
    if BITCOIN_RPC_PORT:
        host = "%s:%s" % (host, BITCOIN_RPC_PORT)
    service_url = "%s://%s" % (BITCOIN_RPC_SCHEME, host)
    proxy = Proxy(service_url=service_url)
    result = proxy.call(*args)
    return result


def get_block(block_hash):
    try:
        block = bitcoinrpc('getblock', block_hash, 2)
    except Exception as e:
        print(e)
        print('Error: Can\'t retrieve block ' + block_hash + ' from bitcoind.')
        return None
    return block


def sigterm_handler(signal, frame):
    print('Received SIGTERM. Exiting.')
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)

    # Start up the server to expose the metrics.
    start_http_server(METRICS_PORT)
    while True:
        uptime = int(bitcoinrpc('uptime'))
        meminfo = bitcoinrpc('getmemoryinfo', 'stats')['locked']
        blockchaininfo = bitcoinrpc('getblockchaininfo')
        networkinfo = bitcoinrpc('getnetworkinfo')
        chaintips = len(bitcoinrpc('getchaintips'))
        mempool = bitcoinrpc('getmempoolinfo')
        nettotals = bitcoinrpc('getnettotals')
        latest_block = get_block(str(blockchaininfo['bestblockhash']))
        hashps_120 = float(bitcoinrpc('getnetworkhashps', 120))  # 120 is the default
        hashps_neg1 = float(bitcoinrpc('getnetworkhashps', -1))
        hashps_1 = float(bitcoinrpc('getnetworkhashps', 1))
        smartfee_2 = bitcoinrpc('estimatesmartfee', 2)['feerate']
        smartfee_3 = bitcoinrpc('estimatesmartfee', 3)['feerate']
        smartfee_5 = bitcoinrpc('estimatesmartfee', 5)['feerate']
        smartfee_20 = bitcoinrpc('estimatesmartfee', 20)['feerate']
        banned = bitcoinrpc('listbanned')

        BITCOIN_UPTIME.set(uptime)
        BITCOIN_BLOCKS.set(blockchaininfo['blocks'])
        BITCOIN_PEERS.set(networkinfo['connections'])
        BITCOIN_DIFFICULTY.set(blockchaininfo['difficulty'])
        BITCOIN_HASHPS.set(hashps_120)
        BITCOIN_HASHPS_NEG1.set(hashps_neg1)
        BITCOIN_HASHPS_1.set(hashps_1)
        BITCOIN_ESTIMATED_SMART_FEE_2.set(smartfee_2)
        BITCOIN_ESTIMATED_SMART_FEE_3.set(smartfee_3)
        BITCOIN_ESTIMATED_SMART_FEE_5.set(smartfee_5)
        BITCOIN_ESTIMATED_SMART_FEE_20.set(smartfee_20)
        BITCOIN_SERVER_VERSION.set(networkinfo['version'])
        BITCOIN_PROTOCOL_VERSION.set(networkinfo['protocolversion'])
        BITCOIN_SIZE_ON_DISK.set(blockchaininfo['size_on_disk'])

        for ban in banned:
            BITCOIN_BAN_CREATED.labels(address=ban['address'], reason=ban['ban_reason']).set(ban['ban_created'])
            BITCOIN_BANNED_UNTIL.labels(address=ban['address'], reason=ban['ban_reason']).set(ban['banned_until'])

        if networkinfo['warnings']:
            BITCOIN_WARNINGS.inc()

        BITCOIN_NUM_CHAINTIPS.set(chaintips)

        BITCOIN_MEMINFO_USED.set(meminfo['used'])
        BITCOIN_MEMINFO_FREE.set(meminfo['free'])
        BITCOIN_MEMINFO_TOTAL.set(meminfo['total'])
        BITCOIN_MEMINFO_LOCKED.set(meminfo['locked'])
        BITCOIN_MEMINFO_CHUNKS_USED.set(meminfo['chunks_used'])
        BITCOIN_MEMINFO_CHUNKS_FREE.set(meminfo['chunks_free'])

        BITCOIN_MEMPOOL_BYTES.set(mempool['bytes'])
        BITCOIN_MEMPOOL_SIZE.set(mempool['size'])
        BITCOIN_MEMPOOL_USAGE.set(mempool['usage'])

        BITCOIN_TOTAL_BYTES_RECV.set(nettotals['totalbytesrecv'])
        BITCOIN_TOTAL_BYTES_SENT.set(nettotals['totalbytessent'])

        if latest_block is not None:
            BITCOIN_LATEST_BLOCK_SIZE.set(latest_block['size'])
            BITCOIN_LATEST_BLOCK_TXS.set(len(latest_block['tx']))
            inputs, outputs = 0, 0
            value = 0
            for tx in latest_block['tx']:
                i = len(tx['vin'])
                inputs += i
                o = len(tx['vout'])
                outputs += o
                value += sum(o["value"] for o in tx['vout'])

            BITCOIN_LATEST_BLOCK_INPUTS.set(inputs)
            BITCOIN_LATEST_BLOCK_OUTPUTS.set(outputs)
            BITCOIN_LATEST_BLOCK_VALUE.set(value)

        time.sleep(REFRESH_SECONDS)

if __name__ == '__main__':
    main()
