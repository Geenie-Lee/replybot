from PIL import Image
import os

source_path = r'c:\workspace\db\replybot\static\img\wavve.png'
dest_path = r'c:\workspace\db\replybot\static\favicon.ico'

if os.path.exists(source_path):
    img = Image.open(source_path)
    img.save(dest_path, format='ICO', sizes=[(32, 32)])
    print(f"Favicon created at {dest_path}")
else:
    print(f"Source file not found: {source_path}")
