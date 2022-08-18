
import argparse
import math
import time

import cv2 as cv
from mss import mss
import numpy as np
from PIL import ImageGrab, Image
import win32api, win32gui, win32con

import config
from controls import Controls
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


def optical_flow_test():
    c = Controls()
    c.connect_to_window()
    total_time = 0
    last_time = time.perf_counter()
    n_grabbed = 0
    n = 0
    prev = None
    prev_gray = None
    with mss() as sct:
        while total_time < 120:
            elapsed = time.perf_counter() - last_time
            if elapsed >= 1:
                print(f'FPS: {n_grabbed}')
                total_time += elapsed
                last_time += elapsed
                n_grabbed = 0
            imgss = sct.grab(c.client_rect_dict)
            img = Image.frombytes(
                'RGB', 
                (imgss.width, imgss.height), 
                imgss.rgb, 
            )
            #img.save(f'./hm/{n}.tif')
            imgsmol = img.resize((img.width // 16, img.height // 16))
            img_gray = cv.cvtColor(np.array(imgsmol), cv.COLOR_BGR2GRAY)
            if  prev_gray is not None:
                flow = cv.calcOpticalFlowFarneback(prev_gray, img_gray, None, 0.5, 3, 4, 3, 5, 1.2, 0)
                i = np.concatenate([np.array(flow), np.expand_dims(np.zeros_like(img_gray), axis=2)], axis=2)
                i = np.tanh(i) * 0.5 + 0.5
                i = np.uint8(i * 255)
                resized = Image.fromarray(i).resize(img.size, Image.Resampling.NEAREST)
                #resized.save(f'./hmflow/{n}.tif')

                diff = (np.float32(imgsmol) - np.float32(prev)) / 255
                diff = np.array(Image.fromarray(np.uint8(255*(np.tanh(diff)*0.5+0.5))) \
                    .resize(img.size, Image.Resampling.NEAREST))
                row1 = np.concatenate([img, resized], axis=1)
                row2 = np.concatenate([diff, imgsmol.resize(img.size, Image.Resampling.NEAREST)], axis=1)
                quad = np.concatenate([row1, row2], axis=0)
                cv.imshow('show', cv.cvtColor(quad, cv.COLOR_RGB2BGR))
                cv.waitKey(1)

            prev = imgsmol
            prev_gray = img_gray
            n_grabbed += 1
            n += 1
    cv.destroyAllWindows()

def feature_map_test():
    cont = Controls()
    cont.connect_to_window()
    total_time = 0
    last_time = time.perf_counter()
    n_grabbed = 0
    n = 0
    prev = []
    num_points = 128
    colors = np.random.randint(0, 255, (num_points, 3))
    with mss() as sct:
        while total_time < 60:
            elapsed = time.perf_counter() - last_time
            if elapsed >= 1:
                print(f'FPS: {n_grabbed}')
                total_time += elapsed
                last_time += elapsed
                n_grabbed = 0
            imgss = sct.grab(cont.client_rect_dict)
            img = Image.frombytes(
                'RGB',
                (imgss.width, imgss.height),
                imgss.rgb
            )
            img.save(f'./hm/{n}.tif')

            if len(prev) > 0:
                for j in range(3):
                    img_channel = np.array(img.resize((img.width // 4, img.height // 4)))[...,j]

                    features = cv.goodFeaturesToTrack(prev[j], mask=None,
                        maxCorners = num_points,
                        qualityLevel = 0.6,
                        minDistance = 30,
                        blockSize = 5,
                    )

                    if features is not None:
                        moved_features, st, err = cv.calcOpticalFlowPyrLK(prev[j], img_channel, features, None,
                            winSize  = (8, 8),
                            maxLevel = 2,
                            criteria = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 4, 0.05)
                        )

                        if moved_features is not None:
                            good_new = moved_features[st==1]
                            good_old = features[st==1]

                        if len(good_new) > 0:
                            img = np.array(img)
                            for i, (new, old) in enumerate(zip(good_new, good_old)):
                                a, b = new.ravel()
                                c, d = old.ravel()
                                img = cv.line(img, (int(a), int(b)), (int(c), int(d)), colors[i].tolist(), 8)
                                img = cv.circle(img, (int(a), int(b)), 12, colors[i].tolist(), -1)
                            img = Image.fromarray(img)

                    prev[j] = img_channel

                img.resize(img.size).save(f'./hmfeat/{n}.tif')
            else:
                prev = [np.array(img.resize((img.width // 4, img.height // 4)))[...,j] for j in range(3)]

            n_grabbed += 1
            n += 1


def mouse_test():
    cont = Controls()
    cont.connect_to_window()
    elapsed = 0
    windows.set_cursor_pos(
        cont.client_rect[0] + int(cont.client_rect[2] / 2),
        cont.client_rect[1] + int(cont.client_rect[3] / 2)
    )
    last = time.perf_counter()
    while elapsed < 30:
        step = time.perf_counter() - last
        windows.send_mousemove(cont.window_handle, step * 300 * math.sin(elapsed), step * 300 * math.cos(1.4*elapsed))
        time.sleep(0.01)
        last += step
        elapsed += step




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
    subparsers.add_parser('test2', help='test: test optical flow')
    subparsers.add_parser('test3', help='test: test feature mapping')
    subparsers.add_parser('test4', help='test: test the mouse movement')

    args = parser.parse_args()
    print(vars(args))

    if args.subcommand == 'test1':
        keypress_test()
    elif args.subcommand == 'test2':
        optical_flow_test()
    elif args.subcommand == 'test3':
        feature_map_test()
    elif args.subcommand == 'test4':
        mouse_test()

