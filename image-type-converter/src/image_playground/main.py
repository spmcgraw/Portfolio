from PIL import Image
from pathlib import Path

script_dir = Path(__file__).resolve().parent

image_path = script_dir/".."/".."/"images"/"pikachu.jpg"

img = Image.open(image_path)

print(img)