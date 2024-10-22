# driver.py

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


def setup_web_driver(app):
    options = Options()
    #options.headless = True # must stay on to avoid "selenium.common.exceptions.UnexpectedAlertPresentException: Alert Text: Access forbidden for remote IP address ... "
    app.driver = webdriver.Chrome( options=options)