
import json
import multiprocessing
import os
from pathlib import Path
import queue
import threading

import numpy as np


class ConnectionPolicy():

    # Returns the next available value, blocking if necessary.
    DISCRETE = 0
    # Returns the most recent value, even if it hasn't changed, never blocking.
    CONTINUOUS = 1

    def eval_from_name(name: str) -> int:
        name = name.lower()
        if name == 'discrete':
            return ConnectionPolicy.DISCRETE
        elif name == 'continuous':
            return ConnectionPolicy.CONTINUOUS
        else:
            raise ValueError(f'"{name}" is not a valid connection policy name')

    def name_from_value(value: int) -> str:
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


    def _build(self):
        #self.manager = multiprocessing.Manager()
        self.queue = queue.Queue(maxsize=4)


    def send(self, data: np.array):
        # TODO: IMPLEMENT CONTINUOUS
        self.queue.put(data)


    def request(self) -> np.array or None:
        # TODO: IMPLEMENT CONTINUOUS
        r = self.queue.get()
        return r


    def drain(self) -> np.array or None:
        try:
            while True:
                self.queue.get_nowait()
        except queue.Empty:
            pass


    def post_stop(self):
        try:
            self.queue.put(None, timeout=0.01)
        except queue.Full:
            pass


    def serialize(self, path: Path):
        if not os.path.exists(path):
            os.mkdir(path)
        attributes = self.__dict__.copy()
        if hasattr(self, 'queue'):
            del attributes['queue']
        attributes['policy'] = ConnectionPolicy.name_from_value(attributes['policy'])
        with open(path / 'attributes.json', 'w') as file:
            json.dump(attributes, file)

    def deserialize(path: Path) -> 'Connection':
        with open(path / 'attributes.json', 'r') as file:
            attributes = json.load(file)
        return Connection(**attributes)

