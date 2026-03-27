import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, flash, jsonify
from .helpers import updateElo
import secrets
import random

app = Flask(__name__, 
            template_folder="../templates", 
            static_folder="../static")

app.config["TEMPLATES_AUTO_RELOAD"] = True 
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))

def get_db_connection():
    """ Establish stateless Postgres Connection via Env Var """ 
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    return conn

def get_random_girl(cur):
    """
    O(1) approach for random fetching instead of ORDER BY random().
    ORDER BY random() forces a full table scan and database sort, killing scaling performance.
    Instead, we probabilistically leap into the ID space and take the first row we find.
    """
    cur.execute("""
        SELECT id, filename, elo 
        FROM girls 
        WHERE id >= (
            SELECT floor(random() * (SELECT COALESCE(MAX(id), 0) FROM girls)) + 1
        )
        ORDER BY id LIMIT 1;
    """)
    result = cur.fetchone()
    # Edge case due to massive gaps or if max random generation hits an empty pocket
    if not result:
        cur.execute("SELECT id, filename, elo FROM girls ORDER BY id LIMIT 1;")
        result = cur.fetchone()
    return result

def generate_random_pair(cur):
    """Generate two different random records"""
    girl1 = get_random_girl(cur)
    if not girl1:
        return None, None
        
    girl2 = get_random_girl(cur)
    
    # Deduplication retry limit in case of almost-empty database lengths
    retry_count = 0
    while girl2 and girl1['id'] == girl2['id'] and retry_count < 10:
        girl2 = get_random_girl(cur)
        retry_count += 1
        
    return girl1, girl2

@app.route("/", methods=["GET", "POST"])
def battle():
    try:
        conn = get_db_connection()
    except Exception as e:
        return f"Database connection failed: Make sure DATABASE_URL is set -> {e}", 500
        
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Leaderboard fetch
    cur.execute("SELECT id, filename, elo FROM girls ORDER BY elo DESC LIMIT 3")
    girls = cur.fetchall()
    
    cur.execute("SELECT MAX(id) AS counter FROM girls")
    count_res = cur.fetchone()
    MAX_ID = count_res['counter'] if count_res and count_res['counter'] else 0
    
    if request.method == "GET":
        girl1, girl2 = generate_random_pair(cur)
        if not girl1 or not girl2:
            girl1 = {"id": 0, "filename": "placeholder.jpg", "elo": 0}
            girl2 = {"id": 0, "filename": "placeholder.jpg", "elo": 0}
            
        cur.execute("SELECT SUM(votes) / 2 AS total FROM girls")
        total_res = cur.fetchone()
        total_votes = total_res['total'] if total_res and total_res['total'] else 0
            
        cur.close()
        conn.close()
        return render_template("battle.html", MAX_ID=MAX_ID, girl1=girl1, girl2=girl2, girls=girls, total_votes=int(total_votes))
        
    else:  # POST request
        # Parse JSON if available, otherwise fallback to form
        data = request.get_json(silent=True) or request.form
        
        # Handle explicit pair ID requests conditionally passed inside the application 
        if data.get("id1") and data.get("id2"):
            id1 = data.get("id1")
            id2 = data.get("id2")
            
            # Security Audit: Stringent parsing over Python List Inclusion. Stops injection arrays natively
            try:
                id1 = int(id1)
                id2 = int(id2)
            except ValueError:
                cur.close()
                conn.close()
                return jsonify({"error": "Invalid image IDs selected: Must be integers"}), 400
            
            # Additional logical checks
            if id1 == id2 or id1 <= 0 or id2 <= 0:
                cur.close()
                conn.close()
                return jsonify({"error": "Invalid image IDs selected: IDs must be different and positive"}), 400
                
            cur.execute("SELECT id, filename, elo FROM girls WHERE id = %s", (id1,))
            girl1 = cur.fetchone()
            cur.execute("SELECT id, filename, elo FROM girls WHERE id = %s", (id2,))
            girl2 = cur.fetchone()
            
            cur.execute("SELECT SUM(votes) / 2 AS total FROM girls")
            total_res = cur.fetchone()
            total_votes = total_res['total'] if total_res and total_res['total'] else 0
            
            cur.close()
            conn.close()
            
            if not girl1 or not girl2:
                return jsonify({"error": "Image IDs not found in database"}), 404
                
            return jsonify({
                "girl1": girl1,
                "girl2": girl2,
                "leaderboard": girls,
                "total_votes": int(total_votes)
            })
            
        # Standard Voting Path route
        elif data.get("winner") and data.get("loser"):
            winner_id = data.get("winner")
            loser_id = data.get("loser")
            
            # Security Audit Validation: Ensure they are parseable, unique integers!
            try:
                winner_id = int(winner_id)
                loser_id = int(loser_id)
            except ValueError:
                cur.close()
                conn.close()
                return jsonify({"error": "Invalid vote format: IDs must be integer"}), 400
            
            if winner_id == loser_id or winner_id <= 0 or loser_id <= 0:
                cur.close()
                conn.close()
                return jsonify({"error": "Invalid vote submission: self-votes not allowed"}), 400
                
            try:
                # Actual_Score is strictly passed internally as 1 (winner) and 0 (loser) 
                # resolving the strict actual_score inputs
                updateElo(winner_id, loser_id, conn, k_factor=32, actual_score_winner=1, actual_score_loser=0)
                
                # 1. Update vote counts in DB
                cur.execute("UPDATE girls SET votes = COALESCE(votes, 0) + 1 WHERE id IN (%s, %s)", (winner_id, loser_id))
                
                # 2. Get the Global Total
                cur.execute("SELECT SUM(votes) / 2 AS total FROM girls")
                total_res = cur.fetchone()
                total_votes = total_res['total'] if total_res and total_res['total'] else 0
                
                conn.commit()
            except Exception as e:
                conn.rollback() # Ensure transaction closes properly to avoid locks!
                cur.close()
                conn.close()
                return jsonify({"error": f"Error recording vote: {str(e)}"}), 500
                
            # AUTO-GENERATE NEXT PAIR
            girl1, girl2 = generate_random_pair(cur)
            if girl1 and girl2:
                cur.execute("SELECT id, filename, elo FROM girls ORDER BY elo DESC LIMIT 3")
                girls = cur.fetchall()
                cur.close()
                conn.close()
                return jsonify({
                    "girl1": girl1,
                    "girl2": girl2,
                    "leaderboard": girls,
                    "total_votes": int(total_votes)
                })
            else:
                cur.close()
                conn.close()
                return jsonify({"error": "Failed to generate next pair"}), 500
                
        else:
            cur.close()
            conn.close()
            return jsonify({"error": "Invalid request parameters"}), 400

if __name__ == "__main__":
    app.run(debug=True)