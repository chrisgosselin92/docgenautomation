import os
import subprocess
import sys
import platform

VENV_DIR = "venv"

# Determine paths based on OS
if platform.system() == "Windows":
    PYTHON_BIN = os.path.join(VENV_DIR, "Scripts", "python.exe")
    PIP_BIN = os.path.join(VENV_DIR, "Scripts", "pip.exe")
else:
    PYTHON_BIN = os.path.join(VENV_DIR, "bin", "python")
    PIP_BIN = os.path.join(VENV_DIR, "bin", "pip")

# 1. Create virtual environment if it doesn't exist
if not os.path.exists(VENV_DIR):
    print("Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)

# 2. Upgrade pip inside the venv
subprocess.run([PYTHON_BIN, "-m", "pip", "install", "--upgrade", "pip"], check=True)

# 3. Install dependencies
print("Installing dependencies from requirements.txt...")
subprocess.run([PIP_BIN, "install", "-r", "requirements.txt"], check=True)

# 4. Run the main program
subprocess.run([PYTHON_BIN, "main.py"], check=True)
