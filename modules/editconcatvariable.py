# modules/editconcatvariable_improved.py
"""
Improved Concatenated Variable Editor - FULLY FIXED VERSION
- Shows all DB variables with checkboxes
- Order selection with numbered text boxes
- Option to create new variables
- Search functionality
- Accepts prefill_name parameter to pre-fill and lock variable name
- Returns the computed value after saving
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from modules.db import (
    list_all_concats,
    set_concat_variable,
    delete_concat_variable,
    get_variables,
    list_all_variable_meta,
    set_variable_meta,
    variable_exists
)

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 850

def open_concat_editor(parent, entity_type=None, prefill_name=None):
    """
    Improved Combo Variable Editor UI.
    Shows all DB variables, allows ordering, and creating new variables.
    
    Args:
        parent: Parent window
        entity_type: Type of entity (e.g., "client")
        prefill_name: If provided, pre-fills and locks the variable name field
    
    Returns:
        The computed value if saved, None otherwise
    """
    win = tk.Toplevel(parent)
    win.title("Combo Variable Editor")
    win.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    win.grab_set()
    
    # Track if user saved and the resulting value
    win.user_saved = False
    win.result_value = None

    main_frame = tk.Frame(win)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Left: list of existing combos (30%)
    list_frame = tk.Frame(main_frame, width=int(WINDOW_WIDTH * 0.3))
    list_frame.pack(side="left", fill="both", expand=False, padx=(0, 10))
    
    tk.Label(list_frame, text="Existing Combo Variables", font=("Arial", 11, "bold")).pack(pady=5)
    
    list_canvas = tk.Canvas(list_frame)
    list_scroll = tk.Scrollbar(list_frame, orient="vertical", command=list_canvas.yview)
    scrollable_list = tk.Frame(list_canvas)
    scrollable_list.bind("<Configure>", lambda e: list_canvas.configure(scrollregion=list_canvas.bbox("all")))
    list_canvas.create_window((0,0), window=scrollable_list, anchor="nw")
    list_canvas.configure(yscrollcommand=list_scroll.set)
    list_canvas.pack(side="left", fill="both", expand=True)
    list_scroll.pack(side="right", fill="y")

    # Right: editor (70%)
    editor_frame = tk.Frame(main_frame, relief="groove", bd=2)
    editor_frame.pack(side="right", fill="both", expand=True)

    # Editor title
    title_text = "Build Combo Variable"
    if prefill_name:
        title_text += f" ({prefill_name})"
    tk.Label(editor_frame, text=title_text, font=("Arial", 12, "bold")).pack(pady=10)

    # Name entry - pre-filled and readonly if prefill_name provided
    name_frame = tk.Frame(editor_frame)
    name_frame.pack(fill="x", padx=10, pady=5)
    tk.Label(name_frame, text="Combo Variable Name:", width=20, anchor="w").pack(side="left")
    name_var = tk.StringVar()
    
    if prefill_name:
        # Pre-fill and make readonly
        name_var.set(prefill_name)
        name_entry = tk.Entry(name_frame, textvariable=name_var, width=40, state='readonly', 
                             bg='#f0f0f0')  # Gray background to show it's readonly
    else:
        # Normal editable entry
        name_entry = tk.Entry(name_frame, textvariable=name_var, width=40)
    
    name_entry.pack(side="left", fill="x", expand=True)
    
    if prefill_name:
        tk.Label(name_frame, text="(from template)", fg="gray", font=("Arial", 8)).pack(side="left", padx=5)

    # Separator entry
    sep_frame = tk.Frame(editor_frame)
    sep_frame.pack(fill="x", padx=10, pady=5)
    tk.Label(sep_frame, text="Separator:", width=20, anchor="w").pack(side="left")
    separator_var = tk.StringVar(value=" ")
    sep_entry = tk.Entry(sep_frame, textvariable=separator_var, width=10)
    sep_entry.pack(side="left")
    tk.Label(sep_frame, text='(e.g., " " for space, ", " for comma-space)', fg="gray").pack(side="left", padx=5)

    # Description
    desc_frame = tk.Frame(editor_frame)
    desc_frame.pack(fill="x", padx=10, pady=5)
    tk.Label(desc_frame, text="Description:", anchor="w").pack()
    desc_text = tk.Text(desc_frame, width=60, height=2)
    desc_text.pack(fill="x")

    # Search box for variables
    search_frame = tk.Frame(editor_frame)
    search_frame.pack(fill="x", padx=10, pady=10)
    tk.Label(search_frame, text="Search variables:", width=20, anchor="w").pack(side="left")
    search_var = tk.StringVar()
    tk.Entry(search_frame, textvariable=search_var, width=40).pack(side="left", fill="x", expand=True)

    # Variables selection area
    var_frame = tk.Frame(editor_frame)
    var_frame.pack(fill="both", expand=True, padx=10, pady=5)
    
    tk.Label(var_frame, text="Available Variables (check to include, enter number for order):", 
            font=("Arial", 10, "bold")).pack(anchor="w")
    
    # Scrollable area for variables
    var_canvas = tk.Canvas(var_frame)
    var_scroll = tk.Scrollbar(var_frame, orient="vertical", command=var_canvas.yview)
    var_scrollable = tk.Frame(var_canvas)
    var_scrollable.bind("<Configure>", lambda e: var_canvas.configure(scrollregion=var_canvas.bbox("all")))
    var_canvas.create_window((0,0), window=var_scrollable, anchor="nw")
    var_canvas.configure(yscrollcommand=var_scroll.set)
    
    var_canvas.pack(side="left", fill="both", expand=True)
    var_scroll.pack(side="right", fill="y")

    # Variable selection storage
    var_selections = {}  # {var_name: (BooleanVar, StringVar for order, widget)}
    
    def load_variables():
        """Load all variables from database"""
        for widget in var_scrollable.winfo_children():
            widget.destroy()
        var_selections.clear()
        
        all_vars = list_all_variable_meta()
        search_term = search_var.get().lower()
        
        for var_meta in all_vars:
            var_name = var_meta["var_name"]
            
            # Filter by search
            if search_term and search_term not in var_name.lower():
                continue
            
            # Create row for this variable
            row_frame = tk.Frame(var_scrollable)
            
            # Checkbox
            checked = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(row_frame, text="", variable=checked, width=2)
            cb.pack(side="left")
            
            # Variable name
            tk.Label(row_frame, text=var_name, width=30, anchor="w").pack(side="left")
            
            # Order entry
            tk.Label(row_frame, text="Order:", width=6).pack(side="left")
            order_var = tk.StringVar()
            order_entry = tk.Entry(row_frame, textvariable=order_var, width=5)
            order_entry.pack(side="left", padx=5)
            
            # Description
            desc = var_meta.get("description", "")
            if desc:
                tk.Label(row_frame, text=f"({desc})", fg="gray", anchor="w").pack(side="left")
            
            row_frame.pack(fill="x", pady=1)
            
            var_selections[var_name] = (checked, order_var, row_frame)
    
    # Bind search
    search_var.trace_add("write", lambda *_: load_variables())
    
    # Initial load
    load_variables()

    # Add new variable button
    new_var_frame = tk.Frame(editor_frame)
    new_var_frame.pack(fill="x", padx=10, pady=10)
    
    def add_new_variable():
        """Add a new variable to the database"""
        new_name = simpledialog.askstring("New Variable", "Enter new variable name:", parent=win)
        if not new_name:
            return
        
        new_name = new_name.strip()
        if not new_name:
            return
        
        if variable_exists(new_name):
            messagebox.showwarning("Variable Exists", f"Variable '{new_name}' already exists.", parent=win)
            return
        
        new_desc = simpledialog.askstring("Description", f"Enter description for '{new_name}':", parent=win)
        
        # Add to database
        set_variable_meta(new_name, var_type="string", description=new_desc or "")
        
        # Reload variables
        load_variables()
        messagebox.showinfo("Success", f"Variable '{new_name}' added to database.", parent=win)
    
    tk.Button(new_var_frame, text="+ Create New Variable", command=add_new_variable, width=20).pack(side="left")

    # Preview area
    preview_frame = tk.Frame(editor_frame)
    preview_frame.pack(fill="x", padx=10, pady=10)
    tk.Label(preview_frame, text="Preview:", font=("Arial", 10, "bold")).pack(anchor="w")
    preview_var = tk.StringVar(value="(Select variables and assign order)")
    tk.Label(preview_frame, textvariable=preview_var, bg="#f0f0f0", anchor="w", justify="left", 
            wraplength=800, height=3).pack(fill="x")

    def update_preview(*_):
        """Update the preview based on selections"""
        selected = []
        for var_name, (checked, order_var, _) in var_selections.items():
            if checked.get():
                try:
                    order = int(order_var.get()) if order_var.get().strip() else 999
                except:
                    order = 999
                selected.append((order, var_name))
        
        if not selected:
            preview_var.set("(Select variables and assign order)")
            return
        
        # Sort by order
        selected.sort()
        var_names = [v for _, v in selected]
        
        # Get separator
        sep = separator_var.get()
        
        # Build preview with sample values
        client_vars = get_variables(entity_type or "client", 0)
        values = [client_vars.get(v, f"<{v}>") for v in var_names]
        preview = sep.join(values)
        
        preview_var.set(f"Result: {preview}\n\nComponents: {', '.join(var_names)}")
    
    # Trace updates
    separator_var.trace_add("write", update_preview)
    
    # Periodic preview updates
    def periodic_update():
        if win.winfo_exists():
            update_preview()
            win.after(1000, periodic_update)
    
    periodic_update()

    # Buttons at bottom
    btn_frame = tk.Frame(editor_frame)
    btn_frame.pack(fill="x", padx=10, pady=10)
    
    # Buttons at bottom - FIXED to always be visible
    btn_frame = tk.Frame(editor_frame)
    btn_frame.pack(side="bottom", fill="x", padx=10, pady=10)  # Changed to side="bottom"
    
    # Buttons at bottom - FIXED (removed duplicate btn_frame)
    btn_frame = tk.Frame(editor_frame)
    btn_frame.pack(side="bottom", fill="x", padx=10, pady=10)
    
    def save_combo():
        """Save the combo variable and continue editing"""
        vname = name_var.get().strip()
        if not vname:
            messagebox.showwarning("Save Combo Variable", "Please enter a combo variable name.", parent=win)
            return
        
        # Get selected variables in order
        selected = []
        for var_name, (checked, order_var, _) in var_selections.items():
            if checked.get():
                try:
                    order = int(order_var.get()) if order_var.get().strip() else 999
                except:
                    order = 999
                selected.append((order, var_name))
        
        if not selected:
            messagebox.showwarning("Save Combo Variable", "Please select at least one variable.", parent=win)
            return
        
        # Sort by order and extract names
        selected.sort()
        comp_list = [v for _, v in selected]
        
        sep = separator_var.get()
        desc = desc_text.get("1.0", "end").strip()
        
        # Save to database
        set_concat_variable(var_name=vname, components=comp_list, description=desc,
                           category="Derived", var_type="string", separator=sep)
        
        # Compute the actual value to return
        client_vars = get_variables(entity_type or "client", 0)
        values = [client_vars.get(v, "") for v in comp_list]
        computed_value = sep.join(values)
        
        # Set return values
        win.user_saved = True
        win.result_value = computed_value
        
        # Refresh list (if not pre-filled)
        if not prefill_name:
            refresh_list()
        
        # Show success message but DON'T CLOSE
        messagebox.showinfo("Success", f"Combo variable '{vname}' saved successfully!", parent=win)
        
        # Clear editor for next variable (optional - comment out if you want to keep it)
        if not prefill_name:
            clear_editor()
    
    def delete_selected():
        vname = name_var.get().strip()
        if not vname:
            messagebox.showwarning("Delete Combo Variable", "No combo variable selected to delete.", parent=win)
            return
        if not messagebox.askyesno("Confirm Delete", f"Delete combo variable '{vname}'?", parent=win):
            return
        delete_concat_variable(vname)
        refresh_list()
        clear_editor()
    
    def clear_editor():
        if not prefill_name:  # Only clear if not pre-filled
            name_var.set("")
        separator_var.set(" ")
        desc_text.delete("1.0", "end")
        for var_name, (checked, order_var, _) in var_selections.items():
            checked.set(False)
            order_var.set("")
        preview_var.set("(Select variables and assign order)")
    
    # Buttons - make them VERY visible
    tk.Button(btn_frame, text="💾 SAVE TO DATABASE", command=save_combo, width=25, 
             bg="#4CAF50", fg="white", font=("Arial", 11, "bold")).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Clear", command=clear_editor, width=12).pack(side="left", padx=5)
    
    if not prefill_name:  # Only show delete if we're in admin mode
        tk.Button(btn_frame, text="Delete", command=delete_selected, width=12, 
                 bg="#f44336", fg="white").pack(side="left", padx=5)
    
    tk.Button(btn_frame, text="Exit", command=win.destroy, width=12).pack(side="right", padx=5)





    # --- Existing combos list functions ---
    def refresh_list():
        for w in scrollable_list.winfo_children():
            w.destroy()
        combos = list_all_concats()
        if not combos:
            tk.Label(scrollable_list, text="No combo variables exist yet.", fg="gray").pack(padx=10, pady=10)
            return
        for c in combos:
            btn = tk.Button(scrollable_list, text=c["var_name"], anchor="w", relief="flat",
                          command=lambda cv=c: load_combo(cv), wraplength=250)
            btn.pack(fill="x", pady=1, padx=2)
    
    def load_combo(cv):
        """Load a combo variable into the editor"""
        if prefill_name:
            # Don't load other combos if we're locked to a specific variable
            messagebox.showinfo("Locked", 
                              f"Currently building '{prefill_name}' from template.\n"
                              "Cannot load other combo variables.", parent=win)
            return
            
        clear_editor()
        name_var.set(cv["var_name"])
        separator_var.set(cv.get("separator", " "))
        desc_text.insert("1.0", cv.get("description", ""))
        
        # Set checkboxes and orders
        components = cv["components"]
        for idx, comp in enumerate(components):
            if comp in var_selections:
                checked, order_var, _ = var_selections[comp]
                checked.set(True)
                order_var.set(str(idx + 1))
        
        update_preview()
    
    refresh_list()
    
    win.wait_window()
    
    # Return the computed value if saved
    return win.result_value if win.user_saved else None


# Keep backward compatibility
def get_or_build_derived_value(var_name, client_id, parent_window):
    """
    Returns the value of a derived/concatenated variable.
    Opens modal if needed.
    """
    combos = {c["var_name"]: c for c in list_all_concats()}
    client_vars = get_variables("client", client_id)

    if var_name in combos:
        comp_list = combos[var_name]["components"]
        sep = combos[var_name].get("separator", " ")
        return sep.join([client_vars.get(c, "") for c in comp_list])

    # If not exist, ask user to build it
    response = messagebox.askyesno(
        "Derived Variable",
        f"Variable '{var_name}' is not yet defined.\n\nWould you like to build it now?",
        parent=parent_window
    )
    
    if response:
        # Open concat editor with pre-filled name
        result = open_concat_editor(parent_window, entity_type="client", prefill_name=var_name)
        
        # If user saved, return the result
        if result:
            return result
        
        # Otherwise try fetching from database again
        combos = {c["var_name"]: c for c in list_all_concats()}
        if var_name in combos:
            comp_list = combos[var_name]["components"]
            sep = combos[var_name].get("separator", " ")
            return sep.join([client_vars.get(c, "") for c in comp_list])
    
    # Fallback to manual input
    val = simpledialog.askstring("Derived Variable", 
                                f"Enter value for derived variable '{var_name}'", 
                                parent=parent_window)
    return val or ""