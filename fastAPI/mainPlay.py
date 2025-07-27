from patchright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import time
import datetime
import random
from dotenv import load_dotenv
import os
import asyncio
import shutil
import re

load_dotenv(override=True)


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


async def bol_scraper(URL, delete=False):
    """s
    Scrapes product information from Bol.com

    Args:
    playwright (obj): Playwright instance
    URL (str): Full Bol.com product URL

    Returns:
        dict: Product details including name, current price and original price wether to delete the playwright directory(session data)
    """
    
    async with async_playwright() as playwright:
        try:
            args = ["--disable-blink-features=AutomationControlled",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"]
            
            # Create a headless browser instance and give it extra context to imitate a real user
            browser = await playwright.chromium.launch_persistent_context(
                
                # Load residential proxy from .env file
                proxy={"server": os.getenv("PROXY_SERVER"),
                "username": os.getenv("PROXY_USERNAME"),
                "password": os.getenv("PROXY_PASSWORD")},
                slow_mo=100,
                # VPS path
                user_data_dir="/home/nordinschoenmakers/fastAPI/fastAPI/playwright",	
                #Local path
                #user_data_dir="C:\\playwright",	
                headless=True, 
                args=args,
                channel="chrome",
                viewport={"width": 1920, "height": 1080},
                timeout=10000
            )
            
            
            # Create new page
            log_to_file("Creating new page and navigating to URL", "DEBUG")
            try:
                page = await browser.new_page()
            except Exception as e:
                log_to_file(f"Error creating new page: {e}", "ERROR")
                return {"error": "Failed to create new page", "details": str(e)}, True
            
            # Navigate to the URL, log which proxy is being used
            log_to_file(f"Navigating to Bol.com product page using residential proxy", "DEBUG")
            try:
                await page.goto(URL)
                time.sleep(random.uniform(0.5, 2))
            except Exception as e:
                log_to_file(f"Error navigating to URL: {e}", "ERROR")
                return {"error": "Failed to navigate to URL", "details": str(e)}, True
            log_to_file("Navigated to URL successfully", "DEBUG")
            
            
            # Create a dictionary to store the product details
            dictValues = {
                "name": "",
                "currentPrice": "",
                "ogPrice": ""
            }
            
            
            async def get_page_content():
                #Wait for the promo price, the list-price and name elements to be visible and get its inner HTML/text
                #Data is cleaned up and stored in the dictionary so it can be returned
                log_to_file("Scraping and formatting product data and storing it in dictValues", "DEBUG")
                try:
                    await page.wait_for_selector('[class="promo-price"]', state="visible", timeout=10000)
                    time.sleep(0.2)
                    
                    # Get the inner HTML of the name element, format it and store it in the dictionary
                    name_html = await page.inner_html('[class="u-mr--xs"]', timeout=10000)
                    dictValues["name"] = name_html.replace("\n", "").strip().replace("&amp;", "&")
                    
                    # Get the inner HTML of the current price element, format it and store it in the dictionarys
                    currentPrice_html = await page.locator('[class="promo-price"]').first.inner_text()
                    dictValues["currentPrice"] = currentPrice_html.replace("\n", ".").replace(",", ".").replace("-", "00").strip()
                    
                    # If the original price is not available, set it to the current price
                        # Get the inner HTML of the original price element, format it and store it in the dictionary
                    if await page.query_selector('[class="h-nowrap buy-block__list-price"]') == None:
                        dictValues["ogPrice"] = dictValues["currentPrice"]
                    else:
                        ogPrice_html = await page.locator('[class="h-nowrap buy-block__list-price"]').first.inner_html()
                        dictValues["ogPrice"] = ogPrice_html.replace("\n", "").replace(",", ".").replace("-", "00").strip()
                    return dictValues
                except Exception as e:
                    # If no price is found, look for the class that contains "Niet Leverbaar", incase its found, set price to 0
                    # so i can let the user know that the product is not available anymore
                    log_to_file("Promo price not found, looking for Niet Leverbaar class incase item is unavailable")
                    try:
                        if await page.query_selector('[class="text-18 h2 pb-4 mb-4"]') is not None:
                            # Look for name of product
                            name_html = await page.inner_html('[class="u-mr--xs"]', timeout=10000)
                            dictValues["name"] = name_html.replace("\n", "").strip().replace("&amp;", "&")
                            
                            dictValues["currentPrice"] = 0.0
                            dictValues["ogPrice"] = 0.0
                            
                            log_to_file("Product is not available, returning data that indicates unavailability")
                            return dictValues
                        
                    except Exception as e:
                        log_to_file(f"Error while checking for unavailable product class: {e}", "ERROR")
                    
                    log_to_file(f"Error scraping product data/altering product data: {e}", "ERROR")
                    return {"error": "Failed to scrape product data/alter product data", "details": str(e)}

            # Check if the cookies button is visible to determine if cookies and language need to be accepted
            # If not, scrape the content, check for an error and return the dictionary if no error is found
            if await page.query_selector('[class="ui-btn ui-btn--primary ui-btn--block@screen-small"]') == None:
                result = await get_page_content()
                if not result.get("error"):
                    log_to_file("Scraping succesful", "DEBUG")
                    return dictValues, delete
                else:
                    return result, True
            
            
            # Wait for cookies button to be visable and click it
            log_to_file("Accepting cookies", "DEBUG")
            try:
                await page.wait_for_selector('[class="ui-btn ui-btn--primary ui-btn--block@screen-small"]', timeout=10000)
                time.sleep(random.uniform(0.5, 2))
                await page.click('[class="ui-btn ui-btn--primary ui-btn--block@screen-small"]')
            except Exception as e:
                log_to_file(f"Error accepting cookies: {e}", "ERROR")
                return {"error": "Failed to accept cookies", "details": str(e)}, True
            log_to_file("succesfully accepted cookies", "DEBUG")
            
            
            # Wait for the country/language button to be visiable and enabled, then click it
            log_to_file("Selecting country/language", "DEBUG")
            try:
                # Uncomment the line below to take a screenshot of the page for debugging purposes
                # This line tends to be error prone, not sure why yet
                #wait page.screenshot(path="screenshot1.png")
                await page.wait_for_selector('[class="ui-btn ui-btn--primary  u-disable-mouse js-country-language-btn"]', timeout=10000)
                time.sleep(random.uniform(0.5, 2))
                await page.click('[class="ui-btn ui-btn--primary  u-disable-mouse js-country-language-btn"]')
            except Exception as e:
                log_to_file(f"Error selecting country/language: {e}", "ERROR")
                return {"error": "Failed to select country/language", "details": str(e)}, True
            log_to_file("Selected Country/language succesfully", "DEBUG")
            
            
            # Get the name, current price and original price of the product
            await get_page_content()
            return dictValues, delete
            
            
        finally:
            try:
                if browser:
                    log_to_file("Closing browser, check the logs for more information\n", "DEBUG")
                    await browser.close()
                else:
                    log_to_file("Browser was never initialized, skipping close", "WARNING")
                    return {"error": "Browser was never initialized", "details": "Browser was never initialized"}, True     
            except Exception as e:
                log_to_file(f"Error while closing browser: {str(e)}", "ERROR")
                return {"error": "Failed to close browser", "details": str(e)}, True




# Doesnt work due to solid bot detection from coolblue, might try to break through some day
async def coolblue_scraper(URL, delete=False):
    """s
    Scrapes product information from coolblue.nl

    Args:
    playwright (obj): Playwright instance
    URL (str): Full coolblue.nl product URL

    Returns:
        dict: Product details including name, current price and original price and wether to delete the playwright directory(session data)
    """
    
    async with async_playwright() as playwright:
        try:
            args = ["--disable-blink-features=AutomationControlled",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"]
            
            # Create a headless browser instance and give it extra context to imitate a real user
            browser = await playwright.chromium.launch_persistent_context(
                
                # Load residential proxy from .env file
                proxy={"server": os.getenv("PROXY_SERVER"),
                "username": os.getenv("PROXY_USERNAME"),
                "password": os.getenv("PROXY_PASSWORD")},
                slow_mo=100,
                # VPS path
                #user_data_dir="/home/nordinschoenmakers/fastAPI/fastAPI/playwright",	
                #Local path
                user_data_dir="C:\\playwright",	
                headless=False, 
                args=args,
                channel="chrome",
                viewport={"width": 1920, "height": 1080},
                timeout=10000
            )
            
            
            # Create new page
            log_to_file("Creating new page and navigating to URL", "DEBUG")
            try:
                page = await browser.new_page()
            except Exception as e:
                log_to_file(f"Error creating new page: {e}", "ERROR")
                return {"error": "Failed to create new page", "details": str(e)}, True
            
            # Navigate to the URL, log which proxy is being used
            log_to_file(f"Navigating to coolblue.nl product page using residential proxy", "DEBUG")
            try:
                await page.goto(URL)
                time.sleep(random.uniform(0.5, 2))
            except Exception as e:
                log_to_file(f"Error navigating to URL: {e}", "ERROR")
                return {"error": "Failed to navigate to URL", "details": str(e)}, True
            log_to_file("Navigated to URL successfully", "DEBUG")
            
            
            # Create a dictionary to store the product details
            dictValues = {
                "name": "",
                "currentPrice": "",
                "ogPrice": ""
            }
            
            async def get_page_content():
                #Wait for the price and name elements to be visible and get its inner HTML/text
                #Data is cleaned up and stored in the dictionary so it can be returned
                log_to_file("Scraping and formatting product data and storing it in dictValues", "DEBUG")
                try:
                    await page.wait_for_selector('[class="css-puih25"]', state="visible", timeout=10000)
                    time.sleep(0.2)
                    
                    # Get the inner text of the name element, format it and store it in the dictionary
                    name_html = await page.inner_html('[class="css-1o2kclk"]', timeout=10000)
                    dictValues["name"] = name_html.replace("\n", "").strip().replace("&amp;", "&")
                    
                    # Get the inner HTML of the current price element, format it and store it in the dictionarys
                    currentPrice_html = await page.locator('[class="css-puih25"]').first.inner_text()
                    dictValues["currentPrice"] = currentPrice_html.replace("\n", ".").replace(",", ".").replace("-", "00").strip()
                    
                    # If the original price is not available, set it to the current price
                    if await page.query_selector('[class="css-4q9vvt"]') == None:
                        dictValues["ogPrice"] = dictValues["currentPrice"]
                        
                    # Get the inner text of the original price element, format it and store it in the dictionary
                    else:
                        ogPrice_html = await page.locator('[class="css-4q9vvt"]').first.inner_text()
                        dictValues["ogPrice"] = ogPrice_html.replace("\n", "").replace(",", ".").replace("-", "00").strip()
                    
                    # Check to see product availability
                    try:
                        await page.wait_for_selector('[class="css-s6m3qa"]', timeout=2000)
                        
                        # Set price values to 0. Indicating unavailable product
                        dictValues["currentPrice"] = 0.0
                        dictValues["ogPrice"] = 0.0   
                        
                        log_to_file("Product is not available, returning data that indicates unavailability")
                    
                    # Hitting except block indidicates product is available
                    except PlaywrightTimeoutError:
                        log_to_file("Product available and price data found, returning dictValues")
                        
                    return dictValues
                             
                except Exception as e:
                    log_to_file(f"Error scraping product data/altering product data: {e}", "ERROR")
                    return {"error": "Failed to scrape product data/alter product data", "details": str(e)}
                    


            # Check if the cookies button is visible to determine if cookies need to be accepted
            # If not, scrape the content, check for an error and return the dictionary if no error is found
            
            try:
                await page.wait_for_selector('[class="css-ulyxa5"]', timeout=3000)
            except:
                log_to_file("Cookies button not found, continuing to get_page_content")
                result = await get_page_content()
                if not result.get("error"):
                    log_to_file(f"Scraping succesful, result: {result}", "DEBUG")
                    return dictValues, delete
                else:
                    return result, True
            
            
            # Wait for cookies button to be visable and click it
            log_to_file("Accepting cookies", "DEBUG")
            try:
                await page.wait_for_selector('[class="css-ulyxa5"]', timeout=10000)
                time.sleep(random.uniform(0.5, 2))
                await page.click('[class="css-ulyxa5"]')
            except Exception as e:
                log_to_file(f"Error accepting cookies: {e}", "ERROR")
                return {"error": "Failed to accept cookies", "details": str(e)}, True
            log_to_file("succesfully accepted cookies", "DEBUG")
            
            
            # Get the name, current price and original price of the product
            await get_page_content()
            return dictValues, delete
            
            
        finally:
            try:
                if browser:
                    log_to_file("Closing browser, check the logs for more information\n", "DEBUG")
                    await browser.close()
                else:
                    log_to_file("Browser was never initialized, skipping close", "WARNING")
                    return {"error": "Browser was never initialized", "details": "Browser was never initialized"}, True     
            except Exception as e:
                log_to_file(f"Error while closing browser: {str(e)}", "ERROR")
                return {"error": "Failed to close browser", "details": str(e)}, True



async def mediamarkt_scraper(URL, delete=False):
    """s
    Scrapes product information from coolblue.nl

    Args:
    playwright (obj): Playwright instance
    URL (str): Full coolblue.nl product URL

    Returns:
        dict: Product details including name, current price and original price and wether to delete the playwright directory(session data)
    """
    
    async with async_playwright() as playwright:
        try:
            args = ["--disable-blink-features=AutomationControlled",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"]
            
            # Create a headless browser instance and give it extra context to imitate a real user
            browser = await playwright.chromium.launch_persistent_context(
                
                # Load residential proxy from .env file
                proxy={"server": os.getenv("PROXY_SERVER"),
                "username": os.getenv("PROXY_USERNAME"),
                "password": os.getenv("PROXY_PASSWORD")},
                slow_mo=100,
                # VPS path
                user_data_dir="/home/nordinschoenmakers/fastAPI/fastAPI/playwright",	
                #Local path
                #user_data_dir="C:\\playwright",	
                headless=True, 
                args=args,
                channel="chrome",
                viewport={"width": 1920, "height": 1080},
                timeout=10000
            )
            
            
            # Create new page
            log_to_file("Creating new page and navigating to URL", "DEBUG")
            try:
                page = await browser.new_page()
            except Exception as e:
                log_to_file(f"Error creating new page: {e}", "ERROR")
                return {"error": "Failed to create new page", "details": str(e)}, True
            
            # Navigate to the URL, log which proxy is being used
            log_to_file(f"Navigating to mediamarkt.nl product page using residential proxy", "DEBUG")
            try:
                await page.goto(URL)
                await asyncio.sleep(random.uniform(0.5, 2))
            except Exception as e:
                log_to_file(f"Error navigating to URL: {e}", "ERROR")
                return {"error": "Failed to navigate to URL", "details": str(e)}, True
            log_to_file("Navigated to URL successfully", "DEBUG")
            
            
            # Create a dictionary to store the product details
            dictValues = {
                "name": "",
                "currentPrice": "",
                "ogPrice": ""
            }
            
            name_selector = "fBtdkS"
            currentprice_selector = "bPkjPs"
            button_selector = "gKJbFU"
            
            async def get_page_content():
                #Wait for the price and name elements to be visible and get its inner HTML/text
                #Data is cleaned up and stored in the dictionary so it can be returned
                log_to_file("Scraping and formatting product data and storing it in dictValues", "DEBUG")
                try:
                    await page.wait_for_selector(f'.{currentprice_selector}', state="visible", timeout=10000)
                    await asyncio.sleep(0.2)
                    
                    # Get the inner text of the name element, format it and store it in the dictionary
                    name_html = await page.inner_html(f'.{name_selector}', timeout=10000)
                    dictValues["name"] = name_html.replace("\n", "").strip().replace("&amp;", "&")
                    
                    # Get the inner HTML of the current price element, format it and store it in the dictionarys
                    currentPrice_html = await page.inner_text('[data-test="branded-price-whole-value"]')
                    currentPrice_decimal_html = await page.inner_text('[data-test="branded-price-decimal-value"]')
                    currentPrice_html = currentPrice_html + currentPrice_decimal_html
                    print(currentPrice_html)
                    dictValues["currentPrice"] = currentPrice_html.replace("\n", ".").replace(",", ".").replace("–", "00").strip()
                    
                    # If the original price is not available, set it to the current price
                    if await page.query_selector('[class="sc-6bbc79bc-0 hjKwWk notranslate"]') == None:
                        log_to_file("ogPrice not found, setting ogPrice to currentPrice")
                        dictValues["ogPrice"] = dictValues["currentPrice"]
                        
                    # Get all elements that use the original prices class due to reuse in the HTML, look through them to find the price element
                    else:
                        element_contents = await page.locator('[class="sc-6bbc79bc-0 hjKwWk notranslate"]').all()
                        for contents in element_contents:
                            content = await contents.inner_text()
                            if "€" in content:
                                ogPrice_html = content.strip()
                                break
                            
                        # Extract price using regex
                        ogPrice_html = re.sub("[^0-9.,€]", "", ogPrice_html).replace(',', '.')
                        prices = ogPrice_html.split("€")
                        dictValues["ogPrice"] = prices[-1]
                    
                    # Check to see product availability
                    try:
                        log_to_file("Checking product availability")
                        availabiliy_check = await page.inner_text('[data-test="mms-cofr-delivery_AVAILABLE"]', timeout=2000)
                        if "online" not in availabiliy_check.lower():
                            raise PlaywrightTimeoutError("Product is not available")

                        log_to_file("Product available and price data found, returning dictValues")
                        
                    # Set price values to 0. Indicating unavailable product
                    except PlaywrightTimeoutError:
                        
                        dictValues["currentPrice"] = 0.0
                        dictValues["ogPrice"] = 0.0   
                        log_to_file("Product is not available, returning data that indicates unavailability")
                        
                    return dictValues
                             
                except Exception as e:
                    log_to_file(f"Error scraping product data/altering product data: {e}", "ERROR")
                    return {"error": "Failed to scrape product data/alter product data", "details": str(e)}
                    


            # Check if the cookies button is visible to determine if cookies need to be accepted
            # If not, scrape the content, check for an error and return the dictionary if no error is found
            
            try:
                await page.wait_for_selector(f'.{button_selector}', timeout=1000)
            except:
                log_to_file("Cookies button not found, continuing to get_page_content")
                result = await get_page_content()
                if not result.get("error"):
                    log_to_file(f"Scraping succesful, result: {result}", "DEBUG")
                    return dictValues, delete
                else:
                    return result, True
            
            
            # Wait for cookies button to be visable and click it
            log_to_file("Accepting cookies", "DEBUG")
            try:
                await page.wait_for_selector(f'.{button_selector}', timeout=10000)
                await asyncio.sleep(random.uniform(0.5, 2))
                await page.click(f'.{button_selector}')
            except Exception as e:
                log_to_file(f"Error accepting cookies: {e}", "ERROR")
                return {"error": "Failed to accept cookies", "details": str(e)}, True
            log_to_file("succesfully accepted cookies", "DEBUG")
            
            
            # Get the name, current price and original price of the product
            await get_page_content()
            return dictValues, delete
            
            
        finally:
            try:
                if browser:
                    log_to_file("Closing browser, check the logs for more information\n", "DEBUG")
                    await browser.close()
                else:
                    log_to_file("Browser was never initialized, skipping close\n", "WARNING")
                    return {"error": "Browser was never initialized", "details": "Browser was never initialized"}, True     
            except Exception as e:
                log_to_file(f"Error while closing browser: {str(e)}", "ERROR")
                return {"error": "Failed to close browser", "details": str(e)}, True
            
            
            
            
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



async def main():
    #return await bol_scraper("https://www.youtube.com/watch?v=Vlb_cujWRI0")
    #return await bol_scraper("https://www.bol.com/nl/nl/p/hoesje-geschikt-voor-samsung-galaxy-s25-ultra-book-case-leer-slimline-zwart/9300000232176510")
    #return await coolblue_scraper("https://www.coolblue.nl/product/962462")
    #return await bol_scraper("https://www.bol.com/nl/nl/p/noppies-flared-legging-foix-meisjes-broek-maat-86/9300000176390734/?bltgh=3c186224-e162-420a-9bb0-9492c54ba5c6.topDealsForYou.product-tile-9300000176390734.ProductImage&promo=main_860_deals_for_you___product_19_9300000176390734&cid=1753535241410-9189794353869")
    return await mediamarkt_scraper("https://www.mediamarkt.nl/nl/product/_ninja-ninja-detect-3-in-1-foodprocessor-blender-en-smoothie-maker-blendsense-technologie-tb401eu-hand-mixer-zwart-146115008.html")

if __name__ == "__main__":
    result, delete = asyncio.run(main())
    print(result)

