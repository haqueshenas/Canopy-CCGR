"""
Canopy CCGR for Python
Version 1.0.0

MATLAB-compatible image-based canopy segmentation and
vegetation-index analysis.

## Description

Canopy CCGR segments canopy images into vegetation and
non-vegetation (background) regions and calculates:

```
- Number of total, vegetation, and non-vegetation pixels
- Mean RGB values
- RGB variances
- Canopy Cover (CC)
- Green-Red index (GR)
- Canopy Cover × Green-Red index (CCGR)
- Segmented images
- CCGR visualization graphs and comparison atlas
```

## Segmentation methods currently supported

```
1. G>R
2. G>R&G>B
3. 2G-R-B>0
4. HSV
5. Custom Python segmentation
```

## Scientific basis

This Python implementation is a reimplementation and
extension of the MATLAB Canopy CCGR software previously
released in Versions 1 and 2.

The methodology is based on:

Haghshenas, A. & Emam, Y. (2019).
Image-based tracking of ripening in wheat cultivar
mixtures: A quantifying approach parallel to the
conventional phenology.
Computers and Electronics in Agriculture, 156,
318-333.
https://doi.org/10.1016/j.compag.2018.11.020

## Author

Abbas Haghshenas

Easy Phenotyping Lab (EPL)
https://haqueshenas.github.io/EPL

## Email

[haqueshenas@gmail.com](mailto:haqueshenas@gmail.com)

## Development note

The software concept, scientific design, methodological decisions, project direction, and overall development were
led by Abbas Haghshenas; the Python code was developed with coding assistance from OpenAI's GPT-5.6 Luna.

## Copyright

Copyright (c) 2026 Abbas Haghshenas

## License

MIT License

## Important scientific note

The scientific calculations are performed by this engine
on the original full-resolution input images.

Segmentation methods determine the binary mask only.
The subsequent calculations of CC, GR, CCGR, and RGB
statistics are performed by the Canopy CCGR engine.

The GUI, live preview, visualization, and Custom
segmentation interface must not alter these scientific
calculations.
"""


from pathlib import Path
import importlib.util

import cv2
import numpy as np
import pandas as pd

from visualization import CCGRVisualizer


class CanopyAnalyzer:

    def __init__(
            self,
            segmentation_method="G>R",
            hsv_parameters=None,
            gr_max=0.3,
            custom_segmentation_path=None):

        self.segmentation_method = (
            segmentation_method
        )

        self.gr_max = float(
            gr_max
        )

        self.visualizer = CCGRVisualizer(
            gr_max=self.gr_max
        )

        if hsv_parameters is None:

            self.hsv_parameters = {

                "H_min": 25,
                "H_max": 95,
                "S_min": 40,
                "S_max": 255,
                "V_min": 30,
                "V_max": 255

            }

        else:

            self.hsv_parameters = hsv_parameters

        # ----------------------------------------------------
        # Custom segmentation
        # ----------------------------------------------------
        #
        # The selected Python file is loaded only when the
        # Custom method is actually requested.
        #

        self.custom_segmentation_path = (
            custom_segmentation_path
        )

        self._custom_module = None

        self._custom_create_mask = None

        if self.segmentation_method == "Custom":

            self._load_custom_segmentation()

    # ========================================================
    # Load RGB image
    # ========================================================

    def load_image(
            self,
            path):

        img = cv2.imread(
            str(path)
        )

        if img is None:

            raise ValueError(
                f"Cannot read image: {path}"
            )

        return cv2.cvtColor(
            img,
            cv2.COLOR_BGR2RGB
        )

    # ========================================================
    # Load Custom segmentation module
    # ========================================================
    #
    # IMPORTANT:
    #
    # The external Custom Python file is executable code.
    # Only trusted files should be selected.
    #
    # Required function:
    #
    #     create_mask(image)
    #
    # ========================================================

    def _load_custom_segmentation(self):

        if not self.custom_segmentation_path:

            raise ValueError(
                "No Custom segmentation file has been selected."
            )

        custom_path = Path(
            self.custom_segmentation_path
        )

        if not custom_path.exists():

            raise ValueError(
                "Custom segmentation file does not exist:\n"
                f"{custom_path}"
            )

        if not custom_path.is_file():

            raise ValueError(
                "The selected Custom segmentation path "
                "is not a file:\n"
                f"{custom_path}"
            )

        if custom_path.suffix.lower() != ".py":

            raise ValueError(
                "Custom segmentation file must be a "
                "Python .py file."
            )

        # ----------------------------------------------------
        # Create an isolated module object.
        #
        # The module is intentionally not inserted into the
        # normal application namespace.
        # ----------------------------------------------------

        module_name = (
            "_canopyccgr_custom_segmentation"
        )

        try:

            spec = (
                importlib.util.spec_from_file_location(
                    module_name,
                    str(custom_path)
                )
            )

        except Exception as e:

            raise ValueError(
                "Could not create a loader for the "
                "Custom segmentation file:\n"
                f"{e}"
            ) from e

        if spec is None:

            raise ValueError(
                "Could not load the Custom segmentation file:\n"
                f"{custom_path}"
            )

        if spec.loader is None:

            raise ValueError(
                "The Custom segmentation file has no "
                "usable Python loader:\n"
                f"{custom_path}"
            )

        try:

            module = (
                importlib.util.module_from_spec(
                    spec
                )
            )

            spec.loader.exec_module(
                module
            )

        except Exception as e:

            raise ValueError(
                "The Custom segmentation file could not "
                "be imported.\n\n"
                f"File: {custom_path}\n\n"
                f"Error: {e}"
            ) from e

        create_mask_function = getattr(
            module,
            "create_mask",
            None
        )

        if create_mask_function is None:

            raise ValueError(
                "The selected Custom segmentation file "
                "does not contain the required function:\n\n"
                "create_mask(image)"
            )

        if not callable(
                create_mask_function):

            raise ValueError(
                "The object named 'create_mask' in the "
                "Custom segmentation file is not callable."
            )

        self._custom_module = (
            module
        )

        self._custom_create_mask = (
            create_mask_function
        )

    # ========================================================
    # Validate Custom segmentation mask
    # ========================================================
    #
    # Required contract:
    #
    # Input:
    #     Original RGB uint8 image
    #
    # Output:
    #     NumPy array
    #     shape = (height, width)
    #     binary values = 0 or 1
    #
    # Boolean masks are accepted and converted to uint8.
    #
    # ========================================================

    @staticmethod
    def _validate_custom_mask(
            mask,
            image):

        if not isinstance(
                mask,
                np.ndarray):

            raise ValueError(
                "Custom create_mask(image) must return "
                "a NumPy ndarray."
            )

        expected_shape = (
            image.shape[:2]
        )

        if mask.ndim != 2:

            raise ValueError(
                "Custom segmentation mask must be a 2-D "
                "array with shape (height, width).\n\n"
                f"Expected shape: {expected_shape}\n"
                f"Returned shape: {mask.shape}"
            )

        if mask.shape != expected_shape:

            raise ValueError(
                "Custom segmentation mask has the wrong "
                "dimensions.\n\n"
                f"Expected shape: {expected_shape}\n"
                f"Returned shape: {mask.shape}"
            )

        # ----------------------------------------------------
        # Boolean mask
        # ----------------------------------------------------

        if mask.dtype == np.bool_:

            return mask.astype(
                np.uint8
            )

        # ----------------------------------------------------
        # Numeric mask
        # ----------------------------------------------------

        if not np.issubdtype(
                mask.dtype,
                np.number):

            raise ValueError(
                "Custom segmentation mask must contain "
                "numeric values or Boolean values."
            )

        # ----------------------------------------------------
        # Complex values are not valid segmentation values.
        # ----------------------------------------------------

        if np.issubdtype(
                mask.dtype,
                np.complexfloating):

            raise ValueError(
                "Custom segmentation mask must not contain "
                "complex values."
            )

        # ----------------------------------------------------
        # Check finite numeric values.
        # ----------------------------------------------------

        if not np.all(
                np.isfinite(mask)):

            raise ValueError(
                "Custom segmentation mask contains NaN "
                "or infinite values."
            )

        # ----------------------------------------------------
        # Binary requirement.
        #
        # Only 0 and 1 are accepted.
        # A 0/255 mask must explicitly be converted by the
        # Custom code to 0/1.
        # ----------------------------------------------------

        binary = (
            (mask == 0)
            |
            (mask == 1)
        )

        if not np.all(
                binary):

            raise ValueError(
                "Custom segmentation mask must contain "
                "only 0 and 1 values.\n\n"
                "Boolean masks are also accepted.\n"
                "A 0/255 mask is not accepted; convert it "
                "to 0/1 in create_mask()."
            )

        return mask.astype(
            np.uint8
        )

    # ========================================================
    # TransformRGB / Segmentation
    # ========================================================

    def create_mask(
            self,
            image):

        R = image[:, :, 0].astype(
            float
        )

        G = image[:, :, 1].astype(
            float
        )

        B = image[:, :, 2].astype(
            float
        )

        if self.segmentation_method == "G>R":

            mask = G > R

        elif self.segmentation_method == "G>R&G>B":

            mask = (
                (G > R)
                &
                (G > B)
            )

        elif self.segmentation_method == "2G-R-B>0":

            mask = (
                (2 * G - R - B) > 0
            )

        elif self.segmentation_method == "HSV":

            hsv = cv2.cvtColor(
                image,
                cv2.COLOR_RGB2HSV
            )

            H = hsv[:, :, 0]
            S = hsv[:, :, 1]
            V = hsv[:, :, 2]

            p = self.hsv_parameters

            mask = (

                    (H >= p["H_min"])
                    &
                    (H <= p["H_max"])
                    &
                    (S >= p["S_min"])
                    &
                    (S <= p["S_max"])
                    &
                    (V >= p["V_min"])
                    &
                    (V <= p["V_max"])

            )

        elif self.segmentation_method == "Custom":

            # ------------------------------------------------
            # Load the function if necessary.
            # ------------------------------------------------

            if self._custom_create_mask is None:

                self._load_custom_segmentation()

            # ------------------------------------------------
            # IMPORTANT SCIENTIFIC PROTECTION:
            #
            # Do NOT pass the original image array directly
            # to external user code.
            #
            # A full copy is provided so that even an
            # incorrectly written Custom algorithm cannot
            # modify the actual image used later for:
            #
            #   CC
            #   GR
            #   CCGR
            #   RGB statistics
            #
            # The scientific calculations therefore always
            # use the original image loaded by this engine.
            # ------------------------------------------------

            custom_input = np.array(
                image,
                copy=True,
                order="C"
            )

            try:

                custom_mask = (
                    self._custom_create_mask(
                        custom_input
                    )
                )

            except Exception as e:

                custom_name = Path(
                    self.custom_segmentation_path
                ).name

                raise ValueError(
                    "Custom segmentation failed.\n\n"
                    f"File: {custom_name}\n\n"
                    f"Error: {e}"
                ) from e

            return self._validate_custom_mask(
                custom_mask,
                image
            )

        else:

            raise ValueError(
                "Unknown segmentation method"
            )

        return mask.astype(
            np.uint8
        )

    # ========================================================
    # Statistics
    # ========================================================

    def matlab_channel_statistics(
            self,
            channel,
            mask):

        channel_double = channel.astype(
            np.float64
        )

        mean_overall = np.mean(
            channel_double
        )

        var_overall = np.var(
            channel_double.flatten(),
            ddof=1
        )

        foreground = (

            channel.astype(
                np.uint8
            )
            *
            mask.astype(
                np.uint8
            )

        ).astype(
            np.float64
        )

        background = (

            channel.astype(
                np.uint8
            )
            *
            (1 - mask).astype(
                np.uint8
            )

        ).astype(
            np.float64
        )

        veg_pixels = foreground[
            mask == 1
        ]

        if len(veg_pixels) > 0:

            mean_veg = np.mean(
                veg_pixels
            )

        else:

            mean_veg = np.nan

        veg_values = foreground[
            foreground > 0
        ]

        if len(veg_values) > 1:

            var_veg = np.var(
                veg_values,
                ddof=1
            )

        else:

            var_veg = np.nan

        soil_values = background[
            background > 1
        ]

        if len(soil_values) > 0:

            mean_soil = np.mean(
                soil_values
            )

        else:

            mean_soil = np.nan

        soil_var_values = channel_double[
            mask == 0
        ]

        if len(soil_var_values) > 1:

            var_soil = np.var(
                soil_var_values,
                ddof=1
            )

        else:

            var_soil = np.nan

        return {

            "Mean_Overall":
                mean_overall,

            "Mean_Veg":
                mean_veg,

            "Mean_Non-veg":
                mean_soil,

            "Var_Overall":
                var_overall,

            "Var_Veg":
                var_veg,

            "Var_Non-veg":
                var_soil

        }

    # ========================================================
    # CC GR CCGR
    # ========================================================

    def calculate_indices(
            self,
            image,
            mask):

        R = image[:, :, 0].astype(
            float
        )

        G = image[:, :, 1].astype(
            float
        )

        total_pixels = R.size

        veg_pixels = np.sum(
            mask
        )

        CC = (
            veg_pixels /
            total_pixels
        )

        if veg_pixels > 0:

            Rveg = (
                np.sum(
                    R * mask
                )
                /
                veg_pixels
            )

            Gveg = (
                np.sum(
                    G * mask
                )
                /
                veg_pixels
            )

            if Gveg != 0:

                GR = (
                    (Gveg - Rveg)
                    /
                    Gveg
                )

            else:

                GR = np.nan

        else:

            GR = np.nan

        CCGR = (
            CC * GR
        )

        return (
            CC,
            GR,
            CCGR
        )

    # ========================================================
    # Analyze image
    # ========================================================

    def analyze_image(
            self,
            path):

        image = self.load_image(
            path
        )

        mask = self.create_mask(
            image
        )

        CC, GR, CCGR = (
            self.calculate_indices(
                image,
                mask
            )
        )

        result = {

            "Image_name":
                Path(path).name,

            "CC":
                CC,

            "GR":
                GR,

            "CCGR":
                CCGR,

            "Num_Total":
                int(mask.size),

            "Num_Veg":
                int(np.sum(mask)),

            "Num_Non-veg":
                int(
                    mask.size
                    -
                    np.sum(mask)
                )

        }

        channels = {

            "Red": 0,
            "Green": 1,
            "Blue": 2

        }

        for name, index in channels.items():

            stats = (
                self.matlab_channel_statistics(
                    image[:, :, index],
                    mask
                )
            )

            for k, v in stats.items():

                result[
                    f"{k}_{name}"
                ] = v

        return (
            result,
            image,
            mask
        )

    # ========================================================
    # Save images
    # ========================================================

    def save_processed_images(
            self,
            image,
            mask,
            output_folder,
            filename):

        output_folder = Path(
            output_folder
        )

        folder = (
            output_folder /
            "Processed_images"
        )

        folder.mkdir(
            parents=True,
            exist_ok=True
        )

        veg = image.copy()
        soil = image.copy()

        purple = np.array(
            [150, 0, 150],
            dtype=np.uint8
        )

        veg[
            mask == 0
        ] = purple

        soil[
            mask == 1
        ] = 0

        cv2.imwrite(

            str(
                folder /
                f"Veg_{filename}"
            ),

            cv2.cvtColor(
                veg,
                cv2.COLOR_RGB2BGR
            )

        )

        cv2.imwrite(

            str(
                folder /
                f"Non-veg_{filename}"
            ),

            cv2.cvtColor(
                soil,
                cv2.COLOR_RGB2BGR
            )

        )

    # ========================================================
    # Folder processing
    # ========================================================

    def process_folder(
            self,
            input_folder,
            output_folder,
            callback=None,
            image_callback=None):

        input_folder = Path(
            input_folder
        )

        output_folder = Path(
            output_folder
        )

        files = []

        for ext in [

            "*.jpg",
            "*.jpeg",
            "*.png",
            "*.bmp",
            "*.tif",
            "*.tiff"

        ]:

            files.extend(
                input_folder.glob(ext)
            )

        files = sorted(
            files
        )

        if len(files) == 0:

            raise ValueError(
                "No images found"
            )

        graph_folder = (
            output_folder /
            "Graphs"
        )

        graph_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        results = []

        total = len(
            files
        )

        for i, file in enumerate(
                files,
                1):

            try:

                row, image, mask = (
                    self.analyze_image(
                        file
                    )
                )

                if image_callback:

                    image_callback(
                        image,
                        mask,
                        row
                    )

                results.append(
                    row
                )

                self.save_processed_images(
                    image,
                    mask,
                    output_folder,
                    file.name
                )

                # Create graph
                self.visualizer.create_from_result(
                    row,
                    graph_folder
                )

            except Exception as e:

                print(
                    f"ERROR processing "
                    f"{file.name}: {e}"
                )

            if callback:

                callback(
                    i,
                    total,
                    file.name
                )

        df = pd.DataFrame(
            results
        )

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        df.to_csv(
            output_folder /
            "Results.csv",
            index=False
        )

        # =================================================
        # Comparison Atlas
        # =================================================
        #
        # IMPORTANT:
        # This uses only the already calculated final
        # DataFrame. No scientific calculation is added
        # or altered here.
        #
        # The Atlas is stored directly in the same
        # Graphs folder as the individual graphs.
        #

        self.visualizer.create_comparison_atlas(
            df,
            graph_folder
        )

        return df