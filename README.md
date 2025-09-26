# Scripture Projector

This project is a Python application designed to quickly find and display scripture verses for projection. It can be run as a simple command-line tool or as a real-time, voice-controlled GUI.

## Features

- **Scripture Recognition:** Identifies Bible references (e.g., "John 3:16", "1 Cor 13:4-7") within text.
- **Asynchronous Fetching:** Fetches multiple scripture references concurrently without blocking.
- **Caching:** Caches previously fetched verses to improve performance.
- **Error Handling:** Gracefully handles cases where a verse is not found.
- **Two Modes:**
    1.  **CLI Mode:** A standard command-line interface for text-based input.
    2.  **GUI Mode:** A fullscreen, voice-controlled interface for real-time projection.

---

## Setup Instructions

### 1. Clone the Repository

First, make sure you have the project files on your local machine.

### 2. Set Up a Virtual Environment (Recommended)

It's good practice to create a virtual environment to manage the project's dependencies.

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Install Dependencies

Install the required Python packages using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Download the Speech Recognition Model (Required for GUI Mode)

The voice-controlled GUI requires a language model from **Vosk**.

1.  **Download a model.** A small, lightweight model is a good starting point. You can download the `vosk-model-small-en-us-0.15` model from the [Vosk Models Page](https://alphacephei.com/vosk/models).
2.  **Create a `model` directory** in the root of the project folder.
3.  **Unzip the downloaded file** and place its contents *inside* the `model` directory. The final structure should look like this:
    ```
    /project-root
    ├── model/
    │   ├── am/
    │   ├── conf/
    │   └── ... (other model files)
    ├── api_client.py
    ├── projector_gui.py
    └── ... (other project files)
    ```

---

## How to Run

### Command-Line Interface (CLI)

To run the text-based version of the application, execute the `main.py` file:

```bash
python main.py
```

You can then type sentences containing scripture references and press Enter. Type `quit` to exit.

### Graphical User Interface (GUI)

To run the fullscreen, voice-controlled version, make sure you have completed the model download step above and have a microphone connected. Then, run the `projector_gui.py` file:

```bash
python projector_gui.py
```

The application will open in fullscreen and start listening for voice commands. Press the `ESC` key to exit.

---

## Connecting to a Real API

This project uses a **mock API client** (`api_client.py`) to simulate fetching scripture data. To connect to a real Bible API, you will need to modify the `_fetch_from_api` function inside `api_client.py`.

Here is an example of how you might change it to use a real API with the `aiohttp` library:

1.  **Identify your API's URL and structure.** For this example, let's assume the API endpoint is `https://my.bible-api.com/v1/scripture?ref={BOOK}+{CHAPTER}:{VERSE}` and it returns JSON like `{"text": "For God so loved the world..."}`.

2.  **Modify the `_fetch_from_api` function:**

    ```python
    import aiohttp

    async def _fetch_from_api(book, reference):
        """The internal function that performs the actual fetch."""
        # Note: You may need to install aiohttp if you haven't already:
        # pip install aiohttp

        api_url = f"https://my.bible-api.com/v1/scripture?ref={book}+{reference}"

        print(f"Fetching {book} {reference} from {api_url}...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status != 200:
                        raise VerseNotFoundError(f"API returned status {response.status} for '{book} {reference}'.")

                    data = await response.json()

                    if "text" not in data or not data["text"]:
                        raise VerseNotFoundError(f"Verse '{book} {reference}' not found in API response.")

                    return data["text"]
        except aiohttp.ClientError as e:
            # Handle network-related errors
            raise VerseNotFoundError(f"Network error for '{book} {reference}': {e}")
        except Exception as e:
            # Handle other unexpected errors, like invalid JSON
            raise VerseNotFoundError(f"An unexpected error occurred for '{book} {reference}': {e}")

    ```

## Projector and Sound System Setup

### Projector Setup

1.  **Connect Laptop:** Connect your laptop to the projector using an HDMI, VGA, or USB-C cable.
2.  **Configure Display:** In your operating system's display settings (Windows Display Settings or macOS Displays), choose either:
    *   **"Duplicate"** to show the same screen on your laptop and the projector.
    *   **"Extend"** to use the projector as a second, separate screen. This is recommended for live use.
3.  **Run the GUI:** When you run `python projector_gui.py`, the fullscreen window will appear on your primary display. If you are using "Extend" mode, you may need to drag the window to the projector screen or set the projector as the primary display in your OS settings.

### Sound System (Microphone) Setup

The application listens for voice commands using the default microphone on your system.

1.  **Connect Microphone:** Connect your desired microphone (e.g., a USB microphone, or the microphone from a lectern or soundboard) to your laptop.
2.  **Set Default Device:** In your operating system's sound settings (Windows Sound or macOS Sound), set your connected microphone as the **default input device**.
3.  **Run the GUI:** The application will automatically use this default microphone to listen for scripture references.