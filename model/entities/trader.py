"""
Agents extends accounts to implement behavior via strategies.
Agents implement the Actor type.
"""
# pylint: disable=too-few-public-methods
from typing import TYPE_CHECKING
from copy import copy, deepcopy
from uuid import UUID

from model.generators.mento import MentoExchangeGenerator
from model.entities import strategies
from model.entities.account import Account, Balance
from model.state_variables import StateVariables
from model.types.pair import Pair
from model.types.configs import MentoExchangeConfig, TraderConfig
from model.utils.rng_provider import RNGProvider

if TYPE_CHECKING:
    from model.generators.accounts import AccountGenerator


class Trader(Account):
    """
    The Trader extens an account with a trading strategy.
    """
    strategy: strategies.TraderStrategy
    config: TraderConfig
    exchange_config: MentoExchangeConfig
    mento: MentoExchangeGenerator
    rngp: RNGProvider

    def __init__(
        self,
        parent: "AccountGenerator",
        account_id: UUID,
        account_name: str,
        config: TraderConfig,
        rngp: RNGProvider
    ):
        super().__init__(parent, account_id, account_name, config.balance)
        self.rngp = rngp
        self.mento = self.parent.container.get(MentoExchangeGenerator)
        self.config = config
        self.exchange_config = self.mento.configs.get(self.config.exchange)

        strategy_class = getattr(strategies, config.trader_type.value)
        assert strategy_class is not None, f"{config.trader_type.value} is not a strategy"
        self.strategy = strategy_class(self)

    def execute(
        self,
        params,
        state: StateVariables,
    ):
        """
        Execute the agent's state change
        """
        order = self.strategy.return_optimal_trade(params, state)
        if order is None:
            return {
                "mento_buckets": state["mento_buckets"],
                "floating_supply": state["floating_supply"],
                "reserve_balance": state["reserve_balance"],
                "collateral_provider": state["collateral_provider"],
            }

        sell_amount = order["sell_amount"]
        sell_reserve_asset = order["sell_reserve_asset"]
        self.rebalance_portfolio(sell_amount, sell_reserve_asset, state)

        account_delta, reserve_delta, state_mutation = self.mento.exchange(
            self.config.exchange,
            sell_amount,
            sell_reserve_asset,
            state
        )

        self.balance += account_delta
        self.parent.reserve.balance += reserve_delta

        state_mutation.add(
            ["floating_supply"], self.parent.floating_supply
        ).add(
            ["reserve_balance"], self.parent.reserve.balance
        )

        return state_mutation.to_diff(state)

    def rebalance_portfolio(self, target_amount, target_is_reserve_asset, prev_state):
        """
        Sometimes the optimal trade might require selling more of an
        asset than the trader has in his portfolio, but the total
        value of the portfolio would cover it therefore they can
        rebalance and execute the trade.
        """
        reserve_asset = self.exchange_config.reserve_asset
        stable = self.exchange_config.stable
        reference_fiat = self.exchange_config.reference_fiat

        # TODO: Should these be quoted in the specific
        # fiat of the stable?
        market_price = (
            prev_state["market_price"].get(Pair(reserve_asset, reference_fiat))
            / prev_state["market_price"].get(Pair(stable, reference_fiat))
        )

        delta = Balance.zero()
        if target_is_reserve_asset and self.balance.get(reserve_asset) < target_amount:
            delta[stable] = -1 * self.balance.get(stable)
            delta[reserve_asset] = self.balance.get(stable) / market_price
        elif (not target_is_reserve_asset) and self.balance.get(stable) < target_amount:
            delta[stable] = self.balance.get(reserve_asset) * market_price
            delta[reserve_asset] = -1 * self.balance.get(reserve_asset)

        self.balance += delta
        self.parent.untracked_floating_supply -= delta
