# modules/main.py
import tkinter as tk
from tkinter import messagebox
import subprocess
import platform
from pathlib import Path
import openpyxl

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
    root = tk.Tk()
    root.title("Document Automation Tool")

    if ICON_PATH.exists():
        try:
            root.iconphoto(True, tk.PhotoImage(file=str(ICON_PATH)))
        except Exception:
            pass

    pad_x = 40
    pad_y = 15
    wrap_len = 260

    tk.Label(root, text="Document Automation", font=("Helvetica", 22)).pack(pady=(15, pad_y))

    buttons = [
        ("Generate Document(s)", on_generate_documents),
        ("Import Client / Matter Data", on_import_intake),
        ("Update/Delete Client", update_client),
        ("Export Clients", export_clients_to_excel),
        ("Admin", open_admin),
        ("Exit", root.destroy),
    ]

    for text, cmd in buttons:
        tk.Button(root, text=text, command=cmd, wraplength=wrap_len)\
            .pack(padx=pad_x, pady=pad_y, fill="x")

    root.update_idletasks()

    width = root.winfo_reqwidth() + pad_x
    height = root.winfo_reqheight() + pad_y
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)

    root.geometry(f"{width}x{height}+{x}+{y}")
    root.mainloop()


if __name__ == "__main__":
    main()
