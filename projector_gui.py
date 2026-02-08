import asyncio
import tkinter as tk
from scripture_finder import find_scripture_references
from data_manager import get_scripture_text, VerseNotFoundError
from fading_text import FadingText
import sounddevice as sd
import queue
import threading
import json
import os

# This queue will hold the audio data from the microphone.
q = queue.Queue()

# --------------- Microphone Listener Thread ---------------

def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio chunk."""
    if status:
        print(status)
    q.put(bytes(indata))

def start_listening(loop, model_path="model"):
    """
    Starts the microphone listener and the Vosk recognizer in a separate thread.
    """
    try:
        import vosk
    except ImportError:
        print("Error: The 'vosk' library is required for voice recognition.")
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, "Vosk library not found. Please run: pip install vosk")
        return

    if not os.path.exists(model_path):
        error_msg = f"Vosk model not found at '{model_path}'.\nPlease see README.md for setup instructions."
        print(f"Error: {error_msg}")
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, error_msg)
        return

    model = vosk.Model(model_path)
    rec = vosk.KaldiRecognizer(model, 16000)

    def recognizer_thread():
        """This thread pulls audio data from the queue and feeds it to Vosk."""
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if text:
                    print(f"Recognized: '{text}'")
                    # Schedule the async processing on the main event loop
                    asyncio.run_coroutine_threadsafe(process_text(text), loop)

    threading.Thread(target=recognizer_thread, daemon=True).start()

    try:
        stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=16000, blocksize=8000)
        stream.start()
        print("Microphone listener started.")
    except Exception as e:
        error_msg = f"Error starting audio stream: {e}\n\nMake sure you have a microphone connected."
        print(error_msg)
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, error_msg)


# --------------- GUI & Async Logic ---------------

async def process_text(text):
    """
    Finds scripture references, fetches them, and updates the GUI with a fade effect.
    """
    references = find_scripture_references(text)
    if not references:
        return

    # Fetch all verses concurrently
    tasks = [get_scripture_text(book.strip(), ref) for book, ref in references]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build the full text to display
    display_text = ""
    for (book, ref), result in zip(references, results):
        book_title = book.strip().title()
        if isinstance(result, (VerseNotFoundError, FileNotFoundError)):
            display_text += f"Could not find: {book_title} {ref}\n\n"
        elif isinstance(result, Exception):
            display_text += f"Error: {result}\n\n"
        else:
            display_text += f"{book_title} {ref}\n{result}\n\n"

    # Use the FadingText widget's method to change text with animation
    await text_widget.change_text(display_text.strip())

async def run_gui():
    """The main async loop for the Tkinter GUI."""
    loop = asyncio.get_event_loop()
    start_listening(loop)

    while True:
        try:
            root.update()
            await asyncio.sleep(0.01)
        except tk.TclError:
            # This happens when the window is closed
            break

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Scripture Projector")
    root.attributes("-fullscreen", True)
    root.configure(bg="black")

    # --- Use the new FadingText Widget ---
    text_widget = FadingText(
        root, bg="black", fg="white", font=("Helvetica", 48),
        wrap=tk.WORD, relief=tk.FLAT, borderwidth=0, insertbackground="white"
    )
    text_widget.pack(expand=True, fill="both", padx=50, pady=50)
    text_widget.insert(tk.END, "Listening for scripture references...")

    # --- Exit Instructions ---
    exit_label = tk.Label(root, text="Press ESC to exit", font=("Helvetica", 14), bg="black", fg="gray")
    exit_label.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")
    root.bind("<Escape>", lambda e: root.destroy())

    try:
        asyncio.run(run_gui())
    except KeyboardInterrupt:
        print("\nExiting application.")
    finally:
        if root.winfo_exists():
            root.destroy()