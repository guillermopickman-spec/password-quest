"""
Password Quest - Phase 3 Gamification Tests

Comprehensive tests for:
- User Progress System (XP, Levels)
- Badge System
- Daily Streaks
- Scenario Challenges

Run with: python -m pytest tests/test_phase3_gamification.py -v
"""

import json
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from app.models import db, User, XPTransaction, Badge, UserBadge, DailyStreak, ChallengeCompletion
from app.progress_service import initialize_badges, calculate_xp_for_analysis


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(config_name="testing")
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    
    with app.app_context():
        db.create_all()
        initialize_badges()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def init_user(client):
    """Initialize a user session and return headers."""
    # First request creates session
    response = client.get("/")
    assert response.status_code == 200
    
    # Initialize system
    response = client.post("/api/init")
    assert response.status_code == 200
    
    return {}


# =============================================================================
# Progress API Tests
# =============================================================================

class TestProgressAPI:
    """Tests for /api/progress endpoint."""
    
    def test_progress_returns_user_data(self, client, init_user):
        """Progress endpoint should return user level, XP, and badges."""
        response = client.get("/api/progress")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Check required fields
        assert "session_id" in data
        assert "level" in data
        assert "xp" in data
        assert "streak" in data
        assert "badges" in data
        assert "challenges" in data
    
    def test_progress_xp_structure(self, client, init_user):
        """XP data should have proper structure."""
        response = client.get("/api/progress")
        data = json.loads(response.data)
        
        xp = data["xp"]
        assert "total" in xp
        assert "current_level" in xp
        assert "required_for_next" in xp
        assert "next_level_threshold" in xp
        
        # New user should start at 0 XP
        assert xp["total"] == 0
        assert xp["current_level"] == 0
    
    def test_progress_streak_structure(self, client, init_user):
        """Streak data should have proper structure."""
        response = client.get("/api/progress")
        data = json.loads(response.data)
        
        streak = data["streak"]
        assert "current_streak" in streak
        assert "max_streak" in streak
        assert "can_checkin" in streak
        assert "streak_at_risk" in streak
        
        # New user starts with no streak
        assert streak["current_streak"] == 0
    
    def test_progress_returns_level_1_for_new_user(self, client, init_user):
        """New users should be level 1."""
        response = client.get("/api/progress")
        data = json.loads(response.data)
        
        assert data["level"] == 1


# =============================================================================
# XP and Level System Tests
# =============================================================================

class TestXPSystem:
    """Tests for XP calculation and level progression."""
    
    def test_xp_awarded_on_password_analysis(self, client, init_user):
        """XP should be awarded when analyzing passwords."""
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "StrongP@ssw0rd123!"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        assert "progress" in data
        assert data["progress"] is not None
        assert data["progress"]["xp_awarded"] > 0
    
    def test_xp_based_on_score(self, client, init_user):
        """Higher scores should award more XP."""
        # Weak password
        weak = client.post(
            "/api/analyze",
            data=json.dumps({"password": "123"}),
            content_type="application/json"
        )
        weak_data = json.loads(weak.data)
        weak_xp = weak_data["progress"]["xp_awarded"]
        
        # Strong password
        strong = client.post(
            "/api/analyze",
            data=json.dumps({"password": "Correct-Horse-Battery-Staple!47"}),
            content_type="application/json"
        )
        strong_data = json.loads(strong.data)
        strong_xp = strong_data["progress"]["xp_awarded"]
        
        # Strong password should award more XP
        assert strong_xp > weak_xp
    
    def test_breach_free_bonus_xp(self, client, init_user):
        """Safe passwords with good scores get bonus XP."""
        # Strong password (score >= 3 and not breached)
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "Unique-Strength-99!Test"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        assert data["progress"]["xp_awarded"] >= 75  # Base 50 + 25 bonus
    
    def test_level_progression_tracked(self, client, init_user):
        """Level progress should be tracked."""
        # Analyze a password
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "Test123!"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        progress = data["progress"]
        assert "level_progress" in progress
        assert "current" in progress["level_progress"]
        assert "required" in progress["level_progress"]
    
    def test_xp_calculation_function(self):
        """Test XP calculation logic directly."""
        # Score 0: 10 XP
        assert calculate_xp_for_analysis(0, False) == 10
        
        # Score 1: 15 XP
        assert calculate_xp_for_analysis(1, False) == 15
        
        # Score 2: 25 XP
        assert calculate_xp_for_analysis(2, False) == 25
        
        # Score 3: 50 + 25 bonus = 75 XP
        assert calculate_xp_for_analysis(3, False) == 75
        
        # Score 4: 100 + 25 bonus = 125 XP
        assert calculate_xp_for_analysis(4, False) == 125
        
        # Breached password (no bonus)
        assert calculate_xp_for_analysis(3, True) == 50


# =============================================================================
# Badge System Tests
# =============================================================================

class TestBadgeSystem:
    """Tests for badge awarding."""
    
    def test_badges_endpoint_returns_all_and_earned(self, client, init_user):
        """Badges endpoint should return all badges and user's earned badges."""
        response = client.get("/api/badges")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "all_badges" in data
        assert "earned_badges" in data
        
        # Should have 8 default badges
        assert len(data["all_badges"]) == 8
    
    def test_first_steps_badge_unlocked(self, client, init_user):
        """First Steps badge unlocks on first password analysis."""
        # Analyze first password
        client.post(
            "/api/analyze",
            data=json.dumps({"password": "test"}),
            content_type="application/json"
        )
        
        # Check badges
        response = client.get("/api/badges")
        data = json.loads(response.data)
        
        earned_names = [b["name"] for b in data["earned_badges"]]
        assert "first_steps" in earned_names
    
    def test_master_of_mystery_badge_unlocked(self, client, init_user):
        """Master of Mystery badge unlocks on score 4."""
        # Analyze password until we get score 4
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "Perfect-Score-Test-99!"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        if data["score"] == 4:
            assert "progress" in data
            badge_names = [b["name"] for b in data["progress"].get("unlocked_badges", [])]
            assert "master_of_mystery" in badge_names
    
    def test_badge_awards_bonus_xp(self, client, init_user):
        """Earning a badge should award bonus XP."""
        # First analysis triggers First Steps badge (50 XP)
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "test"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        # Should have base XP + badge bonus
        assert data["progress"]["total_xp"] >= 60  # 10 base + 50 bonus


# =============================================================================
# Challenge System Tests
# =============================================================================

class TestChallengeSystem:
    """Tests for scenario challenges."""
    
    def test_challenges_list_endpoint(self, client, init_user):
        """Challenges endpoint should return all challenges."""
        response = client.get("/api/challenges")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "challenges" in data
        assert len(data["challenges"]) >= 3
    
    def test_challenge_detail_endpoint(self, client, init_user):
        """Challenge detail endpoint should return specific challenge."""
        response = client.get("/api/challenges/boss_birthday")
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert "challenge" in data
        assert "progress" in data
        
        challenge = data["challenge"]
        assert challenge["id"] == "boss_birthday"
        assert "title" in challenge
        assert "scenario" in challenge
        assert "weak_password" in challenge
        assert "min_score_to_pass" in challenge
        assert "hints" in challenge
    
    def test_challenge_attempt_passes_with_strong_password(self, client, init_user):
        """Challenge should pass with a strong password."""
        response = client.post(
            "/api/challenges/boss_birthday/attempt",
            data=json.dumps({"password": "Correct-Horse-Battery-Staple!47"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        assert "attempt" in data
        assert "validation" in data
        assert "progress" in data
        
        validation = data["validation"]
        assert validation["valid"] is True
        assert validation["passed"] is True
    
    def test_challenge_attempt_fails_with_weak_password(self, client, init_user):
        """Challenge should fail with a weak password."""
        response = client.post(
            "/api/challenges/boss_birthday/attempt",
            data=json.dumps({"password": "weak"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        validation = data["validation"]
        assert validation["valid"] is True
        assert validation["passed"] is False
        assert "feedback" in validation
    
    def test_challenge_completion_records_progress(self, client, init_user):
        """Completing challenge should record progress."""
        # Complete challenge
        client.post(
            "/api/challenges/boss_birthday/attempt",
            data=json.dumps({"password": "Correct-Horse-Battery-Staple!47"}),
            content_type="application/json"
        )
        
        # Check progress
        response = client.get("/api/progress")
        data = json.loads(response.data)
        
        # Should have challenge completion recorded
        assert "boss_birthday" in data["challenges"]
    
    def test_challenge_completion_awards_xp(self, client, init_user):
        """Completing challenge should award bonus XP."""
        response = client.post(
            "/api/challenges/boss_birthday/attempt",
            data=json.dumps({"password": "Correct-Horse-Battery-Staple!47"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        # Should have completion with XP
        assert "completion" in data
        assert data["completion"] is not None


# =============================================================================
# Daily Streak Tests
# =============================================================================

class TestDailyStreak:
    """Tests for daily streak system."""
    
    def test_checkin_endpoint_exists(self, client, init_user):
        """Check-in endpoint should be accessible."""
        response = client.post("/api/progress/checkin")
        assert response.status_code == 200
    
    def test_first_checkin_creates_streak(self, client, init_user):
        """First check-in should start streak at 1."""
        response = client.post("/api/progress/checkin")
        data = json.loads(response.data)
        
        assert data["success"] is True
        assert data["current_streak"] == 1
        assert data["xp_awarded"] > 0
    
    def test_duplicate_checkin_same_day_fails(self, client, init_user):
        """Checking in twice same day should fail."""
        # First check-in
        client.post("/api/progress/checkin")
        
        # Second check-in should fail
        response = client.post("/api/progress/checkin")
        data = json.loads(response.data)
        
        assert data["success"] is False
        assert "Already checked in" in data["message"]
    
    def test_streak_reflected_in_progress(self, client, init_user):
        """Streak should appear in progress endpoint."""
        # Check in
        client.post("/api/progress/checkin")
        
        # Get progress
        response = client.get("/api/progress")
        data = json.loads(response.data)
        
        assert data["streak"]["current_streak"] == 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestGamificationIntegration:
    """Integration tests for full gamification flow."""
    
    def test_full_user_journey(self, client, init_user):
        """Test a complete user journey through multiple features."""
        # 1. Check initial progress
        response = client.get("/api/progress")
        data = json.loads(response.data)
        initial_xp = data["xp"]["total"]
        assert data["level"] == 1
        
        # 2. Analyze first password (triggers First Steps badge)
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "MyFirstTest!"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        assert data["progress"]["xp_awarded"] > 0
        
        # 3. Check badges earned
        response = client.get("/api/badges")
        data = json.loads(response.data)
        earned = [b["name"] for b in data["earned_badges"]]
        assert "first_steps" in earned
        
        # 4. Complete a challenge
        response = client.post(
            "/api/challenges/boss_birthday/attempt",
            data=json.dumps({"password": "Secure-Passphrase-99!"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        assert data["validation"]["passed"] is True
        
        # 5. Check final progress
        response = client.get("/api/progress")
        data = json.loads(response.data)
        final_xp = data["xp"]["total"]
        
        # XP should have increased
        assert final_xp > initial_xp
        
        # Should have challenge completion
        assert "boss_birthday" in data["challenges"]
    
    def test_analysis_returns_progress_data(self, client, init_user):
        """Password analysis should always return progress data."""
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "test"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        assert "progress" in data
        progress = data["progress"]
        
        assert "xp_awarded" in progress
        assert "total_xp" in progress
        assert "level" in progress
        assert "level_progress" in progress


if __name__ == "__main__":
    pytest.main([__file__, "-v"])