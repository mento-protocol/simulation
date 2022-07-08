# pylint: disable=missing-function-docstring,no-self-use,missing-module-docstring
import pytest
from model.entities.collateral_provider_contract import (
    CollateralProviderContract,
    CollateralProviderState
)
from model.state_variables import StateVariables
from model.types.base import MentoExchange, CryptoAsset, Stable, Fiat, Token
from model.types.configs import MentoExchangeConfig
from model.types.pair import Pair

def setup_contract():
    return CollateralProviderContract(
        MentoExchange.CUSD_CELO,
        MentoExchangeConfig(
            reserve_asset=CryptoAsset.CELO,
            stable=Stable.CUSD,
            reference_fiat=Fiat.USD,
            reserve_fraction=0.1,
            spread=0.0025,
            bucket_update_frequency_second=5*60,
            max_sell_fraction_of_float=0.0001
        )
    )


class TestCollateralProviderContract:
    """
    CollateralProviderContract tests
    """
    def test_first_deposit(self):
        contract = setup_contract()
        state = StateVariables(
            oracle_rate={
                Pair(CryptoAsset.CELO, Stable.CUSD): 2
            }
        )

        (next_state, account_delta) = contract.deposit(state, 1000)
        assert next_state['minted_cp_tokens'] == 1000
        assert next_state['reserve_asset_bucket'] == 1000
        assert next_state['stable_bucket'] == 0
        assert account_delta[Token.CP] == 1000
        assert account_delta[CryptoAsset.CELO] == -1000

    def test_deposit_when_only_reserve_asset_in_contract(self):
        contract = setup_contract()
        state = StateVariables(
            collateral_provider={
                MentoExchange.CUSD_CELO: CollateralProviderState(
                    stable_bucket=0,
                    reserve_asset_bucket=1000,
                    minted_cp_tokens=1000
                )
            },
            oracle_rate={
                Pair(CryptoAsset.CELO, Stable.CUSD): 2
            }
        )

        (next_state, account_delta) = contract.deposit(state, 500)
        assert next_state['minted_cp_tokens'] == 1500
        assert next_state['reserve_asset_bucket'] == 1500
        assert next_state['stable_bucket'] == 0
        assert account_delta[Token.CP] == 500
        assert account_delta[CryptoAsset.CELO] == -500

    def test_deposit_when_only_stable_asset_in_contract(self):
        contract = setup_contract()
        state = StateVariables(
            collateral_provider={
                MentoExchange.CUSD_CELO: CollateralProviderState(
                    stable_bucket=2000,
                    reserve_asset_bucket=0,
                    minted_cp_tokens=1000
                )
            },
            oracle_rate={
                Pair(CryptoAsset.CELO, Stable.CUSD): 2
            }
        )

        (next_state, account_delta) = contract.deposit(state, 500)
        assert next_state['minted_cp_tokens'] == 1500
        assert next_state['reserve_asset_bucket'] == 0
        assert next_state['stable_bucket'] == 3000
        assert account_delta[Token.CP] == 500
        assert account_delta[Stable.CUSD] == -1000

    def test_deposit_when_assets_in_contract(self):
        contract = setup_contract()
        state = StateVariables(
            collateral_provider={
                MentoExchange.CUSD_CELO: CollateralProviderState(
                    stable_bucket=1500,
                    reserve_asset_bucket=500,
                    minted_cp_tokens=1500
                )
            },
            oracle_rate={
                Pair(CryptoAsset.CELO, Stable.CUSD): 2
            }
        )

        (next_state, account_delta) = contract.deposit(state, 1000)
        assert next_state['minted_cp_tokens'] == 2700
        assert next_state['reserve_asset_bucket'] == 900
        assert next_state['stable_bucket'] == 2700
        assert account_delta[Token.CP] == 1200
        assert account_delta[Stable.CUSD] == -1200
        assert account_delta[CryptoAsset.CELO] == -400

    def test_withdraw_to_large(self):
        contract = setup_contract()
        state = StateVariables(
            collateral_provider={
                MentoExchange.CUSD_CELO: CollateralProviderState(
                    stable_bucket=1500,
                    reserve_asset_bucket=500,
                    minted_cp_tokens=1500
                )
            },
            oracle_rate={
                Pair(CryptoAsset.CELO, Stable.CUSD): 2
            }
        )

        with pytest.raises(AssertionError, match="Withdrawl amount too large"):
            contract.withdraw(state, 2000)

    def test_withdraw_when_only_reserve_asset(self):
        contract = setup_contract()
        state = StateVariables(
            collateral_provider={
                MentoExchange.CUSD_CELO: CollateralProviderState(
                    stable_bucket=0,
                    reserve_asset_bucket=3000,
                    minted_cp_tokens=2000,
                )
            },
            oracle_rate={
                Pair(CryptoAsset.CELO, Stable.CUSD): 2
            }
        )

        (next_state, account_delta) = contract.withdraw(state, 1000)
        assert next_state['minted_cp_tokens'] == 1000
        assert next_state['stable_bucket'] == 0
        assert next_state['reserve_asset_bucket'] == 1500
        assert account_delta[CryptoAsset.CELO] == 1500
        assert account_delta[Stable.CUSD] == 0
        assert account_delta[Token.CP] == -1000

    def test_withdraw_when_only_stable_asset(self):
        contract = setup_contract()
        state = StateVariables(
            collateral_provider={
                MentoExchange.CUSD_CELO: CollateralProviderState(
                    stable_bucket=3000,
                    reserve_asset_bucket=0,
                    minted_cp_tokens=2000,
                )
            },
            oracle_rate={
                Pair(CryptoAsset.CELO, Stable.CUSD): 2
            }
        )

        (next_state, account_delta) = contract.withdraw(state, 1000)
        assert next_state['minted_cp_tokens'] == 1000
        assert next_state['stable_bucket'] == 1500
        assert next_state['reserve_asset_bucket'] == 0
        assert account_delta[CryptoAsset.CELO] == 0
        assert account_delta[Stable.CUSD] == 1500
        assert account_delta[Token.CP] == -1000

    def test_withdraw(self):
        contract = setup_contract()
        state = StateVariables(
            collateral_provider={
                MentoExchange.CUSD_CELO: CollateralProviderState(
                    stable_bucket=3000,
                    reserve_asset_bucket=1000,
                    minted_cp_tokens=2000,
                )
            },
            oracle_rate={
                Pair(CryptoAsset.CELO, Stable.CUSD): 2
            }
        )

        (next_state, account_delta) = contract.withdraw(state, 1000)
        assert next_state['minted_cp_tokens'] == 1000
        assert next_state['stable_bucket'] == 1500
        assert next_state['reserve_asset_bucket'] == 500
        assert account_delta[CryptoAsset.CELO] == 500
        assert account_delta[Stable.CUSD] == 1500
        assert account_delta[Token.CP] == -1000
