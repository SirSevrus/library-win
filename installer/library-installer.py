import os
import platform
import requests
import shutil
import winshell
import sys
from win32com.client import Dispatch
import ctypes

# Global variables
downloaded_file = None
logs = []

# Logger function for the terminal-like output
def log_message(message):
    logs.append(message)
    print(message)

# Function to check for admin privileges
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

# Function to request admin privileges
def run_as_admin():
    script = sys.argv[0]
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script, None, 1)

# Function to get system architecture
def get_architecture():
    return "x86_64" if platform.architecture()[0] == "64bit" else "x86"

# Function to fetch the latest release URL
def get_latest_release_url():
    api_url = "https://api.github.com/repos/sirsevrus/library-win/releases/latest"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        arch = get_architecture()
        for asset in data.get("assets", []):
            if f"Library-{arch}.exe" in asset["name"]:
                return asset["browser_download_url"]
    raise Exception("Could not fetch the latest release URL.")

# Function to create a shortcut
def make_shortcut(exe_path):
    try:
        desktop_path = winshell.desktop()
        shortcut_path = os.path.join(desktop_path, 'Library.lnk')
        exe_dir_path = os.path.dirname(exe_path)
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = exe_dir_path
        shortcut.IconLocation = exe_path
        shortcut.save()
        log_message("Shortcut created on the desktop.")
    except Exception as e:
        log_message(f"Error creating shortcut: {e}")

# Function to handle the installation process
def install_application():
    global downloaded_file
    try:
        log_message("Starting installation process...")
        # Determine the installation directory
        installation_dir = input("Enter the installation directory (default: Program Files/Library): ") or os.path.join(os.environ.get("ProgramFiles"), "Library")
        if not os.path.exists(installation_dir):
            os.makedirs(installation_dir)
            log_message(f"Created installation directory: {installation_dir}")

        # Move the downloaded file to the installation directory
        dest_path = os.path.join(installation_dir, os.path.basename(downloaded_file))
        shutil.move(downloaded_file, dest_path)
        log_message(f"Moved file to: {dest_path}")

        # Create shortcut
        make_shortcut(dest_path)
        log_message("Installation complete.")
    except Exception as e:
        log_message(f"Installation failed: {e}")

# Function to download the application
def download_application():
    global downloaded_file
    try:
        log_message("Fetching the latest release URL...")
        url = get_latest_release_url()
        filename = os.path.join(os.getcwd(), url.split("/")[-1])
        downloaded_file = filename
        response = requests.get(url, stream=True)

        total_size = int(response.headers.get("content-length", 0))
        downloaded_size = 0
        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    progress = (downloaded_size / total_size) * 100
                    print(f"Downloading... {progress:.2f}% complete", end="\r")

        log_message("\nDownload completed successfully.")
        install_application()  # Start installation after download
    except Exception as e:
        log_message(f"Download failed: {e}")

# Main function to handle the process
def main():
    if not is_admin():
        print("This script requires administrative privileges. Please allow the prompt for admin access.")
        run_as_admin()  # Try to run the script as administrator
        sys.exit(0)  # Exit the current instance

    try:
        log_message("Starting the Library Installer...")
        download_application()  # Start the download process
        input()
    except Exception as e:
        log_message(f"Error: {e}")

if __name__ == "__main__":
    main()
