

from __future__ import annotations
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import dataclass
from typing import Optional, Iterable
import csv

FILENAME = "students.txt"

# ---------------- Linked List Model ----------------
@dataclass
class Student:
    roll_no: int
    name: str
    marks: float
    next: Optional["Student"] = None


class StudentList:
    def __init__(self) -> None:
        self.head: Optional[Student] = None

    def add(self, roll: int, name: str, marks: float) -> None:
        new_node = Student(roll_no=roll, name=name, marks=marks)
        if self.head is None:
            self.head = new_node
            return
        temp = self.head
        while temp.next:
            temp = temp.next
        temp.next = new_node

    def __iter__(self) -> Iterable[Student]:
        temp = self.head
        while temp:
            yield temp
            temp = temp.next

    def to_list(self) -> list[tuple[int, str, float]]:
        return [(n.roll_no, n.name, n.marks) for n in self]

    def find(self, roll: int) -> Optional[Student]:
        temp = self.head
        while temp:
            if temp.roll_no == roll:
                return temp
            temp = temp.next
        return None

    def delete(self, roll: int) -> bool:
        if not self.head:
            return False
        if self.head.roll_no == roll:
            self.head = self.head.next
            return True
        prev = self.head
        curr = self.head.next
        while curr and curr.roll_no != roll:
            prev = curr
            curr = curr.next
        if not curr:
            return False
        prev.next = curr.next
        return True

    def clear(self) -> None:
        self.head = None

    def save(self, filename: str = FILENAME) -> None:
        with open(filename, "w", encoding="utf-8") as f:
            for r, n, m in self.to_list():
                f.write(f"{r} {n} {m}\n")

    def load(self, filename: str = FILENAME) -> None:
        self.clear()
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 3:
                        continue
                    try:
                        roll = int(parts[0])
                        name = parts[1]
                        marks = float(parts[2])
                    except ValueError:
                        continue
                    self.add(roll, name, marks)
        except FileNotFoundError:
            pass


# ---------------- Tkinter UI ----------------
class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Student Record Management")
        self.geometry("820x520")
        self.minsize(720, 460)

        style = ttk.Style(self)
        style.configure("Treeview.Heading", font=(None, 11, "bold"))
        style.configure("TButton", padding=6)

        self.model = StudentList()
        self.model.load()

        self._build_ui()
        self._refresh_table()
        self.editing_roll: Optional[int] = None

        # Keyboard shortcuts
        self.bind('<Control-s>', lambda e: self.on_save())
        self.bind('<Control-r>', lambda e: self.on_reload())
        self.bind('<Escape>', lambda e: self._clear_inputs())

    # ---------- UI Construction ----------
    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.X)

        self.roll_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.marks_var = tk.StringVar()
        self.filter_var = tk.StringVar()

        ttk.Label(top, text="Roll No:").grid(row=0, column=0, sticky=tk.W)
        self.roll_entry = ttk.Entry(top, textvariable=self.roll_var, width=12)
        self.roll_entry.grid(row=1, column=0, padx=(0, 12))

        ttk.Label(top, text="Name (no spaces):").grid(row=0, column=1, sticky=tk.W)
        self.name_entry = ttk.Entry(top, textvariable=self.name_var, width=24)
        self.name_entry.grid(row=1, column=1, padx=(0, 12))

        ttk.Label(top, text="Marks:").grid(row=0, column=2, sticky=tk.W)
        self.marks_entry = ttk.Entry(top, textvariable=self.marks_var, width=12)
        self.marks_entry.grid(row=1, column=2, padx=(0, 12))

        self.add_btn = ttk.Button(top, text="Add", command=self.on_add)
        self.add_btn.grid(row=1, column=3, padx=6)
        ttk.Button(top, text="Delete", command=self.on_delete).grid(row=1, column=4, padx=6)
        ttk.Button(top, text="Clear", command=self._clear_inputs).grid(row=1, column=5, padx=6)
        ttk.Button(top, text="Save", command=self.on_save).grid(row=1, column=6, padx=6)
        ttk.Button(top, text="Reload", command=self.on_reload).grid(row=1, column=7, padx=6)

        ttk.Label(top, text="Filter:").grid(row=0, column=8, sticky=tk.W, padx=(20,0))
        fentry = ttk.Entry(top, textvariable=self.filter_var, width=20)
        fentry.grid(row=1, column=8, padx=(0,6))
        fentry.bind('<KeyRelease>', lambda e: self._refresh_table())

        ttk.Button(top, text="Export CSV", command=self.on_export_csv).grid(row=1, column=9, padx=6)

        container = ttk.Frame(self, padding=(10, 0, 10, 10))
        container.pack(expand=True, fill=tk.BOTH)

        columns = ("roll", "name", "marks")
        self.tree = ttk.Treeview(container, columns=columns, show="headings")
        self.tree.heading("roll", text="Roll No")
        self.tree.heading("name", text="Name")
        self.tree.heading("marks", text="Marks")
        self.tree.column("roll", width=100, anchor=tk.CENTER)
        self.tree.column("name", width=360)
        self.tree.column("marks", width=120, anchor=tk.E)

        vsb = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<Button-3>', self._on_right_click)

        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Edit", command=self._ctx_edit)
        self.menu.add_command(label="Delete", command=self._ctx_delete)

        self.status = ttk.Label(self, text="Ready", anchor=tk.W)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

    # ---------- Functional Methods ----------
    def _refresh_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        filter_txt = self.filter_var.get().lower()
        for roll, name, marks in self.model.to_list():
            if (filter_txt in str(roll).lower() or
                filter_txt in name.lower() or
                filter_txt in str(marks).lower()):
                self.tree.insert("", tk.END, values=(roll, name, marks))
        self.status.config(text="Records loaded.")

    def _clear_inputs(self):
        self.roll_var.set("")
        self.name_var.set("")
        self.marks_var.set("")
        self.editing_roll = None
        self.add_btn.config(text="Add")
        self.status.config(text="Cleared.")

    def on_add(self):
        roll = self.roll_var.get().strip()
        name = self.name_var.get().strip()
        marks = self.marks_var.get().strip()

        if not (roll and name and marks):
            messagebox.showwarning("Invalid", "All fields are required.")
            return
        try:
            roll = int(roll)
            marks = float(marks)
        except ValueError:
            messagebox.showerror("Error", "Roll must be int and Marks must be float.")
            return

        if self.editing_roll is not None:
            old = self.model.find(self.editing_roll)
            if old:
                old.roll_no, old.name, old.marks = roll, name, marks
                self.status.config(text=f"Updated record for Roll {roll}.")
        else:
            if self.model.find(roll):
                messagebox.showerror("Error", "Roll number already exists.")
                return
            self.model.add(roll, name, marks)
            self.status.config(text=f"Added record for Roll {roll}.")
        self._refresh_table()
        self._clear_inputs()

    def on_delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a record to delete.")
            return
        roll = int(self.tree.item(sel[0])["values"][0])
        if messagebox.askyesno("Confirm", f"Delete record with Roll {roll}?"):
            if self.model.delete(roll):
                self.status.config(text=f"Deleted Roll {roll}.")
                self._refresh_table()

    def on_save(self):
        self.model.save()
        self.status.config(text="Saved to file.")

    def on_reload(self):
        self.model.load()
        self._refresh_table()
        self.status.config(text="Reloaded from file.")

    def on_export_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv",
                                                filetypes=[("CSV Files", "*.csv")])
        if not filename:
            return
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Roll No", "Name", "Marks"])
            writer.writerows(self.model.to_list())
        self.status.config(text=f"Exported to {filename}.")

    # ---------- Events ----------
    def _on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        roll, name, marks = self.tree.item(sel[0])["values"]
        self.roll_var.set(roll)
        self.name_var.set(name)
        self.marks_var.set(marks)
        self.editing_roll = roll
        self.add_btn.config(text="Update")
        self.status.config(text=f"Editing Roll {roll}...")

    def _on_right_click(self, event):
        rowid = self.tree.identify_row(event.y)
        if rowid:
            self.tree.selection_set(rowid)
            self.menu.post(event.x_root, event.y_root)

    def _ctx_edit(self):
        self._on_double_click(None)

    def _ctx_delete(self):
        self.on_delete()


# ---------------- Run Program ----------------
if __name__ == "__main__":
    if "--test" in sys.argv:
        s = StudentList()
        s.add(1, "Alice", 90)
        s.add(2, "Bob", 85)
        print("Model test:", s.to_list())
    else:
        app = App()
        app.mainloop()
