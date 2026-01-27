# importvariables.py
from tkinter import filedialog, messagebox
from docx import Document
import re
from modules.db import list_clients, set_client_variable, get_client_variables

def import_variables(root):
    # --- Select a document file ---
    file_path = filedialog.askopenfilename(
        parent=root,
        title="Select Document",
        filetypes=[("Word Documents", "*.docx")]
    )
    if not file_path:
        return

    # --- Extract {{variables}} ---
    doc = Document(file_path)
    text = "\n".join([p.text for p in doc.paragraphs])
    variables_found = set(re.findall(r"\{\{(.*?)\}\}", text))

    # --- Select clients ---
    clients = list_clients()
    if not clients:
        messagebox.showinfo("Import Variables", "No clients found in database.")
        return

    client_input = filedialog.askstring(
        "Select Clients",
        "Enter client IDs separated by commas, or leave blank for ALL clients:"
    )
    if client_input:
        client_ids = [int(cid.strip()) for cid in client_input.split(",") if cid.strip()]
    else:
        client_ids = [c[0] for c in clients]

    # --- Insert new variables with default None ---
    new_vars_count = 0
    for client_id in client_ids:
        existing_vars = set(get_client_variables(client_id).keys())
        new_vars = variables_found - existing_vars
        for var in new_vars:
            set_client_variable(client_id, var, None)
        new_vars_count += len(new_vars)

    messagebox.showinfo(
        "Import Variables",
        f"Imported {new_vars_count} new variable(s) for {len(client_ids)} client(s)."
    )
