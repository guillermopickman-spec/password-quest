"""
Password Quest - Flask Routes

Defines web routes and API endpoints for the gamified password trainer.
"""

import asyncio
from flask import Blueprint, render_template, request, jsonify, session, Response
import os
from functools import wraps

# Import core modules
import sys
from pathlib import Path

# Add parent directory to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.password_evaluator import evaluate_password_strength, PasswordStrengthResult
from core.breach_checker import check_pwned

# Import gamification modules
from app.models import db
from app.progress_service import (
    generate_session_id,
    get_or_create_user,
    record_password_analysis,
    get_user_progress,
    process_daily_checkin,
    complete_challenge,
    initialize_badges
)
from app.challenges import get_all_challenges, get_challenge, validate_challenge_attempt


# =============================================================================
# Blueprints
# =============================================================================

main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__)
admin_bp = Blueprint("admin", __name__)


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("Authorization")
        if api_key and api_key == os.getenv("ADMIN_API_KEY", "default-admin-key"):
            return f(*args, **kwargs)
        else:
            return jsonify({"error": "Unauthorized"}), 401
    return decorated_function


# =============================================================================
# Helper Functions
# =============================================================================

def get_current_user():
    """Get or create user from session."""
    session_id = session.get("session_id")
    if not session_id:
        session_id = generate_session_id()
        session["session_id"] = session_id
        session.permanent = True
    
    return get_or_create_user(session_id)


# =============================================================================
# Web Routes (Main Pages)
# =============================================================================

@main_bp.route("/")
def index():
    """
    Main dashboard - the password quest interface.
    
    Returns:
        Rendered HTML template with the gamified password checker.
    """
    # Ensure user session exists
    get_current_user()
    return render_template("index.html")


@main_bp.route("/challenges")
def challenges():
    """
    Scenario challenges page for structured learning.
    
    Returns:
        Rendered HTML template with level-based challenges.
    """
    return render_template("challenges.html")


@main_bp.route("/challenges/<challenge_id>")
def challenge_detail(challenge_id: str):
    """
    Individual challenge page.
    
    Args:
        challenge_id: The challenge identifier
    
    Returns:
        Rendered challenge page or 404 if not found
    """
    challenge = get_challenge(challenge_id)
    if not challenge:
        return render_template("challenges.html", error="Challenge not found"), 404
    
    # Get user progress for this challenge
    user = get_current_user()
    from app.progress_service import get_challenge_progress
    progress = get_challenge_progress(user, challenge_id)
    
    return render_template("challenge_detail.html", 
                           challenge=challenge,
                           progress=progress)


@main_bp.route("/leaderboard")
def leaderboard():
    """
    Leaderboard page showing top performers.
    
    Returns:
        Rendered HTML template with rankings.
    """
    return render_template("leaderboard.html")


# =============================================================================
# API Routes - Password Analysis
# =============================================================================

@api_bp.route("/analyze", methods=["POST"], endpoint="analyze_password")
def analyze_password():
    """
    Analyze password strength and breach status.
    
    POST JSON body:
        {
            "password": "string to analyze"
        }
    
    Returns:
        JSON response with:
        - score: int (0-4)
        - strength_label: str
        - entropy: float
        - crack_time_display: str
        - crack_time_seconds: float
        - feedback: list[str]
        - warning: str | None
        - is_breached: bool
        - breach_count: int | None
        - is_strong: bool
        - progress: dict (XP, level, badges)
    
    Security Note:
        - Password is never logged or stored
        - HIBP check uses k-anonymity (only sends hash prefix)
    """
    # Parse request
    data = request.get_json(silent=True) or {}
    password = data.get("password", "")
    
    # Validate input
    if not isinstance(password, str):
        return jsonify({
            "error": "Invalid input: password must be a string"
        }), 400
    
    # Empty password is valid input, just returns weak score
    if not password:
        return jsonify({
            "score": 0,
            "strength_label": "Empty",
            "entropy": 0.0,
            "crack_time_display": "instant",
            "crack_time_seconds": 0.0,
            "feedback": ["Enter a password to begin your quest!"],
            "warning": None,
            "is_breached": False,
            "breach_count": 0,
            "is_strong": False,
            "progress": None
        })
    
    # Perform strength analysis
    try:
        strength_result = evaluate_password_strength(password)
    except Exception as e:
        # Log error without password (security)
        return jsonify({
            "error": "Analysis failed",
            "message": str(e)
        }), 500
    
    # Check breach status
    try:
        breach_count = check_pwned(password)
        is_breached = breach_count is not None and breach_count > 0
    except Exception:
        # If breach check fails, continue without it
        breach_count = None
        is_breached = False
    
    # Record progress and award XP
    try:
        user = get_current_user()
        progress_update = record_password_analysis(
            user, 
            strength_result.score, 
            is_breached
        )
    except Exception as e:
        # Don\"t fail the request if progress tracking fails
        progress_update = None
    
    # Build response
    response = {
        "score": strength_result.score,
        "strength_label": strength_result.strength_label,
        "entropy": round(strength_result.entropy, 2),
        "crack_time_display": strength_result.crack_time_display,
        "crack_time_seconds": strength_result.crack_time_seconds,
        "feedback": strength_result.feedback,
        "warning": strength_result.warning,
        "is_breached": is_breached,
        "breach_count": breach_count,
        "is_strong": strength_result.score >= 3,
        "progress": progress_update
    }
    
    return jsonify(response)


# =============================================================================
# API Routes - Progress & Gamification
# =============================================================================

@api_bp.route("/progress", methods=["GET"])
def get_progress():
    """
    Get current user\"s progress summary.
    
    Returns:
        JSON with level, XP, badges, streaks, and challenge progress.
    """
    try:
        user = get_current_user()
        progress = get_user_progress(user)
        return jsonify(progress)
    except Exception as e:
        return jsonify({
            "error": "Failed to get progress",
            "message": str(e)
        }), 500


@api_bp.route("/progress/checkin", methods=["POST"])
def daily_checkin():
    """
    Process daily check-in for streak tracking.
    
    Returns:
        JSON with streak update and XP awarded.
    """
    try:
        user = get_current_user()
        result = process_daily_checkin(user)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "error": "Check-in failed",
            "message": str(e)
        }), 500


@api_bp.route("/badges", methods=["GET"])
def get_badges():
    """
    Get all available badges and user\"s earned badges.
    
    Returns:
        JSON with all badges and user\"s earned badges.
    """
    try:
        from app.progress_service import get_all_badges, get_user_badges
        
        user = get_current_user()
        
        return jsonify({
            "all_badges": get_all_badges(),
            "earned_badges": get_user_badges(user)
        })
    except Exception as e:
        return jsonify({
            "error": "Failed to get badges",
            "message": str(e)
        }), 500


# =============================================================================
# API Routes - Challenges
# =============================================================================

@api_bp.route("/challenges", methods=["GET"])
def get_challenges_list():
    """
    Get list of all available challenges.
    
    Returns:
        JSON array of challenges.
    """
    try:
        challenges = get_all_challenges()
        return jsonify({
            "challenges": challenges
        })
    except Exception as e:
        return jsonify({
            "error": "Failed to get challenges",
            "message": str(e)
        }), 500


@api_bp.route("/challenges/<challenge_id>", methods=["GET"])
def get_challenge_detail(challenge_id: str):
    """
    Get detailed information about a specific challenge.
    
    Args:
        challenge_id: The challenge identifier
    
    Returns:
        JSON with challenge details and user\"s progress.
    """
    try:
        challenge = get_challenge(challenge_id)
        if not challenge:
            return jsonify({
                "error": "Challenge not found"
            }), 404
        
        user = get_current_user()
        from app.progress_service import get_challenge_progress
        progress = get_challenge_progress(user, challenge_id)
        
        return jsonify({
            "challenge": challenge.to_dict(),
            "progress": progress
        })
    except Exception as e:
        return jsonify({
            "error": "Failed to get challenge",
            "message": str(e)
        }), 500


@api_bp.route("/challenges/<challenge_id>/attempt", methods=["POST"])
def attempt_challenge(challenge_id: str):
    """
    Submit a challenge attempt.
    
    POST JSON body:
        {
            "password": "the improved password"
        }
    
    Args:
        challenge_id: The challenge identifier
    
    Returns:
        JSON with validation results, XP awarded, and progress update.
    """
    try:
        challenge = get_challenge(challenge_id)
        if not challenge:
            return jsonify({
                "error": "Challenge not found"
            }), 404
        
        # Get submitted password
        data = request.get_json(silent=True) or {}
        password = data.get("password", "")
        
        if not password:
            return jsonify({
                "error": "Password is required"
            }), 400
        
        # Analyze the submitted password
        strength_result = evaluate_password_strength(password)
        
        # Check breach status
        try:
            breach_count = check_pwned(password)
            is_breached = breach_count is not None and breach_count > 0
        except Exception:
            is_breached = False
        
        # Validate against challenge requirements
        validation = validate_challenge_attempt(challenge_id, strength_result.score)
        
        # Record challenge completion if passed
        user = get_current_user()
        if validation["passed"]:
            completion_result = complete_challenge(user, challenge_id, strength_result.score)
        else:
            completion_result = None
        
        # Also award XP for the attempt (encouragement!)
        progress_update = record_password_analysis(user, strength_result.score, is_breached)
        
        return jsonify({
            "attempt": {
                "score": strength_result.score,
                "strength_label": strength_result.strength_label,
                "is_strong": strength_result.score >= 3,
                "feedback": strength_result.feedback,
                "is_breached": is_breached
            },
            "validation": validation,
            "completion": completion_result,
            "progress": progress_update
        })
        
    except Exception as e:
        return jsonify({
            "error": "Challenge attempt failed",
            "message": str(e)
        }), 500


# =============================================================================
# API Routes - System
# =============================================================================

@api_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        JSON with status and version info.
    """
    return jsonify({
        "status": "healthy",
        "service": "password-quest",
        "version": "1.1.0",
        "features": {
            "gamification": True,
            "challenges": True,
            "progress_tracking": True
        }
    })


@api_bp.route("/init", methods=["POST"])
def initialize_system():
    """
    Initialize system data (badges, etc).
    
    Should be called once after database setup.
    
    Returns:
        JSON with initialization status.
    """
    try:
        initialize_badges()
        return jsonify({
            "status": "initialized",
            "message": "System initialized successfully"
        })
    except Exception as e:
        return jsonify({
            "error": "Initialization failed",
            "message": str(e)
        }), 500


# =============================================================================
# API Routes - Admin
# =============================================================================

@admin_bp.route("/audit/export", methods=["GET"])
@require_api_key
def export_audit_data():
    """
    Export user progress data as a CSV file.

    Requires ADMIN_API_KEY in Authorization header.
    """
    from app.progress_service import get_all_user_progress_for_audit
    import csv
    import io

    try:
        audit_data = get_all_user_progress_for_audit()

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["session_id", "total_xp", "level", "badges_earned", "challenges_completed", "last_active"])

        # Write data
        for user_data in audit_data:
            writer.writerow([
                user_data["session_id"],
                user_data["total_xp"],
                user_data["level"],
                user_data["badges_earned"],
                user_data["challenges_completed"],
                user_data["last_active"]
            ])

        output.seek(0)

        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=audit_export.csv"}
        )

    except Exception as e:
        return jsonify({
            "error": "Failed to export audit data",
            "message": str(e)
        }), 500


