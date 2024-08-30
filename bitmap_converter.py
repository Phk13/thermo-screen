
from PIL import Image

# Function to convert PNG to BMP
def convert_png_to_bitmap(input_file, output_file):
    img = Image.open(input_file)
    img = img.convert('RGB')  # Convert to RGB mode
    # img = img.resize((128, 128), Image.Resampling.LANCZOS)  # Resize if needed
    img.save(output_file, format='BMP')

icon_id_list = ['01', '02', '03', '04', '09', '10', '11', '13', '50']

for id in icon_id_list:
    # Convert each icon
    convert_png_to_bitmap(f'icons/{id}d@2x.png', f'icons/{id}d@2x.bmp')
    convert_png_to_bitmap(f'icons/{id}n@2x.png', f'icons/{id}n@2x.bmp')

