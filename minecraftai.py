
import json
import os
from pathlib import Path
from tabnanny import process_tokens

import config
from connection import Connection
from process import Process, ProcessContainer
import utils



class MinecraftAI():
    

    def __init__(self,
        name: str='MinecraftAI'
    ):
        self.name = name
        self.processes = {}
        self.connections = {}
        
        self.total_running_time = 0
        self.total_training_time = 0
        
        self._built = False



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


    
    def add_process(self,
        process_type: type[Process],
        name: str='',
        type_args: dict={},
    ) -> ProcessContainer:
        '''
        Adds a new Process to this model. process must be a subclass of Process.
        If using a subclass of Process, pass the type itself, not an instance.
        type_args are the arguments used for instantiation. Only used if process is a class.
        '''
        if type(process_type) is not type or not issubclass(process_type, Process):
            raise TypeError('process must be a subclass of Process, and not an instance')
        if not name:
            name == process_type.__name__
        name = utils.create_new_name(name, self.processes.values())
        new_proc_id = utils.create_new_id(self.processes.keys())
        self.processes[new_proc_id] = ProcessContainer(
            parent_model=self,
            process_id=new_proc_id,
            process_type=process_type,
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
        name = utils.create_new_name(name, self.connections.values())
        new_conn_id = utils.create_new_id(self.connections.keys())
        self.connections[new_conn_id] = Connection(
            connection_id=new_conn_id,
            policy=policy,
            name=name
        )
        self.processes[output.process_id].connect_output(new_conn_id, output)
        self.processes[input.process_id].connect_input(new_conn_id, input)



    def build(self):
        if self._built:
            return
        for proc in self.processes.values():
            proc._build()
        for conn in self.connections.values():
            conn._build()
        self._built = True



    def start(self,
        allow_training: bool=True
    ):
        '''
        Launch all processes and start running the model.
        '''
        if not self._built:
            self.build()
        for proc in self.processes.values():
            proc.start()



    def stop(self):
        for proc in self.processes.values():
            proc.stop()
        for conn in self.connections.values():
            conn.post_stop()
        for proc in self.processes.values():
            proc.join()
    



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



    def load(path: Path, verbose: bool=True) -> 'MinecraftAI':
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

        return self


