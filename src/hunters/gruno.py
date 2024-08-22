from hunters.hunter import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import re

class Gruno(Hunter):
    def __init__(self):
        name = 'Gruno Verhuur'
        url = 'https://www.grunoverhuur.nl/woningaanbod/huur/groningen'
        super().__init__(name, url)

    def process(self):
        # Get list or rows
        wait = WebDriverWait(browser, 10)
        rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//div[@class="object_list col-md-12"]//div[@class="row"]')))
        items = []

        # Get items in each row
        for row in rows:
            row_items = row.find_elements(By.XPATH, './article')
            items.extend(row_items)

        # Process items
        preys = []
        for item in items:
            try:
                name = item.find_element(By.CLASS_NAME, 'obj_address').text
                name = name.replace('Te huur: ', '')
                price = item.find_element(By.CLASS_NAME, 'obj_price').text
                price = re.search(r'\d+(?:\.\d+)?', price).group().replace(".", "")
                link = item.find_element(By.CLASS_NAME, 'datacontainer').find_element(By.XPATH, './a').get_attribute('href')
                agency = self.name
                preys.append(Prey(name, price, link, agency, self.name))
            except:
                 # Ignore incomplete items
                continue
        return preys
