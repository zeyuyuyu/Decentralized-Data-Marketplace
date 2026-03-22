import os
import json
import time
import hashlib
from web3 import Web3

# Connect to Ethereum node
w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID'))

# Define contract ABI and address
contract_abi = json.load(open('contract_abi.json'))
contract_address = '0x1234567890123456789012345678901234567890'

# Create contract instance
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Define data exchange function
def exchange_data(seller_address, buyer_address, data_hash, price):
    # Check if buyer has enough Ether
    if w3.eth.get_balance(buyer_address) < price:
        return {'success': False, 'message': 'Insufficient funds'}

    # Transfer Ether from buyer to seller
    tx = {
        'to': seller_address,
        'value': price,
        'gas': 21000,
        'gasPrice': w3.toWei('10', 'gwei'),
        'nonce': w3.eth.getTransactionCount(buyer_address)
    }
    signed_tx = w3.eth.account.signTransaction(tx, private_key=os.environ['BUYER_PRIVATE_KEY'])
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)

    # Add data hash to contract
    contract.functions.addDataHash(data_hash).transact({'from': seller_address})

    return {'success': True, 'message': 'Data exchange successful'}

# Example usage
seller_address = '0x0123456789012345678901234567890123456789'
buyer_address = '0x9876543210987654321098765432109876543210'
data_hash = hashlib.sha256(b'sample data').hexdigest()
price = w3.toWei(1, 'ether')

result = exchange_data(seller_address, buyer_address, data_hash, price)
print(result)