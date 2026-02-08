import tkinter as tk

class FadingText(tk.Text):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.fade_steps = 10  # Number of steps for the fade animation
        self.fade_delay = 50  # Milliseconds between fade steps

    def _fade(self, direction, step=0):
        """
        Internal method to handle the fade animation.
        - direction: 1 for fade-in, -1 for fade-out
        """
        if (direction == 1 and step > self.fade_steps) or \
           (direction == -1 and step > self.fade_steps):
            return

        # Calculate the gray level for the current step
        if direction == 1:  # Fade in (black to white)
            gray_level = int(255 * (step / self.fade_steps))
        else:  # Fade out (white to black)
            gray_level = int(255 * (1 - (step / self.fade_steps)))

        # Format as a hex color string (e.g., #RRGGBB)
        color = f"#{gray_level:02x}{gray_level:02x}{gray_level:02x}"
        self.config(fg=color)

        # Schedule the next step of the animation
        self.after(self.fade_delay, self._fade, direction, step + 1)

    def fade_in(self):
        """Starts the fade-in animation."""
        self._fade(1)

    def fade_out(self):
        """Starts the fade-out animation."""
        self._fade(-1)

    async def change_text(self, new_text):
        """
        A coroutine to smoothly transition from the current text to new text
        by fading out, updating, and fading back in.
        """
        import asyncio

        # Fade out the old text
        self.fade_out()
        await asyncio.sleep(self.fade_steps * self.fade_delay / 1000)

        # Update the text content
        self.delete("1.0", tk.END)
        self.insert(tk.END, new_text)

        # Fade in the new text
        self.fade_in()
        await asyncio.sleep(self.fade_steps * self.fade_delay / 1000)