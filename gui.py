"""
Canopy CCGR for Python
Version 1.0.0

Graphical user interface for Canopy CCGR.

Provides:
- Image-folder selection
- Segmentation-method selection
- Live segmentation preview
- HSV parameter control
- Custom Python segmentation
- Processing progress and status
- Scientific-result preview

Scientific calculations are performed by
CanopyAnalyzer in canopy_engine.py.

Author:
Abbas Haghshenas

Easy Phenotyping Lab (EPL)
https://haqueshenas.github.io/EPL

Email:
[haqueshenas@gmail.com](mailto:haqueshenas@gmail.com)

## Development note

The software concept, scientific design, methodological decisions, project direction, and overall development were
led by Abbas Haghshenas; the Python code was developed with coding assistance from OpenAI's GPT-5.6 Luna.



Copyright (c) 2026 Abbas Haghshenas
License: MIT
"""

from datetime import datetime
from pathlib import Path
from PySide6.QtGui import QIcon

import cv2
import numpy as np

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QFileDialog,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QProgressBar,
    QTextEdit,
    QGroupBox,
    QMessageBox,
    QSizePolicy,
    QLineEdit,
    QDialog,
    QDialogButtonBox,
)

from PySide6.QtCore import QThread, Signal, Qt, QTimer

from canopy_engine import CanopyAnalyzer
from preview import PreviewPanel


# ============================================================
# Worker Thread
# ============================================================

class ProcessingThread(QThread):

    progress = Signal(
        int,
        int,
        str
    )

    preview = Signal(
        object,
        object,
        object
    )

    # IMPORTANT:
    # Do not call this "finished".
    # QThread already has a built-in finished signal.
    processing_finished = Signal(
        object
    )

    error = Signal(
        str
    )

    def __init__(
            self,
            input_folder,
            output_folder,
            method,
            hsv,
            gr_max,
            custom_segmentation_path):

        super().__init__()

        self.input_folder = input_folder
        self.output_folder = output_folder
        self.method = method
        self.hsv = hsv
        self.gr_max = gr_max
        self.custom_segmentation_path = (
            custom_segmentation_path
        )

    def run(self):

        try:

            analyzer = CanopyAnalyzer(

                segmentation_method=self.method,

                hsv_parameters=self.hsv,

                gr_max=self.gr_max,

                custom_segmentation_path=(
                    self.custom_segmentation_path
                )

            )

            dataframe = analyzer.process_folder(

                self.input_folder,

                self.output_folder,

                callback=self.callback,

                image_callback=self.image_callback

            )

            # Send the complete results table to GUI.
            self.processing_finished.emit(
                dataframe
            )

        except Exception as e:

            self.error.emit(
                str(e)
            )

    def image_callback(
            self,
            image,
            mask,
            result):

        self.preview.emit(
            image,
            mask,
            result
        )

    def callback(
            self,
            current,
            total,
            name):

        self.progress.emit(
            current,
            total,
            name
        )


# ============================================================
# Main GUI
# ============================================================

class CanopyGUI(QWidget):

    SOFTWARE_NAME = "Canopy CCGR for Python"
    SOFTWARE_VERSION = "1.0.0"

    HSV_DEFAULTS = {

        "H_min": 25,
        "H_max": 95,
        "S_min": 40,
        "S_max": 255,
        "V_min": 30,
        "V_max": 255

    }

    # Default graph visualization limit.
    # IMPORTANT:
    # This affects graph color normalization only.
    # It does NOT affect scientific calculations.
    GR_MAX = 0.3

    # --------------------------------------------------------
    # Supported image extensions.
    # This is kept consistent with Canopy CCGR processing.
    # --------------------------------------------------------

    IMAGE_EXTENSIONS = (

        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.bmp",
        "*.tif",
        "*.tiff"

    )

    # --------------------------------------------------------
    # Maximum dimension used for interactive display.
    #
    # IMPORTANT:
    # This DOES NOT affect scientific segmentation.
    #
    # The full-resolution image is segmented first.
    # Only the final display copy is resized.
    # --------------------------------------------------------

    SEGMENTATION_PREVIEW_MAX_DIM = 1600

    # --------------------------------------------------------
    # Debounce interval for HSV changes.
    #
    # Rapid SpinBox changes are combined into one preview
    # update instead of recalculating after every keystroke.
    # --------------------------------------------------------

    SEGMENTATION_PREVIEW_DELAY_MS = 150

    def __init__(self):

        super().__init__()

        # ----------------------------------------------------
        # Application Icon
        # ----------------------------------------------------
        #
        # Use one application-wide icon so that the main
        # window and Qt dialog windows use the same identity.
        #
        # The icon file is kept beside this source file:
        #
        #     CanopyCCGR.ico
        #

        self.application_icon_path = (
            Path(__file__).resolve().parent
            /
            "CanopyCCGR.ico"
        )

        if self.application_icon_path.exists():

            self.application_icon = QIcon(
                str(
                    self.application_icon_path
                )
            )

            # Main window
            self.setWindowIcon(
                self.application_icon
            )

            # Application-wide icon.
            #
            # QMessageBox and other Qt-created windows can
            # inherit the application icon from here.
            #

            application = (
                QApplication.instance()
            )

            if application is not None:

                application.setWindowIcon(
                    self.application_icon
                )

        else:

            self.application_icon = QIcon()

            print(
                "WARNING: CanopyCCGR.ico was not found:"
                f" {self.application_icon_path}"
            )

        self.setWindowTitle(
            "Canopy CCGR Analyzer"
        )

        # ----------------------------------------------------
        # Window behavior
        # ----------------------------------------------------

        self.resize(
            1180,
            760
        )

        self.setMinimumSize(
            900,
            600
        )

        self.setWindowState(
            self.windowState() | Qt.WindowMaximized
        )

        self.input_folder = ""
        self.output_folder = ""
        self.thread = None

        # Stores the exact GRmax used by the current run.
        self.processing_gr_max = self.GR_MAX

        # ----------------------------------------------------
        # Live segmentation preview state
        # ----------------------------------------------------

        self.segmentation_preview_image = None
        self.segmentation_preview_path = None

        self.segmentation_preview_timer = QTimer(
            self
        )

        self.segmentation_preview_timer.setSingleShot(
            True
        )

        self.segmentation_preview_timer.setInterval(
            self.SEGMENTATION_PREVIEW_DELAY_MS
        )

        self.segmentation_preview_timer.timeout.connect(
            self.update_segmentation_preview
        )

        # ----------------------------------------------------
        # Custom segmentation state
        # ----------------------------------------------------

        self.custom_segmentation_path = ""

        # ----------------------------------------------------
        # Processing log state
        # ----------------------------------------------------

        self.processing_start_time = None
        self.processing_end_time = None
        self.processing_image_names = []
        self.processing_total_images = 0
        self.processing_input_folder = ""
        self.processing_output_folder = ""
        self.processing_method = ""
        self.processing_gr_max = self.GR_MAX
        self.processing_hsv = {}
        self.processing_custom_path = ""

        # ----------------------------------------------------
        # About dialog
        # ----------------------------------------------------

        self.about_dialog = None

        self.init_ui()
        self.apply_style()

        self.progress.setVisible(
            False
        )

    # ========================================================
    # Build UI
    # ========================================================

    def init_ui(self):

        root = QVBoxLayout()

        root.setContentsMargins(
            14,
            10,
            14,
            8
        )

        root.setSpacing(
            7
        )

        # ====================================================
        # Analysis Setup
        # ====================================================

        setup_box = QGroupBox(
            "Analysis Setup"
        )

        setup_layout = QGridLayout()

        setup_layout.setContentsMargins(
            10,
            9,
            10,
            9
        )

        setup_layout.setHorizontalSpacing(
            10
        )

        setup_layout.setVerticalSpacing(
            5
        )

        # Four visually balanced columns:
        #
        # 0 = Input
        # 1 = Output
        # 2 = Segmentation / GRmax
        # 3 = Start
        #

        for column in range(4):

            setup_layout.setColumnStretch(
                column,
                1
            )

        # ----------------------------------------------------
        # Input folder
        # ----------------------------------------------------

        self.input_button = QPushButton(
            "Select Image Folder"
        )

        self.input_button.setObjectName(
            "secondaryButton"
        )

        self.input_button.clicked.connect(
            self.select_input
        )

        self.input_label = QLineEdit(
            "Input: not selected"
        )

        self.configure_path_field(
            self.input_label
        )

        # ----------------------------------------------------
        # Output folder
        # ----------------------------------------------------

        self.output_button = QPushButton(
            "Select Output Folder"
        )

        self.output_button.setObjectName(
            "secondaryButton"
        )

        self.output_button.clicked.connect(
            self.select_output
        )

        self.output_label = QLineEdit(
            "Output: not selected"
        )

        self.configure_path_field(
            self.output_label
        )

        # ----------------------------------------------------
        # Segmentation method
        # ----------------------------------------------------

        method_header = QWidget()

        method_header_layout = QHBoxLayout(
            method_header
        )

        method_header_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        method_header_layout.setSpacing(
            7
        )

        method_label = QLabel(
            "Segmentation"
        )

        method_label.setObjectName(
            "fieldLabel"
        )

        method_header_layout.addWidget(
            method_label
        )

        method_header_layout.addStretch(
            1
        )

        # ----------------------------------------------------
        # GRmax control
        # ----------------------------------------------------

        grmax_label = QLabel(
            "GRmax"
        )

        grmax_label.setObjectName(
            "fieldLabel"
        )

        self.gr_max_spin = QDoubleSpinBox()

        self.gr_max_spin.setRange(
            0.001,
            1.000
        )

        self.gr_max_spin.setDecimals(
            3
        )

        self.gr_max_spin.setSingleStep(
            0.01
        )

        self.gr_max_spin.setValue(
            self.GR_MAX
        )

        self.gr_max_spin.setMinimumWidth(
            78
        )

        self.gr_max_spin.setMinimumHeight(
            32
        )

        self.gr_max_spin.setToolTip(
            "GRmax controls only the color normalization "
            "range of the graphs. It does not change "
            "CC, GR, or CCGR calculations."
        )

        method_header_layout.addWidget(
            grmax_label
        )

        method_header_layout.addWidget(
            self.gr_max_spin
        )

        # ----------------------------------------------------
        # Segmentation method selector
        # ----------------------------------------------------

        self.method_combo = QComboBox()

        self.method_combo.setMinimumHeight(
            36
        )

        self.method_combo.addItems([
            "G>R",
            "G>R&G>B",
            "2G-R-B>0",
            "HSV",
            "Custom"
        ])

        # Original MATLAB method = default.
        self.method_combo.setCurrentIndex(
            0
        )

        self.method_combo.currentTextChanged.connect(
            self.toggle_segmentation_method
        )

        # ----------------------------------------------------
        # About button
        # ----------------------------------------------------

        self.about_button = QPushButton(
            "ABOUT"
        )

        self.about_button.setObjectName(
            "smallButton"
        )

        self.about_button.setMinimumHeight(
            36
        )

        self.about_button.clicked.connect(
            self.show_about
        )

        # ----------------------------------------------------
        # Start button
        # ----------------------------------------------------

        self.run_button = QPushButton(
            "START PROCESSING"
        )

        self.run_button.setObjectName(
            "startButton"
        )

        self.run_button.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.run_button.clicked.connect(
            self.start
        )

        # ----------------------------------------------------
        # Compact two-row arrangement
        # ----------------------------------------------------

        # Row 0: main controls
        setup_layout.addWidget(
            self.input_button,
            0,
            0
        )

        setup_layout.addWidget(
            self.output_button,
            0,
            1
        )

        setup_layout.addWidget(
            method_header,
            0,
            2
        )

        # Rightmost action column: About above Start Processing.
        action_layout = QVBoxLayout()

        action_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        action_layout.setSpacing(
            6
        )

        action_layout.addWidget(
            self.about_button,
            0
        )

        action_layout.addWidget(
            self.run_button,
            1
        )

        setup_layout.addLayout(
            action_layout,
            0,
            3,
            2,
            1
        )

        # Row 1: selected paths and method.
        setup_layout.addWidget(
            self.input_label,
            1,
            0
        )

        setup_layout.addWidget(
            self.output_label,
            1,
            1
        )

        setup_layout.addWidget(
            self.method_combo,
            1,
            2
        )

        setup_box.setLayout(
            setup_layout
        )

        root.addWidget(
            setup_box,
            0
        )

        # ====================================================
        # HSV Parameters
        # ====================================================

        self.hsv_container = QWidget()

        hsv_layout = QHBoxLayout(
            self.hsv_container
        )

        hsv_layout.setContentsMargins(
            0,
            2,
            0,
            0
        )

        hsv_layout.setSpacing(
            7
        )

        hsv_title = QLabel(
            "HSV:"
        )

        hsv_title.setObjectName(
            "fieldLabel"
        )

        hsv_layout.addWidget(
            hsv_title
        )

        self.h_spin = {}

        hsv_definitions = [

            (
                "H_min",
                "H min",
                self.HSV_DEFAULTS["H_min"],
                0,
                179
            ),

            (
                "H_max",
                "H max",
                self.HSV_DEFAULTS["H_max"],
                0,
                179
            ),

            (
                "S_min",
                "S min",
                self.HSV_DEFAULTS["S_min"],
                0,
                255
            ),

            (
                "S_max",
                "S max",
                self.HSV_DEFAULTS["S_max"],
                0,
                255
            ),

            (
                "V_min",
                "V min",
                self.HSV_DEFAULTS["V_min"],
                0,
                255
            ),

            (
                "V_max",
                "V max",
                self.HSV_DEFAULTS["V_max"],
                0,
                255
            )

        ]

        for (
                key,
                text,
                value,
                minimum,
                maximum
        ) in hsv_definitions:

            label = QLabel(
                text
            )

            label.setObjectName(
                "fieldLabel"
            )

            spin = QSpinBox()

            spin.setRange(
                minimum,
                maximum
            )

            spin.setValue(
                value
            )

            spin.setMinimumWidth(
                72
            )

            spin.setMinimumHeight(
                32
            )

            self.h_spin[key] = spin

            hsv_layout.addWidget(
                label
            )

            hsv_layout.addWidget(
                spin
            )

            spin.valueChanged.connect(
                self.schedule_segmentation_preview_update
            )

        self.reset_hsv_button = QPushButton(
            "Reset Defaults"
        )

        self.reset_hsv_button.setObjectName(
            "smallButton"
        )

        self.reset_hsv_button.clicked.connect(
            self.reset_hsv
        )

        hsv_layout.addWidget(
            self.reset_hsv_button
        )

        hsv_layout.addStretch(
            1
        )

        root.addWidget(
            self.hsv_container,
            0
        )

        self.hsv_container.hide()

        # ====================================================
        # Custom Segmentation
        # ====================================================

        self.custom_container = QWidget()

        custom_layout = QHBoxLayout(
            self.custom_container
        )

        custom_layout.setContentsMargins(
            0,
            2,
            0,
            0
        )

        custom_layout.setSpacing(
            7
        )

        custom_title = QLabel(
            "Custom:"
        )

        custom_title.setObjectName(
            "fieldLabel"
        )

        custom_layout.addWidget(
            custom_title
        )

        self.custom_button = QPushButton(
            "Select Custom .py"
        )

        self.custom_button.setObjectName(
            "smallButton"
        )

        self.custom_button.clicked.connect(
            self.select_custom_segmentation
        )

        custom_layout.addWidget(
            self.custom_button
        )

        self.custom_path_label = QLineEdit(
            "Custom: not selected"
        )

        self.configure_path_field(
            self.custom_path_label
        )

        custom_layout.addWidget(
            self.custom_path_label,
            stretch=1
        )

        root.addWidget(
            self.custom_container,
            0
        )

        self.custom_container.hide()

        # ====================================================
        # Progress / Status
        # ====================================================

        progress_row = QHBoxLayout()

        progress_row.setContentsMargins(
            1,
            0,
            1,
            0
        )

        progress_row.setSpacing(
            8
        )

        self.status = QLabel(
            "Ready"
        )

        self.status.setObjectName(
            "statusLabel"
        )

        self.status.setMinimumWidth(
            250
        )

        self.status.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Fixed
        )

        self.progress = QProgressBar()

        self.progress.setMinimum(
            0
        )

        self.progress.setMaximum(
            100
        )

        self.progress.setTextVisible(
            True
        )

        self.progress.setFixedHeight(
            20
        )

        self.progress.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

        progress_row.addWidget(
            self.status
        )

        progress_row.addWidget(
            self.progress,
            stretch=1
        )

        root.addLayout(
            progress_row,
            0
        )

        # ====================================================
        # Preview
        # ====================================================

        self.preview = PreviewPanel()

        self.preview.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        root.addWidget(
            self.preview,
            stretch=1
        )

        # ====================================================
        # Log
        # ====================================================

        self.log = QTextEdit()

        self.log.setReadOnly(
            True
        )

        self.log.setFixedHeight(
            54
        )

        self.log.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.log.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.log.setPlaceholderText(
            "Latest processing messages"
        )

        root.addWidget(
            self.log,
            0
        )

        self.setLayout(
            root
        )

    # ========================================================
    # Visual Style
    # ========================================================

    def apply_style(self):

        self.setStyleSheet(
            """
            QWidget {
                font-family: "Segoe UI";
                font-size: 10pt;
            }

            QGroupBox {
                font-size: 10pt;
                font-weight: 600;
                border: 1px solid #cfd5dc;
                border-radius: 8px;
                margin-top: 9px;
                padding-top: 7px;
                background: #ffffff;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
                color: #3f4752;
                background: #ffffff;
            }

            QLabel#fieldLabel {
                color: #56616c;
                font-size: 9pt;
            }

            QLabel#statusLabel {
                color: #4d5661;
                font-weight: 600;
                padding-left: 2px;
            }

            QLineEdit#pathField {
                min-height: 32px;
                border: 1px solid #d7dce2;
                border-radius: 5px;
                padding: 3px 8px;
                background: #f7f8fa;
                color: #67717b;
                selection-background-color: #b9d2e5;
            }

            QPushButton {
                min-height: 34px;
                border-radius: 6px;
                border: 1px solid #c7cdd4;
                padding: 5px 12px;
                background: #f7f8fa;
                color: #252b31;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #eef1f4;
            }

            QPushButton:pressed {
                background: #e5e9ed;
            }

            QPushButton:disabled {
                color: #9aa2ab;
                background: #f1f3f5;
            }

            QPushButton#secondaryButton {
                min-height: 38px;
                font-size: 10pt;
            }

            QPushButton#startButton {
                min-height: 78px;
                font-size: 10pt;
                background: #2f6f9f;
                color: white;
                border: 1px solid #285e87;
            }

            QPushButton#startButton:hover {
                background: #3479ad;
            }

            QPushButton#startButton:pressed {
                background: #285f88;
            }

            QPushButton#smallButton {
                min-height: 32px;
                font-size: 9pt;
                font-weight: 500;
                padding-left: 10px;
                padding-right: 10px;
            }

            QComboBox,
            QSpinBox,
            QDoubleSpinBox {
                min-height: 32px;
                border: 1px solid #cbd1d8;
                border-radius: 5px;
                padding: 3px 7px;
                background: white;
                color: #252b31;
            }

            QComboBox:focus,
            QSpinBox:focus,
            QDoubleSpinBox:focus {
                border: 1px solid #6e9ab9;
            }

            QProgressBar {
                border: 1px solid #cbd1d8;
                border-radius: 5px;
                background: #f1f3f5;
                text-align: center;
                color: #4b545e;
            }

            QProgressBar::chunk {
                background: #6f9fbd;
                border-radius: 4px;
            }

            QTextEdit {
                border: 1px solid #d0d5db;
                border-radius: 6px;
                background: #fbfcfd;
                color: #4d5661;
                padding: 4px 6px;
                font-family: "Consolas";
                font-size: 8.5pt;
            }
            """
        )

    # ========================================================
    # About dialog
    # ========================================================

    def show_about(self):

        if self.about_dialog is None:

            dialog = QDialog(
                self
            )

            dialog.setWindowTitle(
                "About Canopy CCGR"
            )

            dialog.setWindowIcon(
                self.application_icon
            )

            dialog.setModal(
                True
            )

            dialog.setFixedSize(
                520,
                430
            )

            layout = QVBoxLayout(
                dialog
            )

            layout.setContentsMargins(
                24,
                20,
                24,
                18
            )

            layout.setSpacing(
                10
            )

            title = QLabel(
                f"{self.SOFTWARE_NAME}"
            )

            title.setAlignment(
                Qt.AlignCenter
            )

            title.setStyleSheet(
                """
                QLabel {
                    color: #57863c;
                    font-size: 18px;
                    font-weight: 700;
                    padding: 2px 0px 0px 0px;
                }
                """
            )

            version = QLabel(
                f"Version {self.SOFTWARE_VERSION}"
            )

            version.setAlignment(
                Qt.AlignCenter
            )

            version.setStyleSheet(
                """
                QLabel {
                    color: #56616c;
                    font-size: 10pt;
                    padding-bottom: 4px;
                }
                """
            )

            intro = QLabel(
                "This software is the updated Python implementation of the "
                "Canopy CCGR computational code previously released "
                "through MATLAB Versions 1 and 2 on Code Ocean."
            )

            intro.setWordWrap(
                True
            )

            intro.setStyleSheet(
                """
                QLabel {
                    color: #3f4752;
                    font-size: 9.5pt;
                    line-height: 1.3;
                    padding: 4px 0px 6px 0px;
                }
                """
            )

            layout.addWidget(
                title
            )

            layout.addWidget(
                version
            )

            layout.addWidget(
                intro
            )

            info = QLabel(
                "<b>Historical MATLAB release</b><br>"
                "Canopy CCGR — MATLAB v2<br>"
                "<a href=\"https://codeocean.com/capsule/2177070/tree/v2\">"
                "Code Ocean capsule</a><br><br>"
                "<b>Scientific publication</b><br>"
                "Haghshenas, A. &amp; Emam, Y. (2019). "
                "<i>Image-based tracking of ripening in wheat cultivar mixtures: "
                "A quantifying approach parallel to the conventional phenology.</i><br>"
                "<a href=\"https://doi.org/10.1016/j.compag.2018.11.020\">"
                "DOI: 10.1016/j.compag.2018.11.020</a><br><br>"
                "<b>Developer</b><br>"
                "Abbas Haghshenas — Easy Phenotyping Lab (EPL)<br>"
                "<a href=\"https://haqueshenas.github.io/EPL\">"
                "https://haqueshenas.github.io/EPL</a><br>"
                "<a href=\"mailto:haqueshenas@gmail.com\">"
                "haqueshenas@gmail.com</a><br><br>"
                "<b>License</b>: MIT License<br>"
                "Copyright (c) 2026 Abbas Haghshenas"
            )

            info.setOpenExternalLinks(
                True
            )

            info.setWordWrap(
                True
            )

            info.setStyleSheet(
                """
                QLabel {
                    color: #3f4752;
                    font-size: 9pt;
                    padding: 2px 0px;
                }
                QLabel a {
                    color: #57863c;
                    text-decoration: none;
                }
                """
            )

            layout.addWidget(
                info,
                stretch=1
            )

            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok,
                parent=dialog
            )

            buttons.accepted.connect(
                dialog.accept
            )

            layout.addWidget(
                buttons
            )

            self.about_dialog = dialog

        self.center_dialog(
            self.about_dialog
        )

        self.about_dialog.exec()

    # ========================================================
    # Center a dialog on the active screen
    # ========================================================

    def center_dialog(
            self,
            dialog):

        screen = self.screen()

        if screen is None:

            screen = QApplication.primaryScreen()

        if screen is None:

            return

        available = screen.availableGeometry()
        geometry = dialog.frameGeometry()
        geometry.moveCenter(
            available.center()
        )
        dialog.move(
            geometry.topLeft()
        )

    # ========================================================
    # Path Field Helper
    # ========================================================

    @staticmethod
    def configure_path_field(
            field):

        field.setObjectName(
            "pathField"
        )

        field.setReadOnly(
            True
        )

        field.setMinimumHeight(
            32
        )

        field.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )

    # ========================================================
    # Find first input image
    # ========================================================

    def find_first_input_image(self):

        if not self.input_folder:

            return None

        input_folder = Path(
            self.input_folder
        )

        files = []

        for ext in self.IMAGE_EXTENSIONS:

            files.extend(
                input_folder.glob(ext)
            )

        files = sorted(
            files
        )

        if not files:

            return None

        return files[0]

    # ========================================================
    # Prepare segmentation preview image
    # ========================================================
    #
    # IMPORTANT:
    #
    # The image remains FULL RESOLUTION.
    #
    # No resize occurs before create_mask().
    #

    def prepare_segmentation_preview(self):

        if not self.input_folder:

            return

        first_image = (
            self.find_first_input_image()
        )

        if first_image is None:

            self.segmentation_preview_image = None
            self.segmentation_preview_path = None

            self.preview.clear_segmentation_views()

            self.status.setText(
                "Segmentation preview unavailable: "
                "no supported image found."
            )

            return

        method = (
            self.method_combo.currentText()
        )

        # ----------------------------------------------------
        # Custom requires a selected Python file.
        # ----------------------------------------------------

        if (
                method == "Custom"
                and
                not self.custom_segmentation_path
        ):

            self.segmentation_preview_image = None
            self.segmentation_preview_path = None

            self.preview.clear_segmentation_views()

            self.status.setText(
                "Custom preview unavailable: "
                "select a Custom .py file."
            )

            return

        # ----------------------------------------------------
        # Reuse the cached FULL-RESOLUTION image when the
        # folder's first image has not changed.
        # ----------------------------------------------------

        if (
                self.segmentation_preview_path is not None
                and
                Path(
                    self.segmentation_preview_path
                ) == first_image
                and
                self.segmentation_preview_image is not None
        ):

            self.update_segmentation_preview()

            return

        try:

            analyzer = CanopyAnalyzer(

                segmentation_method=method,

                hsv_parameters=self.get_hsv_parameters(),

                custom_segmentation_path=(
                    self.custom_segmentation_path
                )

            )

            # IMPORTANT:
            #
            # load_image() loads the ORIGINAL image.
            #

            image = analyzer.load_image(
                first_image
            )

            self.segmentation_preview_image = (
                np.ascontiguousarray(
                    image
                )
            )

            self.segmentation_preview_path = (
                first_image
            )

            self.update_segmentation_preview()

        except Exception as e:

            self.segmentation_preview_image = None
            self.segmentation_preview_path = None

            self.preview.clear_segmentation_views()

            self.status.setText(
                "Segmentation preview unavailable."
            )

            print(
                f"ERROR loading segmentation preview "
                f"{first_image.name}: {e}"
            )

    # ========================================================
    # Create display-sized image and mask
    # ========================================================
    #
    # IMPORTANT:
    #
    # This method is for DISPLAY ONLY.
    #
    # The mask must already have been calculated on the
    # full-resolution image.
    #

    def create_preview_display_data(
            self,
            image,
            mask):

        if image is None:

            return (
                image,
                mask
            )

        height, width = (
            image.shape[:2]
        )

        max_dimension = max(
            height,
            width
        )

        if max_dimension <= (
                self.SEGMENTATION_PREVIEW_MAX_DIM):

            return (

                np.ascontiguousarray(
                    image
                ),

                np.ascontiguousarray(
                    mask
                )

            )

        scale = (

            self.SEGMENTATION_PREVIEW_MAX_DIM
            /
            max_dimension

        )

        new_width = max(
            1,
            int(
                round(
                    width * scale
                )
            )
        )

        new_height = max(
            1,
            int(
                round(
                    height * scale
                )
            )
        )

        display_image = cv2.resize(

            image,

            (
                new_width,
                new_height
            ),

            interpolation=cv2.INTER_AREA

        )

        display_mask = cv2.resize(

            mask,

            (
                new_width,
                new_height
            ),

            interpolation=cv2.INTER_NEAREST

        )

        return (

            np.ascontiguousarray(
                display_image
            ),

            np.ascontiguousarray(
                display_mask
            )

        )

    # ========================================================
    # Schedule live segmentation preview update
    # ========================================================
    #
    # At present only HSV has continuously changing
    # parameters, so only HSV requires debounce.
    #

    def schedule_segmentation_preview_update(
            self,
            *args):

        if self.method_combo.currentText() != "HSV":

            return

        if self.segmentation_preview_image is None:

            return

        self.segmentation_preview_timer.start()

    # ========================================================
    # Update segmentation preview
    # ========================================================
    #
    # SINGLE live-preview path for:
    #
    # G>R
    # G>R&G>B
    # 2G-R-B>0
    # HSV
    # Custom
    #
    # IMPORTANT:
    #
    # The mask is always calculated on the FULL-RESOLUTION
    # image through CanopyAnalyzer.create_mask().
    #

    def update_segmentation_preview(self):

        if self.segmentation_preview_image is None:

            return

        method = (
            self.method_combo.currentText()
        )

        # ----------------------------------------------------
        # Custom requires a selected file.
        # ----------------------------------------------------

        if (
                method == "Custom"
                and
                not self.custom_segmentation_path
        ):

            self.preview.clear_segmentation_views()

            self.status.setText(
                "Custom preview unavailable: "
                "select a Custom .py file."
            )

            return

        # ----------------------------------------------------
        # HSV validation for live preview.
        # ----------------------------------------------------

        if method == "HSV":

            if not self.are_hsv_parameters_valid():

                self.preview.clear_segmentation_views()

                self.status.setText(
                    "HSV preview paused: "
                    "minimum must not exceed maximum."
                )

                return

        try:

            # ------------------------------------------------
            # SAME engine and SAME segmentation algorithm
            # as the actual processing pipeline.
            #
            # The image is FULL RESOLUTION.
            # ------------------------------------------------

            analyzer = CanopyAnalyzer(

                segmentation_method=method,

                hsv_parameters=self.get_hsv_parameters(),

                custom_segmentation_path=(
                    self.custom_segmentation_path
                )

            )

            full_resolution_mask = (
                analyzer.create_mask(
                    self.segmentation_preview_image
                )
            )

            # ------------------------------------------------
            # ONLY NOW create display-sized copies.
            # ------------------------------------------------

            display_image, display_mask = (
                self.create_preview_display_data(

                    self.segmentation_preview_image,

                    full_resolution_mask

                )
            )

            # ------------------------------------------------
            # Update only segmentation images.
            #
            # CC / GR / CCGR remain untouched.
            # ------------------------------------------------

            self.preview.update_segmentation_preview(

                display_image,

                display_mask

            )

            if self.segmentation_preview_path is not None:

                if method == "Custom":

                    custom_name = (
                        Path(
                            self.custom_segmentation_path
                        ).name
                    )

                    self.status.setText(

                        f"Preview — Custom "
                        f"({custom_name}) — "
                        f"{self.segmentation_preview_path.name}"

                    )

                else:

                    self.status.setText(

                        f"Preview — {method} — "
                        f"{self.segmentation_preview_path.name}"

                    )

        except Exception as e:

            self.preview.clear_segmentation_views()

            self.status.setText(
                "Segmentation preview update failed."
            )

            print(
                f"ERROR updating segmentation preview: {e}"
            )

    # ========================================================
    # Check HSV parameters without warning dialog
    # ========================================================

    def are_hsv_parameters_valid(self):

        h_min = (
            self.h_spin["H_min"].value()
        )

        h_max = (
            self.h_spin["H_max"].value()
        )

        s_min = (
            self.h_spin["S_min"].value()
        )

        s_max = (
            self.h_spin["S_max"].value()
        )

        v_min = (
            self.h_spin["V_min"].value()
        )

        v_max = (
            self.h_spin["V_max"].value()
        )

        return (

            h_min <= h_max
            and
            s_min <= s_max
            and
            v_min <= v_max

        )

    # ========================================================
    # Segmentation method
    # ========================================================

    def toggle_segmentation_method(
            self,
            text):

        # ----------------------------------------------------
        # Stop any pending HSV refresh.
        # ----------------------------------------------------

        self.segmentation_preview_timer.stop()

        # ----------------------------------------------------
        # Show / hide HSV controls.
        # ----------------------------------------------------

        if text == "HSV":

            self.hsv_container.show()

        else:

            self.hsv_container.hide()

        # ----------------------------------------------------
        # Show / hide Custom controls.
        # ----------------------------------------------------

        if text == "Custom":

            self.custom_container.show()

        else:

            self.custom_container.hide()

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Changing segmentation method ALWAYS refreshes the
        # live segmentation preview.
        # ----------------------------------------------------

        if self.segmentation_preview_image is not None:

            self.update_segmentation_preview()

        elif self.input_folder:

            self.prepare_segmentation_preview()

    # ========================================================
    # Select Custom segmentation file
    # ========================================================

    def select_custom_segmentation(self):

        file_path, _ = QFileDialog.getOpenFileName(

            self,

            "Select Custom Segmentation Python File",

            "",

            "Python files (*.py);;All files (*.*)"

        )

        if not file_path:

            return

        self.custom_segmentation_path = (
            file_path
        )

        self.custom_path_label.setText(
            f"Custom: {file_path}"
        )

        self.custom_path_label.setToolTip(
            file_path
        )

        # ----------------------------------------------------
        # If Custom is currently selected, refresh the
        # segmentation preview immediately.
        # ----------------------------------------------------

        if (
                self.method_combo.currentText()
                ==
                "Custom"
        ):

            if self.segmentation_preview_image is None:

                self.prepare_segmentation_preview()

            else:

                self.update_segmentation_preview()

    # ========================================================
    # Validate Custom segmentation file
    # ========================================================
    #
    # This verifies that the file can be loaded and that it
    # contains a callable create_mask() function.
    #
    # The actual mask shape/content is validated when the
    # image is processed.
    #

    def validate_custom_segmentation(self):

        if self.method_combo.currentText() != "Custom":

            return True

        if not self.custom_segmentation_path:

            QMessageBox.warning(
                self,
                "Missing Custom Segmentation",
                "Please select a Custom .py segmentation file."
            )

            return False

        try:

            # ------------------------------------------------
            # Use the same engine loader used by actual
            # processing.
            # ------------------------------------------------

            CanopyAnalyzer(

                segmentation_method="Custom",

                custom_segmentation_path=(
                    self.custom_segmentation_path
                )

            )

        except Exception as e:

            QMessageBox.warning(

                self,

                "Invalid Custom Segmentation",

                str(e)

            )

            return False

        return True

    # ========================================================
    # Reset HSV
    # ========================================================

    def reset_hsv(self):

        for key, value in (
                self.HSV_DEFAULTS.items()
        ):

            self.h_spin[key].setValue(
                value
            )

        self.schedule_segmentation_preview_update()

    # ========================================================
    # Get HSV parameters
    # ========================================================

    def get_hsv_parameters(self):

        return {

            "H_min":
                self.h_spin["H_min"].value(),

            "H_max":
                self.h_spin["H_max"].value(),

            "S_min":
                self.h_spin["S_min"].value(),

            "S_max":
                self.h_spin["S_max"].value(),

            "V_min":
                self.h_spin["V_min"].value(),

            "V_max":
                self.h_spin["V_max"].value(),

        }

    # ========================================================
    # Validate HSV parameters
    # ========================================================

    def validate_hsv_parameters(self):

        if self.method_combo.currentText() != "HSV":

            return True

        h_min = (
            self.h_spin["H_min"].value()
        )

        h_max = (
            self.h_spin["H_max"].value()
        )

        s_min = (
            self.h_spin["S_min"].value()
        )

        s_max = (
            self.h_spin["S_max"].value()
        )

        v_min = (
            self.h_spin["V_min"].value()
        )

        v_max = (
            self.h_spin["V_max"].value()
        )

        if h_min > h_max:

            QMessageBox.warning(
                self,
                "Invalid HSV Parameters",
                "H minimum must not be greater "
                "than H maximum."
            )

            return False

        if s_min > s_max:

            QMessageBox.warning(
                self,
                "Invalid HSV Parameters",
                "S minimum must not be greater "
                "than S maximum."
            )

            return False

        if v_min > v_max:

            QMessageBox.warning(
                self,
                "Invalid HSV Parameters",
                "V minimum must not be greater "
                "than V maximum."
            )

            return False

        return True

    # ========================================================
    # Folder Selection
    # ========================================================

    def select_input(self):

        folder = QFileDialog.getExistingDirectory(

            self,

            "Select Images Folder"

        )

        if folder:

            self.input_folder = folder

            self.input_label.setText(
                f"Input: {folder}"
            )

            self.input_label.setToolTip(
                folder
            )

            # ------------------------------------------------
            # Clear the cached preview.
            # The first image of the newly selected folder
            # becomes the new preview image.
            # ------------------------------------------------

            self.segmentation_preview_timer.stop()

            self.segmentation_preview_image = None

            self.segmentation_preview_path = None

            self.prepare_segmentation_preview()

    def select_output(self):

        folder = QFileDialog.getExistingDirectory(

            self,

            "Select Output Folder"

        )

        if folder:

            self.output_folder = folder

            self.output_label.setText(
                f"Output: {folder}"
            )

            self.output_label.setToolTip(
                folder
            )

    # ========================================================
    # Start Processing
    # ========================================================

    def start(self):

        # ----------------------------------------------------
        # Validate folders
        # ----------------------------------------------------

        if not self.input_folder:

            QMessageBox.warning(
                self,
                "Missing Input Folder",
                "Please select the image folder."
            )

            return

        if not self.output_folder:

            QMessageBox.warning(
                self,
                "Missing Output Folder",
                "Please select the output folder."
            )

            return

        # ----------------------------------------------------
        # Validate HSV
        # ----------------------------------------------------

        if not self.validate_hsv_parameters():

            return

        # ----------------------------------------------------
        # Validate Custom
        # ----------------------------------------------------

        if not self.validate_custom_segmentation():

            return

        # ----------------------------------------------------
        # Capture the exact configuration of this run.
        # ----------------------------------------------------

        self.processing_start_time = datetime.now()
        self.processing_end_time = None
        self.processing_image_names = []
        self.processing_total_images = 0

        self.processing_input_folder = self.input_folder
        self.processing_output_folder = self.output_folder
        self.processing_method = self.method_combo.currentText()
        self.processing_gr_max = self.gr_max_spin.value()
        self.processing_hsv = self.get_hsv_parameters()
        self.processing_custom_path = self.custom_segmentation_path

        # ----------------------------------------------------
        # Stop any pending interactive preview update before
        # starting the actual folder-processing worker.
        # ----------------------------------------------------

        self.segmentation_preview_timer.stop()

        # ----------------------------------------------------
        # Store exact GRmax used by this run.
        # ----------------------------------------------------

        self.processing_gr_max = (
            self.gr_max_spin.value()
        )

        # ----------------------------------------------------
        # Prepare GUI
        # ----------------------------------------------------

        self.log.clear()

        self.progress.setValue(
            0
        )

        self.progress.setVisible(
            True
        )

        self.status.setText(
            "Starting processing..."
        )

        self.run_button.setEnabled(
            False
        )

        # Prevent GRmax from changing during processing.
        self.gr_max_spin.setEnabled(
            False
        )

        # ----------------------------------------------------
        # Parameters
        # ----------------------------------------------------

        hsv = (
            self.get_hsv_parameters()
        )

        method = (
            self.method_combo.currentText()
        )

        custom_path = (
            self.custom_segmentation_path
        )

        # ----------------------------------------------------
        # New worker
        # ----------------------------------------------------

        self.thread = ProcessingThread(

            self.input_folder,

            self.output_folder,

            method,

            hsv,

            self.processing_gr_max,

            custom_path

        )

        # ----------------------------------------------------
        # Signals
        # ----------------------------------------------------

        self.thread.progress.connect(
            self.update_progress
        )

        self.thread.preview.connect(
            self.preview.update_preview
        )

        self.thread.processing_finished.connect(
            self.done
        )

        self.thread.error.connect(
            self.show_error
        )

        # ----------------------------------------------------
        # Start
        # ----------------------------------------------------

        self.thread.start()

    # ========================================================
    # Progress Update
    # ========================================================

    def update_progress(
            self,
            current,
            total,
            name):

        self.processing_total_images = int(
            total
        )

        if name not in self.processing_image_names:

            self.processing_image_names.append(
                name
            )

        self.progress.setMaximum(
            total
        )

        self.progress.setValue(
            current
        )

        message = (
            f"Processing image "
            f"{current}/{total}\n"
            f"File: {name}"
        )

        self.status.setText(
            message.replace(
                "\n",
                "   "
            )
        )

        self.log.append(
            message
        )

    # ========================================================
    # Processing Log
    # ========================================================

    def write_processing_log(
            self,
            dataframe=None,
            status="Completed successfully",
            error_message=None):

        if not self.processing_output_folder:

            return

        output_folder = Path(
            self.processing_output_folder
        )

        try:

            output_folder.mkdir(
                parents=True,
                exist_ok=True
            )

            end_time = (
                self.processing_end_time
                or
                datetime.now()
            )

            start_time = (
                self.processing_start_time
                or
                end_time
            )

            duration_seconds = (
                end_time - start_time
            ).total_seconds()

            hours = int(
                duration_seconds // 3600
            )

            minutes = int(
                (duration_seconds % 3600) // 60
            )

            seconds = int(
                round(
                    duration_seconds % 60
                )
            )

            if seconds == 60:
                seconds = 0
                minutes += 1

            if minutes == 60:
                minutes = 0
                hours += 1

            duration_text = (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{seconds:02d}"
            )

            total_images = int(
                self.processing_total_images
            )

            attempted_names = list(
                self.processing_image_names
            )

            if dataframe is not None and not dataframe.empty and "Image_name" in dataframe.columns:

                successful_names = [
                    str(name)
                    for name in dataframe["Image_name"].tolist()
                ]

            else:

                successful_names = []

            successful_set = set(
                successful_names
            )

            attempted_unique = []

            for name in attempted_names:

                if name not in attempted_unique:

                    attempted_unique.append(
                        name
                    )

            lines = []

            lines.append(
                self.SOFTWARE_NAME
            )

            lines.append(
                f"Version: {self.SOFTWARE_VERSION}"
            )

            lines.append(
                "=" * 60
            )

            lines.append(
                "PROCESSING SUMMARY"
            )

            lines.append(
                "-" * 60
            )

            lines.append(
                f"Status: {status}"
            )

            lines.append(
                "Start time: "
                f"{start_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            lines.append(
                "End time: "
                f"{end_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            lines.append(
                f"Processing duration: {duration_text}"
            )

            lines.append(
                f"Images found / attempted: {total_images}"
            )

            lines.append(
                f"Images successfully analyzed: {len(successful_names)}"
            )

            lines.append(
                f"Images not successfully analyzed: "
                f"{max(0, total_images - len(successful_names))}"
            )

            lines.append(
                ""
            )

            lines.append(
                "INPUT / OUTPUT"
            )

            lines.append(
                "-" * 60
            )

            lines.append(
                f"Input folder: {self.processing_input_folder}"
            )

            lines.append(
                f"Output folder: {self.processing_output_folder}"
            )

            lines.append(
                ""
            )

            lines.append(
                "ANALYSIS SETTINGS"
            )

            lines.append(
                "-" * 60
            )

            lines.append(
                f"Segmentation method: {self.processing_method}"
            )

            lines.append(
                f"GRmax: {self.processing_gr_max:.3f}"
            )

            if self.processing_method == "HSV":

                hsv = self.processing_hsv

                lines.append(
                    f"H_min: {hsv.get('H_min', '')}"
                )
                lines.append(
                    f"H_max: {hsv.get('H_max', '')}"
                )
                lines.append(
                    f"S_min: {hsv.get('S_min', '')}"
                )
                lines.append(
                    f"S_max: {hsv.get('S_max', '')}"
                )
                lines.append(
                    f"V_min: {hsv.get('V_min', '')}"
                )
                lines.append(
                    f"V_max: {hsv.get('V_max', '')}"
                )

            else:

                lines.append(
                    "HSV parameters: Not used"
                )

            if self.processing_method == "Custom":

                custom_name = (
                    Path(
                        self.processing_custom_path
                    ).name
                    if self.processing_custom_path
                    else "Not specified"
                )

                lines.append(
                    f"Custom segmentation file: {custom_name}"
                )

                lines.append(
                    f"Custom segmentation path: {self.processing_custom_path}"
                )

            else:

                lines.append(
                    "Custom segmentation: Not used"
                )

            if error_message:

                lines.append(
                    ""
                )
                lines.append(
                    "ERROR"
                )
                lines.append(
                    "-" * 60
                )
                lines.append(
                    str(error_message)
                )

            lines.append(
                ""
            )

            lines.append(
                "IMAGE FILES"
            )

            lines.append(
                "-" * 60
            )

            if attempted_unique:

                for index, name in enumerate(
                        attempted_unique,
                        1):

                    image_status = (
                        "OK"
                        if str(name) in successful_set
                        else "FAILED / NOT IN RESULTS"
                    )

                    lines.append(
                        f"{index}. {name} [{image_status}]"
                    )

            else:

                lines.append(
                    "No image filenames were reported."
                )

            lines.append(
                ""
            )

            lines.append(
                "=" * 60
            )

            lines.append(
                "Canopy CCGR for Python — processing log"
            )

            log_path = output_folder / "Log.txt"

            log_path.write_text(
                "\n".join(lines) + "\n",
                encoding="utf-8"
            )

        except Exception as e:

            print(
                f"ERROR writing processing Log.txt: {e}"
            )

    # ========================================================
    # Processing Completed
    # ========================================================

    def done(
            self,
            dataframe):

        self.processing_end_time = datetime.now()

        successful_count = (
            len(dataframe)
            if dataframe is not None
            else 0
        )

        total_count = self.processing_total_images

        if total_count > 0 and successful_count < total_count:
            completion_message = "Completed with image-level errors."
        else:
            completion_message = "Completed successfully."

        self.status.setText(
            "Finished"
            if completion_message == "Completed successfully."
            else "Finished with errors"
        )

        # Exactly ONE completion message.
        self.log.append(
            completion_message
        )

        self.write_processing_log(
            dataframe=dataframe,
            status=completion_message
        )

        # Hide progress bar after completion.
        self.progress.setValue(
            0
        )

        self.progress.setVisible(
            False
        )

        self.run_button.setEnabled(
            True
        )

        self.gr_max_spin.setEnabled(
            True
        )

        # Check scientific/display warnings.
        self.check_gr_warnings(
            dataframe
        )

        # Clean worker safely.
        if self.thread is not None:

            self.thread.quit()

            self.thread.wait(
                2000
            )

            self.thread.deleteLater()

            self.thread = None

    # ========================================================
    # GR Warning Analysis
    # ========================================================

    def check_gr_warnings(
            self,
            dataframe):

        if dataframe is None:

            return

        if dataframe.empty:

            return

        method = (
            self.method_combo.currentText()
        )

        # Use the exact value that was used for the
        # current processing run.
        gr_max = (
            self.processing_gr_max
        )

        # ----------------------------------------------------
        # GR > current GRmax
        # ----------------------------------------------------

        high_gr = dataframe[
            dataframe["GR"] > gr_max
        ]

        # ----------------------------------------------------
        # GR < 0
        # ----------------------------------------------------

        negative_gr = dataframe[
            dataframe["GR"] < 0
        ]

        warnings = []

        # ----------------------------------------------------
        # High GR
        # ----------------------------------------------------

        if not high_gr.empty:

            lines = []

            for _, row in (
                    high_gr.iterrows()
            ):

                lines.append(
                    f"• {row['Image_name']} "
                    f"— GR = {row['GR']:.4f}"
                )

            max_collection_gr = (
                float(
                    high_gr["GR"].max()
                )
            )

            warnings.append(
                "GR exceeds the current graph "
                f"visualization limit "
                f"(GRmax = {gr_max:.3f}).\n\n"
                + "\n".join(lines)
                + "\n\n"
                f"Maximum GR in this collection: "
                f"{max_collection_gr:.4f}\n\n"
                "Change GRmax in Analysis Setup to at "
                "least the maximum GR above and run "
                "the analysis again to regenerate the "
                "graphs.\n\n"
                "The numerical results in Results.csv "
                "are unchanged."
            )

        # ----------------------------------------------------
        # Negative GR
        # ----------------------------------------------------

        if not negative_gr.empty:

            lines = []

            for _, row in (
                    negative_gr.iterrows()
            ):

                lines.append(
                    f"• {row['Image_name']} "
                    f"— GR = {row['GR']:.4f}"
                )

            if method == "G>R":

                warnings.append(
                    "Negative GR detected with the "
                    "original G>R method.\n\n"
                    + "\n".join(lines)
                    + "\n\n"
                    "With G>R segmentation, each selected "
                    "vegetation pixel satisfies G > R. "
                    "A negative GR therefore indicates an "
                    "unexpected inconsistency and should "
                    "be investigated.\n\n"
                    "The numerical results have NOT "
                    "been modified."
                )

            else:

                warnings.append(
                    "Negative GR values detected.\n\n"
                    + "\n".join(lines)
                    + "\n\n"
                    "With the selected alternative "
                    "segmentation method, negative GR "
                    "values can occur because the selected "
                    "pixels are not necessarily G > R.\n\n"
                    "This does not by itself indicate an "
                    "error in the calculation. The numerical "
                    "results have NOT been modified."
                )

        # ----------------------------------------------------
        # No warning
        # ----------------------------------------------------

        if not warnings:

            return

        message = (
            "Analysis completed.\n\n"
            "Warnings requiring attention:\n\n"
            + "\n\n".join(warnings)
        )

        QMessageBox.warning(
            self,
            "CanopyCCGR — GR Warning",
            message
        )

    # ========================================================
    # Processing Error
    # ========================================================

    def show_error(
            self,
            message):

        self.processing_end_time = datetime.now()

        self.status.setText(
            "Processing failed"
        )

        self.write_processing_log(
            dataframe=None,
            status="Processing failed",
            error_message=message
        )

        self.progress.setValue(
            0
        )

        self.progress.setVisible(
            False
        )

        self.run_button.setEnabled(
            True
        )

        self.gr_max_spin.setEnabled(
            True
        )

        self.log.append(
            f"ERROR: {message}"
        )

        QMessageBox.critical(
            self,
            "Processing Error",
            message
        )

        if self.thread is not None:

            self.thread.quit()

            self.thread.wait(
                2000
            )

            self.thread.deleteLater()

            self.thread = None
