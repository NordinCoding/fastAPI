from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from mainPlay import bol_scraper, log_to_file

app = FastAPI()


@app.get("/")
async def read_root():
    return {"Hello, World!"}


@app.get("/items/{URL}")
def scrape_item(URL: str):
    dictValues = bol_scraper(URL)
    return dictValues
