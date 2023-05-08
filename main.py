import swaps
import uniswap
import sushiswap
import time
from web3 import Web3
import web3
import json
from web3.contract import Contract
from decimal import Decimal


pairs = []
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR-PROJECT-ID'))
account_1 = 'INPUTACCOUNT1'
private_key1 = 'INPUTPRIVATEKEY'
account_2 = '0xf8e81D47203A594245E36C48e151709F0C19fBe8'
with open('bot.json', 'r') as f:
    contract_abi = json.load(f)

contract = Contract.from_abi('Arbitrageur', account_2, contract_abi)


def fillIds():
    sushiswap.fillIds(pairs)

def sendSwap(swap):
    Chain_id = web3.eth.chain_id
    nonce = w3.eth.getTransactionCount(account_1)
    struct_data = {
        'token0': uniswap.pairs_id[swap[2]][1],
        'token1': uniswap.pairs_id[swap[2]][0],
        'stoken0': sushiswap.pairs_id[swap[2]][1],
        'stoken1': sushiswap.pairs_id[swap[2]][0],
        'fee1': Decimal(0.003) * swap[0],
        'amount0': 0,
        'amount1': swap[0],
        'fee2': Decimal(0.003) * swap[0],
        'fee3': Decimal(0.003) * swap[0],
    }

    call_function = contract.functions.initFlash(struct_data).buildTransaction({"chainId": Chain_id, "from": account_1, "nonce": nonce})

    signed_tx = web3.eth.account.sign_transaction(call_function, private_key=private_key1)
    send_tx = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(send_tx)
    print(tx_receipt)



def updatePairsInfo():
    uniswap.updatePairsInfo(pairs)
    sushiswap.updatePairsInfo(pairs)

def updatePrices():
    uniswap.updatePrices(pairs)
    sushiswap.updatePrices(pairs)

def initPhase():
    init_start = time.perf_counter()

    # Get the most liquid pairs
    uniswap.fillPairs(pairs)

    # Fill the ids for the pairs
    fillIds()

    init_end = time.perf_counter()
    elapsed_time = init_end - init_start


    print(f"Intialization Phase: {elapsed_time: .2f} seconds")


def updatePhase():
    update_start = time.perf_counter()
    
    # Get the information for these pairs
    updatePairsInfo()

    # Update the prices
    updatePrices()
    
    # Get the token prices in USD
    uniswap.fillTokenValues(pairs)

    update_end = time.perf_counter()
    elapsed_time = update_end - update_start
    print(f"Update Phase: {elapsed_time: .2f} seconds")

def detectPhase():
    detect_start = time.perf_counter()
    
    orders = swaps.getSwaps(pairs)
    #if len(orders) != 0: sendSwap(orders[0])
    
    detect_end = time.perf_counter()
    elapsed_time = detect_end - detect_start
    print(f"Detect Phase: {elapsed_time: .2f} seconds")

if __name__ == "__main__":
    initPhase()

    for i in range(0,5):
        updatePhase()
        detectPhase()
        # Pause between the updates
        #time.sleep(20)
    
