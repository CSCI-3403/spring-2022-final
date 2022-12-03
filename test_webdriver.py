from seleniumwire import webdriver

options = {
    'addr': 'support',  # Address of the machine running Selenium Wire. Explicitly use 127.0.0.1 rather than localhost if remote session is running locally.
    'port': '8080',
}

firefox_options = webdriver.FirefoxOptions()
driver = webdriver.Remote(
    command_executor='http://localhost:4444',
    seleniumwire_options=options,
    options=firefox_options,
)

driver.get("http://neverssl.com")
print(driver.page_source)

driver.quit()