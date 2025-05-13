import os
from typing import Dict, List

import pyotp
import requests
from kiteext.kiteext import KiteExt

from stock_brokers.base import Broker, post, pre
from stock_brokers.bypass.api_helper import (
    get_order_type,
    get_side,
    make_order_place_args,
)


class Bypass(Broker):
    """
    Automated Trading class
    """

    def __init__(self, userid, password, totp, tokpath="enctoken.txt", enctoken=None):
        self.userid = userid
        self.password = password
        self.totp = totp
        self.tokpath = tokpath
        self.enctoken = enctoken
        self.kite = KiteExt(userid=userid)
        super(Bypass, self).__init__()

    def authenticate(self) -> bool:
        """
        Authenticate the user
        """
        if not self.enctoken:
            print(f"{self.enctoken} not found, getting it")
            if self.get_enctoken():
                print(f"got token {self.enctoken}")
                self.enctoken = open(self.tokpath, "r").read().rstrip()
                print(f"again reading it {self.enctoken}")
        try:
            # self._login()
            print(f"trying to set headers with {self.enctoken}")
            self.kite.set_headers(self.enctoken, self.userid)
        except Exception as err:
            print(f"{err} while authentiating")
            self.remove_token
            return False
        else:
            return True

    def get_enctoken(self) -> bool:
        try:
            session = requests.Session()
            data = {"user_id": self.userid, "password": self.password}
            response = session.post("https://kite.zerodha.com/api/login", data=data)
            otp = pyotp.TOTP(self.totp).now()
            twofa = f"{int(otp):06d}"
            response = session.post(
                "https://kite.zerodha.com/api/twofa",
                data={
                    "request_id": response.json()["data"]["request_id"],
                    "twofa_value": twofa,
                    "user_id": response.json()["data"]["user_id"],
                },
            )
            enctoken = response.cookies.get("enctoken", False)
            if enctoken:
                with open(self.tokpath, "w+") as wr:
                    wr.write(enctoken)
                self.enctoken = enctoken
            else:
                raise Exception("Enter valid details !!!!")
        except Exception as e:
            print(e)
            return False
        else:
            return True

    @pre
    def order_place(self, **kwargs: List[Dict]):
        """
        Place an order

        args:
            exchange, symbol, side, quantity, product, order_type,
        optional:
            price=None, validity=None, disclosed_quantity=None, trigger_price=None,
            squareoff=None, stoploss=None, trailing_stoploss=None, tag=None
        """
        print(f"before order place {kwargs}")
        order_args = make_order_place_args(**kwargs)
        print(f"after order_place {order_args}")
        return self.kite.place_order(**order_args)

    @pre
    def order_modify(self, **kwargs: List[Dict]):
        """
        Modify an existing order
        Note
        ----
        All changes must be passed as keyword arguments
        input:
            variety, order_id,
        optional:
            parent_order_id=None, quantity=None, price=None,
            order_type=None, trigger_price=None, validity=None,
            disclosed_quantity=None)
        """
        order_id = kwargs.pop("order_id", None)
        if order_id is None:
            raise ValueError("order_id is required")
        order_args = dict(
            variety=kwargs.get("variety", "regular"),
        )
        if kwargs.get("quantity", None):
            order_args["quantity"] = kwargs["quantity"]
        if kwargs.get("price", None):
            order_args["price"] = kwargs["price"]
        if kwargs.get("order_type", None):
            order_args["order_type"] = get_order_type(kwargs["order_type"])
        if kwargs.get("trigger_price", None):
            order_args["trigger_price"] = kwargs["trigger_price"]
        if kwargs.get("validity", None):
            order_args["validity"] = kwargs["validity"]
        if kwargs.get("disclosed_quantity", None):
            order_args["disclosed_quantity"] = kwargs["disclosed_quantity"]

        return self.kite.modify_order(order_id=order_id, **kwargs)

    @pre
    def order_cancel(self, **kwargs):
        """
        Cancel an existing order
        """
        order_id = kwargs.pop("order_id", None)
        if order_id is None:
            raise ValueError("order_id is required")
        kwargs["variety"] = kwargs.get("variety", "regular")
        return self.kite.cancel_order(order_id=order_id, **kwargs)

    @property
    @post
    def orders(self):
        status_map = {
            "OPEN": "PENDING",
            "COMPLETE": "COMPLETE",
            "CANCELLED": "CANCELED",
            "CANCELLED AMO": "CANCELED",
            "REJECTED": "REJECTED",
            "MODIFY_PENDING": "WAITING",
            "OPEN_PENDING": "WAITING",
            "CANCEL_PENDING": "WAITING",
            "AMO_REQ_RECEIVED": "WAITING",
            "TRIGGER_PENDING": "WAITING",
        }
        orderbook = self.kite.orders()
        if orderbook:
            for order in orderbook:
                order["status"] = status_map.get(order["status"])
            return orderbook
        else:
            return [{}]

    @property
    @post
    def trades(self) -> List[Dict]:
        tradebook = self.kite.trades()
        if tradebook:
            return tradebook
        else:
            return [{}]

    @property
    @post
    def positions(self):
        position_book = self.kite.positions().get("day")
        if position_book:
            for position in position_book:
                if position["quantity"] > 0:
                    position["side"] = "BUY"
                else:
                    position["side"] = "SELL"
            return position_book
        return [{}]

    @property
    def profile(self):
        return self.kite.profile()

    @property
    def margins(self):
        return self.kite.margins()

    @property
    def remove_token(self):
        if os.path.exists(self.tokpath):
            os.remove(self.tokpath)
        else:
            print(f"not found {self.tokpath}")

    def ltp(self, exchsym):
        return self.kite.ltp(exchsym)

    def historical(self, kwargs):
        try:
            return self.kite.historical_data(**kwargs)
        except Exception as e:
            print(f"{e} while historical")
