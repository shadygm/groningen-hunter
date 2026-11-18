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
                price = self.parse_price(item)
                link = item.find_element(By.CLASS_NAME, 'listing-search-item__link--title').get_attribute('href')
                info_element = item.find_element(By.CLASS_NAME, 'listing-search-item__info')
                agency = info_element.find_element(By.CLASS_NAME, 'listing-search-item__link').text

                # Add new prey
                preys.append(Prey(name, price, link, agency, self.name))
            except:
                 # Ignore if the item is incomplete or not new
                continue
        return preys

    @staticmethod
    def parse_price(item) -> str:
        """Monthly rent as a digit string, or '' when the price is on request.

        Some cards show both a bare rent and a total rent (incl. service costs), e.g.
        "Bare rental price €643 pcm / Total rental price €743 per month". Prefer the
        total, since that is what the tenant pays; otherwise use the single price shown.
        """
        total = item.find_elements(By.CLASS_NAME, 'price-transparency-badge__total-price-value')
        if total:
            price_text = total[0].get_attribute('textContent')
        else:
            price_text = item.find_element(By.CLASS_NAME, 'listing-search-item__price').get_attribute('textContent')
        # Take only the first euro amount, so two prices are never glued together
        match = re.search(r'€\s*([\d.,]+)', price_text)
        return re.sub(r'\D', '', match.group(1)) if match else ''

    def supported_cities(self):
        return {
            'Groningen': 'https://www.pararius.com/apartments/groningen',
            'The Hague': 'https://www.pararius.com/apartments/den-haag',
            'Amsterdam': 'https://www.pararius.com/apartments/amsterdam',
            'Rotterdam': 'https://www.pararius.com/apartments/rotterdam',
            'Enschede': 'https://www.pararius.com/apartments/enschede',
            'Hengelo': 'https://www.pararius.com/apartments/hengelo',
        }
