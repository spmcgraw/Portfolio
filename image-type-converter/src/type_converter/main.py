import sys
from pathlib import Path

from PIL import Image

# Grab first and second arguments
image_folder = sys.argv[1]
new_folder = sys.argv[2]

# Render file paths and check is new/ exists, if not create
project_root = Path(__file__).resolve().parents[2]

image_path = project_root / image_folder
new_path = project_root / new_folder

new_path.mkdir(parents=True, exist_ok=True)

# loop through images/
for filename in image_path.iterdir():
    if filename.is_file():
        clean_name = filename.stem
        new_img = Image.open(filename)
        # convert images to png & save to the new folder
        output_file = new_path / f'{clean_name}.png'
        new_img.save(output_file,'png')
    
print('all done')