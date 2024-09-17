import keyboard
from openai import OpenAI
import os
import time
import threading
import pystray
from PIL import Image
from PyQt5.QtWidgets import QApplication
from menu import (SettingsWindow, load_or_create_api_key, load_or_create_keybinds,
                  load_selected_model, load_settings, load_custom_instructions)
import sys
import ctypes
from ctypes import wintypes
from win32com.client import Dispatch
import pythoncom

from queue import Queue, Empty

# Default keybinds
DEFAULT_OPTIONS = {
    "prompt": "right shift",
    "completion": "right ctrl",
}

# Load or prompt for the API key (now using the function from PyQt5 menu)
api_key = load_or_create_api_key()

if not api_key:
    print("API key not found. Please set it in the settings.")
    #sys.exit(1)

# Initialize the OpenAI client with your API key
client = OpenAI(api_key=api_key)

# Event to control background task pause/resume
pause_event = threading.Event()

# Events to control stopping of typing and TTS
typing_stop_event = threading.Event()
tts_stop_event = threading.Event()

# Global variables to hold settings
keybinds = load_or_create_keybinds()
settings = load_settings()
custom_instructions = load_custom_instructions()

# Define constants for mutex
CREATE_MUTEX = 0x00000001
ERROR_ALREADY_EXISTS = 183


def check_single_instance():
    """Check if an instance of the program is already running."""
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\AIKeyboardMutex")
    if ctypes.GetLastError() == ERROR_ALREADY_EXISTS:
        print("Another instance of the program is already running. Exiting.")
        sys.exit(0)  # Exit the program if another instance is found


def is_chat_model(model_id):
    """Determine if the model is a chat model or a legacy completion model."""
    # List of known chat models
    chat_models = [
        'gpt-3.5-turbo',
        'gpt-3.5-turbo-16k',
        'gpt-3.5-turbo-0125',
        'gpt-3.5-turbo-1106',
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
    ]
    return model_id in chat_models


def wait_for_keypress():
    print(f"Press {keybinds['prompt']} or {keybinds['completion']} to start typing.")

    # Continuously wait for either the prompt or completion keybind
    while True:
        pause_event.wait()  # Wait if the event is paused
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN and event.name in [keybinds['prompt'], keybinds['completion']]:
            return event.name  # Return the key that was pressed to start the input capture


def capture_input():
    print("Started capturing text. Type now... (Press the same key to stop)")

    captured_text = []
    while True:
        pause_event.wait()  # Wait if the event is paused
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            key = event.name

            # Stop capturing input when either keybind is pressed again
            if key in [keybinds['prompt'], keybinds['completion']]:
                break

            if key == 'backspace':
                if captured_text:
                    captured_text.pop()  # Remove last character on backspace
            elif key == 'space':
                captured_text.append(' ')  # Append space
            elif key == 'enter':
                captured_text.append('\n')  # Append newline on enter
            elif len(key) == 1:  # Only add single character keys
                captured_text.append(key)

    # Join the list of captured text into a single string
    captured_string = ''.join(captured_text)
    print("\nCaptured text:\n" + captured_string)

    return captured_string


def stream_openai_completion(prompt):
    try:
        # Load the selected model
        model_id = load_selected_model()
        # Load settings
        current_settings = load_settings()
        temperature = current_settings.get('temperature', 1.0)
        max_tokens = current_settings.get('max_tokens', 256)
        # Load custom instructions
        custom_instructions = load_custom_instructions()

        # Prepare the prompt or messages
        if is_chat_model(model_id):
            # Use the Chat Completion API
            messages = []
            if custom_instructions.strip():
                messages.append({"role": "system", "content": custom_instructions})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                stream=True,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
        else:
            # Use the Legacy Completion API
            # Combine custom instructions and prompt
            combined_prompt = f"{custom_instructions}\n{prompt}" if custom_instructions.strip() else prompt

            response = client.completions.create(
                model=model_id,
                prompt=combined_prompt,
                stream=True,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
        return response
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def clean_text(text):
    """Clean the text by removing newlines and non-printable characters."""
    # Remove newlines
    text = text.replace('\n', ' ').replace('\r', ' ')
    # Remove non-printable or unwanted characters
    text = ''.join(c for c in text if c.isprintable())
    return text.strip()


def type_out_text_fast_streamed(response):
    print("\nTyping out the text as it's received...")

    if response is None:
        return

    # Load settings
    current_settings = load_settings()
    auto_type = current_settings.get('auto_type', True)
    typing_speed_wpm = current_settings.get('typing_speed_wpm', 200)
    letter_by_letter = current_settings.get('letter_by_letter', True)
    play_tts = current_settings.get('play_tts', False)
    tts_rate = current_settings.get('tts_rate', 0)

    # Initialize queues and threads
    typing_queue = Queue()
    tts_queue = Queue()

    # Clear stop events
    typing_stop_event.clear()
    tts_stop_event.clear()

    if auto_type:
        typing_thread = threading.Thread(target=typing_worker, args=(typing_queue, typing_speed_wpm, letter_by_letter, typing_stop_event))
        typing_thread.daemon = True
        typing_thread.start()

    if play_tts:
        tts_thread = threading.Thread(target=tts_worker, args=(tts_queue, tts_rate, tts_stop_event))
        tts_thread.daemon = True
        tts_thread.start()

    # Start the stop listener
    stop_listener = threading.Thread(target=stop_listener_worker)
    stop_listener.daemon = True
    stop_listener.start()

    # Iterate over each streamed chunk as it comes in
    for chunk in response:
        pause_event.wait()  # Wait if the event is paused
        if typing_stop_event.is_set() or tts_stop_event.is_set():
            break  # Stop processing if stop event is set

        if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
            choice = chunk.choices[0]
            token = None
            if hasattr(choice, 'delta') and hasattr(choice.delta, 'content'):
                # Chat completion response
                token = choice.delta.content
            elif hasattr(choice, 'text'):
                # Legacy completion response
                token = choice.text
            else:
                continue  # Skip if no content

            if token:
                # Put token into queues
                if auto_type:
                    typing_queue.put(token)
                if play_tts:
                    tts_queue.put(token)

    # Signal the workers to stop
    if auto_type:
        typing_queue.put(None)  # Sentinel value
        typing_thread.join()
    if play_tts:
        tts_queue.put(None)
        tts_thread.join()

    # Stop the stop listener
    keyboard.unhook_all()


def typing_worker(typing_queue, typing_speed_wpm, letter_by_letter, stop_event):
    # Calculate delay between characters based on typing speed (WPM)
    chars_per_minute = typing_speed_wpm * 5  # Approximate words per minute to characters per minute
    delay_per_char = 60 / chars_per_minute  # Time per character in seconds

    while True:
        if stop_event.is_set():
            break  # Exit the loop

        try:
            token = typing_queue.get(timeout=0.1)
        except Empty:
            continue

        if token is None:
            break  # Exit the loop

        if letter_by_letter:
            for char in token:
                if stop_event.is_set():
                    break  # Exit the loop
                keyboard.write(char)
                time.sleep(delay_per_char)
        else:
            keyboard.write(token)
            time.sleep(len(token) * delay_per_char)
        typing_queue.task_done()


def tts_worker(tts_queue, tts_rate, stop_event):
    pythoncom.CoInitialize()
    try:
        speaker = Dispatch("SAPI.SpVoice")
        SVSFlagsAsync = 1  # Manually define SVSFlagsAsync

        # Set the TTS rate
        speaker.Rate = tts_rate

        sentence_buffer = ""
        sentence_terminators = {'.', '!', '?'}

        while True:
            if stop_event.is_set():
                speaker.Speak("", 3)  # SVSFPurgeBeforeSpeak to stop speaking immediately
                break  # Exit the loop

            try:
                token = tts_queue.get(timeout=0.1)
            except Empty:
                continue  # Wait for more tokens

            if token is None:
                # Process any remaining text
                if sentence_buffer.strip():
                    clean_sentence = clean_text(sentence_buffer)
                    if clean_sentence:
                        speaker.Speak(clean_sentence, SVSFlagsAsync)
                        speaker.WaitUntilDone(-1)
                break  # Exit the loop
            else:
                # Accumulate tokens into sentences
                sentence_buffer += token

                # Process any complete sentences in the buffer
                while True:
                    # Find the earliest occurrence of a sentence terminator
                    indices = [sentence_buffer.find(t) for t in sentence_terminators if sentence_buffer.find(t) != -1]
                    if indices:
                        min_index = min(indices)
                        # Include the terminator
                        sentence_end = min_index + 1
                        sentence = sentence_buffer[:sentence_end]
                        # Clean and speak the sentence
                        clean_sentence = clean_text(sentence)
                        if clean_sentence:
                            speaker.Speak(clean_sentence, SVSFlagsAsync)
                            speaker.WaitUntilDone(-1)
                        # Remove the sentence from the buffer
                        sentence_buffer = sentence_buffer[sentence_end:]
                    else:
                        break  # No complete sentences left in the buffer

            tts_queue.task_done()
    finally:
        pythoncom.CoUninitialize()


def stop_listener_worker():
    def on_key_event(event):
        if event.event_type == 'down':
            # Set the stop events to stop typing and TTS
            typing_stop_event.set()
            tts_stop_event.set()
            # Unhook the listener
            keyboard.unhook_all()

    # Hook the keyboard to listen for any key press
    keyboard.hook(on_key_event)


def background_task():
    # Continuous loop to keep the program running indefinitely
    while True:
        pause_event.wait()  # Wait if the event is paused
        # Wait for prompt or completion keybind to start
        key_pressed = wait_for_keypress()

        # Capture the input from the user
        captured_text = capture_input()

        # Determine the prompt based on the key pressed
        if key_pressed == keybinds['prompt']:
            prompt = captured_text  # Use the captured text as is
        elif key_pressed == keybinds['completion']:
            prompt = f"Continue the following text: {captured_text}"

        # Send the captured text to OpenAI for streaming completion
        print("\nSending captured text to OpenAI for real-time completion...\n")
        response_stream = stream_openai_completion(prompt)

        # Type out the completion text fast as it's received
        type_out_text_fast_streamed(response_stream)


def create_image(image_path):
    # Load an image from the given path
    return Image.open(image_path)


def on_quit(icon, item):
    icon.stop()
    # No need to call sys.exit() here; the main thread will exit after icon.stop()


def reload_settings():
    """Reload keybinds, settings, and custom instructions after settings are updated."""
    global keybinds, settings, custom_instructions
    keybinds = load_or_create_keybinds()
    settings = load_settings()
    custom_instructions = load_custom_instructions()
    print("Settings reloaded:", keybinds, settings)


def open_menu():
    """Function to open the PyQt5 menu and pause the background task."""
    pause_event.clear()  # Pause the background task
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    app.exec_()  # This will block execution until the menu is closed
    reload_settings()  # Reload keybinds, settings, and custom instructions after the menu is closed
    pause_event.set()  # Resume the background task after the menu is closed


def setup_system_tray():
    # Provide the path to your icon image (e.g., "write.png")
    script_directory = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(script_directory, "write.png")
    if not os.path.exists(image_path):
        # Create a simple blank image if the icon doesn't exist
        image = Image.new('RGB', (64, 64), color=(255, 0, 0))
    else:
        image = create_image(image_path)

    icon = pystray.Icon("OpenAI App", image, menu=pystray.Menu(
        pystray.MenuItem("Open Settings", lambda: open_menu()),
        pystray.MenuItem("Quit", lambda: on_quit(icon, None))
    ))
    icon.run()
    # After icon.run() returns, the main thread can exit gracefully


if __name__ == "__main__":
    # Ensure only one instance of the program is running
    check_single_instance()

    # Set the event to 'set' (background task can run)
    pause_event.set()

    # Run the main program in a separate thread
    task_thread = threading.Thread(target=background_task)
    task_thread.daemon = True
    task_thread.start()

    # Setup the system tray icon and run it in the main thread
    setup_system_tray()

    # After the tray icon is stopped, exit the program
    sys.exit(0)
