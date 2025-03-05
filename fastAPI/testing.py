import requests
import json

url = 'https://www.bol.com/nl/nl/p/samsung-g5-c34g55twwu-qhd-va-curved-ultrawide-165hz-gaming-monitor-34-inch/9300000018877944/?bltgh=qg2b2IasX8yauBMeikBB7Q.2_79.83.ProductImage'

response = requests.get(f"http://157.180.29.91/scrape?url={url}")

print(response.json())