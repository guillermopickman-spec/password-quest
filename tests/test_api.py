
"""
Password Quest - API Endpoint Tests

Tests for Flask API routes including:
- /api/analyze endpoint
- /api/health endpoint
- Input validation
- Response structure
"""

import json
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(config_name="testing")
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestHealthEndpoint:
    """Tests for /api/health endpoint."""
    
    def test_health_returns_200(self, client):
        """Health check should return 200 OK."""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_health_returns_json(self, client):
        """Health check should return JSON."""
        response = client.get("/api/health")
        assert response.content_type == "application/json"
    
    def test_health_contains_expected_fields(self, client):
        """Health response should have status and service fields."""
        response = client.get("/api/health")
        data = json.loads(response.data)
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "password-quest"
        assert "version" in data


class TestAnalyzeEndpoint:
    """Tests for /api/analyze endpoint."""
    
    def test_analyze_returns_200_for_valid_password(self, client):
        """Valid password should return 200."""
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "test123!"}),
            content_type="application/json"
        )
        assert response.status_code == 200
    
    def test_analyze_returns_json(self, client):
        """Response should be JSON."""
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "test"}),
            content_type="application/json"
        )
        assert response.content_type == "application/json"
    
    def test_analyze_requires_password_field(self, client):
        """Missing password field should still work with empty string."""
        response = client.post(
            "/api/analyze",
            data=json.dumps({}),
            content_type="application/json"
        )
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data["score"] == 0
        assert data["strength_label"] == "Empty"
    
    def test_analyze_returns_expected_structure(self, client):
        """Response should have all expected fields."""
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "SecureP@ssw0rd123!"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        # Core fields
        assert "score" in data
        assert isinstance(data["score"], int)
        assert 0 <= data["score"] <= 4
        
        assert "strength_label" in data
        assert isinstance(data["strength_label"], str)
        
        assert "entropy" in data
        assert isinstance(data["entropy"], float)
        
        assert "crack_time_display" in data
        assert isinstance(data["crack_time_display"], str)
        
        assert "crack_time_seconds" in data
        assert isinstance(data["crack_time_seconds"], (int, float))
        
        assert "feedback" in data
        assert isinstance(data["feedback"], list)
        
        assert "warning" in data
        
        assert "is_breached" in data
        assert isinstance(data["is_breached"], bool)
        
        assert "breach_count" in data
        
        assert "is_strong" in data
        assert isinstance(data["is_strong"], bool)
    
    def test_analyze_weak_password_low_score(self, client):
        """Weak password should have low score."""
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "123456"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        assert data["score"] < 2
        assert data["is_strong"] is False
    
    def test_analyze_strong_password_high_score(self, client):
        """Strong password should have high score."""
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "Correct-Horse-Battery-Staple!47"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        assert data["score"] >= 3
        assert data["is_strong"] is True
    
    def test_analyze_empty_password(self, client):
        """Empty password should return empty label."""
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": ""}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        assert data["score"] == 0
        assert data["strength_label"] == "Empty"
        assert len(data["feedback"]) > 0
    
    def test_analyze_rejects_non_string_password(self, client):
        """Non-string password should return error."""
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": 12345}),
            content_type="application/json"
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
    
    def test_analyze_common_password_detected(self, client):
        """Common passwords should be detected."""
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "password123"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        # Should be very weak
        assert data["score"] <= 1
        # Should have warning
        assert data["warning"] is not None or len(data["feedback"]) > 0
    
    def test_analyze_provides_feedback(self, client):
        """Weak passwords should provide improvement feedback."""
        response = client.post(
            "/api/analyze",
            data=json.dumps({"password": "abc"}),
            content_type="application/json"
        )
        data = json.loads(response.data)
        
        # Should have feedback for improvement
        assert len(data["feedback"]) > 0
        # Feedback should be strings
        assert all(isinstance(f, str) for f in data["feedback"])


class TestCORSHeaders:
    """Tests for CORS headers."""
    
    def test_cors_headers_present_on_api(self, client):
        """API endpoints should have CORS headers."""
        response = client.options("/api/analyze")
        # CORS preflight should work
        assert response.status_code == 200


class TestSecurityHeaders:
    """Tests for security headers."""
    
    def test_security_headers_present(self, client):
        """Responses should include security headers."""
        response = client.get("/api/health")
        
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
    
    def test_csp_header_present(self, client):
        """Content Security Policy should be set."""
        response = client.get("/")
        assert "Content-Security-Policy" in response.headers


class TestMainRoutes:
    """Tests for main web routes."""
    
    def test_index_page_loads(self, client):
        """Homepage should load successfully."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Password Quest" in response.data
    
    def test_challenges_page_loads(self, client):
        """Challenges page should load."""
        response = client.get("/challenges")
        assert response.status_code == 200
    
    def test_leaderboard_page_loads(self, client):
        """Leaderboard page should load."""
        response = client.get("/leaderboard")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
