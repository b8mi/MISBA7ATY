import json
import tkinter as tk
from pathlib import Path
from datetime import date, timedelta
from tkinter import messagebox

BG, PANEL, GOLD = "#10211d", "#21443a", "#e9c575"
MUTED = "#a9c8bc"

SAVE_FILE = Path.home() / ".tasbeeh_counts.json"
HISTORY_LIMIT = 1000
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
        self.saved_data = self.load_data()
        self.counts = self.load_counts()
        self.goals = self.load_goals()
        self.daily = self.load_daily()

        self.undo_history = {p: [] for p in PHRASES}
        self.redo_history = {p: [] for p in PHRASES}

        self.phrase = tk.StringVar(value=PHRASES[0])
        self.target = tk.IntVar(value=self.goals[PHRASES[0]])
        self.custom_goal = tk.StringVar(value=str(self.target.get()))

        self.configure_window()
        self.build_header()
        self.build_counter()
        self.build_goal_controls()
        self.build_progress()
        self.build_buttons()
        self.build_footer()
        self.bind_shortcuts()
        self.refresh()

        self.last_day = self.today()
        self.root.after(30000, self.check_date)

    def configure_window(self):
        self.root.title("مسبحتي | عداد التسبيح")
        self.root.geometry("480x620")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

    def label(self, parent, text="", size=11, color="white", bold=False):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=("Tahoma", size, "bold" if bold else "normal"))

    def button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command, relief="flat",
                         bg=GOLD if primary else PANEL,
                         fg=BG if primary else "white",
                         disabledforeground=MUTED,
                         font=("Tahoma", 12 if primary else 10, "bold"),
                         padx=10, pady=6)

    def today(self):
        return date.today().isoformat()

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
        stored = self.saved_data.get("_goals", {})

        if isinstance(stored, dict):
            for phrase in PHRASES:
                value = stored.get(phrase, DEFAULT_GOAL)

                if type(value) is int and value > 0:
                    goals[phrase] = value

        return goals

    def load_daily(self):
        stored = self.saved_data.get("_daily", {})
        daily = {}

        if not isinstance(stored, dict):
            return daily

        for day, counts in stored.items():
            try:
                if date.fromisoformat(day).isoformat() != day:
                    continue
            except (ValueError, TypeError):
                continue

            if not isinstance(counts, dict):
                continue

            daily[day] = dict.fromkeys(PHRASES, 0)

            for phrase in PHRASES:
                value = counts.get(phrase, 0)

                if type(value) is int and value >= 0:
                    daily[day][phrase] = value

        return daily

    def save_counts(self):
        data = self.counts.copy()
        data["_goals"] = self.goals.copy()
        data["_daily"] = self.daily

        temporary = SAVE_FILE.with_suffix(".tmp")

        try:
            temporary.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            temporary.replace(SAVE_FILE)

        except OSError as error:
            print(f"Could not save data: {error}")

    def build_header(self):
        self.label(self.root, "مِسْبَحَتِي", 24, GOLD, True).pack(pady=(16, 10))

        menu = tk.OptionMenu(self.root, self.phrase, *PHRASES,
                             command=self.switch_phrase)

        menu.config(bg=PANEL, fg="white", activebackground=PANEL,
                    activeforeground=GOLD, highlightthickness=0)

        menu["menu"].config(bg=PANEL, fg="white")
        menu.pack()

    def switch_phrase(self, phrase):
        self.target.set(self.goals[phrase])
        self.custom_goal.set(str(self.goals[phrase]))
        self.refresh()

    def build_counter(self):
        self.number = self.label(self.root, "0", 65, GOLD, True)
        self.number.pack(pady=(6, 1))

    def build_goal_controls(self):
        frame = tk.Frame(self.root, bg=BG)
        frame.pack()

        self.label(frame, "الهدف").pack(side="right", padx=10)

        for goal in (33, 100):
            tk.Radiobutton(frame, text=str(goal), value=goal,
                           variable=self.target, command=self.select_preset,
                           bg=BG, fg="white", selectcolor=PANEL,
                           activebackground=BG,
                           activeforeground=GOLD).pack(side="right")

        entry = tk.Entry(frame, textvariable=self.custom_goal, width=7,
                         justify="center", bg=PANEL, fg="white",
                         insertbackground=GOLD)

        entry.pack(side="right", padx=5)
        entry.bind("<Return>", lambda _: self.apply_custom_goal())

        self.button(frame, "تحديد", self.apply_custom_goal).pack(side="right")

    def select_preset(self):
        self.custom_goal.set(str(self.target.get()))
        self.save_goal()

    def apply_custom_goal(self):
        try:
            goal = int(self.custom_goal.get())

            if goal <= 0:
                raise ValueError

        except ValueError:
            messagebox.showerror("خطأ", "أدخل عدداً صحيحاً أكبر من صفر.")
            return

        self.target.set(goal)
        self.save_goal()
        self.root.focus_set()

    def save_goal(self):
        self.goals[self.phrase.get()] = self.target.get()
        self.save_counts()
        self.refresh()

    def build_progress(self):
        self.progress = tk.Canvas(self.root, height=15, width=360,
                                  bg=PANEL, highlightthickness=0)
        self.progress.pack(pady=14)

        self.percentage = self.label(self.root, "0%", 11, GOLD, True)
        self.percentage.pack()

        self.status = self.label(self.root, color=MUTED)
        self.status.pack()

        self.cycle_label = self.label(self.root, color=GOLD)
        self.cycle_label.pack(pady=5)

    def build_buttons(self):
        frame = tk.Frame(self.root, bg=BG)
        frame.pack(pady=10)

        self.button(frame, "+1 تسبيحة", self.add, True).pack(side="right", padx=4)

        self.undo_button = self.button(frame, "تراجع", self.undo)
        self.undo_button.pack(side="right", padx=4)

        self.redo_button = self.button(frame, "إعادة", self.redo)
        self.redo_button.pack(side="right", padx=4)

        self.button(frame, "تصفير", self.reset).pack(side="right", padx=4)

    def build_footer(self):
        footer = tk.Frame(self.root, bg=PANEL, padx=12, pady=10)
        footer.pack(fill="x", padx=30, pady=5)

        self.total_label = self.label(footer, color=GOLD, bold=True)
        self.total_label.pack()

        self.daily_label = self.label(footer, color="white")
        self.daily_label.pack(pady=4)

        self.streak_label = self.label(footer, color=GOLD)
        self.streak_label.pack()

        buttons = tk.Frame(footer, bg=PANEL)
        buttons.pack(pady=8)

        self.button(buttons, "إحصائيات اليوم", self.open_daily).pack(side="right", padx=4)
        self.button(buttons, "الإحصائيات العامة", self.open_statistics).pack(side="right", padx=4)

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
        if not isinstance(event.widget, tk.Entry):
            self.undo()
            return "break"

    def on_redo(self, event):
        if not isinstance(event.widget, tk.Entry):
            self.redo()
            return "break"

    def update_daily(self, day, phrase, amount):
        if day not in self.daily:
            self.daily[day] = dict.fromkeys(PHRASES, 0)

        current = self.daily[day][phrase]
        self.daily[day][phrase] = max(0, current + amount)

    def daily_total(self, day=None):
        day = day or self.today()
        return sum(self.daily.get(day, {}).values())

    def active_days(self):
        return {
            date.fromisoformat(day)
            for day, counts in self.daily.items()
            if sum(counts.values()) > 0
        }

    def current_streak(self):
        days = self.active_days()
        current = date.today()

        if current not in days:
            current -= timedelta(days=1)

        streak = 0

        while current in days:
            streak += 1
            current -= timedelta(days=1)

        return streak

    def longest_streak(self):
        days = sorted(self.active_days())
        longest = 0
        current = 0
        previous = None

        for day in days:
            if previous is not None and day - previous == timedelta(days=1):
                current += 1
            else:
                current = 1

            longest = max(longest, current)
            previous = day

        return longest

    def check_date(self):
        if self.last_day != self.today():
            self.last_day = self.today()
            self.refresh()

        self.root.after(30000, self.check_date)

    def current_count(self):
        return self.counts[self.phrase.get()]

    def total_count(self):
        return sum(self.counts.values())

    def total_completed_goals(self):
        return sum(self.counts[p] // self.goals[p] for p in PHRASES)

    def perform_action(self, new_count, daily_delta=0):
        phrase = self.phrase.get()
        old_count = self.counts[phrase]
        day = self.today()

        action = (old_count, new_count, day, daily_delta)

        self.undo_history[phrase].append(action)
        self.undo_history[phrase] = self.undo_history[phrase][-HISTORY_LIMIT:]
        self.redo_history[phrase].clear()

        self.counts[phrase] = new_count

        if daily_delta:
            self.update_daily(day, phrase, daily_delta)

        self.save_counts()
        self.refresh()

    def add(self):
        self.perform_action(self.current_count() + 1, daily_delta=1)

    def undo(self):
        phrase = self.phrase.get()
        history = self.undo_history[phrase]

        if history:
            action = history.pop()
        elif self.current_count() > 0:
            count = self.current_count()
            day = self.today()
            daily_count = self.daily.get(day, {}).get(phrase, 0)

            action = (count - 1, count, day, int(daily_count > 0))
        else:
            return

        old_count, new_count, day, delta = action

        self.counts[phrase] = old_count

        if delta:
            self.update_daily(day, phrase, -delta)

        self.redo_history[phrase].append(action)

        self.save_counts()
        self.refresh()

    def redo(self):
        phrase = self.phrase.get()

        if not self.redo_history[phrase]:
            return

        action = self.redo_history[phrase].pop()
        old_count, new_count, day, delta = action

        self.counts[phrase] = new_count

        if delta:
            self.update_daily(day, phrase, delta)

        self.undo_history[phrase].append(action)
        self.save_counts()
        self.refresh()

    def reset(self):
        if self.current_count() and messagebox.askyesno(
            "تأكيد", "هل تريد تصفير عداد الذكر الحالي؟"
        ):
            self.perform_action(0)

    def open_statistics(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("الإحصائيات العامة")
        dialog.configure(bg=BG, padx=18, pady=15)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        self.label(dialog, "إجمالي التسبيح", 18, GOLD, True).pack(pady=10)

        total = self.total_count()
        highest = max(self.counts.values())

        for phrase in PHRASES:
            row = tk.Frame(dialog, bg=BG)
            row.pack(fill="x", pady=5)

            count = self.counts[phrase]
            share = count / total * 100 if total else 0

            self.label(row, phrase).pack(side="right")
            self.label(row, f"{count} ({share:.1f}%)", 10, GOLD).pack(side="left")

            bar = tk.Canvas(dialog, width=340, height=8,
                            bg=PANEL, highlightthickness=0)
            bar.pack()

            width = 340 * count / highest if highest else 0
            bar.create_rectangle(0, 0, width, 8, fill=GOLD, outline="")

            completed = count // self.goals[phrase]

            self.label(dialog, f"الهدف: {self.goals[phrase]} | المكتمل: {completed}",
                       9, MUTED).pack(anchor="e")

        self.label(dialog, f"المجموع: {total}", 14, GOLD, True).pack(pady=10)
        self.label(dialog, f"الأهداف المكتملة: {self.total_completed_goals()}").pack()
        self.button(dialog, "إغلاق", dialog.destroy).pack(pady=10)

    def open_daily(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("إحصائيات التسبيح اليومية")
        dialog.configure(bg=BG, padx=20, pady=15)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        self.label(dialog, "الإحصائيات اليومية", 20, GOLD, True).pack(pady=10)

        dates = sorted(set(self.daily) | {self.today()}, reverse=True)
        selected = tk.StringVar(value=self.today())

        results = tk.Frame(dialog, bg=BG)
        total_label = self.label(dialog, color=GOLD, size=14, bold=True)

        def display_day(*args):
            for widget in results.winfo_children():
                widget.destroy()

            day = selected.get()
            counts = self.daily.get(day, {})
            highest = max(counts.values(), default=0)

            for phrase in PHRASES:
                count = counts.get(phrase, 0)

                row = tk.Frame(results, bg=BG)
                row.pack(fill="x", pady=6)

                self.label(row, phrase, 11).pack(side="right", padx=8)
                self.label(row, str(count), 12, GOLD, True).pack(side="left")

                bar = tk.Canvas(results, width=340, height=7,
                                bg=PANEL, highlightthickness=0)

                bar.pack()

                width = 340 * count / highest if highest else 0
                bar.create_rectangle(0, 0, width, 7, fill=GOLD, outline="")

            total_label.config(text=f"مجموع اليوم المحدد: {self.daily_total(day)}")

        menu = tk.OptionMenu(dialog, selected, *dates, command=display_day)
        menu.config(bg=PANEL, fg="white", highlightthickness=0)
        menu["menu"].config(bg=PANEL, fg="white")
        menu.pack(pady=5)

        results.pack(fill="x", pady=10)
        total_label.pack(pady=5)

        self.label(dialog, f"الاستمرار الحالي: {self.current_streak()} يوم",
                   11, GOLD).pack()

        self.label(dialog, f"أطول فترة استمرار: {self.longest_streak()} يوم",
                   11, MUTED).pack(pady=5)

        self.button(dialog, "إغلاق", dialog.destroy).pack(pady=10)
        display_day()

    def refresh(self):
        phrase = self.phrase.get()
        count = self.current_count()
        goal = self.target.get()

        ratio = min(count / goal, 1)
        completed, remainder = divmod(count, goal)

        self.number.config(text=str(count))
        self.progress.delete("all")
        self.progress.create_rectangle(0, 0, 360 * ratio, 15, fill=GOLD, outline="")
        self.percentage.config(text=f"{ratio:.0%}")

        if count >= goal:
            self.status.config(text="اكتمل الهدف! بارك الله فيك")
        else:
            self.status.config(text=f"باقي {goal - count} للوصول إلى الهدف")

        self.cycle_label.config(
            text=f"الأهداف المكتملة: {completed} | باقي للهدف التالي: {goal - remainder}"
        )

        self.total_label.config(text=f"المجموع: {self.total_count()}")

        self.daily_label.config(text=f"تسبيحات اليوم: {self.daily_total()}")

        self.streak_label.config(
            text=f"الاستمرار: {self.current_streak()} يوم | الأفضل: {self.longest_streak()}"
        )

        can_undo = self.undo_history[phrase] or count > 0
        can_redo = self.redo_history[phrase]

        self.undo_button.config(state=tk.NORMAL if can_undo else tk.DISABLED)
        self.redo_button.config(state=tk.NORMAL if can_redo else tk.DISABLED)


if __name__ == "__main__":
    window = tk.Tk()
    TasbeehApp(window)
    window.mainloop()
