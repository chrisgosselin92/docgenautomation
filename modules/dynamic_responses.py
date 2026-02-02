# modules/dynamic_responses.py

from pathlib import Path
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from modules.variable_flags import apply_flags

DYNAMIC_RESPONSES_FILE = Path("dynamicpleadingresponses.xlsx")


def load_dynamic_responses(sheet_name: str) -> list[tuple[str, str]]:
    if not DYNAMIC_RESPONSES_FILE.exists():
        return []
    try:
        df = pd.read_excel(DYNAMIC_RESPONSES_FILE, sheet_name=sheet_name, header=0, usecols="A:B")
    except Exception:
        return []
    rows = []
    for _, row in df.iterrows():
        a = row.iloc[0]
        b = row.iloc[1]
        if pd.notna(a) and pd.notna(b):
            rows.append((str(a).strip(), str(b).strip()))
    return rows


def resolve_dynamic_blocks(parent, token_names: set[str], client_vars: dict = None) -> dict[str, str]:
    """
    Resolves dynamic blocks from Excel, respecting single-use vs multi-use.
    Multi-use blocks are cached for the session and reused automatically.
    Single-use blocks are prompted each time.
    """
    results = {}
    if client_vars is None:
        client_vars = {}

    if not DYNAMIC_RESPONSES_FILE.exists():
        return results

    # Initialize session cache
    if not hasattr(resolve_dynamic_blocks, "_session_cache"):
        resolve_dynamic_blocks._session_cache = {}
    multi_use_cache = resolve_dynamic_blocks._session_cache.setdefault("multi_use", {})
    single_use_cache = resolve_dynamic_blocks._session_cache.setdefault("single_use", {})

    for token in sorted(token_names):
        # Reuse cached results if available
        if token in single_use_cache:
            results[token] = single_use_cache[token]
            continue
        if token in multi_use_cache:
            results[token] = multi_use_cache[token]
            continue

        # Load Excel sheet for this block
        try:
            df = pd.read_excel(DYNAMIC_RESPONSES_FILE, sheet_name=token, header=None)
        except Exception:
            messagebox.showwarning(
                "Missing Dynamic Sheet",
                f"Sheet '{token}' not found in dynamicpleadingresponses.xlsx",
                parent=parent,
            )
            continue

        # Determine single-use vs multi-use
        single_use_flag = False
        if df.shape[1] >= 4:
            val = str(df.iloc[0, 3]).strip().lower()
            single_use_flag = val == "true"

        # Collect options
        options = []
        for i in range(1, len(df)):
            a = df.iloc[i, 0]
            b = df.iloc[i, 1]
            if pd.notna(a) and pd.notna(b):
                options.append((str(a).strip(), str(b).strip()))

        # Prompt user
        responses = []
        paragraph_no = 1
        while True:
            win = tk.Toplevel(parent)
            win.title(f"{token} – Paragraph {paragraph_no}")
            win.geometry("700x600")
            win.grab_set()

            choice_var = tk.StringVar()
            custom_top = tk.StringVar()
            last_paragraph = tk.BooleanVar(value=False)

            # Custom text entry
            tk.Label(win, text="Custom text (optional):").pack(anchor="w", padx=8)
            tk.Entry(win, textvariable=custom_top, width=90).pack(padx=8, pady=(0,8))

            # Options frame
            canvas = tk.Canvas(win)
            scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
            frame = tk.Frame(canvas)
            frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            custom_fields = {}
            for label, template in options:
                row = tk.Frame(frame)
                row.pack(fill="x", pady=2, padx=5)
                rb = tk.Radiobutton(
                    row,
                    text=label,
                    variable=choice_var,
                    value=label,
                    wraplength=400,
                    justify="left",
                )
                rb.pack(side="left", anchor="w")
                if "[[custom]]" in template.lower():
                    var = tk.StringVar()
                    tk.Entry(row, textvariable=var, width=30).pack(side="left", padx=5)
                    custom_fields[label] = var

            # Last paragraph checkbox only for multi-use
            if single_use_flag is False:
                tk.Checkbutton(win, text="Last paragraph", variable=last_paragraph).pack(anchor="w", padx=8)

            tk.Button(win, text="Next", command=win.destroy).pack(pady=8)
            win.wait_window()

            selected = choice_var.get()
            if not selected:
                break

            template = next(b for a, b in options if a == selected)
            if selected in custom_fields:
                user_val = custom_fields[selected].get().strip()
                template = template.replace("[[custom]]", user_val).replace("[[CUSTOM]]", user_val)

            text = (custom_top.get().strip() + "\n" if custom_top.get().strip() else "") + template
            text = text.replace("Paragraph #", f"Paragraph {paragraph_no}")

            responses.append(text)
            paragraph_no += 1

            # Stop loop if single-use or last paragraph selected
            if single_use_flag or last_paragraph.get():
                break

        final_text = "\n".join(responses)
        if single_use_flag:
            single_use_cache[token] = final_text
        else:
            multi_use_cache[token] = final_text

        # Assign final text to results
        results[token] = final_text

    return results


