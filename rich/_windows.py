import sys
from dataclasses import dataclass


@dataclass
class WindowsConsoleFeatures:
    """Windows features available."""

    vt: bool = False
    """The console supports VT codes."""
    truecolor: bool = False
    """The console supports truecolor."""


try:
    import atexit
    import ctypes
    from ctypes import LibraryLoader
    from typing import Optional

    if sys.platform == "win32":
        windll = LibraryLoader(ctypes.WinDLL)
    else:
        windll = None
        raise ImportError("Not windows")

    from rich._win32_console import (
        ENABLE_VIRTUAL_TERMINAL_PROCESSING,
        GetConsoleMode,
        GetConsoleOutputCP,
        GetStdHandle,
        LegacyWindowsError,
        SetConsoleMode,
        SetConsoleOutputCP,
    )

except (AttributeError, ImportError, ValueError):
    # Fallback if we can't load the Windows DLL
    def get_windows_console_features() -> WindowsConsoleFeatures:
        features = WindowsConsoleFeatures()
        return features

else:
    _original_output_cp: Optional[int] = None

    def get_windows_console_features() -> WindowsConsoleFeatures:
        """Get windows console features.

        Returns:
            WindowsConsoleFeatures: An instance of WindowsConsoleFeatures.
        """
        handle = GetStdHandle()
        try:
            console_mode = GetConsoleMode(handle)
            success = True
        except LegacyWindowsError:
            console_mode = 0
            success = False

        if success and not (console_mode & ENABLE_VIRTUAL_TERMINAL_PROCESSING):
            try:
                SetConsoleMode(
                    handle, console_mode | ENABLE_VIRTUAL_TERMINAL_PROCESSING
                )
                console_mode = GetConsoleMode(handle)
            except LegacyWindowsError:
                pass

        vt = bool(success and console_mode & ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        truecolor = False
        if vt:
            win_version = sys.getwindowsversion()
            truecolor = win_version.major > 10 or (
                win_version.major == 10 and win_version.build >= 15063
            )

        if success:
            global _original_output_cp
            try:
                cp = GetConsoleOutputCP()
                if cp and cp != 65001:
                    if _original_output_cp is None:
                        _original_output_cp = cp
                        atexit.register(SetConsoleOutputCP, cp)
                    SetConsoleOutputCP(65001)
            except Exception:
                pass

        features = WindowsConsoleFeatures(vt=vt, truecolor=truecolor)
        return features


if __name__ == "__main__":
    import platform

    features = get_windows_console_features()
    from rich import print

    print(f'platform="{platform.system()}"')
    print(repr(features))
