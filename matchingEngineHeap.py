from collections import defaultdict
import uuid
import time
import heapq

class Order:
    def __init__(self,instrument,order_id,side,price,quantity,timestamp):
        self.instrument = instrument
        self.order_id = order_id
        self.side = side
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp
        self.filled_quantity = 0
        
    # price/time priority
    def __lt__(self,other):
        if self.side == 'buy':
            return (self.price, -self.timestamp) > (other.price,-other.timestamp) # to get most recent buy order
        else:
            return (self.price,self.timestamp) < (other.price, other.timestamp)

            
class OrderBook:
    def __init__(self):
        self.bids = []
        self.asks = []
        
    def add(self,order):
        if order.side =='buy':
            heapq.heappush(self.bids,(-order.price,order.timestamp,order))
        elif order.side == 'sell':
            heapq.heappush(self.asks,(order.price,order.timestamp,order))
            
            
    def remove(self, order):
        if order.side == 'buy':
            self.bids.remove((-order.price,order.timestamp,order))
            heapq.heapify(self.bids)
        else:
            self.asks.remove((order.price,order.timestamp,order))
            heapq.heapify(self.asks)
            
    def bestBid(self):
        return self.bids[0][2] if self.bids else None

    def bestAsk(self):
        return self.asks[0][2] if self.asks else None
    
    
class Trade:
    def __init__(self,price,volume):
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
        
    def placeOrder(self,instrument,side,price,quantity):
        order = Order(instrument,uuid.uuid1(),side,price,quantity,timestamp=int(time.time()))
        self.processOrder(order)
        self.orders[order.order_id] = order
        return order.order_id
    
    def getOrderBook(self,instrument):
        orderbook = self.orderbooks[instrument]
        return orderbook.bids,orderbook.asks
    
    def getTrades(self,instrument):
        return self.trades[instrument]
    
    def processOrder(self,order):
            orderbook = self.orderbooks[order.instrument]
        
            if (order.side == 'buy' and orderbook.bestAsk() is not None and order.price >= orderbook.bestAsk().price):
        # Buy order crossed the spread.
                self.matchBuyOrder(order, orderbook)
            elif (order.side == 'sell' and orderbook.bestBid() is not None and order.price <= orderbook.bestBid().price):
        # Sell order crossed the spread.
                self.matchSellOrder(order, orderbook)
            else:
                # Order did not cross the spread, place in order book
                orderbook.add(order)
        
    def acknowledgeOrder(self, matchedOrder):
        # Print the order details
        print(f"Order ID: {matchedOrder.order_id}")
        print(f"Instrument: {matchedOrder.instrument}")
        print(f"Price: {matchedOrder.price}")
        print(f"Quantity: {matchedOrder.filled_quantity}")
        print(f"Timestamp: {matchedOrder.timestamp}")
        print(f"Action: {'Bought' if matchedOrder.side == 'buy' else 'Sold'}")
        
        if matchedOrder.side == 'buy':
            self.buyerAckQueue.append(matchedOrder)
        else:
            self.sellerAckQueue.append(matchedOrder)
        
    def cancelOrder(self, order_id):
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.filled_quantity == order.quantity:
                print(f"Cannot cancel order {order_id}, already fully filled")
                self.buyerAckQueue.append(order)  # Send the order to the buyer
                orderbook = self.orderbooks[order.instrument]
                orderbook.remove(order)
                del self.orders[order_id]
                return True
            elif order.filled_quantity < order.quantity:
                remaining_quantity = order.quantity - order.filled_quantity
                order.quantity -= order.filled_quantity
                orderbook = self.orderbooks[order.instrument]
                orderbook.remove(order)
                del self.orders[order_id]

                # Print the message with filled and remaining quantities
                print(f"Order ID: {order_id} is cancelled. Filled quantity: {order.filled_quantity}, Remaining quantity: {remaining_quantity}")
                
                return True
            else:
                return False

        else:
            print("There is no such order")
            return False

                
    # def match(self,order):
    #     orderbook = self.orderbooks[order.instrument]
        
    #     if (order.side == 'buy' and orderbook.bestAsk() is not None and order.price >= orderbook.bestAsk().price):
    # # Buy order crossed the spread.
    #         self.matchBuyOrder(order, orderbook)
    #     elif (order.side == 'sell' and orderbook.bestBid() is not None and order.price <= orderbook.bestBid().price):
    # # Sell order crossed the spread.
    #         self.matchSellOrder(order, orderbook)
    #     else:
    #         # Order did not cross the spread, place in order book
    #         orderbook.add(order)
            
    def matchBuyOrder(self,order, orderbook):
        while orderbook.asks and order.price >= orderbook.bestAsk().price and order.quantity > 0 :
            ask = orderbook.bestAsk()
            
            if ask.quantity <= order.quantity:
                order.quantity -= ask.quantity
                order.filled_quantity += ask.quantity
                trade = Trade(ask.price,ask.quantity)
                self.trades[order.instrument].append(trade)
                self.acknowledgeOrder(MatchedOrder(ask.order_id,'sell',ask.price,ask.quantity,order.instrument,ask.timestamp))
                orderbook.remove(ask)
            else:
                trade = Trade(ask.price,order.quantity)
                self.trades[order.instrument].append(trade)
                ask.quantity -= order.quantity
                self.acknowledgeOrder(MatchedOrder(ask.order_id,'sell',ask.price,order.quantity,order.instrument,ask.timestamp))
                order.filled_quantity += order.quantity
                order.quantity = 0
                
                
    def matchSellOrder(self, order, orderbook):
        while orderbook.bids and order.price >= orderbook.bestBid().price and order.quantity > 0:
            bid = orderbook.bestBid()

            if bid.quantity <= order.quantity:
                order.quantity -= bid.quantity
                order.filled_quantity += bid.quantity
                trade = Trade(bid.price, bid.quantity)
                self.trades[order.instrument].append(trade)
                self.acknowledgeOrder(MatchedOrder(bid.order_id, 'sell', bid.price, bid.quantity, order.instrument, bid.timestamp))
                orderbook.remove(bid)
            else:
                trade = Trade(bid.price, order.quantity)
                self.trades[order.instrument].append(trade)
                bid.quantity -= order.quantity
                self.acknowledgeOrder(MatchedOrder(bid.order_id, 'sell', bid.price, order.quantity, order.instrument, bid.timestamp))
                order.filled_quantity += order.quantity
                order.quantity = 0

        # If the sell order is not fully filled, add the remaining part to the order book
        if order.quantity > 0:
            orderbook.add(order)
        
    