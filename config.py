

VERSION = 'MinecraftAI 0.1a (Alpha)'

DEFAULT_MODEL_NAME = 'MinecraftAI'

MINECRAFT_TITLE_TEXT_KEYWORD = 'Minecraft'

CONTROLS_WINDOW_X = 25
CONTROLS_WINDOW_Y = 25
CONTROLS_WINDOW_WIDTH = 800
CONTROLS_WINDOW_HEIGHT = 800




def get_config(name: str):
    '''
    Returns the value of the config variable with the given name.
    On error (invalid name), raises KeyError.
    '''
    # Disallow nonexistent and dunder names.
    if '__' in name or name not in globals().keys():
        raise KeyError('Cannot read dunder or nonexistent global config variable.')
    return globals()[name]


def set_config(name: str, value) -> bool:
    '''
    Returns True if the value is changed, false if it's already the assigned value.
    On error (invalid name), raises KeyError.
    '''
    # Disallow nonexistent and dunder names.
    if '__' in name or name not in globals().keys():
        raise KeyError('Cannot assign dunder or nonexistent global config variable')
    old = globals()[name]
    globals()[name] = value
    return old != value
