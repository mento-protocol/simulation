"""
python replication to debug the mento notebook
"""
# Import the setup module:
# * sets up the Python path
# * runs shared notebook-configuration methods, such as loading IPython modules
# import setup
import sys
import copy
from pprint import pprint

# import needed for initialization to avoid circular import later
from model import constants # pylint: disable=unused-import
from experiments import default_experiment
from experiments.run import run
sys.path.append("../..")
sys.path.append("../../..")

simulation_analysis_1 = copy.deepcopy(default_experiment.experiment.simulations[0])

simulation_analysis_1.model.params.update({
    "reserve_fraction": [0.001, 0.01],
})

pprint(simulation_analysis_1.model.initial_state)

pprint(simulation_analysis_1.model.params)

df, exceptions = run(simulation_analysis_1)
