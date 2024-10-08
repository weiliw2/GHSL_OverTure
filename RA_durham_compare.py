import subprocess
import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
import matplotlib.pyplot as plt

# Step 1: Download Overture Maps Building Data for Durham
def download_overture_data():
    print("Downloading Overture Maps data for Durham...")
    bbox = "-78.9382,35.9940,-78.9005,36.0402"  # Define Durham bounding box
    output_file = "durham_buildings.geojson"
    
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
    # Open the GHSL raster using Rasterio
    ghsl_dataset = rasterio.open(ghsl_raster_path)
    print("GHSL raster data loaded.")
    return ghsl_dataset

# Step 3: Load the Overture Maps GeoJSON file
def load_overture_geojson(overture_geojson_path):
    print("Loading Overture Maps data into GeoPandas...")
    # Load the Overture Maps building footprints as a GeoDataFrame
    overture_gdf = gpd.read_file(overture_geojson_path)
    print("Overture Maps data loaded.")
    return overture_gdf

# Step 4: Reproject the Overture Maps data to match the GHSL raster CRS
def reproject_overture_to_raster(overture_gdf, raster_crs):
    print("Reprojecting Overture Maps data to match GHSL CRS...")
    overture_gdf = overture_gdf.to_crs(raster_crs)  # Reproject to raster CRS
    return overture_gdf

# Step 5: Perform Zonal Statistics - Calculate total GHSL built-up area within Overture building footprints
def calculate_zonal_statistics(overture_gdf, ghsl_raster_path):
    print("Performing zonal statistics...")
    stats = zonal_stats(
        overture_gdf,
        ghsl_raster_path,
        stats=['sum'],  # Sum of pixel values
        all_touched=True,  # Count any pixel that touches the building footprints
        nodata=-9999  # Assuming -9999 is used as the nodata value
    )
    
    # Add the sum of GHSL values to the GeoDataFrame
    overture_gdf['ghsl_sum'] = [stat['sum'] if stat['sum'] is not None else 0 for stat in stats]
    
    # Calculate the total GHSL built-up area within the Overture building footprints
    total_ghsl_area = overture_gdf['ghsl_sum'].sum()
    print(f"Total GHSL Built-Up Area within Overture Buildings: {total_ghsl_area} square meters")
    return total_ghsl_area

# Step 6: Calculate and Compare the Precision Ratio
def compare_area_with_precision(overture_gdf, total_ghsl_area):
    print("Calculating precision ratio...")
    overture_gdf['area'] = overture_gdf.geometry.area  # Calculate the area of each building
    total_overture_area = overture_gdf['area'].sum()  # Total area from Overture Maps
    
    # Calculate the precision ratio
    precision_ratio = (total_ghsl_area / total_overture_area) * 100
    print(f"Precision Ratio: {precision_ratio:.2f}%")
    
    return precision_ratio, total_overture_area

# Step 7: Visualize Results (Optional)
def plot_precision_map(overture_gdf):
    print("Visualizing precision ratio...")
    overture_gdf.plot(column='ghsl_sum', cmap='viridis', legend=True)
    plt.title("GHSL Built-Up Area within Overture Buildings")
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
    
    # Step 5: Perform Zonal Statistics to calculate the total GHSL built-up area within Overture buildings
    total_ghsl_area = calculate_zonal_statistics(overture_gdf, ghsl_raster_path)
    
    # Step 6: Compare areas and calculate precision ratio
    precision_ratio, total_overture_area = compare_area_with_precision(overture_gdf, total_ghsl_area)
    
    # Step 7: Optional - Visualize the precision map
    plot_precision_map(overture_gdf)

if __name__ == "__main__":
    main()
