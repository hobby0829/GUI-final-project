import os
import tkinter as tk
from tkinter import messagebox
import json
import time
import pygame
import threading
import cv2
from PIL import Image, ImageTk
import numpy as np
import math

WIDTH = 800
HEIGHT = 400
DRUM_SPEED = 5
JUDGE_LINE = 100
HIT_RANGE = 50

HIT_WAV_RED = "assets/sound/hit_red.wav"
HIT_WAV_BLUE = "assets/sound/hit_blue.mp3"
HIT_WAV = "assets/sound/hit.mp3"
BEAT_MAP = "assets/beatmap"
SONG_LIST = "assets/song"
files = os.listdir(SONG_LIST)
BGM_MENU = os.path.join(SONG_LIST, files[0])
SCORE_LIST = "assets/score.json"
MV = "assets/MV"
SETTINGS = "assets/settings.json"

# Cytus
SPAWN_OFFSET = 1.5  # 提前1.5秒顯示 note
HIT_NOTE = 0.15   # 允許誤差±0.15秒判定 Perfect

btn_style = {
    "font": ("Arial", 14, "bold"),
    "fg": "white",
    "activebackground": "#d48806",
    "activeforeground": "white",
    "bd": 0,
    "relief": "flat",
    "width": 12,
    "height": 0,
    "cursor": "hand2"
}

class GameSettings:
    def __init__(self):
        self.filepath = SETTINGS
        self.volume = 100
        self.red_button = "<KeyPress-z>"
        self.blue_button = "<KeyPress-x>"

        self.load_settings()

    def load_settings(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and data:
                        settings = data[0]
                        self.volume = settings.get("volume", 100)
                        self.red_button = settings.get("red_button", "<KeyPress-z>")
                        self.blue_button = settings.get("blue_button", "<KeyPress-x>")
            except Exception as e:
                print("讀取設定檔時發生錯誤：", e)
        else:
            self.save_settings()

    def save_settings(self):
        data = [{
            "volume": self.volume,
            "red_button": self.red_button,
            "blue_button": self.blue_button
        }]
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print("寫入設定檔時發生錯誤：", e)

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
        SongSelect(self.root, self.settings)


    def play_bgm(self):
        pygame.mixer.music.load(self.bgm)
        pygame.mixer.music.set_volume(self.settings.volume / 100)
        pygame.mixer.music.play()
    

    def show_options_menu(self):
        # 建立半透明遮罩與標題
        self.hide_pause_buttons()
        self.options_overlay = self.canvas.create_rectangle(100, 50, WIDTH-100, HEIGHT-50, fill='black')
        self.options_title = self.canvas.create_text(WIDTH//2, HEIGHT//2 - 100, text="選項", font=("Arial", 28), fill="white")

        # 音量控制
        self.volume_label = tk.Label(self.root, text="背景音樂音量", font=("Arial", 14), bg="black", fg="white")
        self.volume_label.place(x=WIDTH//2 - 60, y=HEIGHT//2 - 75)

        current_volume = pygame.mixer.music.get_volume()
        volume_var = tk.DoubleVar(value=current_volume * 100)

        def set_volume(val):
            volume = float(val) / 100
            pygame.mixer.music.set_volume(volume)
            self.settings.volume = float(val)
            self.settings.save_settings()

        self.volume_slider = tk.Scale(self.root, from_=0, to=100, orient='horizontal',
                                    variable=volume_var, command=set_volume, bg="black", fg="white",
                                    troughcolor='gray')
        self.volume_slider.place(x=WIDTH//2 - 60, y=HEIGHT//2 - 30)

        # 按鍵設定按鈕（點下後再顯示 keybind 編輯區）
        self.btn_keybind = tk.Button(self.root, text="更改按鍵", font=("Arial", 12),
                                    command=self.show_keybind_controls)
        self.btn_keybind.place(x=WIDTH//2 - 50, y=HEIGHT//2 + 40)

        # 關閉選單按鈕
        self.keybind_visible = False
        self.btn_close_options = tk.Button(self.root, text="關閉選單", font=("Arial", 12),
                                        command=self.hide_options_menu)
        self.btn_close_options.place(x=WIDTH//2 - 50, y=HEIGHT//2 + 90)

    def show_keybind_controls(self):
        self.keybind_visible = True
        self.hide_options_menu()
        self.options_overlay = self.canvas.create_rectangle(100, 50, WIDTH-100, HEIGHT-50, fill='black')

        # 顯示提示文字
        self.keybind_tip = tk.Label(self.root, text="點擊欄位後按下要設定的按鍵", font=("Arial", 10), fg="gray", bg="black")
        self.keybind_tip.place(x=WIDTH//2 - 50, y=HEIGHT//2 - 100)

        self.red_var = tk.StringVar()
        self.blue_var = tk.StringVar()

        # 紅色標籤與欄位
        self.red_label = tk.Label(self.root, text="紅色:", font=("Arial", 12), bg="black", fg="white")
        self.red_label.place(x=WIDTH//2 - 120, y=HEIGHT//2 - 50)

        self.red_entry = tk.Entry(self.root, font=("Arial", 12), textvariable=self.red_var, state="readonly")
        self.red_entry.place(x=WIDTH//2 - 60, y=HEIGHT//2 -50)

        # 藍色標籤與欄位
        self.blue_label = tk.Label(self.root, text="藍色:", font=("Arial", 12), bg="black", fg="white")
        self.blue_label.place(x=WIDTH//2 - 120, y=HEIGHT//2)

        self.blue_entry = tk.Entry(self.root, font=("Arial", 12), textvariable=self.blue_var, state="readonly")
        self.blue_entry.place(x=WIDTH//2 - 60, y=HEIGHT//2)

        # 特殊按鍵支援
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
                var.set("")  # 不合法清空

        self.red_entry.bind("<KeyPress>", lambda e: handle_key(e, self.red_var))
        self.blue_entry.bind("<KeyPress>", lambda e: handle_key(e, self.blue_var))

        # 初始化顯示當前綁定
        red_key = self.settings.red_button.replace("<KeyPress-", "").replace(">", "")
        blue_key = self.settings.blue_button.replace("<KeyPress-", "").replace(">", "")
        self.red_var.set(red_key)
        self.blue_var.set(blue_key)

        # 儲存按鈕
        self.btn_back = tk.Button(self.root, text="返回", font=("Arial", 12), command=self.back_to_options_menu)
        self.btn_back.place(x=WIDTH//2 - 60, y=HEIGHT//2 + 50)
        self.btn_save_keys = tk.Button(self.root, text="儲存按鍵", font=("Arial", 12), command=self.save_keybinds)
        self.btn_save_keys.place(x=WIDTH//2 + 20, y=HEIGHT//2 + 50)
    
    def back_to_options_menu(self):
        self.keybind_visible = False
        self.canvas.delete(self.options_overlay)
        self.hide_keybind_controls()
        self.show_options_menu()
    
    
    def save_keybinds(self):
        red_key = self.red_var.get().strip()
        blue_key = self.blue_var.get().strip()
        if red_key and blue_key:
            self.settings.red_button = f"<KeyPress-{red_key}>"
            self.settings.blue_button = f"<KeyPress-{blue_key}>"
            self.settings.save_settings()
            messagebox.showinfo("成功", "按鍵綁定已更新")
            self.keybind_visible = False
            self.canvas.delete(self.options_overlay)
            self.hide_keybind_controls()
            self.show_options_menu()
        else:
            messagebox.showwarning("錯誤", "請按下有效按鍵")
    
    def hide_pause_buttons(self):
        self.start_btn.place_forget()
        self.quit_btn.place_forget()

    def restore_pause_buttons(self):
        self.start_btn.place(x=WIDTH//2 - 60, y=HEIGHT//2)
        self.quit_btn.place(x=WIDTH//2 - 60, y=HEIGHT//2 + 50)

    def hide_options_menu(self):
        if self.options_overlay:
            self.canvas.delete(self.options_overlay)
            self.canvas.delete(self.options_title)
            self.options_overlay = None

        self.volume_label.place_forget()
        self.volume_slider.place_forget()
        self.btn_keybind.place_forget()
        self.btn_close_options.place_forget()
        self.hide_keybind_controls()
        if self.keybind_visible:
            return
        else:
            self.restore_pause_buttons()

    def hide_keybind_controls(self):
        for attr in [
            "keybind_tip", "red_entry", "blue_entry", "btn_back", 
            "btn_save_keys", "red_label", "blue_label"
        ]:
            widget = getattr(self, attr, None)
            if widget:
                widget.destroy()
                delattr(self, attr)
    
class SongSelect:
    def __init__(self, root, settings):
        self.root = root
        
        self.settings = settings
        self.confirmed = False  # 初始值
        self.info_widgets = []
        self.beatmap_path = ''
        self.song_path = ''
        self.default_song = ''
        self.bgm = ''
        self.mv_able = False

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='#1e1e1e')
        self.canvas.pack()

        self.title = self.canvas.create_text(400, 40, text="選擇歌曲", fill="white", font=("Arial", 28, "bold"))
        self.song_buttons = []

        self.selected_mode = 'taiko'  # 預設太鼓模式
        self.mode_buttons = []  # 存儲模式按鈕元件

        mode_canvas = None

        # 左上角的返回按鈕
        self.back_btn = tk.Button(root, text="回主菜單", font=("Arial", 12), command=self.return_to_main_menu)
        self.back_btn.place(x=10, y=10)

        self.load_song_list(SONG_LIST)  # 讀取歌曲資料夾名稱

    def play_bgm(self):
        pygame.mixer.music.load(self.bgm)
        pygame.mixer.music.set_volume(self.settings.volume / 100)
        pygame.mixer.music.play()

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
            if i == 0:
                self.default_song = song
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
                width=20,
                cursor="hand2"
            )
            btn.place(x=WIDTH//4, y=HEIGHT//4 + i * 50)
            self.song_buttons.append(btn)
        self.confirm_song(self.default_song, self.settings)
    

    def confirm_song(self, song, settings):

        def select_mode_canvas(mode):
            self.selected_mode = mode
            # 更新圓形按鈕顏色
            mode_canvas.itemconfig(mode_circles['taiko'],
                                        fill="#f44336" if mode == 'taiko' else "#555555")
            mode_canvas.itemconfig(mode_circles['cytus'],
                                        fill="#4CAF50" if mode == 'cytus' else "#555555")
            
        self.clear_info_panel()
        self.mode_buttons.clear()

        # 嘗試讀取該首歌的最高分數
        try:
            with open(SCORE_LIST, "r", encoding="utf-8") as f:
                scores = json.load(f)
                score_entry = next((s for s in scores if s["song"] == song), None)
                high_score = score_entry["score"] if score_entry else 0
        except (FileNotFoundError, json.JSONDecodeError):
            high_score = 0  # 檔案不存在或格式錯誤，預設為 0 分

        self.bgm = os.path.join(SONG_LIST, f'{song}.mp3')
        self.play_bgm()
        # 顯示資訊
        song_info = {'song':song, 'difficulty':'未知', 'score': high_score}
        
        label = tk.Label(self.root, text=f"歌曲名稱: {song_info['song']}\n"
                        + f"難度: {song_info['difficulty']}\n"
                        + f"最高分數: {song_info['score']}\n"
                        , font=("Arial", 12), bg="#1e1e1e", fg="white", justify="left")
        
        label.place(x=WIDTH//2 + 100, y=HEIGHT//4)
        self.info_widgets.append(label)

        # 模式選擇標籤
        mode_label = tk.Label(self.root, text="選擇模式：", font=("Arial", 12), bg="#1e1e1e", fg="white")
        mode_label.place(x=WIDTH//2 + 100, y=HEIGHT//4 + 100)
        self.info_widgets.append(mode_label)

        # 使用 Canvas 畫出圓形按鈕
        mode_canvas = tk.Canvas(self.root, width=300, height=100, bg="#1e1e1e", highlightthickness=0)
        mode_canvas.place(x=WIDTH//2 + 80, y=HEIGHT//4 + 130)
        self.info_widgets.append(mode_canvas)

        # 畫太鼓模式圓形
        taiko_circle = mode_canvas.create_oval(10, 10, 80, 80,
                                                    fill="#f44336" if self.selected_mode == 'taiko' else "#555555",
                                                    outline="white", width=2)
        taiko_text = mode_canvas.create_text(45, 45, text="太鼓", fill="white", font=("Arial", 10, "bold"))
        mode_canvas.tag_bind(taiko_circle, "<Button-1>", lambda e: select_mode_canvas('taiko'))
        mode_canvas.tag_bind(taiko_text, "<Button-1>", lambda e: select_mode_canvas('taiko'))

        # 畫 Cytus 模式圓形
        cytus_circle = mode_canvas.create_oval(110, 10, 180, 80,
                                                    fill="#4CAF50" if self.selected_mode == 'cytus' else "#555555",
                                                    outline="white", width=2)
        cytus_text = mode_canvas.create_text(145, 45, text="Cytus", fill="white", font=("Arial", 10, "bold"))
        mode_canvas.tag_bind(cytus_circle, "<Button-1>", lambda e: select_mode_canvas('cytus'))
        mode_canvas.tag_bind(cytus_text, "<Button-1>", lambda e: select_mode_canvas('cytus'))

        # 儲存圖形 id，以便切換顏色用
        mode_circles = {
            'taiko': taiko_circle,
            'cytus': cytus_circle
        }

        # 確認按鈕
        self.beatmap_path = os.path.join("assets", "beatmap", f"{song}.json")
        self.song_path = os.path.join("assets", "song", f"{song}.mp3")
        confirm_btn = tk.Button(self.root, text="開始遊玩", font=("Arial", 12), bg="#2196F3", fg="white",
                                command=lambda song=song:self.game_start(song))
        
        filename = f"{song}.mp4"
        filepath = os.path.join(MV, filename)
        if os.path.isfile(filepath):
            switch_MV_btn = tk.Button(self.root, text="使用MV", font=("Arial", 12), bg="#2196F3", fg="white",)
            switch_MV_btn.config(command=lambda btn=switch_MV_btn: self.switch_MV(btn))
            switch_MV_btn.place(x=800//2 + 200, y=200)
            self.info_widgets.append(switch_MV_btn)
            
        
        confirm_btn.place(x=800//2 + 100, y=200)
        self.info_widgets.append(confirm_btn)

    def select_mode(self, mode):
        self.selected_mode = mode
        # 更新按鈕顏色
        for btn in self.mode_buttons:
            text = btn.cget("text")
            if text == "太鼓模式":
                btn.config(bg="#f44336" if mode == 'taiko' else "#555555")
            elif text == "Cytus模式":
                btn.config(bg="#4CAF50" if mode == 'cytus' else "#555555")

    def switch_MV(self, btn):
        if self.mv_able == False:
            self.mv_able = True
            btn.config(text='不使用MV')
        else:
            self.mv_able = False
            btn.config(text='使用MV')

    def game_start(self, song):
        self.beatmap_path = os.path.join("assets", "beatmap", f"{song}.json")
        self.song_path = os.path.join("assets", "song", f"{song}.mp3")
        pygame.mixer.music.stop()
        self.cleanup()
        if self.selected_mode == 'taiko':
            TaikoGame(self.root, self.song_path, self.beatmap_path, self.settings, self.mv_able)
        elif self.selected_mode == 'cytus':
            Cytus(self.root, song, self.settings, self.mv_able)  # 若 Cytus 也需要 MV 開關，你可以再傳 self.mv_able

    def clear_info_panel(self):
        for widget in self.info_widgets:
            widget.destroy()
        self.info_widgets.clear()

    def cleanup(self):
        self.clear_info_panel()
        self.canvas.destroy()
        self.back_btn.destroy()
        for btn in self.song_buttons:
            btn.destroy()

class TaikoGame:
    def __init__(self, root, song_path, beatmap_path, settings, is_use_mv=False):
        self.root = root
        self.settings = settings
        self.root.title("太鼓達人加強版")
        self.song_name = os.path.splitext(os.path.basename(song_path))[0]
        self.line_path = os.path.splitext(beatmap_path)[0] + "_line.json"
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='black')
        self.canvas.pack()

        # 初始化 pygame 音效
        pygame.mixer.init()
        self.hit_sound_red = pygame.mixer.Sound(HIT_WAV_RED)
        self.hit_sound_blue = pygame.mixer.Sound(HIT_WAV_BLUE)
        self.bgm = song_path
        self.beatmap = beatmap_path

        # 分數與 combo
        self.score = 0
        self.combo = 0
        
        # 暫停按鈕
        self.back_btn = tk.Button(root, text="暫停", font=("Arial", 12), command=self.toggle_pause)
        self.back_btn.place(x=750, y=10)

        # 顯示文字
        self.score_text = self.canvas.create_text(10, 10, anchor='nw', text='Score: 0', font=('Arial', 16), fill='white')
        self.combo_text = self.canvas.create_text(10, 40, anchor='nw', text='Combo: 0', font=('Arial', 16), fill='white')
        self.judge_text = self.canvas.create_text(WIDTH // 2, 50, text='', font=('Arial', 24), fill='red')

        # 判定線
        self.canvas.create_line(JUDGE_LINE, 0, JUDGE_LINE, HEIGHT, fill='gray', dash=(4, 2))

        # 鼓列表與開始時間
        self.drums = []
        self.start_time = None
        self.pause_time = None
        self.total_pause_duration = 0
        self.chart = []

        self.drum_timer_id = None
        self.move_timer_id = None

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

        self.btn_menu = tk.Button(root, text="返回主選單", command=self.back_to_menu, bg="#2196F3", **btn_style)
        self.btn_restart = tk.Button(root, text="重新開始(R)", 
                                     command=lambda beatmap_path = beatmap_path, song_path = song_path:                                                                        
                                     self.restart_game(song_path, beatmap_path), bg="#4CAF50", **btn_style)
        self.btn_quit = tk.Button(root, text="繼續(P)", command=self.toggle_pause, bg="#F44336", **btn_style)

        self.is_use_mv = is_use_mv
        self.update_mv_timer_id = None  # 儲存 after 的 id
        self.running = False
        if is_use_mv:
            # 載入影片
            self.video_path = os.path.join(MV, self.song_name + '.mp4')
            self.cap = cv2.VideoCapture(self.video_path)
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frame_interval = int(1000 / self.fps)
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.image_on_canvas = None
            self.mv_start_time = None
            self.running = True
            self.current_frame = 0


        self.time_text_id = None  # 這是用來記錄畫出來的文字的 ID
        self.offset = (((WIDTH-JUDGE_LINE)/DRUM_SPEED) * 0.03 )*0.9
        self.set_volume(settings.volume)

        # 載入譜面與開始遊戲
        self.load_score(beatmap_path)
        self.first_beat = int(self.chart[0]['time'])
        self.start_game(is_use_mv)

    def update_time_text(self):
        now = pygame.mixer.music.get_pos() / 1000  # 換成秒
        display_time = f"{int(now // 60):02}:{int(now % 60):02}.{int((now * 1000) % 1000):03}"

        if self.time_text_id is not None:
            # 更新現有文字
            self.canvas.itemconfig(self.time_text_id, text=f"音樂時間：{display_time}")
        else:
            # 第一次畫出時間文字
            self.time_text_id = self.canvas.create_text(
                100, 30, text=f"音樂時間：{display_time}",
                fill="white", font=("Arial", 16, "bold"), anchor="w"
            )

        # 每 1000 毫秒（1 秒）後再次呼叫自己
        self.canvas.after(1000, self.update_time_text)

    def update_mv_frame(self):
        if not self.running or self.paused or not self.canvas.winfo_exists():
            return

        elapsed_time = (time.time() - self.mv_start_time) * 1000  # 毫秒
        expected_frame = int(elapsed_time / 1000 * self.fps)

        ret = False  # 預設
        while self.current_frame < expected_frame:
            ret, frame = self.cap.read()
            if not ret:
                self.running = False
                self.cap.release()
                return
            self.current_frame += 1

        if ret:
            frame = cv2.resize(frame, (800, 400))  # 調整畫面大小
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image)

            if self.image_on_canvas is None:
                self.image_on_canvas = self.canvas.create_image(0, 0, anchor='nw', image=photo)
                self.canvas.tag_lower(self.image_on_canvas)
            else:
                self.canvas.itemconfig(self.image_on_canvas, image=photo)

            self.canvas.image = photo

        self.update_mv_timer_id = self.root.after(self.frame_interval, self.update_mv_frame)

    def back_to_menu(self):
        self.hide_pause_overlay()
        pygame.mixer.music.stop()
        if self.is_use_mv:
            self.cap.release()
        self.canvas.destroy()
        MainMenu(self.root, self.settings)

    def restart_game(self, song_path, beatmap_path):
        self.hide_pause_overlay()
        self.paused = False
        pygame.mixer.music.stop()
        self.score = 0
        self.combo = 0
        self.update_score()
        for drum in self.drums:
            self.canvas.delete(drum['id'])
        self.root.after_cancel(self.drum_timer_id)
        try:
            self.root.after_cancel(self.move_timer_id)
        except (AttributeError, ValueError):
            pass  # 無需取消
        self.drums.clear()
        self.cleanup()
        TaikoGame(self.root, song_path, beatmap_path, self.settings, self.is_use_mv)
        
    def toggle_pause(self):
        self.toggle_pause_key(event=None)

    def toggle_pause_key(self, event=None):
        if not self.paused:
            self.paused = True
            pygame.mixer.music.pause()
            self.pause_time = time.time()
            self.show_pause_overlay()
        else:
            self.paused = False
            pygame.mixer.music.unpause()
            # 調整 MV 開始時間，避免播放錯誤時間
            pause_duration = time.time() - self.pause_time
            self.total_pause_duration += pause_duration
            if self.is_use_mv:
                self.mv_start_time += pause_duration
                self.update_mv_frame()  # 重新啟動畫面更新
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
        self.btn_restart.place(x=WIDTH//2 - 60, y=HEIGHT//2 + 90)
        self.btn_quit.place(x=WIDTH//2 - 60, y=HEIGHT//2 + 140)
    
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
            self.root.after_cancel(self.drum_timer_id)
            self.root.after_cancel(self.move_timer_id)
            self.canvas.create_text(WIDTH // 2, HEIGHT // 2, text="遊戲結束！", font=("Arial", 32), fill="white")

            # 嘗試載入現有的分數資料
            try:
                with open(SCORE_LIST, "r", encoding="utf-8") as f:
                    scores = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                scores = []

            # 檢查當前歌曲是否已在紀錄中
            song_found = False
            for entry in scores:
                if entry["song"] == self.song_name:  # self.song_name 必須在 game_start 中儲存
                    song_found = True
                    if self.score > entry["score"]:
                        entry["score"] = self.score  # 更新高分
                    break

            if not song_found:
                scores.append({"song": self.song_name, "score": self.score})  # 新增新歌曲記錄

            # 寫回檔案
            with open(SCORE_LIST, "w", encoding="utf-8") as f:
                json.dump(scores, f, ensure_ascii=False, indent=4)

            self.drums.clear()
            if self.is_use_mv:
                self.cap.release()
            self.cleanup()
            Score_Summary(self.root, self.score, self.combo, self.song_name, self.settings, 'Taiko', 
                           self.is_use_mv)
            
    def load_score(self, file):
        with open(file, 'r') as f:
            self.chart = json.load(f)
    
    def load_lines(self):
        self.lines = []
        try:
            with open(self.line_path, 'r', encoding='utf-8') as f:
                self.lines = json.load(f)
                print(f"[line] Loaded {len(self.lines)} lines")
        except Exception as e:
            print(f"[line] Failed to load lines: {e}")

    def schedule_lines(self):
        for line in self.lines:
            delay = line["time"]
            self.root.after(delay, lambda l=line: self.create_line(l))

    def create_line(self, line):
        # 畫線
        line_id = self.canvas.create_line(line["x1"], line["y1"], line["x2"], line["y2"], fill="#FFD700", width=5)
        print(f"[line] Created line {line['id']} at {line['time']}ms")

        # 記住線的 Canvas ID（可選）
        line["canvas_id"] = line_id

        # 安排線的消失
        lifetime = line["end_time"] - line["time"]
        self.root.after(lifetime, lambda: self.remove_line(line))
    
    def remove_line(self, line):
        if "canvas_id" in line:
            self.canvas.delete(line["canvas_id"])
            print(f"[line] Removed line {line['id']} at {line['end_time']}ms")

    def start_game(self, is_use_mv):
        def contain():
            threading.Thread(target=self.play_bgm).start()
            self.start_time = int(time.time())
            self.schedule_drums()
            self.update_time_text()
            self.load_lines()
            self.schedule_lines()
            self.move_drums()
        
        if is_use_mv:
            self.mv_start_time = time.time()
            self.update_mv_frame()  # ✅ 提前播放影片

        # start_delay = max(0, int(self.offset * 1000) - self.first_beat)
        start_delay = 0
        self.root.after(start_delay, contain)

    def play_bgm(self):
        pygame.mixer.music.load(self.bgm)
        pygame.mixer.music.set_volume(self.settings.volume / 100)
        pygame.mixer.music.play()

    def schedule_drums(self):
        # 防止畫面已被銷毀仍執行排程
        if not self.canvas.winfo_exists():
            return
        
        if self.paused:
            self.drum_timer_id = self.root.after(50, self.schedule_drums)
            return
        
        now = int((time.time() - self.total_pause_duration - self.start_time) * 1000)
        #now = pygame.mixer.music.get_pos()
        next_note_time = self.chart[0]['time'] if self.chart else None
        #print(f"[DEBUG] now={now}, next_note_time={self.chart[0]['time'] if self.chart else 'None'}")
        for note in self.chart:
            if note['time'] <= now:
                self.spawn_drum(note)
                self.chart.remove(note)
        self.drum_timer_id = self.root.after(50, self.schedule_drums)

    def spawn_drum(self, note):
        drum_type = note['type']
        x = note['start_x']
        y = note['start_y']
        end_x = note['end_x']
        end_y = note['end_y']
        move_time = note['move_time']  # 讀取移動時間

        width = 20
        height = 80
        border_color = "#FFD700"
        gradient_colors = self.get_gradient_colors(drum_type, steps=10)

        drum_ids = []

        # 畫外框
        border_id = self.canvas.create_rectangle(
            x, y - height // 2, x + width, y + height // 2,
            outline=border_color, width=2, fill=""
        )
        drum_ids.append(border_id)

        # 畫漸層
        step_height = height // len(gradient_colors)
        for i, color in enumerate(gradient_colors):
            step_y1 = y - height // 2 + i * step_height
            step_y2 = step_y1 + step_height
            rect_id = self.canvas.create_rectangle(
                x + 2, step_y1, x + width - 2, step_y2,
                outline="", fill=color
            )
            drum_ids.append(rect_id)

        now = int((time.time() - self.total_pause_duration - self.start_time) * 1000)
        hit_time = now + move_time

        self.drums.append({
            'id': drum_ids,
            'type': drum_type,
            'start_x': x,
            'start_y': y,
            'end_x': end_x,
            'end_y': end_y,
            'start_time': int((time.time() - self.total_pause_duration - self.start_time) * 1000),
            'hit_time': hit_time,
            'move_time': move_time,
            'last_x': x,
            'last_y': y,
            'width': width,
            'height': height
        })
    
    def get_gradient_colors(self, drum_type, steps=10):
        if drum_type == "red":
            start = (255, 100, 100)
            end = (255, 0, 0)
        else:  # blue
            start = (100, 100, 255)
            end = (0, 0, 255)

        colors = []
        for i in range(steps):
            r = int(start[0] + (end[0] - start[0]) * i / (steps - 1))
            g = int(start[1] + (end[1] - start[1]) * i / (steps - 1))
            b = int(start[2] + (end[2] - start[2]) * i / (steps - 1))
            colors.append(f'#{r:02x}{g:02x}{b:02x}')
        return colors

    def move_drums(self):
        if not self.canvas.winfo_exists():
            return

        if self.paused:
            self.root.after(30, self.move_drums)
            return

        now = int((time.time() - self.total_pause_duration - self.start_time) * 1000)
        new_drums = []
        missed_drums = []

        for drum in self.drums:
            start_x = drum['start_x']
            start_y = drum['start_y']
            end_x = drum['end_x']
            end_y = drum['end_y']
            t0 = drum['start_time']
            t1 = drum['hit_time']
            progress = (now - t0) / (t1 - t0) if (t1 - t0) > 0 else 1
            progress = min(max(progress, 0), 1)

            x = start_x + (end_x - start_x) * progress
            y = start_y + (end_y - start_y) * progress

            dx = x - drum['last_x']
            dy = y - drum['last_y']

            for item_id in drum['id']:
                self.canvas.move(item_id, dx, dy)

            drum['last_x'] = x
            drum['last_y'] = y

            if now > t1 + 200:  # 超過擊打時間
                missed_drums.append(drum)
            else:
                new_drums.append(drum)

        # 刪除超時鼓
        for drum in missed_drums:
            self.canvas.itemconfig(self.judge_text, text='Miss')
            for item_id in drum['id']:
                self.canvas.delete(item_id)
            self.combo = 0
            self.update_score()

        self.drums = new_drums

        self.check_game_over()
        self.move_timer_id = self.root.after(30, self.move_drums)

    def hit_red(self, event):
        self.play_hit_sound('red')
        self.check_hit('red')

    def hit_blue(self, event):
        self.play_hit_sound('blue')
        self.check_hit('blue')

    def check_hit(self, hit_type):
        target_drum = None
        min_x = float('inf')

        if hit_type is not None:
            for drum in self.drums:
                distance = abs(drum['last_x'] - JUDGE_LINE)
                if distance < HIT_RANGE:
                    if drum['last_x'] < min_x:
                        min_x = drum['last_x']
                        target_drum = drum

            if target_drum:
                if target_drum['type'] == hit_type:
                    self.canvas.itemconfig(self.judge_text, text='Perfect!')
                    for item_id in target_drum['id']:
                        self.canvas.delete(item_id)
                    self.drums.remove(target_drum)
                    self.combo += 1
                    self.score += 100
                else:
                    self.canvas.itemconfig(self.judge_text, text='Miss')
                    self.combo = 0
                self.update_score()
            else:
                self.canvas.itemconfig(self.judge_text, text='Miss')
                self.combo = 0
                self.update_score()

        else:
            to_remove = []
            for drum in self.drums:
                if drum['last_x'] < JUDGE_LINE - HIT_RANGE:
                    self.canvas.itemconfig(self.judge_text, text='Miss')
                    for item_id in drum['id']:
                        self.canvas.delete(item_id)
                    to_remove.append(drum)
                    self.combo = 0
                    self.update_score()
            for drum in to_remove:
                self.drums.remove(drum)


        ## 沒有鼓在範圍內也 Miss
        #self.canvas.itemconfig(self.judge_text, text='Miss')
        #self.combo = 0
        #self.update_score()

    def play_hit_sound(self, drum_type):
        if drum_type == 'red':
            self.hit_sound_red.play()
        elif drum_type == 'blue':
            self.hit_sound_blue.play()

    def update_score(self):
        self.canvas.itemconfig(self.score_text, text=f'Score: {self.score}')
        self.canvas.itemconfig(self.combo_text, text=f'Combo: {self.combo}')

    def cleanup(self):
        self.canvas.destroy()
        
class Cytus:
    def __init__(self, root, song_name, settings, is_use_mv=False):
        self.root = root
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='#1e1e1e')
        self.canvas.pack()
        self.chart = []
        self.song_name = song_name
        # 初始化 pygame 音效
        pygame.mixer.init()

        # 載入音效
        self.hit_sound = pygame.mixer.Sound(HIT_WAV)
        self.beatmap = os.path.join(BEAT_MAP, song_name+'.json')
        self.bgm = os.path.join(SONG_LIST, song_name+'.mp3')

        # 分數與 combo
        self.score = 0
        self.combo = 0
        # 顯示文字
        self.score_text = self.canvas.create_text(10, 10, anchor='nw', text='Score: 0', font=('Arial', 16), fill='white')
        self.combo_text = self.canvas.create_text(10, 40, anchor='nw', text='Combo: 0', font=('Arial', 16), fill='white')
        self.judge_text = self.canvas.create_text(WIDTH // 2, 50, text='', font=('Arial', 24), fill='red')
        
        # 暫停按鈕
        self.back_btn = tk.Button(root, text="暫停", font=("Arial", 12), command=self.toggle_pause)
        self.back_btn.place(x=750, y=10)

        self.btn_menu = tk.Button(root, text="返回主選單", command=self.back_to_menu, bg="#2196F3", **btn_style)
        self.btn_restart = tk.Button(root, text="重新開始(R)", 
                                     command=lambda beatmap_path = self.beatmap, song_path = self.bgm:                                                                        
                                     self.restart_game(song_path, beatmap_path), bg="#4CAF50", **btn_style)
        self.btn_quit = tk.Button(root, text="繼續(P)", command=self.toggle_pause, bg="#F44336", **btn_style)

        self.paused = False
        self.overlay = None

        self.notes = []
        self.active_notes = []
        self.start_time = None
        self.pause_time = None
        self.total_pause_duration = 0

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

        self.note_id_text = self.canvas.create_text(WIDTH//2, HEIGHT//2, text="", font=("Arial", 20, "bold"), fill="red", tags="ui")
        self.feedback_text = self.canvas.create_text(WIDTH//2, HEIGHT//2 - 150, text="", font=("Arial", 28, "bold"), fill="yellow", tags="ui")
        self.feedback_after_id = None

        self.settings = settings
        self.is_use_mv = is_use_mv
        self.update_mv_timer_id = None  # 儲存 after 的 id
        self.running = False
        if is_use_mv:
            # 載入影片
            self.video_path = os.path.join(MV, self.song_name + '.mp4')
            self.cap = cv2.VideoCapture(self.video_path)
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.frame_interval = int(1000 / self.fps)
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.image_on_canvas = None
            self.mv_start_time = None
            self.running = True
            self.current_frame = 0

        self.root.bind("<KeyPress-p>", self.toggle_pause_key)
        self.root.bind("<KeyPress-z>", self.handle_key_z)
        self.set_volume(settings.volume)
        self.load_music()
        self.load_score()
        self.start_game()

    def handle_key_z(self, event):
        # 取得當前滑鼠位置（相對於 canvas）
        x = self.root.winfo_pointerx() - self.canvas.winfo_rootx()
        y = self.root.winfo_pointery() - self.canvas.winfo_rooty()

        # 模擬滑鼠事件物件（傳給原本的 handle_click）
        fake_event = type("Event", (object,), {"x": x, "y": y})()
        self.handle_click(fake_event)

    def back_to_menu(self):
        self.hide_pause_overlay()
        pygame.mixer.music.stop()
        if self.is_use_mv:
            self.cap.release()
        self.cleanup()

        MainMenu(self.root, self.settings)

    def restart_game(self, song_path, beatmap_path):
        self.hide_pause_overlay()
        self.paused = False
        pygame.mixer.music.stop()

        # 停止影片與釋放資源
        if self.is_use_mv:
            self.running = False
            self.cap.release()

        self.cleanup()
        

        # 建立新的 Cytus 實例來重啟遊戲
        Cytus(self.root, self.song_name, self.settings, self.is_use_mv)

    def toggle_pause(self):
        self.toggle_pause_key(event=None)

    def toggle_pause_key(self, event=None):
        if not self.paused:
            self.paused = True
            pygame.mixer.music.pause()
            self.pause_time = time.time()
            self.show_pause_overlay()
        else:
            self.paused = False
            pygame.mixer.music.unpause()
            # 調整 MV 開始時間，避免播放錯誤時間
            pause_duration = time.time() - self.pause_time
            self.total_pause_duration += pause_duration
            if self.is_use_mv:
                self.mv_start_time += pause_duration
                self.update_mv_frame()  # 重新啟動畫面更新
            self.hide_pause_overlay()

    def set_volume(self, val):
        volume = int(val) / 100
        self.settings.volume = int(val)
        pygame.mixer.music.set_volume(volume)

    def show_pause_overlay(self):
        # 半透明黑色遮罩（使用 rectangle 模擬）
        self.overlay = self.canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill='black', stipple='gray50')
        self.pause_text = self.canvas.create_text(WIDTH//2, HEIGHT//2 - 60, text="暫停中", font=("Arial", 28), fill="white")

        # 顯示音量滑桿
        self.volume_label.place(x=WIDTH//2 - 100, y=HEIGHT//2 - 50)
        self.volume_slider.place(x=WIDTH//2 - 100, y=HEIGHT//2 - 20)

        self.btn_menu.place(x=WIDTH//2 - 60, y=HEIGHT//2 + 40)
        self.btn_restart.place(x=WIDTH//2 - 60, y=HEIGHT//2 + 90)
        self.btn_quit.place(x=WIDTH//2 - 60, y=HEIGHT//2 + 140)
    
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
    
    def update_score(self):
        self.canvas.itemconfig(self.score_text, text=f'Score: {self.score}')
        self.canvas.itemconfig(self.combo_text, text=f'Combo: {self.combo}')

    def check_game_over(self):

        # 1. 確認譜面已無剩餘音符，且畫面上的note已全部被消除
        no_more_notes = not self.chart and not self.notes


        if no_more_notes :
            # 停止音樂與定時器
            pygame.mixer.music.stop()

            # 顯示結束文字或結算畫面
            self.canvas.create_text(WIDTH // 2, HEIGHT // 2, text="遊戲結束！", font=("Arial", 32), fill="white")

            # 載入與更新分數紀錄（與你原本邏輯相同）
            try:
                with open(SCORE_LIST, "r", encoding="utf-8") as f:
                    scores = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                scores = []

            song_found = False
            for entry in scores:
                if entry["song"] == self.song_name:
                    song_found = True
                    if self.score > entry["score"]:
                        entry["score"] = self.score
                    break

            if not song_found:
                scores.append({"song": self.song_name, "score": self.score})

            with open(SCORE_LIST, "w", encoding="utf-8") as f:
                json.dump(scores, f, ensure_ascii=False, indent=4)

            # 清理資源
            if self.is_use_mv:
                self.cap.release()
            self.cleanup()

            # 呼叫 Cytus 風格的結算畫面（你可以修改Score_Summary，或換成自己的結算畫面）
            Score_Summary(self.root, self.score, self.combo, self.song_name, self.settings, 'Cytus', 
                           self.is_use_mv)
        else:
            # 若還沒結束，繼續下一次檢查
            self.root.after(100, self.check_game_over)

    def update_mv_frame(self):
        if not self.running or self.paused or not self.canvas.winfo_exists():
            return

        elapsed_time = (time.time() - self.mv_start_time) * 1000  # 毫秒
        expected_frame = int(elapsed_time / 1000 * self.fps)

        ret = False  # 預設
        while self.current_frame < expected_frame:
            ret, frame = self.cap.read()
            if not ret:
                self.running = False
                self.cap.release()
                return
            self.current_frame += 1

        if ret:
            frame = cv2.resize(frame, (800, 400))  # 調整畫面大小
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image)

            if self.image_on_canvas is None:
                self.image_on_canvas = self.canvas.create_image(0, 0, anchor='nw', image=photo)
                self.canvas.tag_lower(self.image_on_canvas)
            else:
                self.canvas.itemconfig(self.image_on_canvas, image=photo)

            self.canvas.image = photo

        self.update_mv_timer_id = self.root.after(self.frame_interval, self.update_mv_frame)

    def play_bgm(self):
        pygame.mixer.music.load(self.bgm)
        pygame.mixer.music.set_volume(self.settings.volume / 100)
        pygame.mixer.music.play()
        
    def load_score(self):
        with open(self.beatmap, 'r') as f:
            self.chart = json.load(f)

    def load_music(self):
        pygame.mixer.music.load(self.bgm)
        pygame.mixer.music.play()

    def start_game(self):
        self.canvas.bind("<Button-1>", self.handle_click)
        #self.canvas.bind("<KeyPress-z>", self.handle_click)
        #self.canvas.focus_set()  # 確保 canvas 有鍵盤焦點才能偵測鍵盤輸入
        
        if self.is_use_mv:
            self.mv_start_time = time.time()
            self.update_mv_frame()  # ✅ 提前播放影片
        self.start_time = time.time()
        self.update_notes()

    def get_current_time(self):
        return int((time.time() - self.total_pause_duration - self.start_time) * 1000)
    
    def update_notes(self):

        if not self.canvas.winfo_exists():
            return

        if self.paused:
            self.root.after(50, self.update_notes)
            return

        now = self.get_current_time()
        self.canvas.delete("note")

        # 添加新 notes 到畫面
        for note in self.chart[:]:
            if note['time'] - SPAWN_OFFSET * 1000 <= now:
                note['spawn_time'] = note['time'] - SPAWN_OFFSET * 1000  # 加入生成時間
                self.notes.append(note)
                self.chart.remove(note)

        # 找出下一個要打的 note（未超過）
        next_note = None
        min_diff = float('inf')
        for note in self.notes:
            diff = note['time'] - now
            if 0 <= diff < min_diff:
                min_diff = diff
                next_note = note

        for note in self.notes[:]:
            note_time = note['time']
            pos_x, pos_y = note['pos']

            if now > note_time + HIT_NOTE * 1000:
                print("Miss")
                self.show_feedback("Miss", "red")  # 顯示 Miss
                self.combo = 0
                self.update_score()
                self.notes.remove(note)
                continue

            # 動畫參數
            R_MAX = 40  # 外圈大小
            R_MIN = 5   # 內圈初始大小
            progress = min(1.0, max(0.0, (now - note['spawn_time']) / (note_time - note['spawn_time'])))  # 0~1
            inner_radius = R_MIN + (R_MAX - R_MIN) * progress

            # 畫外圈（固定）
            self.canvas.create_oval(pos_x - R_MAX, pos_y - R_MAX,
                                    pos_x + R_MAX, pos_y + R_MAX,
                                    outline="white", width=2, tags="note")

            alpha = int(255 * (1 - progress))  # 越接近打擊時刻越透明

            # 轉換 alpha 到 stipple 紋理
            if alpha > 192:
                stipple = "gray25"   # 比較不透明
            elif alpha > 128:
                stipple = "gray50"   # 中等透明
            elif alpha > 64:
                stipple = "gray75"   # 比較透明
            else:
                stipple = "gray12"   # 幾乎全透明

            self.canvas.create_oval(pos_x - inner_radius, pos_y - inner_radius,
                                    pos_x + inner_radius, pos_y + inner_radius,
                                    fill="#1e90ff", outline="", stipple=stipple, tags="note")

            # 顯示 note id（置中文字）
            self.canvas.create_text(pos_x, pos_y, text=str(note.get("id", "")),
                                    fill="white", font=("Arial", 12, "bold"), tags="note")

            # 顯示閃爍外圈（加強提示）
            if note == next_note:
                # 設定最大與最終半徑
                MAX_SHRINK_RADIUS = 80
                R_MAX = 40
                
                # 動畫進度（0 ~ 1）
                duration = note['time'] - note['spawn_time']
                progress = min(1.0, max(0.0, (now - note['spawn_time']) / duration))
                
                # 固定從 MAX_SHRINK_RADIUS 縮到 R_MAX
                shrink_radius = MAX_SHRINK_RADIUS - (MAX_SHRINK_RADIUS - R_MAX) * progress

                

                # 畫縮小動畫圓圈
                self.canvas.create_oval(pos_x - shrink_radius, pos_y - shrink_radius,
                                        pos_x + shrink_radius, pos_y + shrink_radius,
                                        outline="#00ffff", width=2, tags="note")
        if next_note:
            self.canvas.itemconfigure(self.note_id_text, text=f"NOW: {next_note.get('id', '')}")
        else:
            self.canvas.itemconfigure(self.note_id_text, text="")

        if not self.chart and not self.notes:
            self.check_game_over()
        else:
            self.root.after(16, self.update_notes)

    def handle_click(self, event):
        now = self.get_current_time()
        hit = False
        for note in self.notes[:]:
            pos_x, pos_y = note['pos']
            note_time = note['time']
            distance = ((event.x - pos_x) ** 2 + (event.y - pos_y) ** 2) ** 0.5

            if abs(now - note_time) <= HIT_NOTE * 1000 and distance <= 50:
                print("Perfect!")
                self.score += 100
                self.combo += 1
                self.notes.remove(note)
                hit = True
                self.update_score()
                self.show_feedback("Perfect", "cyan")  # 顯示 Perfect
                # 播放音效
                self.hit_sound.play()
                break

        if not hit:
            print("Miss click!")
            self.show_feedback("Miss click!", "red")  # 顯示 Miss
            self.combo = 0
            self.update_score()

    def show_feedback(self, text, color="yellow"):
        # 如果之前有排程自動清除 feedback，先取消
        if self.feedback_after_id:
            self.root.after_cancel(self.feedback_after_id)

        # 更新畫面文字
        self.canvas.itemconfigure(self.feedback_text, text=text, fill=color)

        # 安排新的清除任務，並記錄 ID
        self.feedback_after_id = self.root.after(500, lambda: self.canvas.itemconfigure(self.feedback_text, text=""))


    def cleanup(self):
        self.canvas.unbind("<Button-1>")
        self.root.unbind("<KeyPress-p>")
        
        if self.update_mv_timer_id:
            self.root.after_cancel(self.update_mv_timer_id)
            self.root.after_cancel(self.update_notes)
        # 銷毀畫布與所有相關資源
        self.canvas.destroy()

class Score_Summary:
    def __init__(self, root, score, combo, song_name, settings, mode, is_use_mv=False):
        self.root = root
        self.score = score
        self.combo = combo
        self.song_name = song_name
        self.beatmap_path = os.path.join(BEAT_MAP, song_name+'.json')
        self.song_path = os.path.join(SONG_LIST, song_name+'.mp3')
        self.mode = mode
        
        self.settings = settings
        self.is_use_mv = is_use_mv

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg='black')
        self.canvas.pack()

        self.canvas.create_text(WIDTH // 2, 80, text="遊戲結束！", font=("Arial", 32, "bold"), fill="white")
        self.canvas.create_text(WIDTH // 2, 150, text=f"總分：{self.score}", font=("Arial", 24), fill="yellow")
        self.canvas.create_text(WIDTH // 2, 200, text=f"最高連擊：{self.combo}", font=("Arial", 24), fill="lightblue")

        self.btn_menu = tk.Button(root, text="返回主選單", command=self.back_to_menu, font=("Arial", 14), bg="#2196F3", fg="white", width=15)
        self.btn_restart = tk.Button(root, text="重新開始", command=self.restart_game, font=("Arial", 14), bg="#4CAF50", fg="white", width=15)
        self.btn_exit = tk.Button(root, text="離開遊戲", command=root.quit, font=("Arial", 14), bg="#F44336", fg="white", width=15)

        self.btn_menu.place(x=WIDTH//2 - 80, y=HEIGHT//2 + 30)
        self.btn_restart.place(x=WIDTH//2 - 80, y=HEIGHT//2 + 80)
        self.btn_exit.place(x=WIDTH//2 - 80, y=HEIGHT//2 + 130)

    def back_to_menu(self):
        self.destroy()
        MainMenu(self.root, self.settings)

    def restart_game(self):
        self.destroy()
        if self.mode == 'Taiko':
            TaikoGame(self.root, self.song_path, self.beatmap_path, self.settings, self.is_use_mv)
        else:
            Cytus(self.root, self.song_name, self.settings, self.is_use_mv)

    def destroy(self):
        self.canvas.destroy()
        self.btn_menu.destroy()
        self.btn_restart.destroy()
        self.btn_exit.destroy()
    
# 主程式
if __name__ == '__main__':
    root = tk.Tk()
    settings = GameSettings()
    menu = MainMenu(root, settings)
    root.mainloop()

