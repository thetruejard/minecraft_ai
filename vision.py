
import cv2
from mss import mss
import numpy as np
from PIL import Image

from minecraft import Minecraft
from process import Process


class ScreenGrab(Process):

    def __init__(self):
        super().__init__(num_inputs=0, num_outputs=1)

    def build(self):
        self.client_rect_dict = Minecraft.resize_window()
        self.sct = mss()

    def run(self, inputs: list):
        img = self.sct.grab(self.client_rect_dict)
        # Convert BGRA to RGB. It's faster to do this here rather than with vision processing
        # because we can drop the alpha channel and not pass it between processes.
        img = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2RGB)
        #if self.time_step() != 0:
        #    print(f'\r{int(1/self.time_step()):.3f}     ', end='')
        ts = self.time_step()
        if ts > 0:
            self.set_property('fps', round(1 / ts))
        return [img]



class VisionProcessing(Process):

    def __init__(self):
        self.prev = None
        self.prev_gray = None
        super().__init__(num_inputs=1, num_outputs=1)

    def run(self, inputs: list):

        SHRINK_FACTOR = 8
        img = inputs[0]
        img_smol = np.array(Image.fromarray(img).resize((img.shape[0] // SHRINK_FACTOR, img.shape[1] // SHRINK_FACTOR)))
        
        #img_smol = cv2.resize(img, (img.shape[0] // SHRINK_FACTOR, img.shape[1] // SHRINK_FACTOR))
        img_gray = cv2.cvtColor(np.array(img_smol), cv2.COLOR_RGB2GRAY)
        if self.prev is None:
            self.prev = np.zeros_like(img_smol)
            self.prev_gray = np.zeros_like(img_gray)
        flow = cv2.calcOpticalFlowFarneback(self.prev_gray, img_gray,
            None, 0.5, 3, 4, 3, 5, 1.2, 0
        )
        diff = (np.float32(img_smol) - np.float32(self.prev)) / 255.0
        edges = cv2.Canny(np.array(img_smol), 100, 200)
        edges = np.expand_dims(edges, axis=2)
        output = np.concatenate([img_smol, flow, diff, edges], axis=2)
        self.prev = img_smol
        self.prev_gray = img_gray

        return [output]

