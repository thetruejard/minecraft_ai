

from controls import Controls
from PIL import Image, ImageGrab
import win32api, win32gui, win32con
import time
from mss import mss
import cv2 as cv
import numpy as np
import math
import windows
import config
from pathlib import Path
from model import MinecraftAI



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
        while total_time < 30:
            elapsed = time.perf_counter() - last_time
            if elapsed >= 1:
                print(f'\rFPS: {n_grabbed}  ', end='')
                total_time += elapsed
                last_time += elapsed
                n_grabbed = 0
            imgss = sct.grab(c.client_rect_dict)
            img = Image.frombytes(
                'RGB', 
                (imgss.width, imgss.height), 
                imgss.rgb, 
            )
            shrink_factor = 8
            imgsmol = img.resize((img.width // shrink_factor, img.height // shrink_factor))
            img_gray = cv.cvtColor(np.array(imgsmol), cv.COLOR_BGR2GRAY)
            if  prev_gray is not None:
                flow = cv.calcOpticalFlowFarneback(prev_gray, img_gray, None, 0.5, 3, 4, 3, 5, 1.2, 0)
                i = np.concatenate([np.array(flow), np.expand_dims(np.zeros_like(img_gray), axis=2)], axis=2)
                i = np.tanh(i) * 0.5 + 0.5
                i = np.uint8(i * 255)
                resized = Image.fromarray(i).resize(img.size, Image.Resampling.NEAREST)

                diff = (np.float32(imgsmol) - np.float32(prev)) / 255
                diff = np.array(Image.fromarray(np.uint8(255*(np.tanh(diff)*0.5+0.5))) \
                    .resize(img.size, Image.Resampling.NEAREST))

                edges = cv.Canny(np.array(imgsmol), 100, 200)
                edges = np.array(Image.fromarray(edges) \
                    .resize(img.size, Image.Resampling.NEAREST))
                edges = np.broadcast_to(np.expand_dims(edges, axis=2), (*edges.shape, 3))

                row1 = np.concatenate([img, resized], axis=1)
                row2 = np.concatenate([diff, edges], axis=1)
                quad = np.concatenate([row1, row2], axis=0)
                Image.fromarray(quad).save(f'./hm/{n}.tif')
                cv.imshow('show', cv.cvtColor(quad, cv.COLOR_RGB2BGR))
                cv.waitKey(1)

            prev = imgsmol
            prev_gray = img_gray
            n_grabbed += 1
            n += 1
    print()
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
        windows.send_mousemove(step *20* math.sin(elapsed), step *20* math.cos(elapsed))
        time.sleep(0.01)
        last += step
        elapsed += step



def load_test():
    path = './test'
    model = MinecraftAI.load(path)




def create_prototype1(
    path: Path,
    name: str=config.DEFAULT_MODEL_NAME
):
    model = MinecraftAI(name=name)
    
    # A Process is a set of operations that loop in parallel to everything else.
    # Each Process runs in its own (multiprocessing) thread.

    # A Process can be a single function. Inputs/outputs are params/return values.
    screen_grab = model.add_process(screengrab.grab, name='screen_grab')
    vision = model.add_process(vis.process_vision, name='vision')

    # A Process can also be a class inheriting from the Process class.
    # Pass the type, not an instance.
    controls = model.add_process(Controls, name='controls')
    simple_logic = model.add_process(SimpleLogic, name='simple_logic')

    # Processes communicate through "connections", which are made by connecting outputs to inputs.
    # Since Processes may run at different speeds, each connection has an evaluation policy.
    # Evalulation policies (default='discrete'):
    #   - 'discrete': wait and use the next available value. Note this may block the input Process.
    #   - 'continuous': return the most recent value, even if it hasn't changed from the last eval.
    
    # Get references to the output(s) of a Process. Arg is the number of expected outputs.
    c_screen = screen_grab.outputs(1)
    # Pass references as input(s) to another Process.
    vision.inputs(c_screen, policy='continuous')

    # Although not demoed here, they don't have to all come from the same processes.
    # Eval policies can be the same (one string) or different for each input (a list).
    c_color, c_motion, c_diff, c_form = vision.outputs(4)
    simple_logic.inputs(c_color, c_motion, c_diff, c_form, policy='discrete')

    c_movement, c_camera = simple_logic.outputs(2)
    controls.inputs(c_movement, c_camera, policy=['discrete', 'discrete'])

    # "Build" the model to declare the architecture as final.
    model.build()
    model.save(path)

