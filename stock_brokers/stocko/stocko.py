from stock_brokers.stocko.stockoapi import AlphaTrade
from stok_brokers.base import Broker, pre, post


class Stocko(Broker):
    def __init__(self, **cnfg):
        self.broker = AlphaTrade(**cnfg)
        super(Stocko, self).__init__()

    def authenticate(self):
        return True

    @post
    def order_cancel(self, **kwargs): ...

    @post
    def order_place(self, **kwargs): ...

    @property
    def positions(self): ...

    @pre
    def orders(self): ...
