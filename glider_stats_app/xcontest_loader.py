# xcontest_loader.py
import re
from bs4 import BeautifulSoup

from config import DefaultConfig


XCONTEST_PAGE_SIZE = 50 
XCONTEST_BASE_URL = 'https://www.xcontest.org'
WEBDRIVER_WAIT = 3

XCONTEST_CTG = {
    2022: 5036,
    2023: 0 # ?
}

CONFIG = DefaultConfig()



async def load_pilots(driver, current_rank:int):
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
        target_url = f"{XCONTEST_BASE_URL}/{year}/world/en/ranking-pg-sport/?#ranking[start]={XCONTEST_PAGE_SIZE*page_num}@flights_scored=all" 
        print(target_url)
        pilots = load_pilots_page(driver,target_url)
        res.extend(pilots)
        # next
        page_num += 1

    print(f"pilots data length: {len(res)}")
    return res


def load_pilots_page(driver,target_url:str):
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException

    pilots, page_source = [], ""
    driver.implicitly_wait(2)
    driver.get(target_url)
    try:        
        wait=WebDriverWait(driver, WEBDRIVER_WAIT)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ol.XCrank"))) # need to make sure a new page is always replaced?!
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.for-flights-fill")))
        page_source = driver.page_source
    except TimeoutException:    
            print("Timeout occurred for", target_url)
    #finally:
    #    driver.quit() # ?

    if page_source:
        soup = BeautifulSoup(page_source, 'html.parser')
        table = soup.find('ol',{'class':"XCrank"})
        #print(table)
        for pilot in table.findChildren('li'):
            #print(pilot)
            xc_rank = pilot['value'] # to track 
            user_link = pilot.find('a',{'class':"name"})['href']
            username = user_link[user_link.find('detail:')+7:]
            pilot_id = None
            pilot_flights_details = pilot.findAll('a')[1]['href']
            id_search = re.search('flights_scored=(\d+)',pilot_flights_details)
            pilot_id = id_search.group(1) if id_search else 0
            #print(xc_rank, username, pilot_id)
            # flights block
            flights = []
            flights_div = pilot.find("div", {'class':"for-flights-fill"})
            if flights_div:
                fl_table = flights_div.find("table") 
                for row in fl_table.findChildren('tr'):
                    #print(row)
                    cols = row.findAll('td')
                    #print(cols)
                    flight_title = cols[0]['title']                    
                    flight_id = flight_title[flight_title.find('FLID:')+5:]                       
                    launch = f"{cols[3].find('a').text} ({cols[3].find('span',{'class':'cic'}).text})"
                    flight_type = cols[4].find('div')['title']
                    flight_length = cols[5].find('strong').text
                    flight_points = cols[6].find('strong').text
                    glider = cols[7].find('div')['title']
                    details = cols[9].find('a')['href']
                    #print(pilot_id, flight_id, launch,flight_type,flight_length,flight_points, glider, details)
                    flights.append({
                        'flight_id':int(flight_id),
                        'launch':launch,
                        'flight_type': flight_type,
                        'flight_length': flight_length,
                        'flight_points': flight_points, 
                        'glider': glider,
                        'details': details
                    })

            pilots.append({
               'xc_rank':int(xc_rank), 
               'username':username, 
               'pilot_id': int(pilot_id),
               'flights': flights
             })

    return pilots