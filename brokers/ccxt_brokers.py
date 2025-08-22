import ccxt

class _BaseCCXT:
    def __init__(self, exchange, key: str = "", secret: str = "", password: str = ""):
        params = {"apiKey": key or "", "secret": secret or "", "enableRateLimit": True}
        if password:
            params["password"] = password
        self.ex = exchange(params)

    def get_price(self, symbol: str) -> float:
        """
        symbol format is usually 'BTC/USDT', 'ETH/USD', etc.
        """
        try:
            t = self.ex.fetch_ticker(symbol)
            return float(t.get("last") or 0.0)
        except Exception:
            return 0.0

    def place_market_order(self, symbol: str, side: str, qty: float):
        try:
            side = side.lower()
            if side == "buy":
                o = self.ex.create_market_buy_order(symbol, qty)
            else:
                o = self.ex.create_market_sell_order(symbol, qty)
            return {"ok": True, "data": o}
        except Exception as e:
            return {"ok": False, "error": str(e)}


class BinanceBroker(_BaseCCXT):
    name = "binance"
    def __init__(self, key: str, secret: str):
        super().__init__(ccxt.binance, key, secret)


class CoinbaseBroker(_BaseCCXT):
    name = "coinbase"
    """
    CCXT supports 'coinbase' (Advanced Trade) and 'coinbasepro' (legacy).
    We use 'coinbase' here; passphrase maps to 'password' in CCXT params.
    """
    def __init__(self, key: str, secret: str, passphrase: str):
        super().__init__(ccxt.coinbase, key, secret, password=passphrase)


# Optional: a generic broker you can use for many exchanges via a name string
SUPPORTED_EXCHANGES = {
    # add more as needed:
    "binance": ccxt.binance,
    "coinbase": ccxt.coinbase,
    "kraken": ccxt.kraken,
    "okx": ccxt.okx,
    "bybit": ccxt.bybit,
    "kucoin": ccxt.kucoin,
    "bitfinex": ccxt.bitfinex,
}

class CCXTBroker(_BaseCCXT):
    """
    Generic CCXT wrapper. Example:
        b = CCXTBroker("kraken", key, secret)
        b.place_market_order("BTC/USD", "buy", 0.001)
    """
    def __init__(self, exchange_name: str, key: str = "", secret: str = "", password: str = ""):
        ex_cls = SUPPORTED_EXCHANGES.get(exchange_name.lower())
        if not ex_cls:
            raise ValueError(f"Exchange '{exchange_name}' not supported in SUPPORTED_EXCHANGES.")
        super().__init__(ex_cls, key, secret, password=password)
    name = "ccxt"
