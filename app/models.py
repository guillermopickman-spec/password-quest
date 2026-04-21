"""
Password Quest - Database Models

SQLAlchemy ORM models for user progress, badges, and gamification.
All models use session-based identification (no personal data stored).
"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """
    User session tracking (anonymous, no PII stored).
    
    Users are identified by a session_id stored in browser localStorage.
    No passwords, emails, or personal information is ever stored.
    """
    
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    xp_transactions = db.relationship("XPTransaction", backref="user", lazy=True, cascade="all, delete-orphan")
    badges = db.relationship("UserBadge", backref="user", lazy=True, cascade="all, delete-orphan")
    streak = db.relationship("DailyStreak", backref="user", lazy=True, uselist=False, cascade="all, delete-orphan")
    challenge_completions = db.relationship("ChallengeCompletion", backref="user", lazy=True, cascade="all, delete-orphan")
    
    def get_total_xp(self) -> int:
        """Calculate total XP from all transactions."""
        return db.session.query(db.func.sum(XPTransaction.xp_amount)).filter(
            XPTransaction.user_id == self.id
        ).scalar() or 0
    
    def get_level(self) -> int:
        """
        Calculate user level based on total XP.
        
        Level formula: XP thresholds increase exponentially
        Level 1: 0-999 XP
        Level 2: 1000-2499 XP
        Level 3: 2500-4999 XP
        Level 4: 5000-9999 XP
        Level 5+: +5000 XP per level
        """
        xp = self.get_total_xp()
        if xp < 1000:
            return 1
        elif xp < 2500:
            return 2
        elif xp < 5000:
            return 3
        elif xp < 10000:
            return 4
        else:
            return 5 + (xp - 10000) // 5000
    
    def get_xp_for_next_level(self) -> int:
        """Get XP required to reach next level."""
        level = self.get_level()
        thresholds = {1: 1000, 2: 2500, 3: 5000, 4: 10000}
        return thresholds.get(level, 10000 + (level - 4) * 5000)
    
    def get_current_level_xp(self) -> int:
        """Get XP progress within current level."""
        total_xp = self.get_total_xp()
        current_level = self.get_level()
        
        # Calculate XP at start of current level
        if current_level == 1:
            level_start = 0
        elif current_level == 2:
            level_start = 1000
        elif current_level == 3:
            level_start = 2500
        elif current_level == 4:
            level_start = 5000
        else:
            level_start = 10000 + (current_level - 5) * 5000
        
        return total_xp - level_start
    
    def get_level_xp_required(self) -> int:
        """Get XP needed to complete current level."""
        current_level = self.get_level()
        return self.get_xp_for_next_level() - (
            0 if current_level == 1 else
            1000 if current_level == 2 else
            2500 if current_level == 3 else
            5000 if current_level == 4 else
            10000 + (current_level - 5) * 5000
        )


class XPTransaction(db.Model):
    """
    XP award history (gamification tracking).
    
    Records all XP gains with source attribution for analytics.
    """
    
    __tablename__ = "xp_transactions"

    def __init__(self, user: 'User', xp_amount: int, source: str, details: Optional[str] = None):
        self.user = user
        self.xp_amount = xp_amount
        self.source = source
        self.details = details
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), index=True)
    xp_amount: Mapped[int]
    source: Mapped[str] = mapped_column(db.String(50))
    details: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<XPTransaction {self.xp_amount}xp from {self.source}>"


class Badge(db.Model):
    """
    Available badges/achievements.
    
    Pre-populated badges that users can earn.
    """
    
    __tablename__ = "badges"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(10), nullable=False)  # Emoji or short icon code
    xp_bonus = db.Column(db.Integer, default=0)  # Bonus XP for earning
    
    # Relationships
    users = db.relationship("UserBadge", backref="badge", lazy=True)
    
    def __repr__(self) -> str:
        return f"<Badge {self.name}>"


class UserBadge(db.Model):
    """
    Junction table for earned badges.
    
    Tracks when users earned each badge (many-to-many relationship).
    """
    
    __tablename__ = "user_badges"

    def __init__(self, user: 'User', badge_id: int):
        self.user = user
        self.badge_id = badge_id
    
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    badge_id = db.Column(db.Integer, db.ForeignKey("badges.id"), primary_key=True)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self) -> str:
        return f"<UserBadge user={self.user_id} badge={self.badge_id}>"


class DailyStreak(db.Model):
    """
    Daily engagement streak tracking.
    
    Encourages regular practice through streak mechanics.
    """
    
    __tablename__ = "daily_streaks"
    
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    current_streak = db.Column(db.Integer, default=0, nullable=False)
    last_checkin = db.Column(db.Date, nullable=True)
    max_streak = db.Column(db.Integer, default=0, nullable=False)

    def __init__(self, user: 'User'):
        self.user = user
    
    def check_in(self) -> dict:
        """
        Process a daily check-in.
        
        Returns dict with:
        - success: bool (whether check-in was valid)
        - streak_continued: bool (if streak increased)
        - streak_broken: bool (if streak reset)
        - current_streak: int
        - xp_awarded: int
        """
        today = date.today()
        
        # Already checked in today
        if self.last_checkin == today:
            return {
                "success": False,
                "streak_continued": False,
                "streak_broken": False,
                "current_streak": self.current_streak,
                "xp_awarded": 0,
                "message": "Already checked in today!"
            }
        
        # Check if streak continues (checked in yesterday)
        if self.last_checkin and (today - self.last_checkin).days == 1:
            self.current_streak += 1
            streak_continued = True
            streak_broken = False
            message = "Streak continued! 🔥"
        elif self.last_checkin and (today - self.last_checkin).days > 1:
            # Streak broken
            self.current_streak = 1
            streak_continued = False
            streak_broken = True
            message = "Streak reset, but you're back! 💪"
        else:
            # First check-in or after long gap
            self.current_streak = 1
            streak_continued = False
            streak_broken = False
            message = "First check-in! Welcome! 🎉"
        
        # Update max streak
        if self.current_streak > self.max_streak:
            self.max_streak = self.current_streak
        
        self.last_checkin = today
        
        # Calculate XP based on streak length
        xp_awarded = min(50 + (self.current_streak * 10), 200)  # Cap at 200 XP
        
        return {
            "success": True,
            "streak_continued": streak_continued,
            "streak_broken": streak_broken,
            "current_streak": self.current_streak,
            "max_streak": self.max_streak,
            "xp_awarded": xp_awarded,
            "message": message
        }
    
    def get_status(self) -> dict:
        """Get current streak status."""
        today = date.today()
        can_checkin = self.last_checkin != today
        
        # Check if streak is at risk (missed yesterday)
        streak_at_risk = False
        if self.last_checkin and self.current_streak > 0:
            days_since = (today - self.last_checkin).days
            streak_at_risk = days_since >= 1 and days_since < 2
        
        return {
            "current_streak": self.current_streak,
            "max_streak": self.max_streak,
            "last_checkin": self.last_checkin.isoformat() if self.last_checkin else None,
            "can_checkin": can_checkin,
            "streak_at_risk": streak_at_risk
        }


class ChallengeCompletion(db.Model):
    """
    Track which challenges users have completed.
    
    Links to scenario challenges with completion time and score.
    """
    
    __tablename__ = "challenge_completions"
    
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    challenge_id = db.Column(db.String(50), primary_key=True)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    attempts = db.Column(db.Integer, default=1, nullable=False)
    best_score = db.Column(db.Integer, nullable=False)  # Password score 0-4
    
    def __init__(self, user: 'User', challenge_id: str, best_score: int, attempts: int):
        self.user = user
        self.challenge_id = challenge_id
        self.best_score = best_score
        self.attempts = attempts

    def __repr__(self) -> str:
        return f"<ChallengeCompletion {self.challenge_id} score={self.best_score}>"
