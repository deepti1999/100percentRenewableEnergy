"""
Test the Final Balance button with new FormulaVariable system
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'landuse_project.settings')
django.setup()

import json
from django.test import Client
from django.contrib.auth.models import User

print("="*80)
print("TESTING FINAL BALANCE BUTTON")
print("="*80)

# Create test client
client = Client()

# Get or create test user
user, created = User.objects.get_or_create(username='testuser')
if created:
    user.set_password('testpass')
    user.save()

# Login
client.login(username='testuser', password='testpass')

print("\n🧪 Sending POST request to /api/final-balance/...\n")

try:
    response = client.post(
        '/api/final-balance/',
        data=json.dumps({
            "driver": "solar",
            "tolerance": 1.0,
            "ws_tolerance": 10.0,
            "max_cycles": 1
        }),
        content_type='application/json'
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"\nResponse Content:\n{json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 500:
        print("\n❌ ERROR DETECTED!")
        resp_data = response.json()
        if 'message' in resp_data:
            print(f"\nError Message: {resp_data['message']}")
        if 'traceback' in resp_data:
            print(f"\nTraceback:\n{resp_data['traceback']}")
    else:
        print("\n✅ Request completed successfully")
        
except Exception as e:
    print(f"\n❌ Exception: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
