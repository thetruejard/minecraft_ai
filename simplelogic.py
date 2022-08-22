
from process import Process


class SimpleLogic(Process):

    def __init__(self):
        super().__init__(num_inputs=1, num_outputs=1)


    def run(self, inputs: list):
        pass

