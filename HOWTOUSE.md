# DocGenAutomation – User Guide

## Version v0.0.3

---

## 0. Install
If you have not installed the file yet, please view README.md first.  It is designed to run by launching launch.sh and should have all installers, dependencies, scripts, etc. for your operating system.

## 1. Client Intake via Excel

1. Open the provided `clients.xlsx` file.
2. Navigate to the IntakeSheet (red tab)
3. Entries in Column B correspond to variables in the system, e.g.:
   - `clientfirstname`
   - `clientlastname`
   - `role` (plaintiff/defendant)
   - Other custom variables.
4. Fill in client information adjacent to the variable in column C and save the file. Close the file.

**Tips:**
- Keep variable names consistent with your system.
- Do not use underscores if unsure — your admin UI can handle naming safely.

---

## 2. Updating Clients

1. Launch the application.
2. Go to **Update/Delete Client**.
3. Select your desired client.
4. Then, search or scroll to locate a variable.
5. Edit its value, type, category, or name.
6. To delete a client, check the box on the bottom titled “Delete Client.”.
7. Click **Save Changes** and confirm.

---

## 3. Updating Variables

1. Launch the application.
2. Go to **Admin Panel → Variable Administration**.
3. Search or scroll to locate a variable.
4. Edit its value, type, category, or name.
5. For deletions, check the box in the “Delete?” column.
6. Click **Save Changes** and confirm.

---

## 4. Creating Relationships & Derived Variables

1. In the Admin Panel, click **Derived Variable Builder**.
2. Select the **first variable** (e.g., `clientfirstname`).
3. Optionally select a **second variable** (e.g., `clientlastname`).
4. Enter a **separator** (space `" "` by default).
5. Choose a **role** (`plaintiff`, `defendant`, etc.).
6. Enter a **name for the new variable** (e.g., `plaintiffcaption`).
7. Click **Create** — the system will store this derived variable.
8. Preview in the admin UI to verify.

Derived variables automatically combine base variables for each client. You can now use them in document generation.

---

## 5. Document Generation

1. Go to **Generate Documents** in the main UI.
2. Select a client or set of clients.
3. Choose a template Word document (`.docx`) or Outlook draft.
4. The system replaces all variables with client-specific values:
   - Standard variables (e.g., `clientfirstname`)  
   - Derived variables (e.g., `plaintiffcaption`)  
5. Output is a Word file or Outlook draft ready for review.

---

## 6. Tips & Best Practices

- Use descriptive variable names for clarity.
- Group related variables under a category in the admin panel.
- When creating derived variables:
  - Keep role assignments consistent.
  - Use the preview table to verify correctness.
- Always back up `clients.xlsx` before bulk changes.
- Document templates should match variable names exactly.

---

## 7. Troubleshooting

- **Variable missing in preview:** Ensure it exists in the admin panel.
- **Derived variable not updating:** Check base variables are filled for the client.
- **Document generation fails:** Confirm template file is `.docx` and contains matching placeholders.

---

## 8. Future Notes

- Relationships could be extended to more complex cases (e.g., multiple defendants).
- Derived variables can be nested (a derived variable can be a base for another derived variable).
