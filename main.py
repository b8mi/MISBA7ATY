
import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

BG, PANEL, GOLD = "#10211d", "#21443a", "#e9c575"
MUTED = "#a9c8bc"

SAVE_FILE = Path.home() / ".tasbeeh_counts.json"
HISTORY_LIMIT = 1000
DEFAULT_GOAL = 33

PHRASES = ["سُبْحَانَ اللَّهِ", "الْحَمْدُ لِلَّهِ", "اللَّهُ أَكْبَرُ",
           "أَسْتَغْفِرُ اللَّهَ", "لَا إِلَهَ إِلَّا اللَّهُ"]


class TasbeehApp:
    def __init__(self, root):
        self.root = root

        self.saved_data = self.load_data()
        self.counts = self.load_counts()
        self.goals = self.load_goals()

        self.undo_history = {phrase: [] for phrase in PHRASES}
        self.redo_history = {phrase: [] for phrase in PHRASES}

        self.phrase = tk.StringVar(value=PHRASES[0])
        self.target = tk.IntVar(value=self.goals[PHRASES[0]])

        self.configure_window()
        self.build_header()
        self.build_counter()
        self.build_goal_controls()
        self.build_progress()
        self.build_buttons()
        self.build_footer()
        self.bind_shortcuts()
        self.refresh()

    def configure_window(self):
        self.root.title("مسبحتي | عداد التسبيح")
        self.root.geometry("480x560")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

    def label(self, parent, text="", size=11, color="white", bold=False):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=("Tahoma", size, "bold" if bold else "normal"))

    def button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command, relief="flat",
                         bg=GOLD if primary else PANEL, fg=BG if primary else "white",
                         font=("Tahoma", 13 if primary else 10, "bold"),
                         disabledforeground=MUTED, padx=12, pady=5)

    def build_header(self):
        self.label(self.root, "مِسْبَحَتِي", 24, GOLD, True).pack(pady=(16, 10))

        menu = tk.OptionMenu(self.root, self.phrase, *PHRASES, command=self.switch_phrase)

        menu.config(bg=PANEL, fg="white", activebackground=PANEL,
                    activeforeground=GOLD, highlightthickness=0)

        menu["menu"].config(bg=PANEL, fg="white")
        menu.pack()

    def switch_phrase(self, phrase):
        goal = self.goals[phrase]

        self.target.set(goal)
        self.custom_goal.set(str(goal))

        self.refresh()

    def build_counter(self):
        self.number = tk.Label(self.root, text="0", bg=BG, fg=GOLD,
                               font=("Segoe UI", 68, "bold"))

        self.number.pack(pady=(6, 1))

    def build_goal_controls(self):
        controls = tk.Frame(self.root, bg=BG)
        controls.pack()

        self.label(controls, "الهدف").pack(side="right", padx=10)

        for goal in (33, 100):
            tk.Radiobutton(controls, text=str(goal), value=goal, variable=self.target,
                           command=self.select_preset, bg=BG, fg="white",
                           selectcolor=PANEL, activebackground=BG,
                           activeforeground=GOLD).pack(side="right")

        self.custom_goal = tk.StringVar(value=str(self.target.get()))

        entry = tk.Entry(controls, textvariable=self.custom_goal, width=7,
                         justify="center", bg=PANEL, fg="white", insertbackground=GOLD)

        entry.pack(side="right", padx=5)
        entry.bind("<Return>", lambda _: self.apply_custom_goal())

        self.button(controls, "تحديد", self.apply_custom_goal).pack(side="right")

    def save_current_goal(self):
        phrase = self.phrase.get()

        self.goals[phrase] = self.target.get()

        self.save_counts()
        self.refresh()

    def select_preset(self):
        self.custom_goal.set(str(self.target.get()))
        self.save_current_goal()

    def apply_custom_goal(self):
        try:
            goal = int(self.custom_goal.get())

            if goal <= 0:
                raise ValueError

        except ValueError:
            messagebox.showerror("خطأ", "أدخل عدداً صحيحاً أكبر من صفر.")
            return

        self.target.set(goal)
        self.save_current_goal()
        self.root.focus_set()

    def build_progress(self):
        self.progress = tk.Canvas(self.root, height=15, width=360,
                                  bg=PANEL, highlightthickness=0)

        self.progress.pack(pady=14)

        self.percentage = self.label(self.root, "0%", 11, GOLD, True)
        self.percentage.pack()

        self.status = self.label(self.root, color=MUTED, size=10)
        self.status.pack()

        self.cycle_label = self.label(self.root, color=GOLD, size=10)
        self.cycle_label.pack(pady=5)

    def build_buttons(self):
        buttons = tk.Frame(self.root, bg=BG)
        buttons.pack(pady=10)

        actions = [
            ("+1  تسبيحة", self.add, True),
            ("تراجع", self.undo, False),
            ("إعادة", self.redo, False),
            ("تصفير", self.reset, False)
        ]

        self.action_buttons = {}

        for text, command, primary in actions:
            button = self.button(buttons, text, command, primary)
            button.pack(side="right", padx=5)

            self.action_buttons[command.__name__] = button

    def build_footer(self):
        footer = tk.Frame(self.root, bg=PANEL, padx=12, pady=8)
        footer.pack(fill="x", padx=35, pady=(0, 8))

        self.total_label = self.label(footer, color=GOLD, bold=True)
        self.total_label.pack(side="right")

        self.button(footer, "الإحصائيات", self.open_statistics).pack(side="left")

        self.label(self.root, "المسافة للعد | Ctrl+Z للتراجع | Ctrl+Y للإعادة",
                   10, MUTED).pack()

    def bind_shortcuts(self):
        self.root.bind("<space>", self.on_space)
        self.root.bind("<Control-z>", self.on_undo)
        self.root.bind("<Control-y>", self.on_redo)

    def on_space(self, event):
        if isinstance(event.widget, (tk.Entry, tk.Button, tk.Radiobutton, tk.Menubutton)):
            return

        self.add()

        return "break"

    def on_undo(self, event):
        if isinstance(event.widget, tk.Entry):
            return

        self.undo()

        return "break"

    def on_redo(self, event):
        if isinstance(event.widget, tk.Entry):
            return

        self.redo()

        return "break"

    def load_data(self):
        try:
            data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))

            if isinstance(data, dict):
                return data

        except (OSError, ValueError):
            pass

        return {}

    def load_counts(self):
        counts = dict.fromkeys(PHRASES, 0)

        for phrase in PHRASES:
            value = self.saved_data.get(phrase, 0)

            if type(value) is int and value >= 0:
                counts[phrase] = value

        return counts

    def load_goals(self):
        goals = dict.fromkeys(PHRASES, DEFAULT_GOAL)
        stored_goals = self.saved_data.get("_goals", {})

        if not isinstance(stored_goals, dict):
            return goals

        for phrase in PHRASES:
            value = stored_goals.get(phrase, DEFAULT_GOAL)

            if type(value) is int and value > 0:
                goals[phrase] = value

        return goals

    def save_counts(self):
        temporary = SAVE_FILE.with_suffix(".tmp")

        data = self.counts.copy()
        data["_goals"] = self.goals.copy()

        try:
            content = json.dumps(data, ensure_ascii=False, indent=2)

            temporary.write_text(content, encoding="utf-8")
            temporary.replace(SAVE_FILE)

        except OSError as error:
            print(f"Could not save counts: {error}")

    def current_count(self):
        return self.counts[self.phrase.get()]

    def total_count(self):
        return sum(self.counts.values())

    def remember_count(self):
        phrase = self.phrase.get()
        history = self.undo_history[phrase]

        history.append(self.current_count())

        if len(history) > HISTORY_LIMIT:
            history.pop(0)

        self.redo_history[phrase].clear()

    def set_count(self, value, record=True):
        value = max(0, value)

        if value == self.current_count():
            return

        if record:
            self.remember_count()

        self.counts[self.phrase.get()] = value

        self.save_counts()
        self.refresh()

    def add(self):
        self.set_count(self.current_count() + 1)

    def undo(self):
        phrase = self.phrase.get()
        history = self.undo_history[phrase]

        if history:
            self.redo_history[phrase].append(self.current_count())

            previous = history.pop()
            self.set_count(previous, record=False)

        elif self.current_count() > 0:
            self.redo_history[phrase].append(self.current_count())
            self.set_count(self.current_count() - 1, record=False)

    def redo(self):
        phrase = self.phrase.get()
        history = self.redo_history[phrase]

        if not history:
            return

        undo_stack = self.undo_history[phrase]
        undo_stack.append(self.current_count())

        if len(undo_stack) > HISTORY_LIMIT:
            undo_stack.pop(0)

        next_count = history.pop()

        self.set_count(next_count, record=False)

    def reset(self):
        if self.current_count() == 0:
            return

        if messagebox.askyesno("تأكيد", "هل تريد تصفير عداد الذكر الحالي؟"):
            self.set_count(0)

    def calculate_cycles(self, count, target):
        completed, remainder = divmod(count, target)

        return completed, remainder

    def total_completed_goals(self):
        return sum(self.counts[phrase] // self.goals[phrase] for phrase in PHRASES)

    def update_history_buttons(self):
        phrase = self.phrase.get()

        can_undo = bool(self.undo_history[phrase]) or self.current_count() > 0
        can_redo = bool(self.redo_history[phrase])

        self.action_buttons["undo"].config(state=tk.NORMAL if can_undo else tk.DISABLED)
        self.action_buttons["redo"].config(state=tk.NORMAL if can_redo else tk.DISABLED)

    def open_statistics(self):
        dialog = tk.Toplevel(self.root)

        dialog.title("إحصائيات التسبيح")
        dialog.configure(bg=BG, padx=18, pady=15)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        self.label(dialog, "إجمالي التسبيح", 18, GOLD, True).pack(pady=(0, 10))

        total = self.total_count()
        highest = max(self.counts.values())

        for phrase in PHRASES:
            self.build_statistics_row(dialog, phrase, total, highest)

        self.label(dialog, f"المجموع: {total}", 14, GOLD, True).pack(pady=(12, 3))

        completed = self.total_completed_goals()

        self.label(dialog, f"إجمالي الأهداف المكتملة: {completed}",
                   11, MUTED).pack(pady=(0, 10))

        self.button(dialog, "إغلاق", dialog.destroy).pack()

    def build_statistics_row(self, parent, phrase, total, highest):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=4)

        count = self.counts[phrase]
        goal = self.goals[phrase]

        share = count / total * 100 if total else 0

        self.label(row, phrase, 12).pack(side="right")
        self.label(row, f"{count} ({share:.1f}%)", 10, MUTED).pack(side="left")

        bar = tk.Canvas(parent, width=340, height=8, bg=PANEL, highlightthickness=0)
        bar.pack()

        width = 340 * count / highest if highest else 0

        bar.create_rectangle(0, 0, width, 8, fill=GOLD, outline="")

        completed = count // goal

        self.label(parent, f"الهدف: {goal} | الأهداف المكتملة: {completed}",
                   9, MUTED).pack(anchor="e", pady=(2, 5))

    def refresh_progress(self, count, target):
        ratio = min(1, count / target)

        self.percentage.config(text=f"{ratio:.0%}")

        self.progress.delete("all")
        self.progress.create_rectangle(0, 0, 360 * ratio, 15, fill=GOLD, outline="")

        if count >= target:
            status = "اكتمل الهدف! بارك الله فيك"

        else:
            status = f"باقي {target - count} للوصول إلى {target}"

        self.status.config(text=status)

    def refresh_cycles(self, count, target):
        completed, remainder = self.calculate_cycles(count, target)

        if completed == 0:
            text = f"الأهداف المكتملة: {completed}"

        else:
            remaining = target - remainder
            text = f"الأهداف المكتملة: {completed} | باقي للهدف التالي: {remaining}"

        self.cycle_label.config(text=text)

    def refresh(self):
        count = self.current_count()
        target = self.target.get()

        self.number.config(text=str(count))

        self.refresh_progress(count, target)
        self.refresh_cycles(count, target)
        self.update_history_buttons()

        self.total_label.config(text=f"المجموع: {self.total_count()}")


if __name__ == "__main__":
    window = tk.Tk()

    TasbeehApp(window)

    window.mainloop()
