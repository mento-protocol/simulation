"""
Strategy: Random Trader
"""
from typing import List
from cvxpy import Variable
import numpy as np

from experiments import simulation_configuration

from model.entities.strategies.trader_strategy import TraderStrategy, TradingRegime
from model.types.order import Order


class RandomTrading(TraderStrategy):
    """
    Random Trading
    """
    order_list: List[Order]

    def __init__(self, parent, acting_frequency=1):
        # The following is used to define the strategy and needs to be provided in subclass
        super().__init__(parent, acting_frequency)
        self.rng = parent.rngp.get_rng("RandomTrader", self.parent.account_id)
        self.order_list = self.generate_sell_amounts()

    def sell_reserve_asset(self, _params, prev_state):
        return self.order_list["sell_reserve_asset"][prev_state["timestep"]]

    def define_variables(self):
        self.variables["sell_amount"] = Variable(pos=True)

    def define_expressions(self, params, prev_state):
        """
        Defines and returns the expressions (made of variables and parameters)
        that are used in the optimization
        """

    def define_objective_function(self, _params, _prev_state):
        """
        Defines and returns the cvxpy objective_function
        """
        self.objective_function = self.variables["sell_amount"]
        self.optimization_direction = "maximize"

    def define_constraints(self, params, prev_state):
        """
        Defines and returns the constraints under which the optimization is conducted
        """
        self.constraints = []
        # TODO: Get budget based on account
        max_budget_stable = self.parent.balance.get(self.stable)
        max_budget_reserve_asset = self.parent.balance.get(self.reserve_asset)
        if self.sell_reserve_asset(params, prev_state):
            self.constraints.append(
                self.variables["sell_amount"]
                <= min(
                    max_budget_reserve_asset,
                    self.order_list["sell_amount"][prev_state["timestep"]]
                )
            )
        else:
            self.constraints.append(
                self.variables["sell_amount"]
                <= min(
                    max_budget_stable,
                    self.order_list["sell_amount"][prev_state["timestep"]]
                )
            )

    def determine_trading_regime(self, prev_state) -> TradingRegime:
        """
        Indicates how the trader will act depending on the relation of mento price
        and market price
        """
        sell_reserve_asset = self.order_list[
            'sell_reserve_asset'][prev_state['timestep']]
        regime = TradingRegime.PASS
        if sell_reserve_asset:
            regime = TradingRegime.SELL_RESERVE_ASSET
        elif not sell_reserve_asset:
            regime = TradingRegime.SELL_STABLE
        return regime

    def generate_sell_amounts(
        self,
    ):
        """
        This function generates lognormal returns
        """
        sample_size = simulation_configuration.TOTAL_BLOCKS + 1

        sell_reserve_asset = (self.rng.binomial(1, 0.5, sample_size) == 1)
        sell_amount = np.abs(self.rng.normal(1000, 0, size=sample_size))

        orders = {"sell_reserve_asset": sell_reserve_asset,
                  "sell_amount": sell_amount}
        return orders

    def calculate(self, _params, prev_state):
        """
        Calculates optimal trade if analytical solution is available
        """
        sell_amounts = self.order_list["sell_amount"]
        order_directions = self.order_list["sell_reserve_asset"]
        self.order.sell_amount = sell_amounts[prev_state["timestep"]]
        self.order.sell_reserve_asset = order_directions[prev_state["timestep"]]
