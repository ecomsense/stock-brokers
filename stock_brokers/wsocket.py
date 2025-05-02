from typing import Protocol


class Wsocket(Protocol):

    def on_connect(self):
        pass

    def on_ticks(self):
        pass

    def on_message(self):
        pass

    def on_close(self):
        pass

    def on_error(self):
        pass

    def on_reconnect(self):
        pass

    def on_noreconnect(self):
        pass

    def on_order_update(self):
        pass
