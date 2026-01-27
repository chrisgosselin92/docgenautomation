# listclients.py
import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime
import os
import platform
import subprocess
from modules.db import DB_PATH

def export_clients_to_excel():
    # Connect to DB and get clients
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, email, phone FROM clients')
    rows = c.fetchall()
    conn.close()

    if not rows:
        raise ValueError("No clients found in database.")

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=["ID", "Name", "Email", "Phone"])

    # Build filename
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    downloads = str(Path.home() / "Downloads")
    file_path = Path(downloads) / f"clients_{now}.xlsx"

    # Save to Excel
    df.to_excel(file_path, index=False)

    # Open file automatically
    if platform.system() == "Darwin":        # macOS
        subprocess.run(["open", str(file_path)])
    elif platform.system() == "Windows":     # Windows
        os.startfile(file_path)
    else:                                    # Linux (gnome / xdg-open)
        subprocess.run(["xdg-open", str(file_path)])

    return file_path
