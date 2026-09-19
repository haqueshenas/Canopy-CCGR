"""
Canopy CCGR for Python
Version 1.0.0

Application entry point for the Canopy CCGR graphical
user interface.

Author:
Abbas Haghshenas
Easy Phenotyping Lab (EPL)
https://haqueshenas.github.io/EPL
haqueshenas@gmail.com

Development note

The software concept, scientific design, methodological decisions,
project direction, and overall development were led by Abbas Haghshenas;
the Python code was developed with coding assistance from OpenAI's
GPT-5.6 Luna.

Copyright (c) 2026 Abbas Haghshenas
License: MIT
"""

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from gui import CanopyGUI


# PyInstaller provides this module only when the application
# is packaged with a PyInstaller splash screen.
try:
    import pyi_splash
except ImportError:
    pyi_splash = None


def close_splash():
    """
    Close the PyInstaller splash screen, if it is active.
    """
    if pyi_splash is not None:
        try:
            if pyi_splash.is_alive():
                pyi_splash.close()
        except Exception:
            pass


def main():
    app = QApplication(sys.argv)

    window = CanopyGUI()
    window.show()

    # Give Qt a brief opportunity to create and paint the main window,
    # then close the PyInstaller splash screen.
    QTimer.singleShot(150, close_splash)

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()