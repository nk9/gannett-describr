import undetected_chromedriver as uc
from gannett_fs import USER_AGENT
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import Chrome


def driver(use_dummy=False, use_offline=False):
    driver = DummyDriver()
    custom_agent = USER_AGENT

    if use_offline:
        options = Options()
        options.add_argument("--user-data-dir=selenium")
        options.add_argument("--disk-cache-size=1024300000")

        options.add_argument(f"--user-agent={custom_agent}")

        driver = Chrome(options=options)
    elif not use_dummy:
        options = uc.ChromeOptions()
        options.add_argument("--user-data-dir=selenium")
        options.add_argument("--disk-cache-size=1024300000")
        options.add_argument("--window-size=1504,1573")  # broken?
        options.add_argument("--window-position=1504,25")  # broken?

        options.add_argument(f"--user-agent={custom_agent}")

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
