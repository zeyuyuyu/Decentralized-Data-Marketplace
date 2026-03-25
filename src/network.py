import blockchain
import data_exchange

class DataMarketplace:
    def __init__(self):
        self.blockchain = blockchain.Blockchain()
        self.data_exchange = data_exchange.DataExchange()

    def buy_data(self, buyer, seller, data_id, price):
        # Verify buyer has enough funds
        if buyer.balance < price:
            return False

        # Execute data purchase transaction on blockchain
        transaction = self.blockchain.create_transaction(buyer, seller, data_id, price)
        self.blockchain.add_transaction(transaction)

        # Transfer data from seller to buyer
        self.data_exchange.transfer_data(seller, buyer, data_id)

        # Update balances
        buyer.balance -= price
        seller.balance += price

        return True

    def sell_data(self, seller, data_id, price):
        # Add data to data exchange
        self.data_exchange.add_data(seller, data_id, price)

        # Create listing on blockchain
        listing = self.blockchain.create_data_listing(seller, data_id, price)
        self.blockchain.add_listing(listing)

        return True
