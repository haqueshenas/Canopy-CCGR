"""
Canopy CCGR for Python
Version 1.0.0

Visualization module for Canopy CCGR.

This module visualizes already-calculated scientific
values and generates:

```
- Individual CC/GR/CCGR graphs
- Vector PDF graphs
- High-resolution PNG previews
- Comparison Atlas
```

IMPORTANT:
This module does not perform or modify scientific
calculations.

Scientific values are supplied by CanopyAnalyzer.

Scientific basis:
Haghshenas, A. & Emam, Y. (2019).
Image-based tracking of ripening in wheat cultivar
mixtures: A quantifying approach parallel to the
conventional phenology.
Computers and Electronics in Agriculture, 156,
318-333.
https://doi.org/10.1016/j.compag.2018.11.020

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

import matplotlib

# Important when figures are generated from a PySide6 worker thread.
matplotlib.use("Agg")

from pathlib import Path
import math
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.backends.backend_pdf import PdfPages


class CCGRVisualizer:

    def __init__(
            self,
            gr_max=0.3):

        self.gr_max = float(
            gr_max
        )

    # =====================================================
    # Draw borderless filled circle
    # =====================================================

    @staticmethod
    def add_circle(
            ax,
            radius,
            color):

        circle = Circle(

            (0.0, 0.0),

            radius,

            facecolor=color,

            edgecolor="none",

            linewidth=0

        )

        ax.add_patch(
            circle
        )

    # =====================================================
    # Configure equal circular axes
    # =====================================================

    @staticmethod
    def setup_axis(ax):

        ax.set_aspect(
            "equal",
            adjustable="box"
        )

        ax.axis(
            "off"
        )

        ax.set_xlim(
            -1.10,
            1.10
        )

        ax.set_ylim(
            -1.10,
            1.10
        )

    # =====================================================
    # Convert actual index to display intensity
    # =====================================================

    def display_intensity(
            self,
            value):

        return float(
            value
        ) / self.gr_max

    # =====================================================
    # Normal graph
    # =====================================================

    def create_normal_graph(
            self,
            CC,
            GR,
            CCGR,
            output_path):

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        fig, axes = plt.subplots(
            1,
            2,
            figsize=(8, 4),
            dpi=300
        )

        # =================================================
        # LEFT:
        #
        # fixed black total-area circle
        # +
        # vegetation circle whose AREA = CC
        #
        # =================================================

        ax = axes[0]

        self.setup_axis(
            ax
        )

        # Total area
        self.add_circle(
            ax,
            1.0,
            (0.0, 0.0, 0.0)
        )

        # Area proportional to CC
        cc_radius = (
            max(
                0.0,
                min(
                    1.0,
                    float(CC)
                )
            )
            ** 0.5
        )

        gr_intensity = (
            max(
                0.0,
                min(
                    1.0,
                    self.display_intensity(GR)
                )
            )
        )

        self.add_circle(
            ax,
            cc_radius,
            (
                0.0,
                gr_intensity,
                0.0
            )
        )

        ax.text(
            0,
            -1.18,
            f"CC={CC:.3f}\nGR={GR:.3f}",
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold"
        )

        # =================================================
        # RIGHT:
        #
        # one fixed-size circle
        # color = CCGR
        #
        # =================================================

        ax = axes[1]

        self.setup_axis(
            ax
        )

        ccgr_intensity = (
            max(
                0.0,
                min(
                    1.0,
                    self.display_intensity(CCGR)
                )
            )
        )

        self.add_circle(
            ax,
            1.0,
            (
                0.0,
                ccgr_intensity,
                0.0
            )
        )

        ax.text(
            0,
            -1.18,
            f"CCGR={CCGR:.3f}",
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold"
        )

        plt.tight_layout()

        # -------------------------------------------------
        # Vector PDF
        # -------------------------------------------------

        fig.savefig(
            output_path.with_suffix(".pdf"),
            format="pdf",
            bbox_inches="tight"
        )

        # -------------------------------------------------
        # High-resolution raster preview
        # -------------------------------------------------

        fig.savefig(
            output_path.with_suffix(".png"),
            dpi=300,
            bbox_inches="tight"
        )

        plt.close(
            fig
        )

    # =====================================================
    # Out-of-range graph
    # =====================================================

    def create_out_of_range_graph(
            self,
            GR,
            output_path,
            message):

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        fig, ax = plt.subplots(
            figsize=(8, 4),
            dpi=300
        )

        ax.axis(
            "off"
        )

        text = (

            "Out of range value!\n\n"

            f"GR = {GR:.3f}\n"

            f"GRmax = {self.gr_max:.3f}\n\n"

            f"{message}\n\n"

            "This affects only the graph display.\n"

            "The numerical result is unchanged."

        )

        ax.text(
            0.5,
            0.5,
            text,
            ha="center",
            va="center",
            fontsize=13,
            fontweight="bold",
            transform=ax.transAxes
        )

        plt.tight_layout()

        fig.savefig(
            output_path.with_suffix(".pdf"),
            format="pdf",
            bbox_inches="tight"
        )

        fig.savefig(
            output_path.with_suffix(".png"),
            dpi=300,
            bbox_inches="tight"
        )

        plt.close(
            fig
        )

    # =====================================================
    # Helpers for comparison atlas
    # =====================================================

    @staticmethod
    def _clip_unit(
            value):

        value = float(
            value
        )

        if not math.isfinite(
            value
        ):

            return 0.0

        return max(
            0.0,
            min(
                1.0,
                value
            )
        )

    @staticmethod
    def _format_atlas_name(
            name,
            width=30):

        name = str(
            name
        )

        lines = textwrap.wrap(

            name,

            width=width,

            max_lines=2,

            placeholder="…",

            break_long_words=True,

            break_on_hyphens=False

        )

        if not lines:

            return name

        return "\n".join(
            lines
        )

    # =====================================================
    # Draw one comparison-atlas cell
    # =====================================================

    def draw_atlas_cell(
            self,
            ax,
            result):

        ax.set_xlim(
            0.0,
            1.0
        )

        ax.set_ylim(
            0.0,
            1.0
        )

        ax.set_aspect(
            "equal"
        )

        ax.axis(
            "off"
        )

        CC = float(
            result["CC"]
        )

        GR = float(
            result["GR"]
        )

        CCGR = float(
            result["CCGR"]
        )

        name = self._format_atlas_name(
            result["Image_name"]
        )

        # -------------------------------------------------
        # Mini graph titles
        # -------------------------------------------------

        ax.text(
            0.25,
            0.90,
            "CC + GR",
            ha="center",
            va="center",
            fontsize=8.5,
            fontweight="bold"
        )

        ax.text(
            0.75,
            0.90,
            "CCGR",
            ha="center",
            va="center",
            fontsize=8.5,
            fontweight="bold"
        )

        # -------------------------------------------------
        # Geometry
        # -------------------------------------------------

        left_x = 0.25
        right_x = 0.75
        center_y = 0.53
        outer_radius = 0.20

        # -------------------------------------------------
        # Normal graph
        # -------------------------------------------------

        if 0.0 <= GR <= self.gr_max:

            # Total area circle
            ax.add_patch(
                Circle(
                    (left_x, center_y),
                    outer_radius,
                    facecolor=(0.0, 0.0, 0.0),
                    edgecolor="none",
                    linewidth=0
                )
            )

            # Vegetation area = CC
            cc_radius = (

                self._clip_unit(
                    CC
                )
                ** 0.5

            ) * outer_radius

            gr_intensity = self._clip_unit(
                self.display_intensity(
                    GR
                )
            )

            ax.add_patch(
                Circle(
                    (left_x, center_y),
                    cc_radius,
                    facecolor=(
                        0.0,
                        gr_intensity,
                        0.0
                    ),
                    edgecolor="none",
                    linewidth=0
                )
            )

            # CCGR circle
            ccgr_intensity = self._clip_unit(
                self.display_intensity(
                    CCGR
                )
            )

            ax.add_patch(
                Circle(
                    (right_x, center_y),
                    outer_radius,
                    facecolor=(
                        0.0,
                        ccgr_intensity,
                        0.0
                    ),
                    edgecolor="none",
                    linewidth=0
                )
            )

            # Compact values
            ax.text(
                left_x,
                0.23,
                f"CC={CC:.3f}\nGR={GR:.3f}",
                ha="center",
                va="center",
                fontsize=7.2,
                fontweight="bold"
            )

            ax.text(
                right_x,
                0.23,
                f"CCGR={CCGR:.3f}",
                ha="center",
                va="center",
                fontsize=7.2,
                fontweight="bold"
            )

        # -------------------------------------------------
        # Out-of-range graph
        # -------------------------------------------------

        else:

            ax.text(
                0.5,
                0.52,
                "OUT OF RANGE",
                ha="center",
                va="center",
                fontsize=8.5,
                fontweight="bold"
            )

            ax.text(
                0.5,
                0.39,
                f"GR={GR:.3f}",
                ha="center",
                va="center",
                fontsize=7.2
            )

        # -------------------------------------------------
        # Image name
        # -------------------------------------------------

        ax.text(
            0.5,
            0.08,
            name,
            ha="center",
            va="center",
            fontsize=6.7
        )

    # =====================================================
    # Create comparison atlas
    # =====================================================

    def create_comparison_atlas(
            self,
            dataframe,
            output_folder,
            columns=5,
            rows=4):

        output_folder = Path(
            output_folder
        )

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        if dataframe is None:

            return

        if dataframe.empty:

            return

        records = dataframe.to_dict(
            orient="records"
        )

        total_items = len(
            records
        )

        items_per_page = (
            columns * rows
        )

        total_pages = math.ceil(
            total_items /
            items_per_page
        )

        output_path = (
            output_folder /
            "CCGR_Comparison_Atlas.pdf"
        )

        # -------------------------------------------------
        # A3 Landscape
        # -------------------------------------------------

        figure_width = 16.54
        figure_height = 11.69

        margin_left = 0.035
        margin_right = 0.035
        margin_bottom = 0.055
        margin_top = 0.095

        horizontal_gap = 0.008
        vertical_gap = 0.010

        cell_width = (

            1.0
            - margin_left
            - margin_right
            - (columns - 1)
            * horizontal_gap

        ) / columns

        cell_height = (

            1.0
            - margin_bottom
            - margin_top
            - (rows - 1)
            * vertical_gap

        ) / rows

        # -------------------------------------------------
        # Multi-page vector PDF
        # -------------------------------------------------

        with PdfPages(
                output_path) as pdf:

            for page_index in range(
                    total_pages):

                fig = plt.figure(
                    figsize=(
                        figure_width,
                        figure_height
                    ),
                    dpi=150,
                    facecolor="white"
                )

                start = (
                    page_index
                    * items_per_page
                )

                end = min(
                    start
                    + items_per_page,
                    total_items
                )

                page_records = records[
                    start:end
                ]

                # -------------------------------------------------
                # Page title
                # -------------------------------------------------

                fig.text(
                    0.035,
                    0.965,
                    "CanopyCCGR Comparison Atlas",
                    ha="left",
                    va="top",
                    fontsize=15,
                    fontweight="bold"
                )

                fig.text(
                    0.965,
                    0.965,
                    (
                        f"Images "
                        f"{start + 1}–{end} "
                        f"of {total_items}"
                    ),
                    ha="right",
                    va="top",
                    fontsize=8.5
                )

                # -------------------------------------------------
                # Cells
                # -------------------------------------------------

                for cell_index, record in enumerate(
                        page_records):

                    # IMPORTANT:
                    # Fill DOWN each column first.
                    #
                    # For 5 columns x 4 rows:
                    # 1,2,3,4   -> column 1
                    # 5,6,7,8   -> column 2
                    # 9,10,11,12 -> column 3
                    # and so on.
                    #

                    row_index = (
                        cell_index
                        % rows
                    )

                    column_index = (
                        cell_index
                        // rows
                    )

                    x = (

                        margin_left
                        + column_index
                        * (
                            cell_width
                            + horizontal_gap
                        )

                    )

                    y = (

                        1.0
                        - margin_top
                        - cell_height
                        - row_index
                        * (
                            cell_height
                            + vertical_gap
                        )

                    )

                    ax = fig.add_axes(
                        [
                            x,
                            y,
                            cell_width,
                            cell_height
                        ]
                    )

                    self.draw_atlas_cell(
                        ax,
                        record
                    )

                # -------------------------------------------------
                # Page number
                # -------------------------------------------------

                fig.text(
                    0.965,
                    0.018,
                    (
                        f"Page "
                        f"{page_index + 1} "
                        f"of {total_pages}"
                    ),
                    ha="right",
                    va="bottom",
                    fontsize=7.5
                )

                pdf.savefig(
                    fig,
                    bbox_inches=None
                )

                plt.close(
                    fig
                )

        return output_path

    # =====================================================
    # Main graph dispatcher
    # =====================================================

    def create_graph(
            self,
            CC,
            GR,
            CCGR,
            output_path):

        # IMPORTANT:
        # The scientific values are NOT clipped here.
        # Clipping is used only when drawing a valid graph.

        if GR > self.gr_max:

            self.create_out_of_range_graph(

                GR,

                output_path,

                (
                    "GR is higher than the current "
                    "visualization limit."
                )

            )

            return

        if GR < 0:

            self.create_out_of_range_graph(

                GR,

                output_path,

                (
                    "GR is below the visualization "
                    "range [0, GRmax]."
                )

            )

            return

        self.create_normal_graph(

            CC,

            GR,

            CCGR,

            output_path

        )

    # =====================================================
    # Create graph from result row
    # =====================================================

    def create_from_result(
            self,
            result,
            output_folder):

        output_folder = Path(
            output_folder
        )

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        name = Path(
            result["Image_name"]
        ).stem

        self.create_graph(

            float(
                result["CC"]
            ),

            float(
                result["GR"]
            ),

            float(
                result["CCGR"]
            ),

            output_folder /
            f"Graph_{name}"

        )