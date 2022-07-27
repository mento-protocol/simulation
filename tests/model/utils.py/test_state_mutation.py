import pytest
from model.state_variables import StateVariables
from model.types.base import CryptoAsset, Stable
from model.types.pair import Pair
from model.utils.state_mutation import StateMutation

CELOCUSD = Pair(CryptoAsset.CELO, Stable.CUSD)
CELOCEUR = Pair(CryptoAsset.CELO, Stable.CEUR)
CELOCREAL = Pair(CryptoAsset.CELO, Stable.CREAL)

class TestStateMutation:
    """
    Tests for the StateMutation utility function
    which allows us to easily define composable
    state mutations
    """

    def test_add_one(self):
        state = StateVariables(
            oracle_rate={
                CELOCUSD: 2,
                CELOCEUR: 2.4
            }
        )

        state_mutation = StateMutation().add(
            ["oracle_rate", CELOCUSD], 4
        )

        next_state = state_mutation.to_diff(state)

        assert next_state["oracle_rate"][CELOCUSD] == 4
        assert next_state["oracle_rate"][CELOCEUR] == 2.4

    def test_add_two(self):
        state = StateVariables(
            oracle_rate={
                CELOCUSD: 2,
                CELOCEUR: 2.4
            }
        )

        state_mutation = StateMutation().add(
            ["oracle_rate", CELOCUSD], 4
        ).add(
            ["oracle_rate", CELOCREAL], 5
        )

        next_state = state_mutation.to_diff(state)

        assert next_state["oracle_rate"][CELOCUSD] == 4
        assert next_state["oracle_rate"][CELOCEUR] == 2.4
        assert next_state["oracle_rate"][CELOCREAL] == 5

    def test_add_conflicting(self):
        state = StateVariables(
            oracle_rate={
                CELOCUSD: 2,
                CELOCEUR: 2.4
            }
        )

        state_mutation = StateMutation().add(
            ["oracle_rate", CELOCUSD], 4
        ).add(
            ["oracle_rate", CELOCUSD], 5
        )

        with pytest.raises(AssertionError, match="StateMutations contains two entries for same path: "):
            next_state = state_mutation.to_diff(state)
    
    def test_combine_mutations(self):
        state = StateVariables(
            oracle_rate={
                CELOCUSD: 2,
                CELOCEUR: 2.4
            }
        )

        mutation1 = StateMutation().add(
            ["oracle_rate", CELOCUSD], 4
        )
        mutation2 = StateMutation().add(
            ["oracle_rate", CELOCREAL], 5
        )



        next_state = (mutation1 + mutation2).to_diff(state)

        assert next_state["oracle_rate"][CELOCUSD] == 4
        assert next_state["oracle_rate"][CELOCEUR] == 2.4
        assert next_state["oracle_rate"][CELOCREAL] == 5

