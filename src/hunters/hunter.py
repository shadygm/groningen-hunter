import time
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import WebDriver

# Set browser and driver paths for Chromium
CHROME_BIN       = "/usr/bin/chromium"
CHROMEDRIVER_BIN = "/usr/bin/chromedriver" # chromium-driver's binary is chromedriver

# Fallback user agent, only used if reading the live one fails
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Upper bound for the HTTP cache of the browser profile. The profile lives in
# the temp dir, which is RAM-backed (tmpfs) on some systems.
DISK_CACHE_BYTES = 16 * 1024 * 1024

# How long one browser is kept before it is replaced, to cap Chromium's slow growth
BROWSER_MAX_AGE_SECONDS = 24 * 60 * 60

def start_browser() -> WebDriver:
    """Launch headless Chromium.

    No --user-data-dir: ChromeDriver then creates a throwaway profile and deletes it
    on quit. A profile path of our own would not be deleted under snap Chromium
    (Ubuntu), which writes /tmp paths into its own private /tmp instead.
    """
    options = webdriver.ChromeOptions()
    options.binary_location = CHROME_BIN
    options.add_argument("--headless=new") # modern headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US,en")
    options.add_argument(f"--disk-cache-size={DISK_CACHE_BYTES}")
    # Stop Chrome from downloading its ~40 MB on-device ML models into the profile
    options.add_argument("--disable-features=OptimizationGuideModelDownloading,OptimizationHintsFetching,"
                         "OptimizationTargetPrediction,OptimizationHints")
    # Reduce the most obvious automation fingerprints that passive bot-detection
    # (Cloudflare / DataDome on Kamernet and Pararius) checks for.
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    browser = webdriver.Chrome(service=Service(CHROMEDRIVER_BIN), options=options)
    try:
        # Headless Chrome advertises "HeadlessChrome" in its UA and sets
        # navigator.webdriver=true; both are trivial bot tells. Strip the first (using
        # the browser's real version so we don't mismatch) and mask the second.
        try:
            live_ua = browser.execute_script("return navigator.userAgent")
            ua = live_ua.replace("HeadlessChrome", "Chrome") if live_ua else USER_AGENT
        except WebDriverException:
            ua = USER_AGENT
        browser.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": ua})
        browser.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"},
        )
    except BaseException:
        browser.quit()
        raise
    return browser

class SharedBrowser:
    """
    One long-lived Chromium for all hunters.
    Parked on about:blank while idle so no site's scripts keep running.
    Replaced once a day, or as soon as it dies, so its memory stays bounded.
    """
    def __init__(self):
        self.browser: Optional[WebDriver] = None
        self.started_at = 0.0

    def get(self) -> WebDriver:
        if self.browser is not None:
            if time.monotonic() - self.started_at > BROWSER_MAX_AGE_SECONDS:
                print('Restarting the browser to release memory')
                self.close()
            elif not self._is_alive():
                print('The browser stopped responding, restarting it')
                self.close()
        if self.browser is None:
            self.browser = start_browser()
            self.started_at = time.monotonic()
        return self.browser

    def park(self):
        """Leave the current page so it frees its memory and stops using CPU."""
        if self.browser is None:
            return
        try:
            self.browser.get('about:blank')
        except Exception: # a dead ChromeDriver raises connection errors, not WebDriverException
            self.close()

    def close(self):
        if self.browser is not None:
            try:
                self.browser.quit()
            except Exception:
                pass # already gone
            self.browser = None

    def _is_alive(self) -> bool:
        try:
            self.browser.current_url # any cheap command
            return True
        except Exception:
            return False

class Prey:
    def __init__(self, name: str, price: str, link: str, agency: str, website: str, city: str = None):
        self.name = name
        self.price = price
        self.link = link
        self.agency = agency
        self.website = website
        self.city = city

    def __hash__(self):
        return hash(self.link)

    def __eq__(self, other):
        if not isinstance(other, Prey):
            return False
        return self.link == other.link

    def __str__(self):
        return f"{self.name} | {self.link} | {self.agency} | {self.price}"

class Hunter:
    def __init__(self, name: str):
        self.name = name
        self.city_urls: dict[str, str] = {}

    def start(self):
        pass

    def stop(self):
        pass

    def hunt(self, browser: WebDriver):
        preys: set[Prey] = set()
        city_urls = list(self.city_urls.items())
        for (i, (city, url)) in enumerate(city_urls):
            browser.get(url)
            try:
                found = self.process(browser)
            except TimeoutException:
                print(f'[{self.name}] No listings for {city}: timed out waiting for '
                      f'the results container at {url} (page title: "{browser.title}").')
                found = []
            for prey in found:
                prey.city = city
                preys.add(prey) # add to set (avoids duplicates)
            if i < len(city_urls) - 1: time.sleep(2) # delay between requests to avoid 429
        return preys

    def process(self, browser: WebDriver) -> list[Prey]:
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
        self.city_urls = {city: all_cities[city] for city in intersection}

        # Return the unsupported cities
        return cities - intersection
