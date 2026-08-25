import requests
import json

response = requests.get('http://localhost:8000/api/queue')
print('Status:', response.status_code)
data = response.json()
pred = data['ai_prediction']

print('Admin data used:', pred['admin_data_used'])
print('Admin crowd data:', pred['admin_crowd_data'])
print('Current level:', pred['current_crowd_level'])
print('Wait time:', pred['predicted_wait_minutes'])
print('AI advice:', pred['ai_advice'])
print('SUCCESS: Queue API now has admin data!')
