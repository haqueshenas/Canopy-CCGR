# Canopy CCGR Sample Data

This directory contains five raw, unprocessed field images provided as sample input data for Canopy CCGR for Python.

The images were selected from the larger dataset:

Diverse Canopy of Wheat Cultivar Mixtures: A Comprehensive Image Dataset for Phenotyping, Phenology, and Water Stress Studies

Zenodo:
https://doi.org/10.5281/zenodo.10694706

The complete dataset contains 1676 ground-based nadir images collected across 19 dates during two growing seasons from wheat experimental plots. The five images provided here are a small subset of that dataset and are intended specifically for testing Canopy CCGR and demonstrating its image-analysis workflow.

## Image naming

Image filenames contain information about the crop and sampling date.

For example:

155 DAS cv Chamran

means:

155 days after sowing (DAS)
Wheat cultivar: Chamran

## How to use these images

1. Launch Canopy CCGR for Python.
2. Select this `Sample_Data` folder as the input image folder.
3. Select an output folder of your choice.
4. Use the default `G>R` segmentation method for a basic reproduction of the standard Canopy CCGR workflow.
5. Run the analysis.
6. Inspect the generated `Results.csv`, processed images, and graphs.

The images in this directory are raw input images. They have not been pre-segmented or processed for use as software outputs.

## Reproducibility

These images are provided so that users can test the software with real field imagery and reproduce the general analysis workflow described in the Canopy CCGR documentation.

The exact numerical results depend on the image files and analysis settings used. For scientifically comparable analyses, keep the same input images and use the same segmentation method and relevant parameters.

## Source dataset

Haghshenas, A. (2024). Diverse Canopy of Wheat Cultivar Mixtures: A Comprehensive Image Dataset for Phenotyping, Phenology, and Water Stress Studies. Zenodo.

https://doi.org/10.5281/zenodo.10694706

## License

The sample images in this directory are distributed under the MIT License, consistent with the license of the parent dataset.

See `LICENSE.txt` in this directory for the applicable license terms.
