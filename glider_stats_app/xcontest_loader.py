# xcontest_loader.py
import os
import requests
import aiohttp
#from bs4 import BeautifulSoup


from config import DefaultConfig


XCONTEST_PAGE_SIZE = 50 
XCONTEST_BASE_URL = 'https://www.xcontest.org'

XCONTEST_CTG = {
    2022: 5036,
    2023: 0 # ?
}

CONFIG = DefaultConfig()



async def load_pilots(current_rank:int):
    year = 2023 # ?
    #key, param = os.environ["XCONTEST_KEY"], os.environ["XCONTEST_PARAM"]

    res = []
    print(current_rank)
    page_num = 0 
    if current_rank is not None:
        page_num = int(current_rank) // XCONTEST_PAGE_SIZE

    print(f"starting with page_num = {page_num}")
    while page_num < int(CONFIG.XCONTEST_MAX_PAGE_NUM):
        #print(page_num)
        target_url = f"{XCONTEST_BASE_URL}/{year}/world/en/ranking-pg-sport/?#ranking[start]={XCONTEST_PAGE_SIZE*page_num}" 
        print(target_url)
        pilots = await load_pilots_page(target_url)
        res.extend(pilots)
        # next
        page_num += 1

    print(f"pilots data length: {len(res)}")
    return res


async def load_pilots_page(target_url:str):
    pilots = []
    try:
        print("todo load")

    except requests.exceptions.Timeout:    
            print("Timeout occurred for", target_url)

    return pilots