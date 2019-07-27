#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import time
import subprocess
import sys
from prometheus_client import start_http_server, Gauge, Counter

# INSTALLATION
#   apt install -y python-pip python-setuptools
#   pip install wheel 
#   pip install prometheus_client

# CONFIG
#   counting transaction inputs and outputs requires that bitcoind is configured with txindex=1, which may also necessitate reindex=1 in bitcoin.conf
#   set True or False, according to your bicoind configuration
txindex_enabled = False

#   when using a non-standard path for bitcoin.conf, set it here as cli argument (e.g. "-conf=/btc/bitcoin.conf") or leave empty
bitcoind_conf = "-conf=/etc/bitcoin/bitcoin.conf"


# Create Prometheus metrics to track bitcoind stats.
BITCOIN_BLOCKS = Gauge('bitcoin_blocks', 'Block height')
BITCOIN_DIFFICULTY = Gauge('bitcoin_difficulty', 'Difficulty')
BITCOIN_PEERS = Gauge('bitcoin_peers', 'Number of peers')
BITCOIN_HASHPS = Gauge('bitcoin_hashps', 'Estimated network hash rate per second')

BITCOIN_WARNINGS = Counter('bitcoin_warnings', 'Number of warnings detected')
BITCOIN_UPTIME = Gauge('bitcoin_uptime', 'Number of seconds the Bitcoin daemon has been running')

BITCOIN_MEMPOOL_BYTES = Gauge('bitcoin_mempool_bytes', 'Size of mempool in bytes')
BITCOIN_MEMPOOL_SIZE = Gauge('bitcoin_mempool_size', 'Number of unconfirmed transactions in mempool')

BITCOIN_LATEST_BLOCK_SIZE = Gauge('bitcoin_latest_block_size', 'Size of latest block in bytes')
BITCOIN_LATEST_BLOCK_TXS = Gauge('bitcoin_latest_block_txs', 'Number of transactions in latest block')

BITCOIN_NUM_CHAINTIPS = Gauge('bitcoin_num_chaintips', 'Number of known blockchain branches')

BITCOIN_TOTAL_BYTES_RECV = Gauge('bitcoin_total_bytes_recv', 'Total bytes received')
BITCOIN_TOTAL_BYTES_SENT = Gauge('bitcoin_total_bytes_sent', 'Total bytes sent')

BITCOIN_LATEST_BLOCK_INPUTS = Gauge('bitcoin_latest_block_inputs', 'Number of inputs in transactions of latest block')
BITCOIN_LATEST_BLOCK_OUTPUTS = Gauge('bitcoin_latest_block_outputs', 'Number of outputs in transactions of latest block')

def find_bitcoin_cli():
    if sys.version_info[0] < 3:
        from whichcraft import which
    if sys.version_info[0] >= 3:
        from shutil import which
    return which('bitcoin-cli')

BITCOIN_CLI_PATH = str(find_bitcoin_cli())

def bitcoin(cmd):
    args = [cmd]
    if len(bitcoind_conf) > 0:
      args = [bitcoind_conf] + args
    bitcoin = subprocess.Popen([BITCOIN_CLI_PATH] + args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    output = bitcoin.communicate()[0]
    return json.loads(output.decode('utf-8'))


def bitcoincli(cmd):
    args = [cmd]
    if len(bitcoind_conf) > 0:
      args = [bitcoind_conf] + args
    bitcoin = subprocess.Popen([BITCOIN_CLI_PATH] + args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    output = bitcoin.communicate()[0]
    return output.decode('utf-8')


def get_block(block_height):
    args = ["getblock", block_height]
    if len(bitcoind_conf) > 0:
      args = [bitcoind_conf] + args

    try:
        block = subprocess.check_output([BITCOIN_CLI_PATH] + args)
    except Exception as e:
        print(e)
        print('Error: Can\'t retrieve block number ' + block_height + ' from bitcoind.')
        return None
    return json.loads(block.decode('utf-8'))


def get_raw_tx(txid):
    args = ["getrawtransaction", txid, '1']
    if len(bitcoind_conf) > 0:
      args = [bitcoind_conf] + args

    try:
        rawtx = subprocess.check_output([BITCOIN_CLI_PATH])
    except Exception as e:
        print(e)
        print('Error: Can\'t retrieve raw transaction ' + txid + ' from bitcoind.')
        return None
    return json.loads(rawtx.decode('utf-8'))


def main():
    # Start up the server to expose the metrics.
    start_http_server(8334)
    while True:
        blockchaininfo = bitcoin('getblockchaininfo')
        networkinfo = bitcoin('getnetworkinfo')
        chaintips = len(bitcoin('getchaintips'))
        mempool = bitcoin('getmempoolinfo')
        nettotals = bitcoin('getnettotals')
        latest_block = get_block(str(blockchaininfo['bestblockhash']))
        hashps = float(bitcoincli('getnetworkhashps'))

        BITCOIN_BLOCKS.set(blockchaininfo['blocks'])
        BITCOIN_PEERS.set(networkinfo['connections'])
        BITCOIN_DIFFICULTY.set(blockchaininfo['difficulty'])
        BITCOIN_HASHPS.set(hashps)

        if networkinfo['warnings']:
            BITCOIN_WARNINGS.inc()

        BITCOIN_NUM_CHAINTIPS.set(chaintips)

        BITCOIN_MEMPOOL_BYTES.set(mempool['bytes'])
        BITCOIN_MEMPOOL_SIZE.set(mempool['size'])

        BITCOIN_TOTAL_BYTES_RECV.set(nettotals['totalbytesrecv'])
        BITCOIN_TOTAL_BYTES_SENT.set(nettotals['totalbytessent'])

        if latest_block is not None:
            BITCOIN_LATEST_BLOCK_SIZE.set(latest_block['size'])
            BITCOIN_LATEST_BLOCK_TXS.set(len(latest_block['tx']))
            inputs, outputs = 0, 0

            if txindex_enabled:
              for tx in latest_block['tx']:

                if get_raw_tx(tx) is not None:
                    rawtx = get_raw_tx(tx)
                    i = len(rawtx['vin'])
                    inputs += i
                    o = len(rawtx['vout'])
                    outputs += o

            BITCOIN_LATEST_BLOCK_INPUTS.set(inputs)
            BITCOIN_LATEST_BLOCK_OUTPUTS.set(outputs)

        time.sleep(300)

if __name__ == '__main__':
    main()