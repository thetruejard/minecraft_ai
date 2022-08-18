
import config
import windows


class Controls():    
    
    class ControlsException(Exception):
        pass


    def __init__(self):
        self.window_handle = None
        self.client_rect = None
        windows.windows_init()


    def connect_to_window(self):
        self.window_handle = windows.find_window(config.CONTROLS_WINDOW_TITLE_TEXT_KEYWORD)
        if self.window_handle is None:
            raise Controls.ControlsException(f'Could not find a window with \
                "{config.CONTROLS_WINDOW_TITLE_TEXT_KEYWORD}" in title text')
        windows.focus_window(self.window_handle)
        self.client_rect = windows.resize_window(self.window_handle)
        self.client_rect_dict = dict(zip(['left', 'top', 'width', 'height'], self.client_rect))
        
        

