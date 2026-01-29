# modules/listclients.py
import pandas as pd
from datetime import datetime
from pathlib import Path
import os
import platform
import subprocess
from tkinter import messagebox

from modules.db import list_clients, get_variables


def export_clients_to_excel():
    """
    Export all clients and their variables to an Excel file in ~/Downloads.
    Core client fields appear first, followed by dynamic variables.
    """

    clients = list_clients()
    if not clients:
        messagebox.showinfo("Export Clients", "No clients found in the database.")
        return None

    rows = []
    all_variable_names = set()

    # First pass: collect data + variable names
    for c in clients:
        client_id, first_name, last_name, birthday, matterid = c

        vars_dict = get_variables("client", client_id)
        all_variable_names.update(vars_dict.keys())

        rows.append({
            "_client_id": client_id,
            "First Name": first_name,
            "Last Name": last_name,
            "Birthday": birthday,
            "Matter ID": matterid,
            "_vars": vars_dict,
        })

    # Second pass: normalize rows so all variables exist as columns
    final_rows = []
    sorted_vars = sorted(all_variable_names)

    for r in rows:
        base = {
            "Client ID": r["_client_id"],
            "First Name": r["First Name"],
            "Last Name": r["Last Name"],
            "Birthday": r["Birthday"],
            "Matter ID": r["Matter ID"],
        }

        for var in sorted_vars:
            base[var] = r["_vars"].get(var)

        final_rows.append(base)

    df = pd.DataFrame(final_rows)

    # Output file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    downloads = Path.home() / "Downloads"
    downloads.mkdir(exist_ok=True)
    file_path = downloads / f"clients_{timestamp}.xlsx"

    df.to_excel(file_path, index=False)

    # Open file automatically
    try:
        if platform.system() == "Darwin":
            subprocess.call(["open", file_path])
        elif platform.system() == "Windows":
            os.startfile(file_path)
        else:
            subprocess.call(["xdg-open", file_path])
    except Exception:
        pass

    messagebox.showinfo(
        "Export Complete",
        f"{len(df)} client(s) exported to:\n{file_path}"
    )

    return str(file_path)
