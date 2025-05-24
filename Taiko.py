import tkinter as tk
import random

WIDTH = 800
HEIGHT = 400
SPEED = 5
HIT_POSITION = 100  # 鼓面位置
TICK_INTERVAL = 20  # ms

class TaikoGame:
    def __init__(self, root):
        self.root = root
        self.root.title("簡易太鼓達人")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="white")
        self.canvas.pack()

        self.score = 0
        self.notes = []
        self.running = True

        self.canvas.create_text(70, 30, text="分數：", font=("Arial", 16), anchor="w")
        self.score_text = self.canvas.create_text(140, 30, text="0", font=("Arial", 16), anchor="w")

        # 鼓面區域
        self.canvas.create_oval(HIT_POSITION-40, HEIGHT//2-40, HIT_POSITION+40, HEIGHT//2+40, fill="gray", outline="black")

        # 綁定按鍵
        self.root.bind("<KeyPress-z>", self.hit_red)
        self.root.bind("<KeyPress-x>", self.hit_blue)

        self.root.after(1000, self.spawn_note)
        self.root.after(TICK_INTERVAL, self.move_notes)

    def spawn_note(self):
        if not self.running:
            return
        kind = random.choice(["red", "blue"])
        color = "red" if kind == "red" else "blue"
        note = self.canvas.create_oval(WIDTH, HEIGHT//2-20, WIDTH+40, HEIGHT//2+20, fill=color)
        self.notes.append((note, kind))
        self.root.after(random.randint(1000, 2000), self.spawn_note)

    def move_notes(self):
        if not self.running:
            return
        to_remove = []
        for note, _ in self.notes:
            self.canvas.move(note, -SPEED, 0)
            x1, y1, x2, y2 = self.canvas.coords(note)
            if x2 < 0:
                to_remove.append((note, _))

        for note in to_remove:
            self.notes.remove(note)
            self.canvas.delete(note[0])

        self.root.after(TICK_INTERVAL, self.move_notes)

    def hit_red(self, event=None):
        self.hit("red")

    def hit_blue(self, event=None):
        self.hit("blue")

    def hit(self, color):
        for note, kind in self.notes:
            x1, y1, x2, y2 = self.canvas.coords(note)
            if HIT_POSITION - 30 <= x1 <= HIT_POSITION + 30 and kind == color:
                self.canvas.delete(note)
                self.notes.remove((note, kind))
                self.score += 10
                self.canvas.itemconfig(self.score_text, text=str(self.score))
                break

if __name__ == "__main__":
    root = tk.Tk()
    game = TaikoGame(root)
    root.mainloop()
