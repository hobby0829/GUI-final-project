import tkinter as tk
import json
import time
import pygame
import threading

WIDTH = 800
HEIGHT = 400
DRUM_SPEED = 5
JUDGE_LINE = 100
HIT_RANGE = 30

HIT_WAV = "assets/hit.wav"
BEAT_MAP = "assets/beatmap.json"
BGM = "assets/bgm.mp3"

class TaikoGame:
    def __init__(self, root):
        self.root = root
        self.root.title("太鼓達人加強版")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='white')
        self.canvas.pack()

        # 初始化 pygame 音效
        pygame.mixer.init()
        self.hit_sound_red = pygame.mixer.Sound(HIT_WAV)
        self.hit_sound_blue = pygame.mixer.Sound(HIT_WAV)
        self.bgm = BGM

        # 分數與 combo
        self.score = 0
        self.combo = 0

        # 顯示文字
        self.score_text = self.canvas.create_text(10, 10, anchor='nw', text='Score: 0', font=('Arial', 16))
        self.combo_text = self.canvas.create_text(10, 40, anchor='nw', text='Combo: 0', font=('Arial', 16))
        self.judge_text = self.canvas.create_text(WIDTH // 2, 50, text='', font=('Arial', 24), fill='red')

        # 判定線
        self.canvas.create_line(JUDGE_LINE, 0, JUDGE_LINE, HEIGHT, fill='gray', dash=(4, 2))

        # 鼓列表與開始時間
        self.drums = []
        self.start_time = None
        self.chart = []

        # 綁定鍵盤
        self.root.bind("<KeyPress-z>", self.hit_red)
        self.root.bind("<KeyPress-x>", self.hit_blue)

        # 載入譜面與開始遊戲
        self.load_score(BEAT_MAP)
        self.start_game()

    def load_score(self, file):
        with open(file, 'r') as f:
            self.chart = json.load(f)

    def start_game(self):
        self.start_time = int(time.time() * 1000)
        threading.Thread(target=self.play_bgm).start()
        self.schedule_drums()
        self.move_drums()

    def play_bgm(self):
        pygame.mixer.music.load(self.bgm)
        pygame.mixer.music.play()

    def schedule_drums(self):
        now = int(time.time() * 1000) - self.start_time
        for note in self.chart:
            if 0 <= note['time'] - now <= 50:  # 時間快到就生成
                self.spawn_drum(note['type'])
                self.chart.remove(note)
        self.root.after(50, self.schedule_drums)

    def spawn_drum(self, drum_type):
        color = 'red' if drum_type == 'red' else 'blue'
        y = HEIGHT // 2
        drum = {
            'id': self.canvas.create_oval(WIDTH, y - 30, WIDTH + 60, y + 30, fill=color),
            'type': drum_type,
            'x': WIDTH
        }
        self.drums.append(drum)

    def move_drums(self):
        for drum in self.drums:
            drum['x'] -= DRUM_SPEED
            self.canvas.coords(drum['id'], drum['x'], HEIGHT // 2 - 30, drum['x'] + 60, HEIGHT // 2 + 30)
        self.drums = [d for d in self.drums if d['x'] + 60 > 0]
        self.root.after(30, self.move_drums)

    def hit_red(self, event):
        self.play_hit_sound('red')
        self.check_hit('red')

    def hit_blue(self, event):
        self.play_hit_sound('blue')
        self.check_hit('blue')

    def check_hit(self, hit_type):
        for drum in self.drums:
            if drum['type'] == hit_type and abs(drum['x'] - JUDGE_LINE) < HIT_RANGE:
                
                self.canvas.itemconfig(self.judge_text, text='Perfect!')
                self.canvas.delete(drum['id'])
                self.drums.remove(drum)
                self.combo += 1
                self.score += 100
                self.update_score()
                return
        self.combo = 0
        self.canvas.itemconfig(self.judge_text, text='Miss')
        self.update_score()

    def play_hit_sound(self, drum_type):
        if drum_type == 'red':
            self.hit_sound_red.play()
        elif drum_type == 'blue':
            self.hit_sound_blue.play()

    def update_score(self):
        self.canvas.itemconfig(self.score_text, text=f'Score: {self.score}')
        self.canvas.itemconfig(self.combo_text, text=f'Combo: {self.combo}')

# 主程式
if __name__ == '__main__':
    root = tk.Tk()
    game = TaikoGame(root)
    root.mainloop()
