import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.environ["FEISHU_APP_ID"]
APP_SECRET = os.environ["FEISHU_APP_SECRET"]
USER_EMAIL = os.environ["FEISHU_USER_EMAIL"]

# Optional: pre-obtained user_access_token (expires in ~2h)
# If not set, the script uses tenant_access_token (requires mailbox admin permission)
USER_ACCESS_TOKEN = os.getenv("FEISHU_USER_ACCESS_TOKEN", "")

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
# How many days back to search (0 = all)
DAYS_BACK = int(os.getenv("DAYS_BACK", "30"))
