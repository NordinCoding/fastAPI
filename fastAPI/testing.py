import requests
import json

url = 'https://www.bol.com/nl/nl/p/rustin-schoenendroger-pro-schoenverfrisser-met-timer-ozone-droogfunctie-geurvreter-verstelbaar/9300000223639085/?bltgh=0bda880b-5ae1-40d8-9d0d-bdead1785228.topDealsForYou.product-tile-9300000223639085.ProductImage&promo=main_860_deals_for_you___product_1_9300000223639085'

response = requests.get(f"http://136.144.172.186/scrape?url={url}")

print(response.json())