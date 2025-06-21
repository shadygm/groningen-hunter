import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from hunters.hunter import Hunter, Prey, browser


class Pararius(Hunter):
    def __init__(self):
        name = 'Pararius'
        super().__init__(name)

    def process(self):
        # Get list
        wait = WebDriverWait(browser, 10)
        item_list = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'search-list')))
        items = item_list.find_elements(By.TAG_NAME, 'li')

        # Process list
        preys: list[Prey] = []
        for item in items:
            try:
                # Get info
                name = item.find_element(By.CLASS_NAME, 'listing-search-item__title').text
                price_text = item.find_element(By.CLASS_NAME, 'listing-search-item__price').text
                # Remove everything except digits to build the price number
                price = re.sub(r'\D', '', price_text)
                link = item.find_element(By.CLASS_NAME, 'listing-search-item__link--title').get_attribute('href')
                info_element = item.find_element(By.CLASS_NAME, 'listing-search-item__info')
                agency = info_element.find_element(By.CLASS_NAME, 'listing-search-item__link').text

                # Add new prey
                preys.append(Prey(name, price, link, agency, self.name))
            except:
                 # Ignore if the item is incomplete or not new
                continue
        return preys

    def supported_cities(self):
        return {
            'Groningen': 'https://www.pararius.com/apartments/groningen',
            'The Hague': 'https://www.pararius.com/apartments/den-haag',
            'Amsterdam': 'https://www.pararius.com/apartments/amsterdam',
            'Rotterdam': 'https://www.pararius.com/apartments/rotterdam',
            'Enschede': 'https://www.pararius.com/apartments/enschede',
            'Hengelo': 'https://www.pararius.com/apartments/hengelo',
        }
