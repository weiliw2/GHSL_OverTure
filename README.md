# GHSL_OverTure
 Overview
This Python script is designed to compare Global Human Settlement Layer (GHSL) raster data with Overture Maps building footprints for a specific region. The comparison is done by generating a grid that matches the GHSL raster’s resolution and performing zonal statistics to calculate the built-up area in each grid cell. The script then compares this to the building footprint data from Overture Maps.

Key Features
GHSL Raster Grid Generation: Generates a grid based on the GHSL raster data, ensuring the grid matches the raster’s resolution and extent.
Zonal Statistics Calculation: Performs zonal statistics to calculate the built-up area from the GHSL raster within each grid cell.
Overture Maps Comparison: Compares the calculated GHSL built-up area with Overture Maps building footprints in the same region.
Precision Ratio Calculation: Computes the ratio between GHSL and Overture Maps data for each grid cell, providing a quantitative measure of precision.
Visualization: Generates a heatmap of the precision ratio for visual inspection.
Data Used
The script works with two datasets:

GHSL Raster Data: A .tif file containing built-up area data at a specified resolution (e.g., 30 arcseconds).
Overture Maps Data: A .geojson file containing building footprint data for the region of interest (downloadable via the Overture Maps Python command-line tool or via S3).
