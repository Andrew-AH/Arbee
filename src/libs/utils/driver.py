from selenium_driverless.sync import webdriver


def get_chrome_driver(headless: bool = True):
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.headless = headless
    return webdriver.Chrome(options=options)
