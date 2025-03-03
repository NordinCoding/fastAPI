from typing import Union
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from mainPlay import bol_scraper, log_to_file
from urllib.parse import unquote

app = FastAPI()


@app.get("/")
async def read_root():
    return {'Correct usage: "http://157.180.29.91/URL"'}


@app.get("/scrape")
def scrape_item(url: str = Query(..., description="URL of the product to scrape")):
    try:
        dictValues = bol_scraper(url)
        return dictValues
    except Exception as e:
        log_to_file(f"Failed to scrape item: {str(e)}", "ERROR")
        return {"error": "Failed to scrape item", "details": str(e)}
        
