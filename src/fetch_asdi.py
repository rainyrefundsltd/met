# Script to fetch ASDI data

import os

data_folder = "data"
file_path = os.path.join(data_folder, "example.csv")

# Writing data
with open(file_path, "w") as f:
    f.write("Sample data")

print(f"Data saved to {file_path}")