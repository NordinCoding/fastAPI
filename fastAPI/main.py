from typing import Union
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
# Change to from mainPlay once youve updated mainPlay.py
from mainPlay import bol_scraper, coolblue_scraper, mediamarkt_scraper, log_to_file
from urllib.parse import unquote, quote
import shutil
import os

app = FastAPI()

@app.get("/")
async def read_root():
    return {'Correct usage: "http://136.144.172.186/scrape?url=[URL]"'}


@app.get("/scrape")
async def scrape_item(url: str = Query(..., description="URL of the product to scrape")):

    log_to_file(f"Scraping item from URL: {url}", "INFO")

    #VPS path
    #playwright_dir = "/home/nordinschoenmakers/fastAPI/fastAPI/playwright"

    #Local path
    playwright_dir = "C:\\playwright"
    
    supported_sites = {"www.bol.com/": bol_scraper,
                        "mediamarkt.de/": mediamarkt_scraper,
                        "mediamarkt.at/": mediamarkt_scraper,
                        "mediamarkt.be/": mediamarkt_scraper,
                        "mediamarkt.hu/": mediamarkt_scraper,
                        "mediamarkt.it/": mediamarkt_scraper,
                        "mediamarkt.nl/": mediamarkt_scraper,
                        "mediamarkt.pl/": mediamarkt_scraper,
                        "mediamarkt.pt/": mediamarkt_scraper,
                        "mediamarkt.es/": mediamarkt_scraper,
                        "mediamarkt.ch/": mediamarkt_scraper,
                        "mediamarkt.com.tr/": mediamarkt_scraper}
    
    try:
        for url_check in supported_sites:
            if url_check in url:
                result, delete = await supported_sites[url_check](url)

        if delete:
            if os.path.exists(playwright_dir):
                # Removes the session folder if delete is True, check mainPlay.py for full function
                try:
                    shutil.rmtree(playwright_dir)
                    log_to_file("Deleted session folder", "DEBUG")
                except Exception as e:
                    log_to_file(f"Failed to delete session folder: {str(e)}", "ERROR")

        return result

    except Exception as e:
        log_to_file(f"Failed to scrape item: {str(e)}", "ERROR")
        return {"error": "Failed to scrape item", "details": str(e)}

        