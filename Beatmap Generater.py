import pygame
import time
import json

# 譜面資料（會是 list of dicts）
beatmap = []

# 音符對應（你可以擴充）
KEY_MAPPING = {
    pygame.K_z: 'red',
    pygame.K_x: 'blue'
}

# 初始化 pygame mixer 播放音樂
pygame.init()
pygame.mixer.init()

SONG_LIST = "assets/song"
SONG_NAME = '春日影'
# 音樂路徑
music_path = SONG_LIST + '/' + SONG_NAME + '.mp3'

# 載入音樂
pygame.mixer.music.load(music_path)

# 開啟一個空白視窗來接收鍵盤事件
screen = pygame.display.set_mode((400, 100))
pygame.display.set_caption("Beatmap Editor")

# 開始播放音樂
pygame.mixer.music.play()
start_time = time.time()

running = True
count = 0
print("開始編譜！按 Z（紅）、X（藍），ESC 結束...")

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            current_time = time.time() - start_time  # 秒數
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key in KEY_MAPPING:
                count += 1
                note = {
                    'time': round(current_time, 3) * 1000,  # 精確到毫秒
                    'type': KEY_MAPPING[event.key],
                    'id' : count
                }
                beatmap.append(note)
                print(f"{note['type'].upper()} at {note['time']}s, 'id' : {count}")

# 停止播放音樂
pygame.mixer.music.stop()

# 儲存譜面
with open(f'{SONG_NAME}.json', 'w', encoding='utf-8') as f:
    json.dump(beatmap, f, indent=2)

print(f"譜面已儲存為 {SONG_NAME}.json！")
pygame.quit()
