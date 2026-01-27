import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from db import create_db, create_variables_table, add_client, list_clients, get_client_variables, set_client_variable
from variables import bulk_add_variables
from docgen import generate_documents, select_client
from importvariables import import_variables
from listclients import export_clients_to_excel

def main():
    create_db()
    create_variables_table()

    root = tk.Tk()
    root.title("LegalDocGenerator")
    root.geometry("600x800")

    # --- Button callbacks ---
    def on_add_client():
        name = simpledialog.askstring("Add Client", "Enter client name:", parent=root)
        if not name:
            return
        email = simpledialog.askstring("Add Client", "Enter email (optional):", parent=root) or ""
        phone = simpledialog.askstring("Add Client", "Enter phone (optional):", parent=root) or ""
        add_client(name, email, phone)
        messagebox.showinfo("Success", f"Added client {name}")





    def on_list_clients():
        try:
            file_path = export_clients_to_excel()
            messagebox.showinfo("Export Complete", f"Clients exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export clients: {e}")

        

    def on_manage_variables():
        clients = list_clients()
        if not clients:
            messagebox.showinfo("Variables", "No clients found.")
            return
        client_choices = {str(c[0]): c[1] for c in clients}
        client_id = simpledialog.askstring(
            "Select Client",
            "Enter client ID:\n" + "\n".join([f"{cid}: {name}" for cid, name in client_choices.items()]),
            parent=root
        )
        if not client_id or client_id not in client_choices:
            return
        client_id = int(client_id)

        vars = get_client_variables(client_id)
        var_name = simpledialog.askstring("Variable Name", "Enter variable name:", parent=root)
        if not var_name:
            return
        current_val = vars.get(var_name, "Not defined for this client")
        var_value = simpledialog.askstring(
            "Variable Value",
            f"Current value: {current_val}\nEnter new value (leave blank to skip):",
            parent=root
        )
        if var_value is not None:
            set_client_variable(client_id, var_name, var_value)
            messagebox.showinfo("Success", f"Set variable '{var_name}' to '{var_value}' for {client_choices[str(client_id)]}")

    def on_bulk_update_db():
        clients = list_clients()
        if not clients:
            messagebox.showinfo("Bulk Update", "No clients found.")
            return

        var_input = simpledialog.askstring(
            "Bulk Update Variables",
            "Enter variable names separated by commas (e.g., case_type, hearing_date):",
            parent=root
        )
        if not var_input:
            return

        var_names = [v.strip() for v in var_input.split(",") if v.strip()]
        if not var_names:
            return

        client_input = simpledialog.askstring(
            "Select Clients",
            "Enter client IDs separated by commas, or leave blank for ALL clients:",
            parent=root
        )
        if client_input:
            try:
                client_ids = [int(cid.strip()) for cid in client_input.split(",") if cid.strip()]
            except ValueError:
                messagebox.showerror("Error", "Invalid client IDs entered.")
                return
        else:
            client_ids = [c[0] for c in clients]

        default_val = simpledialog.askstring(
            "Default Value",
            "Enter default value for these variables (optional, leave blank for None):",
            parent=root
        )

        bulk_add_variables(client_ids, var_names, default_val or None)
        messagebox.showinfo("Bulk Update", f"Updated {len(var_names)} variables for {len(client_ids)} clients.")


    def on_generate_documents():
        clients = list_clients()
        if not clients:
            messagebox.showinfo("Generate Documents", "No clients found.")
            return

        client_id = select_client(clients)
        if not client_id:
            return

        generate_documents(client_id)

    def on_import_variables():
        import_variables(root)

    def on_exit():
        root.destroy()

    # --- Layout ---
    tk.Label(root, text="LegalDocGenerator", font=("Helvetica", 16)).pack(pady=10)
    tk.Button(root, text="Generate Document(s)", width=20, height=2, command=on_generate_documents).pack(pady=5)
    tk.Button(root, text="Add Client", width=20, height=2, command=on_add_client).pack(pady=5)
    tk.Button(root, text="Export Client Info (.xsl)", width=20, height=2, command=on_list_clients).pack(pady=5)
    tk.Button(root, text="Update Client Info", width=20, height=2, command=on_manage_variables).pack(pady=5)
    tk.Button(root, text="Import Variables", width=20, height=2, command=on_import_variables).pack(pady=5)
    tk.Button(root, text="Bulk Update DB", width=20, height=2, command=on_bulk_update_db).pack(pady=5)
    tk.Button(root, text="Exit", width=20, height=2, command=on_exit).pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
