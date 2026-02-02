# modules/derivedvariables.py
import tkinter as tk
from tkinter import messagebox
from modules.db import list_all_variable_meta, set_variable_meta

from modules.db import (
    list_all_variable_meta,
    set_variable_meta,
    list_clients,
    get_all_variables_for_client,
    DB_PATH,
)

DEFAULT_SEPARATOR = " "



def setup_derived_wizard_ui(parent):
    """
    Build the Derived/Combined Variable Wizard UI in the given parent window.
    Features:
    - Search bar to filter variables
    - Scrollable variable list
    - Bottom panel for new variable name, separator, and buttons
    """
    parent.title("Derived/Combined Variable Wizard")
    parent.geometry("500x500")  # taller
    parent.grab_set()

    from modules.db import list_all_variable_meta, set_variable_meta
    import tkinter as tk
    from tkinter import messagebox

    vars_meta = list_all_variable_meta()
    all_var_names = [v["var_name"] for v in vars_meta]

    # Top frame: search bar
    top_frame = tk.Frame(parent)
    top_frame.pack(fill="x", padx=10, pady=(10,0))

    tk.Label(top_frame, text="Search variables:", font=("Helvetica", 12, "bold")).pack(side="left")
    search_var = tk.StringVar()
    search_entry = tk.Entry(top_frame, textvariable=search_var, width=30)
    search_entry.pack(side="left", padx=(5,0))

    # Middle frame: scrollable checkbox list
    middle_frame = tk.Frame(parent)
    middle_frame.pack(fill="both", expand=True, padx=10, pady=5)

    canvas = tk.Canvas(middle_frame)
    scrollbar = tk.Scrollbar(middle_frame, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    selections = {}  # {var_name: tk.BooleanVar}
    checkbuttons = {}  # store the widget for filtering

    def populate_vars(filter_term=""):
        # Clear current
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        checkbuttons.clear()
        for var in all_var_names:
            if filter_term.lower() in var.lower():
                var_check = tk.BooleanVar(value=False)
                selections[var] = var_check
                cb = tk.Checkbutton(scroll_frame, text=var, variable=var_check, anchor="w", width=40)
                cb.pack(anchor="w")
                checkbuttons[var] = cb

    populate_vars()

    def on_search(*_):
        populate_vars(search_var.get())

    search_var.trace_add("write", on_search)

    # Bottom frame: reserved for new variable, separator, buttons (~25%)
    bottom_frame = tk.Frame(parent, relief="raised", bd=1)
    bottom_frame.pack(fill="x", side="bottom", padx=10, pady=10)

    tk.Label(bottom_frame, text="New variable name:").grid(row=0, column=0, sticky="w")
    new_var_name = tk.StringVar()
    tk.Entry(bottom_frame, textvariable=new_var_name, width=25).grid(row=0, column=1, sticky="w", padx=5)

    tk.Label(bottom_frame, text="Separator:").grid(row=1, column=0, sticky="w", pady=(5,0))
    sep = tk.StringVar(value=" ")
    tk.Entry(bottom_frame, textvariable=sep, width=10).grid(row=1, column=1, sticky="w", padx=5, pady=(5,0))

    def create():
        if not new_var_name.get().strip():
            messagebox.showerror("Error", "New variable name required.", parent=parent)
            return

        selected_vars = [v for v, var in selections.items() if var.get()]
        if not selected_vars:
            messagebox.showerror("Error", "Select at least one variable.", parent=parent)
            return

        expr = f' {sep.get()} '.join(selected_vars)
        set_variable_meta(
            var_name=new_var_name.get(),
            var_type="string",
            category="Derived",
            description=f"Derived: {expr}",
            is_derived=1,
            derived_expression=expr,
        )
        messagebox.showinfo("Success", f"Derived variable '{new_var_name.get()}' created.", parent=parent)
        parent.destroy()

    btn_frame = tk.Frame(bottom_frame)
    btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
    tk.Button(btn_frame, text="Create", command=create).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Cancel", command=parent.destroy).pack(side="left", padx=5)



def open_derived_variable_wizard(parent):
    """
    Wizard for creating and computing conditional derived variables.
    """
    clients = list_clients()
    if not clients:
        messagebox.showinfo("Derived Variable", "No clients found.")
        return

    wizard = tk.Toplevel(parent)
    wizard.title("Derived Variable Wizard")
    wizard.geometry("750x500")
    wizard.grab_set()

    # ------------------------
    # Step 1: Select base variables
    # ------------------------
    vars_meta = list_all_variable_meta()
    var_names = [v["var_name"] for v in vars_meta]

    tk.Label(wizard, text="Step 1: Select Variables & Optional Conditions",
             font=("Helvetica", 12, "bold")).pack(pady=5)

    frame_vars = tk.Frame(wizard)
    frame_vars.pack(padx=10, fill="x")

    selections = {}  # {var_name: (tk.StringVar, tk.BooleanVar)}
    for i, var in enumerate(var_names):
        var_var = tk.StringVar(value=var)
        cond_var = tk.BooleanVar(value=False)
        selections[var] = (var_var, cond_var)

        tk.Label(frame_vars, text=var).grid(row=i, column=0, sticky="w")
        tk.Checkbutton(frame_vars, text="Include Conditionally", variable=cond_var).grid(row=i, column=1)
        tk.Entry(frame_vars, textvariable=var_var, width=20).grid(row=i, column=2)

    # ------------------------
    # Step 2: Separator and New Variable Name
    # ------------------------
    sep_var = tk.StringVar(value=DEFAULT_SEPARATOR)
    new_name_var = tk.StringVar()

    tk.Label(wizard, text="Step 2: Separator").pack(pady=(10,0))
    tk.Entry(wizard, textvariable=sep_var, width=10).pack()

    tk.Label(wizard, text="Step 3: New Variable Name").pack(pady=(10,0))
    tk.Entry(wizard, textvariable=new_name_var, width=30).pack()

    # ------------------------
    # Step 4: Select Client(s)
    # ------------------------
    tk.Label(wizard, text="Step 4: Select Client", font=("Helvetica", 12, "bold")).pack(pady=(10,0))
    client_options = [f"{c[1]} {c[2]} (ID: {c[0]})" for c in clients]
    client_var = tk.StringVar(value=client_options[0])
    tk.OptionMenu(wizard, client_var, *client_options).pack(pady=5)

    # ------------------------
    # Compute and save
    # ------------------------
    def create_and_compute():
        new_var_name = new_name_var.get().strip()
        if not new_var_name:
            messagebox.showerror("Error", "New variable name is required.", parent=wizard)
            return

        # Build expression
        parts = []
        for var, (var_var, cond_var) in selections.items():
            if cond_var.get():
                parts.append(f'({var_var.get()} if {var_var.get()} else "")')
            else:
                parts.append(var_var.get())

        expr = f" {sep_var.get()} ".join(parts)

        # Store derived variable in metadata
        set_variable_meta(
            var_name=new_var_name,
            var_type="string",
            category="Derived",
            description=f"Derived (conditional): {expr}",
            is_derived=1,
            derived_expression=expr,
        )

        # Compute for selected client
        selected_client_id = int(client_var.get().split("ID: ")[1].rstrip(")"))
        client_vars_dict = get_all_variables_for_client("client", selected_client_id)

        try:
            value = eval(expr, {}, client_vars_dict)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to compute derived variable:\n{e}", parent=wizard)
            return

        # Save value to database
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO variables (client_id, var_name, var_value) VALUES (?, ?, ?)",
            (selected_client_id, new_var_name, value)
        )
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", f"Derived variable '{new_var_name}' created for client.")
        wizard.destroy()

    tk.Button(wizard, text="Create & Compute", command=create_and_compute).pack(pady=10)
    tk.Button(wizard, text="Cancel", command=wizard.destroy).pack()

