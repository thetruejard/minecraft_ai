
import argparse
import time

from PIL import ImageGrab, Image
import win32api, win32gui, win32con

import config
import windows





def keypress_test():
    windows.windows_init()
    wnd = windows.find_window('Notepad')
    if wnd is None:
        raise Exception('Could not find window')
    # Notepad Only:
    ewnd = win32gui.FindWindowEx(wnd, None, "EDIT", None)
    windows.focus_window(wnd)
    for c in "WHYHELLOTHEREGENERALKENOBI":
        windows.send_keydown(ewnd, ord(c))
        windows.send_keyup(ewnd, ord(c))
    bbox = windows.resize_window(wnd)
    time.sleep(0.2)
    print(bbox)
    img = ImageGrab.grab(bbox)
    img.save('./hm.png')





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

    parser_run = subparsers.add_parser('run', help='run an existing model')
    parser_run.add_argument('model_path', action='store', type=str,
        help='path to load the model from')
    parser_run.add_argument('-nt', '--no_train', dest='train', action='store_false',
        help='freeze the model to prevent learning')

    subparsers.add_parser('test1', help='test: detect wnd & send keypresses')

    args = parser.parse_args()
    print(vars(args))

    if args.subcommand == 'test1':
        keypress_test()

