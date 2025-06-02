import json
import math


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 400

def generate_lines_from_drums(drum_file, line_file):
    with open(drum_file, 'r', encoding='utf-8') as f:
        drums = json.load(f)

    lines = []
    line_id = 1

    for drum in drums:
        start_x = drum['start_x']
        start_y = drum['start_y']
        end_x = drum['end_x']
        end_y = drum['end_y']
        move_time = drum['move_time']
        spawn_time = drum['time']

        # 計算移動方向
        dx = end_x - start_x
        dy = end_y - start_y

        # 垂直方向向量（法向量）
        length = math.hypot(dx, dy)
        if length == 0:
            continue  # 忽略無移動鼓
        ndx = -dy / length
        ndy = dx / length

        # 判定線的長度（可調）
        line_length = 1200


        lx1 = end_x + ndx * line_length / 2
        ly1 = end_y + ndy * line_length / 2
        lx2 = end_x - ndx * line_length / 2
        ly2 = end_y - ndy * line_length / 2


        line = {
            "id": f"auto_{line_id}",
            "time": spawn_time,
            "end_time": spawn_time + move_time,
            "x1": lx1,
            "y1": ly1,
            "x2": lx2,
            "y2": ly2,
            "movement": []
        }
        lines.append(line)
        line_id += 1

    with open(line_file, 'w', encoding='utf-8') as f:
        json.dump(lines, f, indent=4)
    print(f"[OK] 生成 {len(lines)} 條判定線到 {line_file}")

PATH = 'assets\\beatmap\\春日影'
DRUM_FILE = PATH + '.json'
LINE_FILE = PATH + '_line.json'
# 使用方式
generate_lines_from_drums(DRUM_FILE, LINE_FILE)
