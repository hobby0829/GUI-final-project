from PIL import Image, ImageTk

# 開啟圖片並縮放
def resize(path, x, y):
    image = Image.open(path)
    resized_image = image.resize((x, y))  # 調整成 100x100 大小

    return resized_image

if __name__ == "__main__":
    path = 'assets/drum.png'
    resized_image = resize(path, 64, 64)
    resized_image.save("assets/drum_resized.png")