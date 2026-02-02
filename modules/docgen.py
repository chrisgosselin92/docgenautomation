# modules/docgen.py
import tkinter as tk
from tkinter import messagebox, simpledialog
from pathlib import Path
from datetime import datetime
import pandas as pd
import zipfile
import re

from docxtpl import DocxTemplate
from modules.db import (
    list_clients,
    get_variables,
    set_variable,
    get_variable_value_for_client,
    list_all_concats,
    get_variable_meta
)
from modules.systemvariables import resolve_system_variables
from modules.editconcatvariable import get_or_build_derived_value


# -------------------------------------------------
# System date context
# -------------------------------------------------
def get_system_date_context():
    now = datetime.now()

    def ordinal(n):
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    return {
        "currentday": now.day,
        "currentdayordinal": ordinal(now.day),
        "currentmonth": now.strftime("%B"),
        "monthabbr": now.strftime("%b"),
        "year": now.year,
        "year2": now.strftime("%y"),
        "weekday": now.strftime("%A"),
        "weekdayabbr": now.strftime("%a"),
    }


# -------------------------------------------------
# DOCX placeholder extraction (NO Jinja parsing)
# -------------------------------------------------
PLACEHOLDER_PATTERN = re.compile(r"{{\s*(.*?)\s*}}")

def extract_placeholders_from_docx(docx_path: Path) -> set[str]:
    found = set()
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        for match in PLACEHOLDER_PATTERN.findall(xml):
            found.add(match.strip())
    return found


# -------------------------------------------------
# Client helpers
# -------------------------------------------------
def build_client_label(client_id):
    vars_ = get_variables("client", client_id)
    parts = [
        vars_.get("matterid", ""),
        f"{vars_.get('firstname','')} {vars_.get('lastname','')}".strip(),
    ]
    parts = [p for p in parts if p]
    return f"ID {client_id}" + (" | " + " | ".join(parts) if parts else "")


def select_client(clients):
    selected_id = tk.IntVar(value=-1)
    popup = tk.Toplevel()
    popup.title("Select Client")
    popup.geometry("420x420")
    popup.grab_set()

    search_var = tk.StringVar()
    tk.Label(popup, text="Search Client:").pack(pady=(10, 0))
    tk.Entry(popup, textvariable=search_var, width=50).pack(pady=5)

    frame = tk.Frame(popup)
    frame.pack(fill="both", expand=True, padx=10)

    def refresh(*_):
        for w in frame.winfo_children():
            w.destroy()
        term = search_var.get().lower()
        for cid, *_ in clients:
            label = build_client_label(cid)
            if term in label.lower():
                tk.Radiobutton(
                    frame,
                    text=label,
                    variable=selected_id,
                    value=cid,
                    wraplength=380
                ).pack(anchor="w")

    search_var.trace_add("write", refresh)
    refresh()

    def submit():
        if selected_id.get() == -1:
            messagebox.showwarning("Select Client", "No client selected.")
            return
        popup.destroy()

    tk.Button(popup, text="Select", command=submit).pack(pady=10)
    popup.wait_window()
    return selected_id.get() if selected_id.get() != -1 else None


# -------------------------------------------------
# Prompt dynamic paragraphs from Excel
# -------------------------------------------------
def prompt_dynamic_paragraphs(parent, placeholder_name, client_id, excel_path="dynamicpleadingresponses.xlsx"):
    try:
        df = pd.read_excel(excel_path, sheet_name=placeholder_name)
    except Exception as e:
        messagebox.showwarning(
            "Excel Load Error",
            f"Could not load sheet '{placeholder_name}': {e}",
            parent=parent
        )
        return ""

    selections = {}
    win = tk.Toplevel(parent)
    win.title(f"Select paragraphs for {placeholder_name}")
    win.geometry("600x400")
    win.grab_set()

    frame = tk.Frame(win)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    for idx, row in df.iterrows():
        text = str(row.iloc[1])
        var = tk.BooleanVar(value=False)
        selections[idx] = (var, text)
        tk.Checkbutton(
            frame,
            text=f"{text[:60]}...",
            variable=var,
            anchor="w",
            justify="left",
            wraplength=550
        ).pack(anchor="w", pady=2)

    done_var = tk.BooleanVar(value=False)
    tk.Button(win, text="Use Selected", command=lambda: done_var.set(True)).pack(pady=5)
    win.wait_variable(done_var)

    selected_texts = [text for var, text in selections.values() if var.get()]
    full_text = "\n\n".join(selected_texts)
    set_variable("client", client_id, placeholder_name, full_text)
    return full_text


# -------------------------------------------------
# Generate document (FILTER-SAFE)
# -------------------------------------------------
def generate_document_from_template(template_path, client_id, parent_window):
    """
    Renders a DOCX template for a client.
    Supports |derived, |upper, |caps without defining Jinja filters.
    """

    tpl = DocxTemplate(template_path)

    # -------------------------------------------------
    # Extract placeholders WITHOUT triggering Jinja filters
    # -------------------------------------------------
    try:
        raw_vars = tpl.get_undeclared_template_variables()
    except Exception:
        # Fallback: extract variables manually to avoid Jinja filter parsing
        import zipfile
        import re
        vars_found = set()
        with zipfile.ZipFile(template_path) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
            for match in re.findall(r"{{\s*(.*?)\s*}}", xml):
                vars_found.add(match)
        raw_vars = vars_found

    context = {}

    for placeholder in raw_vars:
        # Split modifiers
        parts = [p.strip() for p in placeholder.split("|")]
        base_name = parts[0]
        modifiers = set(parts[1:])

        is_derived = "derived" in modifiers
        do_caps = "caps" in modifiers or "upper" in modifiers

        # Fetch DB value
        value = get_variable_value_for_client(base_name, client_id)

        # Compute derived if needed
        if is_derived or value is None:
            value = get_or_build_derived_value(
                parent_window,   # ✅ correct Tk parent
                base_name,
                "client"
            )

        # Apply caps
        if do_caps and isinstance(value, str):
            value = value.upper()

        context[base_name] = value if value is not None else ""

    # -------------------------------------------------
    # Inject system variables
    # -------------------------------------------------
    context.update(get_system_date_context())

    # -------------------------------------------------
    # Render + save
    # -------------------------------------------------
    output_dir = Path("output_documents")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / (
        f"{template_path.stem}_filled_{client_id}_"
        f"{datetime.now().strftime('%Y%m%d%H%M%S')}.docx"
    )

    tpl.render(context)
    tpl.save(output_file)

    return str(output_file)


# -------------------------------------------------
# Orchestrator
# -------------------------------------------------
def generate_documents(client_id=None):
    clients = list_clients()
    if not clients:
        messagebox.showinfo("Generate Documents", "No clients found.")
        return

    if client_id is None:
        client_id = select_client(clients)
        if client_id is None:
            return

    templates = sorted(Path("templates").glob("*.docx"))
    if not templates:
        messagebox.showinfo("Generate Documents", "No templates found.")
        return

    window = tk.Toplevel()
    window.title("Select Templates")
    window.geometry("520x740")
    window.grab_set()

    selections = {}
    frame = tk.Frame(window)
    frame.pack(fill="both", expand=True)

    for t in templates:
        var = tk.BooleanVar()
        selections[t] = var
        tk.Checkbutton(frame, text=t.name, variable=var).pack(anchor="w")

    def run():
        chosen = [t for t, v in selections.items() if v.get()]
        if not chosen:
            messagebox.showwarning("Generate", "No templates selected.", parent=window)
            return
        for template in chosen:
            generate_document_from_template(template, client_id, window)
        messagebox.showinfo("Done", "Documents generated.", parent=window)
        window.destroy()

    tk.Button(window, text="Generate Selected", command=run).pack(side="bottom", fill="x", pady=5)
    window.wait_window()
