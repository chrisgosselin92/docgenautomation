# LegalDocGenerator (v0.0.4)

**A local desktop application for managing legal clients, variables, and generating document templates from stored data.**

LegalDocGenerator is a prototype for law office workflows, designed to:
- Track clients and client-specific data
- Manage variables for document automation
- Generate Word documents from pre-defined templates using stored client information

This project is intended for local desktop use and does **not** require a web server.

---

## Features (Overview)
- Add, list, and update clients (SQLite database)
- Manage client-specific variables
- Bulk-create variables across multiple clients
- Import variables automatically from .docx templates
- Generate documents using templates, with support for:
  - Dates
  - Concatenated variables
  - Derived variables (grammar/gender/pluralization)
  - Dynamic variables from Excel sheets
- Tkinter-based GUI (cross-platform)

---

## Project Structure

```text
docgenautomation/
├── data/
│   └── clients.db
├── modules/
│   ├── main.py                 # Main GUI entry point
│   ├── db.py                   # Database queries and setup
│   ├── dbsync.py               # Sync variables with intake.xlsx
│   ├── admin.py                 # Admin DB modifications
│   ├── admin_attorney.py       # Admin for attorney users
│   ├── docgen.py               # Document generation
│   ├── editconcatvariable.py   # Concatenated variable editor
│   ├── intake.py               # Excel intake and client import
│   ├── listclients.py          # Export client list to Excel
│   ├── updateclient.py         # Bulk client variable updates
│   ├── variables.py            # Bulk variable utilities
│   ├── bracket_variables.py    # Grammar / bracket variable logic
│   ├── grammar.py              # Derived variable / grammar adjustments
│   └── template_builder.py     # Dynamic variables & template processing
├── templates/                  # Word templates (.docx)
├── tempstuff/                  # Temporary scripts
├── run.py                      # Bootstraps venv, installs dependencies, runs GUI
├── requirements.txt
├── README.md
├── HOWTOUSE.md
├── launch.sh
├── dynamicpleadingresponses.xlsx
├── intake.xlsx
└── attorney_input.xlsx
```


## Quick Start

Clone the repository:

`git clone https://github.com/chrisgosselin92/docgenautomation.git`
`cd docgenautomation`


Launch the app (automatic venv creation and dependency installation):

`python run.py`

Place .docx templates in the templates/ folder.

Begin managing clients, variables, and generating documents.

## Examples

Example template placeholders:

{{client_name}}

{{case_type}}

{{court_date}}

Grammar variable example:

My (@clients@) state(@standard-s_plural@) that (@he_she_they@) (@is_are@) ready to vindicate (@his_her_their@) rights, and the evidence support(@plural_s@) (@him_her_them@).

Renders as:

Singular Male: "My client states that he is ready to vindicate his rights, and the evidence supports him."

Singular Female: "My client states that she is ready to vindicate her rights, and the evidence supports her."

Plural: "My clients state that they are ready to vindicate their rights, and the evidence supports them."

Dynamic variable example:

<<venue>> pulls from dynamicpleadingresponses.xlsx (Column A = choices, Column B = output text).

## Status

Version 0.0.4 — initial working prototype

Expect rough edges and rapid iteration

Core architecture in place

## License

Private / internal use.
