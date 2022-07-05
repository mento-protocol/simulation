"""
Various Python types used in the model
"""
from __future__ import annotations
from typing import TypedDict, Union
from enum import Enum


class SerializableEnum(Enum):
    def __str__(self):
        return self.value


class TraderType(Enum):
    """
    different account holders
    """
    ARBITRAGE_TRADER = "ArbitrageTrading"
    RANDOM_TRADER = "RandomTrading"
    MAX_TRADER = "SellMax"


class Stable(SerializableEnum):
    """
    Celo Stable assets
    """
    CUSD = "cusd"
    CREAL = "creal"
    CEUR = "ceur"


class CryptoAsset(SerializableEnum):
    CELO = "celo"
    ETH = "eth"
    BTC = "btc"
    DAI = "dai"


class Fiat(SerializableEnum):
    USD = "usd"
    EUR = "eur"
    BRL = "brl"


class MentoExchange(SerializableEnum):
    CUSD_CELO = "cusd_celo"
    CREAL_CELO = "creal_celo"
    CEUR_CELO = "ceur_celo"


Currency = Union[Stable, Fiat, CryptoAsset]


class MentoBuckets(TypedDict):
    stable: float
    reserve_asset: float


class MarketPriceModel(Enum):
    QUANTLIB = "quantlib"
    PRICE_IMPACT = "price_impact"
    HIST_SIM = "hist_sim"
    SCENARIO = "scenario"


class PriceImpact(Enum):
    ROOT_QUANTITY = "root_quantity"
    CUSTOM = "custom"


class ImpactDelayType(Enum):
    INSTANT = "instant"
    NBLOCKS = "nblocks"


class AggregationMethod(Enum):
    IDENTITY = 'indentity'


class OracleType(Enum):
    SINGLE_SOURCE = 'single_source'


class Exchange(SerializableEnum):
    MENTO = 'mento'
    GENERAL_MARKET = 'general_market'

# pylint:disable = too-few-public-methods


class Order():
    def __init__(self, asset, sell_amount, buy_amount, sell_reserve_asset, exchange):
        self.asset: Currency = asset
        self.sell_amount: float = sell_amount
        self.buy_amount: float = buy_amount
        self.sell_reserve_asset: bool = sell_reserve_asset
        self.exchange: Exchange = exchange
