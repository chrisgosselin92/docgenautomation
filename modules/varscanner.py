# modules/varprompt.py
import tkinter as tk
from modules.admin import create_variable_dialog

def prompt_and_create_variables(parent, undefined_vars):
    """
    parent: parent Tk window
    undefined_vars: list of strings
    """
    if not undefined_vars:
        return

    prompt_win = tk.Toplevel(parent)
    prompt_win.title("Undefined Variables Detected")
    prompt_win.geometry("400x400")
    prompt_win.grab_set()

    tk.Label(prompt_win, text="The following variables are undefined.\nCheck the ones you want to define:", wraplength=380).pack(pady=5)
    frame = tk.Frame(prompt_win)
    frame.pack(fill="both", expand=True)

    var_checks = {}
    for v in undefined_vars:
        var_checks[v] = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text=v, variable=var_checks[v]).pack(anchor="w")

    proceed = tk.BooleanVar(value=False)
    def on_proceed():
        proceed.set(True)
        prompt_win.destroy()
    tk.Button(prompt_win, text="Continue", command=on_proceed).pack(pady=10)
    prompt_win.wait_variable(proceed)

    # Sequentially prompt for checked variables
    for var_name, checked_var in var_checks.items():
        if checked_var.get():
            create_variable_dialog(parent, prefill_name=var_name)
