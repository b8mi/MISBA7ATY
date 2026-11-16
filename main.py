
import tkinter as tk
from tkinter import messagebox

BG, PANEL, GOLD = "#10211d", "#21443a", "#e9c575"
PHRASES = ["سُبْحَانَ اللَّهِ", "الْحَمْدُ لِلَّهِ", "اللَّهُ أَكْبَرُ",
           "أَسْتَغْفِرُ اللَّهَ", "لَا إِلَهَ إِلَّا اللَّهُ"]


class TasbeehApp:
    def __init__(self, root):
        self.root = root
        root.title("مسبحتي | عداد التسبيح")
        root.geometry("480x480")
        root.configure(bg=BG)
        root.resizable(False, False)
        tk.Label(root, text="مِسْبَحَتِي", bg=BG, fg=GOLD,
                 font=("Tahoma", 24, "bold")).pack(pady=(16, 10))
        self.phrase = tk.StringVar(value=PHRASES[0])
        tk.OptionMenu(root, self.phrase, *PHRASES, command=lambda _: self.refresh()).pack()
        self.number = tk.Label(root, text="0", bg=BG, fg=GOLD, font=("Segoe UI", 68, "bold"))
        self.number.pack(pady=(6, 1))
        self.target = tk.IntVar(value=33)
        controls = tk.Frame(root, bg=BG)
        controls.pack()
        tk.Label(controls, text="الهدف", bg=BG, fg="white", font=("Tahoma", 11)).pack(side="right", padx=10)
        tk.Radiobutton(controls, text="33", value=33, variable=self.target,
                       command=self.refresh, bg=BG, fg="white", selectcolor=PANEL,
                       activebackground=BG).pack(side="right")
        tk.Radiobutton(controls, text="100", value=100, variable=self.target,
                       command=self.refresh, bg=BG, fg="white", selectcolor=PANEL,
                       activebackground=BG).pack(side="right")
        self.progress = tk.Canvas(root, height=15, width=360, bg=PANEL, highlightthickness=0)
        self.progress.pack(pady=14)
        self.status = tk.Label(root, text="", bg=BG, fg="#a9c8bc", font=("Tahoma", 10))
        self.status.pack()
        buttons = tk.Frame(root, bg=BG)
        buttons.pack(pady=10)
        tk.Button(buttons, text="+1  تسبيحة", command=self.add,
                  bg=GOLD, relief="flat", font=("Tahoma", 13, "bold"), padx=14, pady=6).pack(side="right", padx=5)
        tk.Button(buttons, text="تراجع", command=self.undo, bg=PANEL, fg="white",
                  font=("Tahoma", 10), relief="flat").pack(side="right", padx=5)
        tk.Button(buttons, text="تصفير", command=self.reset, bg=PANEL, fg="white",
                  font=("Tahoma", 10), relief="flat").pack(side="right", padx=5)
        tk.Label(root, text="يمكنك الضغط على زر المسافة للعد", bg=BG, fg="#a9c8bc",
                 font=("Tahoma", 10)).pack()
        self.counts = {phrase: 0 for phrase in PHRASES}
        root.bind("<space>", lambda _: self.add())
        self.refresh()

    def add(self):
        self.counts[self.phrase.get()] += 1
        self.refresh()

    def undo(self):
        phrase = self.phrase.get()
        self.counts[phrase] = max(0, self.counts[phrase] - 1)
        self.refresh()

    def reset(self):
        if messagebox.askyesno("تأكيد", "هل تريد تصفير عداد الذكر الحالي؟"):
            self.counts[self.phrase.get()] = 0
            self.refresh()

    def refresh(self):
        count = self.counts.get(self.phrase.get(), 0)
        target = self.target.get()
        self.number.config(text=str(count))
        self.progress.delete("all")
        self.progress.create_rectangle(0, 0, int(360 * min(1, count / target)), 15,
                                       fill=GOLD, outline="")
        self.status.config(text="اكتمل الهدف! بارك الله فيك" if count >= target
                           else f"باقي {target - count} للوصول إلى {target}")


if __name__ == "__main__":
    window = tk.Tk()
    TasbeehApp(window)
    window.mainloop()
