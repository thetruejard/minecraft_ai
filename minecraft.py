
import config
import windows


class Minecraft():
    '''
    Handles information about the Minecraft instance, such as window handle, etc.
    Also handles sending operations to the game, such as movement controls.
    If there are any platform-dependent operations, this is where code delegation occurs.
    '''

    window_handle = None

    def get_window_handle():
        if Minecraft.window_handle is not None:
            return Minecraft.window_handle
        Minecraft.window_handle = windows.find_window(config.MINECRAFT_TITLE_TEXT_KEYWORD)
        if Minecraft.window_handle is None:
            raise Exception(f'Could not find a window with \
                "{config.MINECRAFT_TITLE_TEXT_KEYWORD}" in title text')

    def focus_window():
        windows.focus_window(Minecraft.get_window_handle())

    def resize_window():
        rect = windows.resize_window(Minecraft.get_window_handle())
        return dict(zip(['left', 'top', 'width', 'height'], rect))
