import requests
from random import randrange

location = "http://localhost:5000/sensor"
pm25 = randrange(10)
co2 = randrange(10)
data = {'password': 'fuck', 'pm25': pm25, 'co2': co2}
r = requests.post(location, data)
print(r.status_code, r.reason)
