import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# Set browser and driver paths for Chromium
CHROME_BIN       = "/usr/bin/chromium"
CHROMEDRIVER_BIN = "/usr/bin/chromedriver" # chromium-driver's binary is chromedriver

# Configure browser
options = webdriver.ChromeOptions()
options.binary_location = CHROME_BIN
options.add_argument("--headless=new") # modern headless mode
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service(CHROMEDRIVER_BIN)
browser = webdriver.Chrome(service=service, options=options)

class Prey:
    def __init__(self, name, price, link, agency, website):
        self.name = name
        self.price = price
        self.link = link
        self.agency = agency
        self.website = website

    def __str__(self):
        return f"{self.name} | {self.link} | {self.agency} | {self.price}"

class Hunter:
    def __init__(self, name: str):
        self.name = name
        self.urls: list[str] = []

    def start(self):
        pass

    def stop(self):
        browser.close()

    def hunt(self):
        preys: list[Prey] = []
        for (i, url) in enumerate(self.urls):
            browser.get(url)
            preys.extend(self.process())
            if i < len(self.urls) - 1: time.sleep(2) # delay between requests to avoid 429
        return preys

    def process(self) -> list[Prey]:
        # This method should be overloaded by derived classes
        raise NotImplementedError(f"process not implemented for {self.name}")

    def supported_cities(self) -> dict[str, str]:
        # This method should be overloaded by derived classes
        raise NotImplementedError(f"supported_cities not implemented for {self.name}")

    # Set the cities and return unsupported ones
    def set_cities(self, cities: set[str]) -> set[str]:
        all_cities = self.supported_cities()

        # Set URLs for supported cities
        intersection = cities & set(all_cities.keys())
        self.urls = [all_cities[city] for city in intersection]

        # Return the unsupported cities
        return cities - intersection
