"""
Password Quest - Manual Testing Script

Run this to test Phase 1 functionality without a browser.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_health():
    """Test the health endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    try:
        r = requests.get(f"{BASE_URL}/api/health")
        print(f"Status: {r.status_code}")
        print(f"Response: {json.dumps(r.json(), indent=2)}")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("   Is the server running? (python run.py)")
        return False

def test_weak_password():
    """Test a weak password."""
    print("\n" + "="*60)
    print("TEST 2: Weak Password (password123)")
    print("="*60)
    try:
        r = requests.post(f"{BASE_URL}/api/analyze", json={"password": "password123"})
        data = r.json()
        print(f"Status: {r.status_code}")
        print(f"Score: {data['score']}/4 ({data['strength_label']})")
        print(f"Breach Count: {data['breach_count']:,}")
        print(f"Crack Time: {data['crack_time_display']}")
        print(f"Is Breached: {data['is_breached']}")
        print(f"Feedback: {data['feedback'][:2]}...")  # First 2 tips
        return data['score'] < 2 and data['is_breached']
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_strong_password():
    """Test a strong password."""
    print("\n" + "="*60)
    print("TEST 3: Strong Password")
    print("="*60)
    try:
        r = requests.post(f"{BASE_URL}/api/analyze", 
                         json={"password": "Correct-Horse-Battery-Staple!47"})
        data = r.json()
        print(f"Status: {r.status_code}")
        print(f"Score: {data['score']}/4 ({data['strength_label']})")
        print(f"Entropy: {data['entropy']} bits")
        print(f"Crack Time: {data['crack_time_display']}")
        print(f"Is Strong: {data['is_strong']}")
        print(f"Is Breached: {data['is_breached']}")
        return data['score'] >= 3 and data['is_strong']
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_pages():
    """Test web pages load."""
    print("\n" + "="*60)
    print("TEST 4: Web Pages")
    print("="*60)
    pages = ["/", "/challenges", "/leaderboard"]
    all_ok = True
    for page in pages:
        try:
            r = requests.get(f"{BASE_URL}{page}")
            status = "✅" if r.status_code == 200 else "❌"
            print(f"{status} {page}: {r.status_code}")
            if r.status_code != 200:
                all_ok = False
        except Exception as e:
            print(f"❌ {page}: ERROR - {e}")
            all_ok = False
    return all_ok

def main():
    print("\n" + "="*60)
    print("🎮 PASSWORD QUEST - PHASE 1 MANUAL TEST")
    print("="*60)
    print(f"\nTesting server at: {BASE_URL}")
    print("Make sure the server is running: python run.py")
    
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Weak Password", test_weak_password()))
    results.append(("Strong Password", test_strong_password()))
    results.append(("Web Pages", test_pages()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + "="*60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Phase 1 is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    print("="*60)
    
    print("\n📖 For visual testing, open: http://127.0.0.1:5000")

if __name__ == "__main__":
    main()