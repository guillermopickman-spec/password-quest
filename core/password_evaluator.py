"""
Password Evaluator Module

Evaluates password strength using both pattern matching and
professional entropy estimation via zxcvbn library.
"""

import math
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from zxcvbn import zxcvbn


@dataclass
class PasswordStrengthResult:
    """
    Container for password strength evaluation results.
    
    Attributes:
        score: zxcvbn score (0-4, where 4 is strongest)
        strength_label: Human-readable strength label
        entropy: Shannon entropy in bits (guesses_log2)
        crack_time_display: Human-readable crack time estimate
        crack_time_seconds: Estimated seconds to crack
        feedback: List of dictionaries, each with 'tip' and 'explainer'
        warning: High-level warning message
        has_patterns: Whether password contains common patterns
    """
    score: int
    strength_label: str
    entropy: float
    crack_time_display: str
    crack_time_seconds: float
    feedback: List[Dict[str, str]]
    warning: Optional[str]
    has_patterns: bool


# Regex-based checks for basic requirements
MIN_LENGTH = 12

# Explainers for feedback tips
EXPLAINERS = {
    "length_insufficient": {
        "tip": "Use at least {min_length} characters (current: insufficient)",
        "explainer": "Longer passwords increase the number of possible combinations, making them exponentially harder to guess or crack. Aim for at least 12-16 characters."
    },
    "add_lowercase": {
        "tip": "Add lowercase letters (a-z)",
        "explainer": "Including lowercase letters significantly expands the character set available, making brute-force attacks more time-consuming."
    },
    "add_uppercase": {
        "tip": "Add uppercase letters (A-Z)",
        "explainer": "Adding uppercase letters, along with lowercase, further increases the complexity and length of time required to crack your password."
    },
    "add_numbers": {
        "tip": "Add numbers (0-9)",
        "explainer": "Numbers introduce another type of character, adding to the password's entropy and making it harder for attackers to predict."
    },
    "add_special": {
        "tip": "Add special characters (!@#$%^&*)",
        "explainer": "Special characters diversify your password, making it much more resistant to dictionary and brute-force attacks."
    },
    "generic_longer_random": {
        "tip": "Consider using a longer, more random password",
        "explainer": "Randomness and length are the two most critical factors in password strength. Avoid predictable patterns and personal information."
    },
    "avoid_common_words": {
        "tip": "Avoid common words and patterns",
        "explainer": "Many password attacks use dictionaries of common words and known patterns. Avoid using easily guessable sequences, dates, or personal names."
    },
    "use_passphrase": {
        "tip": "Try a passphrase (multiple random words)",
        "explainer": "Passphrases like 'correct horse battery staple' are long, random, and easier to remember than complex, short passwords. They offer excellent security."
    },
    "no_personal_info": {
        "tip": "Do not use personal information",
        "explainer": "Birthdays, names, pet names, or any easily discoverable personal information make your password vulnerable to social engineering and reconnaissance attacks."
    },
    "keyboard_patterns": {
        "tip": "Avoid keyboard patterns (e.g., 'qwerty', 'asdfgh')",
        "explainer": "Sequential keys on a keyboard are highly predictable and easily guessed by attackers. Choose characters that are not adjacent."
    }
}


def check_basic_requirements(password: str) -> dict:
    """
    Check basic password requirements using regex patterns.
    
    Args:
        password: Password to check
    
    Returns:
        Dictionary with check results
    """
    return {
        "length_ok": len(password) >= MIN_LENGTH,
        "has_uppercase": bool(re.search(r"[A-Z]", password)),
        "has_lowercase": bool(re.search(r"[a-z]", password)),
        "has_digits": bool(re.search(r"\d", password)),
        "has_special": bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)),
    }


def get_missing_requirements(checks: dict) -> List[Dict[str, str]]:
    """
    Generate feedback for missing requirements.
    
    Args:
        checks: Result from check_basic_requirements
    
    Returns:
        List of improvement suggestions with explainers
    """
    feedback: List[Dict[str, str]] = []
    
    if not checks["length_ok"]:
        feedback.append(EXPLAINERS["length_insufficient"].copy())
        feedback[-1]["tip"] = feedback[-1]["tip"].format(min_length=MIN_LENGTH)
    
    if not checks["has_lowercase"]:
        feedback.append(EXPLAINERS["add_lowercase"].copy())
    
    if not checks["has_uppercase"]:
        feedback.append(EXPLAINERS["add_uppercase"].copy())
    
    if not checks["has_digits"]:
        feedback.append(EXPLAINERS["add_numbers"].copy())
    
    if not checks["has_special"]:
        feedback.append(EXPLAINERS["add_special"].copy())
    
    return feedback


def evaluate_password_strength(password: str) -> PasswordStrengthResult:
    """
    Evaluate password strength using zxcvbn and custom checks.
    
    Combines professional entropy estimation from zxcvbn with
    basic requirement checking for comprehensive evaluation.
    
    Args:
        password: Password to evaluate
    
    Returns:
        PasswordStrengthResult with detailed analysis
    """
    # Get zxcvbn analysis
    zxcvbn_result = zxcvbn(password)
    
    # Map zxcvbn score to label
    score_labels = {
        0: "Very Weak",
        1: "Weak", 
        2: "Fair",
        3: "Good",
        4: "Strong"
    }
    
    # Get feedback from zxcvbn
    zxcvbn_feedback_strings = zxcvbn_result["feedback"]["suggestions"]
    warning = zxcvbn_result["feedback"]["warning"] or None
    
    # Convert zxcvbn feedback to our structured format
    feedback_list: List[Dict[str, str]] = []
    for tip_str in zxcvbn_feedback_strings:
        # Attempt to map common zxcvbn tips to our explainers
        if "use a few words" in tip_str.lower():
            feedback_list.append(EXPLAINERS["use_passphrase"].copy())
        elif "no personal info" in tip_str.lower():
            feedback_list.append(EXPLAINERS["no_personal_info"].copy())
        elif "avoid common words" in tip_str.lower():
            feedback_list.append(EXPLAINERS["avoid_common_words"].copy())
        elif "avoid keyboard patterns" in tip_str.lower():
            feedback_list.append(EXPLAINERS["keyboard_patterns"].copy())
        else:
            feedback_list.append({"tip": tip_str, "explainer": "This is a general suggestion from the password strength engine."})
    
    # Add our custom requirements check
    basic_checks = check_basic_requirements(password)
    missing = get_missing_requirements(basic_checks)
    
    # Combine feedback (prepend our basic requirements if any)
    if missing:
        feedback_list = missing + feedback_list
    
    # If no feedback but score is low, add generic message
    if not feedback_list and zxcvbn_result["score"] < 3:
        feedback_list.append(EXPLAINERS["generic_longer_random"].copy())
    
    # Check for patterns (dictionary words, sequences, etc.)
    has_patterns = bool(
        zxcvbn_result["sequence"] or 
        warning or 
        zxcvbn_result["score"] < 3
    )
    
    # Calculate entropy from guesses (log2)
    guesses = zxcvbn_result["guesses"]  # type: ignore
    entropy = math.log2(float(guesses)) if guesses > 0 else 0.0
    
    return PasswordStrengthResult(
        score=zxcvbn_result["score"],
        strength_label=score_labels.get(zxcvbn_result["score"], "Unknown"),
        entropy=entropy,
        crack_time_display=zxcvbn_result["crack_times_display"]["offline_slow_hashing_1e4_per_second"],
        crack_time_seconds=float(zxcvbn_result["crack_times_seconds"]["offline_slow_hashing_1e4_per_second"]),
        feedback=feedback_list,
        warning=warning,
        has_patterns=has_patterns
    )


def format_strength_result(result: PasswordStrengthResult) -> str:
    """
    Format password strength result for display.
    
    Args:
        result: PasswordStrengthResult to format
    
    Returns:
        Formatted multi-line string
    """
    # Strength indicator with emoji
    emojis = {
        "Very Weak": "🔴",
        "Weak": "🟠", 
        "Fair": "🟡",
        "Good": "🟢",
        "Strong": "🟢"
    }
    
    emoji = emojis.get(result.strength_label, "⚪")
    
    lines = [
        f"{emoji}  Strength: {result.strength_label} (Score: {result.score}/4)",
        f"📊  Entropy: {result.entropy:.1f} bits",
        f"⏱️   Crack time: {result.crack_time_display}"
    ]
    
    if result.warning:
        lines.append(f"⚠️   Warning: {result.warning}")
    
    if result.feedback:
        lines.append("\n💡 Suggestions:")
        for item in result.feedback:
            lines.append(f"   • {item['tip']} (Explainer: {item['explainer']})")  # Updated to show explainer
    
    return "\n".join(lines)


def is_password_strong(password: str, min_score: int = 3) -> bool:
    """
    Quick check if password meets strong criteria.
    
    Args:
        password: Password to check
        min_score: Minimum zxcvbn score (default: 3 - Good)
    
    Returns:
        True if password is strong enough
    """
    result = evaluate_password_strength(password)
    return result.score >= min_score


def get_password_recommendations(password: str) -> List[str]:
    """
    Get actionable recommendations for improving password.
    
    Args:
        password: Current password
    
    Returns:
        List of specific recommendations (only tips, no explainers)
    """
    result = evaluate_password_strength(password)
    
    recommendations = []
    
    # Add high priority items first
    if not check_basic_requirements(password)["length_ok"]:
        recommendations.append(EXPLAINERS["length_insufficient"]["tip"].format(min_length=MIN_LENGTH))
    
    if result.warning:
        recommendations.append(f"Address: {result.warning}")
    
    # Add other feedback
    for item in result.feedback:
        if item["tip"] not in recommendations:
            recommendations.append(item["tip"])
    
    return recommendations
