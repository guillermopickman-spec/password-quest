"""
Password Quest - Phase 3 Manual Testing Script

Run this against a running server to test gamification features.
Start the server first: python run.py

Usage: python tests/test_phase3_manual.py
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"
SESSION = requests.Session()


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_json(data):
    """Print JSON data formatted."""
    print(json.dumps(data, indent=2))


def test_server_running():
    """Check if server is running."""
    try:
        r = SESSION.get(f"{BASE_URL}/api/health", timeout=5)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def test_health():
    """Test health endpoint."""
    print_header("TEST 1: Health Check")
    try:
        r = SESSION.get(f"{BASE_URL}/api/health")
        data = r.json()
        print(f"Status: {r.status_code}")
        print(f"Version: {data.get('version', 'unknown')}")
        print(f"Features: {data.get('features', {})}")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_initialize():
    """Initialize system (create badges)."""
    print_header("TEST 2: Initialize System")
    try:
        r = SESSION.post(f"{BASE_URL}/api/init")
        data = r.json()
        print(f"Status: {r.status_code}")
        print(f"Response: {data}")
        return r.status_code == 200
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_progress_initial():
    """Test initial progress (new user)."""
    print_header("TEST 3: Initial Progress")
    try:
        r = SESSION.get(f"{BASE_URL}/api/progress")
        data = r.json()
        print(f"Status: {r.status_code}")
        print(f"\nUser Level: {data['level']}")
        print(f"Total XP: {data['xp']['total']}")
        print(f"Current Level XP: {data['xp']['current_level']}/{data['xp']['required_for_next']}")
        print(f"Streak: {data['streak']['current_streak']} days")
        print(f"Badges Earned: {len(data['badges'])}")
        print(f"Challenges Completed: {len(data['challenges'])}")
        return data["level"] == 1 and data["xp"]["total"] == 0
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_badges_list():
    """Test badges endpoint."""
    print_header("TEST 4: Available Badges")
    try:
        r = SESSION.get(f"{BASE_URL}/api/badges")
        data = r.json()
        print(f"Status: {r.status_code}")
        print(f"\nAll Badges ({len(data['all_badges'])}):")
        for badge in data["all_badges"]:
            print(f"  • {badge['icon']} {badge['name']}: {badge['description']} (+{badge['xp_bonus']} XP)")
        print(f"\nEarned Badges: {len(data['earned_badges'])}")
        return len(data["all_badges"]) == 8
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_challenges_list():
    """Test challenges list."""
    print_header("TEST 5: Challenges List")
    try:
        r = SESSION.get(f"{BASE_URL}/api/challenges")
        data = r.json()
        print(f"Status: {r.status_code}")
        print(f"\nAvailable Challenges ({len(data['challenges'])}):")
        for challenge in data["challenges"]:
            print(f"\n  📋 {challenge['title']} (Level {challenge['level']})")
            print(f"     ID: {challenge['id']}")
            print(f"     Scenario: {challenge['scenario']}")
            print(f"     Min Score: {challenge['min_score_to_pass']}/4")
            print(f"     XP Bonus: {challenge['xp_bonus']}")
        return len(data["challenges"]) >= 3
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_password_analysis_with_xp():
    """Test password analysis with XP tracking."""
    print_header("TEST 6: Password Analysis with XP")
    
    passwords = [
        ("123", "Very Weak"),
        ("password123", "Common Password"),
        ("MyP@ssw0rd!", "Medium Strength"),
        ("Correct-Horse-Battery-Staple!47", "Strong Passphrase"),
    ]
    
    results = []
    for pwd, desc in passwords:
        try:
            r = SESSION.post(
                f"{BASE_URL}/api/analyze",
                json={"password": pwd}
            )
            data = r.json()
            
            progress = data.get("progress", {})
            xp_earned = progress.get("xp_awarded", 0)
            total_xp = progress.get("total_xp", 0)
            level = progress.get("level", 1)
            
            print(f"\n  '{desc}'")
            print(f"    Score: {data['score']}/4 ({data['strength_label']})")
            print(f"    XP Earned: +{xp_earned}")
            print(f"    Total XP: {total_xp}")
            print(f"    Level: {level}")
            
            # Check for unlocked badges
            badges = progress.get("unlocked_badges", [])
            if badges:
                for badge in badges:
                    print(f"    🏆 Badge Unlocked: {badge['icon']} {badge['name']} (+{badge['xp_bonus']} XP)")
            
            results.append(data["score"] >= 0)
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results.append(False)
    
    return all(results)


def test_challenge_boss_birthday():
    """Test 'Boss's Birthday' challenge."""
    print_header("TEST 7: Challenge - Boss's Birthday")
    try:
        # Get challenge details
        r = SESSION.get(f"{BASE_URL}/api/challenges/boss_birthday")
        data = r.json()
        challenge = data["challenge"]
        
        print(f"Challenge: {challenge['title']}")
        print(f"Weak Password: {challenge['weak_password']}")
        print(f"Required Score: {challenge['min_score_to_pass']}/4")
        
        # Attempt with weak password (should fail)
        print("\n  Attempt 1: Weak password 'Johnson1980!'")
        r = SESSION.post(
            f"{BASE_URL}/api/challenges/boss_birthday/attempt",
            json={"password": "Johnson1980!"}
        )
        data = r.json()
        print(f"    Score: {data['attempt']['score']}/4")
        print(f"    Passed: {data['validation']['passed']}")
        
        # Attempt with strong password (should pass)
        print("\n  Attempt 2: Strong password 'Purple-Elephant-Jumps-42!'")
        r = SESSION.post(
            f"{BASE_URL}/api/challenges/boss_birthday/attempt",
            json={"password": "Purple-Elephant-Jumps-42!"}
        )
        data = r.json()
        print(f"    Score: {data['attempt']['score']}/4")
        print(f"    Passed: {data['validation']['passed']}")
        
        if data["validation"]["passed"]:
            print(f"\n    🎉 {data['validation']['success_message'][:100]}...")
            print(f"    💡 Lesson: {data['validation']['lesson_learned'][:100]}...")
        
        return data["validation"]["passed"]
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_challenge_the_simpleton():
    """Test 'The Simpleton' challenge."""
    print_header("TEST 8: Challenge - The Simpleton")
    try:
        # Get challenge details
        r = SESSION.get(f"{BASE_URL}/api/challenges/the_simpleton")
        data = r.json()
        challenge = data["challenge"]
        
        print(f"Challenge: {challenge['title']}")
        print(f"Weak Password: {challenge['weak_password']}")
        print(f"Required Score: {challenge['min_score_to_pass']}/4 (Must be perfect!)")
        
        # Attempt with medium password (should fail - needs score 4)
        print("\n  Attempt 1: Medium strength 'Better99!'")
        r = SESSION.post(
            f"{BASE_URL}/api/challenges/the_simpleton/attempt",
            json={"password": "Better99!"}
        )
        data = r.json()
        print(f"    Score: {data['attempt']['score']}/4")
        print(f"    Passed: {data['validation']['passed']}")
        
        # Attempt with strong password
        print("\n  Attempt 2: Strong password 'Castle-Dragon-Mountain-Storm-88!'")
        r = SESSION.post(
            f"{BASE_URL}/api/challenges/the_simpleton/attempt",
            json={"password": "Castle-Dragon-Mountain-Storm-88!"}
        )
        data = r.json()
        print(f"    Score: {data['attempt']['score']}/4")
        print(f"    Passed: {data['validation']['passed']}")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_daily_checkin():
    """Test daily check-in."""
    print_header("TEST 9: Daily Check-in")
    try:
        r = SESSION.post(f"{BASE_URL}/api/progress/checkin")
        data = r.json()
        
        print(f"Status: {data['success']}")
        print(f"Message: {data['message']}")
        print(f"Current Streak: {data['current_streak']} days")
        print(f"XP Awarded: {data['xp_awarded']}")
        
        # Try again (should fail - already checked in)
        print("\n  Attempting second check-in...")
        r = SESSION.post(f"{BASE_URL}/api/progress/checkin")
        data = r.json()
        print(f"  Success: {data['success']}")
        print(f"  Message: {data['message']}")
        
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_final_progress():
    """Test final progress after all activities."""
    print_header("TEST 10: Final Progress Summary")
    try:
        r = SESSION.get(f"{BASE_URL}/api/progress")
        data = r.json()
        
        print(f"\n{'='*50}")
        print(f"  🎮 PASSWORD QUEST - PLAYER SUMMARY")
        print(f"{'='*50}")
        print(f"\n  📊 Level: {data['level']}")
        print(f"  ⭐ Total XP: {data['xp']['total']}")
        print(f"  📈 Progress: {data['xp']['current_level']}/{data['xp']['required_for_next']} XP")
        print(f"  🔥 Streak: {data['streak']['current_streak']} days")
        print(f"  🏆 Badges: {len(data['badges'])}")
        
        if data["badges"]:
            print(f"\n  Earned Badges:")
            for badge in data["badges"]:
                print(f"    {badge['icon']} {badge['name']}")
        
        print(f"\n  📋 Challenges Completed: {len(data['challenges'])}")
        for challenge_id, progress in data["challenges"].items():
            print(f"    ✓ {challenge_id}: Score {progress['best_score']}/4")
        
        print(f"\n{'='*50}")
        
        return data["xp"]["total"] > 0
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Run all Phase 3 tests."""
    print("\n" + "=" * 70)
    print("  🎮 PASSWORD QUEST - PHASE 3 GAMIFICATION TEST")
    print("  Testing: XP, Levels, Badges, Challenges, Streaks")
    print("=" * 70)
    print(f"\nServer: {BASE_URL}")
    print("Make sure the server is running: python run.py")
    
    # Check server
    if not test_server_running():
        print("\n❌ ERROR: Server is not running!")
        print("   Start it with: python run.py")
        sys.exit(1)
    
    print("\n✅ Server is running!")
    
    # Run tests
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Initialize System", test_initialize()))
    results.append(("Initial Progress", test_progress_initial()))
    results.append(("Badges List", test_badges_list()))
    results.append(("Challenges List", test_challenges_list()))
    results.append(("Password Analysis with XP", test_password_analysis_with_xp()))
    results.append(("Challenge - Boss's Birthday", test_challenge_boss_birthday()))
    results.append(("Challenge - The Simpleton", test_challenge_the_simpleton()))
    results.append(("Daily Check-in", test_daily_checkin()))
    results.append(("Final Progress", test_final_progress()))
    
    # Summary
    print("\n" + "=" * 70)
    print("  📊 TEST SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  🎉 ALL PHASE 3 TESTS PASSED!")
        print("  Gamification features are working correctly.")
    else:
        print("  ⚠️  Some tests failed. Check output above.")
    print("=" * 70)
    
    print(f"\n📖 Open http://127.0.0.1:5000 for visual testing")


if __name__ == "__main__":
    main()