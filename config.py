import os
from dotenv import load_dotenv,dotenv_values

class DefaultConfig:
    
    load_dotenv()

    PORT = 3977
    ROOT_PATH = os.getenv("GLIDER_STATS_APP_ROOT_PATH", "")
    XCONTEST_MAX_PAGE_NUM =  os.getenv("XCONTEST_MAX_PAGE_NUM", 2)
    ALLOW_DELETE = os.getenv("ALLOW_DELETE", str(False)).lower() in ("yes", "y", "true", "1", "t")