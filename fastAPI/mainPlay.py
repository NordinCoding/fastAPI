from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import datetime
import random


def log_to_file(message, level="INFO"):
    """
    Log a message to a file with timestamps

    Args:
        message (str): Message to log
        level (str): Log level of severity (default: "INFO")
    """

    # Create formatted error message with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {level}: {message}\n"

    # Write the log entry to the log file
    with open("scraper_logs.txt", "a", encoding="utf-8") as file:
        file.write(log_entry)


def bol_scraper(URL):
    """s
    Scrapes product information from Bol.com

    Args:
        URL (str): Full Bol.com product URL

    Returns:
        dict: Product details including name, current price and original price
    """
    user_agent_strings = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko",
    ]

    proxies = [
        {"server": "http://166.0.35.15:6524"},#GOOD
        {"server": "http://23.27.65.71:5574"},#GOOD
        {"server": "http://166.0.37.79:5588"},#GOOD
        {"server": "http://45.39.212.203:8746"},#GOOD
        {"server": "http://82.23.97.234:7960"},#GOOD
        {"server": "http://45.39.150.33:8267"},#GOOD
        {"server": "http://166.0.41.244:6752"},#GOOD
        {"server": "http://166.0.36.52:6061"},#GOOD
        {"server": "http://166.0.47.113:6620"},#GOOD
        {"server": "http://150.241.117.165:5669"},#GOOD
        {"server": "http://104.253.248.15:5794"},#GOOD
        {"server": "http://166.0.40.8:7016"},#GOOD
        {"server": "http://166.0.36.235:6244"},#GOOD
        {"server": "http://166.0.34.109:7118"},#GOOD
        {"server": "http://45.39.157.230:9262"},#GOOD
        {"server": "http://46.203.184.203:7470"}]#GOOD
    
    
    with sync_playwright() as p:
        try:
            # Create a headless browser instance and give it extra context to imitate a real user
            log_to_file("Initializing Bol.com scraper browser instance", "DEBUG")

            browser = p.firefox.launch(
                #Rotatig proxies to avoid getting blocked
                proxy={"server": proxies[15]["server"],
                       "username": "syhmtvia",
                       "password": "jja001k6t9wu"},
                headless=False,
                slow_mo=100,
                timeout=10000,
                args=["--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-audio-output",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-breakpad",
                "--disable-component-extensions-with-background-pages",
                "--disable-features=TranslateUI,BlinkGenPropertyTrees",
                "--disable-ipc-flooding-protection",
                ]
            )
            context = browser.new_context(
                user_agent=random.choice(user_agent_strings),
                locale="NL",
                viewport={"width": 1920, "height": 1080},
                timezone_id="Europe/Amsterdam",
                accept_downloads=True,
                bypass_csp=True
            )
            
            context.add_cookies([
                {'name': 'cookie_consent', 'value': 'true', 'domain': 'example.com', 'path': '/'}
            ])

            context.set_default_timeout(10000)

            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)


            # Create a new page, Go to the URL and wait for the page to load
            log_to_file("Creating new page", "DEBUG")
            try:
                page = context.new_page()
            except Exception as e:
                log_to_file(f"Failed to create new page: {str(e)}", "ERROR")
                return {"error": "Failed to create new page", "details": str(e)}

            log_to_file("Navigating to Bol.com product page", "DEBUG")
            try:
                page.goto(URL)
                time.sleep(random.uniform(0.5, 1.0))
            except Exception as e:
                log_to_file(f"Failed to load page: {str(e)}", "ERROR")
                return {"error": "Page not found", "details": str(e)}
            log_to_file("Page loaded successfully", "DEBUG")


            # Wait for the accept cookies button to be visible and enabled, then click it
            log_to_file("Accepting cookies", "DEBUG")

            try:
                log_to_file(page.inner_html('[class="modal__window js_modal_window"]'), "DEBUG")
                page.wait_for_selector('[class="ui-btn ui-btn--primary ui-btn--block@screen-small"]')
                time.sleep(random.uniform(0.5, 1.0))
                page.click('[class="ui-btn ui-btn--primary ui-btn--block@screen-small"]')
            except Exception as e:
                log_to_file(f"Failed to accept cookies: {str(e)}", "ERROR")
                return {"error": "Cookies button not found", "details": str(e)}
            log_to_file("Cookies accepted", "DEBUG")


            # Wait for the country/language button to be visible and enabled, then click it
            log_to_file("Selecting country/language", "DEBUG")

            try:
                page.wait_for_selector('[class="ui-btn ui-btn--primary  u-disable-mouse js-country-language-btn"]')
                time.sleep(random.uniform(0.5, 1.0))
                page.click('[class="ui-btn ui-btn--primary  u-disable-mouse js-country-language-btn"]')
            except Exception as e:
                log_to_file(f"Failed to select country/language: {str(e)}", "ERROR")
                return {"error": "Country/language button not found", "details": str(e)}
            log_to_file("Selected country/language Successfully", "DEBUG")

            # Create dictionary to store the product details
            dictValues = {
                "name": "",
                "currentPrice": "",
                "ogPrice": ""
            }

            # Wait for the promo price, the list-price and name elements to be visible and get its inner HTML/text
            # The inner HTML/text is then cleaned up and stored in the dictionary so it can be returned to the main script
            log_to_file("Scraping and formatting product data and storing it in dictValues", "DEBUG")

            try:
                page.wait_for_selector('[class="promo-price"]', state="visible")
                time.sleep(0.2)
                dictValues["name"] = page.inner_html('[class="u-mr--xs"]').replace("\n", "").strip().replace("&amp;", "&")
                dictValues["currentPrice"] = page.locator('[class="promo-price"]').first.inner_text().replace("\n", ".").replace(",", ".").replace("-", "00").strip()

                visible = page.locator('[class="h-nowrap buy-block__list-price"]').is_visible()
                if visible:
                    dictValues["ogPrice"] = page.locator('[class="h-nowrap buy-block__list-price"]').first.inner_html().replace("\n", "").replace(",", ".").replace("-", "00").strip()
                else:
                    dictValues["ogPrice"] = dictValues["currentPrice"]
            except Exception as e:
                log_to_file(f"Failed to find product data or error altering product data: {str(e)}", "ERROR")
                return {"error": "Failed to find product data or error altering product data", "details": str(e)}

            return dictValues

        finally:
            try:
                if browser:
                    log_to_file("Closing browser, scraping successful\n", "DEBUG")
                    browser.close()
            except NameError:
                log_to_file("Browser was never initialized, skipping close", "WARNING")
            except Exception as e:
                log_to_file(f"Error while closing browser: {str(e)}", "ERROR")



def test_scraper():
    #Simple test function to verify the scraper works correctly

    #Regular product with while number discount price(currentPrice) and decimal orginal price(ogPrice)"
    test_url = "https://www.bol.com/nl/nl/p/lynnz-schoenlepel-lang-zwart-metaal-rvs-42-cm-met-leren-handgreep-stevig-leer-schoentrekker-schoen-lepel-schoenlepels/9300000072529393/?bltgh=jJfsF2XpJwjWWuh33qFIfg.2_57.59.ProductImage"


    result = bol_scraper(test_url)

    # Check that the result has the expected structure
    assert isinstance(result, dict), "Result should be a dictionary"
    assert "name" in result, "Result should contain product name"
    assert "currentPrice" in result, "Result should contain current promo price"
    assert "ogPrice" in result, "Result should contain original price"

    # Print test results for manual verification
    print("Test passed successfully!")
    print(f"Product: {result['name']}")
    print(f"Current price: {result['currentPrice']}")
    print(f"Original price: {result['ogPrice']}")

    return result

if __name__ == "__main__":
    dictValues = bol_scraper("https://www.bol.com/nl/nl/p/msi-mpg-321urx-qd-oled-4k-gaming-monitor-usb-c-90w-kvm-240hz-32-inch/9300000170615582/?s2a=&bltgh=lA0upNIJYGjnpqDtg19Lcw.2_72_73.74.FeatureOptionButton#productTitle")
    print(dictValues)

    # Uncomment the line below to run the test function
    # results = test_scraper()
    # print(results)

