"""
Various Python types used in the model
"""
from __future__ import annotations
from enum import Enum, EnumMeta
from typing import TypedDict, Union


class SerializableEnum(Enum):
    def __str__(self):
        return self.value

# pylint: disable=no-value-for-parameter


class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True


class ReflectiveSerializableEnum(SerializableEnum, metaclass=MetaEnum):
    pass


class TraderType(Enum):
    """
    different account holders
    """
    ARBITRAGE_TRADER = "ArbitrageTrading"
    RANDOM_TRADER = "RandomTrading"
    MAX_TRADER = "SellMax"


class Stable(ReflectiveSerializableEnum):
    """
    Celo Stable assets
    """
    CUSD = "cusd"
    CREAL = "creal"
    CEUR = "ceur"


class CryptoAsset(ReflectiveSerializableEnum):
    CELO = "celo"
    ETH = "eth"
    BTC = "btc"
    DAI = "dai"


class Fiat(ReflectiveSerializableEnum):
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
