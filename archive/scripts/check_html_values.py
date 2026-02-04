#!/usr/bin/env python
"""Check what's in the actual HTML being served"""
import urllib.request

try:
    response = urllib.request.urlopen('http://127.0.0.1:8000/annual-electricity/')
    html = response.read().decode('utf-8')
    
    # Find the JavaScript variable definitions
    import re
    
    # Search for the const declarations
    bio_match = re.search(r'const bio = ([^;]+);', html)
    pv_match = re.search(r'const pv = ([^;]+);', html)
    wind_match = re.search(r'const wind = ([^;]+);', html)
    m_total_match = re.search(r'const m_total = ([^;]+);', html)
    
    print("Values found in rendered HTML:")
    print("=" * 70)
    print(f"bio = {bio_match.group(1) if bio_match else 'NOT FOUND'}")
    print(f"pv = {pv_match.group(1) if pv_match else 'NOT FOUND'}")
    print(f"wind = {wind_match.group(1) if wind_match else 'NOT FOUND'}")
    print(f"m_total = {m_total_match.group(1) if m_total_match else 'NOT FOUND'}")
    
    if bio_match and float(bio_match.group(1)) > 0:
        print("\n✅ VALUES ARE IN THE HTML!")
        print("The problem is in the JavaScript or browser rendering.")
        print("\nTroubleshooting:")
        print("1. Open browser DevTools (F12 or Cmd+Option+I)")
        print("2. Go to Console tab")
        print("3. Look for any JavaScript errors")
        print("4. Check if you see '=== WS DIAGRAM VALUES ===' console output")
    else:
        print("\n❌ VALUES ARE ZERO OR MISSING IN HTML!")
        print("The problem is in Django template rendering.")
        
except Exception as e:
    print(f"Error: {e}")
    print("Make sure the server is running at http://127.0.0.1:8000")
