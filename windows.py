
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
    '''Returns the window rect as (x, y, width, height)'''
    win32gui.SetWindowPos(window_handle, None,
        config.CONTROLS_WINDOW_X, config.CONTROLS_WINDOW_Y,
        config.CONTROLS_WINDOW_WIDTH, config.CONTROLS_WINDOW_HEIGHT,
        win32con.SWP_SHOWWINDOW | win32con.SWP_NOZORDER)
    client_rect = win32gui.GetClientRect(window_handle)
    xy = win32gui.ClientToScreen(window_handle, client_rect[:2])
    br = win32gui.ClientToScreen(window_handle, client_rect[-2:])
    return (*xy, br[0]-xy[0], br[1]-xy[1])



def send_keydown(window_handle: HWND, keycode: int):
    win32gui.PostMessage(window_handle, win32con.WM_KEYDOWN, keycode, 0)

def send_keyup(window_handle: HWND, keycode: int):
    win32gui.PostMessage(window_handle, win32con.WM_KEYUP, keycode, 0xC0000001)

def send_mousemove(window_handle: HWND, delta_x: int, delta_y: int):
    ctypes.windll.user32.mouse_event(0x0001, int(delta_x), int(delta_y), 0)


def set_cursor_pos(x: int, y: int):
    win32api.SetCursorPos((x, y))
