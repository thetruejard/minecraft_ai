
import itertools
from itertools import filterfalse
import json
import os
from pathlib import Path
from tabnanny import process_tokens

import config
from connection import Connection
from process import Process, ProcessContainer



class MinecraftAI():
    

    def __init__(self,
        name: str='MinecraftAI'
    ):
        self.name = name
        self.processes = {}
        self.connections = {}
        
        self.total_running_time = 0
        self.total_training_time = 0



    def _create_process_name(self, base_name):
        if not any(p.name == base_name for p in self.processes.values()):
            return base_name
        i = 0
        while True:
            n = base_name + '_' + str(i)
            if not any(p.name == n for p in self.processes.values()):
                return n
            i += 1

    def _create_connection_name(self, base_name):
        if not any(c.name == base_name for c in self.connections.values()):
            return base_name
        i = 0
        while True:
            n = base_name + '_' + str(i)
            if not any(c.name == n for c in self.connections.values()):
                return n
            i += 1

    def _create_process_id(self):
        return next(filterfalse(self.processes.keys().__contains__, itertools.count(1)))

    def _create_connection_id(self):
        return next(filterfalse(self.connections.keys().__contains__, itertools.count(1)))


    
    def add_process(self,
        process: type[Process] or callable,
        name: str='',
        type_args: dict={},
        num_outputs: int=None
    ) -> ProcessContainer:
        '''
        Adds a new Process to this model.
        process must either be a subclass of Process or a function.
        If using a subclass of Process, pass the type itself, not an instance.
        type_args are the arguments used for instantiation. Only used if process is a class.
        num_outputs is the number of outputs. Only used if process is a function.
        '''
        if False:#callable(process):
            proc_arg = dict(process_func=process)
        elif type(process) is type and issubclass(process, Process):
            proc_arg = dict(process_type=process)
        else:
            raise TypeError('process must be a function or a subclass of Process')
        if not name:
            name == process.__name__
        name = self._create_process_name(name)
        new_proc_id = self._create_process_id()
        self.processes[new_proc_id] = ProcessContainer(
            parent_model=self,
            process_id=new_proc_id,
            **proc_arg,
            name=name,
            type_args=type_args
        )
        return self.processes[new_proc_id]



    def add_connection(self,
        output: ProcessContainer.OutputReference,
        input: ProcessContainer.InputReference,
        policy: str='discrete',
        name: str='connection'
    ):
        '''
        Adds a connection to this model from the given output to the given input.
        Input and output references can be acquired by calling inputs() and outputs() on
        the process returned by add_process().
        '''
        name = self._create_connection_name(name)
        new_conn_id = self._create_connection_id()
        self.connections[new_conn_id] = Connection(
            connection_id=new_conn_id,
            policy=policy,
            name=name
        )
        self.processes[output.process_id].connect_output(new_conn_id, output)
        self.processes[input.process_id].connect_input(new_conn_id, input)




    def start(self,
        allow_training: bool=True
    ):
        '''
        Launch all processes and start running the model.
        '''
        for proc in self.processes:
            pass



    def save(self, path: Path, verbose: bool=True):
        '''
        Saves the model to a given directory.
        If the path does not exist, it will be created.
        '''
        if type(path) is str:
            path = Path(path)
        path = path.resolve()
        if not os.path.exists(path):
            os.makedirs(path)
        elif not path.is_dir():
            raise FileExistsError(f'A file "{path}" already exists')

        # Generate and save config file.
        _config = {
            'attributes': {
                'name': self.name,
                'total_running_time': self.total_running_time,
                'total_training_time': self.total_training_time,
            }
        }
        _config.update((c, config.get_config(c)) for c in [
            'VERSION',
            'CONTROLS_WINDOW_WIDTH',
            'CONTROLS_WINDOW_HEIGHT',
        ])
        with open(path / 'config.json', 'w') as file:
            json.dump(_config, file)

        # Save Processes.
        processes_dir = path / 'processes'
        if not os.path.exists(processes_dir):
            os.mkdir(processes_dir)
        for proc in self.processes.values():
            proc.serialize(processes_dir / str(proc.process_id))

        # Save Connections.
        connections_dir = path / 'connections'
        if not os.path.exists(connections_dir):
            os.mkdir(connections_dir)
        for conn in self.connections.values():
            conn.serialize(connections_dir / str(conn.connection_id))



    def load(path: Path, verbose: bool=True):
        '''
        Loads a model from the given directory.
        '''
        self = MinecraftAI()
        if type(path) is str:
            path = Path(path)
        path = path.resolve()
        if not os.path.exists(path):
            raise FileNotFoundError(f'Could not find path "{path}"')
        elif not path.is_dir():
            raise FileExistsError(f'"{path}" is a file, not a directory')
        
        # Load config file.
        with open(path / 'config.json') as file:
            _config = json.load(file)
        # Always compare the version first.
        if _config['VERSION'] != config.VERSION:
            # TODO: Allow attempting to run it anyway?
            raise Exception(f'The model version "{_config["VERSION"]}"' + \
                f'does not match the code version "{config.VERSION}"')
        # Retrieve model attributes.
        for name, value in _config['attributes'].items():
            setattr(self, name, value)
        del _config['attributes']
        # Push the rest to config.
        failed_config = {}
        overwritten_config = {}
        for name, value in _config.items():
            try:
                if config.set_config(name, value):
                    overwritten_config[name] = value
            except KeyError as e:
                failed_config[name] = value
        if verbose:
            if failed_config:
                print('The following extraneous properties were NOT used:')
                for k, v in failed_config.items():
                    print(f'\t{k}: {v}')
            if overwritten_config:
                print('The following properties were overwritten by the model configuration:')
                for k, v in overwritten_config.items():
                    print(f'\t{k}: {v}')

        # Load Processes.
        processes_dir = path / 'processes'
        for proc_id_str in os.listdir(processes_dir):
            self.processes[int(proc_id_str)] = ProcessContainer.deserialize(
                path=processes_dir / proc_id_str,
                parent_model=self
            )

        # Load Connections.
        connections_dir = path / 'connections'
        for conn_id_str in os.listdir(connections_dir):
            self.connections[int(conn_id_str)] = Connection.deserialize(
                path=connections_dir / conn_id_str,
            )


