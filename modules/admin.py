# modules/admin.py
import tkinter as tk
import sqlite3
import modules.editdynamicvariable as edv
import modules.editconcatvariable as ecv
from tkinter import messagebox
from tkinter import ttk
from modules.editdynamicvariable import open_derived_editor
from modules.db import (
    list_all_variable_meta,
    set_variable_meta,
    variable_exists,
    DB_PATH,
)

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
    "Derived",
]

VAR_TYPES = ["string", "date", "number", "boolean"]


def admin_access_allowed():
    return True


# -------------------------------------------------
# Create Variable Dialog
# -------------------------------------------------
def create_variable_dialog(parent):
    win = tk.Toplevel(parent)
    win.title("Create New Variable")
    win.geometry("450x350")
    win.grab_set()

    name = tk.StringVar()
    desc = tk.StringVar()
    cat = tk.StringVar(value="Ungrouped")
    order = tk.IntVar(value=0)
    vtype = tk.StringVar(value="string")

    def row(r, label, widget):
        tk.Label(win, text=label).grid(row=r, column=0, sticky="w", padx=5, pady=5)
        widget.grid(row=r, column=1, sticky="w", padx=5)

    row(0, "Variable Name", tk.Entry(win, textvariable=name, width=30))
    row(1, "Description", tk.Entry(win, textvariable=desc, width=30))
    row(2, "Category", tk.OptionMenu(win, cat, *DEFAULT_CATEGORIES))
    row(3, "Display Order", tk.Entry(win, textvariable=order, width=10))
    row(4, "Variable Type", tk.OptionMenu(win, vtype, *VAR_TYPES))

    def create():
        if not name.get().strip():
            messagebox.showerror("Error", "Variable name required.", parent=win)
            return
        if variable_exists(name.get()):
            messagebox.showerror("Error", "Variable already exists.", parent=win)
            return

        set_variable_meta(
            var_name=name.get(),
            description=desc.get(),
            category=cat.get(),
            display_order=order.get(),
            var_type=vtype.get(),
        )
        win.destroy()
        parent.event_generate("<<RefreshAdmin>>")

    btns = tk.Frame(win)
    btns.grid(row=10, column=0, columnspan=2, pady=15)
    tk.Button(btns, text="Create", command=create).pack(side="left", padx=5)
    tk.Button(btns, text="Clear", command=win.destroy).pack(side="left", padx=5)


# -------------------------------------------------
# Admin Panel
# -------------------------------------------------
def open_admin():
    if not admin_access_allowed():
        return
    if not messagebox.askyesno("ADMIN WARNING", WARNING_TEXT):
        return

    win = tk.Toplevel()
    win.title("Variable Administration")
    win.geometry("800x650")
    win.grab_set()

    # -----------------------------
    # Search bar
    # -----------------------------
    search_var = tk.StringVar()
    tk.Label(win, text="Search Variables:", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=5, pady=(5, 0))
    tk.Entry(win, textvariable=search_var, width=40).pack(anchor="w", padx=5, pady=(0, 5))

    # -----------------------------
    # Main container: left list, right editor
    # -----------------------------
    main_frame = tk.Frame(win)
    main_frame.pack(fill="both", expand=True, padx=5, pady=5)

    # --- Scrollable variable list ---
    list_container = tk.Frame(main_frame)
    list_container.pack(side="left", fill="both", expand=True)

    canvas = tk.Canvas(list_container)
    scrollbar = tk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)
    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # --- Editor frame ---
    editor_frame = tk.Frame(main_frame, relief="groove", bd=2, width=300)
    editor_frame.pack(side="right", fill="y", padx=10, pady=5)

    # --- Editor variables ---
    var_name_var = tk.StringVar()
    category_var = tk.StringVar()
    type_var = tk.StringVar()
    order_var = tk.StringVar(value="0")

    # --- Editor fields ---
    tk.Label(editor_frame, text="Variable Name:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
    tk.Entry(editor_frame, textvariable=var_name_var, width=28).grid(row=0, column=1, padx=5, pady=2)

    tk.Label(editor_frame, text="Category:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
    DEFAULT_CATEGORIES_COMBO = ["General", "Client", "Opposing Party", "Case Information", "Deadlines",
                                "Damages", "Settlement", "Internal", "Document Control", "Derived"]
    category_cb = ttk.Combobox(editor_frame, textvariable=category_var,
                               values=DEFAULT_CATEGORIES_COMBO, width=26, state="readonly")
    category_cb.grid(row=1, column=1, padx=5, pady=2)

    def convert_category_to_text():
        category_cb.destroy()
        tk.Entry(editor_frame, textvariable=category_var, width=28).grid(row=1, column=1, padx=5, pady=2)
        add_cat_btn.destroy()

    add_cat_btn = tk.Button(editor_frame, text="Add category", command=convert_category_to_text)
    add_cat_btn.grid(row=1, column=2, padx=5)

    tk.Label(editor_frame, text="Type:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
    type_cb = ttk.Combobox(editor_frame, textvariable=type_var,
                           values=["string", "bool", "int", "float", "date"], width=28, state="readonly")
    type_cb.grid(row=2, column=1, padx=5, pady=2)

    tk.Label(editor_frame, text="Description:").grid(row=3, column=0, sticky="nw", padx=5, pady=2)
    desc_text = tk.Text(editor_frame, width=28, height=2)
    desc_text.grid(row=3, column=1, padx=5, pady=2)

    tk.Label(editor_frame, text="Display Order:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
    tk.Entry(editor_frame, textvariable=order_var, width=28).grid(row=4, column=1, padx=5, pady=2)

    # --- Editor buttons ---
    def clear_editor():
        var_name_var.set("")
        category_var.set("General")
        type_var.set("string")
        desc_text.delete("1.0", "end")
        order_var.set("0")

    def load_into_editor(var):
        var_name_var.set(var["var_name"])
        category_var.set(var.get("category", "General"))
        type_var.set(var.get("var_type", "string"))
        desc_text.delete("1.0", "end")
        desc_text.insert("1.0", var.get("description", ""))
        order_var.set(str(var.get("display_order", 0)))

    def save_var():
        name = var_name_var.get().strip()
        if not name:
            messagebox.showwarning("Save Variable", "Variable name cannot be empty.")
            return
        set_variable_meta(
            var_name=name,
            var_type=type_var.get(),
            description=desc_text.get("1.0", "end").strip(),
            category=category_var.get(),
            display_order=int(order_var.get() or 0)
        )
        populate_list()
        clear_editor()

    tk.Button(editor_frame, text="Save", command=save_var).grid(row=5, column=0, padx=5, pady=5)
    tk.Button(editor_frame, text="Clear", command=clear_editor).grid(row=5, column=1, padx=5, pady=5)

    # --- Bottom buttons ---
    bottom_frame = tk.Frame(win)
    bottom_frame.pack(fill="x", padx=5, pady=5)

    left_btn_frame = tk.Frame(bottom_frame)
    left_btn_frame.pack(side="left")

    tk.Button(
        left_btn_frame,
        text="Smart Variable Editor",
        command=lambda: edv.open_derived_editor(parent=win, entity_type=None)
    ).pack(side="left", padx=5)

    tk.Button(
        left_btn_frame,
        text="Combo Variable Editor",
        command=lambda: ecv.open_concat_editor(parent=win, entity_type=None)
    ).pack(side="left", padx=5)

    tk.Button(bottom_frame, text="Exit", command=win.destroy).pack(side="right", padx=5)

    # --- Populate variable list ---
    def populate_list(*_):
        for widget in scroll_frame.winfo_children():
            widget.destroy()

        term = search_var.get().lower()
        grouped = {}
        for var in list_all_variable_meta():
            cat = var.get("category", "Ungrouped")
            grouped.setdefault(cat, []).append(var)

        for cat, vars_in_cat in sorted(grouped.items()):
            header = tk.Label(scroll_frame, text=cat, font=("Helvetica", 10, "bold"), bg="#e0e0e0")
            header.pack(fill="x", pady=(5, 0))
            for var in sorted(vars_in_cat, key=lambda v: v["var_name"].lower()):
                label = f"  {var['var_name']}"
                if term in label.lower():
                    tk.Button(scroll_frame, text=label, anchor="w", relief="flat",
                              command=lambda v=var: load_into_editor(v)).pack(fill="x", padx=2, pady=1)

    search_var.trace_add("write", populate_list)
    populate_list()

