# 🔐 Password Quest

An interactive password security training platform that gamifies learning strong password practices. Built with Flask and modern password security best practices.

## 🎯 Overview

Password Quest transforms password security education into an engaging, game-like experience. Instead of boring compliance training, users learn through interactive challenges, real-time feedback, and achievement systems.

## ✨ Features

### Core Security Engine ✅
- **Password Strength Analysis** - Uses Dropbox's zxcvbn for professional entropy estimation
- **Breach Detection** - HaveIBeenPwned API integration with k-anonymity
- **Secure Generation** - Cryptographically secure password and passphrase generation
- **Policy Profiles** - Configurable compliance frameworks (SOC2, NIST, PCI-DSS)

### Gamified Frontend ✅
- **Real-time Analysis** - Instant password feedback as you type
- **Visual Strength Meter** - Color-coded progress bar (Red → Yellow → Green)
- **Hacker Alert** - Glowing red warning for breached passwords
- **Coach Tips** - Duo-style encouraging feedback for improvement
- **Dark Theme** - Modern gamified UI with Tailwind CSS

### Gamification Layer (Coming Soon)
- **XP System** - Earn experience points for strong passwords
- **Achievement Badges** - "Breach Buster", "Diceware Disciple", and more
- **Daily Streaks** - Maintain your security learning streak
- **Scenario Challenges** - Fix realistic password scenarios (e.g., "The Boss's Birthday")

## 🏗️ Project Structure

```
password-quest/
├── app/                    # Flask Web Application
│   ├── __init__.py        # App factory with security headers
│   ├── routes.py          # API routes and web views
│   ├── templates/         # HTML Templates (Jinja2)
│   │   ├── base.html      # Base layout with gamified UI
│   │   ├── index.html     # Main password analyzer
│   │   ├── challenges.html # Scenario challenges
│   │   └── leaderboard.html # Rankings page
│   └── static/            # CSS, JS, Assets (if needed)
├── core/                   # Security Engine (The Logic)
│   ├── password_evaluator.py  # zxcvbn-based analysis
│   ├── breach_checker.py      # HIBP API with k-anonymity
│   ├── password_generator.py  # Secure generation
│   ├── config.py              # Policy profiles & settings
│   └── logger.py              # Structured logging
├── tests/                  # Pytest Suite
│   ├── __init__.py
│   └── test_api.py        # 19 comprehensive tests
├── data/                   # Training Modules (JSON/YAML)
├── manual_test.py          # Quick manual testing script
├── run.py                  # Application Entry Point
└── requirements.txt        # Dependencies
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd password-quest
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python run.py
```

The application will be available at `http://127.0.0.1:5000`

### Quick Test

Run the automated test suite:
```bash
python -m pytest tests/test_api.py -v
```

Or use the manual test script:
```bash
python manual_test.py
```

## 📡 API Endpoints

### POST `/api/analyze`
Analyze a password's strength and breach status.

**Request:**
```json
{
  "password": "your_password_here"
}
```

**Response:**
```json
{
  "score": 3,
  "strength_label": "Good",
  "entropy": 45.2,
  "crack_time_display": "2 days",
  "crack_time_seconds": 172800,
  "feedback": ["Add a capital letter", "Avoid common words"],
  "warning": "This is similar to a commonly used password",
  "is_breached": false,
  "breach_count": 0,
  "is_strong": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `score` | int | 0-4 strength score (0=very weak, 4=strong) |
| `strength_label` | string | Human-readable strength label |
| `entropy` | float | Shannon entropy in bits |
| `crack_time_display` | string | Human-readable crack time estimate |
| `crack_time_seconds` | float | Crack time in seconds |
| `feedback` | array | Specific improvement suggestions |
| `warning` | string \| null | High-level warning message |
| `is_breached` | bool | True if password found in breaches |
| `breach_count` | int \| null | Number of known breaches (0 if safe) |
| `is_strong` | bool | True if score >= 3 |

### GET `/api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "password-quest",
  "version": "1.0.0"
}
```

## 🛠️ Development Roadmap

### Phase 1: Bridge & API ✅ COMPLETE
- [x] Move core logic to `/core`
- [x] Flask app with `/api/analyze` and `/api/health` endpoints
- [x] 19 comprehensive API tests
- [x] Security headers (CSP, CORS, XSS protection)

### Phase 2: Interactive Dashboard ✅ COMPLETE
- [x] Tailwind CSS gamified UI
- [x] Real-time password analysis
- [x] Visual strength meter
- [x] Hacker Alert for breached passwords
- [x] Coach Tips feedback system

### Phase 3: Gamification Layer 🚧 IN PROGRESS
- [ ] SQLite database for user progress
- [ ] XP and badge system
- [ ] Scenario challenges
- [ ] Daily streaks

### Phase 4: Refinement & Security
- [ ] Rate limiting
- [ ] Zero logging verification
- [ ] Educational tooltips

### Phase 5: Deployment
- [ ] Docker containerization
- [ ] Audit export functionality

## 🔒 Security

- **Zero Password Logging** - Passwords are never logged or stored
- **k-Anonymity** - Breach checking uses HIBP's k-anonymity protocol (only first 5 hash chars sent)
- **Secure Memory** - Passwords handled with secure memory practices
- **Structured Logging** - JSON-formatted logs with automatic sensitive data redaction
- **Security Headers** - CSP, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov=core

# Manual test
python manual_test.py
```

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit PRs.

---

**Built with ❤️ for better password security education**