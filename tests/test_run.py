"""
Test that runs the experiment as a sanity check
"""

import pytest
from experiments.run import run


@pytest.mark.slow
def test_run():
    """
    Check that the model run() method completes
    """

    _results, _exceptions = run()
    assert True
