# modules/docgen.py
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from docx import Document
import pandas as pd
import re
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from modules.db import (
    list_clients,
    get_variables,
    set_variable,
    variable_exists,
)
from modules.admin import create_variable_dialog

# ---------------------------
# XML placeholder extraction
# ---------------------------
def extract_placeholders_from_docx(path: Path) -> set[str]:
    placeholders = set()
    with ZipFile(path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    texts = [node.text for node in root.iter() if node.tag.endswith("}t") and node.text]
    combined = "".join(texts)
    for match in re.findall(r"\{\{\s*([^{}]+?)\s*\}\}", combined):
        if match.strip():
            placeholders.add(match.strip())
    return placeholders

# ---------------------------
# Tag handling
# ---------------------------
INTAKE_FILE = Path("intake.xlsx")
INTAKE_SHEET = "IntakeSheet"
INTAKE_TAGS_SHEET = "tags"

def load_tags():
    tags_map = {}
    if not INTAKE_FILE.exists():
        return tags_map
    try:
        df = pd.read_excel(INTAKE_FILE, sheet_name=INTAKE_TAGS_SHEET, header=None, skiprows=1)
    except Exception:
        return tags_map

    for _, row in df.iterrows():
        var_name = str(row[0]).strip() if not pd.isna(row[0]) else None
        if not var_name or not var_name.isalpha():
            continue
        tags_map[var_name] = {}
        for i in range(1, len(row), 2):
            tag = row[i]
            example = row[i + 1] if i + 1 < len(row) else None
            if not pd.isna(tag):
                tags_map[var_name][str(tag).strip()] = example
    return tags_map

def apply_tags(value, var_name, tags_map):
    if value is None:
        return ""
    if var_name not in tags_map or not tags_map[var_name]:
        return str(value)
    tag, _ = next(iter(tags_map[var_name].items()))
    try:
        if "date" in tag.lower():
            return pd.to_datetime(value).strftime("%Y-%m-%d")
        if "amount" in tag.lower():
            return f"${float(value):,.2f}"
    except Exception:
        pass
    return str(value)

# ---------------------------
# Client display helpers
# ---------------------------
def build_client_label(client_id):
    vars_ = get_variables("client", client_id)
    matterid = vars_.get("matterid", "")
    first = vars_.get("firstname", "")
    last = vars_.get("lastname", "")
    name = " ".join(p for p in [first, last] if p).strip()
    label = f"ID {client_id}"
    if matterid:
        label += f" | {matterid}"
    if name:
        label += f" | {name}"
    return label

# ---------------------------
# Client selection
# ---------------------------
def select_client(clients):
    selected_id = tk.IntVar(value=-1)
    popup = tk.Toplevel()
    popup.title("Select Client")
    popup.geometry("420x420")
    popup.grab_set()
    tk.Label(popup, text="Search Client:").pack(pady=(10, 0))
    search_var = tk.StringVar()
    frame = tk.Frame(popup)
    frame.pack(fill="both", expand=True, padx=10)
    all_clients = [c[0] for c in clients]

    def update_list(*_):
        term = search_var.get().lower()
        for w in frame.winfo_children():
            w.destroy()
        matches = []
        for cid in all_clients:
            label = build_client_label(cid)
            if term in label.lower():
                matches.append((cid, label))
        if not matches:
            tk.Label(frame, text="No matches found").pack(anchor="w")
            return
        for cid, label in matches:
            tk.Radiobutton(frame, text=label, variable=selected_id, value=cid, wraplength=380).pack(anchor="w")

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











# ---------------------------
# Prompt for client value with SKIP
# ---------------------------
def prompt_for_variable_value(parent, var_name):
    value = tk.StringVar()
    win = tk.Toplevel(parent)
    win.title("Enter Variable Value")
    win.geometry("400x200")
    win.grab_set()

    tk.Label(
        win,
        text=(
            "Your database does not have a value for:\n\n"
            f"{{{{{var_name}}}}}\n\n"
            "Please enter the value or skip to leave unchanged:"
        ),
        wraplength=380,
        justify="left",
    ).pack(pady=10)

    entry = tk.Entry(win, textvariable=value, width=50)
    entry.pack(pady=5)
    entry.focus_set()

    action = tk.StringVar(value="none")  # Tracks Save or Skip

    def save():
        action.set("save")
        win.destroy()

    def skip():
        action.set("skip")
        win.destroy()

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="Save", command=save).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Skip", command=skip).pack(side="left", padx=5)

    win.wait_variable(action)

    if action.get() == "save":
        return value.get().strip() or None
    elif action.get() == "skip":
        return None























# ---------------------------
# Document generation with skip handling
# ---------------------------
def generate_documents(client_id=None):
    clients = list_clients()
    if not clients:
        messagebox.showinfo("Generate Documents", "No clients found.")
        return
    if client_id is None:
        client_id = select_client(clients)
        if client_id is None:
            return

    templates_dir = Path("templates")
    if not templates_dir.exists():
        messagebox.showerror("Error", "Templates folder does not exist.")
        return
    templates = [f for f in templates_dir.iterdir() if f.suffix.lower() == ".docx"]
    if not templates:
        messagebox.showinfo("Generate Documents", "No templates found.")
        return

    tags_map = load_tags()
    output_dir = Path("output_documents")
    output_dir.mkdir(exist_ok=True)

    window = tk.Toplevel()
    window.title("Select Templates")
    window.geometry("420x420")
    window.grab_set()
    tk.Label(window, text="Select templates to generate", font=("Helvetica", 14)).pack(pady=5)

    selections = {}
    for t in templates:
        var = tk.BooleanVar(value=False)
        selections[t] = var
        tk.Checkbutton(window, text=t.name, variable=var).pack(anchor="w")

    def generate():
        chosen_paths = [p for p, v in selections.items() if v.get()]
        if not chosen_paths:
            messagebox.showwarning("Generate", "No templates selected.", parent=window)
            return

        # Extract placeholders from selected templates
        all_placeholders = set()
        for path in chosen_paths:
            all_placeholders |= extract_placeholders_from_docx(path)

        # Identify undefined variables
        undefined_vars = sorted(v for v in all_placeholders if not variable_exists(v))
        client_vars = get_variables("client", client_id)

        # Phase 1: Prompt for missing variables
        for var in undefined_vars:
            current_val = client_vars.get(var, "")
            if not str(current_val).strip():
                val = prompt_for_variable_value(window, var)
                if val is None:  # User clicked Skip or left empty
                    continue  # Do not overwrite DB
                set_variable("client", client_id, var, val)
                client_vars[var] = val

        # Phase 2: Generate documents with available variable values
        for template_path in chosen_paths:
            doc = Document(template_path)
            # Replace variables in paragraphs
            for p in doc.paragraphs:
                for var, val in client_vars.items():
                    token = f"{{{{{var}}}}}"
                    if token in p.text:
                        p.text = p.text.replace(token, apply_tags(val, var, tags_map))
            # Replace variables in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for var, val in client_vars.items():
                            token = f"{{{{{var}}}}}"
                            if token in cell.text:
                                cell.text = cell.text.replace(token, apply_tags(val, var, tags_map))

            matterid = client_vars.get("matterid", "unknown")
            out = output_dir / f"{template_path.stem}-{matterid}.docx"
            doc.save(out)

        messagebox.showinfo(
            "Documents Generated",
            f"{len(chosen_paths)} document(s) generated.\nSaved in:\n{output_dir.resolve()}",
            parent=window,
        )
        window.destroy()

    tk.Button(window, text="Generate", command=generate).pack(pady=10)
    window.protocol("WM_DELETE_WINDOW", window.destroy)
    window.wait_window()


