from typing import Protocol


class Symbols(Protocol):
    """
    protocol designed based on finvasia
    add exchange, base, expiry, diff, depth
    """

    def find_token_from_tradingsymbol(self, tradingsymbols):
        """applies to equity only"""
        if isinstance(tradingsymbols, str):
            tradingsymbols = [tradingsymbols]

    def _download(self):
        pass

    def _find_atm_from_underlying(self, underlying_price: float):
        pass

    def find_optiontype_from_tradingsymbol(self, tradingsymbol):
        pass

    def find_map_from_depth(self, underlying_price):
        atm = self._find_atm_from_underlying(underlying_price)

    def find_tradingsymbol_by_moneyness(
        self, underlying_price, distance: int, c_or_p: str, dct_symbols: dict
    ):
        atm = self._find_atm_from_underlying(underlying_price)

    def find_tradingsymbol_with_closest_premium(
        self, quotes: dict[str, float], premium: float, contains: str
    ):
        pass
