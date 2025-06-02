import os
from moviepy.editor import VideoFileClip

path = r"C:\Users\dada2\Videos\Captures\tk 2025-06-01 22-39-50.mp4"
filename_without_ext = os.path.splitext(os.path.basename(path))[0]
clip = VideoFileClip(path).subclip(2, 8)  # 前5秒
clip = clip.resize(height=300)  # 調整大小以減少GIF大小
clip.write_gif(f"PPT/{filename_without_ext}.gif", fps=10)