"""
Canopy CCGR for Python
Custom Segmentation Template
Compatible with Version 1.0.0

This file is a template for user-defined segmentation
methods.

Required function:

    create_mask(image)

The function must receive an original RGB uint8 image
with shape (height, width, 3) and return a binary
segmentation mask with shape (height, width):

    0 = non-vegetation
    1 = vegetation

Canopy CCGR performs all scientific calculations
(CC, GR, CCGR, and RGB statistics) independently
from this returned mask.

Author of Canopy CCGR:
Abbas Haghshenas

Easy Phenotyping Lab (EPL)
https://haqueshenas.github.io/EPL

Email:
haqueshenas@gmail.com

## Development note

The software concept, scientific design, methodological decisions, project direction, and overall development were
led by Abbas Haghshenas; the Python code was developed with coding assistance from OpenAI's GPT-5.6 Luna.

Copyright (c) 2026 Abbas Haghshenas
License: MIT
"""

import numpy as np


def create_mask(image):

    # --------------------------------------------------------
    # Original RGB channels
    # --------------------------------------------------------

    R = image[:, :, 0].astype(
        np.float32
    )

    G = image[:, :, 1].astype(
        np.float32
    )

    B = image[:, :, 2].astype(
        np.float32
    )

    # --------------------------------------------------------
    # Example segmentation
    #
    # Replace this with your own algorithm.
    # --------------------------------------------------------

    mask = (

        (G > R)
        &
        (G > B)

    )

    # --------------------------------------------------------
    # Required output:
    #
    # 0 = non-vegetation
    # 1 = vegetation
    # --------------------------------------------------------

    return mask.astype(
        np.uint8
    )