"""
Provides a Order class
"""


from typing import TYPE_CHECKING
from model.types.base import Currency, Exchange


if TYPE_CHECKING:
    from model.entities.account import Account

# pylint:disable = too-few-public-methods


class Order():
    def __init__(self, account, asset, sell_amount, buy_amount, sell_reserve_asset, exchange):
        self.account: Account = account
        self.asset: Currency = asset
        self.sell_amount: float = sell_amount
        self.buy_amount: float = buy_amount
        self.sell_reserve_asset: bool = sell_reserve_asset
        self.exchange: Exchange = exchange
