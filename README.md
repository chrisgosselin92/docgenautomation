# LegalDocGenerator (v0.0.4)
**A local desktop application for managing legal clients, variables, and generating document templates from stored data.**

This is an early working prototype focused on:
·	Client management
·	Variable management (per client and bulk)
·	Template-driven document generation (in progress)
·	Importing variables from document templates

**Features (Current)**
·	Add and list clients (stored in SQLite)
·	Manage client-specific variables
·	Bulk-create variables across clients
·	Import variables automatically from .docx templates
·	Export client list to Excel
·	Generate documents from templates (early version)
·	Tkinter-based GUI (no web dependencies)

**Project Structure**

```text
docgenautomation/
├── data/
│   └── clients.db
├── modules/
│   └── main.py                # Main GUI entry point
│   └── db.py                  # Database setup and queries
│   └── dbsync.py              # One way sync of db variables, variable types, descriptions onto the intake.xlsx
│   └── admin.py               # For modifying the db
│   └── docgen.py              # Document generation logic
│   └── intake.py              # For launching excel (if no client there) or saving from excel into db
│   └── variables.py           # Bulk variable utilities
│   └── updateclient.py        # Modifying clients by variable checkbox selection
│   └── listclients.py         # Export clients to Excel
├── run.py                 # Bootstraps venv, installs deps, runs app
├── requirements.txt
├── README.md
├── templates/             # Word templates (.docx); tree won't be updated.
└── venv/                  # Virtual environment (ignored by git)
```

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
·	Client Variables are defined using double braces:
{{client_name}}
{{case_type}}
{{court_date}}

·	Grammar Variables are defined using standard parentheses **(** and **@** symbols as delimeters:

E.g.) My (@clients@) state(@standard-s_plural@) that (@he_she_they@) (@is_are@) ready to vindicate (@his_her_their@) rights, and the evidence support(@plural_s@) (@him_her_them@).
- Singular Male: "My client states that he is ready to vindicate his rights, and the evidence supports him."
- Singular Female: "My client states that she is ready to vindicate her rights, and the evidence supports her."
- Plural: "My clients state that they are ready to vindicate their rights, and the evidence supports them."

This may take some getting used to.  Generating a few documents and seeing a few grammatical errors for sex/plurals/possessives will be instructive on how to fix your 


·	Dynamic Variables are set in the excel document called dynamicpleadingresponses.xlsx.  The name of the sheet should be used for the variable.  They have two functions (more on that in a moment).  Put "<<" and ">>" for variables with matching names to the sheet  Here's an example for how to use them:

- The sheet that came with this repository has <<venue>> as a variable.  These are all the counties in Nebraska.  Column A is a the selections visible to the user and column B is the output that should enter the document where <<venue>> was.  E.g. "In the District Court of <<venue>>, Nebraska" will return "In the District Court for **Lancaster County**, Nebraska." (it will not come back bold, that is for emphasis.)
- The excel has a sheet which is also <<Answer>> as variable.  These are standard responses in my practice.  An output in a document may be: "[[defendant_plural]] admit[[defendant_plural_s]] to Paragraph #." as part of a numbered list.  The [[ ]] variables **are the exact same as the {{}} variables** but you must use brackets instead of braces.  

In cell D1, if you answer "TRUE" for that variable, it will be the same one used throughout the document you generate.  If you use "FALSE", it should create a numbered list, placing this variable over and over until the user selects "Last paragraph for this variable."  This will allow you to (for example) answer a Complaint paragraph by paragraph.  

·	Variables may be tagged for special purposes:
This is limited right now to "_upper", "_combo", and "_derived".  Below are examples/explanations of all three.
- <<venue_upper>> should return the variable as ALL CAPS, e.g. "IN THE DISTRICT COURT OF **LANCASTER COUNTY**, NEBRASKA." (Bolded for emphasis, not how it's returned in the document)

- _combo should prompt the user to create variable from other previously created variables.  E.g. clientfirstname and clientlastname could be combined (with a spacer) to form "clientfullname".  You would do this by defining whatever you'd like as the variable name, then use the tag.  E.g. {{clientfullname_combo}} will prompt the user to create a variable, which is then assigned to that client in the database.


* If a variable is missing for a client, the system will prompt or mark it as not defined.*

## Status
**This is v0.0.4 — an initial working prototype.**
Expect:
·	Rough edges
·	Rapid iteration
·	Breaking changes
The core architecture is now in place.

## License
Private / internal use (license to be defined).

## Notes
Built incrementally with an emphasis on correctness over polish.

