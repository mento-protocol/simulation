"""
CollateralProviderContract that manages the state of LP-style position
"""

import functools
from typing import Tuple
from contextlib import contextmanager

from model.entities.balance import Balance
from model.state_variables import StateVariables
from model.types.base import CollateralProviderState, CryptoAsset, MentoExchange, Stable, Token
from model.types.configs import MentoExchangeConfig
from model.types.pair import Pair

def with_state(func):
    @functools.wraps(func)
    def func_with_state(self, *args, **kwargs):
        assert self.__state__ is not None, "No state provided"
        return func(self, *args, **kwargs)
    return func_with_state

class CollateralProviderContract:
    """
    CollateralProvider - manage state for a two-bucket position with LP tokens
    """
    mento_exchange: MentoExchange
    reserve_asset: CryptoAsset
    stable: Stable
    pair: Pair
    cp_token: Token = Token.CP

    __state__: CollateralProviderState
    __global_state__: StateVariables

    def __init__(self, exchange: MentoExchange, config: MentoExchangeConfig):
        self.stable = config.stable
        self.reserve_asset = config.reserve_asset
        self.mento_exchange = exchange

    def deposit(
        self,
        state: StateVariables,
        total_to_deposit_in_reserve_asset: float
    ) -> Tuple[CollateralProviderState, Balance]:
        """
        Simulate a deposit to this contract:
        Given a current state and an amount to deposit denominated in reserve asset,
        compute the next state of the contract and the balance delta for the account
        making the deposit.
        """
        with self.set_state(state):
            required_reserve_asset_fraction = self.required_reserve_asset_fraction
            reserve_asset_to_deposit = (
                total_to_deposit_in_reserve_asset *
                required_reserve_asset_fraction
            )
            stable_asset_to_deposit = (
                total_to_deposit_in_reserve_asset *
                (1 - required_reserve_asset_fraction) *
                self.reserve_to_stable_rate
            )

            cp_tokens_to_mint = self.cp_tokens_to_mint(total_to_deposit_in_reserve_asset)

            next_state = CollateralProviderState(
                stable_bucket=self.stable_bucket + stable_asset_to_deposit,
                reserve_asset_bucket=self.reserve_asset_bucket + reserve_asset_to_deposit,
                minted_cp_tokens=self.minted_cp_tokens + cp_tokens_to_mint
            )

            account_delta = Balance({
                self.stable: -1 * stable_asset_to_deposit,
                self.reserve_asset: -1 * reserve_asset_to_deposit,
                self.cp_token: cp_tokens_to_mint
            })

            return (next_state, account_delta)

    def exchange(
        self,
        state: StateVariables,
        _amount: float,
        _sell_reserve_asset: bool
    ) -> Tuple[CollateralProviderState, float, float]:
        with self.set_state(state):
            pass

    def withdraw(
        self,
        state: StateVariables,
        cp_tokens_to_withdraw: float
    ) -> Tuple[CollateralProviderState, Balance]:
        """
        Simulate a withdrawl from this contract:
        Given a current state and an amount of CP tokens to withdraw,
        compute the next state of the contract and the balance delta for the account
        making the withdrawl.
        """
        with self.set_state(state):
            assert cp_tokens_to_withdraw <= self.minted_cp_tokens, "Withdrawl amount too large"

            required_reserve_asset_fraction = self.required_reserve_asset_fraction
            total_to_withdraw_in_reserve_asset = (
                cp_tokens_to_withdraw /
                self.cp_tokens_per_reserve_asset
            )
            reserve_assets_to_withdraw = (
                required_reserve_asset_fraction *
                total_to_withdraw_in_reserve_asset
            )
            stable_assets_to_withdraw = (
                (total_to_withdraw_in_reserve_asset - reserve_assets_to_withdraw) *
                self.reserve_to_stable_rate
            )

            next_state = CollateralProviderState(
                stable_bucket=self.stable_bucket - stable_assets_to_withdraw,
                reserve_asset_bucket=self.reserve_asset_bucket - reserve_assets_to_withdraw,
                minted_cp_tokens=self.minted_cp_tokens - cp_tokens_to_withdraw
            )

            account_delta = Balance({
                self.stable: stable_assets_to_withdraw,
                self.reserve_asset: reserve_assets_to_withdraw,
                self.cp_token: -1 * cp_tokens_to_withdraw
            })
            return (next_state, account_delta)
    
    @with_state
    def cp_tokens_to_mint(
        self,
        total_to_deposit_in_reserve_asset: float
    ) -> float:
        if self.minted_cp_tokens == 0:
            return total_to_deposit_in_reserve_asset
        return self.cp_tokens_per_reserve_asset * total_to_deposit_in_reserve_asset

    @functools.cached_property
    def pair(self) -> Pair:
        return Pair(self.reserve_asset, self.stable)

    @property
    @with_state
    def minted_cp_tokens(self) -> float:
        return self.__state__['minted_cp_tokens']

    @property
    @with_state
    def stable_bucket(self) -> float:
        return self.__state__['stable_bucket']

    @property
    @with_state
    def reserve_asset_bucket(self) -> float:
        return self.__state__['reserve_asset_bucket']

    @property
    @with_state
    def cp_tokens_per_reserve_asset(self) -> float:
        return self.minted_cp_tokens / self.total_value_in_reserve_asset

    @property
    @with_state
    def required_reserve_asset_fraction(self) -> float:
        if self.minted_cp_tokens == 0:
            return 1
        return self.reserve_asset_bucket / self.total_value_in_reserve_asset

    @property
    @with_state
    def total_value_in_reserve_asset(self) -> float:
        return (
            self.reserve_asset_bucket +
            self.stable_bucket * self.stable_to_reserve_rate
        )

    @property
    @with_state
    def stable_to_reserve_rate(self) -> float:
        return 1 / self.reserve_to_stable_rate

    @property
    @with_state
    def reserve_to_stable_rate(self) -> float:
        return self.__global_state__['oracle_rate'].get(self.pair)


    @contextmanager
    def set_state(self, state: StateVariables):
        """
        Sets the state of the contract from the simulation state
        for the duration of the execution of some logic:

        ```
        with self.set_state(state):
            # do something here
        ```
        """
        self.__global_state__ = state
        self.__state__ = state.get('collateral_provider', {}).get(
            self.mento_exchange,
            CollateralProviderState(
                stable_bucket=0,
                reserve_asset_bucket=0,
                minted_cp_tokens=0
            ))
        yield self
        self.__global_state__ = None
        self.__state__ = None
