
import config
import windows


class _Controls():    
    
    class ControlsException(Exception):
        pass


    def __init__(self):
        self.window_handle = None
        windows.windows_init()


    def connect_to_window(self):
        self.window_handle = windows.find_window('Minecraft')
        if self.window_handle is None:
            raise _Controls.ControlsException('Could not find a window with "Minecraft" in title text')
        
        


Controls = _Controls()
