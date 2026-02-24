import requests
import json

# Test login
login_response = requests.post('http://127.0.0.1:8000/api/login', json={
    'username': 'admin',
    'password': 'admin2026'
})

print("LOGIN RESPONSE:", login_response.status_code)
print(login_response.text)

if login_response.status_code == 200:
    token = login_response.json()['access_token']
    
    # Test team endpoint
    headers = {'Authorization': f'Bearer {token}'}
    team_response = requests.get('http://127.0.0.1:8000/api/team', headers=headers)
    
    print("\nTEAM RESPONSE:", team_response.status_code)
    print("TEAM DATA:")
    print(json.dumps(team_response.json(), ensure_ascii=False, indent=2))
