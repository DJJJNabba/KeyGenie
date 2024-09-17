Instructions for AIKeyboard

Thank you for using AIKeyboard! This application allows you to interact with OpenAI's language models directly from your keyboard.

---

Getting Started

1. Ensure Python 3 is Installed

   - Check if Python is installed:
     - Open Command Prompt (Windows) or Terminal (Mac/Linux).
     - Type python --version and press Enter.
     - If Python 3 is installed, it will display the version number (e.g., Python 3.8.5).
   
   - If Python is not installed:
     - Download Python 3 from https://www.python.org/downloads/.
     - Install Python by following the instructions on the website.

2. Run the Application

   - First Run:
     - Navigate to the folder containing run.py.
     - Double-click run.py to run it.
     - Alternatively, you can run it from the command line:
       - Open Command Prompt or Terminal.
       - Navigate to your project folder using cd commands.
       - Run python run.py.
   
   - First Time Setup:
     - On the first run, the application will automatically install all the necessary Python modules.
     - Please be patient as this may take a few minutes.
     - A file named first_run.txt will be created inside the brain folder after setup is complete.

3. Provide Your OpenAI API Key

   - After running the application, you'll find an AIKeyboard icon in your system tray (near the clock on your taskbar).
   
   - For Windows Users:
     - Look for a small icon resembling a keyboard or AI assistant.
     - You might need to click on the "Show hidden icons" arrow to see it.
   
   - Access Settings:
     - Right-click the AIKeyboard icon and select "Open Settings".
   
   - Enter API Key:
     - In the settings window, enter your OpenAI API key in the "API Key" field.
     - Click "Save API Key" to save your key.
   
   - Note: You need a valid OpenAI API key to use this application. Sign up at https://platform.openai.com/signup/ if you don't have one.

4. Configure Settings (Optional)

   - Model Selection:
     - Choose which OpenAI model to use from the dropdown menu.
   
   - Custom Instructions:
     - Add any custom instructions for the AI in the provided text area.
   
   - Keybinds:
     - Set the keys you use to activate the AI.
     - Prompt Keybind: Starts a new AI prompt.
     - Completion Keybind: Asks the AI to continue your text.
   
   - Additional Settings:
     - Temperature: Controls the randomness of the AI's responses.
     - Max Tokens: Limits the length of the AI's responses.
     - Auto-Type: Enable or disable automatic typing of AI responses.
     - Typing Speed: Adjust how fast the AI types back.
     - Letter by Letter Typing: Choose whether the AI types letter by letter or in chunks.
     - Play TTS: Enable text-to-speech to have the AI speak responses.
     - TTS Rate: Adjust the speaking rate of the AI.
   
   - Save Settings:
     - Don't forget to click "Save Settings" after making changes.

5. Using AIKeyboard

   - Activate Prompt Mode:
     - Press the "Prompt Keybind" (default is right shift) to start capturing your input.
     - Type your prompt, and press the keybind again to stop capturing.
     - The AI will process your input and type out the response automatically.
   
   - Activate Completion Mode:
     - Press the "Completion Keybind" (default is right ctrl) to start capturing text to be completed.
     - Type the text you want the AI to continue, and press the keybind again to stop capturing.
     - The AI will generate a continuation of your text.
   
   - Stopping the AI Typing or TTS:
     - To stop the AI from typing or speaking, press any key on your keyboard.

6. Exiting the Application

   - To exit AIKeyboard, right-click the system tray icon and select "Quit".

---

Additional Notes

- Python Version:
  - Ensure you have Python 3 installed. The application may not work correctly with older versions.
  
- Dependencies:
  - The application will automatically install necessary Python modules on the first run. Although you may need to restart the program for changes to take effect.
  
- Privacy:
  - Your OpenAI API key is stored locally in your user directory in a folder named privateVariables.
  
- Support:
  - If you encounter any issues, please reach out my discord - @djjj.

---

Troubleshooting

- Application Doesn't Start:
  - Make sure you have Python 3 installed and added to your system's PATH.
  - Ensure all files are in the correct folders as specified in the folder structure.

- Cannot Find AIKeyboard Icon:
  - It might be hidden in the system tray. Click on the arrow to show hidden icons.

- Modules Not Installed:
  - If the necessary Python modules are not installed, you can manually install them by running:
    pip install -r requirements.txt
    Note: You may need to create a requirements.txt file listing all dependencies.

- Permission Issues:
  - Run the application as an administrator if you encounter permission errors.

---

Uninstallation

- To Uninstall the Application:
  - Delete the project folder.
  - Remove any shortcuts or startup entries if you enabled them in settings.
  - Delete the privateVariables folder located in your user directory to remove saved settings and API keys.

---

Thank You for Using AIKeyboard!
