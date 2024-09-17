import subprocess
import sys
import os

# Path to the first run indicator file in the 'brain' folder
brain_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brain')
first_run_file = os.path.join(brain_folder, "first_run.txt")

def get_pythonw_path():
    """Find pythonw.exe in the current Python installation directory."""
    python_dir = os.path.dirname(sys.executable)  # Get the directory of the current Python interpreter
    pythonw_path = os.path.join(python_dir, 'pythonw.exe')  # Path to pythonw.exe
    if os.path.exists(pythonw_path):
        return pythonw_path
    else:
        return None  # Return None if pythonw.exe is not found

def relaunch_with_pythonw():
    """Relaunch the script using pythonw.exe to avoid showing the terminal window."""
    pythonw_executable = get_pythonw_path()
    if pythonw_executable:
        # Relaunch using pythonw.exe
        subprocess.Popen([pythonw_executable, __file__], close_fds=True)
        sys.exit(0)  # Exit the current instance to prevent double execution

def run_script(script_name, use_pythonw=True):
    """Run the given Python script located in the 'brain' folder."""
    try:
        script_path = os.path.join(brain_folder, script_name)
        python_executable = get_pythonw_path() if use_pythonw else sys.executable
        result = subprocess.run([python_executable, script_path], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def main():
    # Check if the script is already being run by pythonw.exe
    if "pythonw" not in sys.executable:
        relaunch_with_pythonw()  # Relaunch using pythonw.exe if it is not already running with it

    if not os.path.exists(first_run_file):
        # First time running the script
        print("First run detected. Running setup.py...")

        # Run setup.py and retry if it fails
        if not run_script('setup.py', use_pythonw=False):  # Use python.exe for setup
            print("setup.py failed. Retrying...")
            if not run_script('setup.py', use_pythonw=False):
                print("setup.py failed twice. Exiting.")
                return

        # Setup completed, create first_run_file in 'brain' folder
        with open(first_run_file, 'w') as f:
            f.write("Setup completed")

        # Now run backgroundai.py using pythonw.exe
        print("Running backgroundai.py...")
        run_script('backgroundai.py', use_pythonw=True)

    else:
        # Not the first run, just run backgroundai.py using pythonw.exe
        print("Not the first run. Running backgroundai.py...")
        run_script('backgroundai.py', use_pythonw=True)

if __name__ == "__main__":
    main()
