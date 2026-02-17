import logging
import os

from dotenv import load_dotenv
from pythonjsonlogger.json import JsonFormatter
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID") or "0")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH") or ""
TELEGRAM_SESSION_NAME = os.getenv("TELEGRAM_SESSION_NAME") or "telegram_session"

SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING")

logger = logging.getLogger("telegram_mcp")
logger.setLevel(logging.ERROR)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)

script_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(script_dir, "mcp_errors.log")

try:
    file_handler = logging.FileHandler(log_file_path, mode="a")
    file_handler.setLevel(logging.ERROR)

    console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    json_formatter = JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    file_handler.setFormatter(json_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.info(f"Logging initialized to {log_file_path}")
except Exception as log_error:
    print(f"WARNING: Error setting up log file: {log_error}")
    logger.addHandler(console_handler)
    logger.error(f"Failed to set up log file handler: {log_error}")


if SESSION_STRING:
    client = TelegramClient(StringSession(SESSION_STRING), TELEGRAM_API_ID, TELEGRAM_API_HASH)
else:
    client = TelegramClient(TELEGRAM_SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)


async def start_client() -> None:
    """Start the Telegram client connection."""
    await client.start()
    logger.info("Telegram client started successfully")
