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

The software concept, scientific design, methodological
decisions, project direction, and overall development
were led by Abbas Haghshenas; the Python code was
developed with coding assistance from OpenAI's GPT-5.6 Luna.

Copyright (c) 2026 Abbas Haghshenas
License: MIT
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QSplashScreen,
)

from gui import CanopyGUI


def resource_path(filename):
    """
    Return the path to a bundled application resource.

    Works both when running from source and when running
    from a PyInstaller onedir package.
    """

    return (
        Path(__file__).resolve().parent
        /
        filename
    )


def main():

    app = QApplication(
        sys.argv
    )

    # --------------------------------------------------------
    # Application icon
    # --------------------------------------------------------

    icon_path = resource_path(
        "CanopyCCGR.ico"
    )

    if icon_path.exists():

        app.setWindowIcon(
            QIcon(
                str(icon_path)
            )
        )

    # --------------------------------------------------------
    # Startup splash
    # --------------------------------------------------------

    splash = None

    splash_path = resource_path(
        "CanopyCCGR.png"
    )

    if splash_path.exists():

        pixmap = QPixmap(
            str(splash_path)
        )

        # Keep the splash reasonably sized on all Windows
        # display resolutions while preserving its aspect ratio.

        screen = app.primaryScreen()

        if screen is not None:

            available = (
                screen.availableGeometry()
            )

            max_width = min(
                420,
                int(
                    available.width()
                    * 0.40
                )
            )

            max_height = min(
                280,
                int(
                    available.height()
                    * 0.40
                )
            )

            pixmap = pixmap.scaled(
                max_width,
                max_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

        splash = QSplashScreen(
            pixmap
        )

        splash.setWindowFlags(
            Qt.WindowStaysOnTopHint
            |
            Qt.FramelessWindowHint
        )

        splash.show()

        app.processEvents()

    # --------------------------------------------------------
    # Create the actual GUI
    # --------------------------------------------------------

    window = CanopyGUI()

    window.show()

    app.processEvents()

    # --------------------------------------------------------
    # Close splash after GUI is visible
    # --------------------------------------------------------

    if splash is not None:

        splash.finish(
            window
        )

        app.processEvents()

    # --------------------------------------------------------
    # Start Qt event loop
    # --------------------------------------------------------

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":

    main()