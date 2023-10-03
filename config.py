import os
from dotenv import load_dotenv,dotenv_values

class DefaultConfig:
    
    load_dotenv()

    PORT = 3978
    XCONTEST_MAX_PAGE_NUM =  os.getenv("XCONTEST_MAX_PAGE_NUM", 2)