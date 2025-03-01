from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Product(BaseModel):
    URL: str
    name: str
    ogPrice: float
    currentPrice: float



@app.get("/")
async def read_root():
    return {"Hello, World!"}


@app.get("/items/{product_id}")
async def read_item(product_id: int, q: Union[str, None] = None):
    return {"item_id": product_id, "q": q}


@app.put("/items/{item_id}")
async def update_item(item_id: int, product: Product):
    return {"product_name": product.name, "ogPrice": product.ogPrice, "currentPrice": product.currentPrice}
