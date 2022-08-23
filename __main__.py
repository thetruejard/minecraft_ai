
import argparse
from pathlib import Path

import config
from controls import Controls
from model import MinecraftAI
from simplelogic import SimpleLogic
import tests
import vision



def create(
    path: Path,
    name: str=config.DEFAULT_MODEL_NAME
):
    model = MinecraftAI(name=name)
    
    # A Process is a set of operations that loop in parallel to everything else.
    # Each Process runs in its own (multiprocessing) thread.

    # A Process can be a single function. Inputs/outputs are params/return values.
    PROC_screen_grab = model.add_process(vision.ScreenGrab, name='screen_grab')
    PROC_vision = model.add_process(vision.VisionProcessing, name='vision')

    # A Process can also be a class inheriting from the Process class.
    # Pass the type, not an instance.
    PROC_controls = model.add_process(Controls, name='controls')
    PROC_simple_logic = model.add_process(SimpleLogic, name='simple_logic')

    # Processes communicate through "connections", which are made by connecting outputs to inputs.
    # Since Processes may run at different speeds, each connection has an evaluation policy.
    # Evalulation policies (default='discrete'):
    #   - 'discrete': wait and use the next available value. Note this may block the input Process.
    #   - 'continuous': return the most recent value, even if it hasn't changed from the last eval.
    
    # connect() takes inputs and returns outputs.
    # It enables an easy sequential-like model definition, while also 
    # supporting more complex configurations.

    screen = PROC_screen_grab.connect()
    vision_data = PROC_vision.connect(screen, policy='continuous')
    movement = PROC_simple_logic.connect(vision_data, policy='discrete')
    PROC_controls.connect(movement, policy='discrete')

    #model.build()
    model.save(path)











if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='MinecraftAI',
        description='An AI designed to play Minecraft.'
    )
    subparsers = parser.add_subparsers(dest='subcommand', required=True)
    parser.add_argument('-v', '--version', action='version', version=config.VERSION)

    parser_create = subparsers.add_parser('create', help='create a new model')
    parser_create.add_argument('dest_path', action='store', type=str,
        help='path to save the new model')
    parser_create.add_argument('--name', '-n', action='store', type=str,
        help='the name of the model',
        default=config.DEFAULT_MODEL_NAME)

    parser_run = subparsers.add_parser('run', help='run an existing model')
    parser_run.add_argument('model_path', action='store', type=str,
        help='path to load the model from')
    parser_run.add_argument('-nt', '--no_train', dest='train', action='store_false',
        help='freeze the model to prevent learning')

    subparsers.add_parser('test1', help='test: detect wnd & send keypresses')
    subparsers.add_parser('test2', help='test: test optical flow')
    subparsers.add_parser('test3', help='test: test feature mapping')
    subparsers.add_parser('test4', help='test: test the mouse movement')
    subparsers.add_parser('test5', help='test: test the model loading capability')

    args = parser.parse_args()

    if args.subcommand == 'create':
        create(args.dest_path, args.name)

    elif args.subcommand == 'test1':
        tests.keypress_test()
    elif args.subcommand == 'test2':
        tests.optical_flow_test()
    elif args.subcommand == 'test3':
        tests.feature_map_test()
    elif args.subcommand == 'test4':
        tests.mouse_test()
    elif args.subcommand == 'test5':
        tests.load_test()
