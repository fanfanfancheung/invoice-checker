import os
from dotenv import load_dotenv

load_dotenv()

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
DAYS_BACK = int(os.getenv("DAYS_BACK", "30"))
