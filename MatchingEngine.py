from collections import defaultdict
import uuid
import time
import heapq
import datetime
import  json


class Order:
    def __init__(self, instrument, order_id, side, price, quantity, timestamp):
        self.instrument = instrument
        self.order_id = order_id
        self.side = side
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp
        self.filled_quantity = 0

    # price/time priority
    def __lt__(self, other):
        if self.side == 'buy':
            return (self.price, -self.timestamp) > (other.price, -other.timestamp)  # to get most recent buy order
        else:
            return (self.price, self.timestamp) < (other.price, other.timestamp)


class OrderBook:
    def __init__(self):
        self.bids = []
        self.asks = []

    def add(self, order):
        if order.side == 'buy':
            heapq.heappush(self.bids, (-order.price, order.timestamp, order))
        elif order.side == 'sell':
            heapq.heappush(self.asks, (order.price, order.timestamp, order))

    def remove(self, order):
        if order.side == 'buy':
            self.bids.remove((-order.price, order.timestamp, order))
            heapq.heapify(self.bids)
        else:
            self.asks.remove((order.price, order.timestamp, order))
            heapq.heapify(self.asks)

    def bestBid(self):
        return self.bids[0][2] if self.bids else None

    def bestAsk(self):
        return self.asks[0][2] if self.asks else None

    def showBestBidAndAsk(self):
        best_bid = self.bestBid()
        best_ask = self.bestAsk()

        if (best_bid is not None and best_bid.quantity > 0):
            print(
                f"Best Bid: Instrument: {best_bid.instrument}, Price: {best_bid.price}, Quantity: {best_bid.quantity}")
            print(
                "----------------------------------------------------------------------------------------------------")
        else:
            print("No best bid available.")
            print(
                "----------------------------------------------------------------------------------------------------")

        if (best_ask is not None and best_ask.quantity > 0):
            print(
                f"Best Ask: Instrument: {best_ask.instrument}, Price: {best_ask.price}, Quantity: {best_ask.quantity}")
            print(
                "----------------------------------------------------------------------------------------------------")
        else:
            print("No best ask available.")
            print(
                "----------------------------------------------------------------------------------------------------")


class Trade:
    def __init__(self, id, name, price, volume):
        self.id = id
        self.name = name
        self.price = price
        self.volume = volume


class MatchedOrder:
    def __init__(self, order_id, side, price, filled_quantity, instrument, timestamp):
        self.order_id = order_id
        self.side = side
        self.price = price
        self.filled_quantity = filled_quantity
        self.instrument = instrument
        self.timestamp = timestamp


class MatchingEngine:
    def __init__(self):
        self.orderbooks = defaultdict(OrderBook)
        self.trades = defaultdict(list)
        self.buyerAckQueue = []
        self.sellerAckQueue = []
        self.orders = {}

    def placeOrder(self, instrument, side, price, quantity):
        order = Order(instrument, uuid.uuid1(), side, price, quantity, timestamp=int(time.time()))
        self.processOrder(order)
        self.orders[order.order_id] = order
        return order.order_id

    # Change the code to show order instrument,quantity,timestamp
    def getOrderBook(self, instrument):
        orderbook = self.orderbooks[instrument]
        # orderbook.showBestBidAndAsk()
        return orderbook.bids, orderbook.asks

    def showBestBidAsk(self, instrument):
        orderbook = self.orderbooks[instrument]
        orderbook.showBestBidAndAsk()

    def getTrades(self, instrument):
        return self.trades[instrument]

    def showTrades(self, instrument):
        trade_obj = self.getTrades(instrument)
        for i in trade_obj:
            trade_details = {
                "message": f"Trades made for {i.name}",
                "order_id": f"Order id {i.id}",
                "price": f"{i.price}",
                "quantity traded": f"{i.volume}"
            }

            # Convert the dictionary to a JSON-formatted string
            json_data_trade = json.dumps(trade_details, indent=2, default=self.uuid_serializer)

            # Print the JSON-formatted string
            print(json_data_trade)

    def processOrder(self, order):
        orderbook = self.orderbooks[order.instrument]

        timestamp = datetime.datetime.fromtimestamp(order.timestamp)

        if (order.side == 'buy'):
            print(f"{timestamp} : Buy order {order.order_id, order.instrument, order.price, order.quantity} is added to orderbook")


        else:
            print(f"{timestamp} : Sale order {order.order_id, order.instrument, order.price, order.quantity} is added to orderbook")

        if (order.side == 'buy' and orderbook.bestAsk() is not None and order.price >= orderbook.bestAsk().price):
            # Buy order crossed the spread
            self.matchBuyOrder(order, orderbook)
            # print(f"Buy order {order.order_id,order.instrument,order.price,order.quantity} matched with buy order {orderbook.bestAsk().order_id,orderbook.Ask().price,orderbook.bestAsk().quantity}")
            # print("----------------------------------------------------------------------------------------------------")


        elif (order.side == 'sell' and orderbook.bestBid() is not None and order.price <= orderbook.bestBid().price):
            # Sell order crossed the spread.
            qty = order.quantity
            self.matchSellOrder(order, orderbook)
            # print(f"Sale order {order.order_id,order.instrument,order.price,qty} matched with buy order {orderbook.bestBid().order_id,orderbook.bestBid().price,orderbook.bestBid().quantity}")
            # print("----------------------------------------------------------------------------------------------------")
        else:
            # Order did not cross the spread, place in order book
            orderbook.add(order)

    def uuid_serializer(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

    def acknowledgeOrder(self, matchedOrder):
        timeACk = datetime.datetime.fromtimestamp(matchedOrder.timestamp)

        # Store the order details in a dictionary with the "message" key first
        order_details = {
            "message": f"Order acknowledgement for {'buy' if matchedOrder.side == 'buy' else 'sell'} order {matchedOrder.order_id, matchedOrder.instrument}",
            "order_id": matchedOrder.order_id,
            "instrument": matchedOrder.instrument,
            "price": matchedOrder.price,
            "filled_quantity": matchedOrder.filled_quantity,
            "timestamp": timeACk.isoformat(),
            "action": "Bought" if matchedOrder.side == "buy" else "Sold",
        }

        # Convert the dictionary to a JSON-formatted string
        json_data = json.dumps(order_details, indent=2, default=self.uuid_serializer)

        # Print the JSON-formatted string
        print(json_data)
        print("----------------------------------------------------------------------------------------------------")

        if matchedOrder.side == "buy":
            self.buyerAckQueue.append(matchedOrder)
        else:
            self.sellerAckQueue.append(matchedOrder)

    def cancelOrder(self, order_id):
        if order_id in self.orders:
            order = self.orders[order_id]
            if (order.quantity == 0):
                print(f"Cannot cancel order {order_id}, already fully filled")
                return True
            elif order.filled_quantity < order.quantity:
                filled_qty = order.filled_quantity
                remaining_quantity = order.quantity
                order.quantity -= order.filled_quantity
                orderbook = self.orderbooks[order.instrument]
                orderbook.remove(order)
                del self.orders[order_id]

                print(
                    f"Order ID: {order_id} is cancelled. Filled quantity: {filled_qty}, Remaining quantity: {remaining_quantity}")


            else:
                orderbook = self.orderbooks[order.instrument]
                orderbook.remove(order)
                del self.orders[order_id]
                print(f"Order ID: {order_id} is cancelled")
        else:
            print("There is no such order")

    def match(self, order):
        orderbook = self.orderbooks[order.instrument]

        if (order.side == 'buy' and orderbook.bestAsk() is not None and order.price >= orderbook.bestAsk().price):
            # Buy order crossed the spread.
            self.matchBuyOrder(order, orderbook)
        elif (order.side == 'sell' and orderbook.bestBid() is not None and order.price <= orderbook.bestBid().price):
            # Sell order crossed the spread.
            self.matchSellOrder(order, orderbook)
        # else:
        #     # # Order did not cross the spread, place in order book
        #     orderbook.add(order)

    def matchBuyOrder(self, order, orderbook):

        # if sell price is less than buy price
        if (orderbook.bestAsk().price < order.price):
            new_price = orderbook.bestAsk().price

        while orderbook.asks and order.price >= orderbook.bestAsk().price and order.quantity > 0:
            ask = orderbook.bestAsk()
            buyMatchedOrder = []

            if ask.quantity <= order.quantity:  # quantity for sale is less than quantity for buy

                order.quantity -= ask.quantity
                order.filled_quantity += ask.quantity
                trade = Trade(order.order_id, order.instrument, ask.price, order.filled_quantity)
                self.trades[order.instrument].append(trade)

                buyMatchedOrder.append(
                    MatchedOrder(ask.order_id, 'sell', ask.price, ask.quantity, ask.instrument, ask.timestamp))

                if new_price:
                    buyMatchedOrder.append(
                        MatchedOrder(order.order_id, 'buy', new_price, order.filled_quantity, order.instrument,
                                     order.timestamp))

                else:
                    buyMatchedOrder.append(
                        MatchedOrder(order.order_id, 'buy', order.price, order.filled_quantity, order.instrument,
                                     order.timestamp))

                self.acknowledgeOrder(buyMatchedOrder[0])
                self.acknowledgeOrder(buyMatchedOrder[1])

                orderbook.remove(ask)
                # Acknowledgements



            else:  # quantity for sale is more than quantity for buy

                ask.quantity -= order.quantity
                order.filled_quantity += order.quantity
                ask.filled_quantity += order.filled_quantity

                trade = Trade(order.order_id, order.instrument, ask.price, order.filled_quantity)
                self.trades[order.instrument].append(trade)
                buyMatchedOrder.append(
                    MatchedOrder(ask.order_id, 'sell', ask.price, ask.filled_quantity, ask.instrument, ask.timestamp))

                if new_price:
                    buyMatchedOrder.append(
                        MatchedOrder(order.order_id, 'buy', new_price, order.quantity, order.instrument,
                                     order.timestamp))

                else:
                    buyMatchedOrder.append(
                        MatchedOrder(order.order_id, 'buy', order.price, order.filled_quantity, order.instrument,
                                     order.timestamp))

                self.acknowledgeOrder(buyMatchedOrder[0])
                self.acknowledgeOrder(buyMatchedOrder[1])

                order.quantity = 0

            # if buy order not fully filled add remaining back to orderbook
            if order.quantity > 0:
                orderbook.add(order)

    def matchSellOrder(self, order, orderbook):

        ### check to see if sale price less than buy price. if it is update buy price
        if (order.price <= orderbook.bestBid().price):
            new_buy_price = order.price

        while orderbook.bids and order.price >= new_buy_price and order.quantity > 0:
            bid = orderbook.bestBid()

            sellMatchedOrder = []

            if bid.quantity <= order.quantity:  # quantity for buy is less than quantity for sale
                order.quantity -= bid.quantity
                order.filled_quantity += bid.quantity
                bid.quantity = 0

                trade = Trade(order.order_id, order.instrument, new_buy_price, order.filled_quantity)
                self.trades[order.instrument].append(trade)
                # self.acknowledgeOrder(MatchedOrder(bid.order_id, 'buy', bid.price, bid.quantity, order.instrument, bid.timestamp))
                sellMatchedOrder.append(
                    MatchedOrder(bid.order_id, 'buy', new_buy_price, order.filled_quantity, bid.instrument,
                                 bid.timestamp))
                sellMatchedOrder.append(
                    MatchedOrder(order.order_id, 'sell', order.price, order.filled_quantity, order.instrument,
                                 order.timestamp))

                self.acknowledgeOrder(sellMatchedOrder[0])
                self.acknowledgeOrder(sellMatchedOrder[1])
                orderbook.remove(bid)
            else:  # quantity for buy is more than quantity for sale

                sellMatchedOrder.append(
                    MatchedOrder(order.order_id, 'sell', new_buy_price, order.quantity, order.instrument,
                                 order.timestamp))

                trade = Trade(order.order_id, order.instrument, new_buy_price, order.quantity)
                self.trades[order.instrument].append(trade)
                bid.quantity -= order.quantity
                # self.acknowledgeOrder(MatchedOrder(bid.order_id, 'buy', bid.price, order.quantity, order.instrument, bid.timestamp))
                order.filled_quantity += order.quantity
                order.quantity = 0
                sellMatchedOrder.append(
                    MatchedOrder(bid.order_id, 'buy', new_buy_price, order.filled_quantity, bid.instrument,
                                 bid.timestamp))

                self.acknowledgeOrder(sellMatchedOrder[0])
                self.acknowledgeOrder(sellMatchedOrder[1])

        # If the sell order is not fully filled, add the remaining part to the order book
        if order.quantity > 0:
            orderbook.add(order)