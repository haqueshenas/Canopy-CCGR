"""
Canopy CCGR for Python
Version 1.0.0

Application entry point for the Canopy CCGR graphical
user interface.

Live Preview Panel
Canopy CCGR Analyzer

Displays:

1. Original
2. Vegetation
3. Non-vegetation

The image keeps its original aspect ratio.
Unused space is filled with the normal GUI background.
No black image border is used.

The panel supports two update modes:

1. Normal processing preview:
   image + mask + calculated indices

2. Live segmentation preview:
   image + mask only

The live segmentation preview does NOT calculate
or replace scientific CC / GR / CCGR results.

IMPORTANT:

The segmentation mask supplied to this panel must already
have been calculated by CanopyAnalyzer.create_mask().

This panel contains NO scientific segmentation algorithm.
It only prepares images for display.


Author:
Abbas Haghshenas
Easy Phenotyping Lab (EPL)
https://haqueshenas.github.io/EPL
haqueshenas@gmail.com

## Development note

The software concept, scientific design, methodological decisions, project direction, and overall development were
led by Abbas Haghshenas; the Python code was developed with coding assistance from OpenAI's GPT-5.6 Luna.


Copyright (c) 2026 Abbas Haghshenas
License: MIT
"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QSizePolicy
)

from PySide6.QtGui import (
    QImage,
    QPixmap
)

from PySide6.QtCore import Qt

import numpy as np


# ============================================================
# Image Viewer
# ============================================================

class ImageViewer(QLabel):

    def __init__(self):

        super().__init__()

        self.setAlignment(
            Qt.AlignCenter
        )

        self.setMinimumSize(
            250,
            220
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        # IMPORTANT:
        # No border.
        # No artificial black background.
        #
        # The widget therefore shows the GUI's own
        # normal background around images whose aspect
        # ratio does not fill the available rectangle.

        self.setStyleSheet(
            """
            QLabel {
                border: none;
                padding: 0px;
                margin: 0px;
                background: transparent;
            }
            """
        )

        self._pixmap = None

    # ========================================================
    # Show NumPy image
    # ========================================================

    def show_numpy_image(
            self,
            image):

        if image is None:

            return

        image = np.asarray(
            image
        )

        image = np.ascontiguousarray(
            image
        )

        # ----------------------------------------------------
        # Grayscale
        # ----------------------------------------------------

        if image.ndim == 2:

            if image.dtype != np.uint8:

                image = np.clip(
                    image,
                    0,
                    255
                ).astype(
                    np.uint8
                )

            h, w = image.shape

            qimage = QImage(

                image.data,

                w,

                h,

                image.strides[0],

                QImage.Format_Grayscale8

            ).copy()

        # ----------------------------------------------------
        # RGB
        # ----------------------------------------------------

        elif image.ndim == 3 and image.shape[2] == 3:

            if image.dtype != np.uint8:

                image = np.clip(
                    image,
                    0,
                    255
                ).astype(
                    np.uint8
                )

            h, w, _ = image.shape

            qimage = QImage(

                image.data,

                w,

                h,

                image.strides[0],

                QImage.Format_RGB888

            ).copy()

        else:

            raise ValueError(
                "Unsupported image format for preview."
            )

        self._pixmap = QPixmap.fromImage(
            qimage
        )

        self._refresh_pixmap()

    # ========================================================
    # Resize handling
    # ========================================================

    def resizeEvent(
            self,
            event):

        super().resizeEvent(
            event
        )

        self._refresh_pixmap()

    # ========================================================
    # Keep original aspect ratio
    # ========================================================

    def _refresh_pixmap(self):

        if self._pixmap is None:

            return

        available = self.contentsRect().size()

        if available.width() <= 0:

            return

        if available.height() <= 0:

            return

        scaled = self._pixmap.scaled(

            available,

            Qt.KeepAspectRatio,

            Qt.SmoothTransformation

        )

        self.setPixmap(
            scaled
        )


# ============================================================
# Preview Panel
# ============================================================

class PreviewPanel(QWidget):

    def __init__(self):

        super().__init__()

        self.init_ui()

    # ========================================================
    # UI
    # ========================================================

    def init_ui(self):

        main_layout = QVBoxLayout()

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        images_layout = QHBoxLayout()

        images_layout.setSpacing(
            8
        )

        self.original_view = ImageViewer()

        self.vegetation_view = ImageViewer()

        self.soil_view = ImageViewer()

        images_layout.addWidget(

            self.create_box(
                "Original",
                self.original_view
            ),

            stretch=1

        )

        images_layout.addWidget(

            self.create_box(
                "Vegetation",
                self.vegetation_view
            ),

            stretch=1

        )

        images_layout.addWidget(

            self.create_box(
                "Non-vegetation",
                self.soil_view
            ),

            stretch=1

        )

        main_layout.addLayout(

            images_layout,

            stretch=1

        )

        # ----------------------------------------------------
        # Indices
        # ----------------------------------------------------

        self.index_label = QLabel(
            "CC = -     GR = -     CCGR = -"
        )

        self.index_label.setAlignment(
            Qt.AlignCenter
        )

        self.index_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 6px;
                border: none;
                background: transparent;
            }
            """
        )

        main_layout.addWidget(
            self.index_label
        )

        self.setLayout(
            main_layout
        )

    # ========================================================
    # Group box
    # ========================================================

    def create_box(
            self,
            title,
            widget):

        box = QGroupBox(
            title
        )

        box_layout = QVBoxLayout()

        box_layout.setContentsMargins(
            4,
            4,
            4,
            4
        )

        box_layout.addWidget(
            widget
        )

        box.setLayout(
            box_layout
        )

        return box

    # ========================================================
    # Build vegetation and non-vegetation images
    # ========================================================

    @staticmethod
    def create_segmented_images(
            image,
            mask):

        vegetation = image.copy()

        purple = np.array(
            [150, 0, 150],
            dtype=np.uint8
        )

        vegetation[
            mask == 0
        ] = purple

        non_vegetation = image.copy()

        black = np.array(
            [0, 0, 0],
            dtype=np.uint8
        )

        non_vegetation[
            mask == 1
        ] = black

        return (
            vegetation,
            non_vegetation
        )

    # ========================================================
    # Clear segmentation panels
    # ========================================================
    #
    # IMPORTANT:
    #
    # This prevents an old mask from remaining visible when
    # a new segmentation method cannot currently produce a
    # valid mask, for example when Custom has no selected
    # Python file.
    #
    # The Original panel is intentionally preserved.
    #
    # Scientific indices are also intentionally preserved.
    #

    def clear_segmentation_views(self):

        self.vegetation_view.clear()

        self.soil_view.clear()

    # ========================================================
    # Live segmentation preview
    # ========================================================
    #
    # IMPORTANT:
    #
    # This method updates only the image segmentation panels.
    #
    # It does NOT calculate CC / GR / CCGR.
    #
    # It does NOT modify the displayed scientific indices.
    #
    # The supplied image and mask may be display-sized copies.
    # Scientific segmentation has already been performed by
    # CanopyAnalyzer on the original image.
    #

    def update_segmentation_preview(
            self,
            image,
            mask):

        if image is None:

            return

        if mask is None:

            return

        self.original_view.show_numpy_image(
            image
        )

        vegetation, non_vegetation = (
            self.create_segmented_images(
                image,
                mask
            )
        )

        self.vegetation_view.show_numpy_image(
            vegetation
        )

        self.soil_view.show_numpy_image(
            non_vegetation
        )

    # ========================================================
    # Normal processing preview
    # ========================================================

    def update_preview(
            self,
            image,
            mask,
            result):

        if image is None:

            return

        if mask is None:

            return

        # ----------------------------------------------------
        # Original
        # ----------------------------------------------------

        self.original_view.show_numpy_image(
            image
        )

        # ----------------------------------------------------
        # Vegetation / Non-vegetation
        # ----------------------------------------------------

        vegetation, non_vegetation = (
            self.create_segmented_images(
                image,
                mask
            )
        )

        self.vegetation_view.show_numpy_image(
            vegetation
        )

        self.soil_view.show_numpy_image(
            non_vegetation
        )

        # ----------------------------------------------------
        # Indices
        # ----------------------------------------------------

        CC = result.get(
            "CC",
            np.nan
        )

        GR = result.get(
            "GR",
            np.nan
        )

        CCGR = result.get(
            "CCGR",
            np.nan
        )

        self.index_label.setText(

            f"CC = {CC:.4f}"
            f"     GR = {GR:.4f}"
            f"     CCGR = {CCGR:.4f}"

        )