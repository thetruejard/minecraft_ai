
import torch.nn as nn


class Model(nn.Module):

    def __init__(self):
        super().__init__()
        self.model_id = None
        self.name = None
        self.optimizer = None
        self.init()

    def init(self):
        pass

    def forward(self, x):
        raise NotImplementedError()

    def loss(self, output, target):
        raise NotImplementedError()

    def serialize(self):
        return {}

    def deserialize(self, config: dict):
        pass