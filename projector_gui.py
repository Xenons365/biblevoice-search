import asyncio
import tkinter as tk
from tkinter import ttk
from collections import deque
from scripture_finder import find_scripture_references
from data_manager import get_scripture_text, VerseNotFoundError, get_available_translations
import sounddevice as sd
import queue
import threading
import json
import os

# This queue will hold the audio data from the microphone.
q = queue.Queue()
# A deque to hold the active verse widgets on screen.
displayed_verses = deque()
# A global variable to hold the selected translation from the dropdown.
selected_translation = None

# --- GUI Components ---

class FadingLabel(tk.Label):
    """A custom Label widget that can animate its foreground color."""
    def fade(self, start_color, end_color, duration_ms, steps=30):
        start_rgb = tuple(int(start_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        end_rgb = tuple(int(end_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        delta_rgb = [(end - start) / steps for start, end in zip(start_rgb, end_rgb)]
        delay = duration_ms // steps

        def animate_step(current_step):
            if current_step > steps or not self.winfo_exists():
                if self.winfo_exists(): self.config(fg=end_color)
                return
            new_rgb = [int(start + delta * current_step) for start, delta in zip(start_rgb, delta_rgb)]
            new_color = f"#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}"
            if self.winfo_exists():
                self.config(fg=new_color)
                self.after(delay, animate_step, current_step + 1)
        animate_step(1)

class VerseWidget(tk.Frame):
    """A custom widget to display a single scripture, with fading labels."""
    def __init__(self, parent, book, ref, text, **kwargs):
        super().__init__(parent, bg="black", **kwargs)
        self.config(pady=20)
        wraplength = parent.winfo_width() - 100
        self.ref_label = FadingLabel(self, text=f"{book.title()} {ref}", font=("Helvetica", 36, "bold"), bg="black", fg="#000000", wraplength=wraplength, justify="left")
        self.ref_label.pack(fill="x", padx=10, anchor="w")
        self.text_label = FadingLabel(self, text=text, font=("Helvetica", 48), bg="black", fg="#000000", wraplength=wraplength, justify="left")
        self.text_label.pack(fill="x", padx=10, pady=(10, 0), anchor="w")

    def fade_in(self, duration=500):
        self.ref_label.fade("#000000", "#FFFFFF", duration)
        self.text_label.fade("#000000", "#FFFFFF", duration)

    def fade_to_dim(self, duration=500):
        DIM_COLOR = "#808080"
        self.ref_label.fade("#FFFFFF", DIM_COLOR, duration)
        self.text_label.fade("#FFFFFF", DIM_COLOR, duration)

# --------------- Microphone Listener Thread ---------------
def audio_callback(indata, frames, time, status):
    if status: print(status)
    q.put(bytes(indata))

def start_listening(loop, model_path="model"):
    try:
        import vosk
    except ImportError:
        display_message("Error: 'vosk' library not found. Please run: pip install vosk", is_error=True)
        return

    if not os.path.exists(model_path):
        display_message(f"Error: Vosk model not found at '{model_path}'.", is_error=True)
        return

    model = vosk.Model(model_path)
    rec = vosk.KaldiRecognizer(model, 16000)

    def recognizer_thread():
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if text:
                    print(f"Recognized: '{text}'")
                    # Pass the currently selected translation to the processing function.
                    asyncio.run_coroutine_threadsafe(process_text(text, selected_translation.get()), loop)

    threading.Thread(target=recognizer_thread, daemon=True).start()

    try:
        stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=16000, blocksize=8000)
        stream.start()
        print("Microphone listener started.")
    except Exception as e:
        display_message(f"Error starting audio stream: {e}", is_error=True)

# --------------- GUI & Async Logic ---------------

def display_message(text, is_error=False):
    for widget in list(displayed_verses): widget.destroy()
    displayed_verses.clear()
    color = "red" if is_error else "gray"
    verse_container.update_idletasks()
    wraplength = verse_container.winfo_width() - 100
    widget = tk.Label(verse_container, text=text, font=("Helvetica", 24), bg="black", fg=color, wraplength=wraplength)
    widget.pack(pady=50)
    displayed_verses.append(widget)

async def process_text(text, translation="KJV"):
    references = find_scripture_references(text)
    if not references: return

    if displayed_verses and isinstance(displayed_verses[0], tk.Label):
        displayed_verses.popleft().destroy()

    for verse_widget in displayed_verses:
        if isinstance(verse_widget, VerseWidget):
            verse_widget.fade_to_dim()

    tasks = [get_scripture_text(book.strip(), ref, translation) for book, ref in references]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for (book, ref), result in reversed(list(zip(references, results))):
        book_title = book.strip().title()
        verse_text = str(result) if not isinstance(result, Exception) else f"Error: {result}"

        verse_widget = VerseWidget(verse_container, book_title, ref, verse_text)
        verse_widget.pack(side="top", fill="x", anchor="n")
        displayed_verses.appendleft(verse_widget)
        verse_widget.fade_in()

async def gui_update_loop():
    """The main async loop for the Tkinter GUI."""
    while True:
        try:
            root.update()
            canvas.configure(scrollregion=canvas.bbox("all"))
            await asyncio.sleep(0.01)
        except tk.TclError:
            break

def on_mouse_wheel(event):
    if event.num == 4 or event.delta > 0: canvas.yview_scroll(-1, "units")
    elif event.num == 5 or event.delta < 0: canvas.yview_scroll(1, "units")

async def main():
    """Sets up the GUI and runs the main async event loop."""
    loop = asyncio.get_event_loop()

    # --- Populate Translation Dropdown ---
    translations = await get_available_translations()
    translation_dropdown['values'] = translations
    # Set default to KJV if available, otherwise the first in the list.
    if "KJV" in translations:
        selected_translation.set("KJV")
    elif translations:
        selected_translation.set(translations[0])

    # Start the microphone listener thread.
    start_listening(loop)
    # Start the GUI update loop.
    await gui_update_loop()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Scripture Projector")
    root.attributes("-fullscreen", True)
    root.configure(bg="black")

    # --- Scrollable Frame & Canvas ---
    main_frame = tk.Frame(root, bg="black")
    main_frame.pack(fill="both", expand=True)
    canvas = tk.Canvas(main_frame, bg="black", highlightthickness=0)
    verse_container = tk.Frame(canvas, bg="black")
    canvas.create_window((0, 0), window=verse_container, anchor="nw")
    canvas.pack(side="left", fill="both", expand=True, padx=(50, 0), pady=50)

    # --- Scrollbar ---
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y", pady=50, padx=(0, 50))

    # --- Translation Dropdown ---
    selected_translation = tk.StringVar()
    style = ttk.Style()
    style.theme_use('clam')
    # Configure the dropdown style for dark mode.
    style.configure("TCombobox", fieldbackground="black", background="#333", foreground="white", arrowcolor="white", selectbackground="black", selectforeground="white", padding=(10, 5))
    translation_dropdown = ttk.Combobox(root, textvariable=selected_translation, state="readonly", font=("Helvetica", 14), width=10)
    translation_dropdown.place(relx=1.0, rely=0.0, x=-20, y=20, anchor="ne")

    # Bind mouse wheel events for scrolling.
    root.bind("<MouseWheel>", on_mouse_wheel)
    root.bind("<Button-4>", on_mouse_wheel)
    root.bind("<Button-5>", on_mouse_wheel)

    display_message("Listening for scripture references...")

    # --- Exit Instructions ---
    exit_label = tk.Label(root, text="Press ESC to exit", font=("Helvetica", 14), bg="black", fg="gray")
    exit_label.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")
    root.bind("<Escape>", lambda e: root.destroy())

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, tk.TclError):
        print("\nExiting application.")
    finally:
        if root.winfo_exists():
            root.destroy()