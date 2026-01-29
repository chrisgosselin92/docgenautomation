# modules/admin.py
import tkinter as tk
from tkinter import messagebox
from modules.db import (
    list_all_variable_meta,
    set_variable_meta,
    variable_exists,
    DB_PATH,
)
import sqlite3
import ast

WARNING_TEXT = (
    "⚠ ADMIN MODE ⚠\n\n"
    "Changes here affect ALL documents and clients.\n\n"
    "Proceed only if you understand the consequences."
)

DEFAULT_CATEGORIES = [
    "Client",
    "Opposing Party",
    "Opposing Counsel",
    "Case Information",
    "Deadlines",
    "Damages",
    "Settlement",
    "Internal",
    "Document Control",
    "Ungrouped",
]

VAR_TYPES = [
    "string",
    "date",
    "number",
    "boolean",
]


def admin_access_allowed():
    """Future password hook."""
    return True


def create_variable_dialog(parent, prefill_name=""):
    win = tk.Toplevel(parent)
    win.title("Create New Variable")
    win.geometry("450x400")
    win.grab_set()

    fields = {}

    def row(label, widget, r):
        tk.Label(win, text=label, anchor="w").grid(row=r, column=0, sticky="w", padx=5, pady=5)
        widget.grid(row=r, column=1, sticky="w", padx=5)

    fields["var_name"] = tk.StringVar(value=prefill_name)
    fields["description"] = tk.StringVar()
    fields["category"] = tk.StringVar(value="Ungrouped")
    fields["display_order"] = tk.IntVar(value=0)
    fields["var_type"] = tk.StringVar(value="string")

    row("Variable Name", tk.Entry(win, textvariable=fields["var_name"], width=30), 0)
    row("Description", tk.Entry(win, textvariable=fields["description"], width=30), 1)
    row("Category", tk.OptionMenu(win, fields["category"], *DEFAULT_CATEGORIES), 2)
    row("Display Order", tk.Entry(win, textvariable=fields["display_order"], width=10), 3)
    row("Variable Type", tk.OptionMenu(win, fields["var_type"], *VAR_TYPES), 4)

    def create():
        name = fields["var_name"].get().strip()
        if not name:
            messagebox.showerror("Error", "Variable name is required.", parent=win)
            return
        if variable_exists(name):
            messagebox.showerror("Error", "Variable already exists.", parent=win)
            return
        set_variable_meta(
            var_name=name,
            var_type=fields["var_type"].get(),
            description=fields["description"].get(),
            category=fields["category"].get(),
            display_order=fields["display_order"].get(),
        )
        win.destroy()
        messagebox.showinfo("Admin", "Variable created successfully.", parent=parent)

    btns = tk.Frame(win)
    btns.grid(row=10, column=0, columnspan=2, pady=15)
    tk.Button(btns, text="Create", command=create).pack(side="left", padx=5)
    tk.Button(btns, text="Cancel", command=win.destroy).pack(side="left", padx=5)

    win.wait_window()


def open_admin():
    if not admin_access_allowed():
        return
    if not messagebox.askyesno("ADMIN WARNING", WARNING_TEXT):
        return

    win = tk.Toplevel()
    win.title("Variable Administration")
    win.geometry("1200x650")
    win.grab_set()

    def refresh_ui():
        for widget in win.winfo_children():
            widget.destroy()
        build_ui()

    def build_ui():
        vars_meta = list_all_variable_meta()

        body_container = tk.Frame(win)
        body_container.pack(fill="both", expand=True)
        canvas = tk.Canvas(body_container)
        scrollbar = tk.Scrollbar(body_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Headers
        headers = ["Variable", "Category", "Order", "Type", "Description", "Delete?", "New Name"]
        widths = [20, 20, 6, 10, 53, 7, 20]
        for col, (h, w) in enumerate(zip(headers, widths)):
            tk.Label(scrollable_frame, text=h, width=w, font=("Helvetica", 10, "bold"), anchor="w").grid(row=0, column=col, sticky="w")

        # Storage
        rows_widgets = []
        delete_vars = {}
        new_name_vars = {}

        def populate_rows(filter_text=""):
            for row in rows_widgets:
                for w in row:
                    if isinstance(w, tk.Widget):
                        w.destroy()
            rows_widgets.clear()

            ft = filter_text.lower()
            filtered_meta = [m for m in vars_meta if ft in m["var_name"].lower() or ft in (m.get("description") or "").lower()]

            for row_index, meta in enumerate(filtered_meta, start=1):
                var_name = meta["var_name"]
                cat_var = tk.StringVar(value=meta.get("category", "Ungrouped"))
                order_var = tk.IntVar(value=meta.get("display_order", 0))
                type_var = tk.StringVar(value=meta.get("var_type", "string"))
                desc_var = tk.StringVar(value=meta.get("description", ""))

                # Widgets
                tk.Label(scrollable_frame, text=var_name, anchor="w", width=20).grid(row=row_index, column=0, sticky="w")
                tk.OptionMenu(scrollable_frame, cat_var, *DEFAULT_CATEGORIES).grid(row=row_index, column=1, sticky="w")
                tk.Entry(scrollable_frame, textvariable=order_var, width=6).grid(row=row_index, column=2)
                tk.OptionMenu(scrollable_frame, type_var, *VAR_TYPES).grid(row=row_index, column=3, sticky="w")
                tk.Entry(scrollable_frame, textvariable=desc_var, width=50).grid(row=row_index, column=4, sticky="w")

                delete_var = tk.BooleanVar()
                tk.Checkbutton(scrollable_frame, variable=delete_var).grid(row=row_index, column=5)
                delete_vars[var_name] = delete_var

                new_name_var = tk.StringVar(value=var_name)
                tk.Entry(scrollable_frame, textvariable=new_name_var, width=20).grid(row=row_index, column=6, sticky="w")
                new_name_vars[var_name] = new_name_var

                rows_widgets.append([cat_var, order_var, type_var, desc_var, delete_var, new_name_var, var_name])

        # Search bar
        search_frame = tk.Frame(win)
        search_frame.pack(fill="x", pady=5)
        tk.Label(search_frame, text="Search Variables:").pack(side="left", padx=5)
        search_var = tk.StringVar()
        tk.Entry(search_frame, textvariable=search_var, width=50).pack(side="left", padx=5)
        search_var.trace_add("write", lambda *_: populate_rows(search_var.get()))

        populate_rows()

        # ---------------------------
        # Buttons
        # ---------------------------
        btns = tk.Frame(win)
        btns.pack(pady=10)

        def save_changes():
            changes = []
            deletions = []

            for row in rows_widgets:
                cat_var, order_var, type_var, desc_var, delete_var, new_name_var, var_name = row
                old_meta = next((m for m in vars_meta if m["var_name"] == var_name), {})

                if delete_var.get():
                    deletions.append(var_name)
                    continue

                new_name = new_name_var.get().strip()
                new_cat = cat_var.get()
                new_order = order_var.get()
                new_type = type_var.get()
                new_desc = desc_var.get().strip()

                if (new_name != var_name or new_cat != old_meta.get("category") or
                    new_order != old_meta.get("display_order") or new_type != old_meta.get("var_type") or
                    new_desc != old_meta.get("description")):
                    changes.append((var_name, new_name, new_cat, new_order, new_type, new_desc, old_meta))

            if not changes and not deletions:
                messagebox.showinfo("Admin", "No changes detected.", parent=win)
                return

            # Summary window
            summary_win = tk.Toplevel()
            summary_win.title("Confirm Changes")
            summary_win.geometry("1100x400")
            summary_win.grab_set()

            tk.Label(summary_win, text="You are making the following changes:", font=("Helvetica", 12, "bold")).pack(pady=5)

            # Show renames/updates
            if changes:
                for var_name, new_name, new_cat, new_order, new_type, new_desc, old_meta in changes:
                    old_cat = old_meta.get("category", "")
                    old_order = old_meta.get("display_order", "")
                    old_type = old_meta.get("var_type", "")
                    old_desc = old_meta.get("description", "")
                    text = f"{var_name} → {new_name if new_name != var_name else var_name} | " \
                           f"Category: {old_cat} → {new_cat} | Type: {old_type} → {new_type} | " \
                           f"Description: {old_desc} → {new_desc if new_desc != old_desc else old_desc}"
                    tk.Label(summary_win, text=text, anchor="w", justify="left", wraplength=1100).pack()

            # Show deletions
            if deletions:
                tk.Label(summary_win, text="Variables to be DELETED:", font=("Helvetica", 12, "bold"), fg="red").pack(pady=(10,0))
                tk.Label(summary_win, text=", ".join(deletions), fg="red").pack()

            confirmed = tk.BooleanVar(value=False)

            def confirm():
                conn = sqlite3.connect(DB_PATH)
                try:
                    c = conn.cursor()
                    # Deletions
                    for var_name in deletions:
                        c.execute("DELETE FROM variables_meta WHERE var_name=?", (var_name,))
                        c.execute("DELETE FROM variables WHERE var_name=?", (var_name,))
                    # Changes
                    for var_name, new_name, new_cat, new_order, new_type, new_desc, _ in changes:
                        set_variable_meta(
                            var_name=new_name,
                            category=new_cat,
                            display_order=new_order,
                            var_type=new_type,
                            description=new_desc,
                            conn=conn
                        )
                        if new_name != var_name:
                            c.execute("UPDATE variables_meta SET var_name=? WHERE var_name=?", (new_name, var_name))
                            c.execute("UPDATE variables SET var_name=? WHERE var_name=?", (new_name, var_name))
                    conn.commit()
                finally:
                    conn.close()
                confirmed.set(True)
                summary_win.destroy()
                refresh_ui()

            def cancel():
                confirmed.set(True)
                summary_win.destroy()

            btn_frame = tk.Frame(summary_win)
            btn_frame.pack(pady=10)
            tk.Button(btn_frame, text="Yes", command=confirm).pack(side="left", padx=5)
            tk.Button(btn_frame, text="No", command=cancel).pack(side="left", padx=5)

            summary_win.wait_variable(confirmed)

        tk.Button(btns, text="Create New Variable", command=lambda: create_variable_dialog(win)).pack(side="left", padx=5)
        tk.Button(btns, text="Save Changes", command=save_changes).pack(side="left", padx=5)
        tk.Button(btns, text="Cancel", command=win.destroy).pack(side="left", padx=5)

    build_ui()
