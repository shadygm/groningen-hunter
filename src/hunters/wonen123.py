import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from hunters.hunter import Hunter, Prey, browser


class Wonen123(Hunter):
    def __init__(self):
        name = '123Wonen'
        super().__init__(name)

    def process(self):
        # Get list
        wait = WebDriverWait(browser, 10)
        items_wrap = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'pandlist')))
        items = items_wrap.find_elements(By.CSS_SELECTOR, '.pandlist-container')

        # Process items
        preys: list[Prey] = []
        for item in items:
            name = item.find_element(By.CLASS_NAME, 'pand-address').text
            price = item.find_element(By.CLASS_NAME, 'pand-price').text
            price = re.search(r'\d+(?:\.\d+)?', price).group().replace(".", "")
            link = item.find_element(By.CLASS_NAME, 'textlink-design').get_attribute('href')
            agency = self.name
            preys.append(Prey(name, price, link, agency, self.name))
        return preys

    def supported_cities(self):
        return {
            'Groningen': 'https://www.expatrentalsholland.com/offer/in/groningen',
            'The Hague': 'https://www.expatrentalsholland.com/offer/in/den+haag',
            'Enschede': 'https://www.expatrentalsholland.com/offer/in/enschede',
            'Hengelo': 'https://www.expatrentalsholland.com/offer/in/hengelo',
        }
