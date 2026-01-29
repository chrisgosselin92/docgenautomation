# modules/variables.py
from pathlib import Path
import pandas as pd
import tkinter as tk
from tkinter import simpledialog, messagebox

from modules.db import (
    set_variable,
    set_variable_meta,
    list_all_variable_meta,
)

INTAKE_FILE = Path("intake.xlsx")
INTAKE_SHEET = "IntakeSheet"

SUPPORTED_TYPES = {"string", "int", "float", "bool", "iso-date"}


# -------------------------------------------------
# Helpers
# -------------------------------------------------
def normalize_type(raw_type):
    if not raw_type or pd.isna(raw_type):
        return "string"
    t = str(raw_type).strip().lower()
    return t if t in SUPPORTED_TYPES else "string"


def coerce_value(value, var_type: str):
    if value is None or value == "":
        return None
    try:
        if var_type == "int":
            return int(value)
        if var_type == "float":
            return float(value)
        if var_type == "bool":
            return str(value).strip().lower() in {"1", "true", "yes", "y"}
        return str(value).strip()
    except Exception:
        return str(value).strip()


def get_meta_lookup():
    """Return {var_name: meta_dict}"""
    return {v["var_name"]: v for v in list_all_variable_meta()}


# -------------------------------------------------
# Core function
# -------------------------------------------------
def add_missing_variable(var_name: str, client_id: int):
    """
    Handles variables discovered at doc-generation time.

    - Ensures metadata exists
    - Ensures intake.xlsx contains the variable
    - Prompts once for value
    """
    root = tk.Tk()
    root.withdraw()

    meta_lookup = get_meta_lookup()
    meta = meta_lookup.get(var_name)

    # ---------------------------------------------
    # Step 1: Ensure metadata exists
    # ---------------------------------------------
    if not meta:
        description = simpledialog.askstring(
            "New Variable",
            f"Description for '{var_name}':"
        ) or ""

        var_type = simpledialog.askstring(
            "Variable Type",
            f"Type for '{var_name}' (string/int/float/bool/iso-date):",
            initialvalue="string"
        )
        var_type = normalize_type(var_type)

        set_variable_meta(
            var_name=var_name,
            var_type=var_type,
            description=description
        )
    else:
        var_type = meta.get("var_type", "string")
        description = meta.get("description", "")

    # ---------------------------------------------
    # Step 2: Ensure intake.xlsx has the variable
    # ---------------------------------------------
    if INTAKE_FILE.exists():
        try:
            df = pd.read_excel(INTAKE_FILE, sheet_name=INTAKE_SHEET, header=0)
        except ValueError:
            df = pd.DataFrame(columns=["Variable", "Value", "Type", "Description"])
    else:
        df = pd.DataFrame(columns=["Variable", "Value", "Type", "Description"])

    if "Variable" not in df.columns:
        df = pd.DataFrame(columns=["Variable", "Value", "Type", "Description"])

    if var_name not in df["Variable"].astype(str).values:
        new_row = {
            "Variable": var_name,
            "Value": "",
            "Type": var_type,
            "Description": description
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        with pd.ExcelWriter(
            INTAKE_FILE,
            engine="openpyxl",
            mode="a" if INTAKE_FILE.exists() else "w",
            if_sheet_exists="replace"
        ) as writer:
            df.to_excel(writer, sheet_name=INTAKE_SHEET, index=False)

    # ---------------------------------------------
    # Step 3: Prompt for value and save
    # ---------------------------------------------
    value = simpledialog.askstring(
        "Set Variable Value",
        f"Enter value for '{var_name}':"
    )

    value = coerce_value(value, var_type)

    if value is not None:
        set_variable("client", client_id, var_name, value)

    root.destroy()
