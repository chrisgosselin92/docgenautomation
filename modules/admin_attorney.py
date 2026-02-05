# modules/admin_attorney.py
import tkinter as tk
from tkinter import messagebox, ttk
from modules.db import (
    list_opposing_counsel,
    get_opposing_counsel,
    create_opposing_counsel,
    update_opposing_counsel,
    delete_opposing_counsel,
    ensure_opposing_counsel_table,
    DB_PATH,  # ← Make sure this is here
    get_variables  # ← And this
)

WARNING_TEXT = (
    "⚠ ATTORNEY DB MANAGER ⚠\n\n"
    "This manages the opposing counsel database.\n"
    "Changes here will affect all documents that reference these attorneys."
)


def admin_attorney_access_allowed():
    return True


def open_admin_attorney():
    """Main attorney admin panel"""
    if not admin_attorney_access_allowed():
        return
    
    if not messagebox.askyesno("Attorney Database", WARNING_TEXT):
        return
    
    ensure_opposing_counsel_table()
    
    win = tk.Toplevel()
    win.title("Opposing Counsel Database Manager")
    win.geometry("1000x750")
    win.grab_set()
    
    # Search bar
    search_var = tk.StringVar()
    tk.Label(win, text="Search Attorneys:", font=("Helvetica", 10, "bold")).pack(anchor="w", padx=5, pady=(5, 0))
    tk.Entry(win, textvariable=search_var, width=40).pack(anchor="w", padx=5, pady=(0, 5))
    
    # Main container: left list, right editor
    main_frame = tk.Frame(win)
    main_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    # --- Left: Attorney List (40%) ---
    list_container = tk.Frame(main_frame)
    list_container.pack(side="left", fill="both", expand=True)
    
    tk.Label(list_container, text="Opposing Counsel List", font=("Helvetica", 11, "bold"), bg="#e0e0e0").pack(fill="x")
    
    canvas = tk.Canvas(list_container)
    scrollbar = tk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)
    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # --- Right: Editor Frame (60%) ---
    editor_frame = tk.Frame(main_frame, relief="groove", bd=2, width=600)
    editor_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)
    
    tk.Label(editor_frame, text="Attorney Details", font=("Helvetica", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
    
    # Editor variables
    attorney_id_var = tk.IntVar(value=-1)
    first_name_var = tk.StringVar()
    last_name_var = tk.StringVar()
    email_var = tk.StringVar()
    service_email_var = tk.StringVar()
    address_street_var = tk.StringVar()
    address_city_var = tk.StringVar()
    address_state_var = tk.StringVar()
    address_zip_var = tk.StringVar()
    phone_var = tk.StringVar()
    fax_var = tk.StringVar()
    firm_var = tk.StringVar()
    bar_number_var = tk.StringVar()
    
    # Editor fields
    def add_field(row, label_text, var, width=40):
        tk.Label(editor_frame, text=label_text + ":", anchor="w").grid(row=row, column=0, sticky="w", padx=5, pady=3)
        tk.Entry(editor_frame, textvariable=var, width=width).grid(row=row, column=1, sticky="ew", padx=5, pady=3)
    
    add_field(1, "First Name (Required)", first_name_var)
    add_field(2, "Last Name (Required)", last_name_var)
    add_field(3, "Law Firm", firm_var)
    add_field(4, "Email", email_var)
    add_field(5, "E-Service Email", service_email_var)
    add_field(6, "Street Address", address_street_var)
    add_field(7, "City", address_city_var)
    add_field(8, "State", address_state_var, width=10)
    add_field(9, "ZIP Code", address_zip_var, width=15)
    add_field(10, "Business Phone", phone_var)
    add_field(11, "Fax", fax_var)
    add_field(12, "Bar Number", bar_number_var)
    
    # Notes (multi-line)
    tk.Label(editor_frame, text="Notes:", anchor="w").grid(row=13, column=0, sticky="nw", padx=5, pady=3)
    notes_text = tk.Text(editor_frame, width=40, height=4)
    notes_text.grid(row=13, column=1, sticky="ew", padx=5, pady=3)
    
    editor_frame.grid_columnconfigure(1, weight=1)
    
    # --- Editor Functions ---
    def clear_editor():
        attorney_id_var.set(-1)
        first_name_var.set("")
        last_name_var.set("")
        email_var.set("")
        service_email_var.set("")
        address_street_var.set("")
        address_city_var.set("")
        address_state_var.set("")
        address_zip_var.set("")
        phone_var.set("")
        fax_var.set("")
        firm_var.set("")
        bar_number_var.set("")
        notes_text.delete("1.0", "end")
    
    def load_into_editor(counsel_id):
        row = get_opposing_counsel(counsel_id)
        if not row:
            return
        
        attorney_id_var.set(row[0])
        first_name_var.set(row[1] or "")
        last_name_var.set(row[2] or "")
        email_var.set(row[3] or "")
        service_email_var.set(row[4] or "")
        address_street_var.set(row[5] or "")
        address_city_var.set(row[6] or "")
        address_state_var.set(row[7] or "")
        address_zip_var.set(row[8] or "")
        phone_var.set(row[9] or "")
        fax_var.set(row[10] or "")
        firm_var.set(row[11] or "")
        bar_number_var.set(row[12] or "")
        notes_text.delete("1.0", "end")
        notes_text.insert("1.0", row[13] or "")
    
    def view_associated_clients():
        """Show all clients associated with this attorney"""
        counsel_id = attorney_id_var.get()
        if counsel_id == -1:
            messagebox.showinfo("No Attorney Selected", "Please select an attorney first.", parent=win)
            return
        
        # Get attorney name
        attorney_name = f"{first_name_var.get()} {last_name_var.get()}"
        
        # Query clients with this opposing_counsel_id
        import sqlite3
        from modules.db import DB_PATH, get_variables
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM clients WHERE opposing_counsel_id = ?", (counsel_id,))
        client_rows = c.fetchall()
        conn.close()
        
        if not client_rows:
            messagebox.showinfo(
                "No Associated Clients",
                f"No clients are currently assigned to {attorney_name}.",
                parent=win
            )
            return
        
        # Create display window
        clients_win = tk.Toplevel(win)
        clients_win.title(f"Clients for {attorney_name}")
        clients_win.geometry("600x425")
        clients_win.grab_set()
        
        tk.Label(
            clients_win,
            text=f"Clients assigned to: {attorney_name}",
            font=("Arial", 12, "bold")
        ).pack(pady=10)
        
        tk.Label(
            clients_win,
            text=f"Total: {len(client_rows)} client(s)",
            font=("Arial", 10),
            fg="gray"
        ).pack(pady=5)
        
        # Scrollable list
        list_frame = tk.Frame(clients_win)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(list_frame)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Build list
        for idx, (client_id,) in enumerate(client_rows, 1):
            vars_ = get_variables("client", client_id)
            matterid = vars_.get("matterid", "")
            firstname = vars_.get("firstname", "")
            lastname = vars_.get("lastname", "")
            
            name = f"{firstname} {lastname}".strip() or "(No Name)"
            label_text = f"{idx}. Client ID {client_id}"
            if matterid:
                label_text += f" - Matter: {matterid}"
            label_text += f" - {name}"
            
            tk.Label(scroll_frame, text=label_text, anchor="w").pack(anchor="w", padx=5, pady=2, fill="x")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        tk.Button(clients_win, text="Close", command=clients_win.destroy, width=15).pack(pady=10)
    
    def save_attorney():
        first_name = first_name_var.get().strip()
        last_name = last_name_var.get().strip()
        
        if not first_name or not last_name:
            messagebox.showwarning("Save Attorney", "First and last name are required.", parent=win)
            return
        
        email = email_var.get().strip()
        service_email = service_email_var.get().strip()
        address_street = address_street_var.get().strip()
        address_city = address_city_var.get().strip()
        address_state = address_state_var.get().strip()
        address_zip = address_zip_var.get().strip()
        phone = phone_var.get().strip()
        fax = fax_var.get().strip()
        firm = firm_var.get().strip()
        bar_number = bar_number_var.get().strip()
        notes = notes_text.get("1.0", "end").strip()
        
        counsel_id = attorney_id_var.get()
        
        if counsel_id == -1:
            # Create new
            new_id = create_opposing_counsel(first_name, last_name, email, service_email, address_street, address_city, address_state, address_zip, phone, fax, firm, bar_number, notes)
            if new_id is None:
                messagebox.showerror("Error", f"Attorney '{first_name} {last_name}' already exists.", parent=win)
                return
            attorney_id_var.set(new_id)
            messagebox.showinfo("Success", f"Attorney '{first_name} {last_name}' created successfully!", parent=win)
        else:
            # Update existing
            update_opposing_counsel(counsel_id, first_name, last_name, email, service_email, address_street, address_city, address_state, address_zip, phone, fax, firm, bar_number, notes)
            messagebox.showinfo("Success", f"Attorney '{first_name} {last_name}' updated successfully!", parent=win)
        
        populate_list()
    
    def delete_attorney():
        counsel_id = attorney_id_var.get()
        if counsel_id == -1:
            messagebox.showwarning("Delete Attorney", "No attorney selected.", parent=win)
            return
        
        name = f"{first_name_var.get()} {last_name_var.get()}"
        if not messagebox.askyesno("Confirm Delete", f"Delete attorney '{name}'?\n\nThis cannot be undone.", parent=win):
            return
        
        delete_opposing_counsel(counsel_id)
        messagebox.showinfo("Deleted", f"Attorney '{name}' has been deleted.", parent=win)
        clear_editor()
        populate_list()
    
    def create_new():
        clear_editor()
    
    # --- Editor Buttons (NOW all functions are defined above) ---
    button_frame = tk.Frame(editor_frame)
    button_frame.grid(row=14, column=0, columnspan=2, pady=15)
    
    tk.Button(button_frame, text="Save", command=save_attorney, width=12, bg="#4CAF50", fg="white").pack(side="left", padx=5)
    tk.Button(button_frame, text="View Associated Clients", command=view_associated_clients, width=20, bg="#2196F3", fg="white").pack(side="left", padx=5)
    tk.Button(button_frame, text="Delete", command=delete_attorney, width=12, bg="#f44336", fg="white").pack(side="left", padx=5)
    tk.Button(button_frame, text="Clear", command=clear_editor, width=12).pack(side="left", padx=5)
    
    # --- List Population ---
    def populate_list(*_):
        for widget in scroll_frame.winfo_children():
            widget.destroy()
        
        term = search_var.get().lower()
        attorneys = list_opposing_counsel()
        
        match_count = 0
        for row in attorneys:
            counsel_id = row[0]
            first_name = row[1] or ""
            last_name = row[2] or ""
            firm = row[11] or ""
            email = row[3] or ""
            
            # Search in name, firm, email
            full_name = f"{first_name} {last_name}".strip()
            searchable = f"{full_name} {firm} {email}".lower()
            if term and term not in searchable:
                continue
            
            match_count += 1
            
            # Build display label
            label = full_name
            if firm:
                label += f" ({firm})"
            
            # Create row frame
            row_frame = tk.Frame(scroll_frame)
            row_frame.pack(fill="x", padx=2, pady=1)
            
            # Button to load attorney (takes most space)
            tk.Button(
                row_frame,
                text=label,
                anchor="w",
                relief="flat",
                command=lambda cid=counsel_id: load_into_editor(cid)
            ).pack(side="left", fill="x", expand=True)
            
            # Small delete button
            tk.Button(
                row_frame,
                text="🗑",
                width=3,
                bg="#f44336",
                fg="white",
                command=lambda cid=counsel_id, n=full_name: delete_attorney_from_list(cid, n)
            ).pack(side="right", padx=2)
        
        if match_count == 0:
            tk.Label(scroll_frame, text="No attorneys found", fg="gray").pack(pady=20)
    
    def delete_attorney_from_list(counsel_id, name):
        """Delete attorney directly from list"""
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete attorney '{name}'?\n\nThis cannot be undone.",
            parent=win
        ):
            return
        
        delete_opposing_counsel(counsel_id)
        messagebox.showinfo("Deleted", f"Attorney '{name}' has been deleted.", parent=win)
        
        # Clear editor if this attorney was loaded
        if attorney_id_var.get() == counsel_id:
            clear_editor()
        
        populate_list()



    def view_associated_clients():
        """Show all clients associated with this attorney"""
        counsel_id = attorney_id_var.get()
        if counsel_id == -1:
            messagebox.showinfo("No Attorney Selected", "Please select an attorney first.", parent=win)
            return
        
        # Get attorney name
        attorney_name = f"{first_name_var.get()} {last_name_var.get()}"
        
        # Query clients with this opposing_counsel_id
        import sqlite3
        from modules.db import DB_PATH, get_variables
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM clients WHERE opposing_counsel_id = ?", (counsel_id,))
        client_rows = c.fetchall()
        conn.close()
        
        if not client_rows:
            messagebox.showinfo(
                "No Associated Clients",
                f"No clients are currently assigned to {attorney_name}.",
                parent=win
            )
            return
        
        # Create display window
        clients_win = tk.Toplevel(win)
        clients_win.title(f"Clients for {attorney_name}")
        clients_win.geometry("600x400")
        clients_win.grab_set()
        
        tk.Label(
            clients_win,
            text=f"Clients assigned to: {attorney_name}",
            font=("Arial", 12, "bold")
        ).pack(pady=10)
        
        tk.Label(
            clients_win,
            text=f"Total: {len(client_rows)} client(s)",
            font=("Arial", 10),
            fg="gray"
        ).pack(pady=5)
        
        # Scrollable list
        list_frame = tk.Frame(clients_win)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(list_frame)
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas)
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Build list
        for idx, (client_id,) in enumerate(client_rows, 1):
            vars_ = get_variables("client", client_id)
            matterid = vars_.get("matterid", "")
            firstname = vars_.get("firstname", "")
            lastname = vars_.get("lastname", "")
            
            name = f"{firstname} {lastname}".strip() or "(No Name)"
            label_text = f"{idx}. Client ID {client_id}"
            if matterid:
                label_text += f" - Matter: {matterid}"
            label_text += f" - {name}"
            
            tk.Label(scroll_frame, text=label_text, anchor="w").pack(anchor="w", padx=5, pady=2, fill="x")
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        tk.Button(clients_win, text="Close", command=clients_win.destroy, width=15).pack(pady=10)

    
    # --- Bottom Buttons ---
    bottom_frame = tk.Frame(win)
    bottom_frame.pack(fill="x", padx=5, pady=5)
    
    #tk.Button(bottom_frame, text="Close", command=win.destroy, width=15).pack(side="right", padx=5)
    
    # Connect search to list refresh
    search_var.trace_add("write", populate_list)
    
    # CRITICAL: Initial population
    populate_list()
    
    # Bottom buttons
    bottom_frame = tk.Frame(win)
    bottom_frame.pack(fill="x", padx=5, pady=5)
    
    tk.Button(bottom_frame, text="Close", command=win.destroy, width=15).pack(side="right", padx=5)
    
    win.mainloop()  # This should be the LAST line