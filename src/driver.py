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

        driver = uc.Chrome(options=options, enable_cdp_events=True)

    return driver


class DummyDriver:
    # def get(self, url):
    #     pass

    # def execute_script(self, script):
    #     pass

    # def add_cdp_listener(self, message, func):
    #     pass

    # def quit(self):
    #     pass
    def __getattr__(self, name):
        # Return self so that any attribute or method access returns the object itself
        return self

    def __call__(self, *args, **kwargs):
        # Allow the object to be called like a function and do nothing
        return self
