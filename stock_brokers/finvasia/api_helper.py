from typing import Dict
from stock_brokers.finvasia.NorenApi import NorenApi
import time
import concurrent.futures

api = None


def get_order_type(order_type: str) -> str:
    order_types = {
        "LIMIT": "LMT",
        "MARKET": "MKT",
        "SL": "SL-LMT",
        "SLL": "SL-LMT",
        "SL-L": "SL-LMT",
        "SLM": "SL-MKT",
        "SL-M": "SL-MKT",
    }
    return order_types.get(order_type.upper(), order_type)


def get_product(product_type: str) -> str:
    product_types = {"MIS": "I", "CNC": "C", "NRML": "M", "BRACKET": "B", "COVER": "H"}
    return product_types.get(product_type.upper(), product_type)


def make_order_modify_args(**kwargs) -> Dict:
    order_args = dict(
        symbol=convert_symbol(kwargs.pop("symbol", None), kwargs["exchange"]),
        order_type=get_order_type(kwargs.pop("order_type")),
        price=(lambda x: x if x >= 0 else 0.05)(kwargs.pop("price", 0)),
        trigger_price=(lambda x: x if x >= 0 else 0.05)(kwargs.pop("trigger_price", 0)),
        quantity=kwargs.pop("quantity"),
    )
    order_args.update(kwargs)
    return order_args


def make_order_place_args(**kwargs) -> Dict:
    order_args = dict(
        side=kwargs.pop("side")[0].upper(),
        product=get_product(kwargs.pop("product", "I")),
        symbol=convert_symbol(kwargs.pop("symbol", None), kwargs["exchange"]),
        disclosed_quantity=kwargs.pop("disclosed_quantity", kwargs["quantity"]),
        order_type=get_order_type(kwargs.pop("order_type")),
        price=(lambda x: x if x >= 0 else 0.05)(kwargs.pop("price", 0)),
        trigger_price=(lambda x: x if x >= 0 else 0.05)(kwargs.pop("trigger_price", 0)),
        validity=kwargs.pop("validity", "DAY"),
        tag=kwargs.pop("tag", "stock_brokers"),
    )
    # kwargs now contain quantity and exchange
    order_args.update(kwargs)
    return order_args


def convert_symbol(symbol: str, exchange: str = "NSE") -> str:
    """
    Convert raw symbol to finvasia
    """
    if exchange == "NSE":
        if symbol.endswith("-EQ"):
            return symbol
        elif symbol.endswith("-eq"):
            return symbol.upper()
        else:
            return f"{symbol}-EQ"
    return symbol


class Order:
    def __init__(
        self,
        buy_or_sell: str = None,
        product_type: str = None,
        exchange: str = None,
        tradingsymbol: str = None,
        price_type: str = None,
        quantity: int = None,
        price: float = None,
        trigger_price: float = None,
        discloseqty: int = 0,
        retention: str = "DAY",
        remarks: str = "tag",
        order_id: str = None,
    ):
        self.buy_or_sell = buy_or_sell
        self.product_type = product_type
        self.exchange = exchange
        self.tradingsymbol = tradingsymbol
        self.quantity = quantity
        self.discloseqty = discloseqty
        self.price_type = price_type
        self.price = price
        self.trigger_price = trigger_price
        self.retention = retention
        self.remarks = remarks
        self.order_id = None


# print(ret)


def get_time(time_string):
    data = time.strptime(time_string, "%d-%m-%Y %H:%M:%S")

    return time.mktime(data)


class ShoonyaApiPy(NorenApi):
    def __init__(
        self,
        host="https://api.shoonya.com/NorenWClientTP/",
        websocket="wss://api.shoonya.com/NorenWSTP/",
    ):
        NorenApi.__init__(self, host=host, websocket=websocket)
        global api
        api = self

    def place_basket(self, orders):

        resp_err = 0
        resp_ok = 0
        result = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:

            future_to_url = {
                executor.submit(self.place_order, order): order for order in orders
            }
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
            try:
                result.append(future.result())
            except Exception as exc:
                print(exc)
                resp_err = resp_err + 1
            else:
                resp_ok = resp_ok + 1

        return result

    def placeOrder(self, order: Order):
        ret = NorenApi.place_order(
            self,
            buy_or_sell=order.buy_or_sell,
            product_type=order.product_type,
            exchange=order.exchange,
            tradingsymbol=order.tradingsymbol,
            quantity=order.quantity,
            discloseqty=order.discloseqty,
            price_type=order.price_type,
            price=order.price,
            trigger_price=order.trigger_price,
            retention=order.retention,
            remarks=order.remarks,
        )
        # print(ret)

        return ret
