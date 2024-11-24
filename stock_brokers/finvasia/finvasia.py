from stock_brokers.finvasia.api_helper import ShoonyaApiPy
from stock_brokers.finvasia.api_helper import (
    convert_symbol,
    get_price_type,
    get_product,
)
from stock_brokers.base import Broker, pre, post
from typing import List, Dict, Union
import pendulum
import pyotp
from traceback import print_exc


class Finvasia(Broker):
    """
    Automated Trading class
    """

    def __init__(
        self,
        user_id: str,
        password: str,
        pin: str,
        vendor_code: str,
        app_key: str,
        imei: str,
        broker: str = "",
    ):
        self._user_id = user_id
        self._password = password
        self._pin = pin
        self._vendor_code = vendor_code
        self._app_key = app_key
        self._imei = imei
        if broker == "profitmart":
            self.finvasia = ShoonyaApiPy(
                host="https://profitmax.profitmart.in/NorenWClientTP",
                websocket="wss://profitmax.profitmart.in/NorenWSTP/",
            )
        elif broker == "flattrade":
            self.finvasia = ShoonyaApiPy(
                host="https://piconnect.flattrade.in/PiConnectTP/",
                websocket="wss://piconnect.flattrade.in/PiConnectWSTp/",
            )
        else:
            self.finvasia = ShoonyaApiPy()
        super(Finvasia, self).__init__()

    def authenticate(self) -> Union[Dict, None]:
        try:
            if len(self._pin) > 15:
                twoFA = (
                    self._pin if len(self._pin) == 4 else pyotp.TOTP(self._pin).now()
                )
            else:
                twoFA = self._pin
            return self.finvasia.login(
                userid=self._user_id,
                password=self._password,
                twoFA=twoFA,
                vendor_code=self._vendor_code,
                api_secret=self._app_key,
                imei=self._imei,
            )
        except Exception as e:
            print(f"{e} in login")
            print_exc()
            return None

    @property
    @post
    def orders(self) -> List[Dict]:
        order_list = []
        orderbook = self.finvasia.get_order_book()

        if not orderbook or len(orderbook) == 0:
            return [{}]

        float_cols = ["avgprc", "prc", "rprc", "trgprc"]
        int_cols = ["fillshares", "qty"]
        for order in orderbook:
            for int_col in int_cols:
                order[int_col] = int(order.get(int_col, 0))
            for float_col in float_cols:
                order[float_col] = float(order.get(float_col, 0))
            # pendulum current datetime
            now = pendulum.now(tz="Asia/Kolkata").format("DD-MM-YYYY HH:mm:ss")
            ts = order.get("exch_tm", now)
            # Timestamp converted to str to facilitate loading into pandas dataframe
            order["exchange_timestamp"] = str(
                pendulum.from_format(ts, fmt="DD-MM-YYYY HH:mm:ss", tz="Asia/Kolkata")
            )
            ts2 = order.get("norentm", now)
            order["broker_timestamp"] = str(
                pendulum.from_format(ts2, fmt="HH:mm:ss DD-MM-YYYY", tz="Asia/Kolkata")
            )
            order_list.append(order)
        return order_list

    @property
    @post
    def positions(self) -> List[Dict]:
        positionbook = self.finvasia.get_positions()

        if not positionbook or len(positionbook) == 0:
            return [{}]

        position_list = []
        int_cols = [
            "netqty",
            "daybuyqty",
            "daysellqty",
            "cfbuyqty",
            "cfsellqty",
            "openbuyqty",
            "opensellqty",
        ]
        float_cols = [
            "daybuyamt",
            "daysellamt",
            "lp",
            "rpnl",
            "dayavgprc",
            "daybuyavgprc",
            "daysellavgprc",
            "urmtom",
        ]
        for position in positionbook:
            try:
                for int_col in int_cols:
                    position[int_col] = int(position.get(int_col, 0))
                for float_col in float_cols:
                    position[float_col] = float(position.get(float_col, 0))
            except Exception as e:
                print(f"{e} while iter stockbroker trades")
                print_exc()
            position_list.append(position)
        return position_list

    @property
    @post
    def trades(self) -> List[Dict]:
        trade_list = []
        tradebook = self.finvasia.get_trade_book()
        if not tradebook or len(tradebook) == 0:
            return [{}]

        int_cols = ["flqty", "qty", "fillshares"]
        float_cols = ["prc", "flprc"]
        for trade in tradebook:
            try:
                for int_col in int_cols:
                    trade[int_col] = int(trade.get(int_col, 0))
                for float_col in float_cols:
                    trade[float_col] = float(trade.get(float_col, 0))
                now = pendulum.now(tz="Asia/Kolkata").format("DD-MM-YYYY HH:mm:ss")
                ts = trade.get("norentm", now)
                trade["broker_timestamp"] = str(
                    pendulum.from_format(
                        ts, fmt="HH:mm:ss DD-MM-YYYY", tz="Asia/Kolkata"
                    )
                )
            except Exception as e:
                print(f"{e} while iter stockbroker trades")
                print_exc()
            trade_list.append(trade)
        return trade_list

    @pre
    def order_place(self, **kwargs) -> Union[str, None]:
        try:
            order_args = dict(
                side=kwargs.pop("side")[0].upper(),
                product=get_product(kwargs.pop("product", "I")),
                symbol=convert_symbol(kwargs.pop("symbol", None), kwargs["exchange"]),
                disclosed_quantity=kwargs.pop("disclosed_quantity", kwargs["quantity"]),
                price_type=get_price_type(kwargs.pop("price_type")),
                price=(lambda x: x if x >= 0 else 0.05)(kwargs.pop("price", 0)),
                trigger_price=(lambda x: x if x >= 0 else 0.05)(
                    kwargs.pop("trigger_price", 0)
                ),
                validity=kwargs.pop("validity", "DAY"),
                tag=kwargs.pop("tag", "stock_brokers"),
            )
            # kwargs now contain quantity and exchange
            order_args.update(kwargs)
            response = self.finvasia.place_order(**order_args)
            if isinstance(response, dict) and response.get("norenordno") is not None:
                return response["norenordno"]
        except Exception as err:
            print(err)

    @post
    def order_cancel(self, order_id: str) -> Union[Dict, None]:
        """
        Cancel an existing order
        """
        return self.finvasia.cancel_order(orderno=order_id)

    @pre
    def order_modify(self, **kwargs) -> Union[str, None]:
        """
        Modify an existing order
        """
        try:
            order_type = kwargs.pop("newprice_type", "MARKET")
            if order_type:
                kwargs["newprice_type"] = get_price_type(order_type)
            return self.finvasia.modify_order(**kwargs)
        except Exception as e:
            print(f"{e} order modify with params {kwargs}")
            print_exc()

    @property
    def margins(self):
        return self.finvasia.get_limits()

    def instrument_symbol(self, exch: str, txt: str):
        res = self.finvasia.searchscrip(exchange=exch, searchtext=txt)
        if res:
            return res["values"][0].get("token", 0)

    def historical(self, exch: str, tkn: str, fm: str, to: str, tf: int = 1):
        """
        ret = api.get_time_price_series(exchange='NSE', token='22',
        starttime=obj_datetime.timestamp(), interval=5)
        interval: acceptable integer values in minutes are
        “1”, ”3”, “5”, “10”, “15”, “30”, “60”, “120”, “240”
        """
        return self.finvasia.get_time_price_series(exch, tkn, fm, to, tf)

    def scriptinfo(self, exch: str, tkn: str):
        return self.finvasia.get_quotes(exch, tkn)
