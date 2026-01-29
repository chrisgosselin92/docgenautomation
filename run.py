#!/usr/bin/env python3
import os
import subprocess
import sys
import platform
import shutil

VENV_DIR = "venv"

# Detect OS and Linux distro
def get_linux_distro():
    try:
        import distro  # requires 'distro' package
        return distro.id().lower()
    except ImportError:
        # fallback if distro package not installed
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        return line.strip().split("=")[1].strip('"').lower()
        except Exception:
            return "linux"
    return "linux"

# Check Tkinter availability
def check_tkinter():
    try:
        import tkinter  # noqa: F401
        return True
    except ImportError:
        return False

# Install system packages if Tkinter missing
def install_system_packages():
    if check_tkinter():
        print("Tkinter detected. Skipping system package install.")
        return

    system = platform.system().lower()
    if system == "linux":
        distro_name = get_linux_distro()
        print(f"Detected Linux distro: {distro_name}")

        if distro_name in ["ubuntu", "debian"]:
            print("Installing system packages for Tkinter: sudo apt install python3-tk")
            print("If prompted, enter your password and confirm installation.")
        elif distro_name in ["fedora"]:
            print("Installing system packages for Tkinter: sudo dnf install python3-tkinter")
        elif distro_name in ["arch", "manjaro", "cachyos"]:
            print("Detected Arch-based distro. Tkinter must be installed manually:")
            print("  sudo pacman -S tk python")
        else:
            print("Unknown Linux distro, ensure Tkinter is installed manually.")
    elif system == "darwin":
        print("macOS detected. Tkinter should be installed via Homebrew if missing:")
        print("  brew install python-tk")
    elif system == "windows":
        print("Windows detected. Tkinter is included with standard Python.")
    else:
        print("Unknown OS. Ensure Tkinter is installed.")

# Ensure virtual environment exists and Python dependencies installed
def ensure_venv():
    if platform.system() == "Windows":
        python_bin = os.path.join(VENV_DIR, "Scripts", "python.exe")
        pip_bin = os.path.join(VENV_DIR, "Scripts", "pip.exe")
    else:
        python_bin = os.path.join(VENV_DIR, "bin", "python")
        pip_bin = os.path.join(VENV_DIR, "bin", "pip")

    # 1. Create virtual environment if missing
    if not os.path.exists(VENV_DIR):
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)

    # 2. Upgrade pip
    subprocess.run([python_bin, "-m", "pip", "install", "--upgrade", "pip"], check=True)

    # 3. Install Python dependencies
    if not os.path.exists("requirements.txt"):
        print("requirements.txt not found. Exiting.")
        sys.exit(1)

    print("Installing Python dependencies from requirements.txt...")
    subprocess.run([pip_bin, "install", "-r", "requirements.txt"], check=True)

    return python_bin

def main():
    install_system_packages()
    python_bin = ensure_venv()

    # Add project root to path
    sys.path.insert(0, os.path.abspath("."))

    # Launch main application
    from modules.main import main as app_main
    app_main()

if __name__ == "__main__":
    main()
