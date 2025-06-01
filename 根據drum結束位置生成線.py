import json
import math


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 400

def clip_line_to_window(end_x, end_y, ndx, ndy, width, height):
    candidates = []

    # 左邊界 x=0
    if ndx != 0:
        t = (0 - end_x) / ndx
        y = end_y + t * ndy
        if 0 <= y <= height:
            candidates.append((t, 0, y))

    # 右邊界 x=width
    if ndx != 0:
        t = (width - end_x) / ndx
        y = end_y + t * ndy
        if 0 <= y <= height:
            candidates.append((t, width, y))

    # 上邊界 y=0
    if ndy != 0:
        t = (0 - end_y) / ndy
        x = end_x + t * ndx
        if 0 <= x <= width:
            candidates.append((t, x, 0))

    # 下邊界 y=height
    if ndy != 0:
        t = (height - end_y) / ndy
        x = end_x + t * ndx
        if 0 <= x <= width:
            candidates.append((t, x, height))

    if len(candidates) < 2:
        # 沒找到兩個有效點，退回預設短線
        return None

    # 依 t 值排序
    candidates.sort(key=lambda c: c[0])

    # 取最小和最大 t 的點作為線段端點
    _, x1, y1 = candidates[0]
    _, x2, y2 = candidates[-1]

    return x1, y1, x2, y2


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
        line_length = 100

        # 呼叫 clip_line_to_window 取得延伸至邊界的兩點
        res = clip_line_to_window(end_x, end_y, ndx, ndy, WINDOW_WIDTH, WINDOW_HEIGHT)
        if res is None:
            # fallback 回短線，或跳過
            lx1 = end_x + ndx * line_length / 2
            ly1 = end_y + ndy * line_length / 2
            lx2 = end_x - ndx * line_length / 2
            ly2 = end_y - ndy * line_length / 2
        else:
            lx1, ly1, lx2, ly2 = res

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
