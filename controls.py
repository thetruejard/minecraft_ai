
from minecraft import Minecraft
from process import Process


class Controls(Process):

    def __init__(self):
        super().__init__(num_inputs=1, num_outputs=0)
    
    def run(self, inputs: list):
        CAM_SPEED = 2000

        cam_x, cam_y = inputs[0][0], inputs[0][1]
        speed = CAM_SPEED * self.time_step()

        #Minecraft.move_camera(0, 0)
        #print(f'\r{cam_x} {cam_y}     ', end='')
        Minecraft.move_camera(speed * cam_x, speed * cam_y)

        return []


        

