import json
import urllib.request
import urllib.error

# Test login
login_data = json.dumps({'username': 'admin', 'password': 'admin2026'}).encode()
try:
    req = urllib.request.Request('http://127.0.0.1:8000/api/login', data=login_data, 
                                  headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read())
        print("LOGIN OK:", data)
        token = data['access_token']
        
        # Test team endpoint
        req2 = urllib.request.Request('http://127.0.0.1:8000/api/team',
                                     headers={'Authorization': f'Bearer {token}'})
        with urllib.request.urlopen(req2) as response2:
            team_data = json.loads(response2.read())
            print("\nTEAM DATA:", json.dumps(team_data, ensure_ascii=False, indent=2))
except urllib.error.URLError as e:
    print(f"ERROR: {e}")
