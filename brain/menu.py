import os
import shutil
import sys
import json
import ctypes
import copy
from threading import Event
from PyQt5.QtGui import QCloseEvent, QIcon, QPixmap, QFont, QPainter, QColor, QFont, QFontDatabase
import keyboard
from ctypes import wintypes
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
                             QVBoxLayout, QHBoxLayout, QSlider, QCheckBox, QComboBox, QMessageBox,
                             QScrollArea, QDialog)
from PyQt5.QtCore import Qt
from win32com.client import Dispatch

# File paths for saving settings
PRIVATE_FOLDER = os.path.join(os.path.expanduser("~"), "privateVariables")
API_KEY_FILE = os.path.join(PRIVATE_FOLDER, "apikey.txt")
SETTINGS_FILE = os.path.join(PRIVATE_FOLDER, "settings.json")

# Default keybinds and settings
DEFAULT_MODEL = "gpt-4o-mini-2024-07-18"
DEFAULT_SETTINGS = {
    "temperature": 1.0,
    "max_tokens": 256,
    "auto_type": True,
    "typing_speed_wpm": 200,
    "letter_by_letter": True,  # Default to letter-by-letter typing
    "play_tts": False,         # Default to not playing TTS
    "tts_rate": 0,             # Default TTS rate
    "model": "gpt-4o-mini-2024-07-18",
    "keybinds" : {
        "prompt" : "right shift",
        "completion" : "right ctrl",
    },
    "custom_instructions": "",
}

# Startup shortcut paths
APPDATA_FOLDER = os.getenv('APPDATA')
STARTUP_SHORTCUT_PATH = os.path.join(APPDATA_FOLDER, r'Microsoft\Windows\Start Menu\Programs\Startup', 'AIKeyboard.lnk')

model_ids = [
            # Chat models
            'gpt-4',
            'gpt-4-0613',
            'gpt-4-1106-preview',
            'gpt-4-turbo',
            'gpt-4-turbo-2024-04-09',
            'gpt-4-turbo-preview',
            'gpt-4o',
            'gpt-4o-2024-05-13',
            'gpt-4o-mini',
            'gpt-4o-mini-2024-07-18',
            'gpt4o-0806-loco-vm',
            'gpt-3.5-turbo',
            'gpt-3.5-turbo-16k',
            'gpt-3.5-turbo-0125',
            'gpt-3.5-turbo-1106',
            'gpt-3.5-turbo-instruct',  # Legacy completion model
            'gpt-3.5-turbo-instruct-0914',  # Legacy completion model
            # Legacy completion models
            'davinci-002',
            'babbage-002',
            'text-davinci-003',
            'text-curie-001',
            'text-babbage-001',
            'text-ada-001',
        ]

def load_or_create_api_key() -> str:
    """Load or create an API key."""
    if not os.path.exists(PRIVATE_FOLDER):
        os.makedirs(PRIVATE_FOLDER)

    if os.path.exists(API_KEY_FILE):
        with open(API_KEY_FILE, "r") as file:
            api_key = file.read().strip()
        if api_key:
            return api_key
    return ""

def enable_startup() -> None:
    """Enable the app to run on startup by creating a shortcut."""
    script_directory = os.path.dirname(os.path.abspath(__file__))
    shortcut_target = os.path.join(script_directory, "backgroundai.py")
    pythonw_executable = shutil.which("pythonw")

    if not pythonw_executable:
        pythonw_executable = sys.executable  # Fallback to current Python executable if pythonw.exe is not found

    icon_path = os.path.join(script_directory, "write.ico")

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(STARTUP_SHORTCUT_PATH)
    shortcut.Targetpath = pythonw_executable
    shortcut.Arguments = f'"{shortcut_target}"'
    shortcut.WorkingDirectory = script_directory
    shortcut.IconLocation = f"{icon_path}, 0"  # Set the icon location
    shortcut.save()

    QMessageBox.information(None, "Startup Enabled", "The application is now set to run at startup.")


def disable_startup():
    """Disable the app from running on startup by removing the shortcut."""
    if os.path.exists(STARTUP_SHORTCUT_PATH):
        os.remove(STARTUP_SHORTCUT_PATH)
        QMessageBox.information(None, "Startup Disabled", "The application is no longer set to run at startup.")
    else:
        QMessageBox.warning(None, "Already Disabled", "The application is not set to run at startup.")

    
def make_bold(font: QFont, size: int = 12) -> QFont:
    font.setWeight(QFont.Bold)
    font.setPointSize(size)  # Set a larger font size
    return font

def make_normal(font: QFont, size: int = 12) -> QFont:
    font.setPointSize(size)  # Set a larger font size
    return font


def load_settings() -> dict[str:float|int|bool|str]:
    """Load settings from file or use default settings."""
    settings = DEFAULT_SETTINGS.copy()
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS
    with open(SETTINGS_FILE, "r") as file:
        settings = json.load(file)
    return settings


def save_settings(settings:dict[str:float|int|bool|str]) -> None:
    """Save settings to a file."""
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=4)

class SettingsWindow(QDialog):
    class Settings():
        def __init__(self,settings:dict[str:float|int|str|bool]):
            self._settings_dict = settings
            self.model = settings["model"]
            self.temperature = settings["temperature"]
            self.max_tokens = settings["max_tokens"]
            self.auto_type = settings["auto_type"]
            self.typing_speed_wpm = settings["typing_speed_wpm"]
            self.letter_by_letter = settings["letter_by_letter"]
            self.play_tts = settings["play_tts"]
            self.tts_rate = settings["tts_rate"]
            self.custom_instructions = settings["custom_instructions"]
            self.keybinds = settings["keybinds"]
            self.keybind_prompt = settings["keybinds"]["prompt"]
            self.keybind_completion = settings["keybinds"]["completion"]
        def __getitem__(self,key):
            return self.__getattribute__(key)
        def __setitem__(self, key, value) -> None:
            return self.__setattr__(key,value)
        def __setattr__(self, name: str, value) -> None:
            if name == "_settings_dict": #avoids key error when setting the self._settings_dict for the first time.
                pass
            elif name in self._settings_dict:
                self.__getattribute__("_settings_dict")[name] = value
            return super().__setattr__(name,value)
        def __iter__(self):
            return self._settings_dict.__iter__()
        @property
        def settings_dict(self): return self._settings_dict.copy()

    def __init__(self) -> None:
        super().__init__()
        settings_dict = load_settings()
        self.settings = self.Settings(copy.deepcopy(settings_dict))
        self.saved_settings = self.Settings(copy.deepcopy(settings_dict))

        self.setWindowTitle("KeyGenie Menu")
        # Set the window icon
        script_directory = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_directory, "write.png")  # Path to the new icon

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))  # Set window icon
        else:
            print(f"Icon file not found at {icon_path}")

        # Get Screensize
        user32 = ctypes.windll.user32
        screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        # Adaptive menu placement according to computer specs
        menuPlacement = (int(user32.GetSystemMetrics(0)*0.03),
                        int(user32.GetSystemMetrics(1)*0.03),
                        int(user32.GetSystemMetrics(0)*0.25),
                        int(user32.GetSystemMetrics(1)*0.8))
        # Sets window size and position relative to monitor size
        self.setGeometry(*menuPlacement)

        # Removes question mark next to quit button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)


        self.load_custom_fonts()

        self.init_ui()
        self.current_action = None  # Track which keybind is being set
        self.api_key_visible = False  # Track visibility of the API key
    
    def load_custom_fonts(self):
        # Load fonts
        script_directory = os.path.dirname(os.path.abspath(__file__))
        rowdies_path = os.path.join(script_directory, 'Rowdies-Regular.ttf')
        ubuntu_bold_path = os.path.join(script_directory, 'Ubuntu-Bold.ttf')
        noto_sans_path = os.path.join(script_directory, 'NotoSans-Medium.ttf')

        # Load Rowdies-Regular for the title
        if os.path.exists(rowdies_path):
            rowdies_font_id = QFontDatabase.addApplicationFont(rowdies_path)
            if rowdies_font_id != -1:
                self.rowdies_font = QFont(QFontDatabase.applicationFontFamilies(rowdies_font_id)[0])
            else:
                print(f"Failed to load Rowdies font from {rowdies_path}")
        else:
            print(f"Rowdies font not found at {rowdies_path}")

        # Load Ubuntu-Bold for bold sections
        if os.path.exists(ubuntu_bold_path):
            ubuntu_bold_font_id = QFontDatabase.addApplicationFont(ubuntu_bold_path)
            if ubuntu_bold_font_id != -1:
                self.ubuntu_bold_font = QFont(QFontDatabase.applicationFontFamilies(ubuntu_bold_font_id)[0])
            else:
                print(f"Failed to load Ubuntu-Bold font from {ubuntu_bold_path}")
        else:
            print(f"Ubuntu-Bold font not found at {ubuntu_bold_path}")

        # Load NotoSans-Medium for normal text
        if os.path.exists(noto_sans_path):
            noto_sans_font_id = QFontDatabase.addApplicationFont(noto_sans_path)
            if noto_sans_font_id != -1:
                self.noto_sans_font = QFont(QFontDatabase.applicationFontFamilies(noto_sans_font_id)[0])
            else:
                print(f"Failed to load NotoSans font from {noto_sans_path}")
        else:
            print(f"NotoSans font not found at {noto_sans_path}")
    
    

    def init_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        # Increase overall font size
        bold_font_size = 16    # Medium-large size for section headings 
        normal_font_size = 14  # Normal size for text fields, buttons, etc.
        
        # Create a horizontal layout for the title and image
        title_image_layout = QHBoxLayout()

        # Add the title "Key" first, then the image to the right
        self.title_label = QLabel("Key ", self)
        self.title_label.setFont(QFont(self.rowdies_font.family(), 26))  # Example for larger title font size
        self.title_label.setAlignment(Qt.AlignLeft)  # Align the text to the left
        title_image_layout.addWidget(self.title_label)

        # Add the image (write.png) to the right of the text
        self.image_label = QLabel(self)
        script_directory = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_directory, "write.png")

        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            
            # Scale the image to make it smaller
            scaled_pixmap = pixmap.scaled(55, 55, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Apply a black color overlay using QPainter
            black_pixmap = QPixmap(scaled_pixmap.size())
            black_pixmap.fill(Qt.transparent)  # Make the background transparent
            
            painter = QPainter(black_pixmap)
            painter.drawPixmap(0, 0, scaled_pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(black_pixmap.rect(), QColor('black'))  # Apply black color overlay
            painter.end()
            
            self.image_label.setPixmap(black_pixmap)
        else:
            self.image_label.setText("Image not found")  # Display text if the image is not found

        # Align the image to the right and center it vertically with the text
        self.image_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_image_layout.addWidget(self.image_label)

        self.title_label = QLabel(" Genie", self)
        self.title_label.setFont(QFont(self.rowdies_font.family(), 26))  # Example for larger title font size
        self.title_label.setAlignment(Qt.AlignLeft)  # Align the text to the left
        title_image_layout.addWidget(self.title_label)

        # Ensure title and image layout is centered horizontally
        title_image_layout.setAlignment(Qt.AlignCenter)

        # Add the title-image layout to the main layout
        main_layout.addLayout(title_image_layout)

        # Create a scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        # Create a widget to contain all the settings
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setSpacing(10)  # Adds spacing between widgets
        
        # 1. API Key Section
        api_key_layout = QHBoxLayout()  # Create a horizontal layout for the API Key section

        self.api_key_label = QLabel("API Key:")
        self.api_key_label.setFont(make_bold(QFont(self.noto_sans_font.family()), bold_font_size))  # Bold + bigger
        content_layout.addWidget(self.api_key_label)

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Get one at platform.openai.com/api-keys")
        self.api_key_input.setEchoMode(QLineEdit.Password)  # Hide API key by default
        self.api_key_input.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        api_key_layout.addWidget(self.api_key_input)

        # Show/Hide button next to the API key input
        self.toggle_api_key_button = QPushButton("Show")
        self.toggle_api_key_button.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        self.toggle_api_key_button.setFixedWidth(100)  # Set a fixed width for the button
        self.toggle_api_key_button.clicked.connect(self.toggle_api_key_visibility)
        api_key_layout.addWidget(self.toggle_api_key_button)

        # Add the horizontal layout for API Key and Show/Hide button to the main content layout
        content_layout.addLayout(api_key_layout)

        # Save button for API key (this stays on a new line)
        self.save_api_button = QPushButton("Save API Key")
        self.save_api_button.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        self.save_api_button.clicked.connect(self.save_api_key)
        content_layout.addWidget(self.save_api_button)

        # Load the API key after creating the layout
        self.load_api_key()
        
        # 2. Model Selection Section
        self.model_label = QLabel("Model Selection:")
        self.model_label.setFont(make_bold(QFont(self.ubuntu_bold_font.family()), bold_font_size))  # Bold + bigger
        content_layout.addWidget(self.model_label)
        
        self.model_combo_box = QComboBox()
        self.model_combo_box.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Bigger combo box text
        self.model_combo_box.addItems(model_ids)
        content_layout.addWidget(self.model_combo_box)
        selected_model = self.settings.model
        if selected_model in model_ids:
            index = model_ids.index(selected_model)
            self.model_combo_box.setCurrentIndex(index)
        else:
            self.model_combo_box.setCurrentIndex(0)
        
        self.model_combo_box.currentIndexChanged.connect(self.on_model_selection_changed)
        
        # 3. Custom Instructions Section
        self.custom_instructions_label = QLabel("Custom Instructions:")
        self.custom_instructions_label.setFont(make_bold(QFont(self.ubuntu_bold_font.family()), bold_font_size))  # Bold + bigger
        content_layout.addWidget(self.custom_instructions_label)
        
        self.custom_instructions_text = QTextEdit()
        self.custom_instructions_text.setPlaceholderText("Enter custom instructions for the AI here...")
        self.custom_instructions_text.setPlainText(self.settings.custom_instructions)
        self.custom_instructions_text.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        content_layout.addWidget(self.custom_instructions_text)
        self.custom_instructions_text.textChanged.connect(self.on_instructions_text_changed)
        
        self.save_instructions_button = QPushButton("Save Instructions")
        self.save_instructions_button.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        self.save_instructions_button.clicked.connect(self.save_custom_instructions)
        content_layout.addWidget(self.save_instructions_button)
        
        # 4. Keybinds Section
        self.keybinds_label = QLabel("Keybinds:")
        self.keybinds_label.setFont(make_bold(QFont(self.ubuntu_bold_font.family()), bold_font_size))  # Bold + bigger  
        content_layout.addWidget(self.keybinds_label)

        # Prompt Keybind Layout (Text field and button on the same line)
        prompt_keybind_layout = QHBoxLayout()
        self.prompt_keybind_label = QLabel("Prompt Keybind:")
        self.prompt_keybind_label.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        prompt_keybind_layout.addWidget(self.prompt_keybind_label)

        self.prompt_keybind_input = QLineEdit()
        self.prompt_keybind_input.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Bigger input field
        self.prompt_keybind_input.setReadOnly(True)
        prompt_keybind_layout.addWidget(self.prompt_keybind_input)

        self.prompt_keybind_button = QPushButton("Set")
        self.prompt_keybind_button.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Bigger button text
        self.prompt_keybind_button.setFixedWidth(150)  # Set a fixed width to make the button smaller
        self.prompt_keybind_button.clicked.connect(lambda: self.select_keybind("prompt", self.prompt_keybind_button))
        prompt_keybind_layout.addWidget(self.prompt_keybind_button)

        content_layout.addLayout(prompt_keybind_layout)

        # Completion Keybind Layout (Text field and button on the same line)
        completion_keybind_layout = QHBoxLayout()
        self.completion_keybind_label = QLabel("Completion Keybind:")
        self.completion_keybind_label.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        completion_keybind_layout.addWidget(self.completion_keybind_label)

        self.completion_keybind_input = QLineEdit()
        self.completion_keybind_input.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        self.completion_keybind_input.setReadOnly(True)
        completion_keybind_layout.addWidget(self.completion_keybind_input)

        self.completion_keybind_button = QPushButton("Set")
        self.completion_keybind_button.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        self.completion_keybind_button.setFixedWidth(150)  # Set a fixed width to make the button smaller
        self.completion_keybind_button.clicked.connect(lambda: self.select_keybind("completion", self.completion_keybind_button))
        completion_keybind_layout.addWidget(self.completion_keybind_button)

        content_layout.addLayout(completion_keybind_layout)

        self.revert_keybinds_button = QPushButton("Revert to Default Keybinds")
        self.revert_keybinds_button.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        self.revert_keybinds_button.clicked.connect(self.revert_to_default_keybinds)
        content_layout.addWidget(self.revert_keybinds_button)

        # set the text for the input boxes, so the current keybind is visable.
        self.prompt_keybind_input.setText(self.settings.keybinds["prompt"])
        self.completion_keybind_input.setText(self.settings.keybinds["completion"])
        
        # 5. Additional Settings (Temperature, Max Tokens, Typing, TTS)
        self.settings_label = QLabel("Additional Settings:")
        self.settings_label.setFont(make_bold(QFont(self.ubuntu_bold_font.family()), bold_font_size))  # Bold + bigger  
        content_layout.addWidget(self.settings_label)
        
        # Temperature Slider
        temp_layout = QHBoxLayout()
        self.temperature_label = QLabel(f"Temperature: {self.settings['temperature']}")
        self.temperature_label.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        temp_layout.addWidget(self.temperature_label)
        
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setMinimum(0)
        self.temperature_slider.setMaximum(20)  # Slider steps from 0 to 20 representing 0.0 to 2.0
        self.temperature_slider.setValue(int(self.settings['temperature'] * 10))
        self.temperature_slider.valueChanged.connect(self.on_temperature_changed)
        temp_layout.addWidget(self.temperature_slider)
        content_layout.addLayout(temp_layout)
        
        # Max Tokens Input
        max_tokens_layout = QHBoxLayout()
        self.max_tokens_label = QLabel("Max Completion Tokens:")
        self.max_tokens_label.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        max_tokens_layout.addWidget(self.max_tokens_label)
        
        self.max_tokens_input = QLineEdit(str(self.settings['max_tokens']))
        self.max_tokens_input.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        max_tokens_layout.addWidget(self.max_tokens_input)
        content_layout.addLayout(max_tokens_layout)
        
        # Auto-Type Checkbox
        self.auto_type_checkbox = QCheckBox("Auto-Type")
        self.auto_type_checkbox.setChecked(self.settings['auto_type'])
        self.auto_type_checkbox.stateChanged.connect(self.on_auto_type_changed)
        self.auto_type_checkbox.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        content_layout.addWidget(self.auto_type_checkbox)
        
        # Typing Speed Slider
        self.typing_speed_layout = QHBoxLayout()
        self.typing_speed_label = QLabel(f"Typing Speed: {self.settings['typing_speed_wpm']} WPM")
        self.typing_speed_label.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        self.typing_speed_layout.addWidget(self.typing_speed_label)
        
        self.typing_speed_slider = QSlider(Qt.Horizontal)
        self.typing_speed_slider.setMinimum(10)
        self.typing_speed_slider.setMaximum(1000)
        self.typing_speed_slider.setValue(self.settings['typing_speed_wpm'])
        self.typing_speed_slider.valueChanged.connect(self.on_typing_speed_changed)
        self.typing_speed_slider.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        self.typing_speed_layout.addWidget(self.typing_speed_slider)
        content_layout.addLayout(self.typing_speed_layout)
        
        # Letter by Letter Checkbox (only visible if Auto-Type is enabled)
        self.letter_by_letter_checkbox = QCheckBox("Letter by Letter Typing")
        self.letter_by_letter_checkbox.setChecked(self.settings['letter_by_letter'])
        self.letter_by_letter_checkbox.stateChanged.connect(self.on_letter_by_letter_changed)
        self.letter_by_letter_checkbox.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        content_layout.addWidget(self.letter_by_letter_checkbox)
        
        # Play TTS Checkbox
        self.play_tts_checkbox = QCheckBox("Play TTS")
        self.play_tts_checkbox.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        self.play_tts_checkbox.setChecked(self.settings['play_tts'])
        self.play_tts_checkbox.stateChanged.connect(self.on_play_tts_changed)
        content_layout.addWidget(self.play_tts_checkbox)
        
        # TTS Rate Slider (initially hidden)
        self.tts_rate_layout = QHBoxLayout()
        self.tts_rate_label = QLabel(f"TTS Rate: {self.settings['tts_rate']}")
        self.tts_rate_label.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        self.tts_rate_layout.addWidget(self.tts_rate_label)
        
        self.tts_rate_slider = QSlider(Qt.Horizontal)
        self.tts_rate_slider.setMinimum(-10)
        self.tts_rate_slider.setMaximum(10)
        self.tts_rate_slider.setValue(self.settings['tts_rate'])
        self.tts_rate_slider.valueChanged.connect(self.on_tts_rate_changed)
        self.tts_rate_layout.addWidget(self.tts_rate_slider)
        content_layout.addLayout(self.tts_rate_layout)
        
        self.tts_rate_slider.setVisible(self.play_tts_checkbox.isChecked())
        self.tts_rate_label.setVisible(self.play_tts_checkbox.isChecked())
        
        # 6. Startup Buttons
        startup_buttons_layout = QHBoxLayout()
        
        self.enable_startup_button = QPushButton("Enable from Startup")
        self.enable_startup_button.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        self.enable_startup_button.clicked.connect(enable_startup)
        startup_buttons_layout.addWidget(self.enable_startup_button)
        
        self.disable_startup_button = QPushButton("Disable from Startup")
        self.disable_startup_button.setFont(make_normal(QFont(self.noto_sans_font.family()), normal_font_size))  # Normal + bigger
        self.disable_startup_button.clicked.connect(disable_startup)
        startup_buttons_layout.addWidget(self.disable_startup_button)
        
        content_layout.addLayout(startup_buttons_layout)
        
        # 7. Save and Revert Buttons
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.setFont(make_bold(QFont(self.ubuntu_bold_font.family()), bold_font_size))  # Bold + bigger  
        self.save_settings_button.clicked.connect(self.save_settings)
        content_layout.addWidget(self.save_settings_button)
        
        self.revert_settings_button = QPushButton("Revert to Default Settings")
        self.revert_settings_button.setFont(make_bold(QFont(self.ubuntu_bold_font.family()), bold_font_size))  # Bold + bigger  
        self.revert_settings_button.clicked.connect(self.revert_to_default_settings)
        content_layout.addWidget(self.revert_settings_button)
        
        # Finalize the layout with the scroll area
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        """
        The PyQt5 main event loop runs this method when the red X has been clicked on the settings menu. 
        \n\n if the settings are not saved, ask the user if they want to save before exiting the settings menu. It handles this as you'd expect.
        \n\n Removes the instance of the SettingsWindow with self.close(), such that the window is removed. 
        """
        self.settings['custom_instructions'] = self.custom_instructions_text.toPlainText()
        self.settings['max_tokens'] = int(self.max_tokens_input.text())
        self.settings['play_tts'] = self.play_tts_checkbox.isChecked()

        if self.saved_settings.settings_dict != self.settings.settings_dict:
            # ask user if they want to save before exiting settings, as they have unsaved changes.
            ask_to_save_QDialog = QMessageBox(self)
            ask_to_save_QDialog.setWindowTitle("Unsaved Changes")
            ask_to_save_QDialog.setText("The document has been modified.")
            ask_to_save_QDialog.setInformativeText("Do you want to save your changes?")
            ask_to_save_QDialog.setStandardButtons(QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
            ask_to_save_QDialog.setDefaultButton(QMessageBox.StandardButton.Save)
            ret = ask_to_save_QDialog.exec()
            if ret == QMessageBox.StandardButton.Save:
                self.save_settings()
            elif ret == QMessageBox.StandardButton.Discard:
                # do nothing, therefore not saving the unsaved data. 
                pass
            elif ret == QMessageBox.StandardButton.Cancel:
                # Stop the exiting from occuring
                a0.ignore()
                return
        self.close()

    def load_api_key(self) -> None:
        """Loads the api key using the load_or_create_api_key() function, then adds the api key string to a QLineEdit object for display (self.api_key_input)
        \n\n Also, there is no plain str attribute with the api key for some reason."""
        api_key = load_or_create_api_key()
        if api_key:
            self.api_key_input.setText(api_key)

    def save_api_key(self):
        api_key = self.api_key_input.text().strip()
        if api_key:
            with open(API_KEY_FILE, "w") as file:
                file.write(api_key)
            QMessageBox.information(self, "Success", "API key saved successfully!")
        else:
            QMessageBox.warning(self, "Error", "No API key provided!")

    def toggle_api_key_visibility(self):
        """Toggle the visibility of the API key."""
        if self.api_key_visible:
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.toggle_api_key_button.setText("Show")
        else:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
            self.toggle_api_key_button.setText("Hide")
        self.api_key_visible = not self.api_key_visible


    def select_keybind(self, action, button) -> None:
        """Change the button color and wait for key input."""
        if self.current_action:
            return  # Prevent setting multiple keybinds at once

        self.current_action = action
        button.setStyleSheet("background-color: yellow")

        # Use keyboard.hook to detect the key press in the background
        def on_key_event(event):
            if event.event_type == "down":  # Only capture key down events
                key = event.name
                if action == "prompt":
                    self.settings.keybinds["prompt"] = key
                    self.prompt_keybind_input.setText(key)
                elif action == "completion":
                    self.settings.keybinds["completion"] = key
                    self.completion_keybind_input.setText(key)
                
                # save the keybinds to file
                # self.saved_settings.keybinds = self.settings.keybinds
                # save_settings(self.saved_settings.settings_dict)

                # Reset the button color
                button.setStyleSheet("")
                keyboard.unhook_all()  # Stop listening for keyboard events
                self.current_action = None

        keyboard.hook(on_key_event)  # Hook keyboard events for key detection

    def revert_to_default_keybinds(self):
        """Revert to default keybinds and update UI."""
        self.settings.keybinds = DEFAULT_SETTINGS["keybinds"].copy()
        self.saved_settings.keybinds = DEFAULT_SETTINGS["keybinds"].copy()
        save_settings(self.saved_settings.settings_dict)
        self.prompt_keybind_input.setText(self.settings.keybinds["prompt"])
        self.completion_keybind_input.setText(self.settings.keybinds["completion"])
        # save_settings(self.settings.settings_dict)
        QMessageBox.information(self, "Info", "Keybinds reverted to default!")

    def on_instructions_text_changed(self):
        self.settings.custom_instructions = self.custom_instructions_text.toPlainText()

    def on_model_selection_changed(self):
        """Save the selected model when the selection changes."""
        model_id = self.model_combo_box.currentText()
        self.settings.model = model_id
        
    def on_temperature_changed(self):
        """Update temperature label when the slider value changes."""
        temperature = self.temperature_slider.value() / 10.0
        self.temperature_label.setText(f"Temperature: {temperature}")
        self.settings['temperature'] = temperature

    def on_auto_type_changed(self):
        """Show or hide typing speed and letter-by-letter checkbox based on auto-type checkbox."""
        auto_type_enabled = self.auto_type_checkbox.isChecked()
        self.settings['auto_type'] = auto_type_enabled
        self.typing_speed_slider.setVisible(auto_type_enabled)
        self.typing_speed_label.setVisible(auto_type_enabled)
        self.letter_by_letter_checkbox.setVisible(auto_type_enabled)

    def on_typing_speed_changed(self):
        """Update typing speed label when the slider value changes."""
        typing_speed_wpm = self.typing_speed_slider.value()
        self.typing_speed_label.setText(f"Typing Speed: {typing_speed_wpm} WPM")
        self.settings['typing_speed_wpm'] = typing_speed_wpm

    def on_letter_by_letter_changed(self):
        """Update the letter-by-letter setting when the checkbox is toggled."""
        self.settings['letter_by_letter'] = self.letter_by_letter_checkbox.isChecked()

    def on_tts_rate_changed(self):
        """Update TTS rate label and settings when the slider value changes."""
        rate = self.tts_rate_slider.value()
        self.tts_rate_label.setText(f"TTS Rate: {rate}")
        self.settings['tts_rate'] = rate
        
    def on_play_tts_changed(self):
        """Show or hide TTS rate settings based on the 'Play TTS' checkbox."""
        play_tts_enabled = self.play_tts_checkbox.isChecked()
        self.tts_rate_slider.setVisible(play_tts_enabled)
        self.tts_rate_label.setVisible(play_tts_enabled)
        self.settings['play_tts'] = play_tts_enabled


    def revert_to_default_settings(self):
        """Revert all settings to default values."""
        self.settings = self.Settings(DEFAULT_SETTINGS.copy())
        self.model_combo_box.setCurrentIndex(model_ids.index(self.settings["model"]))
        self.custom_instructions_text.setPlainText(self.settings.custom_instructions)
        self.completion_keybind_input.setText(self.settings.keybinds["completion"])
        self.prompt_keybind_input.setText(self.settings.keybinds["prompt"])
        self.temperature_slider.setValue(int(self.settings['temperature'] * 10))
        self.temperature_label.setText(f"Temperature: {self.settings['temperature']}")
        self.max_tokens_input.setText(str(self.settings['max_tokens']))
        self.auto_type_checkbox.setChecked(self.settings['auto_type'])
        self.letter_by_letter_checkbox.setChecked(self.settings['letter_by_letter'])
        self.typing_speed_slider.setValue(self.settings['typing_speed_wpm'])
        self.typing_speed_label.setText(f"Typing Speed: {self.settings['typing_speed_wpm']} WPM")
        self.play_tts_checkbox.setChecked(self.settings['play_tts'])
        self.tts_rate_slider.setValue(self.settings['tts_rate'])
        self.tts_rate_label.setText(f"TTS Rate: {self.settings['tts_rate']}")
        QMessageBox.information(self, "Info", "Settings reverted to default!")

    def save_settings(self):
        try:
            # all other settings, when the buttons or sliders are interacted with, are written to the self.settings object. 
            # Need to catch the ones that don't have these on edit events here.
            self.settings['custom_instructions'] = self.custom_instructions_text.toPlainText()
            self.settings['max_tokens'] = int(self.max_tokens_input.text())
            self.settings['play_tts'] = self.play_tts_checkbox.isChecked()
            # TTS rate is already updated via on_tts_rate_changed
            self.saved_settings = self.Settings(self.settings.settings_dict)
            # save the settings to the file
            save_settings(self.saved_settings.settings_dict)
            QMessageBox.information(self, "Success", "Settings saved successfully!")
        except ValueError:
            QMessageBox.warning(self, "Error", "Max tokens must be an integer!")

    def save_custom_instructions(self):
        """Save the custom instructions entered by the user."""
        instructions = self.custom_instructions_text.toPlainText()
        self.settings.custom_instructions = instructions
        self.saved_settings.custom_instructions = instructions
        save_settings(self.saved_settings.settings_dict)
        QMessageBox.information(self, "Success", "Custom instructions saved successfully!")
