import pendulum
from traceback import print_exc
from typing import List, Dict


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


def convert_time_string(dct, key, fmt):
    # pendulum current datetime
    now = pendulum.now(tz="Asia/Kolkata").format("DD-MM-YYYY HH:mm:ss")
    if dct[key] is None:
        ts = now
    else:
        ts = dct.pop(key)
    dct[key] = str(pendulum.from_format(ts, fmt=fmt, tz="Asia/Kolkata"))
    return dct


def filter_dictionary_by_keys(elephant: Dict, keys: List) -> Dict:
    """
    generic function to filter any dict
    """
    if not any(elephant):
        return elephant

    filtered = {}
    for item in keys:
        filtered[item] = elephant.get(item, None)
    return filtered


def get_product(product_type: str) -> str:
    product_types = {"MIS": "I", "CNC": "C", "NRML": "M", "BRACKET": "B", "COVER": "H"}
    return product_types.get(product_type.upper(), product_type)


def make_order_modify_args(**kwargs) -> Dict:
    order_args = dict(
        symbol=convert_symbol(kwargs.pop("symbol", None), kwargs["exchange"]),
        order_type=kwargs.pop("order_type"),
        price=(lambda x: x if x >= 0 else 0.05)(kwargs.pop("price", 0)),
        trigger_price=(lambda x: x if x >= 0 else 0.05)(kwargs.pop("trigger_price", 0)),
        quantity=kwargs.pop("quantity"),
    )
    order_args.update(kwargs)
    return order_args


def make_order_place_args(**kwargs) -> Dict:
    order_args = dict(
        tradingsymbol=kwargs.pop("tradingsymbol"),
        transaction_type=kwargs.pop("transaction_type"),
        exchange=kwargs.pop("exchange"),
        quantity=kwargs.pop("quantity"),
        product=kwargs.pop("product", "MIS"),
        variety=kwargs.pop("variety", "regular"),
    )
    if kwargs.get("order_type", None):
        order_args["order_type"] = kwargs.pop("order_type")
    if kwargs.get("price", None):
        order_args["price"] = kwargs.pop("price")
    if kwargs.get("trigger_price", None):
        order_args["trigger_price"] = kwargs.pop("trigger_price")
    if kwargs.get("disclosed_quantity", None):
        order_args["disclosed_quantity"] = kwargs.pop("disclosed_quantity")

    order_args["tag"] = kwargs.pop("tag", "stock_brokers")
    # kwargs now contain quantity and exchange
    print(f"remaining in dict {kwargs}")
    return order_args


def post_order_hook(*orderbook):
    try:
        keys = [
            "symbol",
            "quantity",
            "side",
            "validity",
            "price",
            "trigger_price",
            "average_price",
            "filled_quantity",
            "order_id",
            "exchange",
            "exchange_order_id",
            "disclosed_quantity",
            "broker_timestamp",
            "exchange_timestamp",
            "status",
            "product",
            "order_type",
        ]
        # Extract only the key-value pairs where the key is in the predefined keys list
        orderbook = [filter_dictionary_by_keys(order, keys) for order in orderbook]
        float_cols = ["average_price", "price", "trigger_price"]
        int_cols = ["filled_quantity", "quantity"]
        order_list = []
        for order in orderbook:
            for int_col in int_cols:
                order[int_col] = (
                    lambda x: int(x) if isinstance(x, str) and x.isdigit() else 0
                )(order.pop(int_col))
            for float_col in float_cols:
                order[float_col] = (
                    lambda x: float(x) if isinstance(x, str) and x.isdigit() else 0
                )(order.pop(float_col))

            order = convert_time_string(
                order, "exchange_timestamp", "DD-MM-YYYY HH:mm:ss"
            )
            order = convert_time_string(
                order, "broker_timestamp", "HH:mm:ss DD-MM-YYYY"
            )
            order_list.append(order)
        return order_list
    except Exception as e:
        print(f"{e} while processing stock_brokers orderbook")
        print_exc()


def get_side(side):
    if side[0].upper() == "B":
        return "BUY"
    else:
        return "SELL"
