# modules/editdynamicvariable.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from modules.db import (
    list_all_variable_meta,
    set_variable_meta,
    get_all_variables_for_client,
    get_variables,
)

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600


def open_derived_editor(parent, entity_type="client", entity_id=None):
    def get_derived_variables(entity_type=None):
        """
        Returns a list of all derived variables for the given entity_type.
        Each item is a dict containing the variable metadata.
        """
        derived = []
        for var in list_all_variable_meta():
            if var.get("is_derived"):
                if entity_type is None or var.get("entity_type") == entity_type:
                    derived.append(var)
        return derived

    derived_vars = get_derived_variables(entity_type)
    if not derived_vars:
        no_vars_win = tk.Toplevel(parent)
        no_vars_win.title("No Derived Variables")
        no_vars_win.geometry("400x150")
        tk.Label(no_vars_win, text="No derived variables found for this client.").pack(pady=20)
        tk.Button(no_vars_win, text="OK", command=no_vars_win.destroy).pack(pady=10)

        no_vars_win.lift()
        no_vars_win.grab_set()
        no_vars_win.focus_force()
        no_vars_win.wait_window()
        return

    client_vars = {}
    if entity_id is not None:
        client_vars = get_all_variables_for_client(entity_type, entity_id)

    win = tk.Toplevel(parent)
    win.title(f"Derived Variables — {entity_type} ID: {entity_id}")
    win.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    win.grab_set()

    # --- Search bar ---
    tk.Label(win, text="Search Derived Variable:").pack(anchor="w", padx=5, pady=(5, 0))
    search_var = tk.StringVar()
    tk.Entry(win, textvariable=search_var, width=60).pack(anchor="w", padx=5, pady=(0, 5))

    # --- Table frame with scrollbar ---
    container = tk.Frame(win)
    container.pack(fill="both", expand=True, padx=5, pady=5)

    canvas = tk.Canvas(container)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    headers = [
        "Variable Name",
        "Source Variables",
        "Current Value",
        "Description",
        "Type",
        "Category",
        "Derived",
        "Edit Expression"
    ]
    for col, h in enumerate(headers):
        tk.Label(scrollable_frame, text=h, font=("Helvetica", 10, "bold"), borderwidth=1, relief="solid").grid(
            row=0, column=col, sticky="nsew", padx=1, pady=1
        )

    def get_source_vars(expression):
        import re
        if not expression:
            return ""
        return ", ".join(sorted(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expression)))

    def edit_expression(var_meta):
        expr = var_meta.get("derived_expression", "")

        new_expr = simpledialog.askstring(
            "Edit Derived Expression",
            f"Variable: {var_meta['var_name']}\n\nCurrent expression:\n{expr}\n\nEnter new expression:",
            parent=win,
            initialvalue=expr
        )

        if new_expr is None:
            return

        test_context = {v: 1 for v in get_source_vars(new_expr).split(", ") if v}
        try:
            eval(new_expr, {"__builtins__": {}}, test_context)
        except Exception as e:
            messagebox.showerror("Invalid Expression", f"Error evaluating expression:\n{e}")
            return

        is_derived_flag = 1 if messagebox.askyesno("Derived", "Mark this variable as derived?") else 0

        set_variable_meta(
            var_name=var_meta["var_name"],
            var_type=var_meta["var_type"],
            description=var_meta.get("description"),
            category=var_meta.get("category"),
            display_order=var_meta.get("display_order", 0),
            is_derived=is_derived_flag,
            derived_expression=new_expr
        )
        messagebox.showinfo("Saved", f"Derived expression for {var_meta['var_name']} updated.")
        win.destroy()
        parent.event_generate("<<RefreshAdmin>>")

    # Populate table
    for row_index, var_meta in enumerate(derived_vars, start=1):
        name = var_meta["var_name"]
        expr = var_meta.get("derived_expression", "")
        sources = get_source_vars(expr)
        current_value = client_vars.get(name, {}).get("value") if entity_id else ""
        desc = var_meta.get("description", "")
        vtype = var_meta.get("var_type", "")
        category = var_meta.get("category", "")
        is_derived_flag = var_meta.get("is_derived", 0)

        tk.Label(scrollable_frame, text=name, anchor="w", width=25, borderwidth=1, relief="solid").grid(row=row_index, column=0, sticky="nsew")
        tk.Label(scrollable_frame, text=sources, anchor="w", width=25, borderwidth=1, relief="solid").grid(row=row_index, column=1, sticky="nsew")
        tk.Label(scrollable_frame, text=current_value, anchor="w", width=20, borderwidth=1, relief="solid").grid(row=row_index, column=2, sticky="nsew")
        tk.Label(scrollable_frame, text=desc, anchor="w", width=30, borderwidth=1, relief="solid").grid(row=row_index, column=3, sticky="nsew")
        tk.Label(scrollable_frame, text=vtype, anchor="w", width=10, borderwidth=1, relief="solid").grid(row=row_index, column=4, sticky="nsew")
        tk.Label(scrollable_frame, text=category, anchor="w", width=15, borderwidth=1, relief="solid").grid(row=row_index, column=5, sticky="nsew")

        # Derived checkbox
        derived_cb_var = tk.IntVar(value=is_derived_flag)
        tk.Checkbutton(scrollable_frame, variable=derived_cb_var, state="disabled").grid(row=row_index, column=6, sticky="nsew")

        edit_btn = tk.Button(scrollable_frame, text="Edit", command=lambda v=var_meta: edit_expression(v))
        edit_btn.grid(row=row_index, column=7, sticky="nsew", padx=1, pady=1)
