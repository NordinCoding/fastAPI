import requests
import json

url = 'http://157.180.29.91'

response = requests.get(url)

print(response.json())