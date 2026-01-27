# docgen.py
import tkinter as tk
from tkinter import messagebox, simpledialog
from pathlib import Path
from db import list_clients, get_client_variables  # assuming you have db.py for DB functions

def select_client(clients):
    selected_id = tk.IntVar()
    window = tk.Toplevel()
    window.title("Select Client")
    window.geometry("400x300")

    tk.Label(window, text="Select Client:", font=("Helvetica", 14)).pack(pady=5)
    for c in clients:
        tk.Radiobutton(window, text=f"{c[0]}: {c[1]}", variable=selected_id, value=c[0]).pack(anchor="w")

    def submit():
        if not selected_id.get():
            messagebox.showerror("Error", "No client selected.")
            return
        window.destroy()

    tk.Button(window, text="Select", command=submit).pack(pady=10)
    window.grab_set()
    window.wait_window()
    return selected_id.get()

def generate_documents(client_id=None):
    """
    Main entry for generating documents.
    If client_id is None, prompt user to select a client.
    """
    clients = list_clients()
    if not clients:
        messagebox.showinfo("Generate Documents", "No clients found.")
        return

    if client_id is None:
        client_id = select_client(clients)
        if not client_id:
            return

    # At this point, client_id is valid
    client_vars = get_client_variables(client_id)

    # --- Template selection ---
    templates_dir = Path("templates")
    if not templates_dir.exists():
        messagebox.showerror("Error", "Templates folder does not exist.")
        return

    templates = [f.name for f in templates_dir.iterdir() if f.is_file() and f.suffix == ".docx"]
    if not templates:
        messagebox.showinfo("Generate Documents", "No templates found.")
        return

    # Ask user which templates to generate
    window = tk.Toplevel()
    window.title("Select Templates")
    window.geometry("400x400")

    tk.Label(window, text="Select Templates to Generate:", font=("Helvetica", 14)).pack(pady=5)

    selections = {}
    for t in templates:
        var = tk.IntVar()
        tk.Checkbutton(window, text=t, variable=var).pack(anchor="w")
        selections[t] = var

    def submit_templates():
        chosen = [name for name, var in selections.items() if var.get()]
        if not chosen:
            messagebox.showerror("Error", "No templates selected.")
            return
        window.destroy()
        # For now, just show a summary
        messagebox.showinfo("Templates Selected",
                            f"Client ID: {client_id}\nTemplates: {', '.join(chosen)}")

    tk.Button(window, text="Generate", command=submit_templates).pack(pady=10)
    window.grab_set()
    window.wait_window()
