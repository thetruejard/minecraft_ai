
import inspect
import json
import multiprocessing
import os
from pathlib import Path
from unittest.mock import NonCallableMagicMock
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

    def _serialize(self, path: Path):
        return {
            '_num_inputs': self._num_inputs,
            '_num_outputs': self._num_outputs,
            'attributes': self.serialize()
        }

    def _deserialize(self, config: dict, path: Path):
        self._num_inputs = config['_num_inputs']
        self._num_outputs = config['_num_outputs']
        self.deserialize(config['attributes'])

    def _build(self):
        self.build()


    def build(self):
        pass

    def run(self, inputs: list):
        raise NotImplementedError()

    def serialize(self) -> dict:
        return dict()

    def deserialize(self, config: dict):
        pass



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
        while self._keep_running:
            inputs = [self.parent_model.connections[c].request() for c in self.input_connections]
            outputs = self.process_obj.run(inputs)
            for c, data in zip(self.output_connections, outputs):
                self.parent_model.connections[c].send(data)


    def start(self):
        '''
        Start running the process.
        '''
        if self.subprocess is not None:
            raise ProcessException('Process is already running')
        self._keep_running = True
        self.subprocess = multiprocessing.Process(target=self._run, name=self.name)


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
        self.subprocess.join()
        self.subprocess = None



    def serialize(self, path: Path):
        if not os.path.exists(path):
            os.mkdir(path)
        attributes = self.__dict__.copy()
        del attributes['parent_model']
        del attributes['subprocess']
        del attributes['process_obj']
        attributes['process_obj_name'] = self.process_obj.__class__.__qualname__
        attributes['process_obj_path'] = utils.serialize_class(self.process_obj.__class__)
        attributes['process_obj_data'] = self.process_obj._serialize(path)
        with open(path / 'attributes.json', 'w') as file:
            json.dump(attributes, file)


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
        return self
