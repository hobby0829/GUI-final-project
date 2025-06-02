import json
import random

# 螢幕尺寸（你可以根據遊戲畫面自行調整）
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
MARGIN = 100  # 保留邊界，不要太靠近邊緣

BEATMAP = "assets/beatmap"
SONG_NAME = '春日影'
beatmap_path = BEATMAP + '/' + SONG_NAME + '.json'

# 載入原始譜面
with open(beatmap_path, "r", encoding="utf-8") as f:
    chart = json.load(f)

# 為每一個 note 加上隨機位置
for note in chart:
    x = random.randint(MARGIN, SCREEN_WIDTH - MARGIN)
    y = random.randint(MARGIN, SCREEN_HEIGHT - MARGIN)
    note["pos"] = [x, y]


with open(beatmap_path, "w", encoding="utf-8") as f:
    json.dump(chart, f, indent=2, ensure_ascii=False)

print("成功產生新譜面 chart_with_positions.json ✅")
