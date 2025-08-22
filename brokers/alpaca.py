import requests

class AlpacaBroker:
    name = "alpaca"

    def __init__(self, key: str, secret: str, base_url: str = "https://paper-api.alpaca.markets"):
        self.base = base_url.rstrip("/")
        self.sess = requests.Session()
        self.sess.headers.update({
            "APCA-API-KEY-ID": key or "",
            "APCA-API-SECRET-KEY": secret or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def get_price(self, symbol: str) -> float:
        """
        Try to fetch latest trade from Alpaca Data API v2.
        If base is paper-api.alpaca.markets -> data host is data.alpaca.markets
        """
        try:
            data_host = self.base.replace("https://api.", "https://data.").replace("https://paper-api.", "https://data.")
            url = f"{data_host}/v2/stocks/{symbol}/trades/latest"
            r = self.sess.get(url, timeout=10)
            if r.ok:
                return float(r.json().get("trade", {}).get("p", 0.0))
        except Exception:
            pass
        return 0.0

    def place_market_order(self, symbol: str, side: str, qty: float):
        """
        Place a simple market order (stocks). time_in_force=day
        """
        try:
            url = f"{self.base}/v2/orders"
            payload = {
                "symbol": symbol,
                "qty": qty,
                "side": side.lower(),  # "buy" or "sell"
                "type": "market",
                "time_in_force": "day"
            }
            r = self.sess.post(url, json=payload, timeout=15)
            data = r.json() if r.content else {}
            return {"ok": r.ok, "status_code": r.status_code, "data": data}
        except Exception as e:
            return {"ok": False, "error": str(e)}
