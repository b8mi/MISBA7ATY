import json
import tkinter as tk
from pathlib import Path
from datetime import date
from tkinter import ttk, messagebox, simpledialog

BG = "#10211d"
PANEL = "#21443a"
GOLD = "#e9c575"
WHITE = "#ffffff"

SAVE_FILE = Path.home() / ".tasbeeh_custom_counts.json"
DEFAULT_GOAL = 33

PHRASES = [
    "سُبْحَانَ اللَّهِ",
    "الْحَمْدُ لِلَّهِ",
    "اللَّهُ أَكْبَرُ",
    "أَسْتَغْفِرُ اللَّهَ",
    "لَا إِلَهَ إِلَّا اللَّهُ"
]


class TasbeehApp:
    def __init__(self, root):
        self.root = root
        self.root.title("مسبحتي")
        self.root.geometry("420x680")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.data = self.load_data()
        self.phrases = list(dict.fromkeys(PHRASES + self.data.get("phrases", [])))
        self.counts = self.data.get("counts", {})
        self.goals = self.data.get("goals", {})
        self.daily = self.data.get("daily", {})

        self.undo_history = {}
        self.redo_history = {}

        for phrase in self.phrases:
            self.initialize_phrase(phrase)

        selected = self.data.get("selected", self.phrases[0])

        if selected not in self.phrases:
            selected = self.phrases[0]

        self.phrase = tk.StringVar(value=selected)

        self.build_interface()
        self.bind_keys()
        self.refresh()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def initialize_phrase(self, phrase):
        self.counts.setdefault(phrase, 0)
        self.goals.setdefault(phrase, DEFAULT_GOAL)
        self.undo_history.setdefault(phrase, [])
        self.redo_history.setdefault(phrase, [])

    def load_data(self):
        try:
            data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_data(self):
        data = {
            "phrases": self.phrases,
            "counts": self.counts,
            "goals": self.goals,
            "daily": self.daily,
            "selected": self.phrase.get()
        }

        temp = SAVE_FILE.with_suffix(".tmp")

        try:
            temp.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
            temp.replace(SAVE_FILE)
        except OSError as error:
            messagebox.showerror("خطأ في الحفظ", str(error))

    def label(self, parent, text, size=12, color=WHITE, bold=False):
        weight = "bold" if bold else "normal"
        return tk.Label(parent, text=text, font=("Arial", size, weight), bg=parent.cget("bg"), fg=color)

    def button(self, parent, text, command, size=12):
        return tk.Button(parent, text=text, command=command, font=("Arial", size, "bold"), bg=PANEL, fg=WHITE, activebackground=GOLD, activeforeground=BG, relief="flat", cursor="hand2", padx=12, pady=8)

    def build_interface(self):
        self.label(self.root, "مِسْبَحَتِي", 28, GOLD, True).pack(pady=(18, 12))

        self.build_phrase_selector()
        self.build_counter()
        self.build_goal_controls()
        self.build_actions()
        self.build_statistics()

    def build_phrase_selector(self):
        self.menu = tk.OptionMenu(self.root, self.phrase, *self.phrases, command=self.switch_phrase)

        self.menu.config(bg=PANEL, fg=WHITE, font=("Arial", 16), highlightthickness=0, width=24)
        self.menu["menu"].config(bg=PANEL, fg=WHITE, font=("Arial", 14))
        self.menu.pack(pady=5)

        self.button(self.root, "+ إضافة ذكر", self.add_custom_phrase).pack(pady=5)

    def build_counter(self):
        self.counter = self.label(self.root, "0", 58, GOLD, True)
        self.counter.pack(pady=(12, 0))

        self.goal_label = self.label(self.root, "", 14)
        self.goal_label.pack()

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Tasbeeh.Horizontal.TProgressbar", troughcolor=PANEL, background=GOLD, borderwidth=0, lightcolor=GOLD, darkcolor=GOLD)

        self.progress = ttk.Progressbar(self.root, length=330, maximum=100, style="Tasbeeh.Horizontal.TProgressbar")
        self.progress.pack(pady=12)

        self.progress_label = self.label(self.root, "", 12, GOLD)
        self.progress_label.pack()

        self.count_button = tk.Button(self.root, text="سَبِّحْ", command=self.increment, font=("Arial", 24, "bold"), bg=GOLD, fg=BG, activebackground="#f5dca0", relief="flat", cursor="hand2", width=14, height=2)
        self.count_button.pack(pady=15)

    def build_goal_controls(self):
        frame = tk.Frame(self.root, bg=BG)
        frame.pack(pady=5)

        self.button(frame, "33", lambda: self.set_goal(33)).pack(side="left", padx=4)
        self.button(frame, "100", lambda: self.set_goal(100)).pack(side="left", padx=4)
        self.button(frame, "هدف مخصص", self.custom_goal).pack(side="left", padx=4)

    def build_actions(self):
        frame = tk.Frame(self.root, bg=BG)
        frame.pack(pady=10)

        self.button(frame, "تراجع", self.undo).pack(side="left", padx=4)
        self.button(frame, "إعادة", self.redo).pack(side="left", padx=4)
        self.button(frame, "تصفير", self.reset).pack(side="left", padx=4)

    def build_statistics(self):
        frame = tk.Frame(self.root, bg=PANEL, padx=15, pady=10)
        frame.pack(fill="x", padx=25, pady=10)

        self.today_label = self.label(frame, "", 12)
        self.today_label.pack()

        self.total_label = self.label(frame, "", 12, GOLD)
        self.total_label.pack(pady=5)

        self.label(self.root, "Space: +1   |   Ctrl+Z: Undo   |   Ctrl+Y: Redo", 9, GOLD).pack(pady=4)

    def bind_keys(self):
        self.root.bind("<space>", self.keyboard_increment)
        self.root.bind("<Control-z>", lambda event: self.undo())
        self.root.bind("<Control-y>", lambda event: self.redo())

    def keyboard_increment(self, event):
        self.increment()
        return "break"

    def add_custom_phrase(self):
        phrase = simpledialog.askstring("إضافة ذكر", "أدخل الذكر الجديد:", parent=self.root)

        if phrase is None:
            return

        phrase = phrase.strip()

        if not phrase:
            return

        if phrase in self.phrases:
            self.select_phrase(phrase)
            return

        self.phrases.append(phrase)
        self.initialize_phrase(phrase)

        self.menu["menu"].add_command(label=phrase, command=lambda p=phrase: self.select_phrase(p))

        self.select_phrase(phrase)

    def select_phrase(self, phrase):
        self.phrase.set(phrase)
        self.switch_phrase(phrase)

    def switch_phrase(self, phrase=None):
        self.refresh()
        self.save_data()

    def custom_goal(self):
        goal = simpledialog.askinteger("هدف مخصص", "أدخل عدد التسبيحات:", parent=self.root, minvalue=1, maxvalue=1000000)

        if goal is not None:
            self.set_goal(goal)

    def set_goal(self, goal):
        phrase = self.phrase.get()
        self.goals[phrase] = goal

        self.refresh()
        self.save_data()

    def update_daily(self, phrase, amount, day):
        records = self.daily.setdefault(day, {})
        records[phrase] = max(0, records.get(phrase, 0) + amount)

    def change_count(self, new_count, daily_delta=0):
        phrase = self.phrase.get()
        previous = self.counts[phrase]
        new_count = max(0, new_count)
        day = date.today().isoformat()

        if previous == new_count:
            return

        action = (previous, new_count, daily_delta, day)

        self.undo_history[phrase].append(action)
        self.redo_history[phrase].clear()

        self.counts[phrase] = new_count
        self.update_daily(phrase, daily_delta, day)

        self.refresh()
        self.save_data()

    def increment(self):
        phrase = self.phrase.get()
        previous = self.counts[phrase]

        self.change_count(previous + 1, 1)

        if previous + 1 == self.goals[phrase]:
            self.root.bell()

    def undo(self):
        phrase = self.phrase.get()

        if not self.undo_history[phrase]:
            return

        action = self.undo_history[phrase].pop()
        previous, current, delta, day = action

        self.redo_history[phrase].append(action)
        self.counts[phrase] = previous
        self.update_daily(phrase, -delta, day)

        self.refresh()
        self.save_data()

    def redo(self):
        phrase = self.phrase.get()

        if not self.redo_history[phrase]:
            return

        action = self.redo_history[phrase].pop()
        previous, current, delta, day = action

        self.undo_history[phrase].append(action)
        self.counts[phrase] = current
        self.update_daily(phrase, delta, day)

        self.refresh()
        self.save_data()

    def reset(self):
        phrase = self.phrase.get()

        if self.counts[phrase] == 0:
            return

        confirmed = messagebox.askyesno("تأكيد", "هل تريد تصفير العداد؟")

        if confirmed:
            self.change_count(0)

    def refresh(self):
        phrase = self.phrase.get()
        count = self.counts[phrase]
        goal = self.goals[phrase]

        percentage = count / goal * 100
        remaining = max(0, goal - count)

        self.counter.config(text=f"{count:,}")
        self.goal_label.config(text=f"الهدف: {goal:,}")
        self.progress["value"] = min(100, percentage)

        if count >= goal:
            self.progress_label.config(text=f"{percentage:.1f}% — تم تحقيق الهدف!")
        else:
            self.progress_label.config(text=f"{percentage:.1f}% — المتبقي: {remaining:,}")

        today = date.today().isoformat()
        today_count = sum(self.daily.get(today, {}).values())
        total_count = sum(sum(records.values()) for records in self.daily.values())

        self.today_label.config(text=f"تسبيحات اليوم: {today_count:,}")
        self.total_label.config(text=f"إجمالي التسبيحات: {total_count:,}")

    def close(self):
        self.save_data()
        self.root.destroy()


def main():
    root = tk.Tk()
    TasbeehApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
