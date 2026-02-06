### **HOWTOUSE.md**  

# LegalDocGenerator – How To Use (v0.0.4)

This guide provides a detailed walkthrough of all features, with examples and explanations.

---

## 1. Launching the App
From the project root:
```bash
python run.py
bash```
Automatically creates a virtual environment if missing

Installs dependencies from requirements.txt

Launches the GUI (Tkinter)

No need to manually activate the venv

## 2. Client Management
Add new clients via Main -> Add Client

Edit existing clients via Main -> Update Client

Export all clients to Excel using Main -> Export Clients

## 3. Variable Management
Variables store client-specific information (e.g., client_name, case_type)

Manage via:

Admin -> Edit Variables (bulk)

Client update dialogs (per client)

Variable types:

Standard: single value

Concatenated (_combo): combination of other variables

Derived (_derived): computed based on conditions (gender, pluralization, grammar)

Dynamic: imported from dynamicpleadingresponses.xlsx using <<>> or [[]]

### 3a. Concatenated Variables
Combine multiple existing variables with separators

Example:

clientfirstname + " " + clientlastname → clientfullname_combo

Built via editconcatvariable.py editor

### 3b. Derived Variables
Handle grammar and conditional text

Examples:

Pluralization: @standard-s_plural@ → "s" or ""

Gendered pronouns: @he_she_they@, @his_her_their@, @him_her_them@

Hard-coded; templates should use these brackets and @ symbols

### 3c. Dynamic Variables
Defined in dynamicpleadingresponses.xlsx

Use <<variable>> in templates

TRUE / FALSE mode (cell D1 of sheet):

TRUE: one-time selection for entire doc

FALSE: repeated selection until user marks "last paragraph"

Example:

In the District Court of <<venue>>, Nebraska
User selects "Lancaster County" → inserted into document

[[]] works like {{}} but supports numbered lists

## 4. Document Generation
Click Generate Documents

Select clients (all or individually)

Select templates to generate

For missing variables:

Prompted to input per client

Or define new variables dynamically

Generated documents saved to output_documents/ (ignored by git)

## 5. Template & Variable Syntax

Standard Variables
{{client_name}}, {{case_type}}, {{court_date}}
Grammar Variables
Use parentheses () and @ symbols:

(@clients@) state(@standard-s_plural@) that (@he_she_they@) (@is_are@) ready to vindicate (@his_her_their@) rights, support(@plural_s@) (@him_her_them@)
Renders according to client gender and plurality

List of grammar tokens:

Token	Output Example
@clients@	"client"/"clients"
@standard-s_plural@	"s"/""
@he_she_they@	"he"/"she"/"they"
@is_are@	"is"/"are"
@his_her_their@	"his"/"her"/"their"
@him_her_them@	"him"/"her"/"them"
@plural_s@	"s"/""
Concatenated Variables
Defined with _combo

Prompted for component variables and separator

Derived Variables
Defined with _derived

Automatically computed from database or rules

Dynamic Variables
Defined in Excel with <<>> or [[]]

TRUE: single-use, FALSE: numbered list, repeat until last paragraph selected

## 6. Examples

**Example Template:**

Dated this {{currentday}} of {{currentmonth}}, {{year}}.

Dear {{clientfullname_combo}},

My (@clients@) state(@standard-s_plural@) that (@he_she_they@) (@is_are@) ready to vindicate (@his_her_their@) rights.

In the District Court of <<venue>>, Nebraska.

Rendered for client John Doe (male):

Dated this 2nd of February, 2026.

Dear John Doe,

My client states that he is ready to vindicate his rights.

In the District Court of Lancaster County, Nebraska.

## 7. Notes
Rough edges exist; rapid iteration expected

Focused on correctness of variable substitution and document generation

Output documents are ignored in Git; do not commit them
