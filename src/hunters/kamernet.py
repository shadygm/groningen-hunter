from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from hunters.hunter import Hunter, Prey


class Kamernet(Hunter):
    def __init__(self):
        name = 'Kamernet'
        super().__init__(name)

    def process(self, browser):
        # Get list
        wait = WebDriverWait(browser, 10)

        # Locate the container holding listings (adjust if necessary)
        listings_container = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'ListingsGrid_root__2kNRD')))
        listings = listings_container.find_elements(By.CLASS_NAME, 'SearchResultCard_root__hSxn3')

        preys: list[Prey] = []
        for listing in listings:
            try:
                name = listing.find_element(By.CLASS_NAME, 'MuiTypography-subtitle1').text[:-1]
                price = listing.find_element(By.CLASS_NAME, 'MuiTypography-h5').text.replace("€", "").replace(",", "")
                link = listing.get_attribute('href')
                agency = 'No Agency'
                preys.append(Prey(name, price, link, agency, self.name))
            except:
                continue
        return preys

    def supported_cities(self):
        return {
            'Groningen': 'https://kamernet.nl/en/for-rent/properties-groningen',
            'The Hague': 'https://kamernet.nl/en/for-rent/properties-den-haag',
            'Enschede': 'https://kamernet.nl/en/for-rent/properties-enschede',
            'Hengelo': 'https://kamernet.nl/en/for-rent/properties-hengelo',
            'Rotterdam': 'https://kamernet.nl/en/for-rent/properties-rotterdam'
        }
