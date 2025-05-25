import os
import tkinter as tk
from tkinter import messagebox
import json
import time
import pygame
import threading

WIDTH = 800
HEIGHT = 400
DRUM_SPEED = 5
JUDGE_LINE = 100
HIT_RANGE = 30

HIT_WAV = "assets/sound/hit.wav"
BEAT_MAP = "assets/beatmap"
SONG_LIST = "assets/song"
BGM_MENU = "assets/song/test.mp3"

btn_style = {
    "font": ("Arial", 14, "bold"),
    "bg": "#f0a500",
    "fg": "white",
    "activebackground": "#d48806",
    "activeforeground": "white",
    "bd": 0,
    "relief": "flat",
    "width": 12,
    "height": 2,
    "cursor": "hand2"
}

class GameSettings:
    def __init__(self):
        self.volume = 100
        self.red_button = "<KeyPress-z>"
        self.blue_button = "<KeyPress-x>"

class MainMenu:
    def __init__(self, root, settings):
        self.root = root
        self.settings = settings
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='lightblue')
        self.canvas.pack()

        pygame.mixer.init()
        self.bgm = BGM_MENU
        self.play_bgm()

        self.title = self.canvas.create_text(WIDTH//2, HEIGHT//2 - 100, text="太鼓達人 加強版", font=("Arial", 32, "bold"))

        self.start_btn = tk.Button(root, text="開始遊戲", font=("Arial", 16), command=self.start_game)
        self.quit_btn = tk.Button(root, text="選單", font=("Arial", 16), command=self.show_options_menu)

        self.start_btn.place(x=WIDTH//2 - 60, y=HEIGHT//2)
        self.quit_btn.place(x=WIDTH//2 - 60, y=HEIGHT//2 + 50)

    def start_game(self):
        self.start_btn.place_forget()
        self.quit_btn.place_forget()
        self.canvas.destroy()
        SongSelect(self.root, self.start_taiko_game, self.settings)

    def start_taiko_game(self, song_path, beatmap_path, settings):
        TaikoGame(self.root, song_path, beatmap_path, settings)

    def play_bgm(self):
        pygame.mixer.music.load(self.bgm)
        pygame.mixer.music.set_volume(self.settings.volume / 100)
        pygame.mixer.music.play()

    def show_options_menu(self):
        options_window = tk.Toplevel(self.root)
        options_window.title("選項")
        options_window.geometry("300x300")
        options_window.resizable(False, False)

        def open_volume_control():
            volume_window = tk.Toplevel(self.root)
            volume_window.title("音量控制")
            volume_window.geometry("300x150")
            volume_window.resizable(False, False)

            tk.Label(volume_window, text="背景音樂音量", font=("Arial", 14)).pack(pady=10)

            current_volume = pygame.mixer.music.get_volume()
            volume_var = tk.DoubleVar(value=current_volume * 100)

            def set_volume(val):
                volume = float(val) / 100
                pygame.mixer.music.set_volume(volume)
                self.settings.volume = float(val)  # ✅ 更新 settings

            tk.Scale(volume_window, from_=0, to=100, orient='horizontal',
                    variable=volume_var, command=set_volume).pack(pady=5)

            tk.Button(volume_window, text="關閉", command=volume_window.destroy).pack(pady=10)

        def open_keybind_control():
            keybind_window = tk.Toplevel(self.root)
            keybind_window.title("按鍵設定")
            keybind_window.geometry("300x200")
            keybind_window.resizable(False, False)
            tk.Label(keybind_window, text="點擊欄位後按下要設定的按鍵", font=("Arial", 10), fg="gray").pack(pady=2)
            
            tk.Label(keybind_window, text="紅色:", font=("Arial", 12)).pack(pady=5)
            red_var = tk.StringVar()
            blue_var = tk.StringVar()

            red_entry = tk.Entry(keybind_window, font=("Arial", 12), textvariable=red_var, state="readonly")
            red_entry.pack()
            
            tk.Label(keybind_window, text="藍色:", font=("Arial", 12)).pack(pady=5)
            blue_entry = tk.Entry(keybind_window, font=("Arial", 12), textvariable=blue_var, state="readonly")
            blue_entry.pack()

            special_keys = {
                "space", "Left", "Right", "Up", "Down", "Return",
                "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"
            }

            def handle_key(event, var):
                key = event.keysym
                if len(key) == 1:
                    var.set(key.lower())
                elif key in special_keys:
                    var.set(key)
                else:
                    var.set("")  # 不合法就清空

            red_entry.bind("<KeyPress>", lambda e: handle_key(e, red_var))
            blue_entry.bind("<KeyPress>", lambda e: handle_key(e, blue_var))

            # 初始化
            red_key = self.settings.red_button.replace("<KeyPress-", "").replace(">", "")
            blue_key = self.settings.blue_button.replace("<KeyPress-", "").replace(">", "")
            red_var.set(red_key)
            blue_var.set(blue_key)

            def save_keybinds():
                red_key = red_var.get().strip()
                blue_key = blue_var.get().strip()
                if red_key and blue_key:
                    self.settings.red_button = f"<KeyPress-{red_key}>"
                    self.settings.blue_button = f"<KeyPress-{blue_key}>"
                    messagebox.showinfo("成功", "按鍵綁定已更新")
                    keybind_window.destroy()
                else:
                    messagebox.showwarning("錯誤", "請按下有效按鍵")
            
            tk.Button(keybind_window, text="儲存", command=save_keybinds).pack(pady=10)

        # 主選單的按鈕
        tk.Button(options_window, text="音量大小", font=("Arial", 12), command=open_volume_control).pack(pady=10)
        tk.Button(options_window, text="更改按鍵", font=("Arial", 12), command=open_keybind_control).pack(pady=10)
        tk.Button(options_window, text="關閉選單", font=("Arial", 12), command=options_window.destroy).pack(pady=20)
    
class SongSelect:
    def __init__(self, root, on_song_selected, settings):
        self.root = root
        self.on_song_selected = on_song_selected
        self.settings = settings

        self.canvas = tk.Canvas(root, width=800, height=400, bg='#1e1e1e')
        self.canvas.pack()

        self.title = self.canvas.create_text(400, 40, text="選擇歌曲", fill="white", font=("Arial", 28, "bold"))
        self.song_buttons = []

        # 左上角的返回按鈕
        self.back_btn = tk.Button(root, text="回主菜單", font=("Arial", 12), command=self.return_to_main_menu)
        self.back_btn.place(x=10, y=10)

        self.load_song_list(SONG_LIST)  # 讀取歌曲資料夾名稱

    def return_to_main_menu(self):
        self.canvas.destroy()
        self.back_btn.destroy()
        for btn in self.song_buttons:
            btn.destroy()
        MainMenu(self.root, self.settings)

    def load_song_list(self, folder):
        songs = [
            os.path.splitext(f)[0]  # 取得去掉副檔名的檔案名稱
            for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))
        ]
        
        for i, song in enumerate(songs):
            btn = tk.Button(
                self.root,
                text=song,
                command=lambda name=song: self.confirm_song(name, self.settings),
                font=("Arial", 14, "bold"),
                bg="#4CAF50",
                fg="white",
                activebackground="#388E3C",
                relief="flat",
                bd=0,
                width=30,
                cursor="hand2"
            )
            btn.place(x=800//2 - 150, y=100 + i * 50)
            self.song_buttons.append(btn)

    def confirm_song(self, song, settings):
        answer = messagebox.askyesno("確認", f"是否要遊玩「{song}」？")
        if answer:
            beatmap_path = os.path.join("assets", "beatmap", f"{song}.json")
            song_path = os.path.join("assets", "song", f"{song}.mp3")
            self.cleanup()
            self.on_song_selected(song_path, beatmap_path, self.settings)

    def cleanup(self):
        self.canvas.destroy()
        for btn in self.song_buttons:
            btn.destroy()

class TaikoGame:
    def __init__(self, root, song_path, beatmap_path, settings):
        self.root = root
        self.settings = settings
        self.root.title("太鼓達人加強版")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='white')
        self.canvas.pack()

        # 初始化 pygame 音效
        pygame.mixer.init()
        self.hit_sound_red = pygame.mixer.Sound(HIT_WAV)
        self.hit_sound_blue = pygame.mixer.Sound(HIT_WAV)
        self.bgm = song_path

        # 分數與 combo
        self.score = 0
        self.combo = 0
        
        # 暫停按鈕
        self.back_btn = tk.Button(root, text="暫停", font=("Arial", 12), command=self.toggle_pause)
        self.back_btn.place(x=750, y=10)

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
        self.root.bind(self.settings.red_button, self.hit_red)
        self.root.bind(self.settings.blue_button, self.hit_blue)

        self.paused = False
        self.overlay = None

        self.volume_label = tk.Label(root, text="音量", font=("Arial", 12), bg='#222222', fg='white')
        self.volume_label.place_forget()

        self.volume_slider = tk.Scale(
            root,
            from_=0, to=100,
            orient='horizontal',
            command=self.set_volume,
            length=200,
            font=("Arial", 12, "bold"),
            bg="#222222",
            fg="white",
            troughcolor="#555555",
            bd=0,
            sliderrelief='flat',
            highlightthickness=0
        )
        self.volume_slider.set(settings.volume)
        self.volume_slider.place_forget()

        self.root.bind("<KeyPress-p>", self.toggle_pause_key)

        self.btn_menu = tk.Button(root, text="返回主選單", command=self.back_to_menu, **btn_style)
        self.btn_restart = tk.Button(root, text="重新開始(R)", command=self.restart_game, **btn_style)
        self.btn_quit = tk.Button(root, text="繼續(P)", command=self.toggle_pause, **btn_style)


        self.set_volume(settings.volume)

        # 載入譜面與開始遊戲
        self.load_score(beatmap_path)
        self.start_game()

    def back_to_menu(self):
        self.hide_pause_overlay()
        pygame.mixer.music.stop()
        self.canvas.destroy()
        MainMenu(self.root, self.settings)

    def restart_game(self):
        self.hide_pause_overlay()
        self.paused = False
        pygame.mixer.music.stop()
        self.score = 0
        self.combo = 0
        self.update_score()
        for drum in self.drums:
            self.canvas.delete(drum['id'])
        self.drums.clear()
        self.load_score(BEAT_MAP)
        self.start_game()

    def toggle_pause(self):
        self.toggle_pause_key(event=None)

    def toggle_pause_key(self, event):
        if not self.paused:
            self.paused = True
            pygame.mixer.music.pause()
            self.show_pause_overlay()
        else:
            self.paused = False
            pygame.mixer.music.unpause()
            self.hide_pause_overlay()

    def set_volume(self, val):
        volume = int(val) / 100
        self.settings.volume = int(val)
        pygame.mixer.music.set_volume(volume)
        self.hit_sound_red.set_volume(volume)
        self.hit_sound_blue.set_volume(volume)

    def show_pause_overlay(self):
        # 半透明黑色遮罩（使用 rectangle 模擬）
        self.overlay = self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill='black', stipple='gray50')
        self.pause_text = self.canvas.create_text(WIDTH//2, HEIGHT//2 - 60, text="暫停中", font=("Arial", 28), fill="white")

        # 顯示音量滑桿
        self.volume_label.place(x=WIDTH//2 - 100, y=HEIGHT//2 - 50)
        self.volume_slider.place(x=WIDTH//2 - 100, y=HEIGHT//2 - 20)

        self.btn_menu.place(x=WIDTH//2 - 60, y=HEIGHT//2 + 40)
        self.btn_restart.place(x=WIDTH//2 - 60, y=HEIGHT//2 + 80)
        self.btn_quit.place(x=WIDTH//2 - 60, y=HEIGHT//2 + 120)
    
    def hide_pause_overlay(self):
        if self.overlay:
            self.canvas.delete(self.overlay)
            self.canvas.delete(self.pause_text)
            self.overlay = None
        self.volume_label.place_forget()
        self.volume_slider.place_forget()
        self.btn_menu.place_forget()
        self.btn_restart.place_forget()
        self.btn_quit.place_forget()

    def check_game_over(self):
        if not self.chart and not self.drums:
            pygame.mixer.music.stop()
            self.canvas.create_text(WIDTH//2, HEIGHT//2, text="遊戲結束！", font=("Arial", 32), fill="black")
            

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
        pygame.mixer.music.set_volume(self.settings.volume / 100)
        pygame.mixer.music.play()

    def schedule_drums(self):
        now = int(time.time() * 1000) - self.start_time
        for note in self.chart:
            if note['time'] <= now + 200:  # 時間快到就生成
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
        if self.paused:
            self.root.after(30, self.move_drums)
            return
         
        for drum in self.drums:
            drum['x'] -= DRUM_SPEED
            self.canvas.coords(drum['id'], drum['x'], HEIGHT // 2 - 30, drum['x'] + 60, HEIGHT // 2 + 30)
        self.drums = [d for d in self.drums if d['x'] + 60 > 0]
        self.root.after(30, self.move_drums)
        self.check_game_over()

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
    settings = GameSettings()
    menu = MainMenu(root, settings)
    root.mainloop()

