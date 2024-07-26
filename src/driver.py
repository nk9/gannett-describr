import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options


def driver(use_dummy):
    driver = DummyDriver()

    if not use_dummy:
        options = uc.ChromeOptions()
        options.add_argument("--user-data-dir=selenium")
        options.add_argument("--disk-cache-size=1024300000")
        options.add_argument("--window-size=1504,1573")  # broken?
        options.add_argument("--window-position=1504,25")  # broken?

        driver = uc.Chrome(options=options)

    return driver


class DummyDriver:
    def get(self, url):
        pass

    def execute_script(self, script):
        pass
