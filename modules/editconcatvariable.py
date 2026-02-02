# modules/editconcatvariable.py
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from modules.db import (
    list_all_concats,
    set_concat_variable,
    delete_concat_variable,
    get_variables
)

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600

def open_concat_editor(parent, entity_type=None):
    """
    Full Combo Variable Editor UI.
    Allows viewing, creating, editing, deleting combo variables.
    """
    win = tk.Toplevel(parent)
    win.title("Combo Variable Editor")
    win.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    win.grab_set()

    main_frame = tk.Frame(win)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Left: list of existing combos
    list_frame = tk.Frame(main_frame)
    list_frame.pack(side="left", fill="both", expand=True)
    list_canvas = tk.Canvas(list_frame)
    list_scroll = tk.Scrollbar(list_frame, orient="vertical", command=list_canvas.yview)
    scrollable_list = tk.Frame(list_canvas)
    scrollable_list.bind("<Configure>", lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all")))
    list_canvas.create_window((0,0), window=scrollable_list, anchor="nw")
    list_canvas.configure(yscrollcommand=list_scroll.set)
    list_canvas.pack(side="left", fill="both", expand=True)
    list_scroll.pack(side="right", fill="y")

    # Right: editor
    editor_frame = tk.Frame(main_frame, relief="groove", bd=2, width=400)
    editor_frame.pack(side="right", fill="y", padx=10)

    name_var = tk.StringVar()
    combo_var = tk.StringVar()
    separator_var = tk.StringVar(value=" ")
    preview_var = tk.StringVar()
    desc_text = tk.Text(editor_frame, width=40, height=3)

    # --- Build editor UI ---
    tk.Label(editor_frame, text="Combo Name:").pack(anchor="w", padx=5, pady=2)
    tk.Entry(editor_frame, textvariable=name_var, width=40).pack(anchor="w", padx=5, pady=2)
    tk.Label(editor_frame, text="Variables to Combine (comma separated):").pack(anchor="w", padx=5, pady=2)
    tk.Entry(editor_frame, textvariable=combo_var, width=40).pack(anchor="w", padx=5, pady=2)
    tk.Label(editor_frame, text="Separator:").pack(anchor="w", padx=5, pady=2)
    tk.Entry(editor_frame, textvariable=separator_var, width=10).pack(anchor="w", padx=5, pady=2)
    tk.Label(editor_frame, text="Preview Value:").pack(anchor="w", padx=5, pady=2)
    tk.Label(editor_frame, textvariable=preview_var, bg="#f0f0f0", width=40, anchor="w").pack(anchor="w", padx=5, pady=2)
    tk.Label(editor_frame, text="Description:").pack(anchor="w", padx=5, pady=2)
    desc_text.pack(anchor="w", padx=5, pady=2)

    def update_preview(*_):
        comps = [v.strip() for v in combo_var.get().split(",") if v.strip()]
        client_vars = get_variables(entity_type or "client", 0)  # 0 means current/all
        val = separator_var.get().join([client_vars.get(c, "") for c in comps])
        preview_var.set(val)
    combo_var.trace_add("write", update_preview)
    separator_var.trace_add("write", update_preview)

    # --- Buttons ---
    btn_frame = tk.Frame(editor_frame)
    btn_frame.pack(pady=5, fill="x")
    tk.Button(btn_frame, text="Save", command=lambda: save_combo()).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Delete", command=lambda: delete_selected()).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Clear", command=lambda: clear_editor()).pack(side="left", padx=5)

    # --- Core functions ---
    def refresh_list():
        for w in scrollable_list.winfo_children():
            w.destroy()
        combos = list_all_concats()
        if not combos:
            tk.Label(scrollable_list, text="No combo variables exist yet.").pack(padx=10, pady=10)
            return
        for c in combos:
            tk.Button(scrollable_list, text=c["var_name"], anchor="w", relief="flat",
                      command=lambda cv=c: load_combo(cv)).pack(fill="x", pady=1, padx=2)
    def load_combo(cv):
        name_var.set(cv["var_name"])
        combo_var.set(",".join(cv["components"]))
        separator_var.set(cv.get("separator"," "))
        desc_text.delete("1.0", "end")
        desc_text.insert("1.0", cv.get("description",""))
        update_preview()
    def clear_editor():
        name_var.set("")
        combo_var.set("")
        separator_var.set(" ")
        desc_text.delete("1.0", "end")
        preview_var.set("")
    def save_combo():
        vname = name_var.get().strip()
        comps = [v.strip() for v in combo_var.get().split(",") if v.strip()]
        sep = separator_var.get()
        desc = desc_text.get("1.0", "end").strip()
        if not vname or not comps:
            messagebox.showwarning("Save Combo Variable", "Combo name and components required.")
            return
        set_concat_variable(var_name=vname, components=comps, description=desc,
                            category="Derived", var_type="string", separator=sep)
        refresh_list()
        clear_editor()
    def delete_selected():
        vname = name_var.get().strip()
        if not vname:
            messagebox.showwarning("Delete Combo Variable", "No combo variable selected to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", f"Delete combo variable '{vname}'?"):
            return
        delete_concat_variable(vname)
        refresh_list()
        clear_editor()

    refresh_list()
    win.wait_window()

# -----------------------------
# New function: get or build derived value
# -----------------------------
def get_or_build_derived_value(parent, var_name, entity_type="client"):
    """
    Returns the value of a derived variable.
    Opens modal if needed, allows creating combo variable.
    """
    combos = {c["var_name"]: c for c in list_all_concats()}
    client_vars = get_variables(entity_type, 0)

    if var_name in combos:
        comp_list = combos[var_name]["components"]
        sep = combos[var_name].get("separator"," ")
        return sep.join([client_vars.get(c,"") for c in comp_list])

    # If not exist, ask user to build it
    messagebox.showinfo("Derived Variable", f"Variable '{var_name}' not yet defined. Build it now?", parent=parent)
    open_concat_editor(parent, entity_type=entity_type)

    # After editor closes, try fetching again
    combos = {c["var_name"]: c for c in list_all_concats()}
    if var_name in combos:
        comp_list = combos[var_name]["components"]
        sep = combos[var_name].get("separator"," ")
        return sep.join([client_vars.get(c,"") for c in comp_list])
    else:
        # fallback manual input
        val = tk.simpledialog.askstring("Derived Variable", f"Enter value for derived variable '{var_name}'", parent=parent)
        return val or ""

