import requests

response = requests.get('http://127.0.0.1:8001/api/transport/routes')
data = response.json()
print('Total routes:', data['count'])
for r in data['routes']:
    print(f"{r['source_location']} -> {r['destination_location']}")
