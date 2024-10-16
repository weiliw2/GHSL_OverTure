import geopandas as gpd
import rasterio
from shapely.geometry import box
import numpy as np
from rasterstats import zonal_stats
import matplotlib.pyplot as plt

# Step 1: Open GHSL Raster and Get Raster Properties
def get_ghsl_grid(ghsl_raster_path):
    print("Loading GHSL raster data and generating grid...")
    
    # Open the raster using rasterio
    with rasterio.open(ghsl_raster_path) as ghsl:
        # Get the bounds, resolution, and CRS
        bounds = ghsl.bounds
        res_x, res_y = ghsl.res  # This will give the resolution of the raster (in degrees)
        crs = ghsl.crs
        
        # Extract the bounding box
        minx, miny, maxx, maxy = bounds.left, bounds.bottom, bounds.right, bounds.top
        
        # Generate the grid cells using the raster resolution
        x_coords = np.arange(minx, maxx, res_x)
        y_coords = np.arange(miny, maxy, res_y)
        
        # Create grid cells as polygons
        grid_cells = [box(x, y, x + res_x, y + res_y) for x in x_coords for y in y_coords]
        
        # Create a GeoDataFrame from the grid
        grid = gpd.GeoDataFrame(grid_cells, columns=['geometry'], crs=crs)
        
    print(f"Generated grid with {len(grid)} cells matching GHSL resolution.")
    return grid

# Step 2: Calculate Zonal Statistics for GHSL Raster
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

# Step 3: Perform Spatial Comparison with Overture Maps
def compare_with_overture(grid, overture_gdf):
    print("Calculating Overture Maps building area in each grid cell...")
    
    # Calculate the area of each Overture building footprint
    overture_gdf['building_area'] = overture_gdf.geometry.area
    
    # Perform a spatial join between the Overture buildings and the grid
    overture_in_grid = gpd.sjoin(overture_gdf, grid, how='inner', predicate='intersects')
    
    # Group by grid cell and sum the building areas within each cell
    grid_overture_area = overture_in_grid.groupby('index_right')['building_area'].sum().reset_index()
    
    # Merge the building area data back into the grid GeoDataFrame
    grid = grid.merge(grid_overture_area, left_index=True, right_on='index_right', how='left')
    grid['area'] = grid['building_area'].fillna(0)  # Fill missing values with 0 for grids with no buildings
    
    return grid

# Step 4: Calculate Precision Ratio for Each Grid Cell
def calculate_precision_ratio(grid):
    print("Calculating precision ratio for each grid cell...")
    grid['precision_ratio'] = (grid['ghsl_sum'] / grid['area']) * 100
    grid['precision_ratio'] = grid['precision_ratio'].replace([np.inf, -np.inf], np.nan).fillna(0)
    return grid

# Step 5: Visualize the Precision Ratio
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
    overture_geojson_path = '/Users/weilynnw/Desktop/RA_work/durham_buildings.geojson'  # Replace with your Overture data
    
    # Step 1: Generate the grid based on GHSL raster properties
    grid = get_ghsl_grid(ghsl_raster_path)
    
    # Step 2: Calculate zonal statistics for GHSL raster data
    grid = calculate_zonal_statistics(grid, ghsl_raster_path)
    
    # Step 3: Load the Overture Maps data
    overture_gdf = gpd.read_file(overture_geojson_path)
    
    # Step 4: Perform spatial comparison with Overture Maps
    grid = compare_with_overture(grid, overture_gdf)
    
    # Step 5: Calculate precision ratio for each grid cell
    grid = calculate_precision_ratio(grid)
    
    # Step 6: Visualize the precision ratio grid-by-grid
    visualize_grid(grid)

if __name__ == "__main__":
    main()
