import alpaca_trade_api as tradeapi

class AlpacaBroker:
    def __init__(self, api_key, api_secret, base_url="https://paper-api.alpaca.markets"):
        self.api = tradeapi.REST(api_key, api_secret, base_url, api_version="v2")

    def get_account(self):
        return self.api.get_account()

    def place_order(self, symbol, qty, side, order_type="market", time_in_force="gtc"):
        return self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force=time_in_force
        )
