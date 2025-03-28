from patchright.async_api import async_playwright
from bs4 import BeautifulSoup
import time
import datetime
import random
from dotenv import load_dotenv
import os
import asyncio
import shutil


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
        dict: Product details including name, current price and original price
    """
    
    async with async_playwright() as playwright:
        try:
            args = ["--disable-blink-features=AutomationControlled"
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
                #user_data_dir= "C://playwright",
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
                except Exception as e:
                    log_to_file(f"Error scraping product data/altering product data: {e}", "ERROR")
                    return {"error": "Failed to scrape product data/alter product data", "details": str(e)}


            # Check if the cookies button is visible to determine if cookies and language need to be accepted
            # If not, scrape the content, check for an error and return the dictionary if no error is found
            if await page.query_selector('[class="ui-btn ui-btn--primary ui-btn--block@screen-small"]') == None:
                found_error = await get_page_content()
                if found_error == None:
                    log_to_file("Scraping succesful", "DEBUG")
                    return dictValues, delete
                else:
                    return found_error, True
            
            
            # Wait for cookies button to be visable and click it
            log_to_file("Accepting cookies", "DEBUG")
            try:
                await page.wait_for_selector('[class="ui-btn ui-btn--primary ui-btn--block@screen-small"]', timeout=10000)
                time.sleep(random.uniform(0.5, 2))
                await page.click('[class="ui-btn ui-btn--primary ui-btn--block@screen-small"]')
            except Exception as e:
                log_to_file(f"Error accepting cookies: {e}", "ERROR")
                return {"error": "Failed to accept cookies", "details": str(e)}, True
            log_to_file("succesfully ccepted cookies", "DEBUG")
            
            
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

async def main():
    #return await bol_scraper("https://www.youtube.com/watch?v=Vlb_cujWRI0")
    return await bol_scraper("https://www.bol.com/nl/nl/p/power-8-freshstep-ozon-schoenendroger-schoenverfrisser-met-timer-uv-verlichtin-huidskooldeeltjes-geurvreters-voor-schoenen/9300000222709447/?bltgh=fa4181f4-d88b-4b77-abfe-8f00f0904d19.topDealsForYou.product-tile-9300000222709447.ProductImage&promo=main_860_deals_for_you___product_0_9300000222709447")
    

if __name__ == "__main__":
    result, delete = asyncio.run(main())
    print(result)