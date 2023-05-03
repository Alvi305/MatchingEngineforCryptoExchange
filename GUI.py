import MatchingEngine as engine
import uuid

def get_id(id):
    uuid_string = id
    uuid_object = uuid.UUID(uuid_string)
    return uuid_object

def user_interface():
    eng = engine.MatchingEngine()

    while True:
        print("\nOptions:")
        print("1. Place Order")
        print("2. Retrieve Order Book")
        print("3. Show Executed Trades")
        print("4. Cancel Order")
        print("5. Exit")
        choice = input("\nEnter option number: ")

        if choice == '1':
            instrument = input("Enter instrument name: ").upper()
            side = input("Enter 'buy' or 'sell': ").lower()

            while True:
                quantity = float(input("Enter quantity: "))
                if quantity >= 0:
                    break
                else:
                    print("Error: Quantity must be non-negative. Please enter a valid value.")

            while True:
                price = float(input("Enter price: "))
                if price >= 0:
                    break
                else:
                    print("Error: Price must be non-negative. Please enter a valid value.")

            order_id = eng.placeOrder(instrument, side, price, quantity)


        elif choice == '2':
            instrument = input("Enter instrument name: ").upper()
            bids, asks = eng.getOrderBook(instrument)
            print(f"Order Book for {instrument}:")
            print("Bids:", bids)
            print("Asks:", asks)

        elif choice == '3':
            instrument = input("Enter instrument name: ").upper()
            show_trades(eng, instrument)

        elif choice == '4':
            order_id = input("Enter order ID to cancel: ")

            eng.cancelOrder(get_id(order_id))


        elif choice == '5':
            print("Exiting...")
            break

        else:
            print("Invalid option, please try again")


def show_trades(eng, inst):
    trades = eng.getTrades(inst)

    if len(trades) == 0:
        print(f"No trades were made for {inst}")
        print("No acknowledgments")
        return

    eng.showTrades(inst)

    print("Order acknowledgment for buyer and seller")

    if trades == 0:
        print("No acknowledgements due to no trades")

    for i in trades:
        if eng.buyerAckQueue:
            buy_ack = eng.buyerAckQueue.pop()
            print("Buy filled:", buy_ack.order_id, buy_ack.side, buy_ack.instrument, buy_ack.price, buy_ack.filled_quantity)
        else:
            print("No buy acknowledgements")

        if eng.sellerAckQueue:
            sell_ack = eng.sellerAckQueue.pop()
            print("Sale filled:", sell_ack.order_id, sell_ack.side, sell_ack.price, sell_ack.filled_quantity)
        else:
            print("No sell acknowledgements")


if __name__ == "__main__":
    user_interface()