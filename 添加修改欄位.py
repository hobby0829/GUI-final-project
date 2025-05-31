import json
import random

path = 'assets\\beatmap\\Ave Mujica.json'
outpath = path
# 讀取原始 JSON 資料
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 對每筆資料加上固定欄位
for item in data:
    #item["time"] -= 600
    if item['time'] > 91000 :
        item["judge_point"] = [100, 200]  # 你可以換成你要加的欄位名稱與內容
        item["start_x"], item["end_x"] = (500, 300)

        item["start_y"], item["end_y"] = (0, 300)

        item["move_time"] = 3000
        item["type"] = random.choice(['red', 'blue'])

# 寫回 JSON 檔案（覆蓋）
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
