
import os

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

import config
from process import Process
from model import Model


class SimpleLogicModel(Model):

    def init(self):
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=4, kernel_size=5)
        self.conv2 = nn.Conv2d(in_channels=4, out_channels=4, kernel_size=5)
        self.conv3 = nn.Conv2d(in_channels=4, out_channels=4, kernel_size=5)
        self.lin1 = nn.Linear(in_features=1936, out_features=32)
        self.lin2 = nn.Linear(in_features=32, out_features=2)
        self.criterion = nn.MSELoss()

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.conv1(x)), 2)
        x = F.max_pool2d(F.relu(self.conv2(x)), 2)
        x = torch.flatten(x)
        x = self.lin1(x)
        x = F.relu(x)
        x = self.lin2(x)
        return x

    def loss(self, output, target):
        return self.criterion(output, target)



class SimpleLogic(Process):

    def __init__(self):
        self.model = None
        self.train = True
        self.history = []
        super().__init__(num_inputs=1, num_outputs=1)


    def build(self):
        self.model = self.add_model(
            SimpleLogicModel,
            torch.optim.Adam,
            name='simple_logic',
            optimizer_args=dict(lr=1e-3)
        )


    def run(self, inputs: list):
    
        rgb = inputs[0][:,:,0:3]
        hsv = cv2.cvtColor(np.uint8(rgb), cv2.COLOR_RGB2HSV)
        rgb = rgb / 255


        if self.train:
            target_mask = cv2.inRange(hsv, np.array([245, 50, 0]), np.array([255, 255, 255]))
            target_mask = target_mask | cv2.inRange(hsv, np.array([0, 50, 0]), np.array([15, 255, 255]))

            if np.mean(target_mask) < 0.03:
                return [np.array([0.0, 0.0])]

            #cv2.imshow('color', target_mask)
            #cv2.waitKey(1)
            target_moments = cv2.moments(target_mask)
            # calculate x,y coordinate of center
            if target_moments["m00"] == 0:
                target_x, target_y = 0, 0
            else:
                target_x = target_moments["m10"] / target_moments["m00"]
                target_y = target_moments["m01"] / target_moments["m00"]
            target_x = (target_x - config.CONTROLS_WINDOW_WIDTH/16) * 16 / config.CONTROLS_WINDOW_WIDTH
            target_y = (target_y - config.CONTROLS_WINDOW_HEIGHT/16) * 16 / config.CONTROLS_WINDOW_HEIGHT
            target = torch.from_numpy(np.array([target_x, target_y], dtype=np.float32))

            self.model.optimizer.zero_grad()
            data = torch.from_numpy(np.moveaxis(rgb, 2, 0))
            output = self.model(data)
            loss = self.model.loss(output, target)
            loss.backward()
            for hd, ht in self.history:
                hout = self.model(hd)
                hloss = self.model.loss(hout, ht)
                hloss.backward()
            self.model.optimizer.step()
            if np.random.random() < 0.005:
                if len(self.history) >= 4:
                    self.history.pop(0)
                self.history.append((data, target))
            self.set_property('loss', float(loss))

            return [output]#[np.array([0.0, 0.0])]

        else:
            data = torch.from_numpy(np.float32(np.moveaxis(rgb, 2, 0)))
            output = self.model(data)

        return [output]


    #def serialize(self, path):
    #    if self.model is not None:
    #        if not os.path.exists(path / 'model'):
    #            os.mkdir(path / 'model')
    #        torch.save(self.model.state_dict(), path / 'model' / 'sd.pt')
#
    #def deserialize(self, config, path):
    #    if os.path.exists(path / 'model' / 'sd.pt'):
    #        self.model = SimpleLogicModel()
    #        self.model.load_state_dict(torch.load(path / 'model' / 'sd.pt'))
    #        self.model.eval()
