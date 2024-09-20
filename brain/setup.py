import os
import shutil
import sys
import subprocess
import importlib.util
import ctypes
from ctypes import wintypes
import json

# Define required modules for backgroundai.py
required_modules = [
    "keyboard",
    "openai",
    "pystray",
    "Pillow",   # for handling images
    "PyQt5",    # for GUI (Qt-based settings menu)
    "pywin32",  # Includes win32com.client and pythoncom for Windows API usage
]

# Install required modules if they are not already installed
def install_missing_modules():
    for module in required_modules:
        if importlib.util.find_spec(module) is None:
            print(f"Module '{module}' is not installed. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])
        else:
            print(f"Module '{module}' is already installed.")

# Function to run the pywin32_postinstall script manually
def run_pywin32_postinstall():
    try:
        pywin32_postinstall_path = os.path.join(os.path.dirname(sys.executable), 'Scripts', 'pywin32_postinstall.py')
        if os.path.exists(pywin32_postinstall_path):
            print("Running pywin32 post-install script...")
            subprocess.check_call([sys.executable, pywin32_postinstall_path, "-install"])
            print("pywin32 post-install completed.")
        else:
            print("Could not find pywin32_postinstall script.")
    except Exception as e:
        print(f"Error running pywin32_postinstall: {e}")

# Run post-install for pywin32 if required
def ensure_pywin32_postinstall():
    try:
        # Import win32com.client and pythoncom to ensure they are set up
        import win32com.client
        import pythoncom
        print("win32com and pythoncom are correctly set up.")
    except ImportError:
        # If the imports fail, run the pywin32 post-install
        run_pywin32_postinstall()

# Ensure that pywin32 is set up before proceeding
install_missing_modules()
ensure_pywin32_postinstall()

# Now, import win32com.client after ensuring it is installed
from win32com.client import Dispatch

# Get the directory where the current setup script is located
script_directory = os.path.dirname(os.path.abspath(__file__))

# Define paths dynamically
user_profile = os.getenv('USERPROFILE')  # Dynamically get user's home directory
appdata_folder = os.getenv('APPDATA')
startup_folder = os.path.join(appdata_folder, r'Microsoft\Windows\Start Menu\Programs\Startup')

# Function to find the user's desktop folder path using Windows API
def get_desktop_path():
    CSIDL_DESKTOP = 0  # CSIDL_DESKTOP is the constant for desktop
    SHGFP_TYPE_CURRENT = 0  # Constant for getting the current path

    buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, SHGFP_TYPE_CURRENT, buf)
    return buf.value

# Use Windows API to find the desktop path
desktop_folder = get_desktop_path()

# Define shortcut details
shortcut_name = "AIKeyboard.lnk"
background_script_path = os.path.join(script_directory, "backgroundai.py")  # Path to backgroundai.py
start_in_directory = script_directory  # Start in the directory where the script is located
icon_path = os.path.join(script_directory, "write.ico")  # Using write.ico for the icon

# Function to find pythonw.exe based on the current Python interpreter location
def find_pythonw():
    python_dir = os.path.dirname(sys.executable)  # Get the directory of the current Python interpreter
    pythonw_path = os.path.join(python_dir, 'pythonw.exe')  # pythonw.exe is usually in the same directory
    if os.path.exists(pythonw_path):
        return pythonw_path
    else:
        return None

# Create a shortcut at the specified path
def create_shortcut(shortcut_path, target, start_in, icon):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target
    shortcut.Arguments = f'"{background_script_path}"'  # Script to run
    shortcut.WorkingDirectory = start_in
    shortcut.IconLocation = f"{icon}, 0"  # Set icon with index 0 for the .ico file
    shortcut.save()

# Check for pythonw.exe and ensure it's found
pythonw_executable = find_pythonw()
if pythonw_executable is None:
    print("Could not find pythonw.exe. Please ensure Python is installed.")
    sys.exit(1)

# Full paths for shortcuts in the startup folder and on the desktop
startup_shortcut = os.path.join(startup_folder, shortcut_name)
desktop_shortcut = os.path.join(desktop_folder, shortcut_name)

# Check if the shortcut already exists in the startup folder
if not os.path.exists(startup_shortcut):
    create_shortcut(startup_shortcut, pythonw_executable, start_in_directory, icon_path)
    print(f"Shortcut created in Startup folder: {startup_shortcut}")
else:
    print(f"Shortcut already exists in Startup folder: {startup_shortcut}")

# Create a shortcut on the desktop if it doesn't exist
if not os.path.exists(desktop_shortcut):
    create_shortcut(desktop_shortcut, pythonw_executable, start_in_directory, icon_path)
    print(f"Shortcut created on Desktop: {desktop_shortcut}")
else:
    print(f"Shortcut already exists on Desktop: {desktop_shortcut}")

# ------------------ Added Code to Ensure Files Exist ------------------

# Define the paths for the private variables and files
PRIVATE_FOLDER = os.path.join(os.path.expanduser("~"), "privateVariables")
API_KEY_FILE = os.path.join(PRIVATE_FOLDER, "apikey.txt")
# KEYBINDS_FILE = os.path.join(PRIVATE_FOLDER, "keybinds.txt")
# MODEL_FILE = os.path.join(PRIVATE_FOLDER, "model.txt")
SETTINGS_FILE = os.path.join(PRIVATE_FOLDER, "settings.json")
# CUSTOM_INSTRUCTIONS_FILE = os.path.join(PRIVATE_FOLDER, "custom_instructions.txt")

# Default values
DEFAULT_KEYBINDS = {
    "prompt": "right shift",
    "completion": "right ctrl"
}

DEFAULT_MODEL = "gpt-3.5-turbo"
with open("defaultSettings.json", "r") as file: DEFAULT_SETTINGS = json.load(file)

# Ensure the private variables folder exists
if not os.path.exists(PRIVATE_FOLDER):
    os.makedirs(PRIVATE_FOLDER)
    print(f"Created private variables folder at {PRIVATE_FOLDER}")

# Ensure API_KEY_FILE exists
if not os.path.exists(API_KEY_FILE):
    with open(API_KEY_FILE, 'w') as f:
        f.write('')
    print(f"Created API key file at {API_KEY_FILE}")

# Ensure SETTINGS_FILE exists
if not os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(DEFAULT_SETTINGS,file)
    print(f"Created settings file at {SETTINGS_FILE}")

# ----------------------------------------------------------------------

# Run the background script with pythonw.exe
print("Running backgroundai.py with pythonw.exe...")
subprocess.Popen([pythonw_executable, background_script_path])
