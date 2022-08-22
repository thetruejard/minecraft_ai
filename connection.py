
import json
import numpy as np
import os
from pathlib import Path


class ConnectionPolicy():

    # Returns the next available value, blocking if necessary.
    DISCRETE = 0
    # Returns the most recent value, even if it hasn't changed, never blocking.
    CONTINUOUS = 1

    def eval_from_name(name: str):
        name = name.lower()
        if name == 'discrete':
            return ConnectionPolicy.DISCRETE
        elif name == 'continuous':
            return ConnectionPolicy.CONTINUOUS
        else:
            raise ValueError(f'"{name}" is not a valid connection policy name')

    def name_from_value(value: int):
        if value == ConnectionPolicy.DISCRETE:
            return 'discrete'
        elif value == ConnectionPolicy.CONTINUOUS:
            return 'continuous'
        else:
            raise ValueError(f'Unknown ConnectionPolicy value: {value}')



class Connection():
    '''
    A Connection object, counterintuitively, does not actually track any inputs and outputs.
    Rather, it acts as more of a server node where Processes deliver and request data.
    The Process objects track which Connection nodes to use as inputs and outputs.
    Use send() to deliver data (for outputs) and request() to request data (for inputs).
    '''


    def __init__(self,
        connection_id: int,
        policy: str,
        name: str='connection'
    ):
        self.connection_id = connection_id
        self.policy = ConnectionPolicy.eval_from_name(policy)
        self.name = name


    def send(data: np.array):
        pass

    def request() -> np.array or None:
        pass


    def serialize(self, path: Path):
        if not os.path.exists(path):
            os.mkdir(path)
        attributes = self.__dict__.copy()
        attributes['policy'] = ConnectionPolicy.name_from_value(attributes['policy'])
        with open(path / 'attributes.json', 'w') as file:
            json.dump(attributes, file)

    def deserialize(path: Path):
        with open(path / 'attributes.json', 'r') as file:
            attributes = json.load(file)
        return Connection(**attributes)

