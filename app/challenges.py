"""
Password Quest - Challenge Definitions

Scenario-based challenges that teach password security concepts
through interactive, gamified experiences.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class DifficultyLevel(Enum):
    """Challenge difficulty levels."""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4


@dataclass
class ChallengeHint:
    """Hint for helping users complete challenges."""
    order: int
    text: str
    unlock_after_attempts: int = 0  # Auto-unlock after N failed attempts


@dataclass
class Challenge:
    """
    A scenario-based password security challenge.
    
    Each challenge presents a realistic scenario with a weak password,
    and the user must create a stronger alternative that meets requirements.
    """
    id: str
    level: int
    difficulty: DifficultyLevel
    title: str
    scenario: str
    scenario_details: str
    weak_password: str
    weak_password_explanation: str
    min_score_to_pass: int
    hints: List[ChallengeHint]
    success_message: str
    lesson_learned: str
    xp_bonus: int = 100
    
    def to_dict(self) -> Dict:
        """Convert challenge to dictionary for API/frontend."""
        return {
            "id": self.id,
            "level": self.level,
            "difficulty": self.difficulty.name,
            "title": self.title,
            "scenario": self.scenario,
            "scenario_details": self.scenario_details,
            "weak_password": self.weak_password,
            "weak_password_explanation": self.weak_password_explanation,
            "min_score_to_pass": self.min_score_to_pass,
            "hints": [
                {
                    "order": h.order,
                    "text": h.text,
                    "unlock_after_attempts": h.unlock_after_attempts
                }
                for h in sorted(self.hints, key=lambda x: x.order)
            ],
            "success_message": self.success_message,
            "lesson_learned": self.lesson_learned,
            "xp_bonus": self.xp_bonus
        }


# =============================================================================
# Level 1 Challenges
# =============================================================================

BOSS_BIRTHDAY_CHALLENGE = Challenge(
    id="boss_birthday",
    level=1,
    difficulty=DifficultyLevel.BEGINNER,
    title="The Boss's Birthday",
    scenario="Your Coworker's Insecure Secret",
    scenario_details="""
    <p>You've just started at a new company and noticed your coworker, Sarah Johnson, 
    has a sticky note on her monitor with her password: <code>Johnson1975!</code></p>
    
    <p>She mentions she was born in 1975 and this password is "easy to remember."</p>
    
    <p>Your task: Help Sarah create a much stronger password that she'll still 
    find memorable, but hackers won't crack in seconds.</p>
    
    <div class="bg-quest-card/50 border-l-4 border-quest-warning p-4 my-4">
        <p class="text-sm text-gray-300">
            <strong>💡 Teaching Moment:</strong> Passwords based on personal information 
            (names, birthdates, family members) are among the first things attackers try. 
            They're easy to guess from social media and public records.
        </p>
    </div>
    """,
    weak_password="Johnson1975!",
    weak_password_explanation="""
    This password fails because:
    • Uses a common surname found in dictionaries
    • Includes birth year - publicly available information
    • Follows predictable pattern: Name + Year + Symbol
    • Too short for modern security standards
    """,
    min_score_to_pass=3,
    hints=[
        ChallengeHint(
            order=1,
            text="Personal info (names, dates) is easily discovered. Try using a random phrase instead.",
            unlock_after_attempts=0
        ),
        ChallengeHint(
            order=2,
            text="Think of 3-4 random unrelated words. Example: 'correct horse battery staple'",
            unlock_after_attempts=1
        ),
        ChallengeHint(
            order=3,
            text="Add numbers and symbols in unexpected places, not just at the end.",
            unlock_after_attempts=2
        )
    ],
    success_message="""
    🎉 Excellent work! You've helped Sarah upgrade from a vulnerable password to 
    something truly secure. Remember: the best passwords are long, random, and 
    have no connection to your personal life.
    """,
    lesson_learned="""
    Personal information makes terrible passwords because it's often public 
    knowledge or easily guessed. Use random passphrases instead - they're 
    both secure and memorable!
    """,
    xp_bonus=100
)


# =============================================================================
# Level 2 Challenges
# =============================================================================

THE_SIMPLETON_CHALLENGE = Challenge(
    id="the_simpleton",
    level=2,
    difficulty=DifficultyLevel.BEGINNER,
    title="The Simpleton",
    scenario="The Admin's Awful Password",
    scenario_details="""
    <p>Your company's system administrator - the person with access to EVERYTHING - 
    uses this password: <code>password123</code></p>
    
    <p>When questioned, they say "It's easy to remember and I added numbers!"</p>
    
    <p>This is a critical security risk. You need to convince them to change it 
    to something that will actually protect the company's systems.</p>
    
    <div class="bg-quest-card/50 border-l-4 border-quest-danger p-4 my-4">
        <p class="text-sm text-gray-300">
            <strong>🚨 Critical Vulnerability:</strong> Common passwords like 
            "password123" are tried by attackers within the first few seconds of 
            an attack. They're in every password cracking dictionary.
        </p>
    </div>
    """,
    weak_password="password123",
    weak_password_explanation="""
    This password is extremely dangerous because:
    • "password" is the #1 most common password in the world
    • Adding sequential numbers (123) doesn't help - attackers try these first
    • Appears in every password breach database
    • Can be cracked instantly with any password cracking tool
    """,
    min_score_to_pass=4,  # Must be perfect for this one!
    hints=[
        ChallengeHint(
            order=1,
            text="Forget everything about the original password. Start completely fresh.",
            unlock_after_attempts=0
        ),
        ChallengeHint(
            order=2,
            text="Think of a sentence only you know. Use first letters + modifications.",
            unlock_after_attempts=1
        ),
        ChallengeHint(
            order=3,
            text="Aim for 16+ characters with mixed case, numbers, and symbols scattered throughout.",
            unlock_after_attempts=2
        ),
        ChallengeHint(
            order=4,
            text="Example approach: 'My first car was a red 1987 Honda!' → Mfcw@r'87H!",
            unlock_after_attempts=3
        )
    ],
    success_message="""
    🛡️ Outstanding! You've potentially saved the company from a catastrophic breach. 
    Admin passwords should be the strongest of all - and now they are!
    """,
    lesson_learned="""
    Common passwords and simple patterns are worthless against modern attacks. 
    Administrator accounts need exceptional passwords because they hold the keys 
    to the entire kingdom.
    """,
    xp_bonus=150
)


# =============================================================================
# Level 3 Challenges (Future)
# =============================================================================

REUSED_PASSWORDS_CHALLENGE = Challenge(
    id="reuse_victim",
    level=3,
    difficulty=DifficultyLevel.INTERMEDIATE,
    title="The Reuse Victim",
    scenario="One Password to Rule Them All",
    scenario_details="""
    <p>Alex uses the same strong password everywhere: <code>Tr0ub4dor&3</code></p>
    
    <p>It looks secure - mixed case, numbers, symbols. But Alex just got an email 
    saying "Your Netflix account password was found in a data breach."</p>
    
    <p>Now attackers have this password and are trying it on every service Alex uses.</p>
    
    <div class="bg-quest-card/50 border-l-4 border-quest-warning p-4 my-4">
        <p class="text-sm text-gray-300">
            <strong>⚠️ The Hidden Danger:</strong> Even strong passwords become 
            dangerous when reused. One breach compromises everything.
        </p>
    </div>
    """,
    weak_password="Tr0ub4dor&3",
    weak_password_explanation="""
    This password is technically strong but fails due to reuse:
    • Found in multiple breach databases from various service hacks
    • Once leaked, attackers try it everywhere
    • Password managers solve this by generating unique passwords
    • Reuse is one of the top causes of account takeovers
    """,
    min_score_to_pass=3,
    hints=[
        ChallengeHint(
            order=1,
            text="Create a unique password that has never been used anywhere else.",
            unlock_after_attempts=0
        ),
        ChallengeHint(
            order=2,
            text="Consider using a password manager to generate and store unique passwords.",
            unlock_after_attempts=1
        )
    ],
    success_message="""
    🔐 Perfect! Unique passwords are essential - never reuse, even if the password 
    seems strong. Consider a password manager to handle them all securely.
    """,
    lesson_learned="""
    Password reuse is dangerous because breaches are common. A strong password 
    used on 10 sites becomes 10 vulnerabilities. Use unique passwords everywhere.
    """,
    xp_bonus=200
)


# =============================================================================
# Challenge Registry
# =============================================================================

ALL_CHALLENGES: Dict[str, Challenge] = {
    "boss_birthday": BOSS_BIRTHDAY_CHALLENGE,
    "the_simpleton": THE_SIMPLETON_CHALLENGE,
    "reuse_victim": REUSED_PASSWORDS_CHALLENGE,
}


def get_challenge(challenge_id: str) -> Optional[Challenge]:
    """Get a challenge by ID."""
    return ALL_CHALLENGES.get(challenge_id)


def get_challenges_by_level(level: Optional[int] = None) -> List[Challenge]:
    """Get challenges, optionally filtered by level."""
    challenges = list(ALL_CHALLENGES.values())
    if level:
        challenges = [c for c in challenges if c.level == level]
    return sorted(challenges, key=lambda x: (x.level, x.difficulty.value))


def get_all_challenges() -> List[Dict]:
    """Get all challenges as dictionaries."""
    return [c.to_dict() for c in get_challenges_by_level()]


def validate_challenge_attempt(challenge_id: str, score: int) -> Dict:
    """
    Validate if a challenge attempt meets passing criteria.
    
    Args:
        challenge_id: Challenge being attempted
        score: Password strength score achieved (0-4)
    
    Returns:
        Dict with success status and feedback
    """
    challenge = get_challenge(challenge_id)
    if not challenge:
        return {
            "valid": False,
            "error": "Challenge not found"
        }
    
    passed = score >= challenge.min_score_to_pass
    
    return {
        "valid": True,
        "passed": passed,
        "min_required": challenge.min_score_to_pass,
        "achieved": score,
        "xp_bonus": challenge.xp_bonus if passed else 0,
        "success_message": challenge.success_message if passed else None,
        "lesson_learned": challenge.lesson_learned if passed else None,
        "feedback": "Try again! Your password needs to be stronger." if not passed else None
    }