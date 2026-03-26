import os
from PIL import Image
 
base_dir = os.path.dirname(os.path.abspath(__file__))
img_dir = os.path.join(base_dir, 'static', 'images')

print(f"🔍 Looking for images in: {img_dir}")

if not os.path.exists(img_dir):
    print(f"❌ Error: The directory {img_dir} does not exist!")
else:
    files = os.listdir(img_dir)
    print(f"Found {len(files)} total files in directory.")
    
    count = 0
    for filename in files: 
        if filename.lower().endswith((".jpg", ".png", ".jpeg", ".webp")):
            filepath = os.path.join(img_dir, filename)
            
            with Image.open(filepath) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                 
                new_name = os.path.splitext(filename)[0] + ".webp"
                new_path = os.path.join(img_dir, new_name)
                 
                img.save(new_path, "WEBP", quality=50) 
                print(f"✅ Compressed: {filename} -> {new_name} (Size: {os.path.getsize(new_path)//1024}KB)")
                count += 1
                 
                if not filename.endswith(".webp"):
                    os.remove(filepath)

    print(f"--- Finished! Compressed {count} images. ---")