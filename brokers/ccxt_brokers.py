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
