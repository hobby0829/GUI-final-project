import json
import math
import random

BEAT_MAP = "assets/beatmap"
SONG = "春日影"

json_path = BEAT_MAP + '/' + SONG + '.json'
# 讀取原始 JSON 譜面
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 設定 x, y 的隨機範圍（依照你遊戲畫面範圍修改）
X_RANGE = (100, 700)
Y_RANGE = (100, 300)

placed_positions = []
MIN_DISTANCE = 40
# 為每個 note 新增 pos 欄位
for note in data:
    x = random.randint(*X_RANGE)
    y = random.randint(*Y_RANGE)
    note["pos"] = [x, y]
    for _ in range(100):  # 最多嘗試 100 次找合適位置
        x = random.randint(*X_RANGE)
        y = random.randint(*Y_RANGE)

        too_close = False
        for px, py in placed_positions:
            if math.hypot(x - px, y - py) < MIN_DISTANCE:
                too_close = True
                break

        if not too_close:
            note['pos'] = (x, y)
            placed_positions.append((x, y))
            break
        else:
            # 如果 100 次都找不到合適位置，就允許最後一個強制放置
            note['pos'] = (x, y)
            placed_positions.append((x, y))


# 寫入新的 JSON 檔案（可以覆蓋原始檔，也可以另存）
with open("your_beatmap_with_pos.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("完成：每個 note 都新增了 pos 座標！")
