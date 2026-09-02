"""
display_manager.py - Robust Win32 Display Orientation Manager for FlipMe
Handles flipping screen display horizontally (180 deg) and vertically (portrait/landscape flip),
as well as safely restoring original screen settings.
"""

import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

ENUM_CURRENT_SETTINGS = -1
ENUM_REGISTRY_SETTINGS = -2

DM_DISPLAYORIENTATION = 0x00080000
DM_PELSWIDTH = 0x00080000
DM_PELSHEIGHT = 0x00100000
DISP_CHANGE_SUCCESSFUL = 0

DMDO_DEFAULT = 0   # 0 degrees (Landscape)
DMDO_90 = 1        # 90 degrees (Portrait)
DMDO_180 = 2       # 180 degrees (Flipped Landscape)
DMDO_270 = 3       # 270 degrees (Flipped Portrait)

class POINTL(ctypes.Structure):
    _fields_ = [('x', wintypes.LONG), ('y', wintypes.LONG)]

class DUMMYUNIONNAME(ctypes.Union):
    class _D1(ctypes.Structure):
        _fields_ = [
            ('dmOrientation', ctypes.c_short),
            ('dmPaperSize', ctypes.c_short),
            ('dmPaperLength', ctypes.c_short),
            ('dmPaperWidth', ctypes.c_short),
            ('dmScale', ctypes.c_short),
            ('dmCopies', ctypes.c_short),
            ('dmDefaultSource', ctypes.c_short),
            ('dmPrintQuality', ctypes.c_short),
        ]
    class _D2(ctypes.Structure):
        _fields_ = [
            ('dmPosition', POINTL),
            ('dmDisplayOrientation', wintypes.DWORD),
            ('dmDisplayFixedOutput', wintypes.DWORD),
        ]
    _fields_ = [('s1', _D1), ('s2', _D2)]

class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ('dmDeviceName', wintypes.WCHAR * 32),
        ('dmSpecVersion', wintypes.WORD),
        ('dmDriverVersion', wintypes.WORD),
        ('dmSize', wintypes.WORD),
        ('dmDriverExtra', wintypes.WORD),
        ('dmFields', wintypes.DWORD),
        ('u', DUMMYUNIONNAME),
        ('dmColor', ctypes.c_short),
        ('dmDuplex', ctypes.c_short),
        ('dmYResolution', ctypes.c_short),
        ('dmTTOption', ctypes.c_short),
        ('dmCollate', ctypes.c_short),
        ('dmFormName', wintypes.WCHAR * 32),
        ('dmLogPixels', wintypes.WORD),
        ('dmBitsPerPel', wintypes.DWORD),
        ('dmPelsWidth', wintypes.DWORD),
        ('dmPelsHeight', wintypes.DWORD),
        ('dmDisplayFlags', wintypes.DWORD),
        ('dmDisplayFrequency', wintypes.DWORD),
        ('dmICMMethod', wintypes.DWORD),
        ('dmICMIntent', wintypes.DWORD),
        ('dmMediaType', wintypes.DWORD),
        ('dmDCOrientation', wintypes.DWORD),
        ('dmReserved1', wintypes.DWORD),
        ('dmReserved2', wintypes.DWORD),
        ('dmPanningWidth', wintypes.DWORD),
        ('dmPanningHeight', wintypes.DWORD),
    ]


class DisplayManager:
    def __init__(self):
        self.initial_orientation = self.get_current_orientation()

    def get_devmode(self, mode_enum=ENUM_CURRENT_SETTINGS):
        dm = DEVMODEW()
        dm.dmSize = ctypes.sizeof(DEVMODEW)
        if user32.EnumDisplaySettingsW(None, mode_enum, ctypes.byref(dm)):
            return dm
        return None

    def get_current_orientation(self):
        dm = self.get_devmode(ENUM_CURRENT_SETTINGS)
        if dm:
            return dm.u.s2.dmDisplayOrientation
        return DMDO_DEFAULT

    def set_orientation(self, target_orientation):
        dm = self.get_devmode(ENUM_CURRENT_SETTINGS)
        if not dm:
            return False

        current_orient = dm.u.s2.dmDisplayOrientation
        if current_orient == target_orientation:
            return True

        # Check if swapping width and height is required (switching between landscape and portrait)
        needs_swap = (current_orient % 2) != (target_orientation % 2)
        if needs_swap:
            dm.dmPelsWidth, dm.dmPelsHeight = dm.dmPelsHeight, dm.dmPelsWidth
            dm.dmFields = DM_DISPLAYORIENTATION | DM_PELSWIDTH | DM_PELSHEIGHT
        else:
            dm.dmFields = DM_DISPLAYORIENTATION

        dm.u.s2.dmDisplayOrientation = target_orientation

        res = user32.ChangeDisplaySettingsExW(None, ctypes.byref(dm), None, 0, None)
        return res == DISP_CHANGE_SUCCESSFUL

    def flip_horizontal(self):
        """
        Left Click action: Flip display horizontally.
        Toggles 180 degrees orientation flip (0 <-> 2, or 1 <-> 3).
        """
        curr = self.get_current_orientation()
        target = curr ^ 2  # 0 <-> 2 (180 deg), 1 <-> 3 (270 deg)
        return self.set_orientation(target)

    def flip_vertical(self):
        """
        Right Click action: Flip display vertically.
        Toggles orientation between 0 (Landscape) and 3 (Flipped Portrait / Vertical Flip),
        or toggles vertical orientation.
        """
        curr = self.get_current_orientation()
        if curr == DMDO_DEFAULT:
            target = DMDO_270
        elif curr == DMDO_270:
            target = DMDO_DEFAULT
        elif curr == DMDO_180:
            target = DMDO_90
        else:
            target = DMDO_180
        return self.set_orientation(target)

    def reset_display(self):
        """Reset orientation to normal (0 degrees)."""
        return self.set_orientation(DMDO_DEFAULT)


if __name__ == "__main__":
    dm = DisplayManager()
    print("Initial Orientation:", dm.get_current_orientation())
