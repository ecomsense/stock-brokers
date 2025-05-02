from typing import Protocol, Any, Optional


class Symbols(Protocol):
    """
    protocol designed based on finvasia
    add exchange, base, expiry, diff, depth
    """

    def find_token_from_tradingsymbol(self, tradingsymbols) -> list[dict[str, Any]]:
        """applies to equity only"""
        if isinstance(tradingsymbols, str):
            tradingsymbols = [tradingsymbols]

    def _download(self):
        pass

    def _find_atm_from_underlying(self, underlying_price: float) -> Any[float, int]:
        pass

    def find_optiontype_from_tradingsymbol(self, tradingsymbol: str) -> Optional[str]:
        pass

    def find_map_from_depth(self, underlying_price) -> dict[str, Any]:
        atm = self._find_atm_from_underlying(underlying_price)

    def find_tradingsymbol_by_moneyness(
        self, underlying_price, distance: int, c_or_p: str, dct_symbols: dict
    ) -> Optional[str]:
        atm = self._find_atm_from_underlying(underlying_price)

    def find_tradingsymbol_with_closest_premium(
        self, quotes: dict[str, float], premium: float, contains: str
    ) -> Optional[str]:
        pass
