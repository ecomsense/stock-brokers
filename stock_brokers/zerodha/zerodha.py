import sys
from typing import Dict, List

import pyotp
import requests
from kiteconnect import KiteConnect
from stock_brokers.zerodha.api_helper import get_order_type, get_side

from stock_brokers.base import Broker, post, pre

LOGINURL = "https://kite.zerodha.com/api/login"
TWOFAURL = "https://kite.zerodha.com/api/twofa"


class Zerodha(Broker):
    """
    Automated Trading class
    """

    def __init__(self, userid, password, totp, api_key, secret):
        self.userid = userid
        self.password = password
        self.totp = totp
        self.api_key = api_key
        self.secret = secret
        self.kite = KiteConnect(api_key=api_key)
        super(Zerodha, self).__init__()

    def authenticate(self) -> bool:
        """
        Authenticate the user
        """

        try:
            session = requests.Session()
            session_post = session.post(
                LOGINURL, data={"user_id": self.userid, "password": self.password}
            ).json()
            print(f"{session_post=}")
        except ValueError as ve:
            print(f"ValueError: {ve}")
            sys.exit(1)  # Exit with a non-zero status code to indicate an error
        except requests.RequestException as re:
            print(f"RequestException: {re}")
            sys.exit(1)
        except Exception as e:
            # Handle other unexpected exceptions
            print(f"An unexpected error occurred: {e}")
            sys.exit(1)

        try:
            req_twofa = {
                "user_id": self.userid,
                "request_id": session_post["data"]["request_id"],
                "twofa_value": pyotp.TOTP(self.totp).now(),
                "skip_session": True,
            }
            response = session.post(TWOFAURL, data=req_twofa, allow_redirects=True)
            response.raise_for_status()  # Raise an exception for HTTP errors
        except Exception as e:
            print(f"twofa error: {e}")
            sys.exit(1)

        try:
            req_login = {"api_key": self.api_key, "allow_redirects": True}
            session_get = session.get(
                "https://kite.trade/connect/login/", params=req_login
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
        except Exception as e:
            e = str(e)
            print(f"{e=}")
            if "request_token" in e:
                request_token = e.split("request_token=")[1].split(" ")[0]
                print(f"{request_token=}")
            else:
                print(f"request token error: {e}")
                sys.exit(1)
        else:
            print(f"no errors: trying to get token from {session_get}")
            split_url = session_get.url.split("request_token=")
            print(f"{split_url=}")
            if len(split_url) >= 2:
                request_token = split_url[1].split("&")[0]
                print(f"{request_token=}")

        try:
            data = self.kite.generate_session(request_token, api_secret=self.secret)
            if data and isinstance(data, dict) and data.get("access_token", False):
                print(f"{data['access_token']}")
                self.enctoken = data["access_token"]
                return True
            else:
                raise ValueError("Unable to generate session")
        except Exception as e:
            # Handle any unexpected exceptions
            print(f"generating session error: {e}")
            sys.exit(1)

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
        order_args = dict(
            exchange=kwargs["exchange"],
            tradingsymbol=kwargs["tradingsymbol"],
            transaction_type=get_side(kwargs["transaction_type"]),
            quantity=kwargs["quantity"],
            product=kwargs["product"],
            order_type=get_order_type(kwargs["order_type"]),
            variety=kwargs.get("variety", "regular"),
        )
        if kwargs.get("price", None):
            order_args["price"] = kwargs["price"]
        if kwargs.get("trigger_price", None):
            order_args["trigger_price"] = kwargs["trigger_price"]

        order_args["tag"] = kwargs.pop("tag", "stock_brokers")
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

    def ltp(self, exchsym):
        return self.kite.ltp(exchsym)

    def historical(self, kwargs):
        try:
            return self.kite.historical_data(**kwargs)
        except Exception as e:
            print(f"{e} while historical with params {kwargs}")
