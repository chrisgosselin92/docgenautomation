# modules/importvariables.py
import re
from tkinter import filedialog, messagebox
from docx import Document
from modules.db import list_clients, set_variable, get_variables

def import_variables(root):
    """
    Import variables from a Word template into the database dynamically.
    Prompts the user to select a template and which clients to update.
    """
    # --- Select a document file ---
    file_path = filedialog.askopenfilename(
        parent=root,
        title="Select Word Document",
        filetypes=[("Word Documents", "*.docx")]
    )
    if not file_path:
        return

    # --- Extract {{variables}} from the document ---
    doc = Document(file_path)
    text = "\n".join([p.text for p in doc.paragraphs])
    variables_found = set(re.findall(r"\{\{(.*?)\}\}", text))

    if not variables_found:
        messagebox.showinfo("Import Variables", "No variables found in the document.")
        return

    # --- Select clients ---
    clients = list_clients()
    if not clients:
        messagebox.showinfo("Import Variables", "No clients found in the database.")
        return

    client_input = filedialog.askstring(
        "Select Clients",
        "Enter client IDs separated by commas, or leave blank for ALL clients:"
    )
    if client_input:
        try:
            client_ids = [int(cid.strip()) for cid in client_input.split(",") if cid.strip()]
        except ValueError:
            messagebox.showerror("Error", "Invalid client IDs entered.")
            return
    else:
        client_ids = [c[0] for c in clients]  # all clients

    # --- Insert new variables dynamically ---
    new_vars_count = 0
    for client_id in client_ids:
        existing_vars = set(get_variables("client", client_id).keys())
        new_vars = variables_found - existing_vars
        for var in new_vars:
            set_variable("client", client_id, var, None)  # dynamic variable insert
        new_vars_count += len(new_vars)

    messagebox.showinfo(
        "Import Variables",
        f"Imported {new_vars_count} new variable(s) for {len(client_ids)} client(s)."
    )
