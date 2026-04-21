 
"""
Password Quest - Progress Service

Business logic for user progression, XP management, badge awarding,
and gamification features. Handles session-based user identification.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from app.models import db, User, XPTransaction, Badge, UserBadge, DailyStreak, ChallengeCompletion


# =============================================================================
# Default Badges Configuration
# =============================================================================

DEFAULT_BADGES = [
    {
        "name": "first_steps",
        "description": "Analyze your first password and begin your security journey",
        "icon": "🚀",
        "xp_bonus": 50
    },
    {
        "name": "breach_buster",
        "description": "Check 5 passwords that are safe from known breaches",
        "icon": "🛡️",
        "xp_bonus": 100
    },
    {
        "name": "stronghold",
        "description": "Get 5 'Strong' scores in a row",
        "icon": "🏰",
        "xp_bonus": 150
    },
    {
        "name": "diceware_disciple",
        "description": "Use the password generator to create a secure password",
        "icon": "🎲",
        "xp_bonus": 75
    },
    {
        "name": "streak_keeper",
        "description": "Maintain a 3-day practice streak",
        "icon": "🔥",
        "xp_bonus": 100
    },
    {
        "name": "week_warrior",
        "description": "Practice for 7 days straight",
        "icon": "📅",
        "xp_bonus": 200
    },
    {
        "name": "master_of_mystery",
        "description": "Create a password with a perfect score of 4",
        "icon": "🔐",
        "xp_bonus": 250
    },
    {
        "name": "security_sentinel",
        "description": "Complete all Level 1 challenges",
        "icon": "👁️",
        "xp_bonus": 300
    }
]


# =============================================================================
# XP Calculation Rules
# =============================================================================

XP_REWARDS = {
    "password_analysis": {
        0: 10,  # Very Weak - participation
        1: 15,  # Weak
        2: 25,  # Fair
        3: 50,  # Good
        4: 100  # Strong - perfect!
    },
    "breach_free_bonus": 25,
    "challenge_complete": {
        "base": 100,
        "bonus_per_score_point": 25  # Additional for score 3-4
    },
    "daily_checkin": {
        "base": 50,
        "streak_multiplier": 10  # +10 XP per day of streak
    }
}


# =============================================================================
# Session Management
# =============================================================================

def generate_session_id() -> str:
    """Generate a cryptographically secure session ID."""
    return secrets.token_urlsafe(32)


def get_or_create_user(session_id: str) -> User:
    """
    Get existing user by session ID or create new user.
    
    Args:
        session_id: Browser-stored session identifier
    
    Returns:
        User model instance
    """
    user = User.query.filter_by(session_id=session_id).first()
    
    if not user:
        user = User()
        user.session_id = session_id
        db.session.add(user)
        db.session.flush()  # Ensure user.id is available
        
        # Initialize streak tracking
        streak = DailyStreak(user=user)
        db.session.add(streak)
        
        db.session.commit()
    
    return user


# =============================================================================
# XP Management
# =============================================================================

def calculate_xp_for_analysis(score: int, is_breached: bool) -> int:
    """
    Calculate XP reward for password analysis.
    
    Args:
        score: Password strength score (0-4)
        is_breached: Whether password was found in breaches
    
    Returns:
        Total XP to award
    """
    base_xp = XP_REWARDS["password_analysis"].get(score, 10)
    
    # Bonus for breach-free passwords with good scores
    if not is_breached and score >= 3:
        base_xp += XP_REWARDS["breach_free_bonus"]
    
    return base_xp


def award_xp(user: User, amount: int, source: str, details: Optional[str] = None) -> XPTransaction:
    """
    Award XP to user and create transaction record.
    
    Args:
        user: User to award XP to
        amount: XP amount
        source: Source of XP (for analytics)
        details: Optional context details
    
    Returns:
        Created XPTransaction
    """
    transaction = XPTransaction(
        user=user,
        xp_amount=amount,
        source=source,
        details=details
    )
    db.session.add(transaction)
    db.session.commit()
    
    return transaction


def record_password_analysis(user: User, score: int, is_breached: bool) -> Dict[str, Any]:
    """
    Record password analysis and award appropriate XP.
    
    Args:
        user: User who analyzed password
        score: Password strength score (0-4)
        is_breached: Whether password was in breach database
    
    Returns:
        Dict with XP awarded and any unlocked badges
    """
    # Calculate and award XP
    xp_amount = calculate_xp_for_analysis(score, is_breached)
    award_xp(user, xp_amount, "password_analysis", f"score={score}, breached={is_breached}")
    
    # Check for badge unlocks
    unlocked_badges = check_badge_progress(user, score, is_breached)
    
    return {
        "xp_awarded": xp_amount,
        "total_xp": user.get_total_xp(),
        "level": user.get_level(),
        "level_progress": {
            "current": user.get_current_level_xp(),
            "required": user.get_level_xp_required()
        },
        "unlocked_badges": unlocked_badges
    }


# =============================================================================
# Badge Management
# =============================================================================

def initialize_badges():
    """Create default badges if they don't exist."""
    for badge_data in DEFAULT_BADGES:
        existing = Badge.query.filter_by(name=badge_data["name"]).first()
        if not existing:
            badge = Badge(**badge_data)
            db.session.add(badge)
    
    db.session.commit()


def award_badge(user: User, badge_name: str) -> Optional[Dict[str, Any]]:
    """
    Award a badge to user if not already earned.
    
    Args:
        user: User to award badge to
        badge_name: Name of badge to award
    
    Returns:
        Badge info if newly awarded, None if already had it
    """
    badge = Badge.query.filter_by(name=badge_name).first()
    if not badge:
        return None
    
    # Check if user already has this badge
    existing = UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first()
    if existing:
        return None
    
    # Award badge
    user_badge = UserBadge(user=user, badge_id=badge.id)
    db.session.add(user_badge)
    
    # Award bonus XP
    if badge.xp_bonus > 0:
        award_xp(user, badge.xp_bonus, "badge_bonus", f"Earned badge: {badge.name}")
    
    db.session.commit()
    
    return {
        "name": badge.name,
        "description": badge.description,
        "icon": badge.icon,
        "xp_bonus": badge.xp_bonus
    }


def check_badge_progress(user: User, score: int, is_breached: bool) -> List[Dict[str, Any]]:
    """
    Check and award badges based on current progress.
    
    Args:
        user: User to check
        score: Latest password score
        is_breached: Whether latest password was breached
    
    Returns:
        List of newly unlocked badges
    """
    unlocked = []
    
    # First Steps - first password analyzed
    total_xp = user.get_total_xp()
    if total_xp > 0:
        badge = award_badge(user, "first_steps")
        if badge:
            unlocked.append(badge)
    
    # Master of Mystery - perfect score
    if score == 4:
        badge = award_badge(user, "master_of_mystery")
        if badge:
            unlocked.append(badge)
    
    # Check streak badges
    if user.streak:
        if user.streak.current_streak >= 3:
            badge = award_badge(user, "streak_keeper")
            if badge:
                unlocked.append(badge)
        
        if user.streak.current_streak >= 7:
            badge = award_badge(user, "week_warrior")
            if badge:
                unlocked.append(badge)
    
    # Breach Buster - check history for 5 safe passwords
    safe_count = XPTransaction.query.filter(
        XPTransaction.user_id == user.id,
        XPTransaction.source == "password_analysis"
    ).count()  # Simplified - in production, track breach status separately
    
    if safe_count >= 5:
        badge = award_badge(user, "breach_buster")
        if badge:
            unlocked.append(badge)
    
    return unlocked


def get_user_badges(user: User) -> List[Dict[str, Any]]:
    """
    Get all badges earned by user.
    
    Args:
        user: User to get badges for
    
    Returns:
        List of badge info dicts
    """
    user_badges = UserBadge.query.filter_by(user_id=user.id).all()
    
    return [{
        "name": ub.badge.name,
        "description": ub.badge.description,
        "icon": ub.badge.icon,
        "earned_at": ub.earned_at.isoformat()
    } for ub in user_badges]


def get_all_badges() -> List[Dict[str, Any]]:
    """
    Get all available badges with their requirements.
    
    Returns:
        List of all badge definitions
    """
    badges = Badge.query.all()
    return [{
        "name": badge.name,
        "description": badge.description,
        "icon": badge.icon,
        "xp_bonus": badge.xp_bonus
    } for badge in badges]


# =============================================================================
# Streak Management
# =============================================================================

def process_daily_checkin(user: User) -> Dict[str, Any]:
    """
    Process daily check-in for user.
    
    Args:
        user: User checking in
    
    Returns:
        Check-in result with streak info
    """
    if not user.streak:
        streak = DailyStreak(user=user)
        db.session.add(streak)
        db.session.flush() # Ensure the streak is in the session for the check_in call
    
    result = user.streak.check_in()
    
    if result["success"]:
        # Award XP for check-in
        award_xp(user, result["xp_awarded"], "daily_checkin", f'Day {result["current_streak"]} streak')
        
        # Check for streak badges
        if result["current_streak"] >= 3:
            award_badge(user, "streak_keeper")
        
        if result["current_streak"] >= 7:
            award_badge(user, "week_warrior")
        
        db.session.commit()
    
    return result


def get_streak_status(user: User) -> Dict[str, Any]:
    """
    Get current streak status for user.
    
    Args:
        user: User to check
    
    Returns:
        Streak status dict
    """
    if not user.streak:
        return {
            "current_streak": 0,
            "max_streak": 0,
            "last_checkin": None,
            "can_checkin": True,
            "streak_at_risk": False
        }
    
    return user.streak.get_status()


# =============================================================================
# Challenge Progress
# =============================================================================

def complete_challenge(user: User, challenge_id: str, score: int) -> Dict[str, Any]:
    """
    Record challenge completion and award XP.
    
    Args:
        user: User completing challenge
        challenge_id: Challenge identifier
        score: Password score achieved (0-4)
    
    Returns:
        Completion result with XP awarded
    """
    # Check for existing completion
    existing = ChallengeCompletion.query.filter_by(
        user_id=user.id,
        challenge_id=challenge_id
    ).first()
    
    if existing:
        # Update best score if improved
        if score > existing.best_score:
            existing.best_score = score
            existing.attempts += 1
            improved = True
        else:
            existing.attempts += 1
            improved = False
        
        db.session.commit()
    else:
        # First completion
        completion = ChallengeCompletion(
            user=user,
            challenge_id=challenge_id,
            best_score=score,
            attempts=1
        )
        db.session.add(completion)
        improved = True
        
        # Award base completion XP
        base_xp = XP_REWARDS["challenge_complete"]["base"]
        bonus_xp = max(0, (score - 2)) * XP_REWARDS["challenge_complete"]["bonus_per_score_point"]
        total_xp = base_xp + bonus_xp
        
        award_xp(user, total_xp, "challenge_complete", f"challenge={challenge_id}, score={score}")
        
        # Check for security sentinel badge (all level 1 complete)
        level1_complete = ChallengeCompletion.query.filter(
            ChallengeCompletion.user_id == user.id,
            getattr(ChallengeCompletion.challenge_id, 'in_')(["boss_birthday", "the_simpleton"])
        ).count()
        
        if level1_complete >= 2:
            award_badge(user, "security_sentinel")
        
        db.session.commit()
    
    return {
        "completed": True,
        "improved": improved,
        "best_score": existing.best_score if existing else score,
        "attempts": existing.attempts if existing else 1,
        "total_xp": user.get_total_xp(),
        "level": user.get_level()
    }


def get_challenge_progress(user: User, challenge_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get user's challenge completion progress.
    
    Args:
        user: User to check
        challenge_id: Specific challenge (None for all)
    
    Returns:
        Challenge progress dict
    """
    if challenge_id:
        completion = ChallengeCompletion.query.filter_by(
            user_id=user.id,
            challenge_id=challenge_id
        ).first()
        
        if completion:
            return {
                "completed": True,
                "best_score": completion.best_score,
                "attempts": completion.attempts,
                "completed_at": completion.completed_at.isoformat()
            }
        return {"completed": False}
    
    # All challenges
    completions = ChallengeCompletion.query.filter_by(user_id=user.id).all()
    return {
        c.challenge_id: {
            "best_score": c.best_score,
            "attempts": c.attempts,
            "completed_at": c.completed_at.isoformat()
        }
        for c in completions
    }


# =============================================================================
# User Progress Summary
# =============================================================================

def get_user_progress(user: User) -> Dict[str, Any]:
    """
    Get complete user progress summary.
    
    Args:
        user: User to get progress for
    
    Returns:
        Complete progress dict for frontend display
    """
    return {
        "session_id": user.session_id,
        "level": user.get_level(),
        "xp": {
            "total": user.get_total_xp(),
            "current_level": user.get_current_level_xp(),
            "required_for_next": user.get_level_xp_required(),
            "next_level_threshold": user.get_xp_for_next_level()
        },
        "streak": get_streak_status(user),
        "badges": get_user_badges(user),
        "challenges": get_challenge_progress(user)
    }


def get_all_user_progress_for_audit() -> List[Dict[str, Any]]:
    """
    Get progress summary for all users for audit purposes.

    Returns:
        List of dicts, each containing a user's audit data.
    """
    users = User.query.all()
    audit_data = []

    for user in users:
        user_data = {
            "session_id": user.session_id,
            "total_xp": user.get_total_xp(),
            "level": user.get_level(),
            "badges_earned": len(user.badges),
            "challenges_completed": len(user.challenge_completions),
            "last_active": user.last_active.isoformat() if user.last_active else None
        }
        audit_data.append(user_data)

    return audit_data
