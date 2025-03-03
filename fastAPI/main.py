from typing import Union
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mainPlay import bol_scraper, log_to_file
from urllib.parse import unquote

app = FastAPI()


@app.get("/")
async def read_root():
    return {'Correct usage: "http://157.180.29.91/URL"'}


@app.get("/scrape/<path:mypath>")
def scrape_item(mypath):
    try:
        URL = mypath
        dictValues = bol_scraper(URL)
        return dictValues
    except Exception as e:
        log_to_file(f"Failed to scrape item: {str(e)}", "ERROR")
        raise HTTPException(status_code=500, detail="Failed to scrape item")
