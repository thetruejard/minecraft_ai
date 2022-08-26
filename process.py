
import json
import multiprocessing
import threading
import os
from pathlib import Path
import time
from typing import Any

import torch

from connection import Connection
from model import Model
import utils



class ProcessException(Exception):
    pass



class Process():
    '''
    A Process is a set of model components that run in their own multiprocessing thread.
    It typically contains a full abstraction layer (controls, logic, etc.)
    Time-sensitive operations, such as screen grabbing, may also run in their own Process.
    The constructor must have ALL default args. State must be able to come from deserialization.
    '''

    def __init__(self, num_inputs: int, num_outputs: int):
        self._num_inputs = num_inputs
        self._num_outputs = num_outputs
        self._time_step_last = 0
        self._time_step_elapsed = 0
        self._models_from_disk = False
        # Only used while loading from disk, helps match models to names. See add_model().
        self._model_names = []
        # self.models is a dict owned by its container, assigned in ProcessContainer.__init__().
        self._models = None
        self._properties = {}

    def _build(self):
        self.build()

    def _start(self):
        '''Called right before the first call to _run()'''
        self._time_step_last = time.perf_counter()
        self._time_step_elapsed = 0
        self.start()

    def _run(self, inputs: list):
        r = self.run(inputs)
        now = time.perf_counter()
        self._time_step_elapsed = now - self._time_step_last
        self._time_step_last = now
        return r

    def _serialize(self, path: Path):
        # Models are de/serialized in ProcessContainer.
        return {
            '_num_inputs': self._num_inputs,
            '_num_outputs': self._num_outputs,
            'attributes': self.serialize(path)
        }

    def _deserialize(self, config: dict, path: Path):
        self._num_inputs = config['_num_inputs']
        self._num_outputs = config['_num_outputs']
        self.deserialize(config['attributes'], path)


    def time_step(self):
        return self._time_step_elapsed

    def add_model(self,
        model_type: type[Model],
        optimizer_type: type[torch.optim.Optimizer],
        name: str='model',
        type_args: dict={},
        optimizer_args: dict={}
    ):
        # Two modes, depending on whether this is brand new, or loaded from disk.
        if self._models_from_disk:
            # Try to match with an existing model.
            model_candidates = [m for m in self._models.values() if type(m) is model_type]
            model_candidates = [m for m in model_candidates if m.name not in self._model_names]
            name_candidates = [m.name for m in model_candidates]
            if not name_candidates:
                raise ProcessException(
                    f'Could not match model "{name}" with any existing model from disk'
                )
            for i, n in enumerate(utils.name_generator(name)):
                if n in name_candidates:
                    m = model_candidates[name_candidates.index(n)]
                    break
                if i >= len(self._models):
                    raise ProcessException(
                        f'Could not match model "{name}" with any existing model from disk'
                    )
            self._model_names.append(m.name)
            return m
        else:
            # This is brand new, so construct a new model from scratch.
            if not issubclass(model_type, Model):
                raise TypeError(f'{model_type.__name__} is not a subclass of Model')
            m = model_type(**type_args)
            m.model_id = utils.create_new_id(self._models.keys())
            m.name = utils.create_new_name(name, self._models.values())
            m.optimizer = optimizer_type(m.parameters(), **optimizer_args)
            self._models[m.model_id] = m
            return m

    def set_property(self, name: str, value: Any):
        self._properties[name] = value



    def build(self):
        pass

    def start(self):
        pass

    def run(self, inputs: list):
        raise NotImplementedError()

    def serialize(self, path: Path) -> dict:
        return dict()

    def deserialize(self, config: dict, path: Path):
        pass
        


def _run(self):
    self.process_obj._start()
    while self._keep_running:
        inputs = [None] * len(self.input_connections)
        for i, c in enumerate(self.input_connections):
            x = self.parent_model.connections[c].request()
            if x is None:
                # Signal stoppage by changing length of inputs.
                inputs = []
            else:
                inputs[i] = x
        if len(inputs) != len(self.input_connections):
            continue
        outputs = self.process_obj._run(inputs)
        for c, data in zip(self.output_connections, outputs):
            self.parent_model.connections[c].send(data)


class ProcessContainer():
    '''
    A ProcessContainer is a wrapper around a Process subclass. While Process handles the
    functionality, ProcessContainer takes care of parallelization, serialization, etc.
    '''

    class InputReference():
        def __init__(self, process_id, input_index):
            self.process_id = process_id
            self.input_index = input_index

    class OutputReference():
        def __init__(self, process_id, output_index):
            self.process_id = process_id
            self.output_index = output_index



    def __init__(self,
        parent_model: 'MinecraftAI',
        process_id: int,
        process_type: type,
        name: str='process',
        type_args: dict={}
    ):
        self.parent_model = parent_model
        self.process_id = process_id
        if isinstance(process_type, Process) or not issubclass(process_type, Process):
            raise TypeError(f'process_type must be a subclass of Process; ' + \
                f'"{process_type.__name__}" is not')
        self.process_obj = process_type(**type_args)
        self.name = name
        self.subprocess = None
        self._keep_running = False
        self.input_connections = []
        self.output_connections = []
        self.models = {}
        self.process_obj._models = self.models



    def connect(self,
        *args,
        policy: str or list[str]=None,
        names: list[str]=None
    ) -> 'ProcessContainer.OutputReference' or list['ProcessContainer.OutputReference']:
        '''
        Specify the inputs and evaluation policy of this process.
        Inputs should be references to outputs of another process as returned by outputs().
        Returns a list of output references for this process.
        If unspecified, the evaluation policy defaults to 'discrete' for all inputs.
        To specify per-input evaluation policies, pass a list of policy names.
        '''
        if any(not isinstance(a, ProcessContainer.OutputReference) for a in args):
            raise TypeError('All inputs must be references to outputs of ' + \
                'another process as returned by connect()')
        if len(args) == 0 and policy is not None:
            raise ValueError('Cannot specify input policy without specifying inputs')

        if policy is None:
            policy = ['discrete'] * len(args)
        elif type(policy) is list:
            if len(policy) != len(args):
                raise ValueError('Number of evaluation policies must match number of inputs')
        else:
            policy = [policy] * len(args)

        if names is None:
            names = ['connection' for a in args]
        elif len(names) != len(args):
            raise ValueError('Number of names must match number of inputs')

        for i, output in enumerate(args):
            this_input = ProcessContainer.InputReference(self.process_id, i)
            self.parent_model.add_connection(
                output=output,
                input=this_input,
                policy=policy[i],
                name=names[i]
            )
        if self.process_obj._num_outputs == 1:
            return ProcessContainer.OutputReference(self.process_id, 0)
        else:
            return tuple(ProcessContainer.OutputReference(self.process_id, i)
                for i in range(self.process_obj._num_outputs))
        


    def connect_input(self, connection_id: int, input_reference: InputReference):
        if self.process_id != input_reference.process_id:
            raise ValueError('Process ID mismatch: cannot connect input reference with ' + \
                f'process_id={input_reference.process_id} to process {self.process_id}')
        if len(self.input_connections) == 0:
            self.input_connections = [-1] * self.process_obj._num_inputs
        elif len(self.input_connections) != self.process_obj._num_inputs:
            raise ProcessException('ProcessContainer connections length does not match ' + \
                'process_obj._num_inputs')
        self.input_connections[input_reference.input_index] = connection_id



    def connect_output(self, connection_id: int, output_reference: OutputReference):
        if self.process_id != output_reference.process_id:
            raise ValueError('Process ID mismatch: cannot connect output reference with ' + \
                f'process_id={output_reference.process_id} to process {self.process_id}')
        if len(self.output_connections) == 0:
            self.output_connections = [-1] * self.process_obj._num_outputs
        elif len(self.output_connections) != self.process_obj._num_outputs:
            raise ProcessException('ProcessContainer connections length does not match ' + \
                'process_obj._num_inputs')
        self.output_connections[output_reference.output_index] = connection_id
            

    def _build(self):
        if self.process_obj is not None:
            self.process_obj._build()


    def _run(self):
        self.process_obj._start()
        while self._keep_running:
            inputs = [None] * len(self.input_connections)
            for c, i in enumerate(self.input_connections):
                x = self.parent_model.connections[c].request()
                if x is None:
                    inputs = None
                    break
                inputs[i] = x
            if inputs is None:
                continue
            outputs = self.process_obj._run(inputs)
            for c, data in zip(self.output_connections, outputs):
                self.parent_model.connections[c].send(data)


    def start(self):
        '''
        Start running the process.
        '''
        if self.subprocess is not None:
            raise ProcessException('Process is already running')
        self._keep_running = True
        self.subprocess = threading.Thread(target=_run, name=self.name, args=(self,))
        self.subprocess.start()


    def stop(self):
        '''
        Tell the process to stop running.
        Does NOT wait for the process to actually stop. See self.join().
        '''
        self._keep_running = False


    def join(self):
        '''
        Stops the process if it hasn't stopped already.
        Waits for it to finish stopping before returning.
        '''
        self._keep_running = False
        for conn in self.parent_model.connections.values():
            conn.drain()
        while self.subprocess.is_alive():
            for conn in self.parent_model.connections.values():
                conn.post_stop()
            self.subprocess.join(0.1)
        self.subprocess = None


    def get_properties(self):
        return self.process_obj._properties



    def serialize(self, path: Path):
        if not os.path.exists(path):
            os.mkdir(path)
        attributes = {
            'process_id': self.process_id,
            'name': self.name,
            'input_connections': self.input_connections,
            'output_connections': self.output_connections,
            'process_obj_name': self.process_obj.__class__.__qualname__,
            'process_obj_path': utils.serialize_class(self.process_obj.__class__),
            'process_obj_data': self.process_obj._serialize(path)
        }
        with open(path / 'attributes.json', 'w') as file:
            json.dump(attributes, file)

        if len(self.models) > 0:
            models_path = path / 'models'
            if not os.path.exists(models_path):
                os.mkdir(models_path)
            for model in self.models.values():
                model_data = {
                    'id': model.model_id,
                    'name': model.name,
                    'model': model.state_dict(),
                    'optimizer': model.optimizer.state_dict(),
                    'type': utils.serialize_class(model.__class__),
                    'optimizer_type': utils.name_from_optimizer(model.optimizer.__class__),
                    'config': model.serialize()
                }
                torch.save(model_data, models_path / f'{model.model_id}.pt')



    def deserialize(
        path: Path,
        parent_model: 'MinecraftAI',
        custom_objects: dict={}
    ) -> 'ProcessContainer':
        with open(path / 'attributes.json', 'r') as file:
            attributes = json.load(file)
        if attributes['process_obj_name'] in custom_objects.keys():
            process_type = custom_objects[attributes['process_obj_name']]
        else:
            process_type=utils.deserialize_class(attributes['process_obj_path'])
        self = ProcessContainer(
            parent_model=parent_model,
            process_id=attributes['process_id'],
            process_type=process_type,
            name=attributes['name'],
            type_args={}
        )
        process_obj_data = attributes.pop('process_obj_data')
        del attributes['process_obj_name']
        del attributes['process_obj_path']
        for name, value in attributes.items():
            setattr(self, name, value)
        self.process_obj._deserialize(process_obj_data, path)

        models_path = path / 'models'
        if os.path.exists(models_path):
            for model_file in os.listdir(models_path):
                model_data = torch.load(models_path / model_file)
                model = utils.deserialize_class(model_data['type'])()
                model.model_id = model_data['id']
                model.name = model_data['name']
                model.deserialize(model_data['config'])
                model.load_state_dict(model_data['model'])
                model.optimizer = utils.optimizer_from_name(model_data['optimizer_type'])\
                    (model.parameters())
                model.optimizer.load_state_dict(model_data['optimizer'])
                self.models[model.model_id] = model
            if len(self.models) > 0:
                self._models_from_disk = True
        return self
