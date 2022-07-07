import functools
from typing import Tuple
from model.entities.balance import Balance
from model.state_variables import StateVariables
from model.types.base import CollateralProviderState, CryptoAsset, MentoExchange, Stable, Token
from model.types.configs import MentoExchangeConfig
from model.types.pair import Pair

def with_state(func):
    @functools.wraps(func)
    def func_with_state(self, *args, **kwargs):
        assert self.__state__ is not None, "No state provided"
        return func(*args, **kwargs)
    return func_with_state

class CollateralProviderContract:
    exchange: MentoExchange
    pair: Pair
    cp_token: Token = Token.CP

    __state__: CollateralProviderState
    __global_state__: StateVariables

    def __init__(self, exchange: MentoExchange, config: MentoExchangeConfig):
        self.pair = Pair(config.stable, config.reserve_asset)
        self.exchange = exchange
    
    @property
    def stable_asset(self) -> Stable:
        return self.pair.quote
    
    @property
    def reserve_asset(self) -> CryptoAsset:
        return self.pair.base
    
    def deposit(
        self,
        state: StateVariables,
        total_to_deposit_in_reserve_asset: float
    ) -> Tuple[CollateralProviderState, Balance]: 
        with self.set_state(state):
            required_reserve_asset_fraction = self.required_reserve_asset_fraction
            reserve_asset_to_deposit = total_to_deposit_in_reserve_asset * required_reserve_asset_fraction
            stable_asset_to_deposit = total_to_deposit_in_reserve_asset * (1 - required_reserve_asset_fraction)

            cp_tokens_to_mint = self.cp_tokens_to_mint(total_to_deposit_in_reserve_asset)

            next_state = CollateralProviderState(
                self.stable_basket + stable_asset_to_deposit,
                self.reserve_asset_basket + reserve_asset_to_deposit,
                self.minted_cp_tokens + cp_tokens_to_mint
            )

            account_delta = Balance({
                self.stable_asset: -1 * stable_asset_to_deposit,
                self.reserve_asset: -1 * reserve_asset_to_deposit,
                self.cp_token: cp_tokens_to_mint
            })

            return (next_state, account_delta)

    @with_state
    def cp_tokens_to_mint(
        self,
        total_to_deposit_in_reserve_asset: float
    ) -> float:
        if self.minted_cp_tokens == 0:
            return total_to_deposit_in_reserve_asset
        else:
            return self.cp_tokens_per_reserve_asset * total_to_deposit_in_reserve_asset

    @property
    @with_state
    def minted_cp_tokens(self) -> float:
        return self.__state__['minted_cp_tokens']

    @property
    @with_state
    def stable_basket(self) -> float:
        return self.__state__['stable_basket']

    @property
    @with_state
    def reserve_asset_basket(self) -> float:
        return self.__state__['reserve_asset_basket']
    
    @property
    @with_state
    def cp_tokens_per_reserve_asset(self) -> float:
        return self.minted_cp_tokens / self.total_value_in_reserve_asset
    
    @property
    @with_state
    def required_reserve_asset_fraction(self) -> float:
        if self.minted_cp_tokens == 0:
            return 1
        else:
            return self.reserve_asset_basket / self.total_value_in_reserve_asset
    
    @property
    @with_state
    def total_value_in_reserve_asset(self) -> float:
        stable_to_reserve_rate = self.pair.inverse.get_rate(self.__global_state__)
        return (
            self.reserve_asset_basket + 
            self.stable_basket * stable_to_reserve_rate
        )

    def set_state(self, state: StateVariables):
        self.__global_state__ = state
        self.__state__ = state['collateral_provider'].get(self.exchange, CollateralProviderState(0, 0, 0))
        yield
        self.__global_state__ = None
        self.__state__ = None
