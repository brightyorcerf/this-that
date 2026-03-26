# This > That

https://disdat.vercel.app

![Demo](demo.jpg)

> *Inspiration from "The Social Network"*

This > That is a web application that ranks images using the ELO rating system in a battle-style format. It's a simpler version of another project I'm creating.

---

## Key Features

- Pairwise Comparison: Simple "point-and-click" voting interface
- ELO Rating System: Mathematical algorithm that updates image rankings dynamically based on wins/losses
- Live Leaderboard: Real-time, sortable ranking of all images
- Random Matchmaking: Logic to ensure unbiased pairs are generated for every round
- Responsive Design: Fully optimized for both desktop and mobile using Bootstrap 5

---

## Architecture Overview

```
User clicks image → JavaScript Fetch API → api/index.py (Serverless) → 
Supabase (PostgreSQL) updates ELO → JSON returned → UI updated via DOM manipulation
```

### Technology Stack

- Backend: Python + Flask (web framework) (deployed as vercel serverless functions)
- Database: PostgreSQL (hosted via supabase)
- Frontend: HTML, CSS, JavaScript, Bootstrap 5, jQuery DataTables
- Architecture: SPA (single page application) feel using AJAX/Fetch API for zero-reload voting.

---

## File Structure 

```
this-that/
├── api/
│   ├── index.py          # Main Serverless entry point
│   └── helpers.py        # ELO & DB utility logic
├── static/
│   ├── images/           # Asset storage
│   ├── scripts/          # app.js (AJAX logic)
│   └── styles/           # Custom CSS
├── templates/            # Jinja2 HTML templates
├── seedSupabase.py       # Cloud DB setup script
└── vercel.json           # Deployment configuration
```

--- 

## 🧮 The Logic

The core ranking is calculated using the **ELO formula**. For two images A and B, the expected score E<sub>A</sub> is calculated as:

```
E_A = 1 / (1 + 10^((R_B - R_A) / 400))
```

Where:
- `R_A` = Current rating of image A
- `R_B` = Current rating of image B
- `E_A` = Expected probability that A wins (between 0 and 1)

After each match, ratings are updated:

```
New_Rating_A = Old_Rating_A + K × (Actual_Score - Expected_Score)
```

Where:
- `K` = 32 (K-factor, controls rating volatility)
- `Actual_Score` = 1 if won, 0 if lost
- `Expected_Score` = Calculated probability from formula above


## Adding Images

1. Place any `.jpg`, `.png`, `.gif`, or `.webp` files in `static/images/`
2. Run `python seedSupabase.py` to add them to the database 

---