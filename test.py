import os

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
    
    if os.path.exists(output_file):
        print(f"Overture Maps data saved to {output_file}")
    else:
        print(f"Failed to download Overture Maps data to {output_file}")
    
    return output_file
