import requests

# Test with exact location names from database
test_cases = [
    ("Tirupati Bus Station", "Tirumala Bus Station"),
    ("Tirumala Bus Station", "Tirupati Bus Station"),
    ("Tirupati Railway Station", "Tirumala Bus Station"),
    ("Alipiri", "Tirumala Bus Station"),
]

for from_loc, to_loc in test_cases:
    response = requests.get(f'http://127.0.0.1:8001/api/transport/search?from_location={from_loc}&to_location={to_loc}')
    data = response.json()
    print(f"{from_loc} -> {to_loc}: {data['count']} routes")
    if data['routes']:
        for r in data['routes'][:2]:
            route_name = r['route_name'].encode('ascii', 'ignore').decode('ascii')
            print(f"  - {route_name} ({r['vehicle_type']})")
    print()
