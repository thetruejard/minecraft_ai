
import cv2
from mss import mss
import numpy as np

from minecraft import Minecraft
from process import Process


class ScreenGrab(Process):

    def init(self):
        if self.inited:
            return
        self.client_rect_dict = Minecraft.resize_window()
        self.sct = mss()
        self.inited = True

    def __init__(self):
        self.inited = False
        super().__init__(num_inputs=0, num_outputs=1)


    def run(self, inputs: list):
        self.init()
        img = self.sct.grab(self.client_rect_dict)
        # Convert BGRA to RGB. It's faster to do this here rather than with vision processing
        # because we can drop the alpha channel and not pass it between processes.
        img = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2RGB)
        return img



class VisionProcessing(Process):

    def __init__(self):
        self.prev = None
        self.prev_gray = None
        super().__init__(num_inputs=1, num_outputs=1)

    def run(self, inputs: list):
        SHRINK_FACTOR = 8
        img = inputs[0]
        img_smol = cv2.resize(img, (img.shape[0] // SHRINK_FACTOR, img.shape[1] // SHRINK_FACTOR))
        img_gray = cv2.cvtColor(np.array(img_smol), cv2.COLOR_RGB2GRAY)
        if self.prev is None:
            self.prev = np.zeros_like(img_smol)
            self.prev_gray = np.zeros_like(img_gray)
        flow = cv2.calcOpticalFlowFarneback(self.prev_gray, img_gray,
            None, 0.5, 3, 4, 3, 5, 1.2, 0
        )
        flow = np.expand_dims(flow, axis=2)
        diff = (np.float32(img_smol) - np.float32(self.prev)) / 255.0
        edges = cv2.Canny(np.array(img_smol), 100, 200)
        edges = np.expand_dims(edges, axis=2)
        output = np.concatenate([img_smol, flow, diff, edges], axis=2)
        return output

