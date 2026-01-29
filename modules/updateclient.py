# modules/updateclient.py
import tkinter as tk
from tkinter import messagebox, font
import openpyxl

from modules.db import (
    list_clients,
    set_variable,
    get_variable_meta,
    set_variable_meta,
    delete_client,
    get_all_variables_for_client,
    list_all_variable_meta,
    get_variables,
)

INTAKE_XLSX = "intake.xlsx"
INTAKE_SHEET = "IntakeSheet"


# -------------------------------------------------
# Client display helper
# -------------------------------------------------
def build_client_label(client_id):
    vars_ = get_variables("client", client_id)
    matterid = vars_.get("matterid", "")
    first = vars_.get("firstname", "")
    last = vars_.get("lastname", "")

    name = " ".join(p for p in [first, last] if p).strip()
    label = f"ID-{client_id}"
    if matterid:
        label = f"({matterid}) - {label}"
    if name:
        label += f" - {name}"
    return label


# -------------------------------------------------
# Client selection popup
# -------------------------------------------------
def select_client(clients):
    selected_id = tk.IntVar(value=-1)
    cancelled = tk.BooleanVar(value=False)

    popup = tk.Toplevel()
    popup.title("Select Client")
    popup.geometry("450x450")
    popup.grab_set()

    tk.Label(popup, text="Search Client:").pack(pady=(10, 0))
    search_var = tk.StringVar()

    list_frame = tk.Frame(popup)
    list_frame.pack(fill="both", expand=True, padx=10)

    client_ids = [c[0] for c in clients]

    def update_list(*_):
        term = search_var.get().lower().strip()
        for w in list_frame.winfo_children():
            w.destroy()

        matches = []
        for cid in client_ids:
            label = build_client_label(cid)
            if not term or term in label.lower():
                matches.append((cid, label))

        if not matches:
            tk.Label(list_frame, text="No matches found").pack(anchor="w")
            return

        for cid, label in matches:
            tk.Radiobutton(
                list_frame,
                text=label,
                variable=selected_id,
                value=cid,
                wraplength=380,
            ).pack(anchor="w")

    search_var.trace_add("write", update_list)

    tk.Entry(popup, textvariable=search_var, width=50).pack(pady=5)
    update_list()
    tk.Entry(popup, textvariable=search_var, width=50).focus_set()

    def submit():
        if selected_id.get() == -1:
            messagebox.showwarning("Select Client", "No client selected.", parent=popup)
            return
        popup.destroy()

    def cancel():
        cancelled.set(True)
        popup.destroy()

    btns = tk.Frame(popup)
    btns.pack(pady=10)
    tk.Button(btns, text="Select", command=submit).pack(side="left", padx=5)
    tk.Button(btns, text="Cancel", command=cancel).pack(side="left", padx=5)

    popup.wait_window()

    if cancelled.get():
        return None, True
    return selected_id.get(), False


# -------------------------------------------------
# Intake sheet variable loader
# -------------------------------------------------
def load_intake_variables():
    vars_from_excel = set()
    try:
        wb = openpyxl.load_workbook(INTAKE_XLSX, data_only=True)
        if INTAKE_SHEET not in wb.sheetnames:
            return vars_from_excel

        sheet = wb[INTAKE_SHEET]
        for row in sheet.iter_rows(min_row=2, values_only=True):
            var_name = row[1]  # Column B
            if var_name and isinstance(var_name, str):
                vars_from_excel.add(var_name.strip())
    except Exception:
        pass
    return vars_from_excel


# -------------------------------------------------
# Main update workflow
# -------------------------------------------------
def update_client():
    while True:
        clients = list_clients()
        if not clients:
            messagebox.showinfo("Update Client", "No clients found.")
            return

        client_id, cancelled = select_client(clients)
        if cancelled or client_id is None:
            return

        client_vars = get_all_variables_for_client("client", client_id)

        window = tk.Toplevel()
        window.title(f"Update Client Variables — {build_client_label(client_id)}")
        window.geometry("980x620")
        window.grab_set()

        tk.Label(
            window,
            text="Edit variables or add new ones. All changes will be detected automatically.",
            font=("Helvetica", 13),
        ).pack(pady=8)

        tk.Label(window, text="Search Variable:").pack()
        var_search = tk.StringVar()
        tk.Entry(window, textvariable=var_search, width=50).pack(pady=(0, 10))

        table = tk.Frame(window)
        table.pack(fill="both", expand=True, padx=10)

        headers = ["Variable", "Description", "Value"]
        widths = [25, 45, 25]
        for i, (h, w) in enumerate(zip(headers, widths)):
            tk.Label(
                table,
                text=h,
                width=w,
                font=("Helvetica", 10, "bold"),
                anchor="w",
            ).grid(row=0, column=i, sticky="w")

        # Build variable universe
        all_var_meta = list_all_variable_meta()
        all_var_names = {m["var_name"] for m in all_var_meta}
        all_var_names |= load_intake_variables()
        meta_lookup = {m["var_name"]: m for m in all_var_meta}

        vars_by_category = {}
        for var_name in sorted(all_var_names):
            meta = meta_lookup.get(var_name) or {}
            category = meta.get("category", "General")
            vars_by_category.setdefault(category, []).append(var_name)

        row_vars = {}
        row_index = 1

        for category in sorted(vars_by_category):
            tk.Label(
                table,
                text=category,
                font=("Helvetica", 10, "bold"),
                anchor="w",
            ).grid(row=row_index, column=0, columnspan=3, sticky="w", pady=(6, 2))
            row_index += 1

            for var_name in vars_by_category[category]:
                meta = meta_lookup.get(var_name) or {}
                raw_val = client_vars.get(var_name)
                value = raw_val.get("value") if isinstance(raw_val, dict) else (raw_val or "")
                if isinstance(value, (dict, list, tuple)):
                    value = ""

                val_var = tk.StringVar(value=value)
                desc_var = tk.StringVar(value=meta.get("description", ""))

                tk.Label(table, text=var_name, width=25, anchor="w").grid(row=row_index, column=0, sticky="w")
                tk.Entry(table, textvariable=desc_var, width=45, state="readonly").grid(row=row_index, column=1, sticky="w")
                tk.Entry(table, textvariable=val_var, width=25).grid(row=row_index, column=2, sticky="w")

                row_vars[var_name] = {
                    "val": val_var,
                    "desc": desc_var,
                    "meta": meta,
                }

                row_index += 1

        # Apply updates with automatic change detection
        def apply_updates():
            changed_vars = []
            for var, info in row_vars.items():
                new_val = info["val"].get().strip()
                meta = info["meta"]
                old_val = client_vars.get(var, "")
                if isinstance(old_val, dict):
                    old_val = old_val.get("value", "")
                old_val = old_val or ""
                if new_val != old_val:
                    changed_vars.append((var, meta.get("description", ""), new_val))

            if not changed_vars:
                messagebox.showinfo("Update Client", "No changes detected.")
                return
            


            # BEFORE showing confirmation window
            changed_vars = []
            for var, info in row_vars.items():
                new_val = info["val"].get().strip()
                meta = info["meta"]
                old_val = client_vars.get(var, "")
                if isinstance(old_val, dict):
                    old_val = old_val.get("value", "")
                old_val = old_val or ""
                if new_val != old_val:
                    changed_vars.append((var, meta.get("description", ""), new_val, old_val))





            # -------------------------------------------------
            # Confirmation window with OLD values
            # -------------------------------------------------
            confirm_win = tk.Toplevel()
            confirm_win.title("Confirm Changes")
            confirm_win.geometry("800x400")
            confirm_win.grab_set()
            tk.Label(
                confirm_win,
                text="You are adding/changing values for these variables:",
                font=("Helvetica", 12, "bold"),
            ).pack(pady=5)

            list_frame = tk.Frame(confirm_win)
            list_frame.pack(fill="both", expand=True, padx=10, pady=5)

            headers = ["Variable", "Description", "New Value", "Old Value"]
            for col, h in enumerate(headers):
                tk.Label(list_frame, text=h, font=("Helvetica", 10, "bold")).grid(row=0, column=col, sticky="w", padx=2)

            for i, (var, desc, new_val, old_val) in enumerate(changed_vars, start=1):
                tk.Label(list_frame, text=var, anchor="w").grid(row=i, column=0, sticky="w", padx=2)
                tk.Label(list_frame, text=desc, anchor="w").grid(row=i, column=1, sticky="w", padx=2)
                tk.Label(list_frame, text=new_val, anchor="w", bg="#ffff99").grid(row=i, column=2, sticky="w", padx=2)
                tk.Label(list_frame, text=old_val, anchor="w").grid(row=i, column=3, sticky="w", padx=2)

            submitted = tk.BooleanVar(value=False)

            def confirm():
                for var, _, val, _ in changed_vars:
                    set_variable("client", client_id, var, val)
                submitted.set(True)
                confirm_win.destroy()
                window.destroy()  # back to client selection menu

            def cancel():
                submitted.set(True)
                confirm_win.destroy()  # back to editing

            btn_frame = tk.Frame(confirm_win)
            btn_frame.pack(pady=10)
            tk.Button(btn_frame, text="Yes", command=confirm).pack(side="left", padx=5)
            tk.Button(btn_frame, text="No", command=cancel).pack(side="left", padx=5)

            confirm_win.wait_variable(submitted)



















        btns = tk.Frame(window)
        btns.pack(pady=10)
        tk.Button(btns, text="Apply Updates", command=apply_updates).pack(side="left", padx=5)
        tk.Button(btns, text="Delete Client", command=lambda: delete_client_workflow(client_id, window), fg="red").pack(side="left", padx=5)
        tk.Button(btns, text="Cancel", command=window.destroy).pack(side="left", padx=5)

        window.wait_window()


def delete_client_workflow(client_id, window):
    if not messagebox.askyesno(
        "Delete Client",
        "⚠ WARNING ⚠\n\nThis will permanently delete this client.",
        parent=window,
    ):
        return
    delete_client(client_id)
    window.destroy()
    messagebox.showinfo("Delete Client", "Client deleted.")
