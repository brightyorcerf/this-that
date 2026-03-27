# This > That

https://disdat.vercel.app

![Demo](demo.jpg)

> *Inspiration from "The Social Network"*

This > That is a web application that ranks images using the ELO rating system in a battle-style format.

---

## Key Features

- Pairwise Comparison: Simple "point-and-click" voting interface
- ELO Rating System: Mathematical algorithm that updates image rankings dynamically based on wins/losses
- Live Leaderboard: Real-time, sortable ranking of all images, total number of votes
- Random Matchmaking: Logic to ensure unbiased pairs are generated for every round
- Responsive Design: Fully optimized for both desktop and mobile using Bootstrap 5

---

## Architecture Overview

```
User clicks image → JavaScript Fetch API → api/index.py (Serverless) → 
Supabase (PostgreSQL) updates ELO → JSON returned → UI updated via DOM manipulation
```

The "Fast-Path" Flow:
- User Click: JavaScript triggers an Optimistic UI update (dims images and increments counter instantly).
- Trip 1 (Batch Fetch): A single SQL UNION ALL query retrieves the current combatants' ELO, the next random pair, and the global leaderboard in one network round-trip.
- Local Compute: ELO math is calculated in the Python/Flask layer (nearly 0ms) rather than waiting for multiple database handshakes.
- Trip 2 (Atomic Update): A single SQL CASE statement performs a multi-row update for both images and returns the new global vote count.
- UI Sync: JSON is returned in <200ms, and the DOM is updated via a seamless opacity transition.

### Technology Stack

- Backend: Python + Flask (web framework) (deployed as vercel serverless functions)
- Database: PostgreSQL (hosted via supabase)
- Frontend: HTML, CSS, JavaScript, Bootstrap 5, jQuery DataTables
- Architecture: SPA (single page application) feel using AJAX/Fetch API for zero-reload voting.

--- 

## Fun Things I Learnt  
To keep the LCP (Largest Contentful Paint) under 1 second, I built a custom Python/Pillow pipeline to batch-convert raw JPEGs into high-compression WebP assets. Result: Reduced average asset size from 1.5MB to ~25KB (a 98% reduction!) without noticeable quality loss.

Atomic vs. Race Conditions: I realized that if two people vote at the exact same millisecond, the database might get confused. I learnt to use Atomic SQL updates (votes = votes + 1) to ensure every single click is registered perfectly.
 
How I slashed the latency:
- The Seamless Swap (AJAX/Fetch): Replaced clunky page reloads with a decoupled architecture. Using the Fetch API, votes are processed in the background, injecting new pairs instantly without a "flash of white."
- Fast-Path Execution: Re-engineered the backend to pre-calculate the next pair of images before the database finished saving the previous result.
- Optimistic UI: Programmed the frontend to update the moment a user clicks, effectively "hiding" the transcontinental lag.

My original implementation suffered from a "talkative" backend—making 8+ separate round-trips to Mumbai for every single vote. At 300ms of latency per trip, the app took nearly 10 seconds to respond. I optimized this by refactoring the backend into a Two-Trip Architecture. Using SQL UNION ALL and CASE statements, I consolidated the ELO fetching, next-pair generation, and leaderboard updates into a single batch request. By shifting the ELO math from the database to the application layer and using Optimistic UI patterns to dim images during transitions, I reduced the perceived latency by 98%, turning a sluggish global request into a snappy, sub-second experience.

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

--- 

## Adding Images

1. Place any `.jpg`, `.png`, `.gif`, or `.webp` files in `static/images/`
2. Run `python seedSupabase.py` to add them to the database 

---