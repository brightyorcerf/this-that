![website image](demo.jpg)

This > That: inspired from "the social network"

This-That is a web application that ranks images using the ELO rating system in a battle-style.
It's a simple version of another project I'm creating.

Key Features:

Pairwise Comparison: Users vote by clicking their preferred image
ELO Rating System: Mathematical algorithm that updates ratings based on wins/losses
Live Leaderboard: Real-time ranking of all images sorted by rating
Random Matchmaking: Generates random pairs for unbiased comparisons
Responsive Design: Works on desktop and mobile devices


🏗️ Architecture Overview
User clicks image → JavaScript submits form → Flask processes vote → 
Database updates ELO → Redirect to new pair
Technology Stack

Backend: Python + Flask (web framework)
Database: SQLite (via CS50 library)
Frontend: HTML, CSS, JavaScript, Bootstrap 5
Data Tables: jQuery DataTables (sortable leaderboard)


📁 File Structure & Purpose
this-that/
├── app.py                    # Main Flask application (routing & logic)
├── helpers.py                # ELO calculation functions
├── seed_database.py          # Database setup script
├── database.db               # SQLite database (created by seed script)
│
├── static/                  # Static assets (CSS, JS, images)
│   ├── images/              # Your image files (jpg, png, etc.)
│   ├── scripts/
│   │   ├── app.js           # DataTables initialization
│   │   └── scripts.js       # Vote submission & pair generation
│   └── styles/
│       └── styles.css       # Custom styling
│
└── templates/               # HTML templates (Jinja2)
    ├── layout.html          # Base template (navbar, scripts)
    └── battle.html          # Main voting interface


how to run 
conda activate base
python seed_database.py
python app.py