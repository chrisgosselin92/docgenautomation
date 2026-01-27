# LegalDocGenerator (v0.0.1)
**A local desktop application for managing legal clients, variables, and generating document templates from stored data.**

This is an early working prototype focused on:
·	Client management
·	Variable management (per client and bulk)
·	Template-driven document generation (in progress)
·	Importing variables from document templates
Features (Current)
·	Add and list clients (stored in SQLite)
·	Manage client-specific variables
·	Bulk-create variables across clients
·	Import variables automatically from .docx templates
·	Export client list to Excel
·	Generate documents from templates (early version)
·	Tkinter-based GUI (no web dependencies)
Project Structure
docgenautomation/
├── main.py                # Main GUI entry point
├── run.py                 # Bootstraps venv, installs deps, runs app
├── db.py                  # Database setup and queries
├── docgen.py              # Document generation logic
├── variables.py           # Bulk variable utilities
├── importvariables.py     # Import variables from templates
├── listclients.py         # Export clients to Excel
├── updateclient.py        # Client update helpers
├── requirements.txt
├── README.md
├── data/
│   └── clients.db
├── templates/             # Word templates (.docx)
└── venv/                  # Virtual environment (ignored by git)

## Requirements
·	Python 3.11+
·	Linux / macOS / Windows
·	Internet access (first run only, for dependencies)
Installation & Usage
From the project root:
python run.py

## What this does:
1.	Creates a virtual environment (venv) if missing
2.	Installs dependencies from requirements.txt
3.	Launches the GUI
No manual activation of the virtual environment is required.
### Templates & Variables
·	Templates must be .docx files placed in the templates/ folder
·	Variables are defined using double braces:
{{client_name}}
{{case_type}}
{{court_date}}

* If a variable is missing for a client, the system will prompt or mark it as not defined.*

## Status
**This is v0.0.1 — an initial working prototype.**
Expect:
·	Rough edges
·	Rapid iteration
·	Breaking changes
The core architecture is now in place.

## License
Private / internal use (license to be defined).

## Notes
Built incrementally with an emphasis on correctness over polish.

