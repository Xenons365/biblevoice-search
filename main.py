import asyncio
from ui import start_cli

if __name__ == "__main__":
    try:
        asyncio.run(start_cli())
    except KeyboardInterrupt:
        print("\nApplication closed by user.")