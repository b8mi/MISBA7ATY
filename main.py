

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

BG, PANEL, GOLD = "#10211d", "#21443a", "#e9c575"
SAVE_FILE = Path.home() / ".tasbeeh_counts.json"

PHRASES = ["سُبْحَانَ اللَّهِ", "الْحَمْدُ لِلَّهِ", "اللَّهُ أَكْبَرُ",
           "أَسْتَغْفِرُ اللَّهَ", "لَا إِلَهَ إِلَّا اللَّهُ"]


class TasbeehApp:
    def __init__(self, root):
        self.root = root
        self.counts = self.load_counts()

        root.title("مسبحتي | عداد التسبيح")
        root.geometry("480x480")
        root.configure(bg=BG)
        root.resizable(False, False)

        tk.Label(root, text="مِسْبَحَتِي", bg=BG, fg=GOLD,
                 font=("Tahoma", 24, "bold")).pack(pady=(16, 10))

        self.phrase = tk.StringVar(value=PHRASES[0])
        tk.OptionMenu(
            root, self.phrase, *PHRASES,
            command=lambda _: self.refresh()
        ).pack()

        self.number = tk.Label(
            root, text="0", bg=BG, fg=GOLD,
            font=("Segoe UI", 68, "bold")
        )
        self.number.pack(pady=(6, 1))

        self.target = tk.IntVar(value=33)
        controls = tk.Frame(root, bg=BG)
        controls.pack()

        tk.Label(
            controls, text="الهدف", bg=BG,
            fg="white", font=("Tahoma", 11)
        ).pack(side="right", padx=10)

        for goal in (33, 100):
            tk.Radiobutton(
                controls, text=str(goal), value=goal,
                variable=self.target, command=self.refresh,
                bg=BG, fg="white", selectcolor=PANEL,
                activebackground=BG
            ).pack(side="right")

        self.progress = tk.Canvas(
            root, height=15, width=360,
            bg=PANEL, highlightthickness=0
        )
        self.progress.pack(pady=14)

        # NEW: Percentage indicator
        self.percentage = tk.Label(
            root, text="0%", bg=BG, fg=GOLD,
            font=("Tahoma", 11, "bold")
        )
        self.percentage.pack()

        self.status = tk.Label(
            root, text="", bg=BG, fg="#a9c8bc",
            font=("Tahoma", 10)
        )
        self.status.pack()

        buttons = tk.Frame(root, bg=BG)
        buttons.pack(pady=10)

        tk.Button(
            buttons, text="+1  تسبيحة", command=self.add,
            bg=GOLD, relief="flat",
            font=("Tahoma", 13, "bold"),
            padx=14, pady=6
        ).pack(side="right", padx=5)

        tk.Button(
            buttons, text="تراجع", command=self.undo,
            bg=PANEL, fg="white",
            font=("Tahoma", 10), relief="flat"
        ).pack(side="right", padx=5)

        tk.Button(
            buttons, text="تصفير", command=self.reset,
            bg=PANEL, fg="white",
            font=("Tahoma", 10), relief="flat"
        ).pack(side="right", padx=5)

        tk.Label(
            root,
            text="المسافة للعد | Ctrl+Z للتراجع",
            bg=BG, fg="#a9c8bc",
            font=("Tahoma", 10)
        ).pack()

        root.bind("<space>", lambda _: self.add())
        root.bind("<Control-z>", lambda _: self.undo())

        self.refresh()

    def load_counts(self):
        counts = {phrase: 0 for phrase in PHRASES}

        try:
            if SAVE_FILE.exists():
                data = json.loads(
                    SAVE_FILE.read_text(encoding="utf-8")
                )

                if isinstance(data, dict):
                    for phrase in PHRASES:
                        value = data.get(phrase, 0)
                        if type(value) is int and value >= 0:
                            counts[phrase] = value

        except (OSError, ValueError):
            pass

        return counts

    def save_counts(self):
        try:
            SAVE_FILE.write_text(
                json.dumps(
                    self.counts,
                    ensure_ascii=False,
                    indent=2
                ),
                encoding="utf-8"
            )
        except OSError as error:
            print(f"Could not save counts: {error}")

    def add(self):
        self.counts[self.phrase.get()] += 1
        self.save_counts()
        self.refresh()

    def undo(self):
        phrase = self.phrase.get()
        self.counts[phrase] = max(
            0, self.counts[phrase] - 1
        )
        self.save_counts()
        self.refresh()

    def reset(self):
        if messagebox.askyesno(
            "تأكيد", "هل تريد تصفير عداد الذكر الحالي؟"
        ):
            self.counts[self.phrase.get()] = 0
            self.save_counts()
            self.refresh()

    def refresh(self):
        count = self.counts.get(self.phrase.get(), 0)
        target = self.target.get()

        self.number.config(text=str(count))

        percent = min(100, count / target * 100)
        self.percentage.config(text=f"{percent:.0f}%")

        self.progress.delete("all")
        self.progress.create_rectangle(
            0, 0, int(360 * percent / 100), 15,
            fill=GOLD, outline=""
        )

        self.status.config(
            text="اكتمل الهدف! بارك الله فيك"
            if count >= target
            else f"باقي {target - count} للوصول إلى {target}"
        )


if __name__ == "__main__":
    window = tk.Tk()
    TasbeehApp(window)
    window.mainloop()
