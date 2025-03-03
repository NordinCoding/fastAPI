from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from mainPlay import bol_scraper, log_to_file

app = FastAPI()


@app.get("/")
async def read_root():
    return {'Correct usage: "http://157.180.29.91/URL"'}


@app.get("/{URL}")
def scrape_item(URL: str):
    dictValues = bol_scraper(URL)
    return dictValues
