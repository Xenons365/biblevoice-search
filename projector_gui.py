import asyncio
import tkinter as tk
from collections import deque
from scripture_finder import find_scripture_references, parse_and_expand_reference
from api_client import get_scripture_text, VerseNotFoundError
import sounddevice as sd
import queue
import threading
import json
import os

# This queue will hold the audio data from the microphone.
AUDIO_QUEUE = queue.Queue()
MAX_VERSES_ON_SCREEN = 15  # Max verses to keep in the display queue
FADE_STEPS = 10  # Number of steps in the fade animation
FADE_DELAY = 0.1 # Time between fade steps in seconds

class ProjectorGui:
    def __init__(self, loop):
        self.loop = loop
        self.root = tk.Tk()
        self.root.title("Scripture Projector")
        self.root.configure(bg="black")
        self.root.attributes("-fullscreen", True)

        # A deque to hold the labels of the verses currently displayed
        self.verse_labels = deque(maxlen=MAX_VERSES_ON_SCREEN)

        self._setup_widgets()
        self._setup_listeners()

    def _setup_widgets(self):
        # Create a canvas and a scrollbar
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)

        # This frame will hold the verse labels
        self.scrollable_frame = tk.Frame(self.canvas, bg="black")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack the widgets
        self.canvas.pack(side="left", fill="both", expand=True, padx=50, pady=50)
        # self.scrollbar.pack(side="right", fill="y") # Optional: hide scrollbar for cleaner look

        # Add initial message
        self.add_verse_display("Listening for scripture references...", is_static=True)

    def _setup_listeners(self):
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        # Bind mouse wheel for scrolling on different OSes
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows
        self.root.bind_all("<Button-4>", self._on_mousewheel)  # Linux up
        self.root.bind_all("<Button-5>", self._on_mousewheel)  # Linux down

    def _on_mousewheel(self, event):
        # For Linux, event.num determines direction
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else: # For Windows, event.delta is used
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_verse_display(self, text, is_static=False):
        """Adds a new verse label to the top of the scrollable frame."""
        label = tk.Label(
            self.scrollable_frame,
            text=text,
            font=("Helvetica", 48),
            fg="white",
            bg="black",
            wraplength=self.root.winfo_screenwidth() - 150, # Adjust wraplength
            justify="left"
        )
        label.pack(pady=20, anchor="w")

        if not is_static:
            # Add to the deque for animation tracking
            self.verse_labels.appendleft(label)
            # Start the fade animation for this new label
            self.loop.create_task(self.fade_label(label))

    async def fade_label(self, label):
        """Gradually fades a label from white to grey."""
        await asyncio.sleep(5) # Initial delay before starting the fade
        for i in range(FADE_STEPS + 1):
            # Calculate the color value (255 -> ~80)
            level = 255 - int((i / FADE_STEPS) * 175)
            # Format as a hex color string (e.g., '#FFFFFF')
            color = f"#{level:02x}{level:02x}{level:02x}"
            if label.winfo_exists(): # Check if widget is still alive
                label.config(fg=color)
                await asyncio.sleep(FADE_DELAY)

    async def process_text_and_update_gui(self, text):
        """Finds, fetches, and displays scripture references."""
        references = find_scripture_references(text)
        if not references:
            return

        # Clear the initial "Listening..." message if it's there
        if "Listening" in self.scrollable_frame.winfo_children()[0].cget("text"):
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

        async def fetch_and_display(book, ref):
            try:
                # Fetch the full text for the reference
                full_text = await get_scripture_text(book.strip(), ref.strip())

                # Parse the reference to get chapter and verse numbers
                chapter, verses = parse_and_expand_reference(ref)
                if not verses:
                    display_text = f"{book.title()} {ref}\n{full_text}"
                else:
                    # We have parsed verses, let's format them nicely
                    verse_texts = full_text.split('\n')
                    formatted_verses = []
                    for i, v_num in enumerate(verses):
                        if i < len(verse_texts):
                            # Remove the redundant prefix if it exists
                            v_text = verse_texts[i].split(f"{v_num} ")[-1]
                            formatted_verses.append(f"  {v_num} {v_text}")

                    display_text = f"{book.title()} {chapter}:\n" + "\n".join(formatted_verses)

                self.add_verse_display(display_text)

            except VerseNotFoundError as e:
                self.add_verse_display(f"Error: {e}", is_static=True)
            except Exception as e:
                self.add_verse_display(f"An unexpected error occurred: {e}", is_static=True)

        tasks = [fetch_and_display(book, ref) for book, ref in references]
        await asyncio.gather(*tasks)


def audio_listener_thread(loop, gui_processor):
    """Handles audio input and voice recognition in a separate thread."""
    try:
        import vosk
    except ImportError:
        print("Vosk library not found. Please run 'pip install vosk'.")
        return

    model_path = "model"
    if not os.path.exists(model_path):
        print(f"Vosk model not found at '{model_path}'. See README.md for setup.")
        # Schedule a GUI update on the main thread
        asyncio.run_coroutine_threadsafe(
            gui_processor(f"Vosk model not found at '{model_path}'"), loop
        )
        return

    model = vosk.Model(model_path)
    rec = vosk.KaldiRecognizer(model, 16000)
    rec.SetWords(True)

    def callback(indata, frames, time, status):
        if status:
            print(status)
        AUDIO_QUEUE.put(bytes(indata))

    try:
        with sd.InputStream(samplerate=16000, channels=1, callback=callback):
            print("Microphone listener started...")
            while True:
                data = AUDIO_QUEUE.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    if text:
                        print(f"Recognized: '{text}'")
                        # Schedule the async processing on the main event loop
                        asyncio.run_coroutine_threadsafe(
                            gui_processor(text), loop
                        )
    except Exception as e:
        error_message = f"Error with audio stream: {e}\nIs a microphone connected?"
        print(error_message)
        asyncio.run_coroutine_threadsafe(gui_processor(error_message), loop)


async def run_projector():
    """Main async loop to run the GUI and other tasks."""
    loop = asyncio.get_event_loop()
    gui = ProjectorGui(loop)

    # Start the audio listener in a separate thread
    listener_args = (loop, gui.process_text_and_update_gui)
    threading.Thread(target=audio_listener_thread, args=listener_args, daemon=True).start()

    # Main GUI loop
    while True:
        try:
            gui.root.update()
            await asyncio.sleep(0.01)
        except tk.TclError:
            # This happens when the window is closed
            break

if __name__ == "__main__":
    try:
        asyncio.run(run_projector())
    except KeyboardInterrupt:
        print("\nApplication closed.")