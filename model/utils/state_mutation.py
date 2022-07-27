from copy import copy
from typing import NamedTuple, List, Any, Dict

from model.state_variables import StateVariables

class Mutation(NamedTuple):
    path: List[Any]
    vlaue: Any

class StateMutation():
    """
    Class to manage state updates / mutations
    """

    mutations: List[Mutation]

    def __init__(self, *mutations: List[Mutation]):
        self.mutations = mutations or []
    
    def add(self, path: List[Any], value: Any) -> "StateMutation":
        self.mutations.append(Mutation(path, value))
        return self
    
    def __add__(self, other: "StateMutation") -> "StateMutation":
        return StateMutation(*(self.mutations + other.mutations))
    
    def to_diff(self, state: StateVariables) -> Dict[str, Any]:
        seen_path: Dict[int, bool] = {}
        diff = {}

        for (path, value) in self.mutations:
            path_hash = hash(str(path))
            assert seen_path.get(path_hash) != True, f"StateMutations contains two entries for same path: {path}"
            seen_path[path_hash] = True

            key = path[0]
            diff[key] = diff.get(key, copy(state[key]))
            node = diff
            for key in path[:-1]:
                node = node[key]
            
            node[path[-1]] = value
        return diff
            



