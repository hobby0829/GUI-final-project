import os
from PIL import Image, ImageTk

# 開啟圖片並縮放
def resize(img, x=800, y=400):
    
    resized_image = img.resize((x, y))  # 調整成 100x100 大小

    return resized_image

def convert(img, path, convert_format='PNG'):
    
    # 開啟圖片
    folder_path = os.path.dirname(path)
    filename_without_ext = os.path.splitext(os.path.basename(path))[0]
    save_path = os.path.join(folder_path, f"{filename_without_ext}.png")
    # 另存為 PNG
    img.save(save_path)

if __name__ == "__main__":
    path = 'assets\icon\封面.JPG'
    x = 800
    y = 400
    img = Image.open(path)
    resized_image = resize(img, x, y)
    resized_image = convert(resized_image, path, convert_format='PNG')
    #resized_image.save(path)

