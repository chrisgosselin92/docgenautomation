# modules/main.py
import tkinter as tk
import subprocess
import platform
import openpyxl
from pathlib import Path
from tkinter import messagebox
from modules.dbsync import run_startup_sync
from modules.admin import open_admin
from modules.intake import import_intake_for_client
from modules.updateclient import update_client, INTAKE_XLSX, INTAKE_SHEET
from modules.listclients import export_clients_to_excel
from modules.docgen import generate_documents
from modules.db import (
    create_db,
    ensure_variable_meta_columns,
    list_clients,
    get_variables,
)

ICON_PATH = Path("images/gavel_icon.png")

# -------------------------------------------------
# Ensure DB and variable metadata exist, then run startup sync
# -------------------------------------------------
create_db()
ensure_variable_meta_columns()
run_startup_sync()  # populates IntakeSheet with DB variables and groups

# -------------------------------------------------
# Client display helper
# -------------------------------------------------
def client_display_label(client):
    cid = client[0]
    matterid = client[4]

    vars_for_client = get_variables("client", cid)
    fname = vars_for_client.get("firstname") or ""
    lname = vars_for_client.get("lastname") or ""

    label = f"({matterid}) - ID-{cid}"
    if fname or lname:
        label += f" - {fname} {lname}"
    return label

# -------------------------------------------------
# Client selection popup
# -------------------------------------------------
def select_client_popup(clients):
    selected_id = tk.IntVar(value=-1)

    popup = tk.Toplevel()
    popup.title("Select Client")
    popup.geometry("460x460")
    popup.grab_set()

    tk.Label(popup, text="Search Client:").pack(pady=(10, 0))
    search_var = tk.StringVar()

    frame = tk.Frame(popup)
    frame.pack(fill="both", expand=True, padx=10)

    def update_list(*_):
        term = search_var.get().lower().strip()
        for w in frame.winfo_children():
            w.destroy()

        matches = []
        for client in clients:
            label = client_display_label(client)
            if not term or term in label.lower():
                matches.append((client[0], label))

        if not matches:
            tk.Label(frame, text="No matches found").pack(anchor="w")
            return

        for cid, label in matches:
            tk.Radiobutton(
                frame,
                text=label,
                variable=selected_id,
                value=cid,
                wraplength=400,
                anchor="w",
                justify="left"
            ).pack(anchor="w")

    search_var.trace_add("write", update_list)
    tk.Entry(popup, textvariable=search_var, width=50).pack(pady=5)
    update_list()

    def submit():
        if selected_id.get() == -1:
            messagebox.showwarning("Select Client", "No client selected.")
            return
        popup.destroy()

    tk.Button(popup, text="Select", command=submit).pack(pady=10)
    popup.wait_window()
    return selected_id.get() if selected_id.get() != -1 else None

# -------------------------------------------------
# Button handlers
# -------------------------------------------------
def on_import_intake():
    import_intake_for_client()

def on_generate_documents():
    clients = list_clients()
    if not clients:
        messagebox.showinfo("Generate Documents", "No clients found.")
        return

    client_id = clients[0][0] if len(clients) == 1 else select_client_popup(clients)
    if client_id is None:
        return

    generate_documents(client_id)

# -------------------------------------------------
# Main GUI
# -------------------------------------------------
def main():
    global root
    root = tk.Tk()
    root.title("Document Generation System")
    root.geometry("450x550")

    tk.Label(root, text="Document Generation System", font=("Arial", 16, "bold")).pack(pady=15)

    # Define ALL submenu functions AFTER root is created
    def on_generate_submenu():
        """Generate documents submenu"""
        submenu = tk.Toplevel(root)
        submenu.title("Generate Documents")
        submenu.geometry("400x250")
        submenu.grab_set()
        
        tk.Label(submenu, text="Generate Documents", font=("Arial", 14, "bold")).pack(pady=20)
        
        tk.Button(submenu, text="Generate Documents", command=lambda: [submenu.destroy(), on_generate_documents()], width=30).pack(pady=5)
        tk.Button(submenu, text="Back to Main Menu", command=submenu.destroy, width=30).pack(pady=5)

    def on_client_submenu():
        """Add/Update Client submenu"""
        submenu = tk.Toplevel(root)
        submenu.title("Add or Update Client")
        submenu.geometry("400x300")
        submenu.grab_set()
        
        tk.Label(submenu, text="Add or Update Client", font=("Arial", 14, "bold")).pack(pady=20)
        
        tk.Button(submenu, text="Import from Intake Excel", command=lambda: [submenu.destroy(), on_import_intake()], width=30).pack(pady=5)
        tk.Button(submenu, text="Update Client in DB", command=lambda: [submenu.destroy(), update_client()], width=30).pack(pady=5)
        tk.Button(submenu, text="Export Clients to Excel", command=lambda: [submenu.destroy(), export_clients_to_excel()], width=30).pack(pady=5)
        tk.Button(submenu, text="Back to Main Menu", command=submenu.destroy, width=30).pack(pady=5)

    def on_attorney_submenu():
        """Add/Update Opposing Counsel submenu"""
        submenu = tk.Toplevel(root)
        submenu.title("Add or Update Opposing Counsel")
        submenu.geometry("400x250")
        submenu.grab_set()
        
        tk.Label(submenu, text="Add or Update Opposing Counsel", font=("Arial", 14, "bold")).pack(pady=20)
        
        tk.Button(submenu, text="Add/Update Attorney in DB", 
                 command=lambda: [submenu.destroy(), __import__('modules.admin_attorney', fromlist=['open_admin_attorney']).open_admin_attorney()], 
                 width=30).pack(pady=5)
        tk.Button(submenu, text="Back to Main Menu", command=submenu.destroy, width=30).pack(pady=5)

    def on_tools_submenu():
        """Tools submenu"""
        submenu = tk.Toplevel(root)
        submenu.title("Tools")
        submenu.geometry("400x250")
        submenu.grab_set()
        
        tk.Label(submenu, text="Tools", font=("Arial", 14, "bold")).pack(pady=20)
        
        tk.Button(
            submenu,
            text="Template Builder (Convert Documents)",
            command=lambda: [submenu.destroy(), open_template_builder_tool()],
            width=35
        ).pack(pady=5)
        
        tk.Button(submenu, text="Back to Main Menu", command=submenu.destroy, width=35).pack(pady=5)

    def open_template_builder_tool():
        """Launch the template builder"""
        from modules.template_builder import open_template_builder
        open_template_builder(root)

    # NOW define buttons list (after all functions are defined)
    buttons = [
        ("Generate", on_generate_submenu),
        ("Add or Update Client", on_client_submenu),
        ("Add or Update Opposing Counsel", on_attorney_submenu),
        ("Document Template Builder", on_tools_submenu),
        ("Update Variables & Relations", open_admin),
        ("Exit", root.destroy),
    ]

    # Create the buttons
    for text, command in buttons:
        tk.Button(root, text=text, command=command, width=30, height=2).pack(pady=8)

    root.mainloop()


if __name__ == "__main__":
    main()