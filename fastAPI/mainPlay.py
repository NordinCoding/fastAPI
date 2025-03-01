from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import datetime


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
    with open("scraper_logs.txt", "a") as file:
        file.write(log_entry)


def bol_scraper(URL):
    """
    Scrapes product information from Bol.com
    
    Args:
        URL (str): Full Bol.com product URL
        
    Returns:
        dict: Product details including name, current price and original price
    """
    
    with sync_playwright() as p:
        try:
            # Create a headless browser instance and give it context to imitate a real user
            log_to_file("Initializing Bol.com scraper browser instance", "DEBUG")
            
            browser = p.firefox.launch(
                headless=False,
                args=["--no-sandbox", "--disable-extensions", "--disable-dev-shm-usage"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="NL",
                timezone_id="Netherlands/Amsterdam",
                accept_downloads=True,
                bypass_csp=True
            )

            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

  
            # Go to the URL and wait for the page to load
            log_to_file("Navigating to Bol.com product page", "DEBUG")
            
            page = browser.new_page()
            try:
                page.goto(URL, wait_until="networkidle", timeout=5000)
            except Exception as e:
                log_to_file(f"Failed to load page: {str(e)}", "ERROR")
                return {"error": "Page not found", "details": str(e)}
            log_to_file("Page loaded successfully", "DEBUG")
            
            
            # Wait for the accept cookies button to be visible and enabled, then click it
            log_to_file("Accepting cookies", "DEBUG")
            
            try:
                page.wait_for_selector("button#js-first-screen-accept-all-button", state="visible", timeout=5000)
                time.sleep(0.5)
                page.click("button#js-first-screen-accept-all-button")
            except Exception as e:
                log_to_file(f"Failed to accept cookies: {str(e)}", "ERROR")
                return {"error": "Cookies button not found", "details": str(e)}


            # Wait for the country/language button to be visible and enabled, then click it
            log_to_file("Selecting country/language", "DEBUG")
            
            try:
                button = page.locator('[class="ui-btn ui-btn--primary  u-disable-mouse js-country-language-btn"]')
                button.wait_for(state="visible", timeout=5000)
                time.sleep(0.2)
                button.click()
            except Exception as e:
                log_to_file(f"Failed to select country/language: {str(e)}", "ERROR")
                return {"error": "Country/language button not found", "details": str(e)}

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
                page.wait_for_selector('[class="promo-price"]', state="visible", timeout=5000)
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
        
        except Exception as e:
            log_to_file(f"An error occurred: {str(e)}", "ERROR")
            return {"error": "An error occurred", "details": str(e)}
        finally:
            if 'browser' in locals():
                log_to_file("Closing browser, scraping succesful", "DEBUG")
                browser.close()
        

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
