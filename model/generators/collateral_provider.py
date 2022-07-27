"""
Module that handles the collateral provider contract
"""

from typing import Dict, Tuple
from model.entities.account import Account
from model.entities.balance import Balance
from model.state_variables import StateVariables
from model.types.base import CollateralProviderState, MentoExchange
from model.types.configs import MentoExchangeConfig
from model.utils.generator import Generator
from model.entities.collateral_provider_contract import CollateralProviderContract
from model.utils.state_mutation import StateMutation


class CollateralProviderGenerator(Generator):
    contracts: Dict[MentoExchange, CollateralProviderContract]

    def __init__(
        self,
        exchange_configs: Dict[MentoExchange, MentoExchangeConfig]):
        self.contracts = {
            exchange: CollateralProviderContract(exchange, config)
            for (exchange, config) in exchange_configs.itmes()
        }

    def deposit(
        self,
        state: StateVariables,
        exchange: MentoExchange,
        account: Account,
        total_to_deposit_in_reserve_asset: float
    ) -> Tuple[Balance, StateMutation]:
        next_state, account_delta = self.contracts.get(exchange).deposit(state, total_to_deposit_in_reserve_asset)
        account_balance_after_deposit = account.balance + account_delta
        assert (
            not account_balance_after_deposit.any_negative(),
            "Account doesn't have enough balance to deposit"
        )

        # account.balance = account_balance_after_deposit
        return (
            account_delta,
            StateMutation().add(["collateral_provider", exchange], next_state)
        )

    def withdraw(
        self,
        state: StateVariables,
        exchange: MentoExchange,
        account: Account,
        cp_tokens_to_withdraw: float
    ) -> Tuple[Balance, StateMutation]:
        next_state, account_delta = self.contracts.get(exchange).withdraw(state, cp_tokens_to_withdraw)
        account_balance_after_deposit = account.balance + account_delta
        assert (
            not account_balance_after_deposit.any_negative(),
            "Account doesn't have enough balance to deposit"
        )

        # account.balance = account_balance_after_deposit
        return (
            account_delta,
            StateMutation().add(["collateral_provider", exchange], next_state)
        )
