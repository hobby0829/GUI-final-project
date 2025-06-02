import json
import math
import random

BEAT_MAP = "assets/beatmap"
SONG = 'Mozart - Alla Turca_Osu'

json_path = BEAT_MAP + '/' + SONG + '.json'
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

X_RANGE = (100, 700)
Y_RANGE = (100, 300)

placed_positions = [[400, 200]]
MIN_DISTANCE = 60     # 最小距離限制
MAX_DISTANCE = 300    # 最大距離限制（你可以視情況調整）

for idx, note in enumerate(data):
    for _ in range(100):  # 最多嘗試 100 次找合適位置
        x = random.randint(*X_RANGE)
        y = random.randint(*Y_RANGE)

        valid = True
        # 檢查與前最多四個 drum 的距離是否合適
        for px, py in placed_positions[-8:]:
            dist = math.hypot(x - px, y - py)
            if dist < MIN_DISTANCE or dist > MAX_DISTANCE:
                valid = False
                break

        if valid:
            note["pos"] = [x, y]
            placed_positions.append((x, y))
            break
    else:
        # 如果 100 次都找不到合適位置，就強制放最後一個嘗試的位置
        note["pos"] = [x, y]
        placed_positions.append((x, y))

# 輸出檔案
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("完成：每個 note 都新增了 pos 座標（與前4個 drum 距離限制）！")
