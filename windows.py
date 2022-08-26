
import ctypes

import win32api, win32gui, win32con

import config

HWND = int


keycodes = {
    'forward': ord('W'),
    'backward': ord('S'),
    'left': ord('A'),
    'right': ord('D'),
    'jump': win32con.VK_SPACE,
    'crouch': win32con.VK_LSHIFT,
    'sprint': win32con.VK_LCONTROL
}
def get_keycode(action: str):
    return keycodes[action]


class Win32:
    class Win32Exception(Exception):
        pass

    # The ctypes mouse_event operates on "mickeys" on a 65536x65536 virtual screen
    # These helpers will transform coordinates from pixels to mickeys
    # @source: https://stackoverflow.com/questions/4263608/ctypes-mouse-events
    VIRTUAL_SCREEN_RATIO_X = 65536 / ctypes.windll.user32.GetSystemMetrics(0)
    VIRTUAL_SCREEN_RATIO_Y = 65536 / ctypes.windll.user32.GetSystemMetrics(1)
    def mouse_event_coord(x, y):
        return int(x * Win32.VIRTUAL_SCREEN_RATIO_X + 1), \
            int(y * Win32.VIRTUAL_SCREEN_RATIO_Y + 1)


def windows_init():
    # Set DPI awareness so Windows doesn't lie to us about pixel sizes.
    ctypes.windll.shcore.SetProcessDpiAwareness(2)


def find_window(keyword: str) -> (HWND or None):
    '''Find a window with keyword in the title'''
    ret = None
    def enum_handler(hwnd, ctx):
        nonlocal ret
        if win32gui.IsWindowVisible(hwnd):
            window_text = win32gui.GetWindowText(hwnd)
            # We exclude ':\\' to avoid incorrectly matching with a file explorer.
            if keyword in window_text and ':\\' not in window_text:
                ret = hwnd
    win32gui.EnumWindows(enum_handler, None)
    return ret

def focus_window(window_handle: HWND):
    win32gui.ShowWindow(window_handle, win32con.SW_RESTORE)
    win32gui.BringWindowToTop(window_handle)
    win32gui.SetForegroundWindow(window_handle)

def resize_window(window_handle: HWND) -> tuple:
    '''Returns the window's client rect as (x, y, width, height)'''
    def get_client_rect():
        client_rect = win32gui.GetClientRect(window_handle)
        xy = win32gui.ClientToScreen(window_handle, client_rect[:2])
        br = win32gui.ClientToScreen(window_handle, client_rect[-2:])
        return (*xy, br[0]-xy[0], br[1]-xy[1])
    # We attempt to assign the size twice, because Windows adds a border.
    # After it gives the wrong size the first time, add the difference and try again.
    win32gui.SetWindowPos(window_handle, None,
        config.CONTROLS_WINDOW_X,
        config.CONTROLS_WINDOW_Y,
        config.CONTROLS_WINDOW_WIDTH,
        config.CONTROLS_WINDOW_HEIGHT,
        win32con.SWP_SHOWWINDOW | win32con.SWP_NOZORDER)
    client_rect = get_client_rect()
    extra_x = config.CONTROLS_WINDOW_WIDTH - client_rect[2]
    extra_y = config.CONTROLS_WINDOW_HEIGHT - client_rect[3]
    # Second attempt, add the difference to account for the border.
    win32gui.SetWindowPos(window_handle, None,
        config.CONTROLS_WINDOW_X,
        config.CONTROLS_WINDOW_Y,
        config.CONTROLS_WINDOW_WIDTH + extra_x,
        config.CONTROLS_WINDOW_HEIGHT + extra_y,
        win32con.SWP_SHOWWINDOW | win32con.SWP_NOZORDER)
    client_rect = get_client_rect()
    if client_rect[2] != config.CONTROLS_WINDOW_WIDTH or \
        client_rect[3] != config.CONTROLS_WINDOW_HEIGHT:
        raise Win32.Win32Exception(f'Could not assign size ' + \
            f'{config.CONTROLS_WINDOW_WIDTH}x{config.CONTROLS_WINDOW_HEIGHT}' + \
            f' to window (got {client_rect[2]}x{client_rect[3]})')
    return client_rect



def send_keydown(window_handle: HWND, keycode: int):
    win32gui.PostMessage(window_handle, win32con.WM_KEYDOWN, keycode, 0)

def send_keyup(window_handle: HWND, keycode: int):
    win32gui.PostMessage(window_handle, win32con.WM_KEYUP, keycode, 0xC0000001)

def send_mousemove(delta_x: float, delta_y: float):
    p = win32api.GetCursorPos()
    #delta_x += p[0]
    #delta_y += p[1]
    #ctypes.windll.user32.mouse_event(0x8001, *Win32.mouse_event_coord(delta_x, delta_y), 0)
    ctypes.windll.user32.mouse_event(0x0001, int(delta_x), int(delta_y), 0)


def set_cursor_pos(x: int, y: int):
    win32api.SetCursorPos((x, y))
