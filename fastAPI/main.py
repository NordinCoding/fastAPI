from typing import Union
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
# Change to from mainPlay once youve updated mainPlay.py
from testing import bol_scraper, log_to_file
from urllib.parse import unquote, quote
import shutil

app = FastAPI()

#test

@app.get("/")
async def read_root():
    return {'Correct usage: "http://136.144.172.186/scrape?url=[URL]"'}


@app.get("/scrape")
async def scrape_item(url: str = Query(..., description="URL of the product to scrape")):
    try:
        result, delete = await bol_scraper(url)
        if delete:
            # Removes the session folder if delete is True, check mainPlay.py for full function
            shutil.rmtree("C:\\playwright")
        return result
    except Exception as e:
        log_to_file(f"Failed to scrape item: {str(e)}", "ERROR")
        return {"error": "Failed to scrape item", "details": str(e)}
        
