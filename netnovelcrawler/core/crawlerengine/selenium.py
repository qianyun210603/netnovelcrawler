from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait


class SeleniumEngine:

    def __init__(self, driver: Chrome = None):
        self.driver = driver if driver is not None else self._get_default_driver()

    def __del__(self):
        self.driver.quit()

    @staticmethod
    def _get_default_driver():
        option = ChromeOptions()
        # switch of developer tool, exclude to avoid being identified
        option.add_experimental_option("excludeSwitches", ["enable-automation"])
        return Chrome(options=option)

    def login(self, login_info: dict, login_page: str):
        try:
            self._auto_login(login_info, login_page)
        except Exception:
            self.driver.get(login_page)
        finally:
            self._wait_until_logged_in()

    def _auto_login(self, login_info, login_page):
        raise NotImplementedError("If there is customized automated login method, implement in derived class")

    def _wait_until_logged_in(self, max_wait_time=120):
        wait = WebDriverWait(self.driver, max_wait_time)
        wait.until(self._logged_in_condition())

    def _logged_in_condition(self):
        raise NotImplementedError("implement in derived class")
