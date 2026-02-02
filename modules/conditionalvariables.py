# modules/conditionalvariables.py
import tkinter as tk
from tkinter import messagebox, ttk
from modules.db import list_all_variable_meta, set_variable_meta, get_variables, list_clients
from datetime import datetime

DEFAULT_SEPARATOR = " "

# ---------------------------
# Setup Conditional Wizard UI
# ---------------------------
def setup_conditional_wizard_ui(parent):
    """
    Build the Conditional Derived Variable Wizard UI in the given parent window.
    """
    parent.title("Conditional Derived Variable Wizard")
    parent.geometry("600x550")
    parent.grab_set()

    # --- Top frame: search + test client ---
    top_frame = tk.Frame(parent)
    top_frame.pack(side="top", fill="x", padx=10, pady=5)

    tk.Label(top_frame, text="Search Variable:").pack(side="left")
    search_var = tk.StringVar()
    tk.Entry(top_frame, textvariable=search_var, width=25).pack(side="left", padx=(5, 10))

    tk.Label(top_frame, text="Test Client:").pack(side="left")
    client_preview_var = tk.IntVar()
    clients = list_clients()
    client_map = {c[0]: c for c in clients}  # id -> client tuple
    client_names = [""] + [f"{c[0]} | {c[1]}" for c in clients]
    client_dropdown = ttk.Combobox(top_frame, values=client_names, width=25)
    client_dropdown.current(0)
    client_dropdown.pack(side="left")

    # --- Middle frame: scrollable variable checkboxes ---
    mid_frame = tk.Frame(parent)
    mid_frame.pack(fill="both", expand=True, padx=10)

    canvas = tk.Canvas(mid_frame, highlightthickness=0)
    scrollbar = tk.Scrollbar(mid_frame, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Load all variables
    vars_meta = list_all_variable_meta()
    var_names = [v["var_name"] for v in vars_meta]
    selections = {}  # var_name -> BooleanVar
    for var in var_names:
        var_check = tk.BooleanVar(value=False)
        selections[var] = var_check
        cb = tk.Checkbutton(scroll_frame, text=var, variable=var_check)
        cb.pack(anchor="w")

    # --- Bottom frame: new variable, separator, buttons ---
    bottom_frame = tk.Frame(parent)
    bottom_frame.pack(side="bottom", fill="x", padx=10, pady=10)

    tk.Label(bottom_frame, text="New Variable Name:").grid(row=0, column=0, sticky="w")
    new_var_name = tk.StringVar()
    tk.Entry(bottom_frame, textvariable=new_var_name, width=30).grid(row=0, column=1, sticky="w")

    tk.Label(bottom_frame, text="Separator:").grid(row=1, column=0, sticky="w")
    sep_var = tk.StringVar(value=DEFAULT_SEPARATOR)
    tk.Entry(bottom_frame, textvariable=sep_var, width=10).grid(row=1, column=1, sticky="w")

    btn_frame = tk.Frame(bottom_frame)
    btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

    # --- Preview area ---
    preview_frame = tk.Frame(parent, relief="groove", bd=1)
    preview_frame.pack(side="bottom", fill="x", padx=10, pady=(0,5))
    tk.Label(preview_frame, text="Preview:", font=("Helvetica", 12, "bold")).pack(anchor="w")
    preview_text = tk.StringVar()
    tk.Label(preview_frame, textvariable=preview_text, bg="#f5f5f5", anchor="w", justify="left").pack(fill="x", pady=2)

    # --- Filter function ---
    def filter_vars(*_):
        term = search_var.get().lower().strip()
        for child in scroll_frame.winfo_children():
            child.destroy()
        for var in var_names:
            if not term or term in var.lower():
                cb = tk.Checkbutton(scroll_frame, text=var, variable=selections[var])
                cb.pack(anchor="w")
        update_preview()

    search_var.trace_add("write", filter_vars)

    # --- Helper: get selected client variables ---
    def get_preview_client_vars():
        sel = client_dropdown.get()
        if not sel:
            return {}
        client_id = int(sel.split("|")[0].strip())
        client_vars = get_variables("client", client_id)
        return client_vars

    # --- Update preview dynamically ---
    def update_preview(*_):
        selected_vars = [v for v, var in selections.items() if var.get()]
        expr = f' {sep_var.get()} '.join(selected_vars)
        client_vars = get_preview_client_vars()
        preview_val = evaluate_conditional_variable(client_vars, {
            "derived_expression": expr,
            "separator": sep_var.get()
        })
        preview_text.set(preview_val)

    for var in selections.values():
        var.trace_add("write", update_preview)
    sep_var.trace_add("write", update_preview)
    client_dropdown.bind("<<ComboboxSelected>>", update_preview)

    # --- Create function ---
    def create():
        if not new_var_name.get().strip():
            messagebox.showerror("Error", "New variable name required.", parent=parent)
            return
        selected_vars = [v for v, var in selections.items() if var.get()]
        if not selected_vars:
            messagebox.showerror("Error", "Select at least one variable.", parent=parent)
            return
        expr = f' {sep_var.get()} '.join(selected_vars)
        set_variable_meta(
            var_name=new_var_name.get(),
            var_type="string",
            category="Derived",
            description=f"Conditional Derived: {expr}",
            is_derived=1,
            is_conditional=1,
            derived_expression=expr,
            separator=sep_var.get(),
        )
        messagebox.showinfo("Success", f"Conditional variable '{new_var_name.get()}' created.", parent=parent)
        parent.destroy()

    tk.Button(btn_frame, text="Create", command=create).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Cancel", command=parent.destroy).pack(side="left", padx=5)



# modules/conditionalvariables.py
def evaluate_conditional_variable(client_vars, var_meta, use_conditional=True):
    """
    Evaluate a derived or conditional variable for a client.
    Example:
      expr: "firstname lastname"
      result: "John Doe"
      expr: "JUSTICE_EMAIL if JUSTICE_EMAIL else direct_email"
      result: "by e-service to the following: ..."
    """
    expr = var_meta.get("derived_expression", "")
    if not use_conditional or not expr:
        # default: first variable
        parts = expr.split()
        if parts:
            return client_vars.get(parts[0], "")
        return ""

    # handle simple dynamic conditions
    try:
        # allow ternary-like syntax in your expression
        # e.g., "JUSTICE_EMAIL if JUSTICE_EMAIL else direct_email"
        result = eval(expr, {}, client_vars)
        return str(result)
    except Exception:
        # fallback: concatenate listed variables
        parts = [p.strip() for p in expr.split()]
        values = [client_vars.get(p, "") for p in parts]
        return " ".join(v for v in values if v)





# -------------------------------------------------
# Helper: evaluate a conditional variable for a client
# -------------------------------------------------
def evaluate_conditional_variable(client_vars, var_meta, use_conditional=True):
    """
    Returns the value for a conditional derived variable for a given client.
    If use_conditional=False, returns only the first variable.
    """
    expr = var_meta.get("derived_expression", "")
    separator = var_meta.get("separator", " ")
    parts = [p.strip() for p in expr.split(separator) if p.strip()]
    if not parts:
        return ""

    # Support dynamic variables
    dynamic_map = {
        "currentday": str(datetime.now().day),
        "currentmonth": datetime.now().strftime("%B"),
        "year": str(datetime.now().year)
    }

    values = []
    for part in parts:
        val = client_vars.get(part, "")
        val = val if val else dynamic_map.get(part, "")
        values.append(val)
    if not use_conditional:
        return values[0] if values else ""
    return separator.join(values)
