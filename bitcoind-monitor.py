#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import time
import subprocess
import sys
from prometheus_client import start_http_server, Gauge, Counter

# Create Prometheus metrics to track bitcoind stats.
BITCOIN_BLOCKS = Gauge('bitcoin_blocks', 'Block height')
BITCOIN_DIFFICULTY = Gauge('bitcoin_difficulty', 'Difficulty')
BITCOIN_PEERS = Gauge('bitcoin_peers', 'Number of peers')
BITCOIN_HASHPS = Gauge('bitcoin_hashps', 'Estimated network hash rate per second')

BITCOIN_ERRORS = Counter('bitcoin_errors', 'Number of errors detected')
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
    bitcoin = subprocess.Popen([BITCOIN_CLI_PATH, cmd], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    output = bitcoin.communicate()[0]
    return json.loads(output.decode('utf-8'))


def bitcoincli(cmd):
    bitcoin = subprocess.Popen([BITCOIN_CLI_PATH, cmd], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    output = bitcoin.communicate()[0]
    return output.decode('utf-8')


def get_block(block_height):
    try:
        block = subprocess.check_output([BITCOIN_CLI_PATH, 'getblock', block_height])
    except Exception as e:
        print(e)
        print('Error: Can\'t retrieve block number ' + block_height + ' from bitcoind.')
        return None
    return json.loads(block.decode('utf-8'))


def get_raw_tx(txid):
    try:
        rawtx = subprocess.check_output([BITCOIN_CLI_PATH, 'getrawtransaction', txid, '1'])
    except Exception as e:
        print(e)
        print('Error: Can\'t retrieve raw transaction ' + txid + ' from bitcoind.')
        return None
    return json.loads(rawtx.decode('utf-8'))


def main():
    # Start up the server to expose the metrics.
    start_http_server(8334)
    while True:
        info = bitcoin('getinfo')
        chaintips = len(bitcoin('getchaintips'))
        mempool = bitcoin('getmempoolinfo')
        nettotals = bitcoin('getnettotals')
        latest_block = get_block(str(info['blocks']))
        hashps = float(bitcoincli('getnetworkhashps'))

        BITCOIN_BLOCKS.set(info['blocks'])
        BITCOIN_PEERS.set(info['connections'])
        BITCOIN_DIFFICULTY.set(info['difficulty'])
        BITCOIN_HASHPS.set(hashps)

        if info['errors']:
            BITCOIN_ERRORS.inc()

        BITCOIN_NUM_CHAINTIPS.set(chaintips)

        BITCOIN_MEMPOOL_BYTES.set(mempool['bytes'])
        BITCOIN_MEMPOOL_SIZE.set(mempool['size'])

        BITCOIN_TOTAL_BYTES_RECV.set(nettotals['totalbytesrecv'])
        BITCOIN_TOTAL_BYTES_SENT.set(nettotals['totalbytessent'])

        if latest_block is not None:
            BITCOIN_LATEST_BLOCK_SIZE.set(latest_block['size'])
            BITCOIN_LATEST_BLOCK_TXS.set(len(latest_block['tx']))
            inputs, outputs = 0, 0
            # counting transaction inputs and outputs requires txindex=1
            # to be enabled, which may also necessitate reindex=1 in bitcoin.conf
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