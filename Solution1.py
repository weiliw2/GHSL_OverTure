import subprocess
import geopandas as gpd
from rasterstats import zonal_stats
import rasterio
import numpy as np
from shapely.geometry import box
import matplotlib.pyplot as plt
import os
# Step 1: Download Overture Maps Building Data for Durham
def download_overture_data():
    output_file = "durham_buildings.geojson"
    
    # Check if the file already exists
    if os.path.exists(output_file):
        print(f"Overture Maps data already exists at {output_file}. Skipping download.")
        return output_file
    
    # If the file doesn't exist, proceed with download
    print("Downloading Overture Maps data for Durham...")
    bbox = "-78.9382,35.9940,-78.9005,36.0402"  # Define Durham bounding box
    
    # Use the Overture Maps command-line tool to download building footprints for Durham
    subprocess.run([
        "overturemaps", "download", 
        f"--bbox={bbox}", 
        "-f", "geojson", 
        "-t", "building", 
        "-o", output_file
    ])
    
    print(f"Overture Maps data saved to {output_file}")
    return output_file

# Step 2: Load the GHSL Raster Data for Durham
def load_ghsl_raster(ghsl_raster_path):
    print("Loading GHSL raster data...")
    ghsl_dataset = rasterio.open(ghsl_raster_path)
    print("GHSL raster data loaded.")
    return ghsl_dataset

# Step 3: Load the Overture Maps GeoJSON file
def load_overture_geojson(overture_geojson_path):
    print("Loading Overture Maps data into GeoPandas...")
    overture_gdf = gpd.read_file(overture_geojson_path)
    print("Overture Maps data loaded.")
    return overture_gdf

# Step 4: Reproject the Overture Maps data to match the GHSL raster CRS
def reproject_overture_to_raster(overture_gdf, raster_crs):
    print("Reprojecting Overture Maps data to match GHSL CRS...")
    overture_gdf = overture_gdf.to_crs(raster_crs)
    return overture_gdf

# Step 5: Create 30 Arcsecond Grid for GHSL Comparison
def create_grid(overture_gdf):
    print("Creating 30 arcsecond grid for GHSL comparison...")
    
    # Define the bounding box for the grid based on the extent of the Overture data
    minx, miny, maxx, maxy = overture_gdf.total_bounds
    
    # Define grid size (30 arcseconds in degrees)
    grid_size = 30 / 3600  # 30 arcseconds in degrees
    
    # Generate grid cells
    x_coords = np.arange(minx, maxx, grid_size)
    y_coords = np.arange(miny, maxy, grid_size)
    
    grid_cells = [box(x, y, x + grid_size, y + grid_size) for x in x_coords for y in y_coords]
    
    # Convert to GeoDataFrame
    grid = gpd.GeoDataFrame(grid_cells, columns=['geometry'], crs=overture_gdf.crs)
    
    print(f"Grid created with {len(grid)} cells.")
    print(minx, miny, maxx, maxy)

    return grid

# Step 6: Perform Zonal Statistics for Each Grid Cell
def calculate_zonal_statistics(grid, ghsl_raster_path):
    print("Performing zonal statistics for each grid cell...")
    ghsl_stats = zonal_stats(
        grid,
        ghsl_raster_path,
        stats=['sum'],
        all_touched=True,
        nodata=-9999
    )
    
    # Add the GHSL built-up area to the grid GeoDataFrame
    grid['ghsl_sum'] = [stat['sum'] if stat['sum'] is not None else 0 for stat in ghsl_stats]
    
    return grid

# Step 7: Calculate the Overlap with Overture Maps
def calculate_overture_area_in_grid(overture_gdf, grid):
    print("Calculating Overture Maps building area in each grid cell...")
    
    # First, calculate the area of each Overture building footprint
    overture_gdf['building_area'] = overture_gdf.geometry.area
    
    # Perform a spatial join between the Overture buildings and the grid
    overture_in_grid = gpd.sjoin(overture_gdf, grid, how='inner', predicate='intersects')
    
    # Now, group by grid cell and sum the areas of the buildings within each grid cell
    grid_overture_area = overture_in_grid.groupby('index_right')['building_area'].sum().reset_index()
    
    # Merge the building area data back into the grid GeoDataFrame
    grid = grid.merge(grid_overture_area, left_index=True, right_on='index_right', how='left')
    grid['area'] = grid['building_area'].fillna(0)  # Fill missing values with 0 for grids with no buildings
    
    return grid


# Step 8: Calculate Precision Ratio for Each Grid Cell
def calculate_precision_ratio(grid):
    print("Calculating precision ratio for each grid cell...")
    grid['precision_ratio'] = (grid['ghsl_sum'] / grid['area']) * 100
    grid['precision_ratio'] = grid['precision_ratio'].replace([np.inf, -np.inf], np.nan).fillna(0)
    return grid

# Step 9: Visualize Precision Ratio Grid-by-Grid
def visualize_grid(grid):
    print("Visualizing precision ratio...")
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    grid.plot(column='precision_ratio', ax=ax, legend=True, cmap='viridis', edgecolor='black')
    plt.title('Precision Ratio per Grid Cell')
    plt.show()

# Main function to run the analysis
def main():
    # Paths to the data
    ghsl_raster_path = '/Users/weilynnw/Desktop/RA_work/GHS_BUILT_S_E2030_GLOBE_R2023A_4326_30ss_V1_0_R6_C11/GHS_BUILT_S_E2030_GLOBE_R2023A_4326_30ss_V1_0_R6_C11.tif'  # Replace with the path to your GHSL raster data
    
    # Step 1: Download the Overture Maps data for Durham
    overture_geojson_path = download_overture_data()
    
    # Step 2: Load the GHSL raster data
    ghsl_dataset = load_ghsl_raster(ghsl_raster_path)
    
    # Step 3: Load the Overture Maps data
    overture_gdf = load_overture_geojson(overture_geojson_path)
    
    # Step 4: Reproject Overture data to match GHSL CRS
    overture_gdf = reproject_overture_to_raster(overture_gdf, ghsl_dataset.crs)
    
    # Step 5: Create the 30 arcsecond grid
    grid = create_grid(overture_gdf)
    
    # Step 6: Perform zonal statistics for each grid cell
    grid = calculate_zonal_statistics(grid, ghsl_raster_path)
    
    # Step 7: Calculate the overlap with Overture Maps and their area in each grid cell
    grid = calculate_overture_area_in_grid(overture_gdf, grid)
    
    # Step 8: Calculate precision ratio for each grid cell
    grid = calculate_precision_ratio(grid)
    
    # Step 9: Visualize precision ratio grid-by-grid
    visualize_grid(grid)

if __name__ == "__main__":
    main()
