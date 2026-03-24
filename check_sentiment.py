import requests
r = requests.get('https://api.alternative.me/fng/')
print('Fear & Greed:', r.json()['data'][0]['value'], '/ 100')
