import sys
from pathlib import Path

from PIL import Image

# Grab first and second arguments
image_folder = sys.argv[1]
new_folder = sys.argv[2]

# Render file paths and check is new/ exists, if not create
script_dir = Path(__file__).resolve().parents[2]
image_path = script_dir/image_folder
new_path = script_dir/new_folder

new_path.mkdir(parents=True, exist_ok=True)


# loop through images/
# convert images to png
# save to the new folder
img = Image.open(image_path)

print(img)