import json

path = 'assets\\beatmap\\春日影.json'
outpath = path
# 讀取原始 JSON 資料
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 對每筆資料加上固定欄位
for item in data:
    item["judge_point"] = [100, 200]  # 你可以換成你要加的欄位名稱與內容
    item["start_y"] = 100
    item["end_x"] = 100
    item["end_y"] = 300
    #item["move_time"] = 3000

# 寫回 JSON 檔案（覆蓋）
with open(outpath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
