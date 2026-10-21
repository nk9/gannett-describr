import shutil
import subprocess
from pathlib import Path

import undetected_chromedriver as uc
from gannett_fs import USER_AGENT
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.driver_finder import DriverFinder
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

        driver_path, version = native_chromedriver()
        driver = uc.Chrome(
            options=options,
            enable_cdp_events=True,
            driver_executable_path=str(driver_path),
            version_main=int(version.split(".")[0]),
        )

    return driver


def native_chromedriver():
    """A chromedriver for this machine's architecture and Chrome version, for uc to patch.

    uc 3.5.5 always downloads the mac-x64 driver and re-patches it on every launch,
    so it ran under Rosetta as a brand-new binary each time. Selenium Manager fetches
    the right driver; we patch our own copy once and reuse it.
    """
    source = Path(DriverFinder(Service(), Options()).get_driver_path())
    version = source.parent.name  # ~/.cache/selenium/chromedriver/mac-arm64/<version>/chromedriver
    target = Path(uc.Patcher.data_path) / f"chromedriver_{version}"

    if not target.exists():
        patching = target.with_name(f"{target.name}.tmp")
        shutil.copy2(source, patching)
        uc.Patcher(executable_path=str(patching)).auto()

        # Patching breaks the signature, and macOS kills unsigned arm64 binaries
        subprocess.run(["codesign", "--force", "--sign", "-", patching], check=True)
        patching.rename(target)

    return target, version


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
